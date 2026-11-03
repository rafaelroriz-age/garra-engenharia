---
title: Classificação da documentação existente
type: knowledge
status: draft
owner: Garra Engenharia
related:
  - 00_docs/_preparo/01_sistema.md
  - 00_docs/_preparo/02_inventario.md
tags: [classificacao, documentacao, preparo]
last_updated: 2026-10-28
---

<!-- ai-summary
System: veredito (efetiva / parcial / refazer / ausente) de cada documento inventariado na D02, confrontado com o código do commit 14ead2f.
Flow: correções aos insumos D01/D02 → tabela de vereditos com evidência → lacunas (ausente) → plano de ação para a D04.
Owner: Garra Engenharia.
Status: draft — etapa D03; a execução do plano é a D04.
-->

# Classificação da documentação (tarefa D03)

> Bloco 0 do `BACKLOG.md`, etapa de preparo da documentação. Confronto feito em 2026-10-28 sobre o commit `14ead2f` (`main`), que é o primeiro a conter os dois insumos (`01_sistema.md` e `02_inventario.md`). A branch deste worktree foi avançada por fast-forward de `71ac8fd` para `14ead2f` (`git merge --ff-only main`), já que a base original não tinha esses arquivos.
> Regra deste documento: cada veredito cita o arquivo e o trecho que o sustentam. Onde não deu para verificar, está escrito **não determinado**.

**Vereditos:** **efetiva** = correta, atual e cobre o tema (não será tocada) · **parcial** = correta em parte (seções a corrigir indicadas) · **refazer** = obsoleta, contradiz o código ou é vaga demais · **ausente** = deveria existir e não existe.

---

## 1. Correções aos insumos D01 e D02

A D04 vai se basear em `01_sistema.md`. Os pontos abaixo estão desatualizados nele, porque a D01 analisou o commit `161ba19` (está escrito no cabeçalho do arquivo), e o commit `0b47e64` (2026-10-27, 40 arquivos) **não** é ancestral de `161ba19` (`git merge-base --is-ancestor 0b47e64 161ba19` → código 1).

| Afirmação em `01_sistema.md` | Situação no código atual (`14ead2f`) | Evidência |
|---|---|---|
| §1.2 e risco 9: "A regra RN-04 [...] **não é aplicada**" | **Superada.** A prioridade é derivada do Grau de Risco CMM e a sobrescrita é registrada | `04_backend/app/services/ocorrencia_service.py:12` ("RN-04 (DEC-29): mapeamento Grau de Risco CMM → Prioridade sugerida"), `:106-133` (`_prioridade_sugerida`, `_resolver_prioridade`); migration `alembic/versions/d3b7c9e4f1a2_prioridade_sugerida_sobrescrita_bl_15.py`; 5 testes em `tests/test_ocorrencias_prioridade.py` |
| §1.2: "gravados como vieram, sem cálculo do produto G×U×T" | Continua válido | `grep -rnE "gut_gravidade\s*\*\|gut_produto\|gut_total" 04_backend/app` → nenhum resultado |
| §3: "5 migrations" | São **6** | `ls 04_backend/alembic/versions` (inclui `d3b7c9e4f1a2_...bl_15.py`) |
| §3 e §5.2: "18 módulos pytest" / "93 + 21 testes" | São **20** módulos `test_*.py`; os novos são `test_brand_assets.py` (18 testes) e `test_ocorrencias_prioridade.py` (5) | `ls 04_backend/tests` e `grep -c "def test_"` |
| §3: `04_backend/templates/` = `rfo/`, `ltip/`, `contracts/` + 2 soltos | Existe também `templates/assets/` (`logo-garra.svg`, `logo-garra.png`, `logo-garra-negativa.svg`, `logo-garra-simbolo.svg`, `marca.json`) | `ls 04_backend/templates/assets` |
| §3: lista de `app/scripts/` | Faltam `bitmap_tracer.py` e `build_brand_assets.py` (DEC-30/ADR-16) | `ls 04_backend/app/scripts` |
| Risco 18: uso dos templates soltos "não determinado" | `templates/rfo_benchmark_template.docx` é escrito por `app/scripts/build_rfo_benchmark_docx_template.py:18`. `templates/rfo_template.html.j2` (na raiz de `templates/`) **não é referenciado** por nenhum `.py`: o pipeline usa `rfo/rfo_template.html.j2` | `rfo_pipeline.py:29-30`; `grep -rn "rfo_template.html.j2" 04_backend/app 04_backend/tests` |

| Afirmação em `02_inventario.md` | Situação atual | Evidência |
|---|---|---|
| Coluna "Último commit" | Desatualizada para 21 arquivos: `arquitetura.md`, `estudo-do-contexto.md`, `03_frontend/README.md`, `04_backend/README.md`, `briefing-tecnico-para-ia.md`, os templates `rfo/` e `ltip/` `.docx` e 14 arquivos de `00_docs/projeto/` foram tocados em **2026-10-27** (`0b47e64`); as datas corretas estão na tabela da §2 | `git log --name-only --format=@%cs -- <pastas>` |
| "`BACKLOG.md` [...] não existem" | `BACKLOG.md` existe na raiz (último commit 2026-10-28) e contém a "Regra de pronto" | `git ls-files BACKLOG.md`; `BACKLOG.md`, seção "Regra de pronto" |
| Escopo de 109 arquivos | Não inclui 7 arquivos rastreados: `BACKLOG.md`, `00_docs/backlog-auto/BACKLOG-MANUAL.md`, `00_docs/backlog-auto/CELULAR.md`, `backlog-auto/README.md`, `backlog-auto/docs/PROMPTS.md` e 3 templates em `backlog-auto/src/backlog_auto/templates/` | `git ls-files \| grep -iE '\.(md\|docx)$\|README'` |

---

## 2. Tabela de vereditos

Data = último commit que tocou o arquivo em `14ead2f`.

### 2.1 Documentação técnica do sistema (READMEs e arquitetura)

