# Correção das lacunas de regras de Visitas (BL-10, tarefa T21)

Base: revisão de T15 (`revisao-regras-visitas.md`, L1–L18) e proposta DEC-38 (`00_docs/projeto/decisoes.md`), contra RN-01/RN-02 (`00_docs/estudo-do-contexto.md` §5) e RF-03. Este doc registra o que foi corrigido, o que ficou pendente e a saída dos comandos. `decisoes.md`, `revisao-regras-visitas.md`, backlog e documentos de gestão **não** foram editados; frontend não foi tocado.

> Observação de ambiente: o worktree desta tarefa nasceu de `origin/main` (14ead2f), que não tinha T15 nem DEC-38. A branch `worktree-backlog-T21` foi avançada por fast-forward até `main` local (059f3eb, "backlog: disparo de T21") antes de qualquer alteração.

## Resumo das mudanças

- **Schemas** (`app/schemas/visita*.py`): payloads com `extra="forbid"`; data da visita ≤ hoje; `PUT /visitas/{id}` parcial (campo omitido preserva, `observacoes: null` limpa, `data`/`servicos_executados` não aceitam `null`); equipe com `funcao` aparada e não vazia e `quantidade` inteira 1..32767; medição com `descricao`/`unidade` aparadas e não vazias (unidade segue livre, DEC-29) e `quantidade` ≥ 0 e finita.
- **Service** (`app/services/visita_service.py`): visita só em inspeção RFO (409); uma visita por dia por inspeção (409), na criação e no `PUT` que muda a data; lock `SELECT … FOR UPDATE` na inspeção antes de `max(seq_numero)+1`; `IntegrityError` dos UNIQUE vira 409 (nunca 500). Erros em RFC 7807 via `ConflictError`/`NotFoundError` (ADR-07).
- **Endpoints** (`app/api/v1/visitas.py`): `GET /visitas/{id}`; `GET|POST /visitas/{id}/mao-obra`, `GET|PUT|DELETE /visitas/{id}/mao-obra/{item_id}`; o mesmo para `/medicoes`. Todos com `require_equipe` (auditor/auxiliar, BL-42); cliente → 403. Item de outra visita → 404. `PUT` de item substitui o registro (todos os campos obrigatórios, então nada omitido se perde).
- **Modelo + migration**: `UNIQUE(inspecao_id, seq_numero)` e `UNIQUE(inspecao_id, data)` em `visitas` (`app/models/visita.py:27-30`, `alembic/versions/e5a1c3f7b9d2_visitas_unicidade_seq_e_data_bl_10.py`).

## Tabela L1–L18

"Antes" = linha de base medida nesta tarefa no banco de dev (execução B2). "Depois" = execuções R1–R4 após a correção, no banco descartável com a migration aplicada (ver "Comandos e saídas"). `infra` = falhou com `RuntimeError: There is no current event loop in thread 'MainThread'`, ou seja, a regra nem foi exercida (ver "Ajustes de teste").

