# T33 — Aprovação de legenda IA só por auditor e invalidação ao editar/regerar (DEC-42 A e B)

Escopo: SEG-IA-03, SEG-IA-04, SEG-IA-05 de `seguranca-legenda-ia.md`. Fora de escopo (tarefa à parte): limite de taxa e saneamento da saída do LLM (DEC-42 C e D) e frontend.

## Antes / depois

| Situação | Antes | Depois |
|---|---|---|
| `PUT /fotos/{id}` com `aprovar_legenda_ia: true` por auxiliar | 200, aprovava | **403** RFC 7807 (`.../acesso-negado`), nada gravado |
| Mesmo PUT pelo auditor | 200, aprovava | igual |
| Auxiliar gera (`legenda-ia/gerar`) e edita rascunho | permitido | permitido (inalterado) |
| Regerar legenda de foto aprovada | mantinha `aprovado_por_id/em` com status `rascunho` | `aprovado_*` nulos e status `rascunho` |
| `PUT` que muda `legenda` de foto aprovada | mantinha a aprovação (DP-10 de DEC-37) | volta a `rascunho`, `aprovado_*` nulos |
| `PUT` sem mudar `legenda` (só `ordem`, ou mesma `legenda`) | mantinha | mantém (não invalida) |

## Arquivos

- `04_backend/app/api/v1/fotos.py` (import de `DomainError`; checagem em `atualizar_foto`, ~l.124): 403 se `aprovar_legenda_ia` e `usuario.role != "auditor"`. Feita no endpoint porque o papel exigido depende do corpo; a rota segue com `require_equipe`. O 403 sai antes de qualquer acesso à foto.
- `04_backend/app/services/foto_service.py`: `_invalidar_aprovacao` (l.142); `atualizar` invalida quando `legenda` enviada difere da atual e a foto está `aprovada` (l.~180-185, ramo `elif` do fluxo de aprovação); `gerar_legenda_ia` chama `_invalidar_aprovacao` (l.221).
- Sem migration e sem mudança em models/schemas: os campos necessários já existem.

## Testes

- Novo `04_backend/tests/test_legenda_ia_aprovacao.py` (6 testes; reaproveita fixtures de `test_legenda_ia_endpoints.py`): auxiliar aprova → 403 problem+json; auxiliar gera e edita rascunho; auditor aprova; regerar aprovada invalida; PUT que muda `legenda` invalida; PUT só `ordem`/mesma `legenda` não invalida.
- Ajustado `test_legenda_ia_endpoints.py`: `test_auxiliar_gera_e_aprova` virou `test_auxiliar_gera_mas_nao_aprova` (parametrizado visita/ocorrência): o auxiliar gera (200), tenta aprovar (403) e o auditor aprova. Motivo: o contrato antigo (auxiliar aprova) é exatamente o que DEC-42 A proíbe.

## Comandos e resultados

Ambiente deste worktree: o worktree estava numa base antiga; foi feito `git merge --ff-only main` (local) para trazer o código da T25 e o DEC-42.

- `pytest tests/test_legenda_ia_endpoints.py tests/test_legenda_ia_aprovacao.py tests/test_fotos.py`: **NÃO RODOU.** O Python do ambiente não tem `pytest_asyncio` (`ModuleNotFoundError` ao carregar `conftest.py`), o PostgreSQL de `05_infra` (localhost:5433) não respondeu (timeout) e não há `docker` no PATH deste shell. Os testes novos não foram executados; só compilação (`python -m py_compile` ok) e lint.
- `ruff check` nos 4 arquivos tocados: `All checks passed!`. `ruff check .` na pasta toda: 11 erros, todos em arquivos não tocados (`vistoria_cautelar_*`, `test_foto_origem_enum.py`, `test_ocorrencias_regras.py`, `test_storage_legenda_ia.py`), preexistentes.
- **Pendente para o integrador:** rodar os três arquivos de teste com PostgreSQL/MinIO no ar e as dependências de `requirements`.

## Consequência para a UI (T26)

O painel de legenda IA deve esconder/desabilitar «Aprovar» para o perfil `auxiliar` (só `auditor` vê o botão); o auxiliar continua com «Gerar» e edição do rascunho. Após editar a legenda de uma foto aprovada ou regerar, o estado volta a «rascunho» e o selo de aprovado precisa sumir (a resposta do PUT/POST já traz `status_validacao_ia` e `aprovado_*` atualizados). Tratar também um 403 do PUT como mensagem clara. Tarefa de frontend à parte.

## Para o fechamento de lote (00_docs/projeto/)

- `decisoes.md`: registrar em DEC-42 andamento dos itens A e B (C e D seguem abertos; decisão continua proposta até o dono aprovar).
- `seguranca-legenda-ia.md`: SEG-IA-03/04/05 corrigidos no código, aguardando execução dos testes.
- Aprovação por fluxo `cliente`/portal não foi tocada.
