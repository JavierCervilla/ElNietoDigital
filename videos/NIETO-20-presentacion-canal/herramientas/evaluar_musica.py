#!/usr/bin/env python3
"""Elige entre candidatas de música a imagen con una métrica, no de oído.

Para cada candidata mide el nivel medio (dB) de cada sección del plan (las fronteras salen de los cues) y lo
compara con el nivel objetivo que pide el montaje (SECCIONES de generar_sonido.py): correlación de Pearson
entre ambos perfiles. Además vigila el arranque: la primera sección tiene que sonar (el acorde de «Respire.»),
no quedarse en silencio.

Uso:  python3 herramientas/evaluar_musica.py [ficheros…]   (por defecto: build/candidatas/musica-calma-*.mp3)
"""
import json
import pathlib
import subprocess
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from banda_sonora import calcular_cues  # noqa: E402
from generar_sonido import SECCIONES  # noqa: E402

RAIZ = pathlib.Path(__file__).resolve().parent.parent
SR = 22050


def niveles(ruta, fronteras):
    x = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", str(ruta), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                                     capture_output=True, check=True).stdout, np.float32)
    out = []
    for a, b in zip(fronteras[:-1], fronteras[1:]):
        tramo = x[int(a * SR):int(b * SR)]
        out.append(20 * np.log10(np.sqrt(np.mean(tramo ** 2)) + 1e-9) if len(tramo) else -120.0)
    arranque = 20 * np.log10(np.sqrt(np.mean(x[: int(0.8 * SR)] ** 2)) + 1e-9)
    return np.array(out), arranque


def main():
    c = calcular_cues(json.loads((RAIZ / "voz" / "tiempos.json").read_text(encoding="utf-8")))
    r = c["respire"]
    fronteras = [c[s[1]] - r for s in SECCIONES] + [c["fin"] - r]
    objetivo = np.array([s[6] for s in SECCIONES], float)
    rutas = [pathlib.Path(a) for a in sys.argv[1:]] or sorted((RAIZ / "build" / "candidatas").glob("musica-calma-*.mp3"))
    print("candidata".ljust(30), "corr", "arranque", " ".join(f"{s[0][:8]:>8}" for s in SECCIONES))
    print("objetivo".ljust(30), "    ", "        ", " ".join(f"{v:8.0f}" for v in objetivo))
    for ruta in rutas:
        nv, arranque = niveles(ruta, fronteras)
        rel = nv - nv.mean()
        corr = float(np.corrcoef(rel, objetivo)[0, 1])
        print(ruta.name.ljust(30), f"{corr:+.2f}", f"{arranque:6.1f}dB", " ".join(f"{v:8.1f}" for v in rel))


if __name__ == "__main__":
    main()
