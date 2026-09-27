# NIETO-20 · Vídeo de presentación del canal (narrado, 62 s)

Tráiler **con voz** que cuenta de qué va El Nieto Digital y cómo es su flow: cada vídeo, una cosa nueva paso a
paso o un peligro nuevo que reconocer, y entre todos, quien aprende enseña a otro. Pensado como tráiler del
canal de YouTube y para el post fijado en Facebook e Instagram.

- Formato: 1920×1080 (16:9), 30 fps, 62,0 s, H.264 + AAC. Sonoridad −16 LUFS, pico ≤ −1,5 dBTP.
- Fuente: `index.html` (composición [HyperFrames](https://hyperframes.heygen.com): HTML + un único timeline GSAP
  en pausa). El MP4 **no se versiona**: se regenera con los comandos de abajo.

## La voz es IA, y se dice
La locución la ha generado **ElevenLabs** con una voz diseñada para el canal (Voice Design v3: voz masculina
joven, española peninsular, cálida y pausada). Como manda la guía de estilo («Qué evitar») y
`docs/07-etica-legal-riesgos.md` («Transparencia sobre IA»), se declara **dos veces**: la etiqueta «Voz generada
con IA» está en pantalla del primer al último fotograma (una nota de voz, como las de WhatsApp, cuya onda se
mueve con la locución real), y la propia voz lo cuenta al final: «esta voz la ha creado una inteligencia
artificial. Aquí, siempre se lo diremos.»

## Guion
| # | Escena | Locución |
|---|---|---|
| 1 | El ruido | ¿Le suena? Un mensaje que no entiende… una palabra rara… y ese miedo a tocar algo. |
| 2 | La calma | Respire. El móvil no muerde. |
| 3 | Qué es | Esto es El Nieto Digital: la inteligencia artificial y el móvil, explicados con calma y sin palabras raras. |
| 4 | De qué va | Aprenderá a protegerse de las estafas, a sacarle partido a la inteligencia artificial y a hacer sus trámites desde casa. |
| 5 | Una cosa nueva | Cada vídeo, una sola cosa: paso a paso, con el móvil en pantalla, y le señalamos dónde pulsar. |
| 6 | Un peligro nuevo | Si aparece una estafa nueva, le avisamos. Y recuerde: ante la duda, no toque nada. |
| 7 | Entre pares | Aquí, quien aprende, enseña a otro. Nadie se queda atrás. |
| 8 | Transparencia | Una cosa más: esta voz la ha creado una inteligencia artificial. Aquí, siempre se lo diremos. |
| 9 | Cierre | Suscríbase. Nos vemos en el próximo vídeo. |

No se promete lo que aún no existe: ni cadencia de publicación ni «nuestra comunidad de WhatsApp» (Fase 1 del
roadmap). Se cuenta el principio («quien aprende, enseña a otro»).

## Cómo está hecho
Todo se ancla a la **alineación por carácter** de la locución, no a ojo:

1. `herramientas/generar_voz.py` pide el guion entero a ElevenLabs **en una sola toma** (una interpretación, un
   tono) a `/with-timestamps`, y la congela en `voz/toma.mp3` + `voz/toma.json`. Es el único paso con red y con
   coste; no hace falta repetirlo para renderizar.
2. `herramientas/verificar_voz.py` transcribe cada frase con Whisper (local) y la compara con el guion: una voz
   sintética puede comerse una palabra, y eso se mide, no se escucha a ojo. Resultado de esta toma: 9/9 frases
   sin una sola diferencia.
3. `herramientas/montar_voz.py` afina la alineación contra el audio (la de ElevenLabs adelantaba hasta 0,5 s las
   palabras tras una pausa y derivaba un 0,3 %), añade respiros tras la puntuación, ralentiza al 90 % con
   Rubber Band (sin cambiar el tono) y coloca cada frase en el montaje. Salen `tiempos.js` (cada palabra con su
   tiempo: subtítulos) y la envolvente de la voz (la onda de la etiqueta). Arranques de palabra tras pausa
   medidos contra la energía real: ±15 ms.
4. `herramientas/banda_sonora.py` deriva los **cues** de pantalla de las palabras (`cues.js`: la animación y los
   efectos leen los mismos números), compone la música a imagen (tensión con latido que se corta en seco, el
   acorde que florece en «Respire.», un acorde por idea, casi nada en la confesión de la voz IA) y mezcla con la
   música agachada bajo la voz (≈ 14 dB por debajo mientras se habla).

La mano es el hilo: tiembla con miedo a tocar al principio, se detiene «ante la duda» y al final pulsa
«Suscribirse» con seguridad. El móvil que asusta se convierte en la mascota, y la mascota en el logotipo.

## Marca (D7) y guía de estilo
- Solo naranja `#C8461F`, azul `#1F2A44` y crema `#FBF7F0`; sobre azul, el naranja va detrás del texto crema.
- El símbolo no se gira ni se deforma: escala uniforme y expresión (sonrisa que se dibuja, parpadeo, guiño). El
  logotipo usa los trazados exactos de `marca/logo-horizontal-color.svg`.
- Subtítulos siempre (Atkinson Hyperlegible 50 px), por frases, con la palabra que suena subrayada.

## Cómo regenerar el vídeo
Necesita Node ≥ 22, FFmpeg (con rubberband), Chrome/Chromium y Python 3 con numpy y scipy.

```bash
cd videos/NIETO-20-presentacion-canal
bash herramientas/construir_audio.sh          # tiempos, cues, música y mezcla (sin red)
export HYPERFRAMES_NO_TELEMETRY=1 DO_NOT_TRACK=1
env -u GEMINI_API_KEY npx --yes hyperframes@0.8.80 check .
env -u GEMINI_API_KEY npx --yes hyperframes@0.8.80 render . --quality high --fps 30 \
  --output /tmp/el-nieto-digital-presentacion.mp4
```

`env -u GEMINI_API_KEY`: si esa clave está en el entorno, `hyperframes snapshot` manda los fotogramas a Gemini
para describirlos por defecto (`--describe false` lo apaga). Aquí no se quiere.

Para cambiar el guion: editar `voz/guion.json`, `ELEVENLABS_API_KEY=… python3 herramientas/generar_voz.py`,
`pip install faster-whisper && python3 herramientas/verificar_voz.py`, y después los comandos de arriba.

## Créditos de terceros
- Locución: ElevenLabs (eleven_v3), voz diseñada para el canal. Voz sintética, declarada en pantalla.
- `fonts/`: Nunito y Atkinson Hyperlegible, SIL Open Font License 1.1 (Google Fonts).
- `vendor/gsap.min.js`: GSAP 3.15.0 © GreenSock, bajo su licencia estándar (https://gsap.com/standard-license).
- Música y efectos: sintetizados en `herramientas/banda_sonora.py`, sin muestras de terceros.
