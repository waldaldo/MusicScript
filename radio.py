#!/usr/bin/env python3
import sys
import os
import time
import json
import socket
import subprocess
import threading
import shutil
import argparse
from ytmusicapi import YTMusic
import requests

try:
    import evdev
    from evdev import InputDevice, categorize, ecodes
    HAS_EVDEV = True
except ImportError:
    HAS_EVDEV = False

try:
    from pynput import keyboard
    HAS_PYNPUT = True
except ImportError:
    HAS_PYNPUT = False

# Auto-activación del entorno virtual
if sys.prefix == sys.base_prefix:
    venv_python = os.path.join(os.path.dirname(os.path.abspath(__file__)), "venv", "bin", "python")
    if os.path.exists(venv_python):
        os.execv(venv_python, [venv_python] + sys.argv)

# Configuración
SOCKET_PATH = "/tmp/mpv_radio_socket"
TEMP_THUMB = "/tmp/yt_radio_thumb.jpg"

class MediaKeysController:
    def __init__(self, player):
        self.player = player
        self.running = False
        self.thread = None
        self.evdev_devices = []
        
    def start(self):
        self.running = True
        if HAS_EVDEV:
            self.thread = threading.Thread(target=self._evdev_listener)
        elif HAS_PYNPUT:
            self.thread = threading.Thread(target=self._pynput_listener)
        else:
            print("Advertencia: No se encontró evdev ni pynput. Control por teclas multimedia no disponible.")
            return
        self.thread.daemon = True
        self.thread.start()
        
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
        for dev in self.evdev_devices:
            try:
                dev.ungrab()
            except:
                pass
                
    def _evdev_listener(self):
        try:
            import evdev
            from evdev import ecodes
            devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
            
            for dev in devices:
                caps = dev.capabilities()
                if ecodes.EV_KEY in caps:
                    try:
                        # IMPORTANTE: No usamos grab() para no bloquear el dispositivo al resto del sistema
                        # dev.grab() 
                        self.evdev_devices.append(dev)
                    except PermissionError:
                        continue
                        
            if not self.evdev_devices:
                print("No se pudo acceder a dispositivos de entrada. Requiere permisos (grupo input o root).")
                return
                
            media_key_codes = {
                ecodes.KEY_PLAYPAUSE: "play_pause",
                ecodes.KEY_PLAY: "play",
                ecodes.KEY_PAUSE: "pause",
                ecodes.KEY_STOP: "stop",
                ecodes.KEY_NEXTSONG: "next",
                ecodes.KEY_PREVIOUSSONG: "prev",
                ecodes.KEY_VOLUMEUP: "volume_up",
                ecodes.KEY_VOLUMEDOWN: "volume_down",
                ecodes.KEY_MUTE: "mute",
                ecodes.KEY_MEDIA: "play_pause",
            }
            
            while self.running:
                for dev in self.evdev_devices:
                    try:
                        event = dev.read_one()
                        if event and event.type == ecodes.EV_KEY and event.value == 1:
                            action = media_key_codes.get(event.code)
                            if action:
                                self._handle_media_key(action)
                    except (BlockingIOError, OSError):
                        continue
                time.sleep(0.01)
                
        except Exception as e:
            print(f"Error en listener evdev: {e}")
            
    def _pynput_listener(self):
        try:
            from pynput import keyboard
        except ImportError:
            return
            
        def on_press(key):
            try:
                if hasattr(key, 'vk'):
                    vk = key.vk
                    key_map = {
                        179: "play_pause",
                        176: "next",
                        177: "prev",
                    }
                    if vk in key_map:
                        self._handle_media_key(key_map[vk])
                elif hasattr(key, 'name'):
                    key_map = {
                        'play_pause': "play_pause",
                        'play': "play",
                        'pause': "pause",
                        'stop': "stop",
                        'next': "next",
                        'previous': "prev",
                        'volume_up': "volume_up",
                        'volume_down': "volume_down",
                        'mute': "mute",
                    }
                    if key.name in key_map:
                        self._handle_media_key(key_map[key.name])
            except Exception as e:
                pass
                
        def on_release(key):
            pass
            
        with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            while self.running:
                time.sleep(0.1)
            listener.stop()
            
    def _handle_media_key(self, action):
        if action == "play_pause":
            self.player.send_command({"command": ["cycle", "pause"]})
            print("[Control: Play/Pause]")
        elif action == "play":
            self.player.send_command({"command": ["set", "pause", False]})
            print("[Control: Play]")
        elif action == "pause":
            self.player.send_command({"command": ["set", "pause", True]})
            print("[Control: Pause]")
        elif action == "stop":
            self.player.send_command({"command": ["stop"]})
            print("[Control: Stop]")
        elif action == "next":
            self.player.send_command({"command": ["playlist-next"]})
            print("[Control: Next]")
        elif action == "prev":
            self.player.send_command({"command": ["playlist-prev"]})
            print("[Control: Previous]")
        elif action == "volume_up":
            self.player.send_command({"command": ["add", "volume", 5]})
            print("[Control: Volume +]")
        elif action == "volume_down":
            self.player.send_command({"command": ["add", "volume", -5]})
            print("[Control: Volume -]")
        elif action == "mute":
            self.player.send_command({"command": ["cycle", "mute"]})
            print("[Control: Mute]")

