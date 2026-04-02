#!/usr/bin/env bash
set -euo pipefail

SOCKET="/tmp/mpv_radio_socket"

if [ ! -S "$SOCKET" ]; then
    notify-send "Radio" "No hay ninguna radio activa." -i audio-x-generic
    exit 0
fi

send() {
    echo "$1" | socat - "$SOCKET" > /dev/null 2>&1
}

MENU=$'⏯  Play / Pause\n⏭  Siguiente\n⏮  Anterior\n🔊  Volumen +\n🔉  Volumen -\n⏹  Detener'

CHOICE="$(wofi -dmenu -p 'Radio - Controles' <<< "$MENU" 2>/dev/null || true)"

case "$CHOICE" in
    "⏯  Play / Pause") send '{"command":["cycle","pause"]}' ;;
    "⏭  Siguiente")    send '{"command":["playlist-next"]}' ;;
    "⏮  Anterior")     send '{"command":["playlist-prev"]}' ;;
    "🔊  Volumen +")    send '{"command":["add","volume",5]}' ;;
    "🔉  Volumen -")    send '{"command":["add","volume",-5]}' ;;
    "⏹  Detener")      send '{"command":["stop"]}' ;;
esac
