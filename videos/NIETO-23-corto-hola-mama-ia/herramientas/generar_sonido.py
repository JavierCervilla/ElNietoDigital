#!/usr/bin/env python3
"""Genera la música y los efectos nuevos con ElevenLabs y los congela en sonido/ con su manifiesto.

La música se compone A IMAGEN con Eleven Music (music_v2_5): un plan con una sección por escena, y la duración
de cada sección sale de los MISMOS cues que mueven la animación (banda_sonora.py → calcular_cues). Dos piezas:
la tensión (del gancho al final de la presión del estafador) y la calma (de «Qué hacer:» al final).

Los efectos que ya existían en NIETO-20 no se vuelven a pedir: `--importar` los copia de
videos/NIETO-20-presentacion-canal/sonido/ con su entrada del manifiesto (misma petición, mismo sha256).

Como la voz, es una fuente NO determinista y de pago: se genera una vez, se revisa y se congela en git.
sonido/fuentes.json guarda la petición exacta de cada fichero y su sha256. Solo salen hacia ElevenLabs las
descripciones de abajo (sin datos personales).

Uso:  python3 herramientas/generar_sonido.py --importar
      ELEVENLABS_API_KEY=… python3 herramientas/generar_sonido.py [--solo tecleo,llamada] [--semilla 2023]
      Música por candidatas: --solo musica-calma --candidata --semilla N (varias veces), y después
      --elegir musica-calma --semilla <la mejor> (congela sin volver a llamar a la API).
"""
import argparse
import hashlib
import json
import os
import pathlib
import shutil
import sys
import urllib.error
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from banda_sonora import calcular_cues  # noqa: E402  (los cues son la única fuente de tiempos)

RAIZ = pathlib.Path(__file__).resolve().parent.parent
SONIDO = RAIZ / "sonido"
NIETO20 = RAIZ.parent / "NIETO-20-presentacion-canal" / "sonido"
FORMATO = "mp3_44100_128"

IMPORTADOS = ["vibra", "ding", "pop", "barrido", "alerta", "sello", "toque", "burbuja", "brillo", "latido"]
# Efectos nuevos: (nombre, descripción, segundos, influencia del texto).
EFECTOS = [
    ("tecleo", "soft quick typing on a smartphone touchscreen keyboard, gentle taps, close and clean, no music", 1.2, 0.6),
    ("llamada", "outgoing phone call ringback tone heard through a smartphone speaker, two long rings, calm", 4.0, 0.6),
]

NO_GLOBAL = ["vocals", "choir", "singing", "humming", "drum kit", "electric guitar", "EDM", "dubstep",
             "aggressive", "loud brass", "sudden loud hits"]
# Tensión: (nombre, desde_cue, hasta_cue, adherencia, estilos sí, estilos no).
TENSION = [
    ("Hook", 0, "escena2", "high",
     ["tense cinematic underscore", "suspenseful", "low pulsing synth bass", "ticking clock pulse", "starts immediately",
      "instrumental", "moderate tempo around 96 bpm"], ["happy", "major key"]),
    ("The chat", "escena2", "al_rato", "high",
     ["quiet suspense", "sparse plucked pizzicato", "low tremolo strings", "curious and uneasy", "restrained"],
     ["loud", "happy", "melody"]),
    ("Pressure", "al_rato", "congela", "medium",
     ["tension builds steadily", "faster ticking", "rising tremolo strings", "anxious", "urgent but not loud"],
     ["beat drop", "drums", "happy", "major key"]),
]
# Calma: desde «Qué hacer:» hasta el final.
CALMA = [
    ("What to do", "escena5", "escena6", "medium",
     ["starts almost silent", "a single low sustained cello note", "suspended stillness", "no rhythm",
      "warm cinematic documentary underscore", "instrumental", "moderate tempo around 84 bpm"],
     ["percussion", "pizzicato", "bright", "loud"]),
    ("Call the real number", "escena6", "escena7", "medium",
     ["warm soft felt piano enters", "reassuring", "gentle string pad", "relief", "major key"], ["drums"]),
    ("The rule", "escena7", "escena8", "high",
     ["steady gentle pulse", "soft pizzicato and piano", "clear and confident"], ["drums"]),
    ("Remember", "escena8", "escena9", "high",
     ["calm and warm", "piano and strings", "patient"], ["drums", "riser"]),
    ("Share and goodbye", "escena9", "fin", "medium",
     ["warm uplifting resolution", "piano and strings together", "gentle final cadence", "final chord ringing out"],
     ["drums", "abrupt ending"]),
]


