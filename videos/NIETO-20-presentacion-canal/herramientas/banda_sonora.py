#!/usr/bin/env python3
"""Banda sonora compuesta «a imagen», efectos y mezcla final. Todo sintetizado aquí, determinista.

La clave de ElevenLabs no tiene permisos de música ni de efectos, y un vídeo que enseña a desconfiar no
debería depender de una pista de banco de sonidos con licencia dudosa: la música se sintetiza (numpy) y se
escribe contra los tiempos de la voz (voz/tiempos.json), no contra una rejilla ciega.

  - Los CUES (instantes donde pasa algo en pantalla) se derivan de las palabras de la locución y se emiten
    en cues.js: la animación y los efectos leen LOS MISMOS números, así que el «ding» cae en el fotograma
    en que llega el mensaje.
  - Música: tensión con latido y un racimo disonante mientras se amontona la jerga; corte en seco al terminar
    «…tocar algo.»; el acorde cálido florece justo en «Respire.»; después un acorde por idea (Re mayor, piano
    de fieltro, pad y bajo), más oscura en la alerta, mínima en la confesión de la voz IA, plena en el cierre.
  - Mezcla: la música se agacha bajo la voz (ducking por la envolvente de la voz), sonoridad final −16 LUFS
    y pico real ≤ −1,5 dBTP (loudnorm en dos pasadas, lineal).

Salidas: cues.js · build/musica.wav · build/sfx.wav · audio/banda-sonora.mp3
Uso:  python3 herramientas/banda_sonora.py   (después de montar_voz.py)
"""
import json
import pathlib
import subprocess

import numpy as np
from scipy.signal import butter, fftconvolve, sosfilt

RAIZ = pathlib.Path(__file__).resolve().parent.parent
SR = 44100
BPM = 84
CORCHEA = 60 / BPM / 2


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def rng(semilla):
    return np.random.default_rng(semilla)


# ── cues: lo que pasa en pantalla, anclado a las palabras ─────────────────────────────────────────────
def calcular_cues(tiempos):
    L = {l["id"]: l["palabras"] for l in tiempos["lineas"]}

    def w(linea, palabra, k=1):
        """Instante de la k-ésima aparición de `palabra` (sin puntuación) en la frase `linea`."""
        vistas = 0
        for p in L[linea]:
            if p["p"].strip("¿?¡!.,:;…").lower() == palabra.lower():
                vistas += 1
                if vistas == k:
                    return p["t0"]
        raise KeyError(f"{linea}:{palabra}")

    ini = {l["id"]: l["t0"] for l in tiempos["lineas"]}
    # La jerga se amontona cada vez más deprisa desde «una palabra rara…» hasta «…tocar algo».
    jerga, t, paso = [], w("01", "una"), 0.34
    while t < w("01", "tocar") and len(jerga) < 16:
        jerga.append(round(t, 3))
        t += paso
        paso = max(0.085, paso * 0.83)
    c = {
        "vibra": round(ini["01"] - 0.05, 3),
        "mensaje": w("01", "Un"),
        "jerga": jerga,
        "dedo": w("01", "miedo"),
        "congela": round(tiempos["lineas"][0]["t1"] + 0.04, 3),
        "respire": w("02", "Respire"),
        "sonrisa": w("02", "El"),
        "muerde": w("02", "muerde"),
        "escena3": ini["03"],
        "logo": w("03", "Nieto"),
        "ia": w("03", "inteligencia"),
        "movil": w("03", "móvil"),
        "traduce": w("03", "sin"),
        "escena4": ini["04"],
        "tarjetas": [w("04", "protegerse"), w("04", "sacarle"), w("04", "hacer")],
        "escena5": ini["05"],
        "una": w("05", "una"),
        "pasos": [w("05", "paso"), w("05", "móvil"), w("05", "señalamos")],
        "toque": round(w("05", "pulsar") + 0.12, 3),
        "escena6": ini["06"],
        "estafa_llega": w("06", "aparece"),
        "alerta": w("06", "avisamos"),
        "sello": round(w("06", "avisamos") + 0.42, 3),
        "duda": w("06", "ante"),
        "no_toque": w("06", "no"),
        "escena7": ini["07"],
        "aprende": w("07", "aprende"),
        "ensena": w("07", "enseña"),
        "otro": w("07", "otro"),
        "red": [round(w("07", "otro") + 0.35 + 0.17 * k, 3) for k in range(9)],
        "nadie": w("07", "Nadie"),
        "escena8": ini["08"],
        "esta_voz": w("08", "esta"),
        "ia_voz": w("08", "inteligencia"),
        "siempre": w("08", "siempre"),
        "escena9": ini["09"],
        "suscribase_toque": round(w("09", "Suscríbase") + 0.78, 3),
        "logo_final": w("09", "Nos"),
        "guino": round(tiempos["duracion"] - 1.9, 3),
        "fin": tiempos["duracion"],
    }
    c["transiciones"] = [round(c[k] - 0.2, 3) for k in ("escena3", "escena4", "escena5", "escena6", "escena7", "escena9")]
    return c


