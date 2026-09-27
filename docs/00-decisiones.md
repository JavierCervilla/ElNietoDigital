# Registro de decisiones

Formato tipo ADR: qué se decidió, por qué, y qué haría cambiar la decisión.

## D1 — Nicho principal: personas mayores (2026-09)
**Decisión:** el canal se dirige a mayores 50+/65+, no a programadores jóvenes.
**Por qué:** el nicho de IA para mayores en español está casi vacío de marcas de autor (solo iniciativas institucionales y abuelos virales de entretenimiento); el de devs jóvenes está saturado (midudev, MoureDev, Dot CSV).
**Cambiaría si:** tras 12 meses no hay tracción ni presencial ni digital.

## D2 — El contenido para programadores queda fuera del feed (2026-09)
**Decisión:** no se alternan vídeos de mayores y de devs en el mismo canal.
**Por qué:** el algoritmo aprende una audiencia por canal; mezclar dos audiencias hunde CTR y retención de ambas. Los devs jóvenes aparecen como co-creadores, no como audiencia. Si algún día hay contenido dev, va en cuenta separada, directos o Discord ligado a Universelle.

## D3 — De cara, con perfil bajo (2026-09)
**Decisión:** el creador sale en pantalla. Nombre de pila, sin apellido, sin enlace a Universelle en el feed de mayores, sin dirección concreta.
**Por qué:** los mayores confían en caras; lo faceless se valoró y se descartó. Ser "persona pública" es improbable a la escala prevista y siempre se puede frenar.
**Objetivo personal:** perder la vergüenza de hablar en público, ayudar y ocupar el tiempo, no hacerse conocido.
*Matizada por D10 (2026-09-27): los **cortos**, de momento, sin cara. Los vídeos largos siguen siendo de cara.*

## D4 — Plataformas (2026-09)
**Decisión:** YouTube (ancla) · Facebook (llegar al mayor) · Instagram (llegar al familiar que reenvía) · TikTok y Shorts (cross-posting) · WhatsApp (comunidad).
**Por qué:** en España, 55+: Facebook ~9,6 M > Instagram ~5,9 M > TikTok ~3,0 M (audiencia publicitaria, 2026). Facebook es la red preferida a partir de 46 años (IAB Spain 2025). El distribuidor real es el hijo/nieto de 35-55, que está en Instagram y reenvía por WhatsApp.

## D5 — Nombre: El Nieto Digital (2026-09)
**Decisión:** nombre visible "El Nieto Digital", handle `elnietodigital` en todas las redes, dominio elnietodigital.com. *Excepción (2026-09-23): en Instagram el handle es `elnietodigital.es`, porque el corto no estaba disponible al registrar.*
**Por qué:** cuenta la historia intergeneracional sin explicarla, es cálido, fácil de decir por teléfono y estaba libre en YouTube, TikTok y .com (Instagram/Facebook/.es por confirmar en el momento del registro). Descartados "IA para Mayores" y "Sin miedo a la IA" (ocupados en YouTube). Evitar handles que empiecen por "ia" en minúscula (se lee "la").

## D6 — Es un hobby: 4-6 h/semana (2026-09)
**Decisión:** el plan se dimensiona a 4-6 h/semana con grabación por lotes un sábado al mes.
**Por qué:** compatible con el trabajo de CTO. Si no cabe, se recorta el plan.

## D7 — Logo: el móvil sonriente (2026-09)
**Decisión:** símbolo de un móvil con cara amable, en naranja tostado sobre crema, con logotipo en Nunito ExtraBold.
**Por qué:** es el concepto que un mayor entiende sin explicación ("el móvil no muerde"), funciona en tamaño pequeño y en un solo color. Descartados "Burbujas" (dos generaciones) y "El toque" (dedo que pulsa).
**Archivos:** `marca/`. Editable en el lienzo de diseño de Claude.

## D8 — Se trabaja con el AgenticFramework; el Dashboard es el kanban (2026-09-23)
**Decisión:** el proyecto se gestiona con el AgenticFramework (un vídeo = una trayectoria `NIETO-n`; el issue
queda como ficha pública). El tablero de GitHub Projects y los milestones **se retiran de momento**: el
kanban es el Dashboard del framework y la bitácora es la vista pública (build in public).
**Por qué:** un solo tablero. Dos tableros en paralelo es la forma de que ninguno esté al día con 4-6 h/semana.
**Cambiaría si:** hiciera falta una vista pública del estado de los vídeos que la bitácora no cubra.
**Detalle operativo:** `CLAUDE.md`; trayectoria NIETO-1 del vault.

## D9 — La web vive en este mismo repositorio (2026-09-23)
**Decisión:** la web `elnietodigital.com` (página de enlaces) se construye en `web/` de este repo, no en un
repo aparte.
**Por qué:** un solo CI, un solo `ROADMAP.md`, un solo `CHANGELOG.md`; el gate de contenido y el gate de
código conviven en el mismo pipeline.
**Cambiaría si:** la web creciera hasta necesitar su propio ciclo de despliegue independiente del contenido.

## D10 — Los cortos, sin cara (faceless), a prueba (2026-09-27)
**Decisión:** de momento, los cortos (Reels, Shorts, TikTok) se hacen **sin la cara ni la voz del creador**. Llevan
la voz IA del canal, música y efectos de ElevenLabs y animación con la mascota y la mano, como el piloto NIETO-23.
Los vídeos **largos siguen siendo de cara** (D3).
**Por qué:** el piloto gustó («Me gusta el piloto, sí»). Una vez arreglada la voz (NIETO-24: «mucho mejor, menos
metálica»), se prueba si funcionan: «De momento vamos a dejarlos faceless a ver qué tal funciona».
**Consecuencia:** un corto así no pasa por el sábado de grabación (D6). La voz, el montaje y la miniatura los hace el
agente (`CLAUDE.md`).
**Lo que no cambia:** la IA se dice. «Voz generada con IA» va en pantalla y se marca el contenido sintético en cada
red. No se usa avatar ni cara sintética: un canal que enseña a desconfiar de los deepfakes no puede usarlos (guía de
estilo, «Qué evitar»). Cada pieza sigue teniendo el veredicto del humano y la evaluación entre pares.
**Cambiaría si:** los cortos no retienen: «en caso de que veamos que no tienen retención lo haremos con cara». Se
mira con la «Retención media (%)» de las fichas de métricas a 7 y 30 días (`plantillas/ficha-video.md`) del primer
lote publicado; el umbral lo fija el humano al revisarlas. Está también en los umbrales de la Fase 1 del `ROADMAP.md`.
**Detalle:** trayectorias NIETO-23 (piloto), NIETO-24 (voz) y NIETO-25 (esta decisión) del vault.
