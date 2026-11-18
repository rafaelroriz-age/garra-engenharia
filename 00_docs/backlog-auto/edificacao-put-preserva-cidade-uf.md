# PUT de Edificação preserva `cidade`/`uf` ausentes (DEC-59)

Status: **implementado e testado** no backend. Origem: DEC-59 (proposta de T96), que registrou «`PUT /edificacoes/{id}` sem `cidade`/`uf` zera os dois». Esta tarefa corrige esse comportamento.

## Decisão aplicada (DEC-59, proposta)

`cidade` e `uf` no `PUT /api/v1/edificacoes/{id}` distinguem **campo ausente** de **campo enviado**:

| Corpo do PUT | Resultado |
|---|---|
| `cidade`/`uf` ausentes | valor atual preservado |
| `cidade`/`uf` com valor | gravados (normalizados pelo schema) |
| `cidade`/`uf` como `null`, vazio ou só espaços | gravados como `null` |

Implementação: `04_backend/app/repositories/edificacao_repository.py`, `update()`. Usa `dados.model_fields_set` para descartar do `model_dump()` apenas `cidade`/`uf` que não vieram no corpo (constante `CAMPOS_PRESERVAVEIS_AUSENTES`). Os demais campos mantêm a substituição do BL-08: o `PUT` não virou parcial. Não houve mudança em `schemas/edificacao.py` nem em `services/edificacao_service.py`: o validador já trata vazio como `None`, e `model_fields_set` é preenchido pelo Pydantic antes de chegar ao repositório.

## Ajuste em teste existente

`tests/test_edificacao_cidade_uf.py::test_atualizar_define_e_remove_cidade_uf` afirmava que um `PUT` sem `cidade`/`uf` zerava os dois, o que codificava o bug da DEC-59. Foi renomeado para `test_atualizar_define_e_preserva_cidade_uf`, e a asserção final agora espera `("Goiânia", "GO")`. Nenhum outro teste existente dependia de campos ausentes virarem `null`: `tests/test_edificacoes.py::test_atualizar_edificacao` envia só `nome`/`endereco` e não checa `cidade`/`uf`.

## Testes novos (`tests/test_edificacao_cidade_uf.py`)

- `test_put_sem_cidade_uf_preserva_valores_existentes`: cria com `Anápolis`/`GO`, faz `PUT` só com `nome`/`endereco`, confere a resposta e um `GET` de releitura.
- `test_put_com_cidade_uf_null_zera_os_dois`: `null` explícito zera os dois.
- `test_put_com_cidade_vazia_e_uf_ausente_zera_so_cidade`: `cidade: "   "` vira `null` e `uf` ausente é preservada (`GO`).

## Testes e verificação

Ambiente: PostgreSQL de `05_infra` (`localhost:5433`, usuário `garra`).

O banco `garra_engenharia` local não foi usado para os testes. Ele está num estado em que a migration `d3e7a1c5f9b2` (`edificacao_cidade_uf_dec_50`) é bloqueada por 1 grupo duplicado em `relatorios` (`inspecao_id, tipo, versao` = `RFO`/`BENCH-01`). A migration se recusa a apagar dados, o que é o comportamento esperado; a limpeza cabe ao dono. Para não tocar nesses dados, criei o banco separado `garra_test_t104` no mesmo servidor e rodei `alembic upgrade head` nele.

| Comando | Onde | Resultado |
|---|---|---|
| `pytest tests/test_edificacao_cidade_uf.py tests/test_edificacoes.py -q` | host, `POSTGRES_DB=garra_test_t104` | **44 passed** |
| `ruff check .` | host | `All checks passed!` |
| `pytest` (suite completa) | host, `--continue-on-collection-errors` | **não concluiu**: a execução em background foi encerrada pelo sistema por falta de memória, sem resultado. Não foi reiniciada automaticamente. |

Na suite completa no host, `tests/test_rfo_contexto.py` não coleta (`OSError: cannot load library 'libpango-1.0-0'`, WeasyPrint sem bibliotecas nativas no Windows). É problema de ambiente, sem relação com esta mudança. Pendente: rodar a suite completa de novo quando houver memória (ou na imagem `05_infra-backend`) para confirmar que nada regrediu além dos testes de edificação.

## Decisões propostas

1. Registrar em DEC-59 (ou nova DEC): «`PUT /edificacoes/{id}`: `cidade`/`uf` ausentes são preservados; `null` explícito os limpa». Isso substitui a consequência de zeramento hoje registrada na DEC-59.
2. Os demais campos do `PUT` continuam substituídos (BL-08). Uma eventual mudança para PATCH parcial da Edificação fica para decisão própria.

## Pendências

- Frontend (`03_frontend/app/edificacoes/`): com o backend corrigido, reenviar `cidade`/`uf` no `PUT` deixa de ser necessário para não apagá-los. Ainda vale expor os dois campos no formulário (ver `edificacao-cidade-uf-frontend.md`).
- Banco local `garra_engenharia` (5433): tem 1 grupo duplicado em `relatorios` (`RFO`/`BENCH-01`) que impede `alembic upgrade head`. Precisa de decisão do dono sobre qual registro manter.
