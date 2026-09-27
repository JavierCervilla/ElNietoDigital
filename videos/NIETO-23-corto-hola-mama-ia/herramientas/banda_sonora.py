#!/usr/bin/env python3
"""Banda sonora a imagen del corto «hola mamá»: música y efectos de ElevenLabs congelados en sonido/.

Mismo método que NIETO-20/21 (videos/NIETO-20-presentacion-canal/herramientas/banda_sonora.py), recortado a lo
que usa este corto:
  - Los CUES (instantes donde pasa algo en pantalla) se derivan de las palabras de la locución y se emiten en
    cues.js: la animación, los efectos y la música leen LOS MISMOS números.
  - Música: tensión (sonido/musica-tension.mp3) desde el gancho hasta que se acaba la presión del estafador; se
    corta en seco antes de «Qué hacer:». La calma (sonido/musica-calma.mp3), compuesta a imagen desde ahí, lleva
    la solución, la regla y el cierre. El latido se re-secuencia bajo la presión para que se acelere.
  - Efectos: normalizados a un pico común y alineados por su ATAQUE real, no por el inicio del fichero.
  - Mezcla: la música se agacha bajo la voz con anticipación de 100 ms; −16 LUFS y pico ≤ −1,5 dBTP.

Determinista: mismas fuentes congeladas → mismo audio, byte a byte.
Salidas: cues.js · build/musica.wav · build/sfx.wav · build/mezcla.wav · audio/banda-sonora.mp3
Uso:  python3 herramientas/banda_sonora.py   (después de montar_voz.py)
"""
import json
import pathlib
import subprocess

import numpy as np
from scipy.signal import butter, fftconvolve, sosfilt

RAIZ = pathlib.Path(__file__).resolve().parent.parent
SONIDO = RAIZ / "sonido"
SR = 44100


# ── cues: lo que pasa en pantalla, anclado a las palabras ─────────────────────────────────────────────
def calcular_cues(tiempos):
    L = {l["id"]: l["palabras"] for l in tiempos["lineas"]}
    ini = {l["id"]: l["t0"] for l in tiempos["lineas"]}
    fin_de = {l["id"]: l["t1"] for l in tiempos["lineas"]}

    def w(linea, palabra, k=1):
        """Instante de la k-ésima aparición de `palabra` (sin puntuación) en la frase `linea`."""
        vistas = 0
        for p in L[linea]:
            if p["p"].strip("¿?¡!.,:;…«»").lower() == palabra.lower():
                vistas += 1
                if vistas == k:
                    return p["t0"]
        raise KeyError(f"{linea}:{palabra}")

    c = {
        # 1 · gancho: el mensaje ya está en pantalla en el fotograma 0; el móvil vibra antes de que hable la voz.
        "vibra": 0.04,
        "estafa": w("01", "estafa"),
        # 2-4 · el chat, mensaje a mensaje, y las tres señales.
        "escena2": round(ini["02"] - 0.5, 3),
        "whatsapp": w("02", "WhatsApp"),
        "senal1": w("02", "conoce"),
        "soy_yo": w("03", "hijo"),
        "roto": w("03", "Que", 1),
        "guarde": w("03", "Que", 2),
        "senal2": w("03", "nuevo"),
        "al_rato": w("04", "rato"),
        "escribiendo": round(w("04", "le") - 0.1, 3),
        "dinero": w("04", "dinero"),
        "senal3": w("04", "prisa"),
        "bizum": w("04", "transferencia"),
        "urgente": w("04", "problema"),
        "congela": round(fin_de["04"] + 0.12, 3),
        # 5 · qué hacer.
        "escena5": round(ini["05"] - 0.25, 3),
        "no_conteste": w("05", "no", 1),
        "no_pague": w("05", "no", 2),
        # 6 · el número de siempre.
        "escena6": round(ini["06"] - 0.4, 3),
        "llamar": round(w("06", "hijo") + 0.05, 3),
        "siempre": w("06", "de"),
        "guardado": w("06", "guardado"),
        "borre": w("06", "borre"),
        "nunca": w("06", "nunca"),
        # 7 · la regla: dinero + prisa + mensaje = estafa.
        "escena7": round(ini["07"] - 0.4, 3),
        "f_dinero": w("07", "dinero"),
        "f_prisa": w("07", "prisa"),
        "f_mensaje": w("07", "mensaje"),
        "f_estafa": round(fin_de["07"] + 0.1, 3),
        # 8 · ante la duda.
        "escena8": round(ini["08"] - 0.35, 3),
        # El sello «= ESTAFA» se queda durante «Y recuerde:»; el azul entra justo antes de «ante la duda».
        "iris8": round(w("08", "ante") - 0.9, 3),
        "duda": w("08", "ante"),
        "no_toque": w("08", "no"),
        "pregunte": w("08", "pregunte"),
        "confianza": w("08", "confianza"),
        # 9 · envíeselo a quien lo necesite, y cierre.
        "escena9": round(ini["09"] - 0.35, 3),
        "envie": w("09", "envíeselo"),
        "cierre": round(fin_de["09"] + 0.3, 3),
        "fin_voz": fin_de["09"],
        "fin": tiempos["duracion"],
    }
    c["transiciones"] = [c[k] for k in ("escena5", "escena6", "escena7", "iris8", "escena9")]
    return c


