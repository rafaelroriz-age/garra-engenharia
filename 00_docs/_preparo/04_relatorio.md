# 04 — Relatório de verificação da documentação (tarefa D05)

> Preparo da documentação, Bloco 0 do `BACKLOG.md`. Verificação feita em 2026-11-04 sobre o commit `adab8aa` (`main`, que contém a D04 integrada). A branch `worktree-backlog-D05` partia de `14ead2f`, sem os documentos da D04; foi avançada por `git merge --ff-only main`.
> Regra: toda afirmação cita o arquivo ou o comando que a comprova. Onde não deu para saber, está escrito **não determinado**.

## 1. Resumo

- Os documentos criados ou refeitos na D04 foram conferidos contra o código e estão corretos depois de 5 ajustes pequenos (§3). Veredito: **efetiva**.
- **Não são todos efetiva.** Restam documentos **parcial** que a D04 não podia tocar (`Toca` da D04 = `00_docs`, `README.md`): os três READMEs de pasta, o `cronograma.md`, o `engenheiro-ia.agent.md` e 5 prompts de `.github/prompts/`. Não os reescrevi aqui porque o fechamento de lote do `BACKLOG.md` os atribui a outra etapa e `cronograma.md` exige decisão humana. Estão listados em §4 e §5.
- Os testes de backend (`pytest`) **não rodaram**: PostgreSQL (`localhost:5433`) e MinIO (`localhost:9000`) estavam fora do ar e o `docker` não está no PATH (§2).

## 2. O que foi executado

| Verificação | Comando ou método | Resultado |
|---|---|---|
| Links relativos e caminhos citados entre crases | script que lê os `.md` de `00_docs/`, `README.md` e READMEs de pasta (fora de `convertidos/`) | todos os links resolvem, salvo o de `estudo-do-contexto.md:242` (corrigido, §3). Os caminhos que não existem são ausências declaradas pelos próprios documentos (`03_frontend/.env.example`, `.env` ignorados pelo git, `app/workers/`, `app/services/ia_legenda/`, `04_backend/prompts/`, `strategies/`: "previsto") |
| Referências `arquivo:linha` (7 docs) | script: arquivo existe e tem a linha | nenhum estouro de intervalo; conferência de conteúdo em `ci.yml`, `docker-compose.yml`, `config.py`, `api-client.ts`, `seed_admin.py`, `helpers.ts` (1 desvio corrigido, §3) |
| Variáveis de `00_docs/configuracao.md` | comparação com `04_backend/app/core/config.py`, `seed_admin.py:56-58`, `03_frontend/e2e/helpers.ts:9,65-66`, `playwright.config.ts:22`, `05_infra/docker-compose.yml` (`BACKEND_PORT`, `FRONTEND_PORT`, `MINIO_CONSOLE_PORT`) | nomes e padrões batem |
| Colunas de `00_docs/dicionario-de-dados.md` | script importa `app.models` e compara `Base.metadata` com as tabelas do documento | as 17 tabelas existem; colunas das 12 seções por tabela batem; as 5 do gabarito (`sistemas_prediais`, `subsistemas`, `tipos_anomalia`, `tipos_falha`, `localizacoes`) estão numa seção única, correta |
| Migrations | `python -m alembic heads` em `04_backend/`; `ls 04_backend/alembic/versions` | head `d3b7c9e4f1a2`; 6 arquivos, como no guia |
| Contagem de testes | `ls 04_backend/tests \| grep -c "^test_"` | 19, como a D04 corrigiu |
| `backlog-auto` | `python -m backlog_auto --help` em `backlog-auto/` | CLI responde, com os subcomandos usados em `BACKLOG.md` (`list`, `next`, `run`, `auto`) |
| Frontend | `npm install`, `npm run lint`, `npm run build` em `03_frontend/` | os três passam; lint sem avisos; build lista as rotas, incluindo `/portal` e `/portal/documentos` |
| Lint do backend | `ruff check .` e `ruff check . --isolated` em `04_backend/` (ruff 0.15.1) | **214** erros e **46** com `--isolated` (38 `F821`, 7 `F401`, 1 `F541`). O CI não bloqueia nisso (`ci.yml:80-83`) |
| Testes do backend | `python -m pytest --collect-only -q` | **não rodou**: faltam dependências neste Python 3.14.6 (`ModuleNotFoundError: pytest_asyncio`), e a infraestrutura está fora do ar. Sem resultado de `pytest` |
| Infraestrutura | `Test-NetConnection` nas portas 5433 e 9000; `Get-Command docker` | portas fechadas; `docker` ausente. Os passos `docker compose` do guia **não foram executados** |

