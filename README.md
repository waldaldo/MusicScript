- YouTube Music Radio para Hyprland - Guía rápida y estética

Resumen
- Un conjunto de scripts que permiten reproducir música de YouTube Music mediante MPV, utilizando la API de YouTube Music (ytmusicapi). El núcleo es radio.py, que gestiona búsquedas, moods/géneros y listas de reproducción. Un launcher (wofi_launcher.sh) orquesta la interacción del usuario y llama a radio.py con los parámetros adecuados. Todo pensado para una integración simple con Hyprland.

Estructura del repositorio (en la carpeta Musica)
- radio.py: Lógica principal de radio (búsqueda, mood/genre, playlist, notificaciones y control de MPV vía IPC).
- wofi_launcher.sh: Launcher que utiliza Wofi para dirigir a radio.py.
- requirements.txt: Dependencias de Python.
- README.md: Esta documentación.

Requisitos
- MPV instalado (reproducción de audio).
- Python 3.x y pip disponibles; se recomienda usar un entorno virtual (venv).
- En entornos Wayland, Wofi es recomendado para el launcher. Si prefieres rofi, el launcher puede adaptarse.
- Conexión a Internet para los datos de YouTube Music.

Instalación y entorno
- Crear y activar un entorno virtual:
  python3 -m venv venv
  source venv/bin/activate
- Instalar dependencias:
  pip install -r requirements.txt
- Asegurar permisos de ejecución para el launcher:
  chmod +x /path/to/wofi_launcher.sh

Flujo de uso
- Lanzar el launcher desde terminal:
  /path/to/wofi_launcher.sh
- El launcher muestra tres opciones:
  1) Buscar por artista/canción
  2) Describir con palabras el tipo de música
  3) Explorar categorías de mood/género
- Descripción de cada ruta:
  - Buscar por artista/canción: se solicita una entrada y se llama a radio.py con --mode search --query "<entrada>".
  - Describir con palabras el tipo de música: se solicita una entrada y se llama a radio.py con --mode prompt --query "<entrada>".
  - Explorar mood/género: se obtienen las categorías desde radio.py con --mode list-categories, se muestran y se elige una; se invoca radio.py con --mode category --params "<JSON>".
- La ejecución de radio.py maneja la reproducción mediante MPV, notificaciones y control de volumen/pausas.

Integración con Hyprland
- Bindings de ejemplo para lanzar el launcher con un atajo de teclado:
  bindd = $mainMod, R, YouTube Music launcher, exec, /path/to/wofi_launcher.sh
- Después de editar la configuración, recarga Hyprland:
  hyprctl reload
- Nota: Mod4 commonmente es la tecla Super/Windows. Cambia si usas otro modificador.

Notas técnicas y mantenimiento
- El launcher es deliberadamente ligero para facilitar mantenimiento. Puede adaptarse a rofi si se prefiere ese launcher.
- Si el flujo cambia, se puede actualizar el README con una sección de ejemplos y consideraciones.

Contribución y licencia
- Este README es una guía de uso para el entorno local. Si publicas el proyecto, considera añadir una licencia (MIT, Apache-2.0, etc.).

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
