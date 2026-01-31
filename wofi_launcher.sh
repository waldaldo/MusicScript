#!/usr/bin/env bash
set -euo pipefail

# Wofi launcher for YouTube Music Radio integrated with Hyprland hotkey
# Flow: Present the same top-level options as radio.py and dispatch to it.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RADIO="${SCRIPT_DIR}/radio.py"

WOFI_CMD="$(command -v wofi || true)"
PY_CMD="$(command -v python3 || true)"

if [ -z "$WOFI_CMD" ]; then
  echo "wofi no encontrado. Instala wofi para usar este lanzador." >&2
  exit 1
fi
if [ -z "$PY_CMD" ]; then
  echo "python3 no disponible." >&2
  exit 1
fi

# Top-level menu (three options)
MENU=$'1) Buscar por artista/canción\n2) Describir con palabras el tipo de música (ej: música relajante para estudiar)\n3) Explorar categorías de mood/género\nSalir'
CHOICE="$(${WOFI_CMD} -dmenu -p 'Radio YouTube Music' <<< "$MENU" 2>/dev/null || true)"
if [ -z "$CHOICE" ]; then
  exit 0
fi

case "$CHOICE" in
  "1) Buscar por artista/canción")
    QUERY="$(${WOFI_CMD} -dmenu -p '¿Qué grupo o estilo quieres escuchar?' </dev/null 2>/dev/null || true)"
    if [ -n "$QUERY" ]; then
      "$PY_CMD" "$RADIO" --mode search --query "$QUERY"
    fi
    ;;
  "2) Describir con palabras el tipo de música (ej: música relajante para estudiar)")
    DESC="$(${WOFI_CMD} -dmenu -p 'Describe el tipo de música' </dev/null 2>/dev/null || true)"
    if [ -n "$DESC" ]; then
      "$PY_CMD" "$RADIO" --mode prompt --query "$DESC"
    fi
    ;;
  "3) Explorar categorías de mood/género")
    OUTPUT="$(${PY_CMD} ${RADIO} --mode list-categories 2>/dev/null || true)"
    if [ -z "$OUTPUT" ]; then
      exit 0
    fi
    SELECTED="$(${WOFI_CMD} -dmenu -p 'Moods / Genres' -i <<< "$OUTPUT" 2>/dev/null || true)"
    if [ -z "$SELECTED" ]; then
      exit 0
    fi
    JSON="$(echo "$SELECTED" | awk -F ';;' '{print $3}' | sed -e 's/^[ \t]*//;s/[ \t]*$//')"
    if [ -n "$JSON" ]; then
      "$PY_CMD" "$RADIO" --mode category --params "$JSON"
    fi
    ;;
  *)
    exit 0
    ;;
esac
