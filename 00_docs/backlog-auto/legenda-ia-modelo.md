# Modelo de dados para legendas assistidas por IA (BL-36)

- **Tarefa:** T22, persistência do fluxo de legendas por IA (RF-15, RN-16, RN-17; ADR-12; DEC-21; DEC-37 proposta). Implementa as lacunas da T14 ([modelagem-legendas-ia-lacunas.md](modelagem-legendas-ia-lacunas.md)) que não dependem do provedor de LLM.
- **Escopo:** migration, modelos SQLAlchemy, schemas Pydantic v2, testes e ajuste documental do ER (L20). **Sem** adapter `LegendaIAClient`, sem chamada a LLM, sem endpoint `/legenda-ia/gerar`, sem frontend, sem mudança de lógica em `app/api/v1/fotos.py`.
- **Branch:** `worktree-backlog-T22` (sem push). Commit: `feat(backend): modelo de dados para legendas assistidas por IA (BL-36)`, `Refs DEC-37`.
- **Variáveis de ambiente novas:** nenhuma.
- **Documentos de gestão não editados:** `decisoes.md`, `backlog-tarefas.md`, `backlog-kanban.md`, `status.md`, `riscos.md`, `BACKLOG.md`.

---

## 1. Pré-requisito de ordem

| Verificação | Resultado |
|---|---|
| `git log --oneline -15` (início) | a branch estava em `14ead2f` (`backlog: disparo de D03`), **anterior** às correções de Fotos (T19, `0cfa859`, BL-11) e de Visitas (T21, `1867a37`, BL-10), que já estavam em `main` |
| `git merge-base main HEAD` | `14ead2f` (a branch era ancestral de `main`) |
| Ação | `git merge --ff-only main` → `6538a18` (`backlog: disparo de T22`). Fast-forward, sem commit de merge |
| `alembic heads` (depois do fast-forward) | `e5a1c3f7b9d2 (head)`: **uma única head** (Visitas, BL-10) |
| `down_revision` da migration nova | `e5a1c3f7b9d2` |

---

## 2. As 22 lacunas da T14

Marca: **[I]** independe do provedor, **[P]** depende do provedor (B-04).

| # | Marca | Lacuna | Situação | Onde / por quê |
|---|---|---|---|---|
| L1 | I | Texto bruto do auditor | **Feita** | `fotos.legenda_bruta` TEXT |
| L2 | I | Sugestão da IA separada de `legenda` | **Feita** | `fotos.legenda_ia_sugerida` TEXT (minuta); `fotos.legenda` segue sendo a legenda final |
| L3 | I | Nível de certeza (4 níveis) | **Feita** | `fotos.nivel_certeza_ia` VARCHAR(30) + `ck_fotos_nivel_certeza_ia` |
| L4 | I | Status `rascunho`/`aprovada` | **Feita** | `fotos.status_validacao_ia` VARCHAR(20) + `ck_fotos_status_validacao_ia`; NULL = sem sugestão (DEC-37 DP-1) |
| L5 | I | Pendências e alertas | **Feita** | `fotos.alertas_ia`, `fotos.pendencias_ia` JSONB |
| L6 | I | Tabela `prompts_ia` | **Feita** | `app/models/prompt_ia.py`; `nome`, `versao`, `conteudo`, `ativo`, `created_at`, `criado_por_id` |
| L7 | I | FK `fotos.prompt_ia_id` | **Feita** | FK `prompts_ia.id` ON DELETE RESTRICT, índice `ix_fotos_prompt_ia_id` |
| L8 | I | `aprovado_por_id`, `aprovado_em` | **Feita** | FK `usuarios.id` + timestamptz; `ck_fotos_aprovada_exige_aprovador` |
| L9 | I | Quem editou | **Feita por modelagem** | DP-3: na v1.0 quem edita é quem aprova (`aprovado_por_id`); a sugestão original fica em `legenda_ia_sugerida`, então "sugerido × final" é reconstruível. Sem coluna própria |
| L10 | I | Snapshot do prompt usado | **Feita (coluna)** | `fotos.prompt_conteudo_hash` VARCHAR(64), SHA-256 hex (`ck_fotos_prompt_conteudo_hash`). A imutabilidade das versões de `prompts_ia` **não** é imposta no banco (sem trigger); fica no serviço (BL-37) |
| L11 | I | Data/hora da geração | **Feita** | `fotos.legenda_ia_gerada_em` timestamptz |
| L12 | P | Provedor e modelo | **Pendente** | depende de B-04; fora do escopo por instrução da tarefa |
| L13 | P | Retenção/privacidade dos dados enviados | **Pendente** | decisão do cliente/B-04 (R-10) |
| L14 | I | Bloquear no relatório legenda IA não aprovada | **Pendente** | é regra do pipeline de relatório (BL-38), não persistência. O dado para o filtro já existe (`status_validacao_ia`) |
| L15 | I | `PUT /fotos/{id}` não registra autoria/aprovação | **Pendente** | `_usuario` continua descartado (`app/api/v1/fotos.py:116`); aprovação é lógica de BL-34/BL-38 e a tarefa proíbe alterar a lógica do endpoint |
| L16 | I | Não dá para limpar `legenda` | **Já resolvida antes desta tarefa** | T19 (DEC-39 C): `foto_repository.update` aplica só as chaves enviadas e `legenda: null` limpa (`app/repositories/foto_repository.py:48-52`) |
| L17 | I | Sugestão nunca sobrescreve `legenda` | **Feita (estrutura)** | resolvida por L2: campos distintos. A regra de escrita (DP-4) será imposta no serviço de geração (BL-34) |
| L18 | I | `origem` livre | **Sem ação** | só registro. Observação: a T19 já fechou o domínio no schema (`OrigemFoto`, DEC-39 C) |
| L19 | I | Uma versão ativa por nome | **Feita** | índice único parcial `uq_prompts_ia_nome_ativo ON prompts_ia (nome) WHERE ativo` + `uq_prompts_ia_nome_versao` |
| L20 | I | Rótulo `PROMPT_IA → FOTO` no ER | **Feita** | `arquitetura.md` §3: rótulo "versão usada na geração (opcional)" (DP-8), marcas "planejado" removidas dos campos implementados, nota da §3 e tabela de estado (§0) atualizadas; `dicionario-de-dados.md` com as colunas e a tabela novas |
| L21 | I | Schemas não expõem status/sugestão/aprovação | **Parcial** | `FotoRead` herda `LegendaIARead` (todos os campos, só leitura). `FotoUpdatePayload` **não** ganhou campos de aprovação: aceitá-los sem lógica no `PUT` seria aceitar e ignorar; entra com BL-34 |
| L22 | P | `POST /fotos/{id}/legenda-ia/gerar` | **Pendente** | depende do adapter/provedor (BL-34) |

