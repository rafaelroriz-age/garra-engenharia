#!/usr/bin/env bash
# =============================================================================
# 05_infra/backup/backup-db.sh — BL-29 (RNF-08, plano-gestao-configuracao.md §6)
#
# Faz dump lógico do PostgreSQL e espelha o bucket do MinIO, aplicando a
# política de retenção. Projetado para rodar tanto manualmente quanto por cron.
#
# Uso:
#   cd 05_infra && ./backup/backup-db.sh              # usa docker-compose.prod.yml
#   COMPOSE_FILE=docker-compose.yml ./backup/backup-db.sh   # ambiente de dev
#
# Agendamento sugerido (crontab do host, diário às 02:00):
#   0 2 * * * cd /home/deploy/garra-engenharia/05_infra && ./backup/backup-db.sh >> backup/backup.log 2>&1
#
# Variáveis (lidas de 05_infra/.env, nunca hardcoded):
#   POSTGRES_USER, POSTGRES_DB, MINIO_ROOT_USER, MINIO_ROOT_PASSWORD, MINIO_BUCKET_NAME
#   RETENCAO_DIAS  (default 30)
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(dirname "$SCRIPT_DIR")"
cd "$INFRA_DIR"

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
RETENCAO_DIAS="${RETENCAO_DIAS:-30}"
DUMP_DIR="$SCRIPT_DIR/dumps"
OBJETOS_DIR="$SCRIPT_DIR/objetos"
CARIMBO="$(date +%Y%m%d-%H%M%S)"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

POSTGRES_USER="${POSTGRES_USER:?POSTGRES_USER não definido (05_infra/.env)}"
POSTGRES_DB="${POSTGRES_DB:-garra_engenharia}"
MINIO_BUCKET_NAME="${MINIO_BUCKET_NAME:-relatorios-prediais}"

mkdir -p "$DUMP_DIR" "$OBJETOS_DIR"

echo "[backup] Iniciando backup ($CARIMBO) com $COMPOSE_FILE"

# ---------------------------------------------------------------------------
# 1) Dump lógico do PostgreSQL (formato custom: permite restore seletivo)
# ---------------------------------------------------------------------------
ARQUIVO_DUMP="$DUMP_DIR/garra-db-$CARIMBO.dump"
docker compose -f "$COMPOSE_FILE" exec -T postgres \
  pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom --no-owner \
  > "$ARQUIVO_DUMP"

if [[ ! -s "$ARQUIVO_DUMP" ]]; then
  echo "[backup] ERRO: dump vazio — abortando sem aplicar retenção." >&2
  rm -f "$ARQUIVO_DUMP"
  exit 1
fi
echo "[backup] Dump do banco: $ARQUIVO_DUMP ($(du -h "$ARQUIVO_DUMP" | cut -f1))"

# ---------------------------------------------------------------------------
# 2) Espelho do bucket MinIO (fotos + PDF/DOCX gerados)
# ---------------------------------------------------------------------------
if docker compose -f "$COMPOSE_FILE" ps --services 2>/dev/null | grep -qx "minio"; then
  docker run --rm --network garra-net \
    -v "$OBJETOS_DIR:/espelho" \
    -e MC_HOST_origem="http://${MINIO_ROOT_USER}:${MINIO_ROOT_PASSWORD}@minio:9000" \
    minio/mc:latest mirror --overwrite --remove "origem/${MINIO_BUCKET_NAME}" "/espelho/${MINIO_BUCKET_NAME}"
  echo "[backup] Bucket '${MINIO_BUCKET_NAME}' espelhado em $OBJETOS_DIR"
else
  echo "[backup] AVISO: serviço 'minio' não encontrado em $COMPOSE_FILE — pulando espelho de objetos."
fi

# ---------------------------------------------------------------------------
# 3) Retenção — só executa depois de um dump válido, para nunca apagar o
#    último backup bom por causa de uma execução que falhou.
# ---------------------------------------------------------------------------
find "$DUMP_DIR" -name 'garra-db-*.dump' -type f -mtime "+$RETENCAO_DIAS" -print -delete

echo "[backup] Concluído. Retenção: $RETENCAO_DIAS dias."
echo "[backup] LEMBRETE: copie $DUMP_DIR e $OBJETOS_DIR para fora do host (RNF-08)."
