# Responsáveis: POST com `usuario_id` já vinculado (DEC-59)

**Status: CONCLUÍDA** (branch `worktree-backlog-T103`). Não há push; o integrador atualiza o backlog.

## Problema

`POST /api/v1/responsaveis` com `usuario_id` já vinculado a outro Responsável
caía na violação de unicidade do banco e retornava **500**. O `PUT` já tratava
o caso (422 se o usuário não existe; 409 se já vinculado).

## O que foi feito

- Extraída a regra para `_validar_vinculo_usuario` em
  `04_backend/app/api/v1/responsaveis.py`. Ela é usada pelo `POST` e pelo `PUT`
  (sem duplicação):
  - usuário inexistente → `DomainError` (422, Problem Details);
  - usuário já vinculado a outro Responsável → `ConflictError` (409, Problem Details);
  - o parâmetro `responsavel_id` exclui o próprio Responsável da checagem
    (no `PUT`), e é `None` na criação.
- `POST`: chama o helper só quando `usuario_id` vem preenchido, e envolve o
  `commit` em `try/except IntegrityError` → 409 com rollback, igual ao `PUT`
  (cobre a corrida entre a checagem e o insert).
- Demais casos do contrato não mudaram (sem `usuario_id` → 201 como antes).

## Testes

Adicionados em `04_backend/tests/test_responsaveis.py`:

- `test_criar_responsavel_com_usuario_ja_vinculado_retorna_409_rfc7807`
- `test_criar_responsavel_com_usuario_inexistente_retorna_422_rfc7807`

## Comandos e resultados

| Comando (a partir de `04_backend/`) | Resultado |
|---|---|
| `python -m pytest tests/test_responsaveis.py tests/test_responsaveis_update.py -q -p no:warnings` | **17 passed** (com PostgreSQL de `05_infra/` em `localhost:5433`, verificado como acessível) |
| `python -m ruff check .` (ruff 0.17.5, instalado no ambiente) | **All checks passed!** |
| `python -m pytest -q` (suíte completa, excluindo `tests/test_rfo_contexto.py`) | **Não concluído.** Ver abaixo |

### Suíte completa: o que não fechou

- `tests/test_rfo_contexto.py` não importa neste Windows: WeasyPrint não
  encontra `libpango-1.0-0`. Problema de ambiente, excluído da execução.
- A suíte completa ficou lenta e com várias falhas em outras áreas; não consegui
  concluí-la nesta sessão. Amostra verificada, `test_contratos.py`,
  `test_rbac_portal.py`, `test_portal_cliente.py`, `test_edificacao_cidade_uf.py`
  e `test_models.py`: **55 passed, 2 failed**. As 2 falhas são
  `test_portal_cliente.py::test_download_docx_inexistente_retorna_404` e
  `::test_download_de_relatorio_de_outro_contratante_retorna_404`, ambas por
  `botocore ClientError 403 Forbidden` no `HeadBucket` do S3. É falta de
  credencial de storage no ambiente, não relacionado a Responsável.
- Um primeiro teste meu falhou por ordem de limpeza (o próprio teste apagava o
  Responsável antes do segundo POST). Corrigido: a limpeza ficou no `finally`.

Ou seja: o que cobre esta mudança passa; a suíte completa não foi validada
inteira aqui.

## Decisões propostas (para o fechamento de lote)

- Confirmar que o `POST` deve seguir a mesma regra do `PUT` (422/409 em
  `usuario_id`), como fecha a lacuna registrada em DEC-59. Sem mudança de contrato
  nos demais casos.
- Sugerir ao integrador rodar a suíte completa em ambiente com WeasyPrint e
  credenciais S3 de teste, para validar as falhas de ambiente acima.
