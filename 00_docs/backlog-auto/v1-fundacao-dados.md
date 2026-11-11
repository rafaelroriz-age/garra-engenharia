# V1-01 · Fundação de dados da emissão (T57)

Tipo de serviço normalizado, conteúdo narrativo do relatório e campos de assinatura do responsável. Papel: Engenheiro Backend. Data: 2026-11-11. Branch: `worktree-backlog-T57`.

> **Nota de ambiente:** o worktree nasceu de uma base antiga (`14ead2f`, de 2026-10-28), em que a T57 nem existia. Como a branch não tinha commits próprios e `14ead2f` é ancestral de `main`, fiz `git merge --ff-only main` (até `7aad1d5`) antes de começar. Nada foi reescrito.

## O que mudou

| Arquivo | Mudança |
|---|---|
| `04_backend/app/models/tipo_servico.py` (novo) | `TipoServico(StrEnum)`: RFO, LTIP, RFIP, VISTORIA_CAUTELAR, VISTORIA_RESIDENCIAL. `_missing_` aceita minúsculas e espaços (`" ltip "` → `LTIP`); `TipoServico.normalizar(texto)` devolve `None` para valor desconhecido. |
| `04_backend/app/schemas/contrato.py`, `schemas/inspecao.py` | `tipo_servico`/`tipo` passam a ser `TipoServico` na entrada (`use_enum_values=True`: o modelo grava o texto já em maiúsculas, então `contrato_repository.py:74` continua copiando um `str`). Na leitura (`ContratoRead`, `InspecaoRead`) o campo é `TipoServico \| str`, ver "Decisões propostas" (1). |
| `04_backend/app/services/visita_service.py` | `TIPO_INSPECAO_COM_VISITAS = TipoServico.RFO`; comparação via `TipoServico.normalizar(inspecao.tipo)`. |
| `04_backend/app/services/report_generator/rfo_contexto.py` | `TIPO_RFO = TipoServico.RFO.value`; a checagem 409 `inspecao-nao-rfo` usa `TipoServico.normalizar` (passa a aceitar `'rfo'` legado). |
| `04_backend/alembic/versions/a9c3e5f7b1d2_conteudo_relatorio_tipo_servico_v1_01.py` (novo) | `down_revision = e5a1c7d9b3f4`. `UPDATE ... upper(btrim(...))` em `contratos.tipo_servico` e `inspecoes.tipo`; cria `relatorio_conteudos`; adiciona `titulo_profissional`, `qualificacoes` (JSONB) e `assinatura_storage_key` em `responsaveis`. `downgrade()` remove tabela e colunas e **não** desfaz o upper(). |
| `04_backend/app/models/relatorio_conteudo.py` (novo) | `RelatorioConteudo`: `id` uuid, `inspecao_id` FK `inspecoes` (ON DELETE CASCADE), `tipo` String, `dados` JSONB NOT NULL default `'{}'`, `atualizado_por_id` FK `usuarios` nullable (ON DELETE SET NULL), `atualizado_em` timestamptz default now(); `UNIQUE(inspecao_id, tipo)` = `uq_relatorio_conteudos_inspecao_tipo`. |
| `04_backend/app/models/responsavel.py`, `schemas/responsavel.py` | 3 colunas novas; expostas em `ResponsavelBase` (create/read) e no novo `ResponsavelUpdate` (parcial). Tetos: título ≤ 120, até 20 qualificações de ≤ 300, storage key ≤ 512. |
| `04_backend/app/schemas/relatorio_conteudo.py` (novo) | `ConteudoDados` (contrato de `dados`, `extra="forbid"`), `RelatorioConteudoUpdate`, `RelatorioConteudoRead`. |
| `04_backend/app/services/relatorio_conteudo_service.py` (novo) | `textos_padrao(tipo)`, `chaves_texto(tipo)`, `deep_merge`, `preencher_placeholders`, `obter(db, inspecao_id, tipo)`, `salvar(db, inspecao_id, tipo, dados, usuario_id=)` (upsert `INSERT ... ON CONFLICT DO UPDATE`). |
| `04_backend/app/api/v1/conteudos.py` (novo) + `app/main.py` | `GET` e `PUT /api/v1/inspecoes/{id}/conteudo/{tipo}`; router incluído em `main.py`. |
| `04_backend/app/services/report_generator/textos_padrao/{ltip,vistoria_cautelar,vistoria_residencial}.json` (novos) | Textos padrão com as chaves exatas dos pipelines (ver abaixo). |
| `04_backend/tests/test_relatorio_conteudo.py` (novo) | 23 testes (9 de unidade + 14 de API com banco). |
| `04_backend/tests/test_contratos.py`, `tests/test_rbac_auxiliar.py` | O payload de `POST /contratos` usava `"tipo_servico": "Fiscalização de obra"`, que o enum agora recusa (422); trocado por `"RFO"`. |

