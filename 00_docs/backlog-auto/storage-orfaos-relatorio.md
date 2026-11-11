# T32 — Relatório de órfãos do storage em dry-run (DEC-44, itens 1-3)

## O que foi feito

- `StorageClient.list_objects(prefix)` (novo) devolve `list[tuple[str, datetime]]` = `(chave, LastModified)`.
  Implementado em `S3StorageClient` (paginado, `list_objects_v2`). Em `StorageClient` é método **não abstrato**
  que levanta `NotImplementedError`, para não quebrar fakes existentes. `list_keys` e `listar_orfaos`
  ficaram inalterados.
- `app/scripts/relatorio_orfaos.py` — `python -m app.scripts.relatorio_orfaos [--idade-minima-horas 24] [--prefixo fotos/]`.
  - `consultar_chaves_vinculadas()` (async, `Foto.storage_key` via `AsyncSessionLocal`) — isolada; o núcleo
    `gerar_relatorio(storage, consulta_vinculos, prefixo, idade_minima_horas, agora)` recebe a consulta por injeção.
  - Fluxo: vínculos do banco → `listar_orfaos` → cruza com `list_objects` → filtra idade > limite.
- **Somente dry-run**: o script não tem chamada de exclusão nem flag que apague (há teste que verifica isso).
- Nenhuma variável de ambiente nova.
- Limpeza lateral: removidas as definições duplicadas de `exists` em `base.py` e `s3_client.py`
  (F811 do ruff, vindas da T30; corpo idêntico, sem mudança de comportamento).

## Formato do relatório

```
Relatório de órfãos (DRY-RUN — nada é apagado) prefixo='fotos/' idade>24.0h
CHAVE                                                        LAST_MODIFIED (UTC)  IDADE_H
fotos/antigo-orfao.jpg                                       2026-11-03 12:00:00  48.0
Total de órfãos: 1
```

## Testes (`tests/test_relatorio_orfaos.py`, S3 falso próprio, sem banco/MinIO)

Objeto novo (<24 h) não aparece; antigo sem vínculo aparece; antigo vinculado não aparece; o falso não
recebe `delete_object`/`delete_objects`; idade mínima configurável; o código-fonte não contém chamada de exclusão.

## Comandos e saídas (a partir de `04_backend`)

- `python -m pytest tests/test_relatorio_orfaos.py tests/test_storage_legenda_ia.py -q` → `9 passed`.
- `ruff check app/scripts/relatorio_orfaos.py app/services/storage tests/test_relatorio_orfaos.py` → `All checks passed!`
- `ruff check .` (projeto inteiro) → 10 erros **preexistentes**, em arquivos não tocados (I001, RUF005, RUF001, RUF043).
- A execução real do script contra PostgreSQL/MinIO **não foi feita** (sem serviços no ambiente); só os testes com falso.
- A suíte completa do `pytest` não foi executada (exigiria PostgreSQL em localhost:5433); só os dois arquivos pedidos.

## Fora do escopo / pendências

- **Exclusão**: apagar exige aprovação manual da lista (DEC-44 item 3); fica para tarefa futura.
- **Item 4 de DEC-44** (prefixos `fotos/` x `ia/`): não tratado; o script usa `--prefixo fotos/` por padrão.
- Agendamento periódico do relatório (item 1) não foi criado; hoje é execução manual.
- DEC-44 continua "Proposta"; `decisoes.md` não foi editado (atualizar no fechamento de lote).
