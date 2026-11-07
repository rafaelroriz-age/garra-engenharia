#!/usr/bin/env bash
# =============================================================================
# 05_infra/backup/tests/test_backup_scripts.sh — BL-29 (RNF-08)
#
# Teste dos scripts de backup/restore SEM banco, MinIO ou docker reais.
#
# Como funciona: cada cenário monta uma árvore descartável (mktemp -d) com
# cópias dos scripts em <tmp>/infra/backup/ — assim dumps/ e objetos/ nascem
# dentro do diretório temporário — e coloca stubs de `docker` (único comando
# externo chamado pelos scripts) e de pg_dump/pg_restore/psql/mc/aws/rclone no
# início do PATH. Chamar qualquer um dos stubs "diretos" é registrado como erro.
# Nunca toca em 05_infra/backup/dumps, em .env nem em dados reais.
#
# Uso:  bash 05_infra/backup/tests/test_backup_scripts.sh
# Saída: 0 se tudo passou, 1 se alguma verificação falhou.
# =============================================================================
set -u

AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ORIGEM="$(dirname "$AQUI")"
SCRIPT_BACKUP="$ORIGEM/backup-db.sh"
SCRIPT_RESTORE="$ORIGEM/restore-db.sh"

PASS=0
FAIL=0
TMPS=()

ok()   { PASS=$((PASS + 1)); echo "  ok    - $1"; }
nok()  { FAIL=$((FAIL + 1)); echo "  FALHA - $1"; }
check() { local d="$1"; shift; if "$@"; then ok "$d"; else nok "$d"; fi; }
nao_zero() { [[ "$1" -ne 0 ]]; }

cleanup() {
  local d
  for d in "${TMPS[@]:-}"; do
    [[ -n "$d" && -d "$d" ]] && rm -rf "$d"
  done
}
trap cleanup EXIT

# Monta um ambiente isolado; exporta T, INFRA, DUMPS, BIN, STUB_LOG e PATH.
novo_ambiente() {
  T="$(mktemp -d)"
  TMPS+=("$T")
  INFRA="$T/infra"
  BIN="$T/bin"
  DUMPS="$INFRA/backup/dumps"
  STUB_LOG="$T/chamadas.log"
  mkdir -p "$INFRA/backup" "$BIN" "$DUMPS"
  : > "$STUB_LOG"
  cp "$SCRIPT_BACKUP" "$SCRIPT_RESTORE" "$INFRA/backup/"

  cat > "$BIN/docker" <<'STUB'
#!/usr/bin/env bash
echo "docker $*" >> "$STUB_LOG"
case "$*" in
  *" exec "*pg_dump*)
    case "${STUB_DUMP:-ok}" in
      fail)  echo "pg_dump: erro simulado" >&2; exit 1 ;;
      vazio) exit 0 ;;
      *)
        [[ -n "${STUB_OLD_PROBE:-}" && -e "$STUB_OLD_PROBE" ]] && echo "ANTIGO_PRESENTE_NO_DUMP" >> "$STUB_LOG"
        echo "PGDMP-FALSO"
        ;;
    esac
    ;;
  *" exec "*pg_restore*) echo "STDIN_RESTORE=$(cat)" >> "$STUB_LOG" ;;
  *" ps "*) echo postgres; [[ "${STUB_MINIO:-0}" == 1 ]] && echo minio ;;
esac
exit 0
STUB
  chmod +x "$BIN/docker"

  local c
  for c in pg_dump pg_restore psql mc aws rclone; do
    printf '#!/usr/bin/env bash\necho "DIRETO %s $*" >> "$STUB_LOG"\nexit 0\n' "$c" > "$BIN/$c"
    chmod +x "$BIN/$c"
  done

  export STUB_LOG
  export PATH="$BIN:$ORIGINAL_PATH"
  export POSTGRES_USER=usuario_teste POSTGRES_DB=banco_teste
  export COMPOSE_FILE=compose-fake.yml
  export MINIO_ROOT_USER=minio_teste MINIO_ROOT_PASSWORD=senha_teste
  export RETENCAO_DIAS=30
  unset STUB_DUMP STUB_MINIO STUB_OLD_PROBE

  # Trava de segurança: se o docker resolvido não for o stub, aborta tudo.
  if [[ "$(command -v docker)" != "$BIN/docker" ]]; then
    echo "ABORTADO: 'docker' não resolve para o stub ($(command -v docker))." >&2
    exit 2
  fi
}

