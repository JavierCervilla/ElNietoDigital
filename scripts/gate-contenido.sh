#!/usr/bin/env bash
# =============================================================================
# gate-contenido.sh — gate determinista de un repo de CONTENIDO (El Nieto Digital).
#
# Comprueba lo que un script puede comprobar de verdad; lo demás (apellidos, tono, condescendencia) es
# juicio humano y se dice en el PR template, no aquí. Cuatro sujetos:
#   1. Privacidad: teléfonos españoles, emails y DNI/NIE en ficheros VERSIONADOS (git ls-files).
#   2. Guiones publicados (guiones/publicados/*.md): frontmatter con los campos obligatorios.
#   3. Responsabilidad: `responsabilidad:` declarada; si no es `ninguno`, la sección
#      «## Mensaje de responsabilidad» tiene contenido.
#   4. ROADMAP.md / CHANGELOG.md con el contrato que renderiza el Dashboard.
#
# Exit codes (doctrina_gates_honestos): 0 verde · 1 rojo · 2 error de uso · 3 no aplica (no hay repo git)
# · 4 no pude decidir (falta git/grep). Nunca 0 por defecto.
#
# Uso: gate-contenido.sh [--root DIR] [--self-test]
# =============================================================================
set -u

ROOT="."
SELF_TEST=0
while [ $# -gt 0 ]; do
  case "$1" in
    --root) [ -n "${2:-}" ] || { echo "uso: --root DIR" >&2; exit 2; }; ROOT="$2"; shift 2 ;;
    --self-test) SELF_TEST=1; shift ;;
    -h|--help) sed -n 2,17p "$0"; exit 0 ;;
    *) echo "flag desconocido: $1" >&2; exit 2 ;;
  esac
done

command -v git >/dev/null 2>&1 || { echo "gate-contenido: falta git → no puedo decidir" >&2; exit 4; }
command -v grep >/dev/null 2>&1 || { echo "gate-contenido: falta grep → no puedo decidir" >&2; exit 4; }

# Patrones de privacidad. Teléfono: 9 dígitos que empiezan por 6/7/8/9, con o sin +34 y separadores.
# DNI: 8 dígitos + letra; NIE: X/Y/Z + 7 dígitos + letra. Email: lo obvio.
RE_TEL='(\+34|0034)?[[:space:].-]?[6-9][0-9]{2}[[:space:].-]?[0-9]{3}[[:space:].-]?[0-9]{3}([^0-9]|$)'
RE_DNI='(^|[^A-Za-z0-9])([0-9]{8}[A-Za-z]|[XYZxyz][0-9]{7}[A-Za-z])([^A-Za-z0-9]|$)'
RE_MAIL='[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'
# Ficheros que por naturaleza llevan dominios o correos de ejemplo legítimos se declaran aquí, no se
# apagan con un flag: el propio gate lista las excepciones.
PRIV_EXCLUDE='^(scripts/gate-contenido\.sh|docs/diagrams/.*)$'

gate() {
  local root="$1" rojo=0 f
  cd "$root" || { echo "gate-contenido: no existe $root" >&2; return 2; }
  git rev-parse --show-toplevel >/dev/null 2>&1 || { echo "gate-contenido: $root no es un repo git → no aplica" >&2; return 3; }

  # --- 1. privacidad --------------------------------------------------------------------------------
  local tracked
  tracked="$( { git ls-files; git ls-files --others --exclude-standard; } | sort -u | grep -Ev "$PRIV_EXCLUDE" | grep -Ev '\.(png|jpg|jpeg|gif|webp|svg|ico)$' || true)"
  while IFS= read -r f; do
    [ -n "$f" ] && [ -f "$f" ] || continue
    if grep -nE "$RE_TEL" "$f" | grep -vE 'https?://|[0-9]{10,}' | head -n 3 | sed "s|^|  ✗ $f: teléfono → |" | grep .; then rojo=1; fi
    if grep -nE "$RE_DNI" "$f" | head -n 3 | sed "s|^|  ✗ $f: DNI/NIE → |" | grep .; then rojo=1; fi
    if grep -nE "$RE_MAIL" "$f" | head -n 3 | sed "s|^|  ✗ $f: email → |" | grep .; then rojo=1; fi
  done <<< "$tracked"

  # --- 2 y 3. guiones publicados -------------------------------------------------------------------
  local req campo fm resp
  for f in guiones/publicados/*.md; do
    [ -f "$f" ] || continue
    fm="$(awk 'NR==1 && $0!="---"{exit} NR>1 && $0=="---"{exit} NR>1{print}' "$f")"
    [ -n "$fm" ] || { echo "  ✗ $f: sin frontmatter"; rojo=1; continue; }
    if grep -q '^duracion_objetivo:' <<< "$fm"; then req="titulo pilar plataformas issue fecha_publicacion estado responsabilidad"
    else req="gancho pilar plataformas issue fecha responsabilidad"; fi
    for campo in $req; do
      grep -Eq "^${campo}:[[:space:]]*[^[:space:]]" <<< "$fm" || { echo "  ✗ $f: falta \`$campo:\` en el frontmatter"; rojo=1; }
    done
    resp="$(grep -E '^responsabilidad:' <<< "$fm" | sed -E 's/^responsabilidad:[[:space:]]*//; s/[[:space:]]+$//')"
    case "$resp" in
      ""|ninguno|salud|dinero|ia|"["*"]") ;;
      *) echo "  ✗ $f: \`responsabilidad:\` debe ser ninguno | salud | dinero | ia (o lista), no \`$resp\`"; rojo=1 ;;
    esac
    if [ -n "$resp" ] && [ "$resp" != "ninguno" ]; then
      awk '/^## Mensaje de responsabilidad/{s=1; next} s && /^## /{exit} s{print}' "$f" \
        | grep -Eq '[[:alnum:]]' || { echo "  ✗ $f: responsabilidad=$resp pero «## Mensaje de responsabilidad» está vacía"; rojo=1; }
    fi
  done

  # --- 4. roadmap / changelog ------------------------------------------------------------------------
  if [ -f ROADMAP.md ]; then
    grep -Eq '^## ' ROADMAP.md && grep -Eq '^[[:space:]]*- \[[ xX]\] ' ROADMAP.md \
      || { echo "  ✗ ROADMAP.md: necesita al menos un hito \`## \` con checkboxes \`- [ ]\`"; rojo=1; }
  else echo "  ✗ falta ROADMAP.md"; rojo=1; fi
  if [ -f CHANGELOG.md ]; then
    grep -E '^## ' CHANGELOG.md | head -n 1 | grep -Eq '[0-9]{4}-[0-9]{2}-[0-9]{2}' \
      || { echo "  ✗ CHANGELOG.md: la primera entrada \`## \` debe llevar fecha ISO (AAAA-MM-DD)"; rojo=1; }
  else echo "  ✗ falta CHANGELOG.md"; rojo=1; fi

  return "$rojo"
}

