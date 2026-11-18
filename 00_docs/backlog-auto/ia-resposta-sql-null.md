# T105 — `registrar()` grava SQL NULL em `chamadas_ia.resposta` (DEC-59 P1)

Papel: backend. Branch `worktree-backlog-T105`. Sem push.

## O que foi feito

- **`04_backend/app/models/chamada_ia.py`**: a coluna passou de `JSONB` para `JSONB(none_as_null=True)`. Com isso o SQLAlchemy grava `None` como **SQL NULL** em qualquer caminho de escrita, inclusive `registrar()` (falhas, `origem="cache_local"` e sucesso sem resultado). Antes gravava JSON `null`.
  - **Sem migration:** só muda o tipo Python. Não há DDL, e a coluna continua `JSONB NULL`.
  - `registrar()` não precisou mudar: ele já passa `resposta=None` nesses casos.
- **Proteção do cache mantida:** `tem_resposta()` (`coalesce(jsonb_typeof(resposta),'null') <> 'null'`) e a checagem `linha.resposta is None` em `buscar_em_cache` ficam como estavam. Linhas antigas com JSON `null` seguem sendo miss.
- **Testes novos** em `04_backend/tests/test_chamadas_ia_resposta_null.py` (4):
  - falha sem resposta grava `resposta IS NULL` e `jsonb_typeof` nulo;
  - `origem="cache_local"` também grava SQL NULL;
  - sucesso da API grava objeto JSON e o cache acerta;
  - linha legada com JSON `null` (inserida por SQL) e linha SQL NULL são miss no cache.
- Sem variável de ambiente nova. Originais de `01_output-context/` e documentos de gestão não foram tocados.

## Decisões propostas (não aplicadas)

- Registrar na DEC-59 P1 como resolvida via `none_as_null=True` no tipo da coluna, sem migration.
- **Dados legados:** linhas antigas com JSON `null` continuam no banco. São inofensivas (o cache e o expurgo as tratam). Um `UPDATE chamadas_ia SET resposta = NULL WHERE jsonb_typeof(resposta) = 'null'` as normalizaria, mas é opcional e não foi feito aqui. Se for feito, deve ser uma migration com `downgrade()` (que não consegue restaurar o JSON `null` original; é inofensivo).
- O script `limpar_chamadas_ia` já anulava em SQL NULL; fica consistente com `registrar()`.

## Verificação

Ambiente: PostgreSQL de `05_infra` em `localhost:5433` (usei `POSTGRES_HOST=127.0.0.1`, por causa do IPv6). Resultados de `pytest` e `ruff check .` estão na seção abaixo.

- `ruff check .` em 04_backend: **All checks passed**.
- `pytest tests/test_chamadas_ia_resposta_null.py tests/test_limpar_chamadas_ia.py tests/test_legenda_ia_telemetria.py`: **27 passed**.
- `pytest tests/test_legenda_ia*.py` junto: 176 passed, 1 failed, 18 errors. Os erros de `test_legenda_ia_endpoints.py` são de fixture de armazenamento (`botocore ClientError 403 HeadBucket`: o bucket S3/MinIO local recusa as credenciais do ambiente), não de `resposta`. Não investiguei o 1 failed isolado; a causa provável é a mesma, mas não foi confirmada.
- Não rodei `npm` (frontend não tocado). Credenciais do `.env` do checkout principal não foram usadas: o Postgres aceitou os padrões.
