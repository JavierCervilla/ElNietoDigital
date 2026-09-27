# NIETO-19 · Vídeo de presentación del canal (15 s)

Tráiler **sin audio** de 15 segundos, hecho solo con gráficos en movimiento, que cuenta **de qué va** el canal
y **cómo es su flow**: cada vídeo le deja sabiendo hacer una cosa nueva o reconociendo un peligro nuevo, y
la comunidad se ayuda entre sí. Pensado para la cabecera de YouTube y para el post fijado en Facebook e
Instagram.

- Formato: 1920×1080 (16:9), 30 fps, 15,0 s, sin pista de audio.
- Fuente: `index.html` (composición [HyperFrames](https://hyperframes.heygen.com): HTML + un único timeline
  GSAP en pausa). Todo lo que se ve sale de este fichero; el render es determinista.
- El MP4 **no se versiona** (`*.mp4` está en `.gitignore`): se regenera desde la fuente con el comando de abajo.

## Storyboard (rejilla de 0,5 s)

| t (s) | Escena | Qué se ve | Salida |
|---|---|---|---|
| 0,0 – 2,2 | El ruido | La jerga se amontona (ChatGPT, Código SMS, Cl@ve…), cada vez más deprisa | El móvil sonriente aparece y se lo traga todo |
| 2,2 – 4,2 | La calma | El móvil sonríe y parpadea: «El móvil no muerde.» | Zoom a través de su pantalla |
| 4,2 – 7,0 | De qué va | «La IA y el móvil, sin jerga.» y los cinco pilares, cada uno con su icono vivo | Barrido de bandas naranja y azul |
| 7,0 – 9,6 | Una cosa nueva | «Paso a paso. Sin prisa.»: pasos 1-2-3 en un móvil, con el círculo que enseña dónde pulsar | Llega un mensaje: la cámara entra en él |
| 9,6 – 12,0 | Un peligro nuevo | «Alerta estafa»: el «hola mamá», el sello ESTAFA y «Ante la duda, no toque nada.» | Iris desde el sello |
| 12,0 – 15,0 | Comunidad y cierre | «Nadie se queda atrás.» → logotipo, lema y redes; guiño final | — |

## Marca (D7) y guía de estilo
- Solo los tres colores de marca: naranja `#C8461F`, azul `#1F2A44`, crema `#FBF7F0`. Nunca texto naranja
  sobre azul (contraste insuficiente): sobre azul, el naranja va detrás del texto crema.
- El símbolo **no se gira ni se deforma**: solo escala uniforme y la expresión de la cara (la sonrisa que se
  dibuja, el parpadeo, el guiño). El logotipo del cierre usa los trazados de `marca/logo-horizontal-color.svg`.
- Nunito (titulares) y Atkinson Hyperlegible (texto), grandes. Tratamiento de usted; el lema se mantiene tal cual.

## Cómo regenerar el vídeo
Necesita Node ≥ 22, FFmpeg y Chrome/Chromium.

```bash
export HYPERFRAMES_NO_TELEMETRY=1 DO_NOT_TRACK=1
npx --yes hyperframes@0.8.80 check  videos/NIETO-19-promo-canal
npx --yes hyperframes@0.8.80 render videos/NIETO-19-promo-canal --quality high --fps 30 \
  --output /tmp/el-nieto-digital-presentacion-15s.mp4
```

Para editar la pieza a mano, `npx --yes hyperframes@0.8.80 preview videos/NIETO-19-promo-canal` abre el
editor con la línea de tiempo.

## Créditos de terceros
- `fonts/`: Nunito y Atkinson Hyperlegible, SIL Open Font License 1.1 (Google Fonts).
- `vendor/gsap.min.js`: GSAP 3.15.0 © GreenSock, bajo su licencia estándar (https://gsap.com/standard-license).
  Va vendorizado porque el Chrome headless del render no alcanza la CDN y así el vídeo no depende de la red.
