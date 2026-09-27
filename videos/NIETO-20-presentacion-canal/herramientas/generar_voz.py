#!/usr/bin/env python3
"""Genera la locución con ElevenLabs en UNA sola toma, con su alineación por carácter.

Todo el guion va en una única petición a /v1/text-to-speech/{voz}/with-timestamps: una sola interpretación,
con el mismo tono de principio a fin (eleven_v3 no admite `previous_text`/`next_text`, así que pedir frase a
frase daría tonos sueltos). La respuesta se congela tal cual en voz/toma.mp3 y la alineación en voz/toma.json,
con el tramo [t0, t1] de cada frase. Los silencios entre frases no los decide la voz: montar_audio.py corta
cada frase y la coloca donde manda el montaje.

La voz es una fuente NO determinista y de pago: se genera una vez, se revisa (verificar_voz.py) y se congela
en git. Solo sale hacia ElevenLabs el texto del guion.

Uso:  ELEVENLABS_API_KEY=… python3 herramientas/generar_voz.py [--semilla 2020]
"""
import argparse
import base64
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

RAIZ = pathlib.Path(__file__).resolve().parent.parent
GUION = RAIZ / "voz" / "guion.json"
SEPARADOR = "\n\n"


def pedir(voz, texto, semilla):
    cuerpo = {
        "text": texto,
        "model_id": voz["modelo"],
        "language_code": "es",
        "voice_settings": voz["ajustes"],
        "seed": semilla,
    }
    url = (
        f"https://api.elevenlabs.io/v1/text-to-speech/{voz['voice_id']}/with-timestamps"
        f"?output_format={voz['formato']}"
    )
    peticion = urllib.request.Request(
        url,
        data=json.dumps(cuerpo).encode(),
        headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"], "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(peticion, timeout=300) as r:
        return json.load(r)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--semilla", type=int, default=2020)
    args = ap.parse_args()
    if not os.environ.get("ELEVENLABS_API_KEY"):
        sys.exit("falta ELEVENLABS_API_KEY en el entorno")

    guion = json.loads(GUION.read_text(encoding="utf-8"))
    voz, lineas = guion["voz"], guion["lineas"]
    prefijo = f"{voz['direccion']} " if voz.get("direccion") else ""
    texto = prefijo + SEPARADOR.join(l["texto"] for l in lineas)
    try:
        r = pedir(voz, texto, args.semilla)
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code} {e.read()[:300]!r}")

    al = r["alignment"]
    if "".join(al["characters"]) != texto:
        sys.exit("la alineación no reproduce el texto enviado: no puedo situar las frases")
    tramos, pos = [], len(prefijo)
    for l in lineas:
        a, b = pos, pos + len(l["texto"]) - 1  # índices del primer y último carácter de la frase
        tramos.append({"id": l["id"], "t0": al["character_start_times_seconds"][a],
                       "t1": al["character_end_times_seconds"][b], "desde": a - len(prefijo), "hasta": b - len(prefijo)})
        pos = b + 1 + len(SEPARADOR)

    (RAIZ / "voz" / "toma.mp3").write_bytes(base64.b64decode(r["audio_base64"]))
    toma = {
        "semilla": args.semilla,
        "texto": texto[len(prefijo):],
        "caracteres": al["characters"][len(prefijo):],
        "inicio": al["character_start_times_seconds"][len(prefijo):],
        "fin": al["character_end_times_seconds"][len(prefijo):],
        "lineas": tramos,
    }
    (RAIZ / "voz" / "toma.json").write_text(json.dumps(toma, ensure_ascii=False), encoding="utf-8")
    for t in tramos:
        print(f"{t['id']}: {t['t0']:6.2f} → {t['t1']:6.2f} s")


if __name__ == "__main__":
    main()