self_test() {
  local tmp rc fallos=0
  tmp="$(mktemp -d)"
  espera() { # espera <rc esperado> <nombre> <rc obtenido>
    if [ "$3" -eq "$1" ]; then echo "  ✓ $2 → $3"; else echo "  ✗ $2 → $3 (esperado $1)"; fallos=1; fi
  }
  # Repo limpio mínimo → 0
  local ok="$tmp/ok"; mkdir -p "$ok/guiones/publicados"; git -C "$ok" init -q
  printf '# R\n\n## Hito\n- [ ] x\n' > "$ok/ROADMAP.md"; printf '# C\n\n## 2026-01-01 — a\n- b\n' > "$ok/CHANGELOG.md"
  printf -- '---\ngancho: "Hola"\npilar: seguridad\nplataformas: [reels]\nissue: 3\nfecha: 2026-01-01\nresponsabilidad: dinero\n---\n\n## Mensaje de responsabilidad\n> Esto no es consejo financiero.\n' > "$ok/guiones/publicados/2026-01-01-a.md"
  ( gate "$ok" ) >/dev/null 2>&1; espera 0 "repo limpio" $?
  # Teléfono → 1
  local t1="$tmp/tel"; cp -r "$ok" "$t1"; printf 'Llama al 612 345 678\n' > "$t1/nota.md"
  ( gate "$t1" ) >/dev/null 2>&1; espera 1 "teléfono versionable" $?
  # Email → 1
  local t2="$tmp/mail"; cp -r "$ok" "$t2"; printf 'escribe a alguien@ejemplo.es\n' > "$t2/nota.md"
  ( gate "$t2" ) >/dev/null 2>&1; espera 1 "email" $?
  # DNI → 1
  local t3="$tmp/dni"; cp -r "$ok" "$t3"; printf 'DNI 12345678Z\n' > "$t3/nota.md"
  ( gate "$t3" ) >/dev/null 2>&1; espera 1 "DNI" $?
  # Guion sin responsabilidad → 1
  local t4="$tmp/fm"; cp -r "$ok" "$t4"; sed -i '/^responsabilidad:/d' "$t4/guiones/publicados/2026-01-01-a.md"
  ( gate "$t4" ) >/dev/null 2>&1; espera 1 "frontmatter incompleto" $?
  # responsabilidad=salud con sección vacía → 1
  local t5="$tmp/resp"; cp -r "$ok" "$t5"; sed -i 's/^> Esto no es.*$//' "$t5/guiones/publicados/2026-01-01-a.md"
  ( gate "$t5" ) >/dev/null 2>&1; espera 1 "responsabilidad sin mensaje" $?
  # Sin CHANGELOG → 1
  local t6="$tmp/cl"; cp -r "$ok" "$t6"; rm "$t6/CHANGELOG.md"
  ( gate "$t6" ) >/dev/null 2>&1; espera 1 "sin CHANGELOG" $?
  # No es repo git → 3
  local t7="$tmp/nogit"; mkdir -p "$t7"
  ( gate "$t7" ) >/dev/null 2>&1; espera 3 "sin repo git" $?
  rm -rf "$tmp"
  return "$fallos"
}

if [ "$SELF_TEST" -eq 1 ]; then
  echo "gate-contenido --self-test"
  if self_test; then echo "self-test: verde"; exit 0; else echo "self-test: ROJO (el gate no sabe ponerse rojo donde debe)"; exit 1; fi
fi

echo "gate-contenido sobre $ROOT"
gate "$ROOT"; rc=$?
case "$rc" in
  0) echo "verde: privacidad, guiones, roadmap y changelog en orden" ;;
  1) echo "ROJO: corrige lo marcado con ✗" ;;
esac
exit "$rc"