| Documento | Data | Veredito | Evidência |
|---|---|---|---|
| `04_backend/README.md` | 2026-10-27 | **parcial** | **Obsoleto:** (a) o parágrafo de abertura e "Pendências" dizem que a geração "ainda depende da entrega dos modelos originais do cliente", mas a própria seção "Templates de relatório derivados do original do cliente (BL-12/BL-13)" e o ADR-13 (`00_docs/arquitetura.md` §8) removeram essa dependência; (b) "RBAC básico para auditor/cliente" omite o perfil `auxiliar` (`app/api/deps.py`, `require_equipe`; `tests/test_rbac_auxiliar.py`); (c) a árvore "Estrutura atual" lista 3 migrations (são 6), 5 arquivos de teste (são 20) e não mostra `repositories/`, `services/report_generator/`, `templates/rfo|ltip|contracts/`, `Dockerfile.render`; (d) a tabela de `/auth/register` diz "sem cadastro público", mas o código libera o registro sem autenticação enquanto não há usuários (`app/api/v1/auth.py:38-39`, bootstrap da DEC-24). **Inconsistente:** "Como rodar localmente" manda `cp .env.example .env` sem avisar que `.env.example` tem `POSTGRES_PORT=5432`, enquanto o compose publica `5433` (`05_infra/docker-compose.yml:54`); o aviso só aparece na seção BL-04. "Como rodar localmente" não inclui `alembic upgrade head` nem `seed_gabarito`. **Formatação quebrada:** título "Storage service MinIO/S3 (BL-07)" sem `##` e um `## ` vazio antes de "Como rodar os testes". **Faltante:** `RUN_MIGRATIONS_ON_STARTUP` (`app/core/config.py:25`), `seed_admin` (`app/scripts/seed_admin.py`), `ruff` fora de `requirements.txt` (`.github/workflows/ci.yml:77`). **Correto e a preservar:** seções BL-05, BL-12/BL-13, DEC-30, BL-06 (exceto a frase do registro) e BL-07 batem com `app/scripts/`, `templates/` e `app/services/storage/` |
| `03_frontend/README.md` | 2026-10-27 | **parcial** | **Obsoleto:** a abertura diz que a geração "depende [...] do recebimento de templates originais do cliente" (contradiz o parágrafo seguinte do mesmo arquivo e o ADR-13); em "O que cada teste cobre", "RF-06 segue bloqueado por B-02", mas B-02 foi encerrado (`00_docs/projeto/status.md:100`, DEC-30). **Faltante:** a árvore não mostra `lib/` (`api-client.ts`, `use-usuario-atual.ts`) nem os componentes `foto-upload.tsx`, `photo-annotation-editor.tsx`, `ocorrencia-form-dialog.tsx`, `api-error-alert.tsx`, `pagination-bar.tsx` e `brand/garra-mark.tsx` (`ls 03_frontend/components`); não documenta a variável `NEXT_PUBLIC_API_URL` (`lib/api-client.ts:14`) e não há `03_frontend/.env.example` (`ls -a 03_frontend`); `playwright.config.ts:10` cita `03_frontend/e2e/README.md`, que não existe (`ls 03_frontend/e2e`). **Correto e a preservar:** comandos `npm` (batem com `package.json` `scripts`), rotas de `app/` (batem com `find 03_frontend/app -name page.tsx`), notas de marca, seção E2E (pré-requisitos e variáveis `E2E_*`) e a lista de falhas corrigidas na BL-21 |
| `05_infra/README.md` | 2026-08-12 | **parcial** | **Obsoleto:** "Status atual (BL-01)" diz que `backend` e `frontend` "ainda **não** estão neste arquivo", mas estão (`05_infra/docker-compose.yml:111` e `:150`); "Parar e reverter" diz que `backup/` está "a ser implementado", mas `backup/backup-db.sh` e `restore-db.sh` existem e são descritos mais abaixo no mesmo arquivo; o título "Conteúdo planejado (próximas etapas)" rotula como plano uma árvore toda implementada. **Contradiz o código:** o passo 2 do Render cita as branches `staging_back`/`staging_front` e o passo 3 fala em "4 serviços web + 2 bancos", mas o `render.yaml` só tem `garra-backend` (`main_back`), `garra-frontend` (`main_front`) e `garra-db` (`render.yaml:42-145`), e o próprio README registra a remoção do staging (DEC-22). **Faltante:** o `render.yaml` define `preDeployCommand: alembic upgrade head` (linha 54) e `RUN_MIGRATIONS_ON_STARTUP` (linha 62), e a segunda não está em nenhum `.env.example` (`grep RUN_MIGRATIONS 05_infra/.env.example 04_backend/.env.example` → vazio). **Correto e a preservar:** DEC-09, pré-requisitos (porta 5433), tabela de serviços, deploy em VPS (BL-27), backup/restore (BL-29), limitação do MinIO no Render (bate com `render.yaml:106-114`, `MINIO_*` comentados) |
| `00_docs/arquitetura.md` | 2026-10-27 | **parcial** | Blueprint (`status: draft`) que mistura o implementado e o planejado sem distinguir. **§4 Contratos de API:** não existem no código `/gabarito/funcoes-mao-obra`, `/fotos/{id}/legenda-ia/gerar` nem nenhuma rota de `/relatorios` (`grep -nE '@router\.' 04_backend/app/api/v1/*.py`); existem e não estão na tabela `GET /ocorrencias/{id}` (`ocorrencias.py:58`) e `POST /edificacoes/{id}/documentos` (`edificacoes.py:80`). **§3 ER:** desenha `PROMPT_IA` e os campos `FOTO.prompt_ia_id`/`aprovado_por_id` (linhas 244-252), que não existem em `app/models/` (`grep -n "prompt_ia\|aprovado_por_id" 04_backend/app/models/*.py` → vazio), e não mostra `ocorrencias.prioridade_sugerida`, `prioridade_ajustada_por_id`, `prioridade_ajustada_em` (migration `d3b7c9e4f1a2`) nem `criado_por_id`. **§7 Estrutura de pastas:** marca `03_frontend`/`04_backend`/`05_infra` como "a implementar" e lista `services/report_generator/strategies/`, `services/ia_legenda/`, `workers/`, `04_backend/prompts/` e `templates/ltip_template.html.j2`/`rfip_template.html.j2`, que não existem (`ls 04_backend/app/services/report_generator` → `__init__.py`, `rfo_pipeline.py`). **§2/§10.5 e ai-summary:** apresentam Redis + Celery + Nginx como topologia, mas não há Redis/Celery no compose nem em `requirements.txt` (`05_infra/docker-compose.yml:32`) e a produção real é o Render (`render.yaml`), citado só na tabela da §1 (linha 45). **Correto e a preservar:** §1 (stack), §5, §6, ADR-01 a ADR-16 (decisões registradas), §9, §10.1, §10.7, §10.8, §11 |
| `04_backend/alembic/README` | 2026-07-19 | **efetiva** | Texto padrão do Alembic ("Generic single-database configuration with an async dbapi"), coerente com o `alembic/env.py` assíncrono descrito em `04_backend/README.md` |
| `04_backend/templates/contracts/contrato_revisado_template.placeholders.md` | 2026-08-05 | **efetiva** | Os 23 campos listados batem um a um com os `{{ ... }}` extraídos de `contrato_revisado_template.docx` (leitura de `word/document.xml` com `zipfile`) |