Observação de ambiente: esta máquina tem Python 3.14.6, Node v26.7.0, npm 11.19.0. O guia fixa Python 3.12 e Node 20 (`04_backend/Dockerfile`, `03_frontend/Dockerfile`, `ci.yml:69,100`); a tabela do guia cita as versões da D01 (Python 3.12.4) como "última execução registrada", o que continua verdadeiro como registro histórico.

## 3. O que foi corrigido nesta verificação

| Arquivo | Correção | Evidência |
|---|---|---|
| `00_docs/estudo-do-contexto.md` (linha 242) | link `../cliente/prompt-lado-cliente.md` apontava para fora de `00_docs/`; agora `./cliente/prompt-lado-cliente.md` | o arquivo é `00_docs/cliente/prompt-lado-cliente.md` |
| `00_docs/guia-desenvolvimento.md` | referência do `ruff` no CI: `ci.yml:77` → `ci.yml:82`; `ci.yml:81-83` → `ci.yml:80-83` | `ci.yml:82` é `run: ruff check .`, `:83` é `continue-on-error: true` |
| `00_docs/guia-desenvolvimento.md` | acrescentado o resultado do `ruff` desta verificação (46 com `--isolated`, 214 sem) e uma linha de registro da D05 com o que foi e o que não foi executado | §2 |
| `00_docs/README.md` | índice passa a listar `_preparo/04_relatorio.md` | seção "Preparo da documentação" |
| `00_docs/README.md`, `arquitetura.md`, `configuracao.md`, `dicionario-de-dados.md`, `guia-contribuicao.md`, `guia-desenvolvimento.md` | `status: draft` → `status: ativo` (valor já usado em outros 8 documentos de `00_docs/`) e linha "Status" do `ai-summary` atualizada; `last_updated` do índice e do guia = 2026-11-04 | `grep "^status:" 00_docs -r` |

Nada de código, testes ou dados foi alterado. `BACKLOG.md` e os documentos de gestão (`backlog-tarefas.md`, `backlog-kanban.md`, `status.md`, `decisoes.md`, `riscos.md`) também não.

## 4. Veredito final por documento

Critério: **efetiva** = caminhos, comandos, nomes e configurações conferidos contra o código nesta tarefa. A coluna "Base" diz o quanto foi conferido.

### 4.1 Documentos criados ou refeitos na D04 (conferidos a fundo)

| Documento | Veredito | Base |
|---|---|---|
| `README.md` (raiz) | **efetiva** | objetivo igual ao declarado pelo dono; "Estado atual" confere: `app/api/v1/` não tem rota de geração (só `portal.py` lista/baixa relatórios), `report_generator/rfo_pipeline.py` é o único renderizador; links resolvem |
| `00_docs/README.md` (índice) | **efetiva** | todo `.md` de `00_docs/` (fora de `convertidos/`) está indexado; links resolvem |
| `00_docs/guia-desenvolvimento.md` | **efetiva** (com a ressalva do `docker compose`: não executado) | portas, bucket, scripts de `app/scripts/`, `seed_admin`, `/health`, comandos `npm`, versões de Dockerfile e CI conferidos |
| `00_docs/configuracao.md` | **efetiva** | tabela confere com `Settings` e demais fontes (§2) |
| `00_docs/dicionario-de-dados.md` | **efetiva** | colunas e migrations conferidas (§2) |
| `00_docs/guia-contribuicao.md` | **efetiva** | links e caminhos conferidos; regras de `.github/pull_request_template.md` e `ci.yml` coerentes com o guia (pasta fora da raiz, branches) |
| `00_docs/arquitetura.md` | **efetiva** | caminhos do implementado existem; o que não existe está marcado "previsto" (`app/workers/`, `ia_legenda/`, `strategies/`, `04_backend/prompts/`); `templates/assets/logo-garra.jpg` aparece só como removido; `templates/assets/` contém os SVG/PNG/`marca.json` citados |
| `00_docs/projeto/plano-gestao-configuracao.md` | **efetiva** | links e caminhos resolvem; conteúdo reescrito pela D04 com base em `ci.yml` |
| `00_docs/projeto/resumo-executivo.md` | **efetiva** | links e caminhos resolvem |
| `00_docs/cliente/briefing-tecnico-para-ia.md` | **efetiva** | links e caminhos resolvem |
| `00_docs/cliente/solicitacao-templates-docx.md` | **efetiva** como registro histórico (`status: superado`, nota "não enviar") | links do checklist resolvem |
| `00_docs/_preparo/01_sistema.md`, `02_inventario.md`, `03_classificacao.md`, `04_relatorio.md` | **efetiva** (registros datados, não descrevem o estado corrente) | contagem de 19 `test_*.py` e demais números da D04 reconferidos |

### 4.2 Documentos que a D03 deu como efetiva e a D04 não tocou (conferência limitada)

