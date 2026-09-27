#!/usr/bin/env python3
"""Monta la pista de voz a partir de la toma congelada y emite los tiempos de todo el vídeo.

Antes de nada, afina la alineación contra el audio. La de ElevenLabs tiene dos sesgos medidos en esta toma:
reparte cada pausa entre las dos palabras que la rodean (adelanta hasta 0,5 s la palabra de después) y deriva
≈ 0,3 % (−10 ms al principio, −127 ms al final). Se detectan las pausas REALES de la toma, se emparejan con
los huecos de la alineación, se ajusta una recta tiempo_real = a·t + b sobre esas parejas y cada borde de
pausa se engancha a su silencio real.

Por cada frase del guion (su tramo [t0, t1] de voz/toma.json):
  1. la corta de la toma con un pequeño margen,
  2. le añade «respiros» de silencio tras la puntuación interior (coma, dos puntos, puntos suspensivos…),
     cortando en el hueco entre palabras que da la alineación,
  3. la estira con Rubber Band (`tempo` < 1 ralentiza sin cambiar el tono ni los formantes),
  4. la coloca en la línea de tiempo tras el silencio `pausa_antes` que marca el montaje.

La alineación viaja con cada transformación, así que cada palabra sabe su tiempo final. Salidas:
  - build/voz.wav              pista de voz montada (intermedia, no se versiona)
  - voz/tiempos.json           frases, palabras con sus tiempos, envolvente por fotograma y duración
  - tiempos.js                 lo mismo para la composición (window.NIETO_TIEMPOS), sin fetch en el render

Determinista: misma toma + mismo guion → mismos tiempos y mismo audio.
Uso:  python3 herramientas/montar_voz.py
"""
import json
import pathlib
import subprocess
import tempfile

import numpy as np

RAIZ = pathlib.Path(__file__).resolve().parent.parent
SR = 44100
FUNDIDO = int(0.006 * SR)  # 6 ms: evita el clic al abrir un respiro


def leer_audio(ruta):
    crudo = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(ruta), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
        capture_output=True, check=True,
    ).stdout
    return np.frombuffer(crudo, np.float32).copy()


def escribir_wav(ruta, x):
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", str(ruta)],
        input=x.astype(np.float32).tobytes(), check=True,
    )


def estirar(x, tempo):
    """Rubber Band vía ffmpeg: tempo sin tocar el tono, formantes preservados, detector suave (voz)."""
    with tempfile.TemporaryDirectory() as tmp:
        escribir_wav(f"{tmp}/a.wav", x)
        filtro = f"rubberband=tempo={tempo}:formant=preserved:pitchq=quality:detector=soft:transients=smooth"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{tmp}/a.wav", "-af", filtro, f"{tmp}/b.wav"], check=True)
        return leer_audio(f"{tmp}/b.wav")


def fundir(x, n, entrada):
    n = min(n, len(x))
    rampa = np.linspace(0, 1, n) if entrada else np.linspace(1, 0, n)
    if entrada:
        x[:n] *= rampa
    else:
        x[len(x) - n:] *= rampa
    return x


UMBRAL_DB = -45  # voz frente a un fondo de ≈ −71 dB en la toma
PASO_DB = 0.005