**Resumo.** Das 19 lacunas independentes do provedor: 14 feitas aqui (L1–L11, L17, L19, L20), 1 parcial (L21), 1 já resolvida pela T19 (L16), 1 sem ação (L18) e 2 pendentes por serem lógica de serviço ou relatório, não persistência (L14, L15). As 3 que dependem do provedor (L12, L13, L22) continuam pendentes. Obs.: a seção 2 da T14 diz "20 lacunas independem", mas a própria lista (L1–L11, L14–L21) soma 19.

---

## 3. Escolhas onde o doc/DEC-37 não fixava o detalhe (opção mais simples)

1. **Auditoria de `prompts_ia`:** `created_at` (ADR-12) + `criado_por_id` FK `usuarios` anulável (mesmo padrão de RN-18). Sem `updated_at`, porque as versões são imutáveis (DP-2).
2. **Nomes não fixados pelo DEC-37:** `prompt_conteudo_hash` (citado em DP-2) e `legenda_ia_gerada_em` (L11). Tamanhos: `nome` 100, `versao` 50, `nivel_certeza_ia` 30, `status_validacao_ia` 20.
3. **Domínios por CHECK + VARCHAR**, não `ENUM` nativo do PostgreSQL (mais simples de evoluir e de reverter no `downgrade()`).
4. **CHECKs de coerência** (mais estritos que o DEC-37, compatíveis com ele): `status_validacao_ia` não nulo exige `legenda_ia_sugerida`; `aprovada` exige `aprovado_por_id` **e** `aprovado_em`.
5. **FK do prompt com `ON DELETE RESTRICT`:** uma versão usada por alguma foto não pode ser apagada (RN-17).
6. **`alertas_ia`/`pendencias_ia`:** JSONB anulável; no schema, `list[str] | None`, como no esboço da T14 §3. Se o JSON do prompt do cliente trouxer objetos, BL-34 troca o tipo do schema (o banco já aceita).
7. **Dados existentes:** todas as colunas novas são anuláveis e sem default; nenhuma linha é reescrita. Fotos antigas ficam com `status_validacao_ia = NULL` ("sem sugestão").
8. **Schemas:** os campos de IA ficam em `LegendaIARead` (só leitura) e `FotoRead` herda dele. `PromptIACreate` (`ativo` default `false`) e `PromptIARead`; não há schema de update de prompt (versão imutável).

