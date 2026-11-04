# Revisão de regras — Registro de Visitas do RFO (BL-10, tarefa T15)

Método igual ao de Ocorrências (BL-14); o doc `revisao-regras-ocorrencias.md` não existia neste worktree, então o formato foi inferido do pedido. Escopo: só revisão — **nenhum código de produção foi alterado**; as lacunas são provadas por `04_backend/tests/test_visitas_lacunas.py`, que afirma o comportamento correto (falhará até a tarefa de correção).

Fontes lidas: RF-03, RN-01, RN-02, RN-18 (`00_docs/estudo-do-contexto.md`), DEC-27 e DEC-29 (`00_docs/projeto/decisoes.md`); `app/api/v1/visitas.py`, `app/api/v1/inspecoes.py`, `app/services/visita_service.py`, `app/repositories/visita_repository.py`, modelos `visita*.py`, schemas `visita*.py`, `tests/test_visitas.py`.

## Resultado da execução

**Não rodou.** O PostgreSQL responde em `localhost:5433`, mas o banco está sem o schema (`asyncpg ... UndefinedTableError` já nos 6 testes de `tests/test_visitas.py`, que são pré-existentes e não dependem do meu código). Resultado: `58 errors` (todos de fixture/setup, 158 s). Não apliquei `alembic upgrade head` por ser alteração de estado do banco compartilhado fora do escopo da tarefa. Para reproduzir: `cd 05_infra && docker compose up -d`, `cd 04_backend && alembic upgrade head`, `pytest tests/test_visitas.py tests/test_visitas_lacunas.py`. Os testes foram **coletados** com sucesso (26 funções, 36+ casos parametrizados) e `ruff check tests/test_visitas_lacunas.py` está limpo. `ruff check .` no backend inteiro acusa 215 erros pré-existentes (não relacionados; inclui I001 em `test_visitas.py`).

Como não houve execução, a coluna "falha hoje?" abaixo é **análise estática do código**, não resultado medido.

## Matriz regra → imposição no código → teste

| Regra | Onde é imposta hoje | Teste existente | Lacuna / teste novo | Falha hoje? (análise) |
|---|---|---|---|---|
| RN-02 serviços executados obrigatório | `field_validator` em `VisitaCreatePayload`/`VisitaUpdatePayload` | `test_criar_visita_sem_servicos_executados_retorna_422` (só POST) | PUT em branco sem teste (validador existe) | não |
| RN-01 `seq_numero` sequencial | `_proximo_seq_numero` = max()+1, sem lock nem UNIQUE | `test_criar_visita_atribui_seq_numero_sequencial` | **L5** sem UNIQUE(inspecao_id, seq_numero): corrida gera duplicata | sim |
| RN-01 uma visita por dia | nenhuma | — | **L3** (POST), **L4** (PUT) | sim |
| RN-01/02 data coerente | só tipo `date` | — | **L1** (POST), **L2** (PUT) data futura | sim |
| RF-03 visitas "para RFO" | nenhuma (`Inspecao.tipo` é String livre; `criar_visita` só checa existência) | — | **L6** LTIP/VISTORIA | sim |
| FK inspeção existe | `inspecao_service.obter_por_id` → 404 | `..._inspecao_inexistente_retorna_404` | — | não |
| FK visita existe em mão de obra/medição/PUT | `obter_por_id` → 404 | **sem teste** | cobertura faltante, comportamento já correto | não |
| RN-02 equipe: função + quantidade | `funcao: str`, `quantidade: int` sem restrições | happy path | **L7** qtd ≤ 0, **L8** qtd > int32 (500), **L9** função vazia | sim |
| RF-03/DEC-29 medição, unidade livre | `quantidade: float`, `unidade: str` sem restrições | happy path | **L10** qtd negativa, **L11** descrição/unidade vazias, **L12** unidade sem trim | sim |
| RN-18/DEC-27 cliente sem escrita | `require_equipe` (auditor/auxiliar) | `test_rbac_*` (outros) | **L13** (regressão) cliente → 403; **L14** sem token → 401 | não (travam regressão) |
| DEC-27 auxiliar só em "contratos em que atua" | não existe vínculo usuário↔contrato | — | **L15** auxiliar edita visita do auditor | sim |
| PUT não altera imutáveis (`seq_numero`, `inspecao_id`, `criado_por_id`) | schema omite os campos; extras ignorados em silêncio | — | **L16** exige 422 (extra='forbid'); hoje 200 e valor de fato não muda | sim (contrato) |
| PUT preserva dado omitido | `update_visita` atribui `observacoes=None` | — | **L17** PUT sem `observacoes` apaga o valor | sim |
| RF-03 registro corrigível | só POST de mão de obra/medição; sem GET/PUT/DELETE de item, sem `GET /visitas/{id}` | — | **L18** GET visita e DELETE de item | sim |

## Lacunas não testadas / decisões a tomar

- **Paginação/filtros:** não existe endpoint de listagem de visitas (só o detalhe da inspeção embute as visitas), logo não há o que validar; vale quando L18 criar listagens.
- **Status da inspeção:** não há enum de `status` nem regra para inspeção concluída/emitida aceitar novas visitas; sem regra definida, não testável. Perguntar ao cliente.
- **Mão de obra duplicada (mesma função na mesma visita):** a regra não está definida (somar? rejeitar?); não testada.
- **L1/L2 (data futura) e L6 (tipos)** são interpretações de RN-01/RF-03; confirmar com o dono antes de corrigir (ver propostas).
- **L15:** exige criar o vínculo usuário↔contrato (migration) ou aceitar que "contratos em que atua" é só intenção; hoje DEC-27 não tem imposição.
- **L13/L14** provavelmente passam hoje — são rede de segurança, não defeitos.
- Overflow de `quantidade` float (`1e400`) não é testável via JSON padrão (o parser rejeita).

## Propostas de decisão (apenas aqui; não editar `decisoes.md`)

- **DEC-prop-A:** visita só em inspeção `tipo == "RFO"`; criar visita em outro tipo → 409. Validar `Inspecao.tipo` como enum.
- **DEC-prop-B:** unicidade `(inspecao_id, data)` e `(inspecao_id, seq_numero)` no banco (migration com `downgrade()`), 409 no serviço; data de visita ≤ hoje.
- **DEC-prop-C:** payloads de Visita/Equipe/Medição com `extra='forbid'`, `quantidade` inteira `1..32767`, medição `quantidade ≥ 0`, textos aparados e não vazios (unidade segue livre, DEC-29).
- **DEC-prop-D:** `PUT` passa a `PATCH` parcial (campo omitido preserva) ou exige `observacoes`.
- **DEC-prop-E:** completar CRUD de campo (GET visita, PUT/DELETE de mão de obra e medição) para o auxiliar corrigir erros.

## Arquivos

- `04_backend/tests/test_visitas_lacunas.py` (novo; fixtures próprias porque `test_visitas.py` define as dele no módulo e `conftest.py` só tem `db_session`).
- Este doc.