O frontend (`03_frontend/lib/types.ts:66`) já usa os mesmos 5 valores em maiúsculas; não precisou de mudança.

## API

`GET /api/v1/inspecoes/{inspecao_id}/conteudo/{tipo}`: `auditor` e `auxiliar` (`require_equipe`). `tipo` aceita minúsculas; tipo desconhecido → 422; inspeção inexistente → 404; sem token → 401.

`PUT /api/v1/inspecoes/{inspecao_id}/conteudo/{tipo}`: só `auditor` (`require_auditor`; auxiliar → 403). Corpo `{"dados": {...}}`. **Substitui** o conteúdo salvo daquele (inspeção, tipo); o que não vier volta ao padrão na leitura. Inválido ou acima do teto → 422 e nada é gravado.

Resposta dos dois:

```json
{
  "inspecao_id": "uuid",
  "tipo": "LTIP",
  "dados": { "textos": { "introducao": ["..."], "...": [] }, "data_emissao": "2026-11-10", "...": "..." },
  "salvo": true,
  "atualizado_em": "2026-11-11T22:00:00Z",
  "atualizado_por_id": "uuid"
}
```

`dados` na resposta = `deep_merge({"textos": padrões do tipo com placeholders preenchidos}, dados salvos)`. No deep merge, dicionários se mesclam recursivamente; qualquer outro valor salvo (lista, inclusive `[]`, texto, número) substitui o padrão. Para "apagar" uma seção padrão, salve `textos.<chave> = []`.

O conteúdo é independente por tipo: a mesma inspeção pode ter conteúdo LTIP e RFIP, por exemplo. O serviço **não** exige `tipo == inspecao.tipo` (ver "Decisões propostas" (3)).

## Contrato final de `dados` (para as tarefas seguintes)

Todos os campos são opcionais. Chave fora desta lista → 422 (`extra="forbid"`).

| Campo | Tipo (JSON) | Teto | Uso por relatório |
|---|---|---|---|
| `textos` | objeto `chave → lista de parágrafos` ou `chave → texto livre` (um parágrafo por linha; normalizado para lista ao salvar) | ≤ 100 chaves; ≤ 200 parágrafos por chave; ≤ 20 000 caracteres por parágrafo; chave `^[a-z][a-z0-9_]{0,79}$` **e** pertencente ao tipo (senão 422 `conteudo-chave-texto-invalida`) | LTIP, Cautelar, Residencial (RFO/RFIP não têm chaves de texto) |
| `data_emissao` | data ISO `AAAA-MM-DD` | — | todos (data da emissão/assinatura) |
| `local_emissao` | texto | ≤ 200 | todos ("Aparecida de Goiânia", "Goiânia-GO") |
| `parecer` | texto | ≤ 20 000 | Cautelar: complemento do título 10.1 (`complementos.parecer_tecnico`) |
| `unidade` | texto | ≤ 200 | Residencial ("Apartamento 1404") |
| `datas_vistorias` | lista de datas ISO | ≤ 60 | Cautelar (`conteudo.datas_das_vistorias`), Residencial (`textos.s5_2`) |
| `incluir_resumo` | booleano | — | RFIP (`ctx["incluir_resumo"]`) |
| `metodologia_corretiva` | objeto `ocorrencia_id (uuid) → texto` | ≤ 1 000 entradas; texto ≤ 20 000 | Cautelar: coluna "Metodologia corretiva" do Plano de Correções (10.2) |
| `fundamentacao_tecnica` | objeto `sistema_id (uuid) → lista de parágrafos` | ≤ 1 000 entradas; ≤ 200 parágrafos de ≤ 20 000 | Cautelar (`sistemas[].fundamentacao_tecnica`), Residencial (análise por sistema) |