def nivel_db(x):
    n = int(PASO_DB * SR)
    tramos = x[: len(x) // n * n].reshape(-1, n)
    return 20 * np.log10(np.sqrt(np.mean(tramos ** 2, axis=1)) + 1e-9)


def afinar(al, db):
    """Corrige deriva y sesgo de pausas de la alineación usando los silencios reales de la toma."""
    chars, ini, fin = al["caracteres"], np.array(al["inicio"]), np.array(al["fin"])
    sonoro = db > UMBRAL_DB
    sonoro = sonoro & np.concatenate([sonoro[1:], [False]])  # dos pasos seguidos: ignora chasquidos sueltos
    silencios, desde = [], None
    for k, v in enumerate(np.append(sonoro, True)):
        if not v and desde is None:
            desde = k
        elif v and desde is not None:
            if (k - desde) * PASO_DB >= 0.06:
                silencios.append((desde * PASO_DB, k * PASO_DB))
            desde = None
    voz = np.flatnonzero(sonoro)
    primero, ultimo = voz[0] * PASO_DB, (voz[-1] + 1) * PASO_DB

    letras = [k for k, c in enumerate(chars) if c.isalnum()]
    palabras, actual = [], []
    for k in letras:
        if actual and any(not chars[j].isalnum() for j in range(actual[-1] + 1, k)):
            palabras.append(actual)
            actual = []
        actual.append(k)
    palabras.append(actual)

    # Huecos de la alineación que pueden ser pausa (hay puntuación o ≥ 40 ms) → silencio real más cercano.
    huecos = []
    for i in range(len(palabras) - 1):
        a, b = palabras[i][-1], palabras[i + 1][0]
        puntuado = any(c in ",.:;…?!" for c in chars[a + 1:b])
        if puntuado or ini[b] - fin[a] >= 0.04:
            huecos.append((i, (fin[a] + ini[b]) / 2))
    parejas, usados = {}, set()
    for d, i, s in sorted((abs((s0 + s1) / 2 - c), i, (s0, s1)) for i, c in huecos for s0, s1 in silencios):
        if d < 0.6 and i not in parejas and s not in usados:
            parejas[i] = s
            usados.add(s)

    # Deriva: recta por mínimos cuadrados entre centros de hueco (alineación) y de silencio (real).
    x = np.array([c for i, c in huecos if i in parejas])
    y = np.array([sum(parejas[i]) / 2 for i, c in huecos if i in parejas])
    a_, b_ = np.polyfit(x, y, 1) if len(x) >= 2 else (1.0, 0.0)
    ini, fin = ini * a_ + b_, fin * a_ + b_

    for i, (s0, s1) in parejas.items():
        izq, der = palabras[i], palabras[i + 1]
        for j in izq:
            fin[j] = min(fin[j], s0)
            ini[j] = min(ini[j], fin[j])
        fin[izq[-1]] = s0
        for j in der:
            ini[j] = max(ini[j], s1)
            fin[j] = max(fin[j], ini[j])
        ini[der[0]] = s1
    ini[palabras[0][0]] = primero
    fin[palabras[-1][-1]] = ultimo
    print(f"alineación afinada: deriva a={a_:.5f} b={b_ * 1000:+.0f} ms, {len(parejas)}/{len(huecos)} pausas enganchadas")
    return {**al, "inicio": ini.tolist(), "fin": fin.tolist()}


def tramo_afinado(al, tramo):
    a, b = tramo["desde"], tramo["hasta"]
    letras = [k for k in range(a, b + 1) if al["caracteres"][k].isalnum()]
    return {**tramo, "t0": al["inicio"][letras[0]], "t1": al["fin"][letras[-1]]}


def montar_frase(toma, al, tramo, limites, respiros, tempo):
    """Devuelve (audio, tiempos de cada carácter relativos al audio, desplazamiento del t0 de voz)."""
    a, b = tramo["desde"], tramo["hasta"]
    chars = al["caracteres"][a:b + 1]
    ini = np.array(al["inicio"][a:b + 1])
    fin = np.array(al["fin"][a:b + 1])
    s0 = max(limites[0], tramo["t0"] - 0.08)
    s1 = min(limites[1], tramo["t1"] + 0.22)

    # Puntos de corte: en el hueco entre la puntuación interior y la siguiente palabra.
    cortes = []
    for k, c in enumerate(chars):
        if c in respiros and k < len(chars) - 1:
            sig = next((j for j in range(k + 1, len(chars)) if chars[j].strip()), None)
            if sig is None:
                continue
            previo = max(j for j in range(k + 1) if chars[j].isalnum() or j == 0)
            t = (fin[previo] + ini[sig]) / 2
            cortes.append((t, respiros[c]))

    trozos, desde, anadido = [], s0, []
    for t, silencio in cortes:
        trozo = toma[int(desde * SR):int(t * SR)].copy()
        trozos += [fundir(fundir(trozo, FUNDIDO, True) if desde != s0 else trozo, FUNDIDO, False),
                   np.zeros(int(silencio * SR), np.float32)]
        anadido.append((t, silencio))
        desde = t
    ultimo = toma[int(desde * SR):int(s1 * SR)].copy()
    trozos.append(fundir(ultimo, FUNDIDO, True) if cortes else ultimo)
    x = np.concatenate(trozos)
    x = fundir(fundir(x, int(0.03 * SR), True), int(0.06 * SR), False)

    def reloj(t):  # tiempo en la toma → tiempo en la frase montada (antes de estirar)
        return t - s0 + sum(s for tc, s in anadido if t >= tc)

    y = estirar(x, tempo)
    escala = len(y) / len(x)  # ≈ 1/tempo; se usa la medida real, no la teórica
    t_ini = [reloj(t) * escala for t in ini]
    t_fin = [reloj(t) * escala for t in fin]
    return y, chars, t_ini, t_fin, reloj(tramo["t0"]) * escala, reloj(tramo["t1"]) * escala


def palabras_de(chars, t_ini, t_fin, base):
    palabras, actual = [], []
    for k, c in enumerate(chars + [" "]):
        if c.strip():
            actual.append(k)
            continue
        if actual:
            letras = [j for j in actual if chars[j].isalnum()] or actual
            palabras.append({
                "p": "".join(chars[j] for j in actual),
                "t0": round(base + t_ini[letras[0]], 3),
                "t1": round(base + t_fin[letras[-1]], 3),
            })
            actual = []
    # Palabras átonas muy cortas ("¿Le", "Un") pueden quedar con duración nula o solapadas: se ordenan y se
    # les da un mínimo visible, sin mover el arranque de ninguna palabra más de lo imprescindible.
    for k, w in enumerate(palabras):
        if k:
            w["t0"] = round(max(w["t0"], palabras[k - 1]["t0"] + 0.06), 3)
        w["t1"] = round(max(w["t1"], w["t0"] + 0.08), 3)
    return palabras


def envolvente(voz, fps, total):
    """Energía de la voz por fotograma (0-1), con ataque rápido y caída suave, para la nota de voz."""
    n = int(round(total * fps))
    paso = SR / fps
    env, previo = [], 0.0
    for f in range(n):
        tramo = voz[int(f * paso):int((f + 1) * paso)]
        rms = float(np.sqrt(np.mean(tramo ** 2))) if len(tramo) else 0.0
        db = 20 * np.log10(rms + 1e-9)
        v = float(np.clip((db + 48) / 34, 0, 1))
        previo = v if v > previo else previo * 0.72 + v * 0.28
        env.append(round(previo, 2))
    return env


def main():
    guion = json.loads((RAIZ / "voz" / "guion.json").read_text(encoding="utf-8"))
    al = json.loads((RAIZ / "voz" / "toma.json").read_text(encoding="utf-8"))
    m = guion["montaje"]
    toma = leer_audio(RAIZ / "voz" / "toma.mp3")
    al = afinar(al, nivel_db(toma))
    tramos = [tramo_afinado(al, t) for t in al["lineas"]]

    colocadas, cursor = [], m["preroll"]
    for i, tramo in enumerate(tramos):
        izq = (tramos[i - 1]["t1"] + tramo["t0"]) / 2 if i else 0.0
        der = (tramo["t1"] + tramos[i + 1]["t0"]) / 2 if i + 1 < len(tramos) else len(toma) / SR
        y, chars, t_ini, t_fin, v0, v1 = montar_frase(toma, al, tramo, (izq, der), m["respiros"], m["tempo"])
        if i:
            cursor = colocadas[-1]["t1"] + m["pausa_antes"][tramo["id"]]
        base = cursor - v0  # instante del vídeo en que empieza el audio de la frase
        colocadas.append({
            "id": tramo["id"],
            "escena": guion["lineas"][i]["escena"],
            "texto": guion["lineas"][i]["texto"],
            "t0": round(cursor, 3),
            "t1": round(base + v1, 3),
            "palabras": palabras_de(chars, t_ini, t_fin, base),
            "_audio": (base, y),
        })

    duracion = float(np.ceil(colocadas[-1]["t1"] + m["cola"]))  # segundos enteros: fotogramas exactos
    voz = np.zeros(int(duracion * SR) + SR, np.float32)
    for c in colocadas:
        base, y = c.pop("_audio")
        i0 = int(round(base * SR))
        voz[i0:i0 + len(y)] += y[: len(voz) - i0]
    voz = voz[: int(duracion * SR)]

    (RAIZ / "build").mkdir(exist_ok=True)
    escribir_wav(RAIZ / "build" / "voz.wav", voz)
    datos = {"duracion": duracion, "fps": m["fps"], "lineas": colocadas, "env": envolvente(voz, m["fps"], duracion)}
    (RAIZ / "voz" / "tiempos.json").write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")
    (RAIZ / "tiempos.js").write_text(
        "// Generado por herramientas/montar_voz.py — no editar a mano.\n"
        f"window.NIETO_TIEMPOS = {json.dumps(datos, ensure_ascii=False)};\n",
        encoding="utf-8",
    )
    for c in colocadas:
        print(f"{c['id']} {c['escena']:<14} {c['t0']:6.2f} → {c['t1']:6.2f}  ({len(c['palabras'])} palabras)")
    print(f"duración: {duracion} s")


if __name__ == "__main__":
    main()