### Proposta para o integrador (não registrada em `decisoes.md`)

- **DP-9 (proposta):** em BL-38 (L14), a regra "só `aprovada` entra no relatório" vale para a **legenda de origem IA**. Foto com `status_validacao_ia = NULL` (legenda manual ou legada) continua entrando com `legenda`, como hoje. Foto em `rascunho` entra com `legenda` (o texto manual, se houver), nunca com `legenda_ia_sugerida`.

---

## 4. DDL resultante

Gerado com `alembic upgrade e5a1c3f7b9d2:f7c2a9d4e6b1 --sql` (revisão `f7c2a9d4e6b1`, arquivo `04_backend/alembic/versions/f7c2a9d4e6b1_legendas_ia_prompts_ia_bl_36.py`):

```sql
CREATE TABLE prompts_ia (
    id UUID NOT NULL,
    nome VARCHAR(100) NOT NULL,
    versao VARCHAR(50) NOT NULL,
    conteudo TEXT NOT NULL,
    ativo BOOLEAN DEFAULT false NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    criado_por_id UUID,
    CONSTRAINT pk_prompts_ia PRIMARY KEY (id),
    CONSTRAINT fk_prompts_ia_criado_por_id_usuarios FOREIGN KEY(criado_por_id) REFERENCES usuarios (id),
    CONSTRAINT uq_prompts_ia_nome_versao UNIQUE (nome, versao)
);
CREATE UNIQUE INDEX uq_prompts_ia_nome_ativo ON prompts_ia (nome) WHERE ativo;
ALTER TABLE fotos ADD COLUMN legenda_bruta TEXT;
ALTER TABLE fotos ADD COLUMN legenda_ia_sugerida TEXT;
ALTER TABLE fotos ADD COLUMN nivel_certeza_ia VARCHAR(30);
ALTER TABLE fotos ADD COLUMN status_validacao_ia VARCHAR(20);
ALTER TABLE fotos ADD COLUMN alertas_ia JSONB;
ALTER TABLE fotos ADD COLUMN pendencias_ia JSONB;
ALTER TABLE fotos ADD COLUMN prompt_ia_id UUID;
ALTER TABLE fotos ADD COLUMN prompt_conteudo_hash VARCHAR(64);
ALTER TABLE fotos ADD COLUMN legenda_ia_gerada_em TIMESTAMP WITH TIME ZONE;
ALTER TABLE fotos ADD COLUMN aprovado_por_id UUID;
ALTER TABLE fotos ADD COLUMN aprovado_em TIMESTAMP WITH TIME ZONE;
ALTER TABLE fotos ADD CONSTRAINT fk_fotos_prompt_ia_id_prompts_ia FOREIGN KEY(prompt_ia_id) REFERENCES prompts_ia (id) ON DELETE RESTRICT;
ALTER TABLE fotos ADD CONSTRAINT fk_fotos_aprovado_por_id_usuarios FOREIGN KEY(aprovado_por_id) REFERENCES usuarios (id);
CREATE INDEX ix_fotos_prompt_ia_id ON fotos (prompt_ia_id);
ALTER TABLE fotos ADD CONSTRAINT ck_fotos_status_validacao_ia CHECK (status_validacao_ia IS NULL OR status_validacao_ia IN ('rascunho', 'aprovada'));
ALTER TABLE fotos ADD CONSTRAINT ck_fotos_nivel_certeza_ia CHECK (nivel_certeza_ia IS NULL OR nivel_certeza_ia IN ('constatacao_direta', 'indicio_tecnico', 'hipotese_tecnica', 'causa_comprovada'));
ALTER TABLE fotos ADD CONSTRAINT ck_fotos_status_ia_exige_sugestao CHECK (status_validacao_ia IS NULL OR legenda_ia_sugerida IS NOT NULL);
ALTER TABLE fotos ADD CONSTRAINT ck_fotos_aprovada_exige_aprovador CHECK (status_validacao_ia IS DISTINCT FROM 'aprovada' OR (aprovado_por_id IS NOT NULL AND aprovado_em IS NOT NULL));
ALTER TABLE fotos ADD CONSTRAINT ck_fotos_prompt_conteudo_hash CHECK (prompt_conteudo_hash IS NULL OR prompt_conteudo_hash ~ '^[0-9a-f]{64}$');
```