# ── utilidades de síntesis ─────────────────────────────────────────────────────────────────────────────
def pista(segundos, canales=2):
    return np.zeros((int(segundos * SR) + SR, canales), np.float32)


def sumar(destino, senal, t, gan=1.0, pan=0.0):
    """Suma una señal mono (o estéreo) en `t` segundos con panorama equal-power."""
    i = int(round(t * SR))
    if i >= len(destino):
        return
    if senal.ndim == 1:
        izq, der = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        senal = np.stack([senal * izq, senal * der], 1)
    n = min(len(senal), len(destino) - i)
    destino[i:i + n] += senal[:n] * gan


def paso_bajo(x, fc, orden=2):
    return sosfilt(butter(orden, fc, "low", fs=SR, output="sos"), x, axis=0)


def paso_banda(x, f1, f2, orden=2):
    return sosfilt(butter(orden, [f1, f2], "band", fs=SR, output="sos"), x, axis=0)


def reverb(x, rt60=2.2, mezcla=0.3, semilla=7):
    """Convolución con una respuesta al impulso sintética (ruido con caída exponencial), estéreo decorrelado."""
    n = int(rt60 * 1.2 * SR)
    t = np.arange(n) / SR
    caida = np.exp(-6.9 * t / rt60)
    r = rng(semilla)
    ir = np.stack([paso_bajo(r.standard_normal(n), 5200) * caida for _ in range(2)], 1)
    ir[: int(0.018 * SR)] = 0  # pre-delay
    ir /= np.sqrt((ir ** 2).sum(0))
    humedo = np.stack([fftconvolve(x[:, k], ir[:, k])[: len(x)] for k in range(2)], 1)
    return x * (1 - mezcla) + humedo * mezcla * 1.6


# ── instrumentos ───────────────────────────────────────────────────────────────────────────────────────
def piano(midi, vel=0.6, dur=4.0, semilla=0):
    """Piano de fieltro: parciales inarmónicos, doble caída, cuerdas ligeramente desafinadas y golpe suave."""
    f = hz(midi)
    t = np.arange(int(dur * SR)) / SR
    x = np.zeros_like(t)
    B = 0.00035
    for n in range(1, 12):
        fn = n * f * np.sqrt(1 + B * n * n)
        if fn > 12000:
            break
        amp = vel / n ** 1.35 * np.exp(-(n - 1) * (0.55 - 0.35 * vel))
        k = (0.9 + 0.45 * n) * (f / 262) ** 0.35
        env = 0.62 * np.exp(-t * k * 2.4) + 0.38 * np.exp(-t * k * 0.55)
        for cents in (-0.9, 0.9):
            x += amp * env * np.sin(2 * np.pi * fn * 2 ** (cents / 1200) * t + n)
    x *= 1 - np.exp(-t / 0.005)
    golpe = paso_bajo(rng(semilla).standard_normal(int(0.02 * SR)), 900) * np.exp(-np.arange(int(0.02 * SR)) / (0.004 * SR))
    x[: len(golpe)] += golpe * 0.05 * vel
    x *= np.minimum(1, (dur - t) / 0.3)  # apagado
    return x * 0.22


