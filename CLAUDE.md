# El Nieto Digital — cómo se trabaja en este repo (para agentes y para el humano)

Este repo es el almacén de trabajo de un **canal de contenido**, no de un producto de software: docs, guiones,
plantillas, bitácora y marca. Se gestiona con el **AgenticFramework** (vault + Dashboard) porque organiza, pero
**adaptado al proyecto**: presupuesto de **4-6 h/semana**, grabación por lotes un sábado al mes, y las fases
caras (grabar, editar) las hace una persona, no un agente. Lo que no pueda verificarse determinista se declara
**juicio humano** y no se disfraza de gate. Decisión completa y su porqué: trayectoria `NIETO-1` del vault.

Empieza por `docs/00-decisiones.md`, `docs/02-guia-de-estilo.md` y `ROADMAP.md`. Lo que dicen no se
reescribe desde una trayectoria: son decisiones del humano (formato ADR); si algo huele mal, se **renegocia**.

## Identidad en el framework
- Proyecto del Dashboard: **El Nieto Digital**, prefijo de trayectoria **`NIETO`** (`NIETO-1`, `NIETO-2`, …).
- Un solo repo: `JavierCervilla/ElNietoDigital`. La web (`elnietodigital.com`) vivirá en `web/` de este repo.

## Un vídeo = una trayectoria (y un issue como ficha)
- **Cada vídeo, corto o taller es una trayectoria `NIETO-n`** en el Dashboard, con su rama y su PR draft al
  nacer, y su plan en `Contexto_Base_SRE/trayectorias/NIETO-n/` del vault (framework).
- El **issue de GitHub se mantiene** como ficha pública ligera (plantillas en `.github/ISSUE_TEMPLATE/`): gancho,
  pilar, plataformas, consentimiento. Título con el TID: `[LARGO] NIETO-4 · La estafa del "hola mamá"`. El
  plan enlaza el issue y el issue enlaza el PR. **No hay tablero de GitHub Projects ni milestones**: el kanban
  es el Dashboard (un solo tablero).
- **Lote mensual = épica**: el sábado de grabación se registra como épica `NIETO-n` y cada pieza del lote es
  una trayectoria-hija (`trajectory-create --parent`). Una hija en `done` avanza la épica sola.
- **Ramas: una sola convención**, `claude/NIETO-n-<formato>-<slug>` (`claude/NIETO-4-largo-estafa-hola-mama`,
  `claude/NIETO-5-corto-hola-mama`, `claude/NIETO-9-docs-plan-q1`). Se retiran `video/` y `docs/`.
- Guiones: el borrador vive **en la rama de su trayectoria** en `guiones/` con `estado:` en el frontmatter;
  al publicarse se mueve a `guiones/publicados/AAAA-MM-DD-slug.md`. `guiones/borradores/` ya no hace falta.

## Los seis TODOs canónicos de una trayectoria de vídeo
Son el kanban del README, convertidos en TODOs del Dashboard (se crean con `todo-add` al abrir la trayectoria):

| # | TODO | Quién | Estado de la trayectoria |
|---|---|---|---|
| 1 | Idea aprobada (gancho + pilar + plataformas) | humano + arquitecto | `planning` |
| 2 | Guion escrito con la plantilla y revisado (guía de estilo) | agente/humano | `planning` |
| 3 | Grabado (lote) | humano | `executing` |
| 4 | Editado + subtítulos + miniatura (checklist de producción) | humano | `executing` |
| 5 | Publicado en cada red con descripción propia | humano | `verifying` |
| 6 | Ficha de métricas a 7 y 30 días + aprendizaje | humano/agente | `done` al cerrar los 30 d |

Una trayectoria de **docs** (plan, dosier, bitácora) lleva sus propios TODOs, normalmente 2-3.

## Las cinco fases, redimensionadas a 4-6 h/semana
1. **Negociación (≤ 15 min por pieza)**: aprobar gancho y guion contra `docs/02-guia-de-estilo.md` y
   `docs/07-etica-legal-riesgos.md`. Si aparece alguien más, consentimiento **antes** de grabar.
2. **Descomposición**: los seis TODOs, automáticos. Nada que planificar más allá.
3. **Ejecución**: grabar y editar (humano). El agente redacta guiones, descripciones, capítulos, hashtags.
4. **Cierre**: `plantillas/checklist-produccion.md` + gate de contenido en verde + **evaluación entre pares**
   (dos personas mayores confirman que se entiende sin ayuda — es el *verificador* de este proyecto y no lo
   sustituye ningún script). Ante un fallo tras publicar: **fix forward** (nota fijada, corto de corrección),
   nunca borrar sin dejar rastro.
5. **Conocimiento**: `plantillas/ficha-video.md` a 7 y 30 días → `bitacora/` (domingo, 15 min) →
   `lecciones_destiladas.md` del vault cuando la lección sea reutilizable.

## Definition of Done de cualquier PR de este repo
- Trayectoria registrada (el hook `trajectory-gate` bloquea el commit si no la hay; escape `[skip-traj]`).
- `scripts/gate-contenido.sh` en verde (lo corre el CI; en local: `bash scripts/gate-contenido.sh`).
- `CHANGELOG.md` con la entrada de la trayectoria y `ROADMAP.md` con los checkboxes que completa, **en el
  mismo PR**. El Dashboard los renderiza.
- Sin datos personales ni apellidos ni direcciones. Lo primero lo comprueba el gate; **apellidos, direcciones
  y tono son juicio humano** (marcados así en el PR template).
- Mensajes de responsabilidad (salud, dinero, IA) cuando aplique: se declara en el frontmatter del guion
  (`responsabilidad:`) y el gate exige la sección rellena.
- CI en verde. Después, merge y `trajectory-close.sh` (ledger, plan a `done`, sentinela).

## Gates: qué muerde y qué no (medido, no prometido)
| Gate | En este repo |
|---|---|
| `trajectory-gate.sh` (hook) | **Muerde**: cualquier `.md` fuera del vault es "producción". |
| `scripts/gate-contenido.sh` (CI) | **Muerde**: privacidad, frontmatter de guiones publicados, responsabilidad, roadmap/changelog. Exit codes 0/1/2/3/4 y `--self-test`. |
| `anti-slop-gate.sh` / `code-anti-slop` | Silencioso hasta que exista `web/` (solo mira código). Se instala con el scaffolder al abrir la web. |
| `ui-canvas-gate.sh` / lienzo | Solo para `web/` y plantillas visuales (miniatura, banner): **lienzo antes de implementar**, como ya se hizo con el logo (D7). |
| `security-gate` | Reducido a secretos + privacidad hasta que haya web; entonces escalera completa. |
| `codebase-memory` | N/A sin código. |

## Roles del enjambre, traducidos
- **arquitecto**: negocia gancho/guion, mantiene `docs/00-decisiones.md` y el plan de contenido.
- **planificador**: crea la épica del lote y sus hijas con los seis TODOs.
- **implementador**: escribe guiones, descripciones, capítulos; más adelante la web.
- **verificador**: gate de contenido + checklist + recoge el veredicto de los dos pares.
- **seguridad**: secretos y privacidad en cada PR; consentimientos fuera del repo.
- **qa / qa-adversario**: solo la web.

## Lo que sigue siendo verdad del README
Presupuesto 4-6 h/semana (si no cabe, se recorta el plan, no la vida); labels `pilar:*`, `plat:*`, `formato:*`,
`prio:*`, `necesita-consentimiento`; archivos `AAAA-MM-DD-slug.md`; privacidad del creador (nombre de pila);
lo que **no** es el canal.