### 2.2 Requisitos, decisões e gestão (`00_docs/` e `00_docs/projeto/`)

Os arquivos marcados com † são documentos de gestão compartilhados: pelas regras do lote, só são atualizados no fechamento de lote, nunca pela D04.

| Documento | Data | Veredito | Evidência |
|---|---|---|---|
| `00_docs/estudo-do-contexto.md` | 2026-10-27 | **efetiva** | Diz o objetivo (§1: gargalo da produção manual de documentos), atores (§3), RN/RF/RNF (§5-§7) e lacunas (§9). Tema = requisitos, não implementação. RN-04 (linha 138) e lacuna #10 resolvida (linha 255) batem com `ocorrencia_service.py:106-133`. `status: validated` |
| `00_docs/projeto/decisoes.md` † | 2026-10-27 | **efetiva** | DEC-01 a DEC-30; as recentes batem com o código: DEC-27 → `require_equipe` e migration `7c1a4e0b93d5`; DEC-29 → `ocorrencia_service.py:12`; DEC-30 → `app/scripts/build_brand_assets.py` e `templates/assets/` |
| `00_docs/projeto/status.md` † | 2026-10-27 | **efetiva** | A linha 12 diz que restam "o template do RFIP, o `ltip_pipeline.py` de renderização e a decisão de provedor de IA (B-04)", o que bate com `ls 04_backend/app/services/report_generator` (só `rfo_pipeline.py`) e com `requirements.txt` sem SDK de LLM |
| `00_docs/projeto/backlog-tarefas.md` † | 2026-10-27 | **efetiva** | BL-15 "✅ Concluída (2026-09-20)", com caminhos que existem (`ocorrencia_service.py`, `tests/test_ocorrencias_prioridade.py`, migration `d3b7c9e4f1a2`) |
| `00_docs/projeto/riscos.md` † | 2026-10-27 | **efetiva** | Registro vivo de riscos, atualizado no mesmo commit das decisões. Confronto item a item com o código: **não determinado** (não é documento descritivo do sistema) |
| `00_docs/projeto/backlog-kanban.md` † | 2026-10-27 | **efetiva** | Espelho local do board do Notion (DEC-20/ADR-11). Se está em sincronia com o Notion: **não determinado** (o Notion não foi consultado) |
| `00_docs/projeto/backlog-tarefas-humanas.md` | 2026-10-27 | **efetiva** | Backlog humano (HT-XX), atualizado com DEC-29/DEC-30 no commit `0b47e64` |
| `00_docs/projeto/ata-validacao-lacunas.md` | 2026-10-27 | **efetiva** | Ata datada das sessões de 2026-09-10 e 2026-09-17, coerente com DEC-26 a DEC-29 |
| `00_docs/projeto/pauta-validacao-lacunas.md` | 2026-10-27 | **efetiva** | A linha 14 registra o status: Blocos 1-3 encerrados, resta o Bloco 4 (B-04). Coerente com `status.md` |
| `00_docs/projeto/escopo.md` | 2026-10-27 | **efetiva** | Dentro/fora do escopo e critérios de aceite da v1.0; atualizado com DEC-26/DEC-28 |
| `00_docs/projeto/ciclo-de-vida.md` | 2026-10-27 | **efetiva** | Modelo de ciclo de vida e etapas 0-7 (`status: aprovado`); documento de processo, sem afirmações sobre o código |
| `00_docs/projeto/cronograma.md` | 2026-10-27 | **parcial** | Baseline com marcos vencidos e não atingidos: M4 ("RFO end-to-end funcional (cadastro → visita → PDF/DOCX)", 2026-08-21) e M6/M7 (até 2026-10-23) não ocorreram, porque não há rota de geração de relatório (`app/api/v1/` sem rota de relatório; `03_frontend/app/inspecoes/[id]/relatorio/page.tsx` usa `UnderConstruction`). O frontmatter diz `last_updated: 2026-07-17`. Replanejar datas é decisão humana (ver §5.4) |
| `00_docs/projeto/plano-gestao-configuracao.md` | 2026-08-12 | **parcial** | **Contradiz o código:** §1.1, §1.4, §2 (tabela de ambientes), §3.1 e §3.2 descrevem 4 branches de longa duração com `staging_back`/`staging_front`, os serviços `garra-*-staging` e o banco `garra-db-staging`, que foram removidos pela DEC-22 (`decisoes.md`, DEC-22; `render.yaml` sem staging; `.github/workflows/ci.yml:3` "Staging [...] foi removida"; `git branch -r \| grep -c staging` → 0). A §1.1 diz que `main` "não está mais conectada a nenhum serviço", mas hoje `main` é o tronco sincronizado para `main_back`/`main_front` (`.github/workflows/sync-deploy-branches.yml`; `backlog.toml`, `branch_principal = "main"`). A §3.1 cita `mypy app`, que não roda no `ci.yml` (só `ruff check .` com `continue-on-error: true`, linhas 81-83). **Correto e a preservar:** §1.2 (Conventional Commits, citado pelas regras do lote), §1.3, §1.5/§5 (template de PR, idêntico a `.github/pull_request_template.md`), §6, §7 |
| `00_docs/projeto/resumo-executivo.md` | 2026-07-19 | **parcial** | Diz o objetivo e o problema com clareza (seções "O Problema" e "A Solução"). **Obsoleto:** a tabela "Cronograma Estimado por Fase" ainda marca a Fase 2 como "⏳" e as Fases 3-6 como "⬜", mas backend, frontend e deploy existem (`04_backend/app/api/v1/`, `03_frontend/app/`, `render.yaml`). "Gera relatórios completos [...] com um clique" descreve o objetivo, não o estado atual (a geração não está exposta) |
| `00_docs/projeto/relatorio-benchmark-geracao-pdf-docx.md` | 2026-08-12 | **efetiva** | Relatório datado do benchmark BL-22 (`status: concluido`); os artefatos citados existem (`app/scripts/benchmark_relatorio_geracao.py`, `seed_benchmark_rfo.py`, `templates/rfo_benchmark_template.docx`) |
| `00_docs/projeto/revisao-seguranca-owasp.md` | 2026-09-10 | **efetiva** | Revisão datada (BL-23). Os achados corrigidos batem com o código: S-01 (registro só por auditor depois do primeiro usuário, `auth.py:38-43`), S-02 (`app/core/rate_limit.py`), S-04 (fail-closed em `app/core/config.py`), S-15 (perfis explícitos em `app/api/deps.py`) |
| `00_docs/analise-comparativa-contratos.md` | 2026-07-19 | **efetiva** | Análise jurídica do contrato de desenvolvimento; não descreve o sistema e não há código para confrontar |
| `00_docs/contrato-prestacao-servicos-desenvolvimento.md` | 2026-07-19 | **efetiva** | Minuta contratual; idem |