Nesta tarefa só foram verificados links relativos e caminhos citados, não cada afirmação. Vereditos da D03 mantidos:

`00_docs/estudo-do-contexto.md` (um link corrigido), `analise-comparativa-contratos.md`, `contrato-prestacao-servicos-desenvolvimento.md`, `backlog-auto/BACKLOG-MANUAL.md`, `backlog-auto/CELULAR.md`, `cliente/apresentacao-comercial.md`, `cliente/prompt-lado-cliente.md`, `cliente/proposta-comercial.md`, `projeto/{ata-validacao-lacunas, backlog-kanban, backlog-tarefas, backlog-tarefas-humanas, ciclo-de-vida, decisoes, escopo, pauta-validacao-lacunas, relatorio-benchmark-geracao-pdf-docx, revisao-seguranca-owasp, riscos, status}.md`. Os de gestão (`backlog-*`, `status`, `decisoes`, `riscos`) são atualizados no fechamento de lote, não aqui. Os 94 itens **efetiva** da D03 incluem ainda os `.md` de `00_docs/convertidos/`, fora do escopo desta verificação (são conversões dos originais do cliente).

Os `.md` de `backlog-auto/` e de `00_docs/backlog-auto/` têm links com caminhos de modelo (`docs/BACKLOG-MANUAL.md`, `BACKLOG-MANUAL.md` em `backlog-auto/src/backlog_auto/templates/`); são modelos copiados para outros projetos, não links desta documentação.

### 4.3 Ainda **parcial** (não ficam efetiva nesta tarefa)

| Documento | Motivo (de `03_classificacao.md` §3 e §5.3) |
|---|---|
| `04_backend/README.md`, `03_frontend/README.md`, `05_infra/README.md` | fora do `Toca` da D04; seguem com as seções obsoletas apontadas na D03 (geração "depende de templates", "Status atual (BL-01)"). O `BACKLOG.md` manda atualizá-los no fechamento de lote |
| `00_docs/projeto/cronograma.md` | marcos M4-M7 vencidos; replanejar datas é decisão humana |
| `.github/agents/engenheiro-ia.agent.md` | usa `services/ai/`, `arquitetura.md` usa `services/ia_legenda/`; escolher o nome é decisão |
| `.github/prompts/{03,04,06,07,08}-*.prompt.md` | ainda mandam usar `src/`, contrariando a DEC-09 |

## 5. Pendências que exigem decisão humana

1. **Objetivo do sistema.** Foi usado o texto do dono (`README.md`, §Objetivo). Confiança alta: o código bate com ele, exceto a geração de PDF/DOCX pela interface, que **não existe** (sem rota na API; tela de relatório é placeholder). O `README.md` já declara isso; a decisão é só de prioridade.
2. **Lint do backend vermelho** (46 erros com `--isolated`, 38 deles `F821`), e o CI não bloqueia (`ci.yml:80-83`, comentário "BL-26"). Decidir se o `ruff` passa a bloquear; exige alterar código (fora do escopo de documentação).
3. **`pytest` sem resultado nesta verificação.** Rodar com PostgreSQL e MinIO no ar (guia §5) e registrar. Se os testes de tabela passam no Actions sem `alembic upgrade head` antes: **não determinado** (logs do Actions não consultados).
4. **`cd-staging.yml:83`** faz healthcheck em `/health/ready`, rota que não existe (`app/main.py:85` só tem `/health`). Corrigir o workflow ou criar a rota.
5. **Config do ruff fora do repositório** muda a contagem (214 contra 46). Decidir se o repositório passa a ter um `ruff.toml` próprio.
6. **Documentos parciais de §4.3.** Em especial o nome da pasta de IA (`ia_legenda/` ou `ai/`) e o replanejamento do `cronograma.md`.
7. **Passos com `docker compose`** do guia seguem sem execução de ponta a ponta (Docker ausente). Repetir em máquina com Docker antes de tratar o guia como validado nesse trecho.
8. **Amostras `01_output-context/_amostras_ht09/`** são citadas em `projeto/status.md` e `projeto/backlog-tarefas-humanas.md`, mas a pasta não existe neste checkout; não determinado se foi removida ou nunca versionada. Gestão: atualizar no fechamento de lote.
9. **Python 3.14 / Node 26 locais** diferem do que o CI e os Dockerfiles fixam (3.12 e 20); o venv local precisa de `pip install -r requirements.txt` para o `pytest` coletar.

## 6. Proposta de decisão (não aplicada em `decisoes.md`)

- Tornar `ruff check . --isolated` a forma oficial de reproduzir o CI e, quando o backlog de 46 erros zerar (BL-26), trocar `continue-on-error` por bloqueante.
