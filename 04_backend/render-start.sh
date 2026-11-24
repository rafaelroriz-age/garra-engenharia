#!/bin/sh
# Inicialização da imagem de produção (Dockerfile.render) — T110 / DEC-59.
#
# O disco persistente do Render é montado em tempo de execução com dono root, então o
# usuário sem privilégios `appuser` não consegue gravar nele (verificado com volume Docker:
# GET /health -> "storage": "unavailable"). Este script roda como root só para criar o
# diretório do storage local e passá-lo para `appuser`; em seguida troca de usuário com
# `setpriv` (util-linux, já presente na python:3.12-slim) e executa o uvicorn.
set -eu

if [ "$(id -u)" = "0" ]; then
    if [ "${STORAGE_PROVEDOR:-s3}" = "local" ] && [ -n "${STORAGE_LOCAL_DIR:-}" ]; then
        mkdir -p "$STORAGE_LOCAL_DIR"
        chown appuser:appuser "$STORAGE_LOCAL_DIR"
    fi
    exec env HOME=/home/appuser setpriv --reuid=appuser --regid=appuser --init-groups \
        uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
fi

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
