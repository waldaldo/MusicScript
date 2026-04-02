#!/usr/bin/env bash
set -euo pipefail

# Lanzador wofi para radio.py

export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RADIO="${SCRIPT_DIR}/radio.py"
WOFI_CMD="/usr/bin/wofi"
PY_CMD="/usr/bin/python3"

MENU=$'1) Buscar por artista/canción\n2) Describir con palabras el tipo de música (ej: música relajante para estudiar)\n3) Explorar categorías de mood/género\nSalir'
CHOICE="$("$WOFI_CMD" -dmenu -p 'Radio YouTube Music' <<< "$MENU" 2>/dev/null || true)"
if [ -z "$CHOICE" ]; then
  exit 0
fi

run_radio() {
    "$PY_CMD" "$RADIO" "$@" &
    disown
}

notify_error() {
    /usr/bin/notify-send "Radio" "$1" -i audio-x-generic 2>/dev/null || true
}

case "$CHOICE" in
  "1) Buscar por artista/canción")
    QUERY="$("$WOFI_CMD" -dmenu -p '¿Qué grupo o estilo quieres escuchar?' </dev/null 2>/dev/null || true)"
    if [ -n "$QUERY" ]; then
      run_radio --mode search --query "$QUERY"
    fi
    ;;
  "2) Describir con palabras el tipo de música (ej: música relajante para estudiar)")
    DESC="$("$WOFI_CMD" -dmenu -p 'Describe el tipo de música' </dev/null 2>/dev/null || true)"
    if [ -n "$DESC" ]; then
      run_radio --mode prompt --query "$DESC"
    fi
    ;;
  "3) Explorar categorías de mood/género")
    OUTPUT="$("$PY_CMD" "$RADIO" --mode list-categories 2>/dev/null || true)"
    if [ -z "$OUTPUT" ]; then
      notify_error "No se pudieron obtener categorías."
      exit 0
    fi
    SELECTED="$("$WOFI_CMD" -dmenu -p 'Moods / Genres' -i <<< "$OUTPUT" 2>/dev/null || true)"
    if [ -z "$SELECTED" ]; then
      exit 0
    fi
    JSON="$(echo "$SELECTED" | awk -F ';;' '{print $3}' | sed -e 's/^[ \t]*//;s/[ \t]*$//')"
    if [ -n "$JSON" ]; then
      run_radio --mode category --params "$JSON"
    fi
    ;;
  *)
    exit 0
    ;;
esac
