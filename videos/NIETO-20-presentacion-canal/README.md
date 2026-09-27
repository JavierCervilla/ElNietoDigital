# NIETO-20 · Vídeo de presentación del canal (narrado, 62 s)

Tráiler **con voz** que cuenta de qué va El Nieto Digital y cómo es su flow: cada vídeo, una cosa nueva paso a
paso o un peligro nuevo que reconocer, y entre todos, quien aprende enseña a otro. Pensado como tráiler del
canal de YouTube y para el post fijado en Facebook e Instagram.

- Formatos: horizontal 1920×1080 (16:9) para YouTube y Facebook, y **vertical 1080×1920 (9:16) para Shorts, Reels y
  TikTok** (NIETO-22). Los dos: 30 fps, 62,0 s, H.264 + AAC, −16 LUFS, pico ≤ −1,5 dBTP, misma voz y misma banda.
- Sonido (NIETO-21): música de Eleven Music y efectos de ElevenLabs, editados a imagen sobre los mismos cues.
- Fuente: composiciones [HyperFrames](https://hyperframes.heygen.com) (HTML + un único timeline GSAP en pausa). El
  MP4 **no se versiona**: se regenera con los comandos de abajo.
  - `animacion.js`: el timeline, **compartido** por los dos formatos. Lo que cambia entre ellos no está ahí: son
    los recorridos de `window.NIETO_FORMATO` (la mano, el logotipo, la red, la cámara…), que declara cada
    `index.html`, y las posiciones de `estilos.css`.
  - `index.html` + `estilos.css`: el horizontal.
  - `vertical/index.html`: el vertical. Carga `estilos.css` y solo sobrescribe posiciones y tamaños; el resto de
    `vertical/` son enlaces simbólicos a los recursos compartidos (HyperFrames lee el `index.html` de una carpeta).

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
   PSOLA de Praat (sin cambiar el tono ni el timbre) y coloca cada frase en el montaje.
   - Hasta NIETO-24 se ralentizaba con Rubber Band, y la voz sonaba «un poco metálica».
   - En un A/B con la misma toma, sin estirar sonaba limpia: la culpa era del vocoder de fase, no de la voz.

   Salen `tiempos.js` (cada palabra con su
   tiempo: subtítulos) y la envolvente de la voz (la onda de la etiqueta). Arranques de palabra tras pausa
   medidos contra la energía real: ±15 ms.
4. `herramientas/banda_sonora.py` deriva los **cues** de pantalla de las palabras (`cues.js`: la animación, los
   efectos y la música leen los mismos números).
5. `herramientas/generar_sonido.py` pide a ElevenLabs la música y los efectos y los congela en `sonido/` con su
   manifiesto (`sonido/fuentes.json`: petición exacta y sha256). La música se compone **a imagen** con Eleven
   Music v2.5: una sección por escena, con la duración que dan los cues. Se generaron cuatro tomas y se eligió una
   con `herramientas/evaluar_musica.py` y medidas (la que menos tapa la banda de la voz y termina limpia).
6. `banda_sonora.py` edita esas fuentes contra los cues, como un editor musical:
   - El modelo respeta la duración de las secciones pero no la dinámica que se le pide (medido), así que la
     dinámica se lleva en la mezcla: más oscura en la alerta, casi nada en la confesión de la voz IA.
   - La floración de «Respire.» es el acorde final de la propia pieza (Fa mayor): al revés como *swell* y al
     derecho bajo «El móvil no muerde».
   - El acorde final ataca en «Suscríbase.» todavía oscuro y **se abre cuando la mano pulsa el botón**.
   - El latido grabado no aceleraba: se re-secuencia de 64 a 118 ppm.
   - Cada efecto se alinea por su ataque real, no por el inicio del fichero.
   - La música se agacha bajo la voz con anticipación de 100 ms (−11 dB).
   - En habla plena (ventanas de 100 ms a menos de 12 dB del máximo de la voz), la voz queda 23,3 dB por encima
     de la música de mediana y 16,8 dB en el percentil 10.

La mano es el hilo: tiembla con miedo a tocar al principio, se detiene «ante la duda» y al final pulsa
«Suscribirse» con seguridad. El móvil que asusta se convierte en la mascota, y la mascota en el logotipo.

## El vertical (Shorts, Reels, TikTok)
No es un recorte del horizontal: cada escena se recompone en 9:16 y respeta las zonas que tapa la interfaz de las
plataformas (nada importante por encima de y≈240 ni por debajo de y≈1500, ni en la columna de botones de la
derecha). Los subtítulos van en dos líneas equilibradas a 54 px justo encima de esa zona; en la alerta, la mano
entra por la derecha para no tapar «Ante la duda, no toque nada», que en vertical va debajo del móvil. Duración:
62 s, dentro de lo que admiten Shorts y Reels (hasta 3 min) y TikTok.

Al compartir el timeline, el horizontal se comprobó **píxel a píxel** contra 30 fotogramas de antes del cambio: 29
idénticos. El distinto (8,7 s) destapó un fallo de determinismo que el vídeo ya tenía: la jerga salía en orden
`from: "random"` de GSAP (`Math.random`), y dos renders del mismo fotograma no coincidían. Ahora el orden sale de
un barajado con semilla.

## Marca (D7) y guía de estilo
- Solo naranja `#C8461F`, azul `#1F2A44` y crema `#FBF7F0`; sobre azul, el naranja va detrás del texto crema.
- El símbolo no se gira ni se deforma: escala uniforme y expresión (sonrisa que se dibuja, parpadeo, guiño). El
  logotipo usa los trazados exactos de `marca/logo-horizontal-color.svg`.
- Subtítulos siempre (Atkinson Hyperlegible 50 px), por frases, con la palabra que suena subrayada.

## Cómo regenerar el vídeo
Necesita Node ≥ 22, FFmpeg, Chrome/Chromium y Python 3 con numpy, scipy y praat-parselmouth
(`pip install praat-parselmouth`: el PSOLA que ralentiza la voz).

```bash
cd videos/NIETO-20-presentacion-canal
bash herramientas/construir_audio.sh          # tiempos, cues y mezcla desde las fuentes congeladas (sin red)
export HYPERFRAMES_NO_TELEMETRY=1 DO_NOT_TRACK=1
env -u GEMINI_API_KEY npx --yes hyperframes@0.8.80 check .            # horizontal
env -u GEMINI_API_KEY npx --yes hyperframes@0.8.80 check vertical     # vertical
env -u GEMINI_API_KEY npx --yes hyperframes@0.8.80 render . --quality high --fps 30 \
  --output /tmp/el-nieto-digital-presentacion.mp4
env -u GEMINI_API_KEY npx --yes hyperframes@0.8.80 render vertical --quality high --fps 30 \
  --output /tmp/el-nieto-digital-presentacion-vertical.mp4
```

`env -u GEMINI_API_KEY`: si esa clave está en el entorno, `hyperframes snapshot` manda los fotogramas a Gemini
para describirlos por defecto (`--describe false` lo apaga). Aquí no se quiere.

Para cambiar el guion: editar `voz/guion.json`, `ELEVENLABS_API_KEY=… python3 herramientas/generar_voz.py`,
`pip install faster-whisper && python3 herramientas/verificar_voz.py`, y después los comandos de arriba. Si
cambian los tiempos de las escenas, la música se regenera a imagen: `generar_sonido.py --solo musica-calma
--candidata --semilla N` (varias), `evaluar_musica.py`, y `generar_sonido.py --elegir musica-calma --semilla N`.

## Créditos de terceros
- Locución: ElevenLabs (eleven_v3), voz diseñada para el canal. Voz sintética, declarada en pantalla.
- `fonts/`: Nunito y Atkinson Hyperlegible, SIL Open Font License 1.1 (Google Fonts).
- `vendor/gsap.min.js`: GSAP 3.15.0 © GreenSock, bajo su licencia estándar (https://gsap.com/standard-license).
- Música: Eleven Music (music_v2_5) y efectos: ElevenLabs Sound Effects (eleven_text_to_sound_v2), generados
  para este vídeo (`sonido/fuentes.json`). El uso comercial (p. ej. si el canal se monetiza) depende del plan de
  la cuenta de ElevenLabs con que se generaron: comprobarlo antes de monetizar.