| # | Lacuna | Antes | Depois | Correção (arquivo:linha) | Teste (`tests/test_visitas_lacunas.py`) |
|---|---|---|---|---|---|
| L1 | POST com data futura aceito (201) | FAIL | PASS (R1) | `app/schemas/visita.py:12-27` (`_hoje_limite`, `_validar_data`), `:65` | `test_lacuna_1_…` (:141) |
| L2 | PUT com data futura aceito (200) | FAIL | PASS (R1) | `app/schemas/visita.py:84` | `test_lacuna_2_…` (:152) |
| L3 | duas visitas no mesmo dia (POST, 201) | FAIL | PASS (R1) | `app/services/visita_service.py:64-67`; `app/repositories/visita_repository.py:43-49`; UNIQUE `app/models/visita.py:29` | `test_lacuna_3_…` (:164) |
| L4 | PUT move visita para dia já usado (200) | FAIL | PASS (R1) | `app/services/visita_service.py:75-87` | `test_lacuna_4_…` (:175) |
| L5 | `seq_numero` sem UNIQUE (corrida) | FAIL (infra) | PASS (R2, R3) | `app/models/visita.py:27-30`; migration `e5a1c3f7b9d2`; lock `app/repositories/visita_repository.py:36-40`; 409 `app/services/visita_service.py:26-43,70-72` | `test_lacuna_5_…` (:187) |
| L6 | visita em inspeção não RFO | FAIL ×2 (infra) | PASS ×2 (R2, R3) | `app/services/visita_service.py:21-23,59-63` | `test_lacuna_6_…[LTIP/VISTORIA]` (:199) |
| L7 | mão de obra com quantidade ≤ 0 (201) | FAIL ×2 | PASS ×2 (R1) | `app/schemas/visita_mao_obra.py:10` | `test_lacuna_7_…[0/-3]` (:213) |
| L8 | quantidade 2**40 → 500 | FAIL | PASS (R1) | `app/schemas/visita_mao_obra.py:10` (`le=32767`) | `test_lacuna_8_…` (:224) |
| L9 | função vazia/em branco (201) | FAIL ×2 | PASS ×2 (R1) | `app/schemas/visita_mao_obra.py:9` | `test_lacuna_9_…` (:236) |
| L10 | medição com quantidade negativa (201) | FAIL | PASS (R1) | `app/schemas/visita_medicao.py:11` | `test_lacuna_10_…` (:249) |
| L11 | descrição/unidade vazias (201) | FAIL ×4 | PASS ×4 (R1) | `app/schemas/visita_medicao.py:9-10` | `test_lacuna_11_…` (:262) |
| L12 | unidade sem trim (`'  m²  '`) | FAIL | PASS (R3) | `app/schemas/visita_medicao.py:10` | `test_lacuna_12_…` (:270) |
| L13 | cliente escreve em visitas | FAIL ×3 (infra); PASS ×3 isolado | PASS ×3 (R3) | já imposto por `require_equipe` (`app/api/deps.py`); mantido em todos os endpoints novos (`app/api/v1/visitas.py`) | `test_lacuna_13_…` (:292), `test_correcao_rbac_endpoints_novos` (:448) |
| L14 | PUT sem token | PASS | PASS (R3) | já imposto (`get_current_user`) | `test_lacuna_14_…` (:301) |
| L15 | auxiliar edita visita de outro contrato | FAIL (infra) | XFAIL (R3, R4) | **não corrigido**: depende do vínculo usuário↔contrato (DEC-27), decisão do dono | `test_lacuna_15_…` (:308, `xfail(strict=True, raises=AssertionError)`) |
| L16 | PUT aceita campos imutáveis em silêncio (200) | FAIL | PASS (R3) | `app/schemas/visita.py:77` (`extra="forbid"`) | `test_lacuna_16_…` (:329) |
| L17 | PUT sem `observacoes` apaga o valor | FAIL | PASS (R3) | `app/schemas/visita.py:69-85`; `app/repositories/visita_repository.py:82-87` (`exclude_unset`) | `test_lacuna_17_…` (:347), `test_correcao_put_parcial_…` (:384) |
| L18 | sem GET da visita nem GET/PUT/DELETE de itens (405) | FAIL | PASS (R3) | `app/api/v1/visitas.py:26-158`; `app/services/visita_service.py:90-161`; `app/repositories/visita_repository.py:90-167` | `test_lacuna_18_…` (:367), `test_correcao_crud_itens_…` (:401) |

**Limite da verificação:** L1–L4, L7–L11 e os testes de `tests/test_visitas.py`, exceto `test_atualizar_visita`, passaram em R1. Depois de R1 foram mudados só a infraestrutura de teste (teardown de `inspecao_factory`, `_cleanup_visita`, marca de L15) e uma troca equivalente em `visita_service.py:80` (`dados.data` → `data_alvo`, mesmo valor nesse ramo). Esses testes **não** foram reexecutados depois dessas mudanças, porque R1 foi interrompida por falta de memória (ver Comandos).

### Ajustes de teste

