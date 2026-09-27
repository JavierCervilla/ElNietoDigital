#!/usr/bin/env bash
# Reconstruye todo lo que se deriva de la locución congelada (voz/toma.mp3 + voz/toma.json):
# tiempos de cada palabra (tiempos.js), cues de pantalla (cues.js), música, efectos y la mezcla final
# (audio/banda-sonora.mp3). Determinista y sin red: NO llama a ElevenLabs (eso es generar_voz.py).
# Requiere: python3 con numpy, scipy y praat-parselmouth (PSOLA), y ffmpeg.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 herramientas/montar_voz.py
python3 herramientas/banda_sonora.py
