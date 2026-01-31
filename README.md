YouTube Music Radio for Hyprland - Quick Guide

Overview
- A small collection of scripts that orchestrate YouTube Music playback via MPV using the ytmusicapi. The core radio.py handles search by artist/song, mood/genre, and playlists. A launcher (wofi_launcher.sh) provides a lightweight UI to drive the radio.py flow. The setup is aimed to be simple and easily integrate with Hyprland.

Project layout (in Musica directory)
- radio.py: Core radio logic (search, mood/genre, playlist, notifications, MPV IPC).
- wofi_launcher.sh: Launcher wrapper that drives radio.py via wofi (Wayland).
- requirements.txt: Python dependencies.
- README.md: This file.

Prerequisites
- MPV is installed for audio playback.
- Python 3.x and pip are available; a virtual environment is recommended.
- On Wayland: wofi is recommended for the launcher; rofi can be used with minor adaptations.
- Network access for YouTube data is required.

Setup
- Create a Python virtual environment and install dependencies:
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
- Ensure launcher is executable:
  chmod +x /path/to/wofi_launcher.sh

Usage
- Run the launcher from terminal:
  /path/to/wofi_launcher.sh
- The launcher presents three options:
  1) Buscar por artista/canción
  2) Describir con palabras el tipo de música
  3) Explorar categorías de mood/género
- For mood categories, the launcher fetches the available mood/genre categories from radio.py and shows them for selection. The final invocation uses:
  radio.py --mode category --params "<JSON>"
- All paths refer to the actual installed locations (adjust as needed).

Hyprland integration (hotkey)
- You can bind a hotkey (e.g., Mod+R) to launch the launcher script.
- Example (paths are illustrative):
  bindd = $mainMod, R, YouTube Music launcher, exec, /path/to/wofi_launcher.sh
- After editing the Hyprland config, reload hyprland: hyprctl reload

Extensibility
- The launcher is intentionally minimal to simplify maintenance. It can be adapted to rofi as well by replacing the launcher with a rofi-based variant.

License
- No license specified in this local repository. If you publish, consider adding a license (MIT, Apache-2.0, etc.).
