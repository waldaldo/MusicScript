YouTube Music Radio for Hyprland (Wrapper)

Resumen
- Conjunto de scripts que permiten buscar y reproducir música de YouTube Music mediante MPV, usando la API de YouTube Music (ytmusicapi) y una interfaz de usuario simple basada en Wofi (Wayland).
- El flujo principal es: el script de fondo (radio.py) maneja la obtención de pistas y la reproducción; un launcher (wofi_launcher.sh) orquesta la interacción de usuario y lanza radio.py con los parámetros adecuados.

Estructura del repositorio (en la carpeta Musica)
- radio.py: núcleo de la funcionalidad. Implementa la lógica de búsqueda, mood/genre, playlist, notificaciones y control de MPV a través de IPC.
- wofi_launcher.sh: launcher que presenta un menú con las opciones disponibles y llama a radio.py con el modo correspondiente.
- requirements.txt: dependencias de Python necesarias (ytmusicapi, requests, etc.).
- README.md: presente para documentación y guía de uso.

Requisitos previos
- MPV instalado (para reproducción de audio).
- Python 3.x y pip disponible.
- Dependencias instaladas: ejecutar en el directorio del proyecto:
  - python3 -m venv venv
  - source venv/bin/activate
  - pip install -r requirements.txt
- Si utilizas Wayland, disponer de Wofi para el launcher; el script actual usa wofi. Si prefieres rofi, puedo adaptar el launcher, pero actualmente está enfocado en wofi.

Uso básico
  - /home/walo/.config/hypr/scripts/Musica/wofi_launcher.sh
  - Aparecerá un menú con tres opciones: buscar por artista/canción, describir con palabras el tipo de música, explorar categorías de mood/género.
  - Cada opción se conecta con radio.py para obtener resultados y reproducirlos mediante MPV.

Integración con Hyprland (atajos de teclado)
- Ejemplo mínimo para lanzar el launcher desde Hyprland con Mod+R (sin depender de UserPrefs):
  bindd = $mainMod, R, YouTube Music launcher, exec, /home/walo/.config/hypr/scripts/Musica/wofi_launcher.sh
- Asegúrate de recargar Hyprland tras añadir el binding: hyprctl reload

Notas técnicas
- radio.py administra la reproducción, notificaciones y la creación de la cola de MPV.
- El launcher solo orquesta la interacción del usuario y la invocación de radio.py con la opción adecuada.
- Los archivos y rutas son absolutas para evitar dependencias de entorno al ejecutarse desde Hyprland.
- Si necesitas cambiar la ruta de los scripts, actualiza las rutas en el launcher o en el binding de Hyprland.

Contribución y mantenimiento
- Este README describe el flujo actual y la estructura de archivos. Si necesitas añadir más modos o ampliar el soporte de entrada (p. ej., rofi), puedo adaptar el launcher o crear un segundo launcher.

Licencia
- No se especifica una licencia en este repositorio local. Si vas a publicarlo, te sugiero añadir una licencia (MIT, Apache, etc.).
