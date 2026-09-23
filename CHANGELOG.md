# Changelog — El Nieto Digital

Lo más reciente arriba. Una entrada por trayectoria cerrada, en lenguaje de la persona que no vio el PR.

## 2026-09-23 — NIETO-3 · dominios comprados
- `elnietodigital.com` y `elnietodigital.es` están comprados: tachados en el roadmap (Fase 0) y en la
  checklist de registro de nombre y marca.

## 2026-09-23 — NIETO-2 · handle de Instagram y plantilla de contactos
- El handle de Instagram es `@elnietodigital.es` (el corto no estaba disponible); YouTube sigue siendo
  `@elnietodigital`. Actualizado en README, redes, nombre y marca, y como excepción de la decisión D5.
- La plantilla de contactos de asociaciones se versiona sin datos (`recursos/contactos-asociaciones.plantilla.md`);
  la copia rellenada sigue ignorada por git.

## 2026-09-23 — NIETO-1 · el repo entra en el framework con metodología propia
- Repo creado a partir del paquete de arranque del canal (dosier, guía de estilo, plan de contenido,
  producción, redes, comunidad, ética/legal, marca, plantillas, bitácora).
- Metodología de trabajo escrita en `CLAUDE.md`: un vídeo = una trayectoria `NIETO-n` (el issue queda como
  ficha), los seis pasos del kanban como TODOs, lote mensual = épica, una sola convención de ramas.
- Gate de contenido determinista (`scripts/gate-contenido.sh`) y CI: privacidad, frontmatter de guiones
  publicados, mensajes de responsabilidad, formato de roadmap y changelog.
- Diagrama de arquitectura del proyecto en `docs/diagrams/`.
- Plantillas de guion con el campo `responsabilidad:`; PR template separa lo que verifica el gate de lo que es
  juicio humano.
- Decisiones D8 (Dashboard como kanban, sin GitHub Projects de momento) y D9 (la web en `web/` de este repo)
  en `docs/00-decisiones.md`.
