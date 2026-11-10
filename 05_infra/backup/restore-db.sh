#!/usr/bin/env bash
# =============================================================================
# 05_infra/backup/restore-db.sh — BL-29 (RNF-08, plano-gestao-configuracao.md §6)
#
# Restaura um dump gerado por backup-db.sh. Operação DESTRUTIVA: recria o
# schema do banco alvo. Exige confirmação explícita.
#
# Uso:
#   cd 05_infra && ./backup/restore-db.sh backup/dumps/garra-db-20260807-020000.dump
#   COMPOSE_FILE=docker-compose.yml ./backup/restore-db.sh <arquivo.dump>
#
# Teste periódico de restauração (recomendado, §6 do plano): restaurar o dump
# mais recente em um banco descartável e conferir a contagem de tabelas.
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(dirname "$SCRIPT_DIR")"
cd "$INFRA_DIR"

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
ARQUIVO_DUMP="${1:-}"

if [[ -z "$ARQUIVO_DUMP" ]]; then
  echo "Uso: $0 <caminho/do/arquivo.dump>" >&2
  echo "Dumps disponíveis:" >&2
  ls -1t "$SCRIPT_DIR/dumps"/*.dump 2>/dev/null >&2 || echo "  (nenhum)" >&2
  exit 1
fi

if [[ ! -f "$ARQUIVO_DUMP" ]]; then
  echo "ERRO: arquivo '$ARQUIVO_DUMP' não encontrado." >&2
  exit 1
fi

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

POSTGRES_USER="${POSTGRES_USER:?POSTGRES_USER não definido (05_infra/.env)}"
POSTGRES_DB="${POSTGRES_DB:-garra_engenharia}"

echo "ATENÇÃO: isto vai SOBRESCREVER o banco '$POSTGRES_DB' com '$ARQUIVO_DUMP'."
read -r -p "Digite RESTAURAR para confirmar: " confirmacao
if [[ "$confirmacao" != "RESTAURAR" ]]; then
  echo "Cancelado."
  exit 1
fi

# Backup de segurança do estado atual antes de sobrescrever (DEC-45).
# Sem um pre-restore válido o restore NÃO prossegue: é a única rede de segurança.
# FORCAR_SEM_PRE_RESTORE=1 é o override explícito (ex.: banco vazio recém-criado).
PRE_RESTORE="$SCRIPT_DIR/dumps/pre-restore-$(date +%Y%m%d-%H%M%S).dump"
mkdir -p "$SCRIPT_DIR/dumps"
if [[ "${FORCAR_SEM_PRE_RESTORE:-0}" == "1" ]]; then
  echo "[restore] AVISO: FORCAR_SEM_PRE_RESTORE=1 — pulando o dump pre-restore. NÃO há cópia do estado anterior." >&2
else
  if ! docker compose -f "$COMPOSE_FILE" exec -T postgres \
    pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom --no-owner > "$PRE_RESTORE"; then
    rm -f "$PRE_RESTORE"
    echo "[restore] ERRO: pg_dump pre-restore falhou — restore ABORTADO, nada foi alterado no banco." >&2
    echo "[restore] Para restaurar mesmo assim, sem cópia do estado atual: FORCAR_SEM_PRE_RESTORE=1 $0 <dump>" >&2
    exit 1
  fi
  if [[ ! -s "$PRE_RESTORE" ]]; then
    rm -f "$PRE_RESTORE"
    echo "[restore] ERRO: dump pre-restore vazio — restore ABORTADO, nada foi alterado no banco." >&2
    echo "[restore] Para restaurar mesmo assim, sem cópia do estado atual: FORCAR_SEM_PRE_RESTORE=1 $0 <dump>" >&2
    exit 1
  fi
  echo "[restore] Estado anterior salvo em $PRE_RESTORE"
fi

# Derruba a aplicação para não haver escrita concorrente durante o restore.
docker compose -f "$COMPOSE_FILE" stop backend frontend >/dev/null 2>&1 || true

docker compose -f "$COMPOSE_FILE" exec -T postgres \
  pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists --no-owner \
  < "$ARQUIVO_DUMP"

docker compose -f "$COMPOSE_FILE" start backend frontend >/dev/null 2>&1 || true

echo "[restore] Concluído. Valide com: docker compose -f $COMPOSE_FILE exec backend alembic current"