def pad(notas, dur, ataque=1.4, caida=1.6, brillo=2200, semilla=1):
    """Pad cálido: dientes de sierra de banda limitada, desafinados L/R, filtrados."""
    t = np.arange(int(dur * SR)) / SR
    out = np.zeros((len(t), 2))
    for i, m in enumerate(notas):
        f = hz(m)
        for canal, cents in enumerate((-6, 6)):
            fr = f * 2 ** ((cents + (i % 3 - 1) * 2) / 1200)
            onda = sum(np.sin(2 * np.pi * fr * n * t + i + n) / n for n in range(1, 14) if fr * n < 9000)
            out[:, canal] += onda * (0.9 if m < 52 else 0.55)
    env = np.minimum(1, t / ataque) * np.minimum(1, np.maximum(0, (dur - t) / caida))
    env = env ** 1.6
    lfo = 1 + 0.06 * np.sin(2 * np.pi * 0.18 * t)
    return paso_bajo(out * (env * lfo)[:, None], brillo) * 0.035


def bajo(midi, dur, vel=0.5):
    t = np.arange(int(dur * SR)) / SR
    f = hz(midi)
    x = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(4 * np.pi * f * t)
    env = np.minimum(1, t / 0.08) * np.minimum(1, np.maximum(0, (dur - t) / 0.6))
    return x * env * vel * 0.12


def campana(midi, vel=0.5, dur=3.0):
    t = np.arange(int(dur * SR)) / SR
    f = hz(midi)
    x = np.zeros_like(t)
    for r, a, k in ((1, 1, 1.4), (2.76, 0.45, 3.5), (5.40, 0.22, 6.0), (8.93, 0.1, 9.0)):
        x += a * np.sin(2 * np.pi * f * r * t) * np.exp(-t * k)
    return x * (1 - np.exp(-t / 0.002)) * vel * 0.18


def latido(t0, vel):
    """Latido «pum-pum» grave: dos golpes senoidales con caída de tono."""
    def golpe(v):
        n = int(0.18 * SR)
        t = np.arange(n) / SR
        f = 58 * np.exp(-t * 6) + 38
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 22) * v
    x = np.zeros(int(0.5 * SR))
    a, b = golpe(vel), golpe(vel * 0.7)
    x[: len(a)] += a
    x[int(0.19 * SR): int(0.19 * SR) + len(b)] += b
    return x * 0.5


# ── efectos (SFX) ──────────────────────────────────────────────────────────────────────────────────────
def sfx_ding():
    t = np.arange(int(0.9 * SR)) / SR
    a = np.sin(2 * np.pi * 1318.5 * t) * np.exp(-t * 7)
    b = np.zeros_like(t)
    k = int(0.085 * SR)
    b[k:] = np.sin(2 * np.pi * 1975.5 * t[: len(t) - k]) * np.exp(-t[: len(t) - k] * 6)
    return (a * 0.6 + b * 0.5) * (1 - np.exp(-t / 0.002)) * 0.16


def sfx_vibra():
    t = np.arange(int(0.42 * SR)) / SR
    x = np.sign(np.sin(2 * np.pi * 165 * t)) * (0.5 + 0.5 * np.sin(2 * np.pi * 24 * t))
    env = np.minimum(1, t / 0.02) * np.minimum(1, (0.42 - t) / 0.05)
    return paso_bajo(x * env, 700) * 0.09


