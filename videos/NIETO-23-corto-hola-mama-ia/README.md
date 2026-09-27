# NIETO-23 · Piloto: el corto «hola mamá» hecho entero con IA (53 s, vertical)

**Qué es:** una prueba. El primer corto del lote 1 (guion de NIETO-10, «Si dice "hola mamá, he cambiado de
número", es estafa», en borrador en el PR #18) producido **sin la cara ni la voz del creador**: voz de IA, música
y efectos de ElevenLabs y animación generada por un agente. Sirve para decidir si los cortos pueden hacerse así.

**Qué no es:** un cambio de decisión. D3 («De cara, con perfil bajo») sigue en pie: el creador sale en pantalla.
Si el humano quiere producir los cortos así, eso es un ADR nuevo suyo en `docs/00-decisiones.md`. Tampoco hay
avatar ni cara sintética: un rostro generado, en un canal que enseña a desconfiar de los deepfakes, contradice la
guía de estilo. Presentan la mascota y la mano, como en el tráiler (NIETO-20).

- Formato: 1080×1920 (9:16), 30 fps, 53,0 s, H.264 + AAC, −16 LUFS, pico ≤ −1,5 dBTP. Para Reels (Instagram y
  Facebook), Shorts y TikTok.
- Zonas de interfaz libres: nada importante por encima de y≈240 ni por debajo de y≈1500, y nada en la columna de
  botones de la derecha (x > 920) entre y≈850 y y≈1650. Los subtítulos van centrados en x≈500 y no la pisan.
- Fuente: composición [HyperFrames](https://hyperframes.heygen.com) en `index.html` (HTML + un único timeline
  GSAP en pausa). El MP4 **no se versiona**: se regenera con los comandos de abajo.

## El guion es el de NIETO-10, palabra por palabra
Se locuta solo lo que su guion marca como dicho (120 palabras). El texto en pantalla sigue su sección «Texto en
pantalla»:
- el gancho «"Hola mamá, he cambiado de número" = ESTAFA»;
- el chat de ejemplo con el número tapado y sin nombre;
- las tres señales, que aparecen una a una;
- «Llame al número DE SIEMPRE» y «No borre el número antiguo»;
- el 017 con su horario;
- el mensaje de responsabilidad, en pantalla durante el cierre y sin locutar, como pide el guion.

| # | Escena | Locución |
|---|---|---|
| 1 | Gancho | Si dice «hola mamá, he cambiado de número», es estafa. |
| 2 | Llega | Llega por WhatsApp, desde un número que usted no conoce. |
| 3 | Suplanta | Dice ser su hijo o su hija. Que se le ha roto el móvil. Que guarde este número nuevo. |
| 4 | Dinero | Y al rato, le pide dinero con prisa: una transferencia o un Bizum, para un problema que no puede esperar. |
| 5 | Qué hacer | Qué hacer: no conteste y no pague. |
| 6 | Llame | Llame a su hijo al número DE SIEMPRE, el que ya tenía guardado. Y no borre nunca ese número. |
| 7 | La regla | Nadie de confianza le pide dinero con prisa por un mensaje. |
| 8 | Recuerde | Y recuerde: ante la duda, no toque nada y pregunte a alguien de confianza. |
| 9 | Llamada a la acción | Si le ha servido, envíeselo a alguien que lo necesite. |

## La IA se dice
- «Voz generada con IA» está en pantalla en todos los fotogramas, como una nota de voz cuya onda se mueve con la
  locución real.
- Al publicar, marque la casilla de contenido sintético de cada red:
  - YouTube: «Contenido alterado o sintético»;
  - TikTok: «Contenido generado por IA»;
  - Instagram y Facebook: la etiqueta de IA.
- Añada a cada descripción: «Voz, música y animación hechas con inteligencia artificial.»

## Cómo está hecho
Mismo sistema que el tráiler (NIETO-20/21/22), a ritmo de corto:

1. **Voz.**
   - `herramientas/generar_voz.py` pide el guion entero a ElevenLabs en **una sola toma**, con la misma voz del
     canal. La toma se congela en `voz/toma.mp3` + `voz/toma.json`.
   - `herramientas/verificar_voz.py` la transcribe con Whisper. Se pidieron cuatro tomas:
     - las semillas 2023, 7 y 31 fallaban en el gancho: «Si bife», «hora el mamá» y «oral mamá»;
     - la 11 salió **9/9 frases sin una diferencia**, y es la que se usa.
   - Una locución sintética puede comerse justo la primera palabra, que en un corto es la que más importa.
2. **Montaje.** `herramientas/montar_voz.py`:
   - afina la alineación contra el audio;
   - añade respiros;
   - ralentiza al 88 % con Rubber Band.

   Queda en ~2,6 palabras/s con pausas: la guía pide hablar despacio y esto aún cabe en 53 s.
3. **Cues.** `herramientas/banda_sonora.py` deriva de las palabras los *cues* de pantalla (`cues.js`). Así cada
   mensaje del chat llega con su «ding» en la palabra que lo nombra.
4. **Música.** `herramientas/generar_sonido.py` compone la música **a imagen** con Eleven Music. Son dos piezas
   con una sección por escena:
   - la tensión, del gancho a «…no puede esperar»;
   - la calma, de «Qué hacer:» al final.

   Se pidieron dos tomas de cada una y se eligieron midiendo:
   - la tensión que de verdad crece del chat a la presión (la otra era plana);
   - la calma cuyo acorde final se apaga bajo el logotipo.
5. **Efectos.** Diez se reutilizan de NIETO-20, con su misma petición y su sha256 en `sonido/fuentes.json`. Dos
   son nuevos: el tecleo y el tono de llamada.
6. **Mezcla.**
   - La música se agacha bajo la voz con anticipación de 100 ms.
   - En habla plena, la voz queda 23,4 dB por encima de la música (mediana) y 11,5 dB en el percentil 10.
   - El latido se re-secuencia para que se acelere bajo la presión y se corta en seco antes de «Qué hacer:».

## Cómo regenerar el vídeo
Necesita Node ≥ 22, FFmpeg (con rubberband), Chrome/Chromium y Python 3 con numpy y scipy.

```bash
cd videos/NIETO-23-corto-hola-mama-ia
python3 herramientas/montar_voz.py && python3 herramientas/banda_sonora.py   # sin red, desde las fuentes congeladas
export HYPERFRAMES_NO_TELEMETRY=1 DO_NOT_TRACK=1
env -u GEMINI_API_KEY npx --yes hyperframes@0.8.80 check .
env -u GEMINI_API_KEY npx --yes hyperframes@0.8.80 render . --quality high --fps 30 --output /tmp/corto-hola-mama.mp4
```

`env -u GEMINI_API_KEY`: si esa clave está en el entorno, `hyperframes snapshot` manda los fotogramas a Gemini
para describirlos (`--describe false` lo apaga). Aquí no se quiere.

Si el guion cambia en la revisión del PR #18:
1. Edite `voz/guion.json` y ejecute `ELEVENLABS_API_KEY=… python3 herramientas/generar_voz.py --semilla N`.
2. Verifique la toma con `verificar_voz.py`.
3. Si cambian los tiempos de las escenas, regenere la música con
   `generar_sonido.py --solo musica-calma --candidata --semilla N` y después `--elegir`.

## Créditos de terceros
- Locución: ElevenLabs (eleven_v3), la voz diseñada para el canal (Voice Design v3). Voz sintética, declarada en
  pantalla.
- Música (Eleven Music, music_v2_5) y efectos (ElevenLabs Sound Effects, eleven_text_to_sound_v2): generados para
  este vídeo y para NIETO-21 (`sonido/fuentes.json`). El uso comercial depende del plan de la cuenta de ElevenLabs
  con que se generaron: hay que comprobarlo antes de monetizar.
- `fonts/`: Nunito y Atkinson Hyperlegible, SIL Open Font License 1.1 (Google Fonts).
- `vendor/gsap.min.js`: GSAP 3.15.0 © GreenSock, bajo su licencia estándar (https://gsap.com/standard-license).
