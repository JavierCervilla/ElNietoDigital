#!/usr/bin/env python3
"""Banda sonora a imagen: música y efectos de ElevenLabs congelados en sonido/, editados contra los cues.

  - Los CUES (instantes donde pasa algo en pantalla) se derivan de las palabras de la locución y se emiten
    en cues.js: la animación y los efectos leen LOS MISMOS números, así que el «ding» cae en el fotograma
    en que llega el mensaje. generar_sonido.py también los usa para dar a cada sección de la música la
    duración de su escena.
  - Música (Eleven Music, sonido/musica-calma.mp3, alineada a «Respire.»): el modelo respeta la duración de
    las secciones pero no la dinámica que se le pide (medido en cuatro tomas), así que la dinámica se lleva
    aquí, como haría un editor musical: más oscura en la alerta (−2 dB y paso bajo), −4 dB en «entre pares» (su
    crescendo dejaba la voz a 6 dB), casi nada en la confesión de la voz IA (−12 dB y paso bajo). El acorde final
    ataca en «Suscríbase.» todavía oscuro y se abre al pulsar el botón; bajo el logotipo, +9 dB. La floración de «Respire.» es ese mismo acorde final (Fa mayor): al revés como swell que
    desemboca en la palabra y al derecho bajo «El móvil no muerde», así no hay choque de tonalidad.
  - Tensión (0 → «…tocar algo.»): sonido/musica-tension.mp3 + el latido grabado, re-secuenciado aquí para que
    se acelere de 64 a 118 ppm (el generado no aceleraba); corte en seco antes del silencio.
  - Efectos: cada uno se normaliza a un pico común y se alinea por su ATAQUE real (o por su pico, en los
    barridos), no por el inicio del fichero: algunos traen 140-225 ms de silencio delante.
  - Mezcla: la música se agacha bajo la voz (ducking por la envolvente de la voz), sonoridad final −16 LUFS
    y pico real ≤ −1,5 dBTP (loudnorm en dos pasadas, lineal).

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
        "vibra": round(ini["01"] - 0.6, 3),  # vibra y DESPUÉS habla: el zumbido no pisa «¿Le suena?»
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
        "fin_voz": tiempos["lineas"][-1]["t1"],
        "fin": tiempos["duracion"],
    }
    c["transiciones"] = [round(c[k] - 0.2, 3) for k in ("escena3", "escena4", "escena5", "escena6", "escena7", "escena9")]
    return c




# ── utilidades ─────────────────────────────────────────────────────────────────────────────────────────
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

# ── fuentes congeladas ─────────────────────────────────────────────────────────────────────────────────
def db(v):
    return 10 ** (np.asarray(v, float) / 20)


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


def ultimo_ataque(x):
    """El último ataque fuerte de la pieza: subida ≥ 6 dB en 50 ms que llega a menos de 16 dB del máximo
    (con 25 dB se colaba una ondulación de la cola, −32 → −27 dB, un segundo después del acorde final)."""
    e = energia(x, 0.01)
    subida = e[5:] - e[:-5]
    k = np.flatnonzero((subida > 6) & (e[5:] > e.max() - 16))
    return float(k[-1] + 5) * 0.01


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
    r = c["respire"]

    # 1 · Tensión: entra en 2 s y se corta en seco con «…tocar algo.»; el latido se acelera de 64 a 118 ppm.
    fin = c["congela"]
    tension = tramo(cargar("musica-tension"), 0, fin, 0.04)
    tension *= np.minimum(1, np.arange(len(tension)) / SR / 2.0)[:, None]
    sumar(musica, tension, 0, db(-4))
    lat = cargar("latido")
    golpes = golpes_latido(lat)
    tb, k = 0.35, 0
    while tb < fin - 0.45:
        g = golpes[k % len(golpes)]
        sumar(musica, tramo(lat, g - 0.04, g + 0.62), tb, db(-4) * (0.55 + 0.45 * tb / fin))
        tb += 60 / (64 + 54 * (tb / fin) ** 1.5)
        k += 1

    # 2 · «Respire.»: el acorde final de la propia pieza, al revés (swell) y al derecho.
    calma = cargar("musica-calma")
    ta = ultimo_ataque(calma)
    swell = tramo(calma, ta - 0.01, ta + 1.5, 0.02)[::-1].copy()
    swell *= (np.linspace(0, 1, len(swell)) ** 2)[:, None]
    sumar(musica, swell, r - len(swell) / SR, db(-5))
    acorde = tramo(calma, ta - 0.01, ta + 4.4, 0.02)
    acorde[-int(1.4 * SR):] *= np.linspace(1, 0, int(1.4 * SR))[:, None]
    sumar(musica, acorde, r - 0.01, db(-3))

    # 3 · La pieza, alineada a «Respire.» como se compuso, con la dinámica llevada a imagen.
    t = np.arange(len(calma)) / SR + r
    # El acorde final ataca justo en «Suscríbase.»: entra oscuro y bajo bajo la palabra (a pleno la tapaba: 1,8 dB
    # de margen) y se ABRE —filtro y ganancia— cuando la mano pulsa el botón; crece un poco más al callar la voz.
    abre = c["suscribase_toque"]
    marcas = [0, c["escena6"] - 0.3, c["escena6"] + 0.3, c["escena7"] - 0.3, c["escena7"] + 0.3,
              c["escena8"] - 0.4, c["escena8"] + 0.6, abre - 0.05, abre + 0.35, c["fin_voz"] + 0.3,
              c["fin_voz"] + 1.2, 1e9]
    gan = db(np.interp(t, marcas, [0, 0, -2, -2, -4, -4, -12, -12, 5, 5, 9, 9]))
    oscuro = np.interp(t, marcas, [0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 0, 0])[:, None]
    cuerpo = (calma * (1 - oscuro) + paso_bajo(calma, 900) * oscuro) * gan[:, None]
    sumar(musica, cuerpo, r)
    # La pieza trae mucho grave (36 % de su energía bajo 150 Hz): paso alto a 60 Hz y −3 dB por debajo de 150 Hz,
    # para que en una tele no retumbe bajo la voz.
    musica = sosfilt(butter(2, 60, "high", fs=SR, output="sos"), musica, axis=0)
    return musica - 0.3 * paso_bajo(musica, 150)


# ── efectos ────────────────────────────────────────────────────────────────────────────────────────────
NIVELES = {"vibra": -16, "ding": -9, "pop": -15, "barrido": -17, "respiro": -12, "alerta": -9, "sello": -7,
           "toque": -11, "burbuja": -14, "brillo": -11}


def efectos(c, T):
    fx = pista(T)
    S = {n: cargar(n, mono=True) for n in NIVELES}

    def pon(n, t, extra=0.0, por="arranque", factor=None, pan=0.0):
        x = S[n] if factor is None else tono(S[n], factor)
        sumar(fx, x, t - (arranque(x) if por == "arranque" else pico(x)), db(NIVELES[n] + extra), pan)

    S["vibra"] = tramo(S["vibra"], 0, 0.55, 0.06)
    pon("vibra", c["vibra"])
    pon("ding", c["mensaje"], pan=0.15)
    for k, t in enumerate(c["jerga"]):
        pon("pop", t, extra=-2 + 2 * k / len(c["jerga"]), factor=[0.85, 1.0, 1.15, 0.92, 1.25, 1.06][k % 6],
            pan=((k * 5) % 7 - 3) * 0.2)
    pon("respiro", c["respire"] - 0.02, extra=-2, por="pico")
    for t in c["transiciones"]:
        pon("barrido", t, por="pico")
    pon("burbuja", c["ia"] + 0.05)
    pon("burbuja", c["movil"] + 0.05, factor=0.9)
    pon("barrido", c["traduce"] + 0.25, extra=-4, por="pico")
    for k, t in enumerate(c["tarjetas"]):
        pon("pop", t, factor=0.9 + 0.12 * k)
    pon("pop", c["una"], factor=1.2)
    for k, t in enumerate(c["pasos"]):
        pon("burbuja", t, factor=1.0 + 0.1 * k)
    pon("toque", c["toque"])
    pon("ding", c["estafa_llega"], extra=-1)
    pon("alerta", c["alerta"])
    pon("sello", c["sello"])
    pon("burbuja", c["aprende"] + 0.1, factor=0.9)
    pon("burbuja", c["otro"])
    for k, t in enumerate(c["red"]):
        pon("burbuja", t + 0.2, extra=-4, factor=[1.05, 1.12, 1.2, 1.26, 1.33, 1.4, 1.2, 1.33, 1.5][k],
            pan=((k * 3) % 5 - 2) * 0.25)
    pon("toque", c["suscribase_toque"])
    pon("ding", c["suscribase_toque"] + 0.18, extra=-3)
    pon("brillo", c["logo"] + 0.05)
    pon("brillo", c["guino"], extra=-2)
    return reverb(fx, rt60=1.2, mezcla=0.15, semilla=13)


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
    # Ducking con anticipación: la música baja hasta −11 dB mientras habla la voz y empieza a bajar 100 ms ANTES
    # de cada palabra (offline se puede mirar el futuro); sin ella, los arranques de frase quedaban a 3-5 dB de
    # la música. Ataque ~60 ms, relajación ~450 ms.
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