- **L15** está correto em relação à regra de DEC-27, mas a regra depende de uma decisão em aberto do dono (vínculo usuário↔contrato), que esta tarefa não resolve. Ganhou `pytest.mark.xfail(strict=True, raises=AssertionError, reason=…)`: continua documentando a lacuna e não quebra a suíte. Só a asserção 403 conta como falha esperada (erro de infraestrutura falha de verdade), e com `strict` vira XPASS/falha quando a regra existir, lembrando de remover a marca.
- **Erro de infraestrutura nos testes async** (causa das falhas `infra` da linha de base): `_cleanup_visita` em `tests/test_visitas.py` usava `asyncio.run`, que ao terminar chama `set_event_loop(None)` e derruba o loop de sessão do pytest-asyncio (`pytest.ini`: `asyncio_default_test_loop_scope = session`). Todo teste `async def` executado depois dele no mesmo processo falhava. Isolado, L13 passava (3 passed). Correção: loop próprio (`asyncio.new_event_loop()` + `run_until_complete` + `close`), sem registrá-lo como loop corrente. R3 roda `test_atualizar_visita` antes dos testes async e todos passam.
- **Teardown de `inspecao_factory`** (`MissingGreenlet` em R2): com o UNIQUE, L5 passa a gerar `IntegrityError` e faz `rollback`, o que expira os objetos da sessão. O teardown lia `insp.id` expirado, e isso dispara um lazy load síncrono. A fixture passou a guardar só os ids e faz `rollback` antes da limpeza.
- `ruff --fix` reordenou o bloco de imports de `test_visitas_lacunas.py` (I001). Nenhuma asserção de teste de lacuna foi alterada.
- Novos testes para o que foi criado: `test_correcao_put_parcial_null_limpa_observacoes_e_rejeita_obrigatorios` (null limpa `observacoes`, null em obrigatório → 422, mesma data não conflita consigo), `test_correcao_crud_itens_mao_obra_e_medicao` (listar/obter/PUT/DELETE, 422 no PUT inválido e com `visita_id` extra, 404 de item em outra visita e de visita inexistente, quantidade 0 válida na medição), `test_correcao_rbac_endpoints_novos` (cliente 403 em GET/DELETE novos; auxiliar 200/204).

## Migration `e5a1c3f7b9d2` (down_revision `d3b7c9e4f1a2`)

`alembic heads` antes da tarefa: `d3b7c9e4f1a2 (head)`; depois: `e5a1c3f7b9d2 (head)`. Altera **apenas** a tabela `visitas` (nenhuma tabela de fotos nem de ocorrências).

- `upgrade()`:
  1. Se houver **data duplicada** na mesma inspeção, aborta com `RuntimeError` que lista os pares `(inspecao_id, data)`. Não há correção automática segura (unir visitas ou mover a data exige decisão humana, e há fotos vinculadas por FK). Como o DDL do PostgreSQL é transacional, nada é alterado.
  2. **`seq_numero` duplicado** é renumerado de forma determinística, sem apagar nada: em cada grupo `(inspecao_id, seq_numero)` mantém o número a visita de menor `(data, id)`; as demais recebem `max(seq_numero) + n` da inspeção, na ordem `(seq_numero, data, id)`. Nenhum número que já era único muda. Consequência aceita: a visita renumerada pode ficar com número maior que uma visita de data posterior (ex.: 1,2,4,3,5,6 abaixo); renumerar a inspeção inteira por data mudaria números já usados em relatórios.
  3. Cria `uq_visitas_inspecao_id_seq_numero` e `uq_visitas_inspecao_id_data`.
- `downgrade()`: remove as duas constraints. A renumeração não é desfeita (os números duplicados originais eram inválidos e não são guardados).
- Banco de desenvolvimento (`garra_engenharia`, compartilhado com outros worktrees): 192 visitas no momento da consulta, **0** grupos com `seq_numero` duplicado e **0** com data duplicada (consulta somente leitura antes da migration). A migration não precisaria renumerar nada nele.

### Verificação em banco descartável

Para não deixar o banco de dev compartilhado numa revisão que ainda não está em `main` (outros worktrees falhariam com "Can't locate revision"), a migration nova foi validada num banco descartável `garra_t21_scratch`, criado no mesmo servidor (localhost:5433) e removido ao final. O banco de dev recebeu só o `alembic upgrade head` pedido (`7c1a4e0b93d5 → d3b7c9e4f1a2`) e continua em `d3b7c9e4f1a2`.