`downgrade()` remove, na ordem inversa, os 5 CHECKs, o índice, as 2 FKs, as 11 colunas de `fotos`, o índice parcial e a tabela `prompts_ia`.

---

## 5. Arquivos

| Arquivo | Mudança |
|---|---|
| `04_backend/alembic/versions/f7c2a9d4e6b1_legendas_ia_prompts_ia_bl_36.py` | nova migration (revisa `e5a1c3f7b9d2`) |
| `04_backend/app/models/prompt_ia.py` | novo modelo `PromptIA` |
| `04_backend/app/models/foto.py` | 11 colunas, 5 CHECKs, relação `prompt_ia`; constantes `STATUS_VALIDACAO_IA`, `NIVEIS_CERTEZA_IA` |
| `04_backend/app/models/__init__.py` | registra `PromptIA` |
| `04_backend/app/schemas/foto.py` | `StatusValidacaoIA`, `NivelCertezaIA`, `LegendaIARead`; `FotoRead` herda os campos de IA |
| `04_backend/app/schemas/prompt_ia.py` | novo: `PromptIABase`, `PromptIACreate`, `PromptIARead` |
| `04_backend/app/schemas/__init__.py` | exporta os schemas novos |
| `04_backend/tests/test_legenda_ia_modelo.py` | 24 testes novos (8 de schema sem banco, 16 contra o PostgreSQL) |
| `00_docs/arquitetura.md` | §0 (estado), nota da §3, ER `FOTO`/`PROMPT_IA` e rótulos das relações (L20) |
| `00_docs/dicionario-de-dados.md` | migration nova, colunas de `fotos`, tabela `prompts_ia`, seção "Previsto e não implementado" |

`app/api/v1/fotos.py`, os serviços e os repositórios **não** foram alterados. Os endpoints existentes passam a devolver os campos de IA (todos `null` para fotos sem sugestão) porque usam `response_model=FotoRead`.

---

## 6. Comandos e saídas

Ambiente: Windows, Python 3.12 do `.venv` do repositório, PostgreSQL de `05_infra/docker-compose.yml` em `localhost:5433` (porta aberta; `docker` não está no PATH desta sessão). Antes de aplicar, o banco estava em `d3b7c9e4f1a2`, com 1 visita, 0 fotos e nenhuma duplicata de `(inspecao_id, seq_numero)` ou `(inspecao_id, data)`, então a migration `e5a1c3f7b9d2` de `main` não alterou dados.

### 6.1 Migrations (em `04_backend/`)

```text
$ alembic upgrade head
Running upgrade d3b7c9e4f1a2 -> e5a1c3f7b9d2, visitas_unicidade_seq_e_data_bl_10
Running upgrade e5a1c3f7b9d2 -> f7c2a9d4e6b1, legendas_ia_prompts_ia_bl_36
$ alembic current            -> f7c2a9d4e6b1 (head)
$ alembic downgrade -1
Running downgrade f7c2a9d4e6b1 -> e5a1c3f7b9d2, legendas_ia_prompts_ia_bl_36
$ alembic current            -> e5a1c3f7b9d2
$ alembic upgrade head
Running upgrade e5a1c3f7b9d2 -> f7c2a9d4e6b1, legendas_ia_prompts_ia_bl_36
$ alembic current            -> f7c2a9d4e6b1 (head)
$ alembic check
No new upgrade operations detected.        # modelos e banco coincidem
```

No fim, o banco compartilhado foi deixado em `e5a1c3f7b9d2` (head de `main`), com `alembic downgrade e5a1c3f7b9d2`, para que os checkouts que ainda não têm esta revisão não encontrem uma revisão desconhecida. **Depois da integração, rodar `alembic upgrade head`.**

### 6.2 Testes pedidos

```text
$ pytest tests/test_legenda_ia_modelo.py tests/test_fotos.py
32 passed in 17.75s
```

- `test_fotos.py` precisa de MinIO. Este worktree não tem `04_backend/.env` (correto: não é versionado), e sem credenciais os 8 testes falham com `ClientError (403) HeadBucket` em `app/services/storage/s3_client.py:59`. Eles passaram com as variáveis `MINIO_*` exportadas do `.env` local do checkout principal só no processo do `pytest`. O arquivo não foi copiado, exibido nem commitado.
- Os testes de banco apagam o que criam. Conferido depois: `prompts_ia` 0 linhas, `fotos` 0 linhas, nenhum usuário `Aprovador BL-36`. Três usuários de teste deixados por uma execução intermediária, quando o teardown da fixture ainda tinha um defeito já corrigido, foram removidos por nome, e-mail de teste e ausência de referências.