### 2.3 Material voltado ao cliente (`00_docs/cliente/`)

| Documento | Data | Veredito | Evidência |
|---|---|---|---|
| `00_docs/cliente/briefing-tecnico-para-ia.md` | 2026-10-27 | **parcial** | **Contradiz o código:** §6 descreve "4 branches dedicadas" com `staging_back`/`staging_front` e o banco `garra-db-staging` (removidos pela DEC-22; `render.yaml`); a tabela de stack (linha 96) e o fluxo (linha 99) dão "Redis 7 + Celery" como parte do sistema, mas não estão no compose nem em `requirements.txt`. **Vago:** §7 "Status Atual" não diz que a geração de relatório ainda não está disponível para o usuário. **Correto:** §1-§5 (natureza do serviço, objetivo, escopo, fora do escopo com DEC-26/DEC-28) |
| `00_docs/cliente/solicitacao-templates-docx.md` | 2026-08-12 | **refazer** | Minuta (`status: draft`) para pedir ao cliente os `.docx` e o logo "para resolver o bloqueio B-02". Ficou sem objeto: B-02 foi encerrado e "HT-02 fica reduzida à confirmação de versão vigente dos arquivos, sem nada a solicitar ao cliente" (`00_docs/projeto/status.md:100`; DEC-25 e DEC-30). Se for enviada como está, pede ao cliente algo que já não é necessário |
| `00_docs/cliente/relatorio-situacao-mvp.docx` | 2026-09-10 | **efetiva** | Instantâneo datado ("atualizado em 12/08/2026", lido de `word/document.xml`) para o cliente. Correto para a data; o estado atual fica em `status.md`. Não reescrever um entregável já enviado |
| `00_docs/cliente/proposta-comercial.md` | 2026-07-19 | **efetiva** | Proposta comercial datada (entregável). Não descreve o estado do código |
| `00_docs/cliente/apresentacao-comercial.md` | 2026-07-19 | **efetiva** | Roteiro de slides comerciais (entregável); idem |
| `00_docs/cliente/prompt-lado-cliente.md` | 2026-07-29 | **efetiva** | Prompt-sistema fornecido pelo cliente, insumo do ADR-12/RF-15 (feature ainda não implementada). É insumo, não descrição do sistema |

### 2.4 Insumos convertidos e originais do cliente

| Documento | Data | Veredito | Evidência |
|---|---|---|---|
| `00_docs/convertidos/README.md` | 2026-07-19 | **efetiva** | Índice de 9 conversões; `ls 00_docs/convertidos` tem 9 `.md` além do README |
| As 9 conversões em `00_docs/convertidos/` (`COND.md`, `Contrato_Prestacao_Servicos_Software.md`, `Laudo_Tecnico_de_Inspecao_Predial_2026_-_Cond_Cortina_DAmpezzo.md`, `Laudo_Tecnico_de_Vistoria_Cautelar_de_Recebimento_-_Reforma_New_York_-_V01.md`, `Laudo_Tecnico_de_Vistoria_de_Imovel_Residencial_-_Ap_1404.md`, `RFO_INSPECAO.md`, `Relatorio_Fotografico_de_Inspecao_Predial_-_CORTINA_DAMPAREZZO_-_Versao_Final.md`, `Relatorio_de_Fiscalizacao.md`, `Relatorio_de_Fiscalizacao_1.md`) | 2026-07-19 | **efetiva** | Insumos de conteúdo; `RFO_INSPECAO.md` é lido pelo código (`app/scripts/rfo_gabarito_parser.py`, seed BL-05). Não se reescrevem |
| `01_output-context/README.md`, `Contrato_Revisado_Garra_Software.md`, `Relatorio_de_Fiscalizacao_1.md` | 2026-07-19 | **efetiva** | O índice lista os 2 `.md` presentes. Pasta de originais do cliente: **não pode ser alterada** (regras do lote; DEC-25/ADR-13) |

### 2.5 Templates binários em `04_backend/templates/`

| Documento | Data | Veredito | Evidência |
|---|---|---|---|
| `templates/rfo/rfo_template.docx`, `templates/ltip/ltip_template.docx` | 2026-10-27 | **efetiva** (não é documentação) | Artefatos gerados por `build_rfo_templates.py`/`build_ltip_templates.py` ("não editar à mão", `04_backend/README.md`). Ficam fora da D04 |
| `templates/contracts/contrato_revisado_template.docx` | 2026-08-05 | **efetiva** (não é documentação) | Template `docxtpl` gerado por `app/scripts/build_contract_template_docx.py`; os campos batem com o `.placeholders.md` |
| `templates/rfo_benchmark_template.docx` | 2026-08-12 | **efetiva** (não é documentação) | Gerado por `app/scripts/build_rfo_benchmark_docx_template.py:18`. Se ainda é necessário: **não determinado** (ver §5.4) |

### 2.6 Instruções de agentes e governança (`.github/`)