Teto total: o JSON serializado de `dados` (após validação) ≤ 500 000 caracteres (`DADOS_MAX_CARACTERES`). Constantes em `app/schemas/relatorio_conteudo.py`.

O banco guarda `dados` com `exclude_none` e datas/uuids como texto (`model_dump(mode="json")`).

### Chaves de `textos` por tipo

| Tipo | Chaves aceitas (= arquivo de padrão) | Para onde vão no pipeline |
|---|---|---|
| `LTIP` | `introducao`, `consideracoes_preliminares`, `objetivo`, `objeto`, `metodologia`, `documentacao_analisada`, `conclusao` | chaves de topo do contexto (`ltip_pipeline.SECOES_TEXTO`; o pipeline gera `<chave>_paragrafos`) |
| `VISTORIA_CAUTELAR` | as 31 chaves de `conteudo.get('...')` do `templates/vistoria_cautelar/vistoria_cautelar_template.html.j2` (= `estrutura.secoes[*].chave`/`subsecoes[*].chave` do `layout.json`) | `ctx["conteudo"]` |
| `VISTORIA_RESIDENCIAL` | `vistoria_residencial_pipeline.TEXTOS_CHAVES`: `s1`, `s1_1`, `s2`, `s2_1`, `s2_2`, `s3`, `s3_1`, `s3_2`, `s4`, `s4_1`, `s4_2`, `s4_2_1`, `s4_2_2`, `s4_2_3`, `s4_2_4`, `s4_2_4_1`, `s4_2_4_2`, `s5`, `s5_1`, `s5_2`, `s6`, `s6_1`, `s6_2`, `s6_3`, `s7`, `s7_1`, `s8`, `s9`, `s10`, `s11`, `s12` | `c["textos"]` |
| `RFO`, `RFIP` | nenhuma | — |

Observação: a tarefa listava 6 chaves para o LTIP; o pipeline espera 7 (`objeto` também está em `SECOES_TEXTO`, `ltip_pipeline.py:54`), então o JSON tem as 7.

Chaves das três listas que ficaram com padrão `[]` por dependerem de dado da obra (preenchidas pela tarefa que monta o contexto ou pelo auditor): Cautelar `introducao`, `consideracoes_preliminares`, `objetivo`, `objeto`, `identificacao`, `da_realizacao_da_inspecao`, `apresentacao_do_responsavel_tecnico`, `datas_das_vistorias`, `metodologia`, `ensaios_tecnicos_instrumentais_realizados`, `desenvolvimento_das_atividades_da_inspecao` (os títulos-pai do original não têm texto próprio); Residencial `s1`, `s2`, `s3`, `s4`, `s4_2`, `s4_2_1`, `s4_2_2`, `s4_2_4`, `s4_2_4_1`, `s4_2_4_2`, `s5`, `s5_1`, `s5_2`, `s6`, `s7`.

### Placeholders nos textos padrão

`{edificacao_nome}` e `{edificacao_endereco}` (de `inspecao.contrato.edificacao`). O serviço os troca só nos **padrões**, antes do merge; valor ausente vira `—` (DEC-33). Qualquer outro `{...}` fica intacto.

### Origem dos textos padrão

