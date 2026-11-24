# Limpeza das marcas xfail de test_seguranca_legenda_ia.py (T107)

Status: **execução parcial. Nenhum teste foi alterado.** A remoção das marcas `xfail` depende de uma rodada completa e limpa, que não foi concluída.

Referências: `00_docs/backlog-auto/seguranca-legenda-ia.md` (achados SEG-IA-01..09), DEC-42 (aprovação só pelo auditor), pendência da T35.

## Ambiente

- Worktree: `.claude/worktrees/backlog-T107` (branch `worktree-backlog-T107`), sincronizado com `main` por `git merge --ff-only main`.
- Docker: instalado em `C:\Program Files\Docker\Docker\resources\bin` e fora do PATH. Containers ativos: `garra-postgres` (127.0.0.1:5433) e `garra-minio` (127.0.0.1:9000).
- Banco: `garra_engenharia_test` em `localhost:5433`. `alembic upgrade head` executado com sucesso.
- Venv: `04_backend/.venv` do checkout principal (o worktree não tem venv). O worktree não tem `04_backend/.env`, então as variáveis foram carregadas do `.env` do checkout principal, com `POSTGRES_HOST=localhost`, `POSTGRES_PORT=5433` e `POSTGRES_DB=garra_engenharia_test`. Valores de segredo não foram registrados aqui.
- Observação: uma primeira tentativa de `alembic` sem essas variáveis falhou com `ConnectionDoesNotExistError`, porque a porta padrão (5432) é de outro PostgreSQL.

## Rodada 1: `pytest tests/test_seguranca_legenda_ia.py -v -rxX -p no:warnings`

Saída final (literal, do arquivo de tarefa em background):

```
======== 1 failed, 8 passed, 8 xfailed, 3 errors in 1280.80s (0:21:20) ========
```

Linhas relevantes:

```
test_auxiliar_nao_aprova_legenda_ia
[XPASS(strict)] SEG-IA-05 (decisão pendente): RN-16 exige aprovação do profissional responsável; hoje o auxiliar aprova
XFAIL tests/test_seguranca_legenda_ia.py::test_gerar_tem_limite_de_taxa_por_usuario - SEG-IA-01: ...
XFAIL tests/test_seguranca_legenda_ia.py::test_regerar_apos_aprovar_limpa_aprovacao_anterior - SEG-IA-02: ...
XFAIL tests/test_seguranca_legenda_ia.py::test_editar_legenda_aprovada_nao_atribui_edicao_ao_aprovador_anterior - SEG-IA-03 (DEC-37 DP-10): ...
XFAIL tests/test_seguranca_legenda_ia.py::test_sugestao_longa_do_llm_nao_burla_limite_da_legenda - SEG-IA-04: ...   (duplicado no resumo)
XFAIL tests/test_seguranca_legenda_ia.py::test_auxiliar_nao_aprova_legenda_ia - SEG-IA-05 ...
XFAIL tests/test_seguranca_legenda_ia.py::test_auxiliar_nao_remove_foto_com_legenda_aprovada - SEG-IA-06 ...   (duplicado no resumo)
```

Traceback observado no meio da saída, de `boto3/s3/transfer.py:138`: `OSError: [Errno 22] Invalid argument` ao importar `s3transfer.subscribers`. Pelo caminho do erro, parece ser problema do ambiente Windows (caminho com acento em OneDrive), e não do código de produção. Isso não foi confirmado.

Os 3 erros não foram identificados, porque o início da saída foi cortado.

## Rodada 2

Iniciada com saída completa em arquivo (`-rfEXx --tb=short`). Foi **interrompida pelo sistema por falta de memória** antes de terminar. Não foi reiniciada.

## Interpretação parcial (sem alterar testes)

| Teste | Marca | Estado observado | Decisão proposta | Evidência |
|---|---|---|---|---|
| `test_auxiliar_nao_aprova_legenda_ia` | xfail strict (SEG-IA-05) | **XPASS(strict)**: o auxiliar recebeu 403 ao aprovar | Lacuna aparentemente corrigida (DEC-42). Remover a marca, depois de confirmar que o teste passa de forma limpa na rodada completa | rodada 1, linha `[XPASS(strict)]` |
| `test_gerar_tem_limite_de_taxa_por_usuario` | xfail (SEG-IA-01) | XFAIL na rodada 1 | Não confirmado. Pela T35 deveria estar corrigido (429 por usuário); o XFAIL indica que o teste ainda falha | rodada 1 |
| `test_regerar_apos_aprovar_limpa_aprovacao_anterior` | xfail (SEG-IA-02) | XFAIL na rodada 1 | Não confirmado. Pela T33 deveria estar corrigido | rodada 1 |
| `test_editar_legenda_aprovada_nao_atribui_edicao_ao_aprovador_anterior` | xfail (SEG-IA-03) | XFAIL na rodada 1 | Não confirmado. Pela T33 deveria estar corrigido | rodada 1 |
| `test_sugestao_longa_do_llm_nao_burla_limite_da_legenda` | xfail (SEG-IA-04) | XFAIL na rodada 1 | Não confirmado. Pela T35 deveria estar corrigido (teto de 500) | rodada 1 |
| `test_auxiliar_nao_remove_foto_com_legenda_aprovada` | xfail (SEG-IA-06) | XFAIL na rodada 1 | Não confirmado; sem correção documentada na T33/T35 | rodada 1 |

Atenção: o XFAIL nos testes 01–04 e 06 pode ser causado pelo erro de ambiente (`OSError` de boto3 ou MinIO), e não por falta de correção. Por isso nenhuma marca foi removida nesta rodada. Um XFAIL causado por erro de fixture não prova que a lacuna existe.

## Próximos passos

1. Liberar memória e rodar de novo `pytest tests/test_seguranca_legenda_ia.py -v -rfEXx --tb=short` a partir de `04_backend`, com as variáveis acima. Registrar a saída completa e a causa dos 3 erros.
2. Só depois remover o `xfail` dos testes que aparecem como XPASS(strict) e confirmar que passam de verdade. Manter `xfail` nos demais, com `reason` atualizado.
3. Rodar `pytest -k legenda` e `ruff check .` em `04_backend`.
4. Nenhuma decisão nova foi proposta. Se a rodada 2 confirmar SEG-IA-05 corrigido, a proposta é registrar DEC-37 DP-11 como decidida (auditor-only) no fechamento de lote.

Este Doc não altera `00_docs/projeto/decisoes.md`, `riscos.md`, `status.md` nem os backlogs.