def sfx_pop(tono=1.0, semilla=0):
    n = int(0.09 * SR)
    t = np.arange(n) / SR
    f = (320 + 700 * np.exp(-t * 55)) * tono
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 38)
    clic = rng(semilla).standard_normal(n) * np.exp(-t * 900) * 0.2
    return (x + clic) * 0.09


def sfx_toque():
    n = int(0.12 * SR)
    t = np.arange(n) / SR
    cuerpo = np.sin(2 * np.pi * 190 * t) * np.exp(-t * 45)
    clic = paso_banda(rng(3).standard_normal(n), 2500, 7000) * np.exp(-t * 700)
    return (cuerpo * 0.7 + clic * 0.5) * 0.14


def sfx_barrido(dur=0.55, semilla=5, gan=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    env = np.sin(np.pi * t / dur) ** 2
    x = paso_banda(rng(semilla).standard_normal(n), 350, 2600) * env
    return x * 0.045 * gan


def sfx_alerta():
    t = np.arange(int(0.5 * SR)) / SR
    x = np.zeros_like(t)
    for i, (f, t0) in enumerate(((880.0, 0.0), (659.3, 0.14))):
        k = int(t0 * SR)
        tt = t[: len(t) - k]
        tri = 2 / np.pi * np.arcsin(np.sin(2 * np.pi * f * tt))
        x[k:] += tri * np.exp(-tt * 9) * (1 - np.exp(-tt / 0.004))
    return paso_bajo(x, 3500) * 0.08


def sfx_sello():
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    f = 95 * np.exp(-t * 9) + 45
    cuerpo = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 14)
    golpe = paso_bajo(rng(9).standard_normal(n), 600) * np.exp(-t * 60)
    return (cuerpo * 0.8 + golpe * 0.6) * 0.2


def sfx_pulsacion(midi, vel=0.5):
    return piano(midi, vel, 1.8, semilla=midi) * 0.8


# ── composición musical ────────────────────────────────────────────────────────────────────────────────
ACORDES = {
    "D": [50, 57, 62, 66, 69, 76],
    "A/C#": [49, 57, 61, 64, 69, 71],
    "Bm7": [47, 54, 59, 62, 66, 69],
    "Gmaj7": [43, 55, 59, 62, 66, 69],
    "D/F#": [42, 57, 62, 66, 69, 74],
    "Em7": [40, 55, 59, 62, 64, 67],
    "Asus4": [45, 57, 62, 64, 69, 71],
    "A": [45, 57, 61, 64, 69, 73],
    "Gadd9": [43, 55, 59, 62, 67, 69],
}
PATRON = [0, 2, 1, 3, 2, 4, 3, 2]


def seccion(musica, acorde, t0, t1, densidad, vel, semilla, pad_gan=1.0, octava=0):
    notas = ACORDES[acorde]
    dur = t1 - t0
    sumar(musica, pad(notas, dur + 1.2, semilla=semilla), t0 - 0.15, pad_gan)
    sumar(musica, bajo(notas[0] - 12 if notas[0] > 45 else notas[0], dur + 0.4, vel * 0.9), t0, 1.0)
    if densidad == 0:
        return
    agudas = [n + 12 * octava for n in notas if n >= 57] + [notas[-1] + 12]
    paso = CORCHEA * (2 if densidad == 1 else 1)
    k, t = 0, t0
    while t < t1 - 0.05:
        nota = agudas[PATRON[k % len(PATRON)] % len(agudas)]
        v = vel * (1.0 if k % 4 == 0 else 0.72) * (0.92 + 0.08 * ((k * 7 + semilla) % 5) / 4)
        sumar(musica, piano(nota, v, 3.2, semilla=semilla + k), t, 1.0, pan=((k % 5) - 2) * 0.12)
        k += 1
        t += paso