| Documento | Data | Veredito | Evidência |
|---|---|---|---|
| `.github/pull_request_template.md` | 2026-07-19 | **efetiva** | O checklist (`pytest`, `npm run lint` + `build`, `downgrade()`, `.env.example`, docs) bate com os comandos de `04_backend/pytest.ini`, `03_frontend/package.json` e com as regras do lote |
| `.github/agents/engenheiro-ia.agent.md` | 2026-07-29 | **parcial** | "Lógica de IA reside em `04_backend/app/services/ai/`" (linha 54), mas `arquitetura.md` §7 define `services/ia_legenda/`. Nenhum dos dois existe ainda (`ls 04_backend/app/services`) |
| As outras 13 instruções `.agent.md` (`arquiteto-software`, `backend`, `contratos-juridicos`, `conversor-documentos-md`, `criador-de-prompts`, `design-ui-ux`, `devops`, `engenheiro-software`, `estudo-contexto`, `frontend`, `gestor-projeto-arquiteto-solucoes`, `organizador-pastas`, `prototipagem-documentacao-cliente`) | 2026-07-19 a 2026-08-12 | **efetiva** | Instruções por papel, sem caminhos que contradigam o código. `devops.agent.md:66` e `:72` reforçam DEC-09 ("nunca crie `infra/` ou `src/` na raiz"). `backend.agent.md` remete a `00_docs/arquitetura.md` (que é **parcial**, §2.1) |
| `.github/agents/guia_passo_a_passo_segundo_cerebro_projeto_novo.md`, `.github/agents/prompt_infra_segundo_cerebro_projeto_novo.md` | 2026-07-19 | **efetiva** | Metodologia genérica de base de conhecimento (origem da convenção de frontmatter e `ai-summary` usada em `00_docs/`). Não descreve o sistema. Estão em `agents/` sem serem agentes, o que é questão de organização, não de conteúdo |
| `.github/prompts/03-organizar-pastas.prompt.md` | 2026-07-19 | **parcial** | Linha 19: árvore com `src/  ← código-fonte da aplicação`, contrariando a DEC-09/ADR-05 (`05_infra/README.md`, "Sem aninhamento `src/`") |
| `.github/prompts/04-arquitetura.prompt.md` | 2026-07-19 | **parcial** | Linha 16: "Defina a estrutura de pastas do `src/`" (contraria a DEC-09) |
| `.github/prompts/06-backend.prompt.md` | 2026-07-19 | **parcial** | Linha 20: "Código de backend em `src/`" (o backend fica em `04_backend/`) |
| `.github/prompts/07-frontend.prompt.md` | 2026-07-19 | **parcial** | Linha 21: "Componentes e telas em `src/` (frontend)" (o frontend fica em `03_frontend/`) |
| `.github/prompts/08-engenheiro-software.prompt.md` | 2026-07-19 | **parcial** | Linhas 5-6: "Backend implementado em `src/`" e "Frontend implementado em `src/`" |
| Os outros 40 prompts: `00-ativar-fluxo-completo`, `01-converter-documentos`, `02-estudo-contexto`, `05-prototipagem`, `09-criar-prompt`, `10-iniciar-documentacao-sistema-predial`, `11-projetar-sistema-predial`, `12-devops`, `12-proposta-comercial-e-prototipo`, `13-planejar-ciclo-vida-e-tarefas`, `14-setup-ambiente-desenvolvimento`, `15-scaffold-backend-fastapi`, `16-scaffold-frontend-nextjs-pwa`, `17-modelagem-dados-migrations`, `17-templates-ltip-relatorio-fotografico` e `18` a `42` (todos `.prompt.md`) | 2026-07-19 a 2026-09-10 | **efetiva** | Prompts de ativação de tarefas já registradas no backlog (BL-XX em `backlog-tarefas.md`). São registro do pedido feito, não descrição do estado atual. Os que citam pastas usam os nomes com prefixo (ex.: `15-...:42` "o código deve ficar em `04_backend/`"; `16-...:44` "em `03_frontend/`"; `14-...:32` "o local definitivo é `05_infra/`"). Os prompts 36-39 (legendas por IA) descrevem trabalho ainda não feito (B-04 aberto em `status.md`) |

### 2.7 Arquivos não inventariados pela D02

| Documento | Data | Veredito | Evidência |
|---|---|---|---|
| `BACKLOG.md` | 2026-10-28 | **efetiva** (não tocar) | Backlog executável do `backlog-auto`; a "Regra de pronto" item 3 proíbe editá-lo em lote paralelo |
| `00_docs/backlog-auto/BACKLOG-MANUAL.md`, `00_docs/backlog-auto/CELULAR.md` | 2026-10-28 / 2026-10-27 | **efetiva** (não tocar) | Manual da ferramenta `backlog-auto`, citado em `BACKLOG.md` e `backlog.toml`. Não descreve o sistema. Se bate com o código da ferramenta: **não determinado** (fora do escopo da D03) |
| `backlog-auto/README.md`, `backlog-auto/docs/PROMPTS.md`, `backlog-auto/src/backlog_auto/templates/{BACKLOG,CELULAR,MANUAL}.md` | não determinado | **efetiva** (não tocar) | Documentação e templates internos do módulo `backlog-auto`, isento na barreira (`backlog.toml`, `[guard] isentos`). Fora do escopo da documentação do sistema |

### 2.8 Docstrings de módulo e cabeçalhos de scripts e configs

| Conjunto | Veredito | Evidência |
|---|---|---|
| 119 docstrings de módulo Python (`02_inventario.md`) | **efetiva** (não tocar) | São código-fonte, que a D04 não pode alterar. Amostras conferidas batem com o código: `rfo_pipeline.py` declara a fila assíncrona "pendente" (não há Celery); `ocorrencia_service.py:1` cita RN-04, que está implementada |
| 10 cabeçalhos (`ci.yml`, `cd-*.yml`, `sync-deploy-branches.yml`, `dependabot.yml`, `docker-compose*.yml`, `backup-db.sh`, `restore-db.sh`, `render.yaml`) | **efetiva** (não tocar) | Configuração e scripts. Amostras conferidas: `ci.yml:3` registra a remoção do staging; `docker-compose.yml:32` registra a ausência de `redis`/`celery-worker` |

---