```text
# seq 1,2,2,3,3,3 em datas 07-01..07-06, upgrade d3b7c9e4f1a2 -> e5a1c3f7b9d2
[e5a1c3f7b9d2] 3 visita(s) com seq_numero duplicado renumerada(s).
2026-07-01 1 | 2026-07-02 2 | 2026-07-03 4 | 2026-07-04 3 | 2026-07-05 5 | 2026-07-06 6
unique: ['uq_visitas_inspecao_id_data', 'uq_visitas_inspecao_id_seq_numero']
# downgrade -1 -> constraints removidas, dados preservados; upgrade de novo -> OK
# data duplicada (2 visitas em 2026-07-01 na mesma inspeção) + upgrade:
RuntimeError: Há visitas na mesma data dentro de uma inspeção (RN-01: uma por dia). Corrija manualmente
(mover a data ou unir as visitas) antes de aplicar uq_visitas_inspecao_id_data: inspecao_id=34b9d244-… data=2026-07-01 (2 visitas)
alembic current -> d3b7c9e4f1a2 (nada aplicado; seq_numero do cenário anterior intacto)
```

## Pendências (não resolvidas aqui; decisão do dono)

1. **L15 / DEC-27**: o auxiliar edita visitas de qualquer contrato; restringir "aos contratos em que atua" exige vínculo usuário↔contrato (modelo + migration) ou aceitar a frase como intenção. Teste em `xfail` estrito.
2. **Status da inspeção**: não existe enum de `status` nem regra para inspeção concluída/emitida bloquear visitas novas ou edição.
3. **Mão de obra duplicada** (mesma função duas vezes na mesma visita): somar, rejeitar ou permitir? Hoje permite.
4. **Confirmação de interpretações de DEC-38**: o próprio DEC-38 diz que (A) "só RFO" e a data ≤ hoje precisam de confirmação do dono. Esta tarefa as implementou porque o pedido as lista como problemas a corrigir. Se o dono discordar, a reversão é pontual (`visita_service.py:59-63` e `schemas/visita.py:21-27`).
5. **`Inspecao.tipo` como enum** (parte de DEC-38 A) não foi feito: a coluna segue texto livre e há dados com `"ltip"` minúsculo (`tests/test_portal_cliente.py:97`). A checagem ignora caixa e espaços. Transformar em enum pede migration de dados própria.
6. **Data limite**: usa a data UTC (`schemas/visita.py:12-18`), que nunca fica atrás da de Brasília. Não recusa visita de hoje lançada à noite, mas tolera até ~3 h de "amanhã". Fuso por contrato fica para uma decisão futura, se for preciso.
7. **Fora do escopo**: `DELETE /visitas/{id}` (afeta fotos e numeração), listagem/paginação de visitas e `max_length` dos textos (nenhuma regra definida).
8. **Conflito com a Regra de pronto §4** ("nunca alterar dados existentes"): a renumeração de `seq_numero` duplicado altera dados por pedido explícito da tarefa. No banco de dev não há duplicata, então nada foi alterado. Em outro ambiente, conferir antes com a consulta da migration.

## Comandos e saídas

Todos a partir de `04_backend/`, com o Python 3.12.4 do `.venv` do checkout principal. O `04_backend/.env` local (no `.gitignore`, não versionado) foi copiado do checkout principal: `POSTGRES_HOST=localhost`, `POSTGRES_PORT=5433`.

**PostgreSQL.** `docker` não está no PATH do shell. `docker compose ps` em `05_infra` (via `C:\Program Files\Docker\Docker\resources\bin\docker.exe`) falha porque o worktree não tem `05_infra/.env` (`required variable POSTGRES_PASSWORD is missing a value`). `docker ps` (só leitura) mostra `garra-postgres  Up About an hour (healthy)  127.0.0.1:5433->5432/tcp`. Nenhum serviço foi subido nem derrubado.

```text
$ alembic current            # banco de dev, antes
7c1a4e0b93d5
$ alembic upgrade head       # única vez no banco de dev (o schema já existia; faltava a última revisão)
Running upgrade 7c1a4e0b93d5 -> d3b7c9e4f1a2, prioridade_sugerida_sobrescrita_bl_15
$ alembic heads              # depois de criar a migration desta tarefa
e5a1c3f7b9d2 (head)
```

**B1/B2: linha de base** (código original, banco de dev em `d3b7c9e4f1a2`):

