#!/usr/bin/env python3
"""Genera la música y los efectos con ElevenLabs y los congela en sonido/ con su manifiesto.

La música se compone A IMAGEN con Eleven Music (music_v2_5): un plan de composición con una sección por
escena, y la duración de cada sección sale de los MISMOS cues que mueven la animación (banda_sonora.py →
calcular_cues), así que los cambios de la música caen donde cambia la imagen. music_v2_5 respeta siempre la
duración de cada sección.

Como la voz, es una fuente NO determinista y de pago: se genera una vez, se revisa y se congela en git.
sonido/fuentes.json guarda la petición exacta de cada fichero y su sha256. Solo salen hacia ElevenLabs las
descripciones de abajo (sin datos personales).

Uso:  ELEVENLABS_API_KEY=… python3 herramientas/generar_sonido.py [--solo latido,ding] [--semilla 2020]
      Música por candidatas: --solo musica-calma --candidata --semilla N (varias veces), evaluar_musica.py,
      y después --elegir musica-calma --semilla <la mejor> (congela sin volver a llamar a la API).
"""
import argparse
import hashlib
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from banda_sonora import calcular_cues  # noqa: E402  (los cues son la única fuente de tiempos)

RAIZ = pathlib.Path(__file__).resolve().parent.parent
SONIDO = RAIZ / "sonido"
FORMATO = "mp3_44100_128"

# Efectos: (nombre, descripción, segundos, influencia del texto).
EFECTOS = [
    ("vibra", "smartphone vibrating on a wooden table, short double buzz, close and clean", 0.8, 0.6),
    ("ding", "soft pleasant smartphone message notification chime, two gentle tones, clean", 1.0, 0.6),
    ("pop", "soft subtle bubble pop, user interface sound, short and clean", 0.5, 0.6),
    ("barrido", "soft airy whoosh transition, subtle and clean, no impact", 1.0, 0.6),
    ("respiro", "gentle reverse swell rising into silence, soft airy breath, calm", 1.4, 0.5),
    ("latido", "slow muffled human heartbeat that gradually speeds up, anxious, close, no music", 8.0, 0.6),
    ("alerta", "short friendly warning alert chime, two descending notes, clear but not harsh", 1.0, 0.6),
    ("sello", "rubber stamp slammed hard on paper on a wooden desk, single thud", 0.6, 0.6),
    ("toque", "single soft tap on a glass smartphone touchscreen, subtle click", 0.5, 0.6),
    ("burbuja", "soft glass bubble pop, bright and gentle, short user interface blip", 0.5, 0.6),
    ("brillo", "magical soft sparkle chime, short gentle twinkle, warm", 1.5, 0.5),
]