### 6.3 `ruff check .` (em `04_backend/`)

Arquivos tocados: limpos (`ruff check` neles → `All checks passed!`). O projeto inteiro tem **9 erros anteriores**, todos em arquivos não tocados e vindos de `main`: `app/scripts/vistoria_cautelar_layout_extractor.py` (RUF001 ×2), `tests/test_ocorrencias_regras.py` (I001), `tests/test_vistoria_cautelar_pipeline.py` (RUF043 ×2), `tests/test_vistoria_cautelar_templates.py` (I001, RUF005 ×3).

### 6.4 Suíte completa (`pytest`), comparada com a baseline

Para separar o que é desta tarefa, a mesma suíte rodou sobre uma cópia de `HEAD:04_backend` sem as mudanças desta tarefa (`git archive`, numa pasta temporária fora do repositório) e sobre este worktree, contra o mesmo banco, ignorando os 5 módulos que não coletam (ver item 1 abaixo):

| Execução | Resultado |
|---|---|
| Baseline (sem BL-36) | 20 failed, 189 passed, 5 skipped, 19 errors |
| Com BL-36 | 34 failed, 205 passed, 5 skipped, 13 errors |

Diferença por ID de teste: as **únicas falhas novas são os 14 testes de banco de `test_legenda_ia_modelo.py`**, que passam isolados e junto com `test_fotos.py` (6.2). Os 6 erros a menos (`test_gabarito.py`) vêm de a baseline estar fora do repositório, sem acesso a `01_output-context/`. As demais falhas são **as mesmas nas duas execuções**, e todas são anteriores a esta tarefa:

1. **`openpyxl` ausente no `.venv`** (`requirements.txt:31` o declara): `test_ltip_templates.py`, `test_rfip_templates.py`, `test_rfo_templates.py`, `test_vistoria_cautelar_templates.py` e `test_vistoria_residencial_templates.py` não coletam (`ModuleNotFoundError`).
2. **`asyncio.run` derruba o event loop de sessão:** `tests/test_auth.py`, `test_contratos.py`, `test_edificacoes.py`, `test_fotos.py`, `test_fotos_lacunas.py`, `test_rbac_auxiliar.py` e `test_responsaveis.py` usam `from asyncio import run as run_async`, que faz `set_event_loop(None)` ao terminar. Todo teste async com banco que roda depois deles na ordem alfabética falha com `RuntimeError: There is no current event loop in thread 'MainThread'`: `test_models.py` (6), `test_visitas_lacunas.py` (8) e os 14 de `test_legenda_ia_modelo.py`. A T21 já corrigiu o mesmo problema só em `test_visitas.py:106-113` (loop próprio com `new_event_loop()`). **Proposta:** um helper único em `tests/conftest.py` com esse padrão, usado pelos 7 arquivos. Não foi feito aqui por estar fora do escopo.
3. **`test_ocorrencias_regras.py` (13 erros):** a fixture cria duas inspeções para o mesmo contrato e viola `inspecoes_contrato_id_key`.
4. **`test_ocorrencias_prioridade.py` (5 falhas):** `ValueError: not enough values to unpack (expected 2, got 1)` em `for k, v in headers` (`tests/test_ocorrencias_prioridade.py:120`).
5. **`test_edificacoes.py::test_listar_edificacoes_paginado`:** falha também na baseline.

### 6.5 Frontend

Não tocado; `npm run lint` e `npm run build` não se aplicam.

---

## 7. Pendências para as próximas tarefas

| Item | Tarefa | Observação |
|---|---|---|
| L12 colunas `provedor_ia`/`modelo_ia` | BL-34 (após B-04) | migration nova, anuláveis |
| L13 retenção/privacidade | decisão antes de BL-34 | R-10 |
| L22 `POST /fotos/{id}/legenda-ia/gerar`, adapter `LegendaIAClient`, `FakeLegendaIAClient` | BL-34 | esboço na T14 §3 |
| L15 `PUT /fotos/{id}` com usuário e aprovação; campos de aprovação em `FotoUpdatePayload` (L21) | BL-34 / BL-38 | `aprovado_por_id`/`aprovado_em` vêm do token (DP-3) |
| L14 filtro no relatório | BL-38 | ver DP-9 acima |
| Imutabilidade de `prompts_ia` e troca de versão ativa em transação | BL-37 | o índice parcial já impede duas ativas |
| Helper de event loop nos testes; `openpyxl` no `.venv` | manutenção | itens 6.4.1 e 6.4.2 |