def componer(c, T):
    musica = pista(T)

    # S1 · el ruido: dron grave, racimo agudo con trémolo que acelera y latido que se acelera.
    fin_ruido = c["congela"]
    t = np.arange(int(fin_ruido * SR)) / SR
    dron = (np.sin(2 * np.pi * hz(26) * t) + 0.5 * np.sin(2 * np.pi * hz(33) * t)
            + 0.3 * np.sin(2 * np.pi * hz(38) * t * 1.003)) * np.minimum(1, t / 2.5) * 0.10
    trem = 7 + 5 * (t / fin_ruido) ** 2
    racimo = sum(np.sin(2 * np.pi * hz(m) * t + m) for m in (85, 86, 88)) \
        * (0.5 + 0.5 * np.sin(2 * np.pi * np.cumsum(trem) / SR)) \
        * np.clip((t - c["mensaje"]) / (fin_ruido - c["mensaje"]), 0, 1) ** 1.7 * 0.03
    subida = paso_banda(rng(11).standard_normal(len(t)), 900, 5000) * np.clip((t - c["jerga"][0]) / (fin_ruido - c["jerga"][0]), 0, 1) ** 2.2 * 0.05
    ruido = dron + racimo + subida
    ruido[-int(0.05 * SR):] *= np.linspace(1, 0, int(0.05 * SR))  # corte en seco
    sumar(musica, ruido, 0)
    tb, bpm = 0.35, 68.0
    while tb < fin_ruido - 0.3:
        sumar(musica, latido(tb, 0.5 + 0.4 * tb / fin_ruido), tb)
        bpm = 68 + 52 * (tb / fin_ruido) ** 1.5
        tb += 60 / bpm

    # S2 · «Respire.»: florece el acorde; después un acorde por idea.
    r = c["respire"]
    sumar(musica, pad(ACORDES["D"] + [81], 4.2, ataque=2.2, caida=1.4, brillo=2600, semilla=2), r - 0.1, 1.3)
    sumar(musica, bajo(38, 3.6, 0.45), r + 0.3)
    for k, n in enumerate((69, 74, 78)):
        sumar(musica, piano(n, 0.35, 4.0, semilla=40 + k), c["sonrisa"] + 0.55 * k, 1.0, pan=(k - 1) * 0.2)
    plan = [
        ("D", c["escena3"], c["ia"] - 0.25, 1, 0.5),
        ("A/C#", c["ia"] - 0.25, c["traduce"] - 1.4, 1, 0.5),
        ("Bm7", c["traduce"] - 1.4, c["escena4"] - 0.2, 1, 0.5),
        ("Gmaj7", c["escena4"] - 0.2, c["tarjetas"][1] - 0.1, 2, 0.5),
        ("D/F#", c["tarjetas"][1] - 0.1, c["tarjetas"][2] - 0.2, 2, 0.5),
        ("Em7", c["tarjetas"][2] - 0.2, c["escena5"] - 1.0, 2, 0.48),
        ("Asus4", c["escena5"] - 1.0, c["escena5"] - 0.2, 1, 0.42),
        ("D", c["escena5"] - 0.2, c["pasos"][0] - 0.1, 2, 0.52),
        ("A/C#", c["pasos"][0] - 0.1, c["pasos"][2] - 0.4, 2, 0.52),
        ("Bm7", c["pasos"][2] - 0.4, c["escena6"] - 0.2, 2, 0.5),
        ("Bm7", c["escena6"] - 0.2, c["duda"] - 1.1, 0, 0.4),       # alerta: se quita el piano
        ("Gmaj7", c["duda"] - 1.1, c["no_toque"] + 0.3, 1, 0.42),
        ("Asus4", c["no_toque"] + 0.3, c["escena7"] - 0.2, 1, 0.42),
        ("D", c["escena7"] - 0.2, c["nadie"] - 0.15, 2, 0.52),
        ("Gadd9", c["nadie"] - 0.15, c["nadie"] + 1.6, 2, 0.56),
        ("A", c["nadie"] + 1.6, c["escena8"] - 0.2, 1, 0.5),
        ("Bm7", c["escena8"] - 0.2, c["ia_voz"] + 0.3, 0, 0.35),     # confesión: casi nada
        ("Gmaj7", c["ia_voz"] + 0.3, c["siempre"] - 0.4, 0, 0.35),
        ("Asus4", c["siempre"] - 0.4, c["escena9"] - 0.2, 1, 0.4),
        ("D", c["escena9"] - 0.2, c["logo_final"] - 0.1, 2, 0.58),
        ("Gadd9", c["logo_final"] - 0.1, c["logo_final"] + 1.3, 2, 0.55),
    ]
    for i, (acorde, t0, t1, dens, vel) in enumerate(plan):
        seccion(musica, acorde, t0, t1, dens, vel, semilla=100 + i * 13, octava=1 if acorde == "Gadd9" else 0)
    # Acorde final largo y campana en el guiño.
    fin = c["logo_final"] + 1.3
    sumar(musica, pad(ACORDES["D"] + [81], T - fin + 0.5, ataque=0.6, caida=2.8, semilla=9), fin, 1.25)
    sumar(musica, bajo(38, T - fin, 0.5), fin)
    for k, n in enumerate((62, 66, 69, 74, 78)):
        sumar(musica, piano(n, 0.5 - 0.05 * k, 5.0, semilla=70 + k), fin + 0.09 * k, 1.0, pan=(k - 2) * 0.15)
    sumar(musica, campana(90, 0.5), c["logo"] + 0.05, 1.0, pan=0.2)
    sumar(musica, campana(93, 0.45), c["guino"], 1.0, pan=-0.2)
    musica = reverb(musica, rt60=2.4, mezcla=0.32)
    # Deja sitio a la voz: fuera los subgraves y −4 dB en la zona de «barro» (150-400 Hz).
    musica = sosfilt(butter(2, 50, "high", fs=SR, output="sos"), musica, axis=0)
    return musica - 0.37 * paso_banda(musica, 150, 400)


