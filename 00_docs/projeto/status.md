---
title: Status do Projeto — Sistema de Automação de Relatórios Prediais
type: gestao
status: ativo
owner: Garra Engenharia
last_updated: 2026-08-12
---

# Status do Projeto

**Última atualização:** 2026-08-12  
**Fase atual:** MVP funcional do sistema em evolução, com backend e frontend já operando para os fluxos principais de cadastro, inspeção, ocorrências, dashboard e portal do cliente. Com a reclassificação de B-02 (DEC-25/ADR-13), o gargalo dos templates deixa de existir — restam a decisão de provedor de IA para legendas assistidas e a validação formal das lacunas de negócio.  
**Progresso geral:** ████████████████░ 85%

---

## Progresso por Fase

| Fase | Status | % | Entregável |
|---|---|---|---|
| 1. Conversão de documentos | ✅ Concluída | 100% | Documentos originais convertidos e disponibilizados em [00_docs/convertidos/](../convertidos/) |
| 2. Estudo do Contexto | ✅ Concluída | 100% | [00_docs/estudo-do-contexto.md](../estudo-do-contexto.md) validado com o domínio e os requisitos principais |
| 3. Arquitetura de Software | ✅ Concluída | 100% | [00_docs/arquitetura.md](../arquitetura.md) com stack, modelo de dados e decisões principais |
| 3.5 Planejamento de Ciclo de Vida e Backlog | ✅ Concluída | 100% | [ciclo-de-vida.md](ciclo-de-vida.md), [cronograma.md](cronograma.md) e [backlog-tarefas.md](backlog-tarefas.md) atualizados |
| 4. Validação com cliente (lacunas) | 🟡 Parcialmente concluída | 40% | A validação parcial avançou, mas ainda faltam respostas formais para as lacunas de negócio e arquitetura que impactam offline, multiusuário e assinatura digital |
| 5. Prototipagem de templates PDF/DOCX | 🟡 Em andamento | 45% | Há pipeline básico de geração no backend; a partir de DEC-25/ADR-13 os templates passam a ser derivados dos originais `.xlsx`/`.xlsm`/PDF já disponíveis em `01_output-context/`, sem depender de entrega adicional do cliente |
| 6. Implementação Backend (fundação + domínio) | ✅ Em grande parte concluída | 90% | APIs para edificações, contratos, inspeções, visitas, ocorrências, fotos, dashboard, portal e autenticação já existem e estão integradas ao repositório |
| 7. Implementação Frontend | ✅ Em grande parte concluída | 85% | Login, dashboard, CRUDs de edificações/contratos, visitas, ocorrências, upload/anotação de fotos e portal do cliente já estão presentes na interface |
| 8. Integração + Testes | 🟡 Em andamento | 75% | Testes de integração e E2E foram adicionados; a integração completa do fluxo de geração de relatório/legendas assistidas permanece pendente |
| 9. Deploy + Documentação final | 🟡 Em andamento | 80% | Deploy no Render e infraestrutura básica já foram provisionados; ajustes finais de segredos, validação de produção e documentação operacional ainda precisam terminar |

---

## Artefatos Entregues

