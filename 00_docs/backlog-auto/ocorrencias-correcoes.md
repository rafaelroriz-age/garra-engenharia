# Correções das lacunas L1–L7 de Ocorrências (T08, DEC-34 / R-13)

Continuação da T06 (`00_docs/projeto/revisao-regras-ocorrencias.md`). Sem migration, sem alteração de models, sem frontend. BL-15 (prioridade derivada) e BL-16 (0 a 5) não foram tocados.

**Aviso de ambiente:** esta branch (`worktree-backlog-T08`) não continha o commit da T06; ele foi trazido por `git cherry-pick cd0284c` (doc de revisão + `tests/test_ocorrencias_regras.py`, ambos só adições). O arquivo `ocorrencias-revisao.md` citado no enunciado não existe nesta branch nem em `main`; usei o doc de revisão da T06.

## Resultado dos testes: NÃO RODARAM

Sem Docker (`docker: command not found`), `localhost:5433` recusa conexão (`connect_ex` = 10061) e o Python local não tem `pytest_asyncio` nem `asyncpg`. **Nenhum teste foi executado, nem a linha de base nem depois das correções.** As correções foram feitas por análise estática; a validação fica pendente.

## Tabela L1–L7

| # | Antes | Depois | Arquivo:linha | Teste |
|---|---|---|---|---|
| L1 | Situação aceitava qualquer string | `DomainError` 422 `ocorrencia-situacao-invalida` se fora de {CONFORME, NAO_CONFORME} | `app/services/ocorrencia_service.py:16,101` | `test_lacuna_situacao_fora_do_enum_e_rejeitada` |
| L2 | Classificação aceitava qualquer string | `DomainError` 422 `ocorrencia-classificacao-invalida` se fora de {ANOMALIA, FALHA, ANOMALIA_FALHA, NAO_SE_APLICA}; checado antes das regras de tipo | `ocorrencia_service.py:17,105` | `test_lacuna_classificacao_fora_do_enum_e_rejeitada` |
| L3 | Sistema inexistente → 500 (FK) | `NotFoundError` 404 `sistema-nao-encontrado` | `ocorrencia_service.py:118-121`; consulta `get_sistema` em `app/repositories/ocorrencia_repository.py` | `test_lacuna_sistema_inexistente_retorna_404` |
| L4 | Subsistema inexistente → 500; de outro sistema era aceito | 404 `subsistema-nao-encontrado`; 422 `ocorrencia-subsistema-incoerente` se `subsistema.sistema_id != sistema_id` | `ocorrencia_service.py:122-131` | `test_lacuna_subsistema_inexistente_retorna_404`, `test_lacuna_subsistema_de_outro_sistema_e_rejeitado` |
| L5 | Inspeção inexistente → 500 (FK) | 404 `inspecao-nao-encontrada` em `criar` | `ocorrencia_service.py:54-55`; `ocorrencia_repository.inspecao_existe` | `test_lacuna_inspecao_inexistente_retorna_404` |
| L6 | `PUT` sobrescrevia `inspecao_id` e `seq_numero` | `model_dump(exclude={"inspecao_id", "seq_numero"})` | `app/repositories/ocorrencia_repository.py:118` | `test_lacuna_atualizar_preserva_inspecao_e_seq_numero` |
| L7 | Filtro `sistema_id` inválido → 500 (`ValueError`) | Parâmetro tipado `uuid.UUID`; FastAPI devolve 422; service e repositório também tipados | `app/api/v1/ocorrencias.py:30`; `ocorrencia_repository.py:41` | `test_lacuna_filtro_sistema_id_invalido_retorna_422` |

`atualizar` também chama `_validar_referencias` (L3/L4), mas não revalida a inspeção (ela não muda mais, L6). Nenhum teste `test_lacuna_*` foi alterado: todos estão coerentes com a regra.

O 422 do filtro (L7) vem do handler padrão do FastAPI, não do RFC 7807 do domínio; o teste só confere o status.

## Pendências de decisão do dono (não implementadas)

- **P1** — Restringir ocorrência a Inspeção LTIP (hoje fixtures e dashboard usam RFO).
- **P2** — Auxiliar pode excluir ocorrência? (DEC-27 é omissa; `DELETE` usa `require_equipe`.)
- **P3** — Enums no banco (exigiria migration; L1/L2 ficaram só no service).
- **P4** — Autoria de `prioridade_ajustada_*` é regravada a cada `PUT` enquanto a prioridade diferir da sugestão.

## Comandos e saídas

| Comando | Resultado |
|---|---|
| `docker compose ps` (05_infra) | `docker: command not found`; banco indisponível |
| `pytest tests/test_ocorrencias_dashboard.py tests/test_ocorrencias_prioridade.py tests/test_ocorrencias_regras.py` | **Não rodou** (sem `pytest_asyncio`/`asyncpg`, sem PostgreSQL) |
| `ruff check` nos 3 arquivos alterados + `tests/test_ocorrencias_regras.py` | 14 erros, todos pré-existentes (B008 `Depends`/`Query`, I001, F401 `Foto`, UP017); nenhum em linha nova |
| `ruff check .` (04_backend) | 212 erros pré-existentes; não zerado, fora do escopo |

Para validar: `docker compose up -d` em `05_infra`, instalar as dependências de dev e rodar o `pytest` acima. Pontos a conferir com banco: `test_ocorrencias_prioridade.py` envia `seq_numero` nulo no `PUT` (agora ignorado) e as fixtures precisam ter `subsistema_id` coerente com o sistema.