def efectos(c, T):
    fx = pista(T)
    sumar(fx, sfx_vibra(), c["vibra"])
    sumar(fx, sfx_ding(), c["mensaje"], pan=0.1)
    for k, t in enumerate(c["jerga"]):
        sumar(fx, sfx_pop(0.8 + 0.07 * (k % 6), semilla=k), t, 0.9, pan=((k * 5) % 7 - 3) * 0.2)
    sumar(fx, sfx_barrido(1.1, gan=1.3)[::-1].copy(), c["respire"] - 0.75)
    for t in c["transiciones"]:
        sumar(fx, sfx_barrido(0.6, semilla=int(t * 10)), t - 0.25)
    sumar(fx, sfx_pop(1.2), c["ia"] + 0.05)
    sumar(fx, sfx_pop(1.05), c["movil"] + 0.05)
    sumar(fx, sfx_barrido(0.4, gan=0.9), c["traduce"] + 0.2)
    for k, t in enumerate(c["tarjetas"]):
        sumar(fx, sfx_pop(0.9 + 0.12 * k, semilla=20 + k), t, 1.1)
    sumar(fx, sfx_pop(1.3), c["una"])
    for k, t in enumerate(c["pasos"]):
        sumar(fx, sfx_pop(1.0 + 0.1 * k, semilla=30 + k), t, 0.9)
    sumar(fx, sfx_toque(), c["toque"])
    sumar(fx, sfx_ding(), c["estafa_llega"], 0.9)
    sumar(fx, sfx_alerta(), c["alerta"])
    sumar(fx, sfx_sello(), c["sello"])
    sumar(fx, sfx_pulsacion(74, 0.45), c["aprende"] + 0.1)
    sumar(fx, sfx_pulsacion(78, 0.45), c["otro"])
    for k, t in enumerate(c["red"]):
        sumar(fx, sfx_pulsacion([81, 83, 86, 88, 90, 93, 86, 90, 93][k], 0.25), t, 0.8, pan=((k * 3) % 5 - 2) * 0.25)
    sumar(fx, sfx_toque(), c["suscribase_toque"])
    sumar(fx, sfx_ding(), c["suscribase_toque"] + 0.18, 0.7)
    return reverb(fx, rt60=1.2, mezcla=0.18, semilla=13)