Extraídos de `00_docs/convertidos/` (Laudo_Tecnico_de_Inspecao_Predial_2026_-_Cond_Cortina_DAmpezzo.md, Laudo_Tecnico_de_Vistoria_Cautelar_de_Recebimento_-_Reforma_New_York_-_V01.md, Laudo_Tecnico_de_Vistoria_de_Imovel_Residencial_-_Ap_1404.md), com nome de cliente, síndico, construtora, arquiteta, endereço, número de unidade, datas e quantidades de fotos substituídos por texto genérico ou pelos placeholders. Um teste (`test_textos_padrao_sem_dados_do_cliente_original`) garante que "Cortina", "New York", "Urbânica", "Opus Gyro", "1404", "Roniel" e "Natália Borges" não aparecem. As referências bibliográficas da Cautelar e da Residencial são as do original (sem as referências ao contrato e ao projeto do cliente). `01_output-context/` não foi tocado.

## Testes e comandos

Ambiente: PostgreSQL e MinIO de `05_infra` no ar (`garra-postgres` em localhost:5433). Docker em `C:\Program Files\Docker\Docker\resources\bin`.

### Migration (banco descartável `garra_tmp_v101`, criado com `createdb` no `garra-postgres`; banco de dev não foi tocado)

A partir de `04_backend`, com `POSTGRES_PORT=5433 POSTGRES_DB=garra_tmp_v101`:

```
alembic heads            → a9c3e5f7b1d2 (head)        # único head
alembic upgrade head     → ... e5a1c7d9b3f4 -> a9c3e5f7b1d2
alembic downgrade -1     → a9c3e5f7b1d2 -> e5a1c7d9b3f4 ; current = e5a1c7d9b3f4 (mergepoint)
alembic upgrade head     → current = a9c3e5f7b1d2 (head)
alembic check            → No new upgrade operations detected.
```

Normalização conferida com dado: após `downgrade -1`, inseri um contrato com `tipo_servico = ' ltip '` e uma inspeção com `tipo = 'vistoria_cautelar'`; depois do `upgrade head` o banco tinha `[LTIP]` e `VISTORIA_CAUTELAR`, e as 3 colunas novas em `responsaveis`.

Leitura do banco de dev (sem alterar): `alembic_version = f7c2a9d4e6b1` (atrás do head atual) e valores `RFO`, `LTIP` e `Fiscalização de obra` (estes vindos de testes antigos).

### pytest

O Python do sistema (3.14, anaconda) tem `bcrypt` incompatível com `passlib` (ValueError no self-test) e o venv `04_backend/.venv` do checkout principal está com `greenlet` quebrado; além disso o WeasyPrint precisa de GTK, ausente no Windows (`OSError: cannot load library 'libgobject-2.0-0'` ao coletar `test_rfo_contexto.py`). Por isso:

- `test_relatorio_conteudo.py` rodou num venv descartável (`uv venv --python 3.12` em `$CLAUDE_JOB_DIR/tmp`, `requirements.txt` do backend) contra `garra_tmp_v101`: **23 passed** (209 s).
- Os três arquivos pedidos rodaram num container descartável da imagem `05_infra-backend` (rede `garra-net`, worktree montado em `/work`, `POSTGRES_HOST=garra-postgres POSTGRES_DB=garra_tmp_v101`; a imagem tem pytest-asyncio incompatível com o `pytest.ini`, então o container instalou `pytest==9.0.1 pytest-asyncio==1.3.0` antes):

```
python -m pytest tests/test_relatorio_conteudo.py tests/test_relatorios_rfo_api.py tests/test_rfo_contexto.py -q
→ 34 passed, 7 warnings, 9 errors
  tests/test_relatorio_conteudo.py : 23 passed
  tests/test_rfo_contexto.py       : 7 passed
  tests/test_relatorios_rfo_api.py : 4 passed, 9 errors
```