MUSICA_GLOBAL_SI = [
    "warm cinematic documentary underscore", "soft felt piano", "gentle string ensemble", "reassuring",
    "hopeful", "patient", "instrumental", "background music under a spoken voice", "moderate tempo around 84 bpm",
]
MUSICA_GLOBAL_NO = [
    "vocals", "choir", "singing", "humming", "drum kit", "heavy percussion", "electric guitar", "EDM",
    "aggressive", "loud brass", "sudden loud hits",
]
# Una sección por escena, desde «Respire.» al final: (nombre, desde_cue, hasta_cue, adherencia al contexto,
# estilos sí, estilos no, nivel objetivo en dB relativo). La adherencia baja a «medium» donde la música tiene que
# CAMBIAR (alerta, confesión, cierre): con «high» el modelo prioriza la continuidad y sale un pulso uniforme
# (medido en la primera toma: la confesión quedó la sección más fuerte). El nivel objetivo no se envía: lo usa
# evaluar_musica.py para elegir entre candidatas.
SECCIONES = [
    ("Breath", "respire", "escena3", "high",
     ["starts immediately with a warm sustained major chord", "soft piano and string pad swelling", "calm exhale"],
     ["silence", "fade in", "percussion", "rhythm"], -3),
    ("What it is", "escena3", "escena4", "high",
     ["warm felt piano motif", "light strings enter", "clear and simple", "steady tempo"], ["percussion"], -2),
    ("What you will learn", "escena4", "escena5", "high",
     ["soft pizzicato pulse", "light plucked rhythm", "optimistic", "gentle forward motion"], ["drums"], 0),
    ("One thing, step by step", "escena5", "escena6", "high",
     ["steady gentle groove", "piano and pizzicato", "friendly and patient"], ["drums"], 0),
    ("Scam alert", "escena6", "escena7", "medium",
     ["sudden drop in energy", "only a low sustained cello note and sparse low piano", "suspenseful but calm", "quiet"],
     ["pizzicato", "rhythm", "bright", "happy", "loud"], -8),
    ("Nobody left behind", "escena7", "escena8", "medium",
     ["the gentle rhythm returns", "warm uplifting strings", "hopeful build"], ["drums", "riser"], 0),
    ("The voice is AI", "escena8", "escena9", "medium",
     ["almost silent", "a single soft sustained piano chord", "very quiet and intimate", "no rhythm"],
     ["strings", "percussion", "pizzicato", "riser", "cymbal swell", "crescendo", "build-up"], -12),
    ("Subscribe and goodbye", "escena9", "fin", "medium",
     ["warm full resolution", "piano and strings together", "gentle final cadence", "final chord ringing out"],
     ["drums", "abrupt ending"], -1),
]
TENSION = {"chunks": [{
    "text": "[Noise and fear] {instrumental}",
    "duration_ms": 8000,
    "positive_styles": ["tense ambient underscore", "uneasy and anxious", "low droning synth",
                        "high tremolo strings slowly rising", "ticking pulse", "building anxiety", "instrumental"],
    "negative_styles": ["vocals", "melody", "drums", "happy", "major key", "beat drop", "loud hits"],
}]}


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


def plan_calma(c):
    """Formato de plan de music_v2/v2_5: una lista de chunks; los estilos del primero fijan el tono global."""
    chunks = []
    for k, (nombre, desde, hasta, adherencia, si, no, _nivel) in enumerate(SECCIONES):
        fin = c[hasta] + (1.0 if hasta == "fin" else 0.0)  # un segundo de cola para cortar con fundido
        chunks.append({
            "text": f"[{nombre}] {{instrumental}}",
            "duration_ms": int(round((fin - c[desde]) * 1000)),
            "positive_styles": (MUSICA_GLOBAL_SI if k == 0 else []) + si,
            "negative_styles": MUSICA_GLOBAL_NO + no,
            "context_adherence": adherencia,
        })
    return {"chunks": chunks}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo", help="nombres separados por comas (p. ej. latido,musica-calma)")
    ap.add_argument("--semilla", type=int, default=2020)
    ap.add_argument("--candidata", action="store_true",
                    help="escribe en build/candidatas/<nombre>-s<semilla>.mp3 y no toca sonido/ ni el manifiesto")
    ap.add_argument("--elegir", help="congela build/candidatas/<nombre>-s<semilla>.mp3 en sonido/ (sin red)")
    args = ap.parse_args()
    if not args.elegir and not os.environ.get("ELEVENLABS_API_KEY"):
        sys.exit("falta ELEVENLABS_API_KEY en el entorno")
    solo = set(args.solo.split(",")) if args.solo else None

    tiempos = json.loads((RAIZ / "voz" / "tiempos.json").read_text(encoding="utf-8"))
    c = calcular_cues(tiempos)
    SONIDO.mkdir(exist_ok=True)
    manifiesto_ruta = SONIDO / "fuentes.json"
    manifiesto = json.loads(manifiesto_ruta.read_text(encoding="utf-8")) if manifiesto_ruta.exists() else {}

    encargos = [(f"musica-{n}", "/v1/music", {"composition_plan": plan, "model_id": "music_v2_5", "seed": args.semilla})
                for n, plan in (("tension", TENSION), ("calma", plan_calma(c)))]
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