# ── utilidades ─────────────────────────────────────────────────────────────────────────────────────────
def db(v):
    return 10 ** (np.asarray(v, float) / 20)


def pista(segundos, canales=2):
    return np.zeros((int(segundos * SR) + SR, canales), np.float32)


def sumar(destino, senal, t, gan=1.0, pan=0.0):
    """Suma una señal mono (o estéreo) en `t` segundos con panorama equal-power."""
    i = int(round(t * SR))
    if i >= len(destino):
        return
    if i < 0:
        senal, i = senal[-i:], 0
    if senal.ndim == 1:
        izq, der = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        senal = np.stack([senal * izq, senal * der], 1)
    n = min(len(senal), len(destino) - i)
    destino[i:i + n] += senal[:n] * gan


def paso_bajo(x, fc, orden=2):
    return sosfilt(butter(orden, fc, "low", fs=SR, output="sos"), x, axis=0)


def reverb(x, rt60=1.2, mezcla=0.15, semilla=13):
    """Convolución con una respuesta al impulso sintética (ruido con caída exponencial), estéreo decorrelado."""
    n = int(rt60 * 1.2 * SR)
    t = np.arange(n) / SR
    caida = np.exp(-6.9 * t / rt60)
    r = np.random.default_rng(semilla)
    ir = np.stack([paso_bajo(r.standard_normal(n), 5200) * caida for _ in range(2)], 1)
    ir[: int(0.018 * SR)] = 0  # pre-delay
    ir /= np.sqrt((ir ** 2).sum(0))
    humedo = np.stack([fftconvolve(x[:, k], ir[:, k])[: len(x)] for k in range(2)], 1)
    return x * (1 - mezcla) + humedo * mezcla * 1.6


def leer(ruta, canales):
    crudo = subprocess.run(["ffmpeg", "-v", "error", "-i", str(ruta), "-ac", str(canales), "-ar", str(SR), "-f", "f32le", "-"],
                           capture_output=True, check=True).stdout
    return np.frombuffer(crudo, np.float32).reshape(-1, canales).copy()


def escribir(ruta, x, extra=()):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", str(x.shape[1]), "-i", "-", *extra, str(ruta)],
                   input=np.ascontiguousarray(x, np.float32).tobytes(), check=True)


def cargar(nombre, mono=False, pico_db=-1.0):
    """sonido/<nombre>.mp3 normalizado a un pico común (algunos efectos salen por encima de 0 dBFS)."""
    x = leer(SONIDO / f"{nombre}.mp3", 2)
    x = x * (db(pico_db) / (np.abs(x).max() + 1e-9))
    return x.mean(1) if mono else x