**Os 9 errors de `test_relatorios_rfo_api.py` são da fixture `cenario`, anterior a esta tarefa, e não de código desta tarefa:** ela cria duas `Inspecao` (RFO e LTIP) com o mesmo `contrato_id`, e `inspecoes.contrato_id` é `unique=True` desde o schema inicial (`app/models/inspecao.py`): `UniqueViolationError: duplicate key value violates unique constraint "inspecoes_contrato_id_key"`. O arquivo não foi alterado aqui (último commit: `f26cff4`). Correção proposta (fora do escopo da T57): criar um segundo contrato para a inspeção LTIP na fixture.

Testes afetados pelo enum, no mesmo container (`MINIO_HOST=garra-minio` para o upload de foto):

```
tests/test_contratos.py        : 6 passed
tests/test_rbac_auxiliar.py    : 9 passed, 1 skipped
tests/test_visitas.py          : 6 passed
tests/test_visitas_lacunas.py  : 28 passed, 1 xfailed
tests/test_responsaveis.py     : 4 passed
tests/test_models.py           : 6 passed
```

(A primeira rodada de `test_rbac_auxiliar.py` sem `MINIO_HOST` deu 1 failed + 1 error por `Connection refused` em `localhost:9000` dentro do container, só ambiente.)

A suíte completa (`pytest` sem argumentos) **não** foi rodada.

### ruff (0.17.4, `ruff.toml` do backend)

- Arquivos tocados por esta tarefa: `All checks passed!`
- `ruff check .`: 10 erros, todos em arquivos não tocados e anteriores a esta tarefa: `alembic/versions/e5a1f0c2b7d4_relatorios_unicidade_versao_dec_48.py` (UP035, I001, 3× UP007), `tests/test_fotos_storage_key_unico.py` (3× F811), `tests/test_portal_versoes_relatorio.py` (I001), `tests/test_relatorio_unicidade.py` (I001).

## Decisões propostas (para o fechamento de lote; não registradas em `00_docs/projeto/decisoes.md`)

1. **Leitura tolerante do tipo.** Entrada estrita (enum), mas `ContratoRead.tipo_servico` e `InspecaoRead.tipo` aceitam `TipoServico | str`. Motivo: depois do `upper()` o banco ainda pode ter valores fora do enum (no dev: `FISCALIZAÇÃO DE OBRA`); com leitura estrita, `GET /contratos` e `GET /inspecoes/{id}` dariam 500. Proposta: uma migration de dados futura mapeando `FISCALIZAÇÃO DE OBRA` (e similares) → `RFO` com aval do cliente, e então tornar a leitura estrita. A tarefa pediu só `upper()`, então não mapeei nada.
2. **PUT substitui (não é PATCH).** O cliente manda o `dados` completo que quer manter. Combinado com o merge na leitura, campo ausente = padrão.
3. **Conteúdo por (inspeção, tipo de relatório), sem amarrar ao `inspecao.tipo`.** Uma inspeção LTIP também emite RFIP (relatório fotográfico); por isso qualquer dos 5 tipos é aceito em qualquer inspeção.
4. **Placeholders só nos padrões.** Texto salvo pelo auditor é devolvido como foi gravado.
5. **`ResponsavelUpdate` sem rota.** O schema existe (pedido da tarefa), mas `app/api/v1/responsaveis.py` ainda não tem `PUT/PATCH`. A tarefa de assinatura/upload deve criar a rota (só `auditor`) e validar `assinatura_storage_key` contra o storage.

## Para o fechamento de lote (00_docs)

- `00_docs/arquitetura.md` (modelo de dados e contratos de API): incluir `relatorio_conteudos`, as 3 colunas de `responsaveis`, o enum `TipoServico` e as rotas `/inspecoes/{id}/conteudo/{tipo}`.
- `00_docs/projeto/decisoes.md`: avaliar as propostas 1 a 5 acima.
- `00_docs/projeto/riscos.md`: valores legados fora do enum (proposta 1) e a fixture quebrada de `test_relatorios_rfo_api.py`.
- Ambiente de testes no Windows: o venv `04_backend/.venv` está com `greenlet` quebrado e a imagem `05_infra-backend` tem pytest-asyncio incompatível com o `pytest.ini`.