## 3. Lacunas: documentos que deveriam existir (veredito **ausente**)

| Tema | Veredito | Evidência |
|---|---|---|
| Visão geral e objetivo na raiz (`README.md`) | **ausente** | `ls README*` na raiz → "No such file or directory". O objetivo só aparece espalhado em `estudo-do-contexto.md` §1, `resumo-executivo.md` e `briefing-tecnico-para-ia.md` §2 |
| Índice da documentação (`00_docs/README.md`) | **ausente** | `ls 00_docs/README.md` → "No such file or directory". Previsto na D04 (`BACKLOG.md`) |
| Arquitetura **como implementada** | **parcial** (não ausente) | Coberta por `00_docs/arquitetura.md`, que precisa separar o implementado do planejado (§2.1) |
| Como instalar, rodar e testar o projeto inteiro | **ausente** como roteiro único | Os passos estão espalhados por `05_infra/README.md`, `04_backend/README.md` (seções BL-04/BL-05/BL-07) e `03_frontend/README.md` (pré-requisitos do E2E), com a divergência de porta 5432/5433 (`04_backend/.env.example` × `05_infra/docker-compose.yml:54`). Nenhum documento dá a sequência completa: subir a infra → `.env` → migrations → seed → backend → frontend → testes |
| Dicionário de dados | **ausente** | Não há documento por tabela e coluna. O ER de `arquitetura.md` §3 diverge dos modelos (§2.1). O código tem 18 tabelas (`grep -n "__tablename__" 04_backend/app/models/*.py`) e 6 migrations |
| Referência de configuração (variáveis de ambiente) | **ausente** | As variáveis estão em `04_backend/.env.example`, `05_infra/.env.example`, `05_infra/.env.render.example` e `render.yaml`, sem tabela única. `RUN_MIGRATIONS_ON_STARTUP` (`app/core/config.py:25`) e `NEXT_PUBLIC_API_URL` (`03_frontend/lib/api-client.ts:14`) não estão em nenhum `.env.example` |
| Decisões | **efetiva** (não ausente) | `00_docs/projeto/decisoes.md` (DEC-01 a DEC-30) e ADR-01 a ADR-16 em `arquitetura.md` §8 |
| Guia de contribuição | **ausente** como documento | As regras existem, mas espalhadas: commits em `plano-gestao-configuracao.md` §1.2, PR em `.github/pull_request_template.md`, pastas em DEC-09 (`05_infra/README.md`), regras de lote em `BACKLOG.md`. Não há `CONTRIBUTING`, `AGENTS.md` nem `CLAUDE.md` (`02_inventario.md`, "Procurado e não encontrado") |
| README do E2E (`03_frontend/e2e/README.md`) | **ausente** | Citado em `03_frontend/playwright.config.ts:10`; `ls 03_frontend/e2e` → `helpers.ts`, `ltip.spec.ts`, `rfo.spec.ts` |

---

## 4. Resumo

| Veredito | Quantidade | Documentos |
|---|---|---|
| **efetiva** | 94 dos 109 inventariados, mais os 8 não inventariados (§2.7) | 15 instruções em `.github/agents/`, 40 prompts, o template de PR, 29 de `00_docs/` (gestão, decisões, requisitos, insumos convertidos, entregáveis datados ao cliente), 3 de `01_output-context/` e 6 de `04_backend/` (README do Alembic, placeholders e templates `.docx`). Docstrings e cabeçalhos (§2.8) também são efetiva, mas não entram nesta contagem |
| **parcial** | 14 | `04_backend/README.md`, `03_frontend/README.md`, `05_infra/README.md`, `00_docs/arquitetura.md`, `plano-gestao-configuracao.md`, `cronograma.md`, `resumo-executivo.md`, `briefing-tecnico-para-ia.md`, `engenheiro-ia.agent.md` e os prompts `03`, `04`, `06`, `07`, `08` |
| **refazer** | 1 | `00_docs/cliente/solicitacao-templates-docx.md` |
| **ausente** | 7 | `README.md` (raiz), `00_docs/README.md`, guia de instalação/execução/testes, dicionário de dados, referência de configuração, guia de contribuição e `03_frontend/e2e/README.md` (citado por `playwright.config.ts`) |

Conferência: 94 efetiva + 14 parcial + 1 refazer = 109 documentos inventariados.

---

## 5. Plano de ação

Escopo da D04 pelo `BACKLOG.md`: **Toca: `00_docs, README.md`**. Os itens em §5.3 ficam fora desse `Toca`. O integrador decide se amplia o `Toca` da D04 ou se os executa no fechamento de lote. Os documentos **efetiva** não são alterados; entram só como link no índice. Nenhum item altera código, testes, dados, `01_output-context/` ou os documentos de gestão compartilhados (†).

### 5.1 Arquivos a criar (dentro do `Toca` da D04)

