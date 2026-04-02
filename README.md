# YouTube Music Radio para Hyprland

Scripts para reproducir música de YouTube Music con MPV, pensados para Hyprland.

## Estructura

- `radio.py` — lógica principal: búsqueda, moods/géneros, playlists, notificaciones y control de MPV vía IPC.
- `wofi_launcher.sh` — lanzador con Wofi que llama a `radio.py` con los parámetros adecuados.
- `requirements.txt` — dependencias de Python.

## Requisitos

- `mpv` instalado
- Python 3.x con `pip`
- `wofi` (en Wayland; se puede adaptar a rofi)
- Conexión a Internet

## Instalación

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
chmod +x wofi_launcher.sh
```

## Uso

```bash
./wofi_launcher.sh
```

El launcher ofrece tres modos:
1. Buscar por artista o canción
2. Describir el tipo de música con palabras ("rock melancólico", "jazz para trabajar"...)
3. Explorar categorías de mood/género de YouTube Music

## Integración con Hyprland

En `~/.config/hypr/hyprland.conf`:

```
bindd = $mainMod, R, YouTube Music launcher, exec, /ruta/a/wofi_launcher.sh
```

Luego `hyprctl reload`.
