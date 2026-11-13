# Unicidade de `fotos.storage_key` (R-15)

## O que mudou
- Migration `04_backend/alembic/versions/e5a1c7d9b3f4_fotos_storage_key_unico_r15.py` (down_revision `d3b7c9e4f1a2`; `alembic heads` → único head `e5a1c7d9b3f4`).
  - `upgrade()`: consulta duplicatas de `storage_key`; se houver, `RuntimeError` listando as chaves (nada é apagado/alterado); senão cria `UNIQUE uq_fotos_storage_key`.
  - `storage_key` é `NOT NULL` → restrição UNIQUE comum, sem índice parcial.
  - `downgrade()` remove a restrição.
- Modelo `Foto`: `UniqueConstraint("storage_key", name="uq_fotos_storage_key")`.
- `foto_repository.create`: captura `IntegrityError` dessa restrição → `ConflictError` (409, problem+json, `storage-key-ja-vinculada`). Nesta branch o 409 da T19 não existia (não integrada), por isso foi incluído aqui; ao integrar a T19, conferir duplicidade de lógica.
- Teste novo: `04_backend/tests/test_fotos_storage_key_unico.py` (409 no endpoint; `IntegrityError` direto).

## Verificação
- `alembic heads`: `e5a1c7d9b3f4 (head)` — OK.
- `ruff check .`: 219 erros já existentes no repositório (baseline); os arquivos novos seguem o estilo das migrations existentes (avisos UP007/F821 equivalentes aos já presentes).
- **NÃO RODOU**: `alembic check`, ciclo upgrade→downgrade→upgrade em banco temporário, `pytest tests/test_fotos_storage_key_unico.py tests/test_fotos*.py`. Motivo: PostgreSQL em localhost:5433 fora do ar (conexão recusada) e `docker` indisponível neste ambiente. Os testes precisam também de MinIO.

## Para rodar depois
```
cd 05_infra && docker compose up -d
cd ../04_backend
# banco descartável: CREATE DATABASE garra_tmp_r15; apontar DATABASE_URL para ele
alembic upgrade head && alembic downgrade -1 && alembic upgrade head && alembic check
pytest tests/test_fotos_storage_key_unico.py tests/test_fotos*.py
```

## Para o fechamento de lote
- `riscos.md`: R-15 pode ser marcado mitigado após a validação acima.
- Em bancos com duplicatas, o upgrade aborta; resolver manualmente.