| Arquivo | O que deve conter | Fontes verificadas |
|---|---|---|
| `README.md` (raiz) | (1) Objetivo do sistema em um parágrafo: o texto declarado pelo dono em `01_sistema.md` §1.1, com a ressalva explícita de que a geração de PDF/DOCX ainda **não** está exposta ao usuário (só por script) e só o RFO tem pipeline; (2) mapa das pastas de topo `00_docs` a `05_infra` (DEC-09) com uma linha cada; (3) início rápido com a sequência mínima (ver o guia de §5.1); (4) link para `00_docs/README.md` | `01_sistema.md` §1-§3; `05_infra/README.md` (DEC-09); §1 deste documento |
| `00_docs/README.md` | Índice com uma linha por documento de `00_docs/` (inclusive `_preparo/`, `backlog-auto/`, `cliente/`, `convertidos/`, `projeto/`), mais os READMEs de `03_frontend/`, `04_backend/`, `05_infra/`, `01_output-context/` e `.github/pull_request_template.md`, agrupado por tema (visão geral, arquitetura, operação, requisitos, gestão, cliente, insumos). Indicar quais são registros datados (benchmark, OWASP, ata, relatório do MVP) e quais são documentos vivos. Seguir o frontmatter e o `ai-summary` de `00_docs/estudo-do-contexto.md` | §2 deste documento |
| `00_docs/guia-desenvolvimento.md` | Roteiro único e testado de ponta a ponta: pré-requisitos (Docker, Python 3.12, Node; versões de `01_sistema.md` §5.2); `05_infra/.env` a partir de `.env.example`; `docker compose up -d postgres minio createbuckets`; `04_backend/.env` com **`POSTGRES_PORT=5433`**; `alembic upgrade head`; `python -m app.scripts.seed_gabarito`; `python -m app.scripts.seed_admin` (com `ADMIN_SENHA` definida); `uvicorn app.main:app --reload`; `npm install` e `npm run dev`; testes (`pytest` e `ruff check .`, com o aviso de que o `ruff` não está em `requirements.txt` e de que um `pyproject.toml` externo ao repositório pode mudar o resultado, como em `01_sistema.md` §5.2; `npm run lint`, `npm run build`, `npm run test:e2e`); limitação do WeasyPrint no Windows; problemas conhecidos (porta 5432 × 5433, serviço PostgreSQL nativo na 5432). Remeter aos READMEs de pasta para os detalhes, sem duplicá-los | `04_backend/README.md`, `03_frontend/README.md`, `05_infra/README.md`, `01_sistema.md` §5 |
| `00_docs/dicionario-de-dados.md` | Uma seção por tabela das 18 (`contratos`, `contrato_executores`, `contrato_nbrs`, `edificacoes`, `fotos`, `inspecoes`, `localizacoes`, `ocorrencias`, `relatorios`, `responsaveis`, `sistemas_prediais`, `subsistemas`, `tipos_anomalia`, `tipos_falha`, `usuarios`, `visitas`, `visita_mao_obras`, `visita_medicoes`) com colunas, tipos, nulabilidade, FKs e a RN/DEC de origem, derivadas de `04_backend/app/models/*.py` e das 6 migrations; valores permitidos (`role`: `auditor`/`auxiliar`/`cliente`; `grau_risco`: `MINIMO`/`MEDIO`/`CRITICO`; prioridade 0-5 com a regra RN-04); nota marcando o que está no ER de `arquitetura.md` §3 mas não no código (`PROMPT_IA`, `FOTO.prompt_ia_id`, `FOTO.aprovado_por_id`) | `app/models/`, `alembic/versions/`, `ocorrencia_service.py` |
| `00_docs/configuracao.md` | Tabela única de variáveis de ambiente: nome, padrão em `Settings` (`app/core/config.py`), onde é definida (`04_backend/.env.example`, `05_infra/.env.example`, `05_infra/.env.render.example`, `render.yaml`), se é obrigatória em produção (fail-closed) e o efeito. Incluir `RUN_MIGRATIONS_ON_STARTUP`, `NEXT_PUBLIC_API_URL`, `E2E_BASE_URL`, `E2E_API_BASE_URL`, `ADMIN_EMAIL`/`ADMIN_SENHA`/`ADMIN_NOME` e a ausência de `MINIO_*` no `render.yaml` (`01_sistema.md`, risco 3) | arquivos citados |
| `00_docs/guia-contribuicao.md` | Regras de contribuição consolidadas, por referência e sem copiar: estrutura de pastas (DEC-09), branches vigentes (`main` → `main_back`/`main_front` por `sync-deploy-branches.yml`, DEC-22), Conventional Commits com escopo da pasta e rodapé `Refs BL-XX` (`plano-gestao-configuracao.md` §1.2), checklist do PR (`.github/pull_request_template.md`), migration sempre com `downgrade()`, variável nova no `.env.example`, nunca commitar `.env`, originais de `01_output-context/` intocáveis, templates gerados não se editam à mão (`04_backend/README.md`), convenção de frontmatter e `ai-summary` em `00_docs/`, agentes em `.github/agents/` e o fluxo do `backlog-auto` (`BACKLOG.md`, `00_docs/backlog-auto/BACKLOG-MANUAL.md`) | arquivos citados |

### 5.2 Arquivos a refazer ou corrigir (dentro do `Toca` da D04)

| Arquivo | Veredito | O que fazer (preservando o que está correto, conforme §2) |
|---|---|---|
| `00_docs/arquitetura.md` | parcial | (1) Acrescentar no topo uma seção "Estado da implementação (2026-10-28)" com uma tabela implementado/planejado por componente; (2) §4: marcar como **planejado** `/gabarito/funcoes-mao-obra`, `/fotos/{id}/legenda-ia/gerar` e toda a subseção "Relatórios", e acrescentar `GET /ocorrencias/{id}` e `POST /edificacoes/{id}/documentos`; (3) §3: acrescentar `prioridade_sugerida`, `prioridade_ajustada_por_id`, `prioridade_ajustada_em` e `criado_por_id`, marcar `PROMPT_IA` e os campos de aprovação da `FOTO` como planejados (ADR-12) e remeter ao novo `dicionario-de-dados.md`; (4) §7: trocar a árvore pela estrutura real (sem "a implementar"; `templates/rfo|ltip|contracts|assets/`; `report_generator/` só com `rfo_pipeline.py`), deixando `strategies/`, `workers/`, `ia_legenda/` e `prompts/` numa lista "previsto"; (5) §2, §10.5 e `ai-summary`: mostrar a topologia real (Render: `garra-backend`, `garra-frontend`, `garra-db`; sem Redis/Celery) ao lado da topologia-alvo, marcando Redis/Celery como pendentes (ADR-06); (6) atualizar `last_updated` |
| `00_docs/projeto/plano-gestao-configuracao.md` | parcial | Reescrever §1.1, §1.4, §2 (linha de Staging) e §3.1-§3.2 conforme a DEC-22: duas branches de deploy (`main_back`, `main_front`) alimentadas por `main` via `sync-deploy-branches.yml`, sem staging no Render; trocar `mypy app` pelo que o `ci.yml` roda de fato (`ruff check .`, não bloqueante, linhas 81-83); manter §1.2, §1.3, §1.5, §5, §6 e §7; atualizar `last_updated` |
| `00_docs/projeto/resumo-executivo.md` | parcial | Substituir a tabela "Cronograma Estimado por Fase" por um estado atual resumido, remetendo a `status.md`, e acrescentar uma frase dizendo que a geração de PDF/DOCX é a entrega pendente; manter "O Problema", "A Solução" e "Benefícios" |
| `00_docs/cliente/briefing-tecnico-para-ia.md` | parcial | §6: duas branches de deploy, sem staging nem `garra-db-staging` (DEC-22); stack e fluxo (linhas 96 e 99): marcar Redis/Celery como previstos, não implantados; §7: dizer que a geração de relatório ainda não está disponível na interface. Manter §1-§5 |
| `00_docs/cliente/solicitacao-templates-docx.md` | refazer | Trocar `status: draft` por um status de superado e pôr no topo uma nota curta: "Sem objeto desde 2026-09-17: os originais já estão em `01_output-context/` (DEC-25/ADR-13) e a marca foi vetorizada internamente (DEC-30); não enviar". Manter o corpo como registro histórico ou removê-lo (o git guarda a versão anterior). Remover é decisão humana; a nota de superado é o mínimo |