def energia(x, paso=0.005):
    m = x.mean(1) if x.ndim > 1 else x
    n = int(paso * SR)
    return 20 * np.log10(np.sqrt(np.mean(m[: len(m) // n * n].reshape(-1, n) ** 2, axis=1)) + 1e-9)


def arranque(x, umbral=-40.0):
    """Primer instante en que el sonido supera `umbral` dBFS."""
    return float(np.argmax(energia(x) > umbral)) * 0.005


def pico(x):
    return float(np.argmax(energia(x, 0.01))) * 0.01


def tono(x, factor):
    """Cambia la altura remuestreando (y con ella la duración): variedad sin fichero nuevo."""
    return np.interp(np.arange(0, len(x) - 1, factor), np.arange(len(x)), x)


def tramo(x, t0, t1, fundido=0.01):
    y = x[int(t0 * SR):int(t1 * SR)].copy()
    n = int(fundido * SR)
    y[:n] *= np.linspace(0, 1, n)[:, None] if y.ndim > 1 else np.linspace(0, 1, n)
    y[-n:] *= np.linspace(1, 0, n)[:, None] if y.ndim > 1 else np.linspace(1, 0, n)
    return y


def golpes_latido(x):
    """Instante de cada «pum» (el primero de cada par pum-pum) del latido grabado."""
    e = energia(x, 0.01)
    u = np.percentile(e, 85)
    picos = [i for i in range(1, len(e) - 1) if e[i] > u and e[i] >= e[i - 1] and e[i] >= e[i + 1]]
    unicos = [picos[0]]
    for i in picos[1:]:
        if i - unicos[-1] > 18:
            unicos.append(i)
    return [unicos[0] * 0.01] + [b * 0.01 for a, b in zip(unicos, unicos[1:]) if b - a > 45]


# ── música ─────────────────────────────────────────────────────────────────────────────────────────────
def componer(c, T):
    musica = pista(T)

    # 1 · Tensión: del gancho a «…no puede esperar.», corte en seco (el silencio antes de «Qué hacer:»).
    fin = c["congela"]
    tension = tramo(cargar("musica-tension"), 0, fin, 0.03)
    t = np.arange(len(tension)) / SR
    # Bajo el chat se queda en cama; crece con la presión (dinero, Bizum, prisa).
    marcas = [0, c["escena2"], c["al_rato"] - 0.3, c["dinero"], fin]
    tension *= db(np.interp(t, marcas, [-3, -6, -6, -2, 0]))[:, None]
    sumar(musica, tension, 0, db(-4))
    # El latido entra con «Y al rato…» y se acelera de 70 a 124 ppm hasta el corte.
    lat = cargar("latido")
    golpes = golpes_latido(lat)
    t0, tb, k = c["al_rato"], c["al_rato"], 0
    while tb < fin - 0.4:
        g = golpes[k % len(golpes)]
        x = (tb - t0) / (fin - t0)
        sumar(musica, tramo(lat, g - 0.04, g + 0.55), tb, db(-6) * (0.5 + 0.5 * x))
        tb += 60 / (70 + 54 * x ** 1.3)
        k += 1

    # 2 · Calma: compuesta a imagen desde «Qué hacer:» (una sección por escena).
    calma = cargar("musica-calma")
    tc = np.arange(len(calma)) / SR + c["escena5"]
    marcas = [0, c["escena6"] - 0.2, c["escena6"] + 0.4, c["escena8"] - 0.3, c["escena8"] + 0.3, c["fin_voz"] + 0.3,
              c["fin_voz"] + 1.2, 1e9]
    gan = db(np.interp(tc, marcas, [-3, -3, 0, 0, -1, -1, 4, 4]))
    # «Qué hacer:» casi a oscuras: la música se queda en un filtro cerrado hasta que suena el número de siempre.
    oscuro = np.interp(tc, marcas, [1, 1, 0, 0, 0, 0, 0, 0])[:, None]
    cuerpo = (calma * (1 - oscuro) + paso_bajo(calma, 700) * oscuro) * gan[:, None]
    sumar(musica, cuerpo, c["escena5"])
    musica = sosfilt(butter(2, 60, "high", fs=SR, output="sos"), musica, axis=0)
    return musica - 0.3 * paso_bajo(musica, 150)


# ── efectos ────────────────────────────────────────────────────────────────────────────────────────────
NIVELES = {"vibra": -15, "ding": -9, "pop": -14, "barrido": -17, "alerta": -9, "sello": -7, "toque": -11,
           "burbuja": -13, "brillo": -11, "tecleo": -20, "llamada": -17}


def efectos(c, T):
    fx = pista(T)
    S = {n: cargar(n, mono=True) for n in NIVELES}

    def pon(n, t, extra=0.0, por="arranque", factor=None, pan=0.0):
        x = S[n] if factor is None else tono(S[n], factor)
        sumar(fx, x, t - (arranque(x) if por == "arranque" else pico(x)), db(NIVELES[n] + extra), pan)

    S["vibra"] = tramo(S["vibra"], 0, 0.55, 0.06)
    pon("vibra", c["vibra"])
    pon("sello", c["estafa"] + 0.05)
    pon("barrido", c["escena2"] + 0.1, por="pico")
    pon("alerta", c["senal1"] + 0.05, extra=-3)
    for t, f in ((c["soy_yo"], 1.0), (c["roto"], 1.06), (c["guarde"], 0.95)):
        pon("ding", t, extra=-5, factor=f, pan=-0.15)
    pon("alerta", c["senal2"] + 0.05, extra=-3)
    pon("pop", c["al_rato"], extra=-2)
    S["tecleo"] = tramo(S["tecleo"], 0, min(len(S["tecleo"]) / SR, c["dinero"] - c["escribiendo"]), 0.05)
    pon("tecleo", c["escribiendo"])
    pon("ding", c["dinero"], extra=-3, pan=-0.15)
    pon("alerta", c["senal3"] + 0.05, extra=-2)
    pon("ding", c["bizum"], extra=-3, factor=1.08, pan=-0.15)
    pon("ding", c["urgente"], extra=-3, factor=1.16, pan=-0.15)
    for t in c["transiciones"]:
        pon("barrido", t, por="pico")
    pon("sello", c["no_conteste"] + 0.05, extra=-5)
    pon("sello", c["no_pague"] + 0.05, extra=-4)
    pon("toque", c["llamar"])
    S["llamada"] = tramo(S["llamada"], 0, min(len(S["llamada"]) / SR, c["borre"] - c["llamar"] - 0.4), 0.2)
    pon("llamada", c["llamar"] + 0.25)
    pon("burbuja", c["guardado"] + 0.05)
    pon("sello", c["nunca"] + 0.05, extra=-5)
    for k, t in enumerate((c["f_dinero"], c["f_prisa"], c["f_mensaje"])):
        pon("pop", t, factor=0.9 + 0.12 * k)
    pon("sello", c["f_estafa"])
    pon("toque", c["no_toque"] - 0.1, extra=-4)
    pon("burbuja", c["pregunte"] + 0.1)
    pon("burbuja", c["confianza"] + 0.1, factor=1.12)
    pon("burbuja", c["envie"] + 0.1, factor=1.2)
    pon("brillo", c["cierre"])
    return reverb(fx)


def mezclar(voz, musica, fx, T):
    n = int(T * SR)
    voz, musica, fx = (np.pad(a, ((0, max(0, n - len(a))), (0, 0)))[:n] for a in (voz, musica, fx))
    # Ducking con anticipación (como NIETO-21): −11 dB bajo la voz, empieza a bajar 100 ms antes de cada palabra.
    paso = 256
    e = np.sqrt(np.mean(voz[: n // paso * paso, 0].reshape(-1, paso) ** 2, axis=1))
    activo = np.clip((20 * np.log10(e + 1e-9) + 50) / 20, 0, 1)
    anticipo = int(0.1 * SR / paso)
    activo = np.maximum(activo, np.concatenate([activo[anticipo:], np.zeros(anticipo)]))
    sig, g = [], 0.0
    for a in activo:
        g = g + (a - g) * (0.35 if a > g else 0.045)
        sig.append(g)
    gan = 10 ** (-11 * np.repeat(sig, paso) / 20)
    gan = np.pad(gan, (0, n - len(gan)), constant_values=gan[-1])
    musica = musica * gan[:, None]
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


def escribir_cues(c):
    (RAIZ / "cues.js").write_text(
        "// Generado por herramientas/banda_sonora.py — no editar a mano. Instantes (s) de lo que pasa en pantalla,\n"
        "// anclados a las palabras de la locución; los efectos de sonido usan exactamente los mismos.\n"
        f"window.NIETO_CUES = {json.dumps(c, ensure_ascii=False)};\n", encoding="utf-8")


def main():
    import sys
    tiempos = json.loads((RAIZ / "voz" / "tiempos.json").read_text(encoding="utf-8"))
    T = tiempos["duracion"]
    c = calcular_cues(tiempos)
    escribir_cues(c)
    if "--solo-cues" in sys.argv:
        print(f"cues: {len(c)}")
        return
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
