#!/usr/bin/env python3
import sys, subprocess, signal, argparse, urllib.request, os, threading, time, shutil
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt, QTimer, QPoint, QVariantAnimation, QRectF, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QPainter, QColor, QFont, QPixmap, QPainterPath, QFontDatabase
class CompactPlayer(QWidget):
    track_updated = pyqtSignal(str, str, str, str)
    def __init__(self, args):
        super().__init__()
        self.args, self.drag_pos, self.target_icon, self.btn_alpha = args, QPoint(), "||", 255
        self.full_text, self.scroll_offset, self.last_art_url = "Нет медиа", 0, ""
        try:
            w_str, h_str = self.args.size.split()
            self.w_val, self.h_val = int(w_str), int(h_str)
        except: self.w_val, self.h_val = 360, 65
        try:
            bw_str, bh_str = self.args.btn_size.split()
            self.btn_w, self.btn_h = int(bw_str), int(bh_str)
        except:
            self.btn_w, self.btn_h = int((self.h_val - 12) * 0.9), self.h_val - 12
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.SubWindow | Qt.WindowType.WindowDoesNotAcceptFocus
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.resize(self.w_val, self.h_val)
        if self.args.pos and len(self.args.pos) == 2: self.move(int(self.args.pos[0]), int(self.args.pos[1]))
        else:
            screen = QApplication.primaryScreen().geometry()
            self.move(screen.width() - self.width() - 30, 80)
        self.bg_color, self.btn_color, self.text_color = QColor(self.args.colorback), QColor(self.args.colorbutton), QColor(self.args.colortext)
        self.bg_color.setAlpha(self.args.alpha_bg)
        self.btn_anim = QVariantAnimation(self)
        self.btn_anim.setDuration(150)
        self.btn_anim.valueChanged.connect(self.animate_btn_text)
        available_fonts = QFontDatabase.families()
        requested_font = self.args.font_name
        if requested_font not in available_fonts:
            fallback_options = ["DejaVu Sans", "Liberation Sans", "Noto Sans", "Ubuntu", "sans-serif"]
            requested_font = next((f for f in fallback_options if f in available_fonts), "sans-serif")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)
        self.art_lbl = QLabel(self)
        self.art_lbl.setFixedSize(self.h_val - 12, self.h_val - 12)
        self.art_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setDefaultArt()
        layout.addWidget(self.art_lbl)
        align_map = {"left": Qt.AlignmentFlag.AlignLeft, "top": Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, "right": Qt.AlignmentFlag.AlignRight, "bottom": Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom}
        chosen_align = align_map.get(self.args.align, Qt.AlignmentFlag.AlignLeft)
        text_container = QVBoxLayout()
        text_container.setContentsMargins(0, 2, 0, 2)
        text_container.setSpacing(1)
        self.track_lbl = QLabel(self)
        self.track_lbl.setAlignment(chosen_align | Qt.AlignmentFlag.AlignVCenter)
        self.track_lbl.setFont(QFont(requested_font, self.args.font_size, QFont.Weight.Bold))
        self.track_lbl.setStyleSheet(f"color: {self.text_color.name()}; margin: 0px; padding: 0px 4px;")
        text_container.addWidget(self.track_lbl)
        self.time_lbl = QLabel(self)
        self.time_lbl.setAlignment(chosen_align | Qt.AlignmentFlag.AlignVCenter)
        time_font = QFont(requested_font, max(7, self.args.font_size - 3), QFont.Weight.Light)
        time_font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
        self.time_lbl.setFont(time_font)
        self.time_lbl.setStyleSheet(f"color: rgba({self.text_color.red()}, {self.text_color.green()}, {self.text_color.blue()}, 0.7); margin: 0px; padding: 0px 4px;")
        text_container.addWidget(self.time_lbl)
        layout.addLayout(text_container, 1)
        self.btn_style_base = f"background: rgba({self.btn_color.red()}, {self.btn_color.green()}, {self.btn_color.blue()}, 0.3); border: none; border-radius: 6px; font-family: monospace; font-size: 13px; font-weight: bold; min-width: {self.btn_w}px; max-width: {self.btn_w}px; min-height: {self.btn_h}px; max-height: {self.btn_h}px; margin: 0px; padding: 0px;"
        detected_playerctl = shutil.which('playerctl')
        if not detected_playerctl: detected_playerctl = 'playerctl'
        self.p_cmd = [detected_playerctl]
        if self.args.player and self.args.player.lower() != "auto": self.p_cmd.extend(['--player', self.args.player])
        if self.args.btn_prev:
            self.btn_prev = QPushButton("|<", self)
            self.btn_prev.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            self.btn_prev.setStyleSheet(f"QPushButton {{{self.btn_style_base} color: {self.text_color.name()};}} QPushButton:hover {{ background: rgba({self.btn_color.red()}, {self.btn_color.green()}, {self.btn_color.blue()}, 0.5); }}")
            self.btn_prev.clicked.connect(lambda: subprocess.Popen(self.p_cmd + ['previous'], env=self.get_clean_env()))
            layout.addWidget(self.btn_prev)
        self.btn_play = QPushButton("||", self)
        self.btn_play.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.update_play_btn_style()
        self.btn_play.clicked.connect(self.toggle_play)
        layout.addWidget(self.btn_play)
        if self.args.btn_next:
            self.btn_next = QPushButton(">|", self)
            self.btn_next.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            self.btn_next.setStyleSheet(f"QPushButton {{{self.btn_style_base} color: {self.text_color.name()};}} QPushButton:hover {{ background: rgba({self.btn_color.red()}, {self.btn_color.green()}, {self.btn_color.blue()}, 0.5); }}")
            self.btn_next.clicked.connect(lambda: subprocess.Popen(self.p_cmd + ['next'], env=self.get_clean_env()))
            layout.addWidget(self.btn_next)
        self.track_updated.connect(self.on_track_updated)
        self.worker_thread = threading.Thread(target=self.async_track_updater, daemon=True)
        self.worker_thread.start()
        self.time_timer = QTimer(self)
        self.time_timer.timeout.connect(self.update_only_time)
        self.time_timer.start(1000)
        if self.args.marquee:
            self.marquee_timer = QTimer(self)
            self.marquee_timer.timeout.connect(self.scroll_text)
            self.marquee_timer.start(250)
    def get_clean_env(self):
        env = os.environ.copy()
        if "DBUS_SESSION_BUS_ADDRESS" not in env:
            uid = os.getuid()
            path = f"/run/user/{uid}/bus"
            if os.path.exists(path): env["DBUS_SESSION_BUS_ADDRESS"] = f"unix:path={path}"
        return env
    def setDefaultArt(self):
        pix = QPixmap(self.art_lbl.width(), self.art_lbl.height())
        pix.fill(QColor("#222222"))
        painter = QPainter(pix)
        painter.setPen(QColor("#FFFFFF"))
        painter.setFont(QFont("sans-serif", int(self.art_lbl.height()*0.45)))
        painter.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, "♫")
        painter.end()
        self.set_rounded_pixmap(pix)
    def set_rounded_pixmap(self, pix):
        target = QPixmap(pix.size())
        target.fill(Qt.GlobalColor.transparent)
        painter = QPainter(target)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, pix.width(), pix.height()), 6.0, 6.0)
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, pix)
        painter.end()
        self.art_lbl.setPixmap(target)
    def load_art(self, url):
        if not url or url == self.last_art_url: return
        self.last_art_url = url
        try:
            if url.startswith("file://"): pix = QPixmap(url.replace("file://", ""))
            elif url.startswith("http"):
                data = urllib.request.urlopen(url, timeout=1).read()
                pix = QPixmap()
                pix.loadFromData(data)
            else: self.setDefaultArt(); return
            if not pix.isNull():
                scaled = pix.scaled(self.art_lbl.width(), self.art_lbl.height(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.set_rounded_pixmap(scaled)
            else: self.setDefaultArt()
        except: self.setDefaultArt()
    def update_play_btn_style(self):
        c = self.text_color
        self.btn_play.setStyleSheet(f"QPushButton {{{self.btn_style_base} color: rgba({c.red()},{c.green()},{c.blue()},{self.btn_alpha});}} QPushButton:hover {{ background: rgba({self.btn_color.red()}, {self.btn_color.green()}, {self.btn_color.blue()}, 0.5); }}")
    def animate_btn_text(self, value):
        self.btn_alpha = value
        self.update_play_btn_style()
        if value == 0:
            self.btn_play.setText(self.target_icon)
            self.btn_anim.setDirection(QVariantAnimation.Direction.Backward)
            self.btn_anim.start()
    def start_icon_transition(self, new_icon):
        if self.btn_play.text() != new_icon and self.btn_anim.state() == QVariantAnimation.State.Stopped:
            self.target_icon = new_icon
            self.btn_anim.setDirection(QVariantAnimation.Direction.Forward)
            self.btn_anim.setStartValue(255)
            self.btn_anim.setEndValue(0)
            self.btn_anim.start()
        elif self.btn_anim.state() == QVariantAnimation.State.Stopped: self.btn_play.setText(new_icon)
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 12.0, 12.0)
        painter.setClipPath(path)
        painter.setBrush(self.bg_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(self.rect())
    def mousePressEvent(self, event):
        if self.args.draggable and event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    def mouseMoveEvent(self, event):
        if self.args.draggable and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()
    def fmt_time(self, microsec_str):
        try:
            sec = int(int(microsec_str) / 1000000)
            return f"{sec // 60}:{sec % 60:02d}"
        except: return "--:--"
    def scroll_text(self):
        if not self.args.marquee or len(self.full_text) <= 18:
            self.track_lbl.setText(self.full_text)
            return
        text = self.full_text + "   "
        self.scroll_offset = (self.scroll_offset + 1) % len(text)
        self.track_lbl.setText(text[self.scroll_offset:] + text[:self.scroll_offset])
    def async_track_updater(self):
        while True:
            try:
                res = subprocess.run(self.p_cmd + ['metadata', '--format', '{{artist}} - {{title}}||{{mpris:artUrl}}'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=self.get_clean_env(), timeout=2)
                parts = res.stdout.strip().split("||")
                if parts and len(parts) > 1 and parts[0] and parts[0] != " - ":
                    self.track_updated.emit(str(parts[0]), "", str(parts[1]) if len(parts) > 1 else "", "")
                else: self.track_updated.emit("Нет медиа", "", "", "")
            except:
                self.track_updated.emit("Нет медиа", "", "", "")
            time.sleep(1.5)
    def update_only_time(self):
        try:
            status_res = subprocess.run(self.p_cmd + ['status'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, env=self.get_clean_env(), timeout=1)
            status = status_res.stdout.strip()
            if status: self.start_icon_transition(">" if status == "Paused" else "||")
            else: self.start_icon_transition("||")
            pos_res = subprocess.run(self.p_cmd + ['metadata', '--format', '{{position}}||{{mpris:length}}'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, env=os.environ, timeout=1)
            t_parts = pos_res.stdout.strip().split("||")
            if len(t_parts) == 2 and t_parts[0] and t_parts[1]:
                self.time_lbl.setText(f"{self.fmt_time(t_parts[0])}/{self.fmt_time(t_parts[1])}")
            else: self.time_lbl.setText("")
        except: self.time_lbl.setText("")
    @pyqtSlot(str, str, str, str)
    def on_track_updated(self, info, time_str, art_url, status):
        if self.full_text != info:
            self.full_text = info
            self.scroll_offset = 0
        if not self.args.marquee:
            self.track_lbl.setText(self.full_text if len(self.full_text) <= 18 else self.full_text[:16] + "...")
        if art_url: self.load_art(art_url)
        else: self.setDefaultArt()
    def toggle_play(self):
        subprocess.Popen(self.p_cmd + ['play-pause'], env=self.get_clean_env())
        QTimer.singleShot(100, self.update_only_time)
if __name__ == '__main__':
    def str2bool(v): return v.lower() in ("yes", "true", "t", "1")
    parser = argparse.ArgumentParser()
    parser.add_argument("--pos", type=int, nargs=2, default=None)
    parser.add_argument("--size", type=str, default="360 65")
    parser.add_argument("--btn_size", type=str, default="auto")
    parser.add_argument("--colorback", type=str, default="#11111B")
    parser.add_argument("--colorbutton", type=str, default="#FFFFFF")
    parser.add_argument("--colortext", type=str, default="#FFFFFF")
    parser.add_argument("--alpha_bg", type=int, default=120)
    parser.add_argument("--btn_prev", type=str2bool, default=True)
    parser.add_argument("--btn_next", type=str2bool, default=True)
    parser.add_argument("--draggable", type=str2bool, default=True)
    parser.add_argument("--align", choices=["left", "top", "right", "bottom"], default="left")
    parser.add_argument("--player", type=str, default="auto")
    parser.add_argument("--marquee", type=str2bool, default=False)
    parser.add_argument("--font_name", type=str, default="sans-serif")
    parser.add_argument("--font_size", type=int, default=11)
    args = parser.parse_args()
    def signal_handler(sig, frame):
        QApplication.quit()
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTSTP, signal_handler)
    app = QApplication(sys.argv)
    player = CompactPlayer(args)
    player.show()
    pos_timer = QTimer()
    pos_timer.start(200)
    pos_timer.timeout.connect(lambda: None)
    sys.exit(app.exec())