### 5.3 Fora do `Toca` da D04 (o integrador decide)

| Arquivo | Veredito | O que fazer |
|---|---|---|
| `04_backend/README.md` | parcial | Reescrever a abertura e "Status atual real" (sem a dependência de "modelos originais"; incluir o perfil `auxiliar` e RN-04); refazer a árvore "Estrutura atual" (6 migrations, 20 módulos de teste, `repositories/`, `services/report_generator/`, `templates/rfo|ltip|contracts|assets/`, `Dockerfile.render`); juntar "Como rodar localmente" e a seção BL-04 numa sequência com `POSTGRES_PORT=5433`, `alembic upgrade head` e `seed_gabarito`; corrigir a frase de `/auth/register` (bootstrap da DEC-24); corrigir os títulos quebrados ("Storage service MinIO/S3 (BL-07)" e o `## ` vazio); documentar `RUN_MIGRATIONS_ON_STARTUP`, `seed_admin` e que o `ruff` é instalado à parte. Manter as seções BL-05, BL-12/13, DEC-30 e BL-07 |
| `03_frontend/README.md` | parcial | Corrigir a abertura e o texto do `rfo.spec.ts` (B-02 encerrado; o que falta é a rota/job de geração); completar a árvore com `lib/`, `e2e/` e os componentes ausentes; documentar `NEXT_PUBLIC_API_URL` (embutida no build). Manter o resto |
| `05_infra/README.md` | parcial | Trocar "Status atual (BL-01)" pelo estado real (compose com `postgres`, `minio`, `createbuckets`, `backend`, `frontend`; sem `redis`/`celery-worker`); tirar "a ser implementado" de `backup/`; renomear "Conteúdo planejado" para "Estrutura"; corrigir os passos 2 e 3 do Render (sem staging; 2 serviços + 1 banco); citar `RUN_MIGRATIONS_ON_STARTUP`/`preDeployCommand`. Manter o resto |
| `03_frontend/e2e/README.md` | ausente | Criar com os pré-requisitos e comandos de E2E (hoje na seção "Testes E2E" de `03_frontend/README.md`), já que `playwright.config.ts:10` o cita. Alternativa: corrigir o comentário do `playwright.config.ts`, mas isso é código e fica fora desta etapa |
| `.github/agents/engenheiro-ia.agent.md` | parcial | Alinhar o caminho com `arquitetura.md` §7 (`services/ia_legenda/`) ou o contrário. Escolher o nome é decisão humana (§5.4) |
| `.github/prompts/03-organizar-pastas`, `04-arquitetura`, `06-backend`, `07-frontend`, `08-engenheiro-software` (`.prompt.md`) | parcial | Trocar as menções a `src/` por `04_backend/` e `03_frontend/` (DEC-09), nas linhas citadas na §2.6 |

### 5.4 Pendências que exigem decisão humana

1. **Objetivo × realidade**: o objetivo declarado promete PDF e DOCX gerados pelo usuário, mas a geração não está exposta (`01_sistema.md` §1.2). Os documentos novos vão registrar isso como pendência. Se o objetivo deve ser reescrito ou se essa é a próxima entrega fica com o dono.
2. **`cronograma.md`**: os marcos M4, M6 e M7 venceram sem ser atingidos. Replanejar datas é decisão de gestão. A D04 não deve inventar datas novas; no máximo acrescenta uma nota "baseline de 2026-07-17; marcos M4-M7 não atingidos em 2026-10-28" se o integrador autorizar.
3. **Nome da pasta de IA**: `services/ai/` (`engenheiro-ia.agent.md`) × `services/ia_legenda/` (`arquitetura.md` §7).
4. **`solicitacao-templates-docx.md`**: manter como histórico com a nota de superado, ou remover.
5. **Templates soltos** `04_backend/templates/rfo_template.html.j2` (sem referência no código) e `rfo_benchmark_template.docx`: se ainda são necessários. Envolve código e fica fora da documentação.
6. **Variáveis fora dos `.env.example`** (`RUN_MIGRATIONS_ON_STARTUP`, `NEXT_PUBLIC_API_URL`) e a porta `POSTGRES_PORT=5432` em `04_backend/.env.example` (propostas P-01 a P-03 de `01_sistema.md`): são arquivos de configuração, não documentação. A D04 só documenta a divergência.

---

## Registro da tarefa

- **Arquivo criado**: só este (`00_docs/_preparo/03_classificacao.md`). Nenhum código, teste, dado ou documento de gestão foi alterado. `BACKLOG.md`, `PROGRESSO.md` e `01_output-context/` não foram tocados.
- **Branch**: `worktree-backlog-D03`, avançada por fast-forward de `71ac8fd` para `14ead2f` (`main`) para conter os insumos D01 e D02; o commit desta tarefa vem por cima.
- **Comandos de verificação usados** (todos de leitura): `git log --name-only --format=@%cs -- <pastas>`, `git merge-base --is-ancestor 0b47e64 161ba19`, `git branch -r`, `grep -nE '@router\.(get|post|put|patch|delete)\(' 04_backend/app/api/v1/*.py`, `grep -n "__tablename__" 04_backend/app/models/*.py`, `ls` das pastas citadas, leitura de `word/document.xml` dos `.docx` com `zipfile` e as buscas `grep` citadas em cada linha.
- **Testes**: não se aplicam. A tarefa só cria um arquivo de documentação (item 1 da "Regra de pronto" vale para tarefas com código). `pytest`, `ruff`, `npm run lint` e `npm run build` não foram executados nesta tarefa; o resultado mais recente registrado está em `01_sistema.md` §5.2.
