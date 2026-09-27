#!/usr/bin/env python3
"""Control de calidad de la locución: Whisper (local) transcribe cada frase y se compara con el guion.

Una voz sintética puede comerse o cambiar una palabra ("no morde" por "no muerde"). Aquí no se escucha a ojo:
cada frase se corta de la toma por su tramo de alineación, se transcribe y se cuentan las palabras que no
casan. Sale 1 si alguna frase tiene diferencias: se repite la toma con `generar_voz.py --semilla <otra>`.

Requiere `pip install faster-whisper` (modelo `small`, corre en CPU). No envía nada a la red salvo la
descarga inicial del modelo.
Uso:  python3 herramientas/verificar_voz.py
"""
import json
import pathlib
import re
import subprocess
import sys
import tempfile
import unicodedata

from faster_whisper import WhisperModel

RAIZ = pathlib.Path(__file__).resolve().parent.parent


def palabras(texto):
    t = unicodedata.normalize("NFD", texto.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.findall(r"[a-zñ0-9]+", t)


def distancia(a, b):
    """Distancia de edición por palabras (Levenshtein)."""
    fila = list(range(len(b) + 1))
    for i, pa in enumerate(a, 1):
        previa, fila[0] = fila[0], i
        for j, pb in enumerate(b, 1):
            previa, fila[j] = fila[j], min(fila[j] + 1, fila[j - 1] + 1, previa + (pa != pb))
    return fila[-1]


def main():
    guion = json.loads((RAIZ / "voz" / "guion.json").read_text(encoding="utf-8"))
    toma = json.loads((RAIZ / "voz" / "toma.json").read_text(encoding="utf-8"))
    tramos = {t["id"]: t for t in toma["lineas"]}
    modelo = WhisperModel("small", device="cpu", compute_type="int8")
    fallos = 0
    with tempfile.TemporaryDirectory() as tmp:
        for linea in guion["lineas"]:
            t = tramos[linea["id"]]
            wav = f"{tmp}/{linea['id']}.wav"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(RAIZ / "voz" / "toma.mp3"),
                            "-ss", f"{max(0, t['t0'] - 0.15):.3f}", "-to", f"{t['t1'] + 0.25:.3f}", wav], check=True)
            segmentos, _ = modelo.transcribe(wav, language="es", beam_size=5)
            oido = " ".join(s.text.strip() for s in segmentos)
            d = distancia(palabras(linea["texto"]), palabras(oido))
            fallos += d > 0
            print(f"{'✓' if d == 0 else '✗'} {linea['id']} ({d}) {oido}")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
