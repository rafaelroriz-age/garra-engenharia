# Legenda IA: `Retry-After` no 429 (T108, pendência da T35)

## O que mudou
- `DomainError` (`04_backend/app/core/errors.py`) ganhou o kwarg opcional `headers: dict[str, str] | None = None`
  (retrocompatível; padrão `None`).
- `_problem_response` / `_handle_domain_error` (`04_backend/app/core/exception_handlers.py`) repassam
  `exc.headers` à `JSONResponse`. Corpo RFC 7807 inalterado.
- `LimiteLegendaIAExcedido` (`04_backend/app/services/legenda_ia/limites.py`) normaliza `retry_after` para
  inteiro >= 1 (`max(1, ceil(...))`) e envia `Retry-After: <retry_after>`; o corpo mantém
  `errors[0] = {field: retry_after_segundos, message: "<n>"}`, agora sempre igual ao header.
- Login (`auth.py`) usa `HTTPException` com `headers` próprio; não passa pelo handler de `DomainError` e não foi tocado.
- Sem nova variável de ambiente nem migration.

## Testes
`04_backend/tests/test_legenda_ia_retry_after.py` reutiliza a fixture `rota` de `test_legenda_ia_limites.py`:
- 429 após estourar o limite: header `Retry-After` inteiro >= 1, igual ao `message` de `retry_after_segundos`, `application/problem+json`.
- 404 (foto inexistente) e 422 (id inválido) não trazem `Retry-After`.

## Resultados
- `ruff check .` (04_backend): `All checks passed!`
- `pytest tests/test_legenda_ia_retry_after.py tests/test_legenda_ia_limites.py`: **56 passed**.
- `pytest -k "legenda or seguranca or auth" --ignore=tests/test_rfo_contexto.py`: 193 passed, 4 skipped, 6 xfailed,
  **39 failed, 27 errors**. Os erros de setup vêm de fixtures com storage real
  (`ClientError 403 HeadBucket Forbidden` no MinIO local: credenciais/bucket do ambiente), em
  `test_legenda_ia_endpoints.py`, `test_seguranca_legenda_ia.py` e afins; não tocam o handler alterado.
  Não rodei a mesma suíte no `main` para comparar, então a causa ambiental é inferida do erro, não provada.
- Obs. de ambiente: o worktree não tem `.venv`; usei o `.venv` do checkout principal. `tests/test_rfo_contexto.py`
  falha na coleta (`OSError: cannot load library 'libpango-1.0'`, WeasyPrint sem libs nativas no Windows),
  problema de ambiente alheio a esta tarefa; a suíte foi rodada com `--ignore=tests/test_rfo_contexto.py`.

## Propostas (não feitas)
- O limitador continua em memória por processo: com vários workers o limite não é compartilhado (armazenamento
  compartilhado, ex. Redis/Postgres, segue pendente).
- Outros 429 que usarem `DomainError` podem passar `headers={"Retry-After": ...}` diretamente.
