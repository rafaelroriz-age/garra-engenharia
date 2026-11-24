#!/usr/bin/env bash
# Smoke-test pós-deploy (T112, DEC-59). Só curl; sem segredos no arquivo.
#
# Uso:
#   API_URL=https://garra-backend.onrender.com ADMIN_EMAIL=... ADMIN_SENHA=... \
#   [FRONT_ORIGIN=https://rafaelroriz-age.github.io] bash 05_infra/smoke/smoke.sh
#
# API_URL é a raiz do backend (sem /api/v1). Sai com código != 0 se qualquer
# verificação falhar.
set -u

API_URL="${API_URL:-}"
ADMIN_EMAIL="${ADMIN_EMAIL:-}"
ADMIN_SENHA="${ADMIN_SENHA:-}"
FRONT_ORIGIN="${FRONT_ORIGIN:-https://rafaelroriz-age.github.io}"

for v in API_URL ADMIN_EMAIL ADMIN_SENHA; do
  if [ -z "${!v}" ]; then
    echo "ERRO: defina a variável $v" >&2
    exit 2
  fi
done
API_URL="${API_URL%/}"

falhas=0
ok()   { echo "OK    $1"; }
fail() { echo "FALHA $1" >&2; falhas=$((falhas + 1)); }

# Primeira requisição pode demorar (cold start do Render).
CURL=(curl -sS --max-time 90)

# 1. /health (sem auth)
code=$("${CURL[@]}" -o /dev/null -w '%{http_code}' "$API_URL/health") || code=000
if [ "$code" = "200" ]; then ok "GET /health -> 200"; else fail "GET /health -> $code (esperado 200)"; fi

# 2. login (JSON {email, senha}; resposta com access_token)
corpo=$(printf '{"email":"%s","senha":"%s"}' "$ADMIN_EMAIL" "$ADMIN_SENHA")
resp=$("${CURL[@]}" -w '\n%{http_code}' -H 'Content-Type: application/json' -d "$corpo" "$API_URL/api/v1/auth/login") || resp=$'\n000'
code="${resp##*$'\n'}"
json="${resp%$'\n'*}"
token=$(printf '%s' "$json" | sed -n 's/.*"access_token" *: *"\([^"]*\)".*/\1/p')
if [ "$code" = "200" ] && [ -n "$token" ]; then
  ok "POST /api/v1/auth/login -> 200 (token recebido)"
else
  fail "POST /api/v1/auth/login -> $code (sem token)"
  token=""
fi

# 3. listagem autenticada
if [ -n "$token" ]; then
  code=$("${CURL[@]}" -o /dev/null -w '%{http_code}' -H "Authorization: Bearer $token" "$API_URL/api/v1/edificacoes") || code=000
  if [ "$code" = "200" ]; then ok "GET /api/v1/edificacoes -> 200"; else fail "GET /api/v1/edificacoes -> $code (esperado 200)"; fi
else
  fail "GET /api/v1/edificacoes pulado (sem token)"
fi

# 4. CORS preflight a partir do front
cab=$("${CURL[@]}" -o /dev/null -D - -X OPTIONS \
  -H "Origin: $FRONT_ORIGIN" \
  -H 'Access-Control-Request-Method: POST' \
  -H 'Access-Control-Request-Headers: authorization,content-type' \
  "$API_URL/api/v1/auth/login") || cab=""
cab=$(printf '%s' "$cab" | tr -d '\r')
code=$(printf '%s\n' "$cab" | head -n1 | awk '{print $2}')
permitido=$(printf '%s\n' "$cab" | grep -i '^access-control-allow-origin:' | head -n1 | cut -d' ' -f2-)
if { [ "$code" = "200" ] || [ "$code" = "204" ]; } && { [ "$permitido" = "$FRONT_ORIGIN" ] || [ "$permitido" = "*" ]; }; then
  ok "OPTIONS login (Origin $FRONT_ORIGIN) -> $code, allow-origin=$permitido"
else
  fail "CORS preflight -> status=${code:-?} allow-origin='${permitido:-}' (esperado $FRONT_ORIGIN)"
fi

echo
if [ "$falhas" -gt 0 ]; then
  echo "$falhas verificação(ões) falharam." >&2
  exit 1
fi
echo "Todas as verificações passaram."