| Artefato | Arquivo | Data | Status |
|---|---|---|---|
| Documentos originais convertidos | [00_docs/convertidos/](../convertidos/) | 2026-07-07 | ✅ Validado |
| Estudo do Contexto | [00_docs/estudo-do-contexto.md](../estudo-do-contexto.md) | 2026-07-08 | ✅ Validado |
| Arquitetura de Software | [00_docs/arquitetura.md](../arquitetura.md) | 2026-07-17 | ✅ Draft (padrões de projeto, system design e RNF atendidos adicionados) |
| Escopo do Projeto | [00_docs/projeto/escopo.md](escopo.md) | 2026-07-08 | ✅ Aprovado |
| Registro de Decisões | [00_docs/projeto/decisoes.md](decisoes.md) | 2026-07-08 | ✅ Registrado |
| Registro de Riscos | [00_docs/projeto/riscos.md](riscos.md) | 2026-07-08 | ✅ Registrado |
| Resumo Executivo | [00_docs/projeto/resumo-executivo.md](resumo-executivo.md) | 2026-07-08 | ✅ Produzido |
| Ciclo de Vida de Desenvolvimento | [00_docs/projeto/ciclo-de-vida.md](ciclo-de-vida.md) | 2026-07-17 | ✅ Aprovado |
| Cronograma | [00_docs/projeto/cronograma.md](cronograma.md) | 2026-07-17 | ✅ Aprovado |
| Backlog de Tarefas | [00_docs/projeto/backlog-tarefas.md](backlog-tarefas.md) | 2026-07-17 | ✅ Ativo |
| Reorganização de pastas (prefixo numérico) + DEC-09/ADR-05 | `00_docs/`, `01_output-context/`, `02_prototipos/`, `03_frontend/`, `04_backend/`, `05_infra/` | 2026-07-17 | ✅ Aplicado |
| Prompts das tarefas iniciais (Etapa 0) | `.github/prompts/14-*.prompt.md` a `19-*.prompt.md` | 2026-07-17 | ✅ Criados (não executados) |
| BL-01 — Ambiente de desenvolvimento (Docker Compose PostgreSQL 16 + MinIO) | `05_infra/docker-compose.yml`, `05_infra/.env.example` | 2026-07-17 | ✅ Implementado e validado (`docker compose up -d` — ambos os serviços `healthy`) |
| BL-02 — Scaffold do backend FastAPI | `04_backend/app/main.py`, `app/core/`, `app/api/` | 2026-07-17 | ✅ Implementado e validado (`GET /health`) |
| BL-03 — Scaffold do frontend Next.js 14 PWA | `03_frontend/app/`, `manifest.json` | 2026-07-17 | ✅ Implementado |
| BL-04 — Modelagem de dados (14 modelos SQLAlchemy 2 async + migration Alembic inicial + schemas Pydantic v2) | `04_backend/app/models/`, `04_backend/app/schemas/`, `04_backend/alembic/versions/` | 2026-07-17 | ✅ Implementado e validado (migration aplicada no PostgreSQL do docker-compose; 7 testes de integração passando) |
| BL-05 — Seed do gabarito de sistemas prediais/subsistemas/tipos de anomalia/falha/localizações | `04_backend/app/scripts/rfo_gabarito_parser.py`, `seed_gabarito.py`, DEC-13 | 2026-07-17 | ✅ Implementado e validado (parser + seed idempotente) |
| BL-06 — Autenticação JWT + bcrypt | `04_backend/app/api/v1/auth.py`, `app/core/security.py`, DEC-15 | 2026-07-19 | ✅ Implementado e validado (7 testes em `tests/test_auth.py`) |
| BL-07 — Storage service MinIO/S3 (boto3) | `04_backend/app/services/storage/` | 2026-07-20 | ✅ Implementado e validado (9 testes em `tests/test_storage.py`) |
| BL-25 — Repositório Git remoto (GitHub) | `github.com/rafaelroriz-age/garra-engenharia` | 2026-07-19 | ✅ Criado e publicado (branch `main`) |
| BL-26 — Workflow de CI (`ci.yml`) | `.github/workflows/ci.yml` | 2026-07-19 | ✅ Publicado |
| Plano de Gestão de Configuração (DEC-14) | `00_docs/projeto/plano-gestao-configuracao.md` | 2026-07-19 | ✅ Aprovado |
| Backlog de Tarefas Humanas | `00_docs/projeto/backlog-tarefas-humanas.md` | 2026-07-20 | ✅ Ativo |
| Tratamento de erros RFC 7807 (global) | `04_backend/app/core/errors.py`, `app/core/exception_handlers.py`, DEC-11 | 2026-07-20 | ✅ Implementado (`DomainError`/`NotFoundError`/`ConflictError` + `RequestValidationError`) |
| BL-08 — CRUD de Edificações + upload de documentos técnicos | `04_backend/app/api/v1/edificacoes.py`, `03_frontend/app/edificacoes/` | 2026-07-20 | ✅ Implementado e validado — backend (7 testes) e frontend (listagem, busca, criação) confirmados funcionais em teste manual de UI (2026-07-22) |
| BL-09 — CRUD de Contratos com executoras/NBRs em cascata + Inspeção 1:1 | `04_backend/app/api/v1/contratos.py`, `03_frontend/app/contratos/` | 2026-07-20 | ✅ Implementado e validado — backend (6 testes) e frontend (listagem com filtros) confirmados funcionais em teste manual de UI (2026-07-22) |
| BL-10 — Registro de Visitas (equipe, serviços, medições) + detalhe de Inspeção | `04_backend/app/api/v1/visitas.py`, `app/api/v1/inspecoes.py`, `03_frontend/app/inspecoes/[id]/visitas/` | 2026-07-20 | ✅ Backend implementado e validado (6 testes); frontend existe e carrega, não re-testado a fundo em 2026-07-22 |
| BL-11 — Upload de fotos (clipboard + manual) com reprocessamento Pillow (A08) | `04_backend/app/api/v1/fotos.py`, `app/services/image_processing.py` | 2026-07-20 | ✅ Backend implementado e validado (8 testes); frontend de upload ainda não confirmado em teste manual de UI |
| Deploy Render (Blueprint IaC) — backend, frontend e banco definidos como código | `render.yaml`, `04_backend/Dockerfile.render`, `03_frontend/Dockerfile.render`, `05_infra/.env.render.example` | 2026-07-21 | ✅ Implementado — falta HT-04 (aplicar o Blueprint no Dashboard do Render) |
| Deploy Render via MCP — recursos de produção criados no workspace Render | `garra-db`, `garra-backend`, `garra-frontend` | 2026-08-03 | ✅ Provisionado (parcial) — pendente preencher segredos do backend, validar `/health` e confirmar alocação no project `garraengenharia` |
| DEC-22 — Consolidação de branches de deploy: staging removida, sync automático `main`→`main_back`/`main_front` | `render.yaml`, `.github/workflows/sync-deploy-branches.yml`, `.github/workflows/ci.yml` | 2026-08-05 | ✅ Implementado e validado — `main_back`/`main_front` sincronizadas com `main` (RBAC/BL-30, dashboard, ocorrências, editor de anotação, template DOCX do contrato), deploy automático confirmado **live** em produção via MCP do Render; 8 PRs do Dependabot mescladas, 5 majors não testados fechados |
| ⚠️ Achado crítico (2026-08-05): produção com banco desconectado | `garra-backend` (Render) | 2026-08-07 | 🟡 Parcialmente resolvido — em 2026-08-07 o agente aplicou via MCP todas as env vars não secretas (`ENVIRONMENT`, `BACKEND_CORS_ORIGINS`, `POSTGRES_HOST/PORT/USER/DB`, `JWT_ALGORITHM`, `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`) e confirmou `NEXT_PUBLIC_API_URL` no frontend; deploy subiu `live`, mas `/health` segue `"database":"unavailable"` porque `POSTGRES_PASSWORD` e `JWT_SECRET_KEY` são segredos que o MCP não expõe/não deve manusear. Restam 4 itens de Dashboard — ver checklist em HT-04 |
| HT-12 — Board Kanban real criado no Notion (DEC-20/ADR-11) | Notion: "Backlog — Garra Engenharia" | 2026-08-07 | ✅ Concluída — banco de dados + view "Quadro" agrupada por Status, com 52 cartões (BL-01 a BL-40 e HT-01 a HT-12) |
| Assets oficiais de marca organizados para o frontend | `03_frontend/public/brand/logos/` | 2026-08-11 | ✅ Organizado — 4 variantes JPEG da marca foram movidas da raiz do repositório para uma pasta canônica de branding com nomes semânticos; a aplicação na interface ficou formalizada na BL-41 |
| Pauta da sessão de validação das lacunas (entregável de agente para HT-01) | [pauta-validacao-lacunas.md](pauta-validacao-lacunas.md) | 2026-08-07 | ✅ Pronta para uso — 9 lacunas remanescentes em 4 blocos, com opções de resposta e encaminhamento pós-reunião |
| Solicitação formal dos templates `.docx` e logo (entregável de agente para HT-02) | [solicitacao-templates-docx.md](../cliente/solicitacao-templates-docx.md) | 2026-08-07 | ⚠️ **Obsoleta em 2026-08-12** — o inventário de `01_output-context/` mostrou que os originais (`.xlsx`/`.xlsm`/PDF) sempre estiveram disponíveis; a solicitação deve ser reduzida à confirmação de versão vigente + logo vetorial (ver DEC-25/ADR-13 e HT-02) |
| Login funcional (BL-06 frontend) | `03_frontend/app/(auth)/login/page.tsx`, `components/layout/app-shell.tsx` (guarda de rota + logout) | 2026-07-22 | ✅ Implementado e validado — antes era só um placeholder; fluxo login → dashboard → logout testado via browser automatizado |
| Fix: `NEXT_PUBLIC_API_URL` sem `/api/v1` (todas as chamadas do frontend voltavam 404) | `05_infra/.env`, `.env.example`, `docker-compose.yml`, `render.yaml`, `.env.render.example` | 2026-07-22 | ✅ Corrigido — bug afetava tanto dev local quanto o Blueprint de produção/staging do Render |
| BL-40 — Template DOCX do Contrato de Prestação de Serviços (placeholders Jinja2) | `04_backend/app/scripts/build_contract_template_docx.py`, `04_backend/templates/contracts/contrato_revisado_template.docx`, `contrato_revisado_template.placeholders.md` | 2026-08-03 | ✅ Implementado — gerado a partir de `01_output-context/Contrato_Revisado_Garra_Software.md`; escopo administrativo/contratual, não resolve B-02/HT-02 (templates de relatório técnico) |
| BL-31 — Editor de anotação de fotos (Fabric.js): seta, retângulo/elipse, texto, traço livre, desfazer, seletor de cor | `03_frontend/components/photo-annotation-editor.tsx`, `03_frontend/components/foto-upload.tsx` | 2026-07-29 (confirmado em 2026-08-05) | ✅ Implementado — achatamento via `canvas.toDataURL()`, integrado ao fluxo de upload (clipboard paste e arquivo manual) sem nenhuma mudança de backend; estava presente no repositório desde o commit `29ea188` mas não constava como concluído em `backlog-tarefas.md` |
| BL-30 — RBAC: `Usuario.role`, `Responsavel.usuario_id`, `Contrato.contratante_id` + router `/portal/edificacoes` | `04_backend/app/api/deps.py` (`require_role`, `get_current_cliente_responsavel`), `app/api/v1/portal.py`, migration `5f9f3cb4d87f` | 2026-07-29 (confirmado e revalidado em 2026-08-05) | ✅ Implementado e validado — migration aplicada no Postgres de dev (`alembic current` = head); 4 testes de integração em `tests/test_rbac_portal.py` passando (acesso padrão auditor, bloqueio 403 `require_role`, escopo do contratante em `/portal/edificacoes`, 404 para cliente sem `Responsavel` vinculado); estava presente no repositório desde o commit `29ea188` mas não constava como concluído em `backlog-tarefas.md` |
| BL-32/BL-33 — Portal do Cliente completo: dashboard, acompanhamento (visitas/ocorrências por contrato), documentos e download por URL pré-assinada | `04_backend/app/services/portal_service.py`, `app/schemas/portal.py`, `app/api/v1/portal.py`, `03_frontend/app/portal/page.tsx`, `app/portal/documentos/page.tsx` | 2026-08-07 | ✅ Implementado e validado — escopo obrigatório por `Responsavel.usuario_id` (404 para recurso de outro contratante, nunca 403, para não revelar existência); 7 testes de integração em `tests/test_portal_cliente.py` passando |
| BL-27 — Stack de produção em VPS próprio (alternativa ao Render) | `05_infra/docker-compose.prod.yml`, `05_infra/nginx/nginx.conf` | 2026-08-07 | ✅ Implementado — imagens GHCR com `IMAGE_TAG` imutável (rollback determinístico), nenhuma porta de banco/objeto publicada, TLS via certbot com renovação automática, rate limit de borda em `/api/v1/auth/login`, HSTS/CSP |
| BL-29 — Backup e restauração (RNF-08) | `05_infra/backup/backup-db.sh`, `restore-db.sh`, `05_infra/README.md` | 2026-08-07 | ✅ Implementado — `pg_dump --format=custom` + espelho do bucket MinIO, retenção aplicada só após dump válido; restore exige confirmação explícita e salva dump `pre-restore`. Destino externo do backup segue `[A ESCLARECER]` (RNF-08) |
| BL-23 — Revisão de segurança OWASP Top 10 (DEC-24) | `00_docs/projeto/revisao-seguranca-owasp.md`, `04_backend/app/core/rate_limit.py`, `app/core/middleware.py`, `app/scripts/seed_admin.py`, `tests/test_seguranca.py` | 2026-08-07 | ✅ Concluída — 6 achados corrigidos: registro público de auditor (A01, **falha crítica real**), força bruta no login (A07), `/docs` em produção e `JWT_SECRET_KEY` default (A05), cabeçalhos de segurança (A05) e `X-Request-ID` (A09); 8 testes automatizados |
| BL-16 — Dashboard de saúde por edificação/sistema predial (RF-07): validação do agregado + revisão de regras de negócio | `04_backend/app/services/edificacao_service.py`, `app/services/ocorrencia_service.py`, `03_frontend/app/dashboard/page.tsx`, `tests/test_ocorrencias_dashboard.py` | 2026-08-12 | ✅ Concluída — agregado (conformidade por sistema, distribuição de Grau de Risco, gravidade GUT média por subsistema) revalidado via `pytest` (3 testes passando); revisão de RN-05 encontrou lacuna real (`prioridade` sem validação de intervalo 0-5) e corrigida em `ocorrencia_service._validar_payload` (`DomainError` 422 `ocorrencia-prioridade-invalida`), com teste novo cobrindo o caso |

