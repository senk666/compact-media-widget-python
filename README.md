# Compact Linux Media Widget

A lightweight, semi-transparent music widget for Linux. Built with Python 3 and PyQt6, this widget interfaces with any active media player supporting MPRIS (such as Spotify, Yandex Music, or browser streams) and runs efficiently in the background without interrupting hardware-intensive tasks or full-screen gaming.

*Note: This project was fully developed and optimized with the assistance of Artificial Intelligence.*

---

## Target Environments & Compatibility

- **Primary Development Platform**: This widget was originally developed, tested, and optimized specifically on **Fedora Linux** using the **GNOME** desktop environment running natively on **Wayland**.
- **Display Server Requirement**: Since the layout forces a semi-transparent, frameless overhead window while retaining game focus, it utilizes the XWayland compatibility layer (`QT_QPA_PLATFORM=xcb`) to safely render on top of applications without crashing the session bus under Wayland.
- **Supported Distributions**: The widget is highly portable and will run seamlessly on any modern Linux distribution that provides standard Python 3 and D-Bus MPRIS hooks. Compatible distributions include, but are not limited to:
  - **Fedora** (Workstation, Silverblue)
  - **Ubuntu / Debian** and their derivatives (Linux Mint, Pop!_OS, Zorin OS)
  - **Arch Linux** / Manjaro
  - **openSUSE** (Tumbleweed, Leap)
- **Supported Desktop Environments**: Works across **GNOME**, **KDE Plasma**, **XFCE**, **Cinnamon**, and **MATE**.

---

## Key Features

- **Resource Efficient**: Highly optimized to run with a minimal footprint, consuming approximately **27 MB of RAM** and near `0%` CPU as verified by system monitoring utilities.
- **Uninterrupted Gaming**: Configured with a native `NoFocus` flag. Clicking controls like pause or track skipping will never steal window focus, collapse, or minimize full-screen applications (tested heavily while playing Minecraft).
- **Dedicated Time Tracking**: Track position and total length (`1:21/5:32`) are extracted into an independent layout row directly below the song title using a distinct, light font weight.
- **Album Art Integration**: Dynamically extracts and caches stream or local artwork file paths, rendering them inside an anti-aliased container with matching border radiuses.
- **Granular Command-Line Customization**: Layout sizing, typography metrics, alignments, exact hex-codes, button structures, and individual transparency channels can be overhauled directly upon script initialization.

---

## Dependencies & Installation

To run this widget, ensure you have Python 3, `playerctl` for MPRIS capabilities, and the PyQt6 framework installed.

On Fedora, install the required packages using DNF:
```bash
sudo dnf install playerctl
pip install PyQt6
```

On Ubuntu / Debian-based distributions:
```bash
sudo apt install playerctl
pip install PyQt6
```

On Arch Linux:
```bash
sudo pacman -S playerctl python-pyqt6
```

---

## Usage Example

Launch the widget utilizing the XWayland translation layer with white background properties, custom font scaling, static screen locking, and fixed `40x40px` button dimensions:

```bash
QT_QPA_PLATFORM=xcb python mediaw.py --pos 1500 100 --colorback "#FFFFFF" --colorbutton "#FFFFFF" --colortext "#CDD6F4" --alpha_bg 75  --align left --size "320 50" --btn_size "40 40" --font_name "Rubik"
```

---

## Command-Line Arguments

The script parses the following customizable arguments during initialization:

| Flag | Data Type | Description | Default Value |
| :--- | :--- | :--- | :--- |
| `--pos` | `int int` | Initial coordinate offset on screen (X Y) | Top Right |
| `--size` | `str` | Total widget proportions string `"Width Height"` | `"360 65"` |
| `--btn_size` | `str` | Interactive button bounds string `"Width Height"`| `"auto"` (matches view height) |
| `--colorback` | `str` | Target background hex-color code | `"#11111B"` |
| `--colorbutton`| `str` | Control button base hex-color code | `"#FFFFFF"` |
| `--colortext` | `str` | Font tracking and string titles hex-color code | `"#FFFFFF"` |
| `--alpha_bg` | `int` | Main window alpha transparency value (`0`-`255`)| `120` |
| `--btn_prev` | `bool` | Toggles rendering of the "Previous" action | `true` |
| `--btn_next` | `bool` | Toggles rendering of the "Next" action | `true` |
| `--draggable` | `bool` | Allows left-click drag window movements | `true` |
| `--align` | `str` | Internal title text layout alignment policy | `left` |
| `--player` | `str` | Forces MPRIS path hooks onto a chosen client name | `auto` |
| `--marquee` | `bool` | Scrolls text arrays if title overflow bounds snap | `false` |
| `--font_name` | `str` | Explicit application font family name | `sans-serif` |
| `--font_size` | `int` | Point sizing for primary asset strings | `11` |

---

## License

This program is distributed under the open-source MIT License. You are free to modify, fork, and re-distribute this software package.