class MpvPlayer:
    def __init__(self):
        # Limpiar socket anterior si existe
        if os.path.exists(SOCKET_PATH):
            os.remove(SOCKET_PATH)
            
        # Iniciar MPV como proceso independiente
        # --idle: no cerrar cuando acabe la playlist
        # --no-video: solo audio (ahorra recursos)
        # --input-ipc-server: para controlarlo
        # --ytdl-format: asegurar audio
        self.process = subprocess.Popen([
            "mpv",
            "--idle",
            "--no-video",
            f"--input-ipc-server={SOCKET_PATH}",
            "--ytdl-format=bestaudio/best"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Esperar a que el socket esté listo
        retries = 20
        while not os.path.exists(SOCKET_PATH) and retries > 0:
            time.sleep(0.1)
            retries -= 1
            
        if not os.path.exists(SOCKET_PATH):
            raise Exception("No se pudo iniciar MPV IPC socket")
            
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(SOCKET_PATH)
        self.current_video_id = None
        
    def send_command(self, command):
        """Envía un comando JSON a MPV."""
        try:
            data = json.dumps(command) + "\n"
            self.sock.sendall(data.encode('utf-8'))
            # Leer respuesta (básico, para vaciar buffer)
            self.sock.setblocking(False)
            try:
                self.sock.recv(4096)
            except BlockingIOError:
                pass
            self.sock.setblocking(True)
        except Exception as e:
            print(f"Error enviando comando MPV: {e}")

    def add_to_playlist(self, url, title=None):
        cmd = {"command": ["loadfile", url, "append"]}
        self.send_command(cmd)

    def get_property(self, prop):
        cmd = {"command": ["get_property", prop]}
        try:
            self.sock.sendall((json.dumps(cmd) + "\n").encode())
            data = self.sock.recv(4096).decode()
            # La respuesta puede ser múltiples líneas JSON
            for line in data.split('\n'):
                if not line: continue
                try:
                    resp = json.loads(line)
                    if resp.get('error') == 'success':
                        return resp.get('data')
                except json.JSONDecodeError:
                    pass
        except Exception as e:
            print(f"Error en get_property({prop}): {e}")
        return None
        
    def close(self):
        try:
            self.process.terminate()
            self.process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self.process.kill()
        except Exception as e:
            print(f"Error cerrando MPV: {e}")
            
        if os.path.exists(SOCKET_PATH):
            try:
                os.remove(SOCKET_PATH)
            except OSError:
                pass

def analyze_music_prompt(prompt):
    """Analiza un prompt de texto para extraer intención musical."""
    prompt_lower = prompt.lower()
    
    # Mapeo de palabras clave a géneros y moods
    mood_keywords = {
        'chill': ['relajante', 'tranquilo', 'chill', 'calma', 'suave'],
        'energize': ['energético', 'activo', 'motivador', 'enérgico', 'energía'],
        'focus': ['concentración', 'estudiar', 'trabajar', 'focus', 'concentrar'],
        'workout': ['ejercicio', 'gym', 'deporte', 'entrenar', 'correr'],
        'party': ['fiesta', 'party', 'bailar', 'celebrar'],
        'sad': ['triste', 'melancólico', 'sad', 'depresivo'],
        'romance': ['romántico', 'amor', 'romance'],
        'sleep': ['dormir', 'sueño', 'descansar']
    }
    
    genre_keywords = {
        'rock': ['rock', 'rock en español'],
        'pop': ['pop', 'pop latino'],
        'jazz': ['jazz'],
        'hip-hop': ['hip-hop', 'rap', 'hip hop'],
        'electronic': ['electrónica', 'edm', 'techno', 'house', 'electronic'],
        'classical': ['clásica', 'classical', 'orquesta'],
        'reggae': ['reggae', 'ska'],
        'metal': ['metal', 'heavy']
    }
    
    # Detectar mood
    detected_mood = None
    for mood, keywords in mood_keywords.items():
        if any(keyword in prompt_lower for keyword in keywords):
            detected_mood = mood
            break
    
    # Detectar género
    detected_genre = None
    for genre, keywords in genre_keywords.items():
        if any(keyword in prompt_lower for keyword in keywords):
            detected_genre = genre
            break
    
    # Construir query de búsqueda
    if detected_mood and detected_genre:
        return f"{detected_mood} {detected_genre}"
    elif detected_mood:
        return detected_mood
    elif detected_genre:
        return detected_genre
    else:
        # Si no se detectó nada, usar el prompt original
        return prompt

def show_mood_categories(yt):
    """Muestra categorías de mood/género disponibles y permite selección."""
    try:
        categories = yt.get_mood_categories()
        
        print("\n=== Categorías Disponibles ===")
        all_options = []
        
        for section, items in categories.items():
            print(f"\n{section}:")
            for idx, item in enumerate(items):
                all_options.append(item)
                print(f"  {len(all_options)}. {item['title']}")
        
        print(f"\n  0. Cancelar y volver")
        
        while True:
            try:
                choice = input("\nSelecciona un número: ").strip()
                if not choice:
                    continue
                    
                choice_num = int(choice)
                
                if choice_num == 0:
                    return None
                    
                if 1 <= choice_num <= len(all_options):
                    selected = all_options[choice_num - 1]
                    print(f"\nSeleccionado: {selected['title']}")
                    return selected
                else:
                    print(f"Por favor, ingresa un número entre 0 y {len(all_options)}")
            except ValueError:
                print("Por favor, ingresa un número válido")
            except KeyboardInterrupt:
                return None
                
    except Exception as e:
        print(f"Error obteniendo categorías: {e}")
        return None

def get_radio_from_mood(yt, mood_params):
    """Obtiene una playlist de radio basada en parámetros de mood."""
    try:
        playlists = yt.get_mood_playlists(mood_params)
        if playlists:
            # Tomar la primera playlist
            first_playlist = playlists[0]
            playlist_id = first_playlist.get('playlistId')
            
            if playlist_id:
                # Obtener contenido de la playlist
                playlist = yt.get_playlist(playlist_id, limit=50)
                return playlist.get('tracks', [])
        return None
    except Exception as e:
        print(f"Error obteniendo radio por mood: {e}")
        return None

def check_dependencies():
    """Verifica que las herramientas del sistema estén instaladas."""
    missing = []
    if not shutil.which("mpv"):
        missing.append("mpv")
    if not shutil.which("notify-send"):
        print("Advertencia: 'notify-send' no encontrado. Las notificaciones de escritorio no funcionarán.")
    
    if "mpv" in missing:
        print("Error crítico: No se encontró 'mpv'.")
        print("Por favor instálalo (ej: sudo apt install mpv).")
        sys.exit(1)

def get_best_thumbnail(thumbnails):
    """Obtiene el thumbnail de mejor calidad de la lista."""
    if not thumbnails or not isinstance(thumbnails, list):
        return None
    
    # Buscar el thumbnail con mayor resolución
    best_thumb = None
    max_height = 0
    
    for thumb in thumbnails:
        if not isinstance(thumb, dict):
            continue
            
        height = thumb.get('height', 0)
        url = thumb.get('url')
        
        if url and height > max_height:
            max_height = height
            best_thumb = url
    
    return best_thumb

def get_youtube_thumbnail(video_id):
    """Obtiene thumbnail directo de YouTube (más confiable)."""
    if not video_id:
        return None
    
    # YouTube thumbnails estándar
    # maxresdefault: 1280x720, sddefault: 640x480, hqdefault: 480x360
    formats = ['maxresdefault', 'sddefault', 'hqdefault', 'mqdefault', 'default']
    
    for fmt in formats:
        url = f"https://img.youtube.com/vi/{video_id}/{fmt}.jpg"
        try:
            response = requests.head(url, timeout=3)
            if response.status_code == 200:
                return url
        except:
            continue
    
    return None

def send_notification(title, artist, video_id, thumb_url=None):
    
    """Descarga thumb y notifica."""
    try:
        # Prioridad: URL del thumbnail de YTMusic > Thumbnail directo de YouTube > Fallback
        final_thumb_url = None
        
        if thumb_url:
            final_thumb_url = thumb_url
        elif video_id:
            final_thumb_url = get_youtube_thumbnail(video_id)
        
        # Descargar imagen
        if final_thumb_url:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                response = requests.get(final_thumb_url, headers=headers, timeout=5)
                if response.status_code == 200:
                    with open(TEMP_THUMB, 'wb') as f:
                        f.write(response.content)
                    icon_arg = TEMP_THUMB
                else:
                    icon_arg = "audio-x-generic"
            except Exception as e:
                print(f"Error descargando thumbnail: {e}")
                icon_arg = "audio-x-generic"
        else:
            icon_arg = "audio-x-generic"
            
        subprocess.run([
            "notify-send",
            "-r", "991122",
            "-i", icon_arg,
            "YouTube Radio",
            f"{title}\n{artist}"
        ], check=False)
    except Exception as e:
        print(f"Error notificación: {e}")

def list_categories_for_rofi(yt):
    """Imprime categorías en formato simple para scripts externos."""
    try:
        categories = yt.get_mood_categories()
        for section, items in categories.items():
            for item in items:
                # Usamos un separador poco común para parsear luego
                print(f"{item['title']} ;; {section} ;; {json.dumps(item['params'])}")
    except Exception as e:
        print(f"Error: {e}")

def main():
    check_dependencies()
    
    # Configurar argumentos
    parser = argparse.ArgumentParser(description="YouTube Music Radio Player")
    parser.add_argument("--mode", choices=['search', 'prompt', 'category', 'list-categories'], help="Modo de operación")
    parser.add_argument("--query", help="Texto de búsqueda o prompt")
    parser.add_argument("--params", help="Parámetros JSON para categorías")
    args = parser.parse_args()

    yt = YTMusic()
    
    # Modo listado para Rofi (solo imprime y sale)
    if args.mode == 'list-categories':
        list_categories_for_rofi(yt)
        return

    tracks = []
    video_id = None
    
    # Lógica de selección (Interactiva vs Argumentos)
    if args.mode:
        # --- MODO NO INTERACTIVO (ARGS) ---
        print(f"=== Radio YouTube Music (Background: {args.mode}) ===")
        
        if args.mode == 'search':
            if not args.query:
                print("Error: --query requerido para search")
                return
            print(f"Buscando '{args.query}'...")
            results = yt.search(args.query, filter="songs")
            if not results:
                results = yt.search(args.query, filter="videos")
            if results:
                first = results[0]
                video_id = first['videoId']
                print(f"Seleccionado: {first['title']}")
                
        elif args.mode == 'prompt':
            if not args.query:
                print("Error: --query requerido para prompt")
                return
            analyzed = analyze_music_prompt(args.query)
            print(f"Interpretado: {analyzed}")
            results = yt.search(analyzed, filter="songs")
            if not results:
                results = yt.search(analyzed, filter="videos")
            if results:
                first = results[0]
                video_id = first['videoId']
                
        elif args.mode == 'category':
            if not args.params:
                # Si viene solo el título en query, intentamos buscarlo (fallback)
                print("Error: --params requerido para category")
                return
            print("Cargando categoría...")
            mood_tracks = get_radio_from_mood(yt, args.params)
            if mood_tracks:
                tracks = mood_tracks
            
    else:
        # --- MODO INTERACTIVO (CLI ORIGINAL) ---
        print("=== Radio YouTube Music (MPV IPC) ===")
        print("\n¿Cómo quieres buscar música?")
        print("1. Búsqueda por artista/canción (tradicional)")
        print("2. Describir con palabras el tipo de música (ej: 'música relajante para estudiar')")
        print("3. Explorar categorías de mood/género")
        
        mode_choice = input("\nSelecciona una opción (1-3): ").strip()
        
        if mode_choice == "1":
            query = input("¿Qué grupo o estilo quieres escuchar?: ").strip()
            if not query: return
            print(f"Buscando '{query}'...")
            results = yt.search(query, filter="songs")
            if not results: results = yt.search(query, filter="videos")
            if not results:
                print("No se encontró nada.")
                return
            first = results[0]
            video_id = first['videoId']
            print(f"Iniciando con: {first['title']}")
            
        elif mode_choice == "2":
            prompt = input("Describe el tipo de música: ").strip()
            if not prompt: return
            analyzed_query = analyze_music_prompt(prompt)
            print(f"\nInterpretando como: '{analyzed_query}'")
            results = yt.search(analyzed_query, filter="songs")
            if not results: results = yt.search(analyzed_query, filter="videos")
            if not results:
                print("No se encontró nada.")
                return
            first = results[0]
            video_id = first['videoId']
            
        elif mode_choice == "3":
            selected_category = show_mood_categories(yt)
            if not selected_category: return
            print(f"\nObteniendo playlists de '{selected_category['title']}'...")
            mood_tracks = get_radio_from_mood(yt, selected_category['params'])
            if mood_tracks:
                tracks = mood_tracks
            else:
                results = yt.search(selected_category['title'], filter="songs")
                if results:
                    video_id = results[0]['videoId']
        else:
            print("Opción no válida.")
            return

    # Validar si tenemos algo para reproducir
    if not tracks and not video_id:
        print("No se pudo obtener música. Saliendo.")
        return

    player = None
    media_controller = None
    try:
        # Iniciar player
        player = MpvPlayer()
        
        # Iniciar control de teclas multimedia
        media_controller = MediaKeysController(player)
        media_controller.start()
        
        # Si no obtuvimos tracks del modo categorías, obtener watch playlist
        if not tracks and video_id:
            watch_playlist = yt.get_watch_playlist(videoId=video_id, limit=50)
            tracks = watch_playlist.get('tracks', [])
        
        # Mapa para guardar metadatos {videoId: track_obj}
        # MPV nos dirá qué videoId está tocando (filename o media-title)
        # pero es mejor llevar el control nosotros.
        track_map = {}
        
        # Cargar cola inicial
        if not isinstance(tracks, list):
            print("Error: formato de tracks inesperado")
            return

        print(f"Cargando {len(tracks)} canciones a la cola...")

        for track in tracks:
            if not isinstance(track, dict): continue
            
            vid = track.get('videoId')
            title = track.get('title')
            
            # Manejar None values
            if not vid:
                continue
                
            # Asegurar que vid y title sean usables como claves (strings)
            if not isinstance(vid, str):
                vid = str(vid)
            
            if title is None:
                title = "Unknown"
            elif not isinstance(title, str):
                # A veces puede venir como objeto complejo o lista, aunque es raro en esta llamada
                title = str(title)
            
            # Construir URL completa
            url = f"https://www.youtube.com/watch?v={vid}"
            
            # Guardar metadatos para uso posterior
            track_map[vid] = track
            track_map[title] = track # Por si acaso MPV devuelve título
            
            # Añadir a MPV
            player.add_to_playlist(url)
            
        # Comenzar reproducción (si estaba idle)
        player.send_command({"command": ["playlist-play-index", 0]})
        
        print("Reproduciendo. Controla con teclas multimedia.")
        print("Presiona Ctrl+C para salir.")
        
        # Bucle de monitorización
        last_title = ""
        while True:
            # Obtener título actual o media-title
            curr_title = player.get_property("media-title")
            
            # Si es un dict (metadatos internos de mpv/ytdl aún cargando), ignorar
            if not isinstance(curr_title, str):
                time.sleep(0.5)
                continue
            
            # A veces media-title es la URL si yt-dlp no ha cargado metadata aún
            # O yt-dlp pone el título real del video.
            
            if curr_title and curr_title != last_title:
                # Ha cambiado la canción
                last_title = curr_title
                
                # Intentar buscar metadatos enriquecidos en nuestro mapa
                # El título de MPV puede diferir ligeramente del de YTMusic
                # Buscamos coincidencia aproximada o directa
                found_track = None
                
                # Intento 1: Coincidencia exacta de título
                if curr_title in track_map:
                    found_track = track_map[curr_title]
                else:
                    # Intento 2: Buscar por substring
                    for k, v in track_map.items():
                        if k in curr_title or curr_title in k:
                            found_track = v
                            break
                
                display_title = curr_title
                display_artist = "Radio"
                video_id_track = None
                thumb_url = None
                
                if found_track:
                    display_title = found_track.get('title', curr_title)
                    artists = found_track.get('artists', [])
                    if artists:
                        display_artist = artists[0]['name']
                    
                    video_id_track = found_track.get('videoId')
                    if found_track.get('thumbnails'):
                        thumb_url = get_best_thumbnail(found_track['thumbnails'])
                
                print(f"\n>> {display_title} - {display_artist}")
                
                # Notificación en hilo aparte para no bloquear
                threading.Thread(target=send_notification, args=(display_title, display_artist, video_id_track, thumb_url)).start()
                
            time.sleep(1)
            
            # Verificar si MPV sigue vivo
            if player.process.poll() is not None:
                print("MPV se cerró inesperadamente.")
                break

    except KeyboardInterrupt:
        print("\nSaliendo...")
        if media_controller:
            media_controller.stop()
        if player:
            player.close()
    except Exception as e:
        print(f"Error: {e}")
        if media_controller:
            media_controller.stop()
        if player:
            player.close()

if __name__ == "__main__":
    main()