---

## Bloqueios Ativos

| # | Bloqueio | Impacto | Responsável | Ação necessária |
|---|---|---|---|---|
| B-01 | 10 lacunas `[A ESCLARECER]` ainda não resolvidas formalmente; #6/#11/#12 já foram tratadas via DEC-18, #13 foi esclarecida parcialmente pelo prompt do cliente e as demais (#1, #2, #3, #4, #5, #7, #8, #9, #10) continuam pendentes | **Alto** — ainda há decisões remanescentes que podem alterar arquitetura offline, multi-usuário e assinatura digital | Gestor de Projeto | Finalizar a validação formal das lacunas remanescentes com Eng. Roniel — ver [HT-01](backlog-tarefas-humanas.md#ht-01--validar-as-10-lacunas-a-esclarecer-com-o-cliente) |
| B-02 | **Reclassificado em 2026-08-12 (DEC-25/ADR-13):** os originais dos 5 modelos **existem** em `01_output-context/` — RFO e RFIP em planilha (`.xlsx`/`.xlsm`), LTIP e as duas vistorias em PDF final de alta fidelidade. O `.docx` nunca chegou porque o cliente não produz esses documentos em Word. Resta pendente apenas a **logo vetorial/transparente** (RN-07) | **Baixo** — deixou de bloquear BL-12, BL-13 e BL-17, que passam a ser construídas a partir dos originais disponíveis; a logo em JPEG já atende provisoriamente o cabeçalho | Gestor de Projeto | Confirmar com o cliente que os arquivos em `01_output-context/` são a versão vigente e solicitar apenas a logo vetorial — ver [HT-02](backlog-tarefas-humanas.md#ht-02--confirmar-versão-vigente-dos-originais-e-obter-a-logo-vetorial) |
| B-04 | Provedor de IA/LLM para geração assistida de legendas técnicas (RF-15, DEC-21) ainda não escolhido (lacuna #13) | **Médio** — bloqueia BL-34 a BL-39; envolve custo por chamada e política de retenção/privacidade dos dados enviados a terceiros (fotos/descrições de imóveis) | Gestor de Projeto | Definir provedor (OpenAI, Azure OpenAI, Anthropic, outro) e política de dados antes de iniciar BL-34/BL-36 a BL-39 |

**Originais disponíveis por tipo de documento** (inventário de `01_output-context/` em 2026-08-12 — arquivos locais/OneDrive, fora do Git por convenção do `.gitignore`):

| # | Documento | Original disponível | Formato | Uso na derivação do template (ADR-13) |
|---|---|---|---|---|
| 1 | **RFO** — Relatório de Fiscalização de Obra (§2.1) | `RFO INSPEÇÃO .xlsx` (77,9 MB) e `Relatório de Fiscalização 1.xlsm` (17,5 MB) | Planilha | Fonte de verdade estrutural e de layout de impressão — extração via `openpyxl`. Já foi a fonte do gabarito de sistemas prediais (BL-05/DEC-13) |
| 2 | **LTIP** — Laudo Técnico de Inspeção Predial (§2.2) | `Laudo Técnico de Inspeção Predial 2026 - Cond. Cortina D'Ampezzo.pdf` (32,5 MB) | PDF final | Extração de métricas tipográficas (fonte, margens, cabeçalho com logo) via `pypdf`/`pdfplumber` |
| 3 | **Vistoria Cautelar de Recebimento** (§2.3) | `Laudo Técnico de Vistoria Cautelar de Recebimento - Reforma New York - V01.pdf` (38,5 MB) | PDF final | Idem LTIP |
| 4 | **Vistoria de Imóvel Residencial** (§2.4) | `Laudo Técnico de Vistoria de Imóvel Residencial - Ap. 1404.pdf` (21,5 MB) | PDF final | Idem LTIP |
| 5 | **RFIP** — Relatório Fotográfico de Inspeção Predial (§2.5) | `Relatório Fotográfico de Inspeção Predial - CORTINA D'AMPAREZZO - Versão Final.xlsx` (479,3 MB) | Planilha | Extração via `openpyxl` em modo `read_only`/streaming (arquivo grande) |
| 6 | **Logo da Garra Engenharia** (RN-07) | 4 variantes JPEG em `03_frontend/public/brand/logos/` | Raster | ⚠️ **Única pendência real de B-02** — versão vetorial (`.svg`/`.ai`) ou `.png` transparente segue recomendada para PWA, favicon e relatórios com fidelidade máxima |

> As versões `.md` em [00_docs/convertidos/](../convertidos/) continuam servindo como referência de **conteúdo e estrutura**, mas deixam de ser a base de layout: a fidelidade visual passa a ser extraída dos originais acima (ADR-13). O `.xlsm` nunca deve ser executado — apenas lido, sem carregar macros VBA (OWASP A08). BL-40 (template do **contrato administrativo**) permanece um escopo distinto e não se confunde com estes 5 modelos técnicos.

> B-03 (preferência de hospedagem) resolvido em 2026-07-21 — hospedagem definida como Render. Em 2026-08-03, o provisionamento foi executado via MCP; a HT-04 permanece em andamento apenas para ajustes finais (segredos, validação e organização no project).
>
> **Impacto adicional do prompt do cliente (2026-07-28):** o fluxo de legendas assistidas por IA não reabre a base técnica já concluída, mas exige revisão de integração em BL-04, BL-07, BL-11 e BL-31 para acomodar o novo fluxo de geração/ aprovação junto ao upload e à anotação de fotos.

> Detalhamento completo dessas ações (passo a passo, links, alternativas via agente/MCP) em [backlog-tarefas-humanas.md](backlog-tarefas-humanas.md).

---

## Próximos Passos (em ordem)

1. **[IMEDIATO — 2 cliques no Dashboard do Render]** Adicionar `POSTGRES_PASSWORD` (via "Add from Database" apontando para `garra-db`) e `JWT_SECRET_KEY` no serviço `garra-backend`; em seguida definir Pre-Deploy Command (`cd 04_backend && alembic upgrade head`) e Health Check Path (`/health`). ⚠️ **A partir de DEC-24, com `ENVIRONMENT=production` o backend NÃO SOBE sem uma `JWT_SECRET_KEY` de pelo menos 32 caracteres** (fail-closed proposital, OWASP A05) — checklist completo em [HT-04](backlog-tarefas-humanas.md#ht-04--aplicar-o-blueprint-do-render-ou-provisionar-servidorvps-alternativo-e-registrar-domínio)
2. **[IMEDIATO]** Iniciar a derivação dos templates a partir dos originais já disponíveis em `01_output-context/` (DEC-25/ADR-13): script de extração `openpyxl` para RFO/RFIP e `pypdf`/`pdfplumber` para os 3 laudos, gerando `layout.json` → `.html.j2` (WeasyPrint) + `.docx` (docxtpl) — destrava BL-12/BL-13/BL-17 sem depender do cliente
3. **[IMEDIATO]** Confirmar com o cliente apenas duas coisas (não é mais uma solicitação de templates): que os arquivos em `01_output-context/` são a versão vigente, e o envio da logo vetorial/transparente (RN-07) — ver [HT-02](backlog-tarefas-humanas.md#ht-02--confirmar-versão-vigente-dos-originais-e-obter-a-logo-vetorial)
4. **[IMEDIATO]** Agendar a sessão de validação das lacunas remanescentes (#1, #2, #3, #4, #5, #7, #8, #9, #10) — pauta pronta em [pauta-validacao-lacunas.md](pauta-validacao-lacunas.md) — reduz B-01 e destrava BL-15
5. Rodar `gh auth login` e aplicar a proteção das branches `main`/`main_back`/`main_front` (HT-05) — comando pronto em [backlog-tarefas-humanas.md](backlog-tarefas-humanas.md#ht-05--configurar-proteção-das-branches-mainmain_frontmain_back-no-github)
6. Rodar `python -m app.scripts.seed_admin` no ambiente de produção (Shell do Render) para criar o auditor de bootstrap — obrigatório desde DEC-24, pois `POST /auth/register` deixou de ser público
7. Confirmar no Dashboard Render que os recursos estão no project/grupo `garraengenharia` (ou mover para ele, se necessário)
8. Executar BL-41 com o agente `Especialista UI/UX`: refatorar o frontend para aplicar as logos oficiais em landing, login, shell autenticado, metadata e PWA, substituindo o placeholder `public/icon.svg` e a nomenclatura legada da marca
9. Re-testar em UI o frontend de Visitas (BL-10), Upload de fotos (BL-11) e Ocorrências (BL-14); endpoints já existem — falta validação manual/end-to-end em navegador (BL-16 já revalidada via testes automatizados em 2026-08-12)
10. Definir o provedor de IA e a política de dados para desbloquear BL-34 e a extensão BL-36 a BL-39 (item do Bloco 4 da pauta)
11. Validar `00_docs/arquitetura.md` com o cliente (stack, modelo de dados)

> **Regra de atualização:** ao concluir qualquer tarefa do backlog, atualizar imediatamente o status em `backlog-tarefas.md`, `backlog-tarefas-humanas.md` (se aplicável) e neste arquivo, desbloqueando (🔴→🟢) toda tarefa dependente que tinha a tarefa concluída como pré-requisito.

---

## Métricas do Projeto

| Métrica | Valor |
|---|---|
| Tipos de documento suportados na v1.0 | 5 (RFO, LTIP, Vistoria Cautelar, Vistoria Residencial, RFIP) |
| Regras de negócio documentadas | 13 (RN-01 a RN-13) |
| Requisitos funcionais | 12 (RF-01 a RF-12) |
| Requisitos não funcionais | 8 (RNF-01 a RNF-08) |
| Lacunas [A ESCLARECER] | 10 (seção 9 do estudo-do-contexto.md); 3 já tratadas/definidas (#6/#11/#12), 1 parcialmente esclarecida (#13) e 9 ainda exigem confirmação formal |
| Decisões arquiteturais registradas | 16 (DEC-01 a DEC-16) |
| Riscos identificados | 9 (R-01 a R-09) |
| Entidades no modelo ER | 14 |
| Endpoints de API definidos | 30+ |
| Tarefas no backlog | 39 (BL-01 a BL-39) |
| Tarefas concluídas | 15+ (fundação técnica + BL-08/BL-09/BL-16/BL-20/BL-25/BL-26/BL-30/BL-31/BL-40, com BL-10/BL-11/BL-14 já parcialmente integrados) |
| Tarefas desbloqueadas para início imediato | 9 (BL-08 a BL-11, BL-14, BL-27, BL-29, BL-32, BL-33) |
| Prompts de tarefas criados | 22 (`14-*` a `39-*`) |