def leer(ruta, canales):
    crudo = subprocess.run(["ffmpeg", "-v", "error", "-i", str(ruta), "-ac", str(canales), "-ar", str(SR), "-f", "f32le", "-"],
                           capture_output=True, check=True).stdout
    return np.frombuffer(crudo, np.float32).reshape(-1, canales).copy()


def escribir(ruta, x, extra=()):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", str(x.shape[1]), "-i", "-", *extra, str(ruta)],
                   input=np.ascontiguousarray(x, np.float32).tobytes(), check=True)


def mezclar(voz, musica, fx, T):
    n = int(T * SR)
    voz, musica, fx = (np.pad(a, ((0, max(0, n - len(a))), (0, 0)))[:n] for a in (voz, musica, fx))
    # Ducking: la música baja hasta −9 dB mientras habla la voz (ataque 60 ms, relajación 450 ms).
    paso = 256
    e = np.sqrt(np.mean(voz[: n // paso * paso, 0].reshape(-1, paso) ** 2, axis=1))
    activo = np.clip((20 * np.log10(e + 1e-9) + 50) / 20, 0, 1)
    sig, g = [], 0.0
    for a in activo:
        g = g + (a - g) * (0.35 if a > g else 0.045)
        sig.append(g)
    gan = 10 ** (-9 * np.repeat(sig, paso) / 20)
    gan = np.pad(gan, (0, n - len(gan)), constant_values=gan[-1])
    musica = musica * gan[:, None]
    # Niveles relativos (la voz manda): la música suena como cama, los efectos por debajo de la voz.
    mezcla = voz * 1.0 + musica * 0.6 + fx * 1.7
    mezcla[-int(1.2 * SR):] *= np.linspace(1, 0, int(1.2 * SR))[:, None] ** 2
    return mezcla


def loudnorm(entrada, salida):
    """loudnorm de ffmpeg en dos pasadas y modo lineal: −16 LUFS, −1,5 dBTP, sin compresión dinámica."""
    objetivo = "I=-16:TP=-1.5:LRA=11"
    med = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(entrada), "-af", f"loudnorm={objetivo}:print_format=json", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    m = json.loads(med[med.rindex("{"):])
    filtro = (f"loudnorm={objetivo}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
              f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(entrada), "-af", filtro, "-ar", str(SR),
                    "-c:a", "libmp3lame", "-b:a", "192k", str(salida)], check=True)


def main():
    tiempos = json.loads((RAIZ / "voz" / "tiempos.json").read_text(encoding="utf-8"))
    T = tiempos["duracion"]
    c = calcular_cues(tiempos)
    (RAIZ / "cues.js").write_text(
        "// Generado por herramientas/banda_sonora.py — no editar a mano. Instantes (s) de lo que pasa en pantalla,\n"
        "// anclados a las palabras de la locución; los efectos de sonido usan exactamente los mismos.\n"
        f"window.NIETO_CUES = {json.dumps(c, ensure_ascii=False)};\n", encoding="utf-8")
    build = RAIZ / "build"
    build.mkdir(exist_ok=True)
    musica, fx = componer(c, T), efectos(c, T)
    escribir(build / "musica.wav", musica)
    escribir(build / "sfx.wav", fx)
    mezcla = mezclar(leer(build / "voz.wav", 2), musica, fx, T)
    escribir(build / "mezcla.wav", mezcla)
    (RAIZ / "audio").mkdir(exist_ok=True)
    loudnorm(build / "mezcla.wav", RAIZ / "audio" / "banda-sonora.mp3")
    print(f"banda sonora: audio/banda-sonora.mp3 ({T} s); cues: {len(c)}")


if __name__ == "__main__":
    main()