```text
$ python -m pytest tests/test_visitas.py tests/test_visitas_lacunas.py -q
25 failed, 7 passed, 6 warnings in 685.05s (0:11:25)        # B1
$ python -m pytest tests/test_visitas.py tests/test_visitas_lacunas.py -q --tb=line -W ignore
25 failed, 7 passed in 681.83s (0:11:21)                    # B2, com o motivo de cada falha
# passaram: os 6 de test_visitas.py e L14. L5, L6×2, L13×3 e L15: RuntimeError de event loop (infra).
# demais: AssertionError com o status 201/200/405/500 indicado na coluna "Lacuna".
$ python -m pytest "tests/test_visitas_lacunas.py::test_lacuna_13_cliente_nao_escreve_em_visitas" -q
3 passed, 1 warning in 89.21s                               # L13 isolado: a regra já era imposta
```

**Depois da correção** (banco descartável `garra_t21_scratch` em `e5a1c3f7b9d2`, via `POSTGRES_DB=garra_t21_scratch`):

```text
# R1: suíte dos dois arquivos. INTERROMPIDA pelo Claude Code por pouca memória livre no sistema
# (não é falha do comando) e não reiniciada. Saída parcial, na ordem de coleta:
..........FFF..........
# = test_visitas.py 6/6 PASS, L1–L4 PASS, L5 + L6×2 FAIL (event loop, infra), L7–L11 (10 casos) PASS

# R2: diagnóstico isolado
$ python -m pytest "…::test_lacuna_5_…" "…::test_lacuna_6_visita_so_para_inspecao_rfo" -q --tb=line
3 passed, 1 error in 48.25s        # o error é MissingGreenlet no teardown de inspecao_factory (corrigido)

# R3: depois dos ajustes de teste (≈2,2 GB de RAM livres no início)
$ python -m pytest "tests/test_visitas.py::test_atualizar_visita" tests/test_visitas_lacunas.py \
    -k "test_atualizar_visita or lacuna_5 or lacuna_6 or lacuna_12 or lacuna_13 or lacuna_14 or lacuna_15 or lacuna_16 or lacuna_17 or lacuna_18 or correcao" -q -rxX
.........x......
XFAIL tests/test_visitas_lacunas.py::test_lacuna_15_auxiliar_nao_edita_visita_de_outro_autor - Pendente de decisão do dono: vínculo usuário<->contrato de DEC-27 (L15). …
15 passed, 14 deselected, 1 xfailed in 483.62s (0:08:03)

# R4: L15 depois de acrescentar raises=AssertionError
1 xfailed in 33.45s
```

**ruff:**

```text
$ ruff check tests/test_visitas.py tests/test_visitas_lacunas.py app alembic
app\scripts\vistoria_cautelar_layout_extractor.py:81:56: RUF001 …   # pré-existente, arquivo não tocado
app\scripts\vistoria_cautelar_layout_extractor.py:86:44: RUF001 …   # pré-existente, arquivo não tocado
Found 2 errors.
$ ruff check tests/test_visitas_lacunas.py
All checks passed!
$ ruff check .
Found 9 errors.   # todos pré-existentes, em arquivos não tocados (vistoria_cautelar_layout_extractor.py,
                  # test_ocorrencias_regras.py, test_vistoria_cautelar_pipeline.py, test_vistoria_cautelar_templates.py).
                  # Antes eram 10: o I001 de test_visitas_lacunas.py foi corrigido.
```

**Não rodou:**

- **`pytest` completo do backend.** A coleta tem 230 testes e 5 erros de coleta de ambiente (`ModuleNotFoundError: pdfplumber`/`openpyxl` em `test_ltip_templates.py`, `test_rfip_templates.py`, `test_rfo_templates.py`, `test_vistoria_cautelar_templates.py` e `test_vistoria_residencial_templates.py`). Não instalei pacotes no venv compartilhado. A ~20 s por teste de integração neste host, a suíte completa levaria mais de 1 h, e o sistema já tinha interrompido R1 por falta de memória. Ficam **sem verificação nesta tarefa** os outros arquivos que criam visitas: `test_rbac_auxiliar.py` (via API, data `2026-09-10`, uma por inspeção), `test_fotos.py`, `test_models.py` e `test_portal_cliente.py` (via ORM, uma visita por inspeção; o de portal usa inspeção `"ltip"`, mas insere direto no ORM e não passa pela regra de RFO do service). Pela leitura, nenhum deles viola os UNIQUE novos.
- **Frontend:** não tocado, então `npm run lint` e `npm run build` não se aplicam.

Para reproduzir depois do merge: `cd 04_backend && alembic upgrade head && pytest tests/test_visitas.py tests/test_visitas_lacunas.py && pytest && ruff check .`.