ORIGINAL_PATH="$PATH"

cria_antigos() {
  OLD="$DUMPS/garra-db-19990101-000000.dump"
  RECENTE="$DUMPS/garra-db-19990102-000000.dump"
  echo "velho" > "$OLD";     touch -d '60 days ago' "$OLD"
  echo "recente" > "$RECENTE"; touch -d '1 day ago' "$RECENTE"
  export STUB_OLD_PROBE="$OLD"
}

roda_backup() { # args opcionais ignorados; resultado em RC, OUT, ERR
  ( cd "$T" && bash "$INFRA/backup/backup-db.sh" ) > "$T/out.txt" 2> "$T/err.txt"
  RC=$?
}

roda_restore() { # $1 = arquivo de dump, stdin = resposta
  ( cd "$T" && bash "$INFRA/backup/restore-db.sh" "$@" ) > "$T/out.txt" 2> "$T/err.txt"
  RC=$?
}

sem_chamadas_diretas() { ! grep -q '^DIRETO ' "$STUB_LOG"; }
sem_docker() { ! grep -q '^docker ' "$STUB_LOG"; }
tem_log() { grep -q -- "$1" "$STUB_LOG"; }
nao_tem_log() { ! grep -q -- "$1" "$STUB_LOG"; }
dumps_novos() { compgen -G "$DUMPS/garra-db-20*.dump" > /dev/null; }
nenhum_dump_novo() { ! dumps_novos; }
dump_novo_nao_vazio() { local f; for f in "$DUMPS"/garra-db-20*.dump; do [[ -s "$f" ]] && return 0; done; return 1; }
linha() { grep -n -- "$1" "$STUB_LOG" | head -1 | cut -d: -f1; }

# ---------------------------------------------------------------------------
echo "== (a) backup feliz: cria dump e aplica retenção só depois"
novo_ambiente; cria_antigos
roda_backup
check "sai com código 0" test "$RC" -eq 0
check "dump novo criado e não vazio" dump_novo_nao_vazio
check "dump foi gerado ANTES da retenção (arquivo antigo ainda existia durante o pg_dump)" tem_log "ANTIGO_PRESENTE_NO_DUMP"
check "backup antigo (60 dias) removido pela retenção" test ! -e "$OLD"
check "backup recente (1 dia) preservado" test -e "$RECENTE"
check "sem minio no compose: espelho pulado (nenhum 'docker run')" nao_tem_log "docker run"
check "nenhum comando externo chamado diretamente (só via docker)" sem_chamadas_diretas

echo "== (a2) backup feliz com serviço minio presente: espelho é acionado"
novo_ambiente; cria_antigos; export STUB_MINIO=1
roda_backup
check "sai com código 0" test "$RC" -eq 0
check "'docker run' do mc mirror executado" tem_log "mirror --overwrite --remove origem/relatorios-prediais"
check "retenção aplicada (antigo removido)" test ! -e "$OLD"

# ---------------------------------------------------------------------------
echo "== (b1) pg_dump falha: sai ≠ 0 e NÃO apaga backups antigos"
novo_ambiente; cria_antigos; export STUB_DUMP=fail
roda_backup
check "sai com código ≠ 0" nao_zero "$RC"
check "backup antigo (60 dias) NÃO foi apagado" test -e "$OLD"
check "backup recente preservado" test -e "$RECENTE"
check "não deixa dump parcial/vazio com nome garra-db-<carimbo>.dump" nenhum_dump_novo

echo "== (b2) pg_dump produz arquivo vazio: sai ≠ 0 e NÃO apaga backups antigos"
novo_ambiente; cria_antigos; export STUB_DUMP=vazio
roda_backup
check "sai com código ≠ 0" nao_zero "$RC"
check "mensagem de erro de dump vazio em stderr" grep -q "dump vazio" "$T/err.txt"
check "backup antigo (60 dias) NÃO foi apagado" test -e "$OLD"
check "backup recente preservado" test -e "$RECENTE"
check "não deixa dump vazio" nenhum_dump_novo
check "espelho do MinIO não foi executado" nao_tem_log "docker run"