def pedir(ruta, cuerpo):
    peticion = urllib.request.Request(
        f"https://api.elevenlabs.io{ruta}?output_format={FORMATO}",
        data=json.dumps(cuerpo).encode(),
        headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"], "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(peticion, timeout=600) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        sys.exit(f"{ruta}: HTTP {e.code} {e.read()[:300]!r}")


def plan(secciones, c):
    """Plan de music_v2_5: una lista de chunks; los estilos del primero fijan el tono global."""
    chunks = []
    for k, (nombre, desde, hasta, adherencia, si, no) in enumerate(secciones):
        t0 = c[desde] if isinstance(desde, str) else desde
        t1 = c[hasta]
        if k == len(secciones) - 1:
            t1 += 1.0 if hasta == "fin" else 0.4  # margen SOLO al final: en medio desplazaría las secciones siguientes
        chunks.append({
            "text": f"[{nombre}] {{instrumental}}",
            "duration_ms": int(round((t1 - t0) * 1000)),
            "positive_styles": si,
            "negative_styles": NO_GLOBAL + no,
            "context_adherence": adherencia,
        })
    return {"chunks": chunks}


def importar(manifiesto):
    origen = json.loads((NIETO20 / "fuentes.json").read_text(encoding="utf-8"))
    for n in IMPORTADOS:
        shutil.copyfile(NIETO20 / f"{n}.mp3", SONIDO / f"{n}.mp3")
        manifiesto[n] = dict(origen[n], origen="videos/NIETO-20-presentacion-canal/sonido (NIETO-21)")
        print(f"{n}: importado de NIETO-20")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo", help="nombres separados por comas (p. ej. tecleo,musica-calma)")
    ap.add_argument("--semilla", type=int, default=2023)
    ap.add_argument("--importar", action="store_true", help="copia los efectos de NIETO-20 (sin red)")
    ap.add_argument("--candidata", action="store_true",
                    help="escribe en build/candidatas/<nombre>-s<semilla>.mp3 y no toca sonido/ ni el manifiesto")
    ap.add_argument("--elegir", help="congela build/candidatas/<nombre>-s<semilla>.mp3 en sonido/ (sin red)")
    args = ap.parse_args()
    SONIDO.mkdir(exist_ok=True)
    manifiesto_ruta = SONIDO / "fuentes.json"
    manifiesto = json.loads(manifiesto_ruta.read_text(encoding="utf-8")) if manifiesto_ruta.exists() else {}
    if args.importar:
        importar(manifiesto)
        manifiesto_ruta.write_text(json.dumps(manifiesto, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return
    if not args.elegir and not os.environ.get("ELEVENLABS_API_KEY"):
        sys.exit("falta ELEVENLABS_API_KEY en el entorno")
    solo = set(args.solo.split(",")) if args.solo else None

    c = calcular_cues(json.loads((RAIZ / "voz" / "tiempos.json").read_text(encoding="utf-8")))
    encargos = [(f"musica-{n}", "/v1/music", {"composition_plan": plan(s, c), "model_id": "music_v2_5", "seed": args.semilla})
                for n, s in (("tension", TENSION), ("calma", CALMA))]
    encargos += [(n, "/v1/sound-generation", {"text": t, "duration_seconds": d, "prompt_influence": p,
                                              "model_id": "eleven_text_to_sound_v2"}) for n, t, d, p in EFECTOS]
    candidatas = RAIZ / "build" / "candidatas"
    for nombre, ruta, cuerpo in encargos:
        if args.elegir:
            if nombre != args.elegir:
                continue
            audio = (candidatas / f"{nombre}-s{args.semilla}.mp3").read_bytes()
        else:
            if solo and nombre not in solo:
                continue
            audio = pedir(ruta, cuerpo)
            if args.candidata:
                candidatas.mkdir(parents=True, exist_ok=True)
                (candidatas / f"{nombre}-s{args.semilla}.mp3").write_bytes(audio)
                print(f"candidata {nombre}-s{args.semilla}: {len(audio) // 1024} KB")
                continue
        (SONIDO / f"{nombre}.mp3").write_bytes(audio)
        manifiesto[nombre] = {"endpoint": ruta, "peticion": cuerpo, "formato": FORMATO,
                              "sha256": hashlib.sha256(audio).hexdigest()}
        print(f"{nombre}: {len(audio) // 1024} KB")
    manifiesto_ruta.write_text(json.dumps(manifiesto, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
