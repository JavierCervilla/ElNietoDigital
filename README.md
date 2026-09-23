# El Nieto Digital

**La IA explicada para que no te dejen atrás.**

Canal divulgativo en español sobre inteligencia artificial y vida digital para personas mayores (50+ / 65+), con espíritu intergeneracional: un joven técnico explica con paciencia, y los mayores que aprenden ayudan a otros mayores.

Nace de un principio aprendido en 42 Madrid: **no dejar a nadie atrás**.

## Dónde está el canal
- YouTube: https://www.youtube.com/@elnietodigital (ancla: vídeos largos + Shorts)
- Facebook: página "El Nieto Digital" (red principal para llegar al mayor)
- Instagram: https://www.instagram.com/elnietodigital.es (para el familiar que reenvía; el handle corto no estaba disponible)
- TikTok: https://www.tiktok.com/@elnietodigital (cross-posting)
- Comunidad de WhatsApp: (enlace en la bio)

## Qué hay en este repositorio
Este repo es el almacén de trabajo del canal: dosier, guiones, plantillas y una bitácora del proceso de crear el canal y la comunidad desde cero.

| Carpeta | Contenido |
|---|---|
| `docs/` | Dosier, guía de estilo, plan de contenido, producción, redes, comunidad, ética/legal, relación con Universelle, nombre y marca |
| `guiones/` | Plantillas de guion y guiones ya publicados |
| `plantillas/` | Checklist de producción, ficha de métricas, consentimiento de imagen |
| `bitacora/` | Diario semanal "build in public" |
| `recursos/` | Hashtags y la plantilla de contactos (`contactos-asociaciones.plantilla.md`); la copia con datos reales está ignorada |
| `marca/` | Logo (SVG/PNG), foto de perfil y reglas de uso de la marca |
| `.github/` | Plantillas de issue y PR, y el CI con el gate de contenido |
| `scripts/` | `gate-contenido.sh`: el gate determinista que corre el CI |

Empieza por `docs/00-decisiones.md`, `ROADMAP.md` y `CLAUDE.md` (cómo se trabaja).

## Cómo se trabaja
- **Un vídeo = una trayectoria** del AgenticFramework (`NIETO-n`, con su rama y su PR) **y un issue** como ficha
  pública (plantilla `Nuevo vídeo`). El kanban `Idea → Guion → Grabado → Editado → Publicado → Métricas` son
  los seis TODOs de cada trayectoria en el Dashboard del framework; no hay tablero de GitHub Projects.
- Labels: `pilar:*`, `plat:*`, `formato:*`, `prio:*`, `necesita-consentimiento`.
- Lote mensual de grabación = épica; cada pieza del lote, una trayectoria-hija.
- Ramas: `claude/NIETO-n-<formato>-<slug>`. Archivos de guion publicado: `AAAA-MM-DD-slug.md`.
- Cada PR pasa el gate de contenido (`scripts/gate-contenido.sh`: privacidad, frontmatter de guiones,
  mensajes de responsabilidad, roadmap/changelog) y actualiza `CHANGELOG.md` y `ROADMAP.md`.
- Presupuesto de tiempo: **4-6 h/semana**. Es un hobby; si no cabe en ese tiempo, se recorta el plan, no la vida.
- Detalle operativo (para agentes y humano): `CLAUDE.md`.

## Lo que NO es
No es un canal de humor a costa de los mayores, no da consejo médico ni financiero, no vende cursos ni promete dinero fácil, y no sustituye a las personas: la IA acompaña, no reemplaza.

## Privacidad
El creador aparece con nombre de pila, sin apellido. Los datos de contacto de asociaciones, consentimientos firmados y listas de la comunidad se guardan fuera del repositorio (ver `.gitignore`).