echo "== (b3) POSTGRES_USER ausente: aborta sem apagar nada"
novo_ambiente; cria_antigos; unset POSTGRES_USER
roda_backup
check "sai com código ≠ 0" nao_zero "$RC"
check "backup antigo preservado" test -e "$OLD"
check "nenhuma chamada ao docker" sem_docker

# ---------------------------------------------------------------------------
ENTRADA_CONTEUDO="PGDMP-ENTRADA"
prepara_restore() { novo_ambiente; echo "$ENTRADA_CONTEUDO" > "$T/entrada.dump"; }
tem_pre_restore() { compgen -G "$DUMPS/pre-restore-*.dump" > /dev/null; }
sem_pre_restore() { ! tem_pre_restore; }

echo "== (c1) restore com confirmação errada: aborta sem pg_restore/psql"
prepara_restore
roda_restore "$T/entrada.dump" <<< "nao"
check "sai com código ≠ 0" nao_zero "$RC"
check "imprime 'Cancelado.'" grep -q "Cancelado." "$T/out.txt"
check "nenhuma chamada ao docker (nem pg_restore, nem pre-restore, nem stop)" sem_docker
check "nenhum pre-restore criado" sem_pre_restore
check "nenhum pg_restore/psql direto" sem_chamadas_diretas

echo "== (c2) restore com 'restaurar' em minúsculas: aborta (confirmação exata)"
prepara_restore
roda_restore "$T/entrada.dump" <<< "restaurar"
check "sai com código ≠ 0" nao_zero "$RC"
check "nenhuma chamada ao docker" sem_docker

echo "== (c3) restore com stdin vazio (EOF): aborta"
prepara_restore
roda_restore "$T/entrada.dump" < /dev/null
check "sai com código ≠ 0" nao_zero "$RC"
check "nenhuma chamada ao docker" sem_docker

echo "== (c4) restore sem argumento / arquivo inexistente: aborta"
prepara_restore
roda_restore < /dev/null
check "sem argumento: sai ≠ 0" nao_zero "$RC"
check "sem argumento: nenhuma chamada ao docker" sem_docker
roda_restore "$T/nao-existe.dump" < /dev/null
check "arquivo inexistente: sai ≠ 0" nao_zero "$RC"
check "arquivo inexistente: nenhuma chamada ao docker" sem_docker

# ---------------------------------------------------------------------------
echo "== (d) restore com confirmação RESTAURAR: dump pre-restore vem primeiro"
prepara_restore
roda_restore "$T/entrada.dump" <<< "RESTAURAR"
check "sai com código 0" test "$RC" -eq 0
check "arquivo pre-restore-*.dump criado" tem_pre_restore
L_DUMP="$(linha 'exec -T postgres pg_dump')"
L_STOP="$(linha 'docker .* stop ')"
L_REST="$(linha 'exec -T postgres pg_restore')"
check "pg_dump (pre-restore) executado" test -n "$L_DUMP"
check "pg_restore executado" test -n "$L_REST"
check "ordem: pg_dump(pre-restore) < pg_restore" test "${L_DUMP:-999}" -lt "${L_REST:-0}"
check "ordem: stop de backend/frontend antes do pg_restore" test "${L_STOP:-999}" -lt "${L_REST:-0}"
check "pg_restore recebeu o conteúdo do dump informado via stdin" tem_log "STDIN_RESTORE=$ENTRADA_CONTEUDO"
check "pg_restore usa --clean --if-exists" tem_log "pg_restore -U usuario_teste -d banco_teste --clean --if-exists"
check "nenhum comando externo direto" sem_chamadas_diretas

# ---------------------------------------------------------------------------
echo "== (INFO) caracterização: pre-restore falha (não conta como falha de teste)"
prepara_restore; export STUB_DUMP=fail
roda_restore "$T/entrada.dump" <<< "RESTAURAR"
if tem_log "exec -T postgres pg_restore"; then
  echo "  info  - pre-restore falhou (pg_dump rc=1) e o script AINDA ASSIM chamou pg_restore (rc final=$RC)."
  echo "          Causa: '|| true' na linha do pg_dump pre-restore. Ver proposta em backup-verificacao.md."
else
  echo "  info  - pre-restore falhou e o script abortou antes do pg_restore (rc final=$RC)."
fi

# ---------------------------------------------------------------------------
echo
echo "Resumo: $PASS ok, $FAIL falha(s)"
[[ "$FAIL" -eq 0 ]]
