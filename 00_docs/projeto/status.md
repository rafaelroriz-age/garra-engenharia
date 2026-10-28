---
title: Status do Projeto — Sistema de Automação de Relatórios Prediais
type: gestao
status: ativo
owner: Garra Engenharia
last_updated: 2026-09-20
---

# Status do Projeto

**Última atualização:** 2026-09-20  
**Fase atual:** MVP funcional do sistema em evolução, com backend e frontend já operando para os fluxos principais de cadastro, inspeção, ocorrências, dashboard e portal do cliente. Os templates do RFO e do LTIP já são derivados por script determinístico dos originais do cliente (BL-12/BL-13/BL-17, ADR-13), agora com a marca vetorizada no cabeçalho (DEC-30/ADR-16). **A validação de requisitos foi concluída em 2026-09-17 (DEC-29): B-01 encerrado, nenhuma tarefa segue bloqueada por lacuna; B-02 também foi encerrado na mesma data (DEC-30).** Restam o template do RFIP, o `ltip_pipeline.py` de renderização e a decisão de provedor de IA (B-04).  
**Progresso geral:** ████████████████░ 88%

---

## Progresso por Fase

| Fase | Status | % | Entregável |
|---|---|---|---|
| 1. Conversão de documentos | ✅ Concluída | 100% | Documentos originais convertidos e disponibilizados em [00_docs/convertidos/](../convertidos/) |
| 2. Estudo do Contexto | ✅ Concluída | 100% | [00_docs/estudo-do-contexto.md](../estudo-do-contexto.md) validado com o domínio e os requisitos principais |
| 3. Arquitetura de Software | ✅ Concluída | 100% | [00_docs/arquitetura.md](../arquitetura.md) com stack, modelo de dados e decisões principais |
| 3.5 Planejamento de Ciclo de Vida e Backlog | ✅ Concluída | 100% | [ciclo-de-vida.md](ciclo-de-vida.md), [cronograma.md](cronograma.md) e [backlog-tarefas.md](backlog-tarefas.md) atualizados |
| 4. Validação com cliente (lacunas) | ✅ Concluída | 100% | Bloco 1 respondido pelo cliente em 2026-09-10 (offline, equipe de campo e assinatura digital — DEC-26/27/28) e Blocos 2 e 3 encerrados em 2026-09-17 (DEC-29). **B-01 encerrado**; só permanece a decisão de provedor de IA (B-04, Bloco 4), que é escolha de fornecedor, não lacuna de requisito |
| 5. Prototipagem de templates PDF/DOCX | 🟡 Em andamento | 85% | Templates do **RFO** (BL-12/BL-13) e do **LTIP** (BL-17) concluídos: layout medido do original (`openpyxl` na planilha, `pdfplumber` no PDF) → `layout.json` → `.html.j2` (WeasyPrint) + `.docx` (docxtpl), tudo regerado por um único script. Faltam o RFIP (planilha de 479 MB), o `ltip_pipeline.py` de renderização e a conferência visual (HT-09) |
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
| Pauta da sessão de validação das lacunas (entregável de agente para HT-01) | [pauta-validacao-lacunas.md](pauta-validacao-lacunas.md) | 2026-08-07 | ✅ Usada — **Bloco 1 respondido em 2026-09-10** (lacunas #2, #3 e #9), gerando DEC-26/DEC-27/DEC-28 e a tarefa BL-42. Blocos 2, 3 e 4 seguem pendentes |
| Ata de validação das lacunas — Bloco 1 (HT-01/BL-18) | [ata-validacao-lacunas.md](ata-validacao-lacunas.md), [decisoes.md](decisoes.md) (DEC-26/27/28), [arquitetura.md](../arquitetura.md) (ADR-14/ADR-15) | 2026-09-10 | ✅ Registrada — offline fora de escopo (online-first confirmado), perfil `auxiliar` no RBAC e ausência de assinatura ICP-Brasil; RNF-02 fechado, risco R-07 encerrado, R-06 rebaixado |
| BL-42 — RBAC: perfil `auxiliar` com escrita limitada e autoria rastreável (RN-18, DEC-27/ADR-14) | `04_backend/app/api/deps.py` (`require_auditor`/`require_equipe`), migration `7c1a4e0b93d5`, `app/models/{visita,ocorrencia,foto}.py`, `tests/test_rbac_auxiliar.py`, `03_frontend/lib/use-usuario-atual.ts` | 2026-09-10 | ✅ Concluída — auxiliar cria visita/ocorrência/foto com `criado_por_id` gravado e recebe 403 em edificação/contrato/responsável/cadastro de usuário. **Fechou também uma falha real de A01**: todos os endpoints internos aceitavam qualquer usuário autenticado (um `cliente` do Portal conseguia listá-los) — agora exigem perfil explícito. 10 testes novos + 53 de regressão passando |
| BL-17 — Templates do LTIP + relatório fotográfico por sistema (ADR-13/DEC-25, RN-11) | `04_backend/app/scripts/ltip_layout_extractor.py`, `app/scripts/build_ltip_templates.py`, `templates/ltip/{layout.json,ltip_template.html.j2,ltip_template.docx}`, `tests/test_ltip_templates.py` | 2026-09-10 | ✅ Concluída — segunda origem do ADR-13 (PDF, via `pdfplumber`) implementada: A4 retrato, margens 2,79/1,99/1,91/2,01 cm, Times New Roman 12 pt (títulos 14, legendas 9), capa Open Sans 45,4 pt e 2 fichas fotográficas por página, tudo **medido** do original. O `layout.json` versionado não carrega dado do cliente — nem o nome do arquivo, que identifica o condómino (A02). 11 testes sobre PDF sintético, sem depender de `01_output-context/` |
| Solicitação formal dos templates `.docx` e logo (entregável de agente para HT-02) | [solicitacao-templates-docx.md](../cliente/solicitacao-templates-docx.md) | 2026-08-07 | ⚠️ **Obsoleta** — o inventário de `01_output-context/` (2026-08-12) mostrou que os originais (`.xlsx`/`.xlsm`/PDF) sempre estiveram disponíveis, e a logo vetorial deixou de ser necessária em 2026-09-17 (DEC-30). A solicitação se reduz à confirmação de versão vigente (ver HT-02) |
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
| BL-12/BL-13 — Templates do RFO derivados do original do cliente (PDF via WeasyPrint + DOCX via docxtpl) | `04_backend/app/scripts/rfo_layout_extractor.py`, `app/scripts/build_rfo_templates.py`, `templates/rfo/layout.json`, `templates/rfo/rfo_template.html.j2`, `templates/rfo/rfo_template.docx`, `app/services/report_generator/rfo_pipeline.py`, `tests/test_rfo_templates.py` | 2026-08-13 | ✅ Concluídas — primeira implementação real de ADR-13/DEC-25. O layout é **medido** do `Relatório de Fiscalização 1.xlsm` (margens, Arial 10/48 pt, cabeçalhos `#D9D9D9`, grade de 2 fotos por linha, 3 assinaturas) e persistido em `layout.json`, do qual PDF e DOCX derivam — impedindo que os dois formatos divirjam. O `layout.json` versionado guarda **apenas geometria**: os valores do exemplar do cliente (CPF, e-mails, nomes) são descartados antes do commit (OWASP A02). 10 testes rodando contra uma planilha sintética, sem depender de `01_output-context/`. **Pendência:** conferência visual do PDF renderizado (WeasyPrint só roda no container Docker) — HT-09 |
| Validação de requisitos concluída — encerramento de B-01 (DEC-29) | `00_docs/projeto/decisoes.md` (DEC-29), `ata-validacao-lacunas.md`, `pauta-validacao-lacunas.md`, `00_docs/estudo-do-contexto.md` (RN-04, RN-05, RN-13, RF-03, RNF-04, §9) | 2026-09-17 | ✅ Concluída — as 6 lacunas restantes (#1, #4, #5, #7, #8, #10) foram fechadas com a posição de menor impacto sobre o que já está entregue; **BL-15 desbloqueada**, BL-18/HT-01 concluídas e risco R-06 encerrado |
| Marca vetorizada — encerramento de B-02 (DEC-30/ADR-16) | `04_backend/app/scripts/bitmap_tracer.py`, `app/scripts/build_brand_assets.py`, `templates/assets/{logo-garra.svg, logo-garra-negativa.svg, logo-garra-simbolo.svg, logo-garra.png, marca.json}`, `tests/test_brand_assets.py` | 2026-09-17 | ✅ Concluída — o JPEG oficial (único formato que o cliente possui) é vetorizado por script determinístico: contornos + Douglas-Peucker + Bézier quadrática nas curvas da tipografia, sem dependência nova além do Pillow. O PDF passa a embutir o SVG e os templates DOCX de RFO/LTIP o PNG transparente, no lugar do JPEG com fundo creme; 20 testes cobrindo o tracer, a derivação e os artefatos versionados. Validado na amostra de HT-09 regerada nesta data |
| BL-15 — Prioridade sugerida pelo Grau de Risco CMM + sobrescrita rastreável (RN-04/DEC-29) | migration `d3b7c9e4f1a2`, `04_backend/app/models/ocorrencia.py`, `app/schemas/ocorrencia.py`, `app/services/ocorrencia_service.py`, `app/repositories/ocorrencia_repository.py`, `app/api/v1/ocorrencias.py`, `tests/test_ocorrencias_prioridade.py` | 2026-09-20 | ✅ Concluída — a Prioridade é **derivada** do Grau de Risco (Crítico=5, Médio=3, Mínimo=1) quando não informada; "Prioridade 0" = **não aplicável** (Conforme / "Não se Aplica", RN-10); sobrescrita explícita persiste `prioridade_sugerida` (valor original), `prioridade_ajustada_por_id` e `prioridade_ajustada_em`. 5 testes de integração cobrindo derivação, sobrescrita e o caso "não aplicável" |

---

## Bloqueios Ativos

| # | Bloqueio | Impacto | Responsável | Ação necessária |
|---|---|---|---|---|
| B-04 | Provedor de IA/LLM para geração assistida de legendas técnicas (RF-15, DEC-21) ainda não escolhido (lacuna #13) | **Médio** — bloqueia BL-34 a BL-39; envolve custo por chamada e política de retenção/privacidade dos dados enviados a terceiros (fotos/descrições de imóveis) | Gestor de Projeto | Definir provedor (OpenAI, Azure OpenAI, Anthropic, outro) e política de dados antes de iniciar BL-34/BL-36 a BL-39 |

> **B-02 encerrado em 2026-09-17 ([DEC-30](decisoes.md#dec-30--marca-vetorizada-internamente-a-partir-do-jpeg-oficial-encerramento-do-bloqueio-b-02)).** A reclassificação de 2026-08-12 (DEC-25/ADR-13) já havia mostrado que os originais dos 5 modelos **sempre existiram** em `01_output-context/` — RFO e RFIP em planilha, LTIP e as duas vistorias em PDF final — e desbloqueado BL-12/BL-13/BL-17. O último item, a **marca vetorial/transparente** (RN-07), foi resolvido internamente: `app.scripts.build_brand_assets` vetoriza o próprio JPEG oficial e gera `logo-garra.svg` (PDF), `logo-garra.png` transparente (DOCX), a variante negativa e o símbolo, com procedência registrada em `marca.json`. HT-02 fica reduzida à confirmação de versão vigente dos arquivos, sem nada a solicitar ao cliente.

> **B-01 encerrado em 2026-09-17 ([DEC-29](decisoes.md#dec-29--fechamento-das-lacunas-remanescentes-blocos-2-e-3-encerramento-do-bloqueio-b-01)).** Após o Bloco 1 (DEC-26/27/28, 2026-09-10) restavam as lacunas #1, #4, #5, #7, #8 e #10, todas de escopo localizado. Os Blocos 2 e 3 da [pauta](pauta-validacao-lacunas.md) foram fechados adotando, em cada caso, a posição de menor impacto sobre o que já está entregue: prioridade sugerida **e editável** com registro do ajuste (#10, "Prioridade 0" = não aplicável), sem periodicidade obrigatória de re-inspeção (#1), unidade de medição livre por item (#8), DOCX obrigatório (#5), fotos por clipboard/upload manual sem monitoramento de pasta (#4) e sem integração com o CREA (#7). **Nenhuma tarefa do backlog segue bloqueada por lacuna de requisito** — BL-15 foi desbloqueada, BL-18 e HT-01 concluídas e o risco R-06 encerrado. O único item de requisitos ainda aberto é o provedor de IA (B-04, Bloco 4 da pauta); o destino externo do backup (RNF-08) segue como escolha operacional, fora de B-01.

**Originais disponíveis por tipo de documento** (inventário de `01_output-context/` em 2026-08-12 — arquivos locais/OneDrive, fora do Git por convenção do `.gitignore`):

| # | Documento | Original disponível | Formato | Uso na derivação do template (ADR-13) |
|---|---|---|---|---|
| 1 | **RFO** — Relatório de Fiscalização de Obra (§2.1) | `RFO INSPEÇÃO .xlsx` (77,9 MB) e `Relatório de Fiscalização 1.xlsm` (17,5 MB) | Planilha | Fonte de verdade estrutural e de layout de impressão — extração via `openpyxl`. Já foi a fonte do gabarito de sistemas prediais (BL-05/DEC-13) |
| 2 | **LTIP** — Laudo Técnico de Inspeção Predial (§2.2) | `Laudo Técnico de Inspeção Predial 2026 - Cond. Cortina D'Ampezzo.pdf` (32,5 MB) | PDF final | Extração de métricas tipográficas (fonte, margens, cabeçalho com logo) via `pypdf`/`pdfplumber` |
| 3 | **Vistoria Cautelar de Recebimento** (§2.3) | `Laudo Técnico de Vistoria Cautelar de Recebimento - Reforma New York - V01.pdf` (38,5 MB) | PDF final | Idem LTIP |
| 4 | **Vistoria de Imóvel Residencial** (§2.4) | `Laudo Técnico de Vistoria de Imóvel Residencial - Ap. 1404.pdf` (21,5 MB) | PDF final | Idem LTIP |
| 5 | **RFIP** — Relatório Fotográfico de Inspeção Predial (§2.5) | `Relatório Fotográfico de Inspeção Predial - CORTINA D'AMPAREZZO - Versão Final.xlsx` (479,3 MB) | Planilha | Extração via `openpyxl` em modo `read_only`/streaming (arquivo grande) |
| 6 | **Logo da Garra Engenharia** (RN-07) | 4 variantes JPEG em `03_frontend/public/brand/logos/` | Raster | ✅ **Resolvido em 2026-09-17 (DEC-30/ADR-16)** — o JPEG oficial é vetorizado por `app.scripts.build_brand_assets` em `04_backend/templates/assets/logo-garra.svg` (PDF), `logo-garra.png` transparente (DOCX), negativa e símbolo |

> As versões `.md` em [00_docs/convertidos/](../convertidos/) continuam servindo como referência de **conteúdo e estrutura**, mas deixam de ser a base de layout: a fidelidade visual passa a ser extraída dos originais acima (ADR-13). O `.xlsm` nunca deve ser executado — apenas lido, sem carregar macros VBA (OWASP A08). BL-40 (template do **contrato administrativo**) permanece um escopo distinto e não se confunde com estes 5 modelos técnicos.

> B-03 (preferência de hospedagem) resolvido em 2026-07-21 — hospedagem definida como Render. Em 2026-08-03, o provisionamento foi executado via MCP; a HT-04 permanece em andamento apenas para ajustes finais (segredos, validação e organização no project).
>
> **Impacto adicional do prompt do cliente (2026-07-28):** o fluxo de legendas assistidas por IA não reabre a base técnica já concluída, mas exige revisão de integração em BL-04, BL-07, BL-11 e BL-31 para acomodar o novo fluxo de geração/ aprovação junto ao upload e à anotação de fotos.

> Detalhamento completo dessas ações (passo a passo, links, alternativas via agente/MCP) em [backlog-tarefas-humanas.md](backlog-tarefas-humanas.md).

---

## Próximos Passos (em ordem)

1. **[IMEDIATO — 2 cliques no Dashboard do Render]** Adicionar `POSTGRES_PASSWORD` (via "Add from Database" apontando para `garra-db`) e `JWT_SECRET_KEY` no serviço `garra-backend`; em seguida definir Pre-Deploy Command (`cd 04_backend && alembic upgrade head`) e Health Check Path (`/health`). ⚠️ **A partir de DEC-24, com `ENVIRONMENT=production` o backend NÃO SOBE sem uma `JWT_SECRET_KEY` de pelo menos 32 caracteres** (fail-closed proposital, OWASP A05) — checklist completo em [HT-04](backlog-tarefas-humanas.md#ht-04--aplicar-o-blueprint-do-render-ou-provisionar-servidorvps-alternativo-e-registrar-domínio)
2. **[AÇÃO HUMANA — HT-09]** Conferir visualmente a amostra do RFO em `01_output-context/_amostras_ht09/` (`amostra_rfo.pdf`, 5 páginas, e `amostra_rfo.docx`) contra o original `Relatório de Fiscalização 1.xlsm`: cabeçalho/rodapé, tabelas, quebras de página, fotos, legendas e tipografia. **Amostra regerada em 2026-09-17**, já com a marca vetorizada de fundo transparente no cabeçalho (DEC-30). Registrar aprovação ou a lista de ajustes — só então o template do RFO está liberado para produção. A geração é feita pelo agente (WeasyPrint dentro do container `garra-backend`; não roda no Windows local)
3. **[IMEDIATO]** ~~BL-17 — replicar o pipeline de ADR-13 para LTIP~~ — ✅ concluída em 2026-09-10 (extração via `pdfplumber` + `templates/ltip/`). **Resta do mesmo pipeline:** o RFIP (planilha de 479 MB, `openpyxl` em modo `read_only`/streaming) e o `ltip_pipeline.py` de renderização, equivalente ao `rfo_pipeline.py`
4. **[IMEDIATO]** Confirmar com o cliente apenas que os arquivos em `01_output-context/` (e as 4 variantes JPEG da marca) são a versão vigente — não há mais nada a solicitar: nem `.docx`, nem logo vetorial (DEC-30). Ver [HT-02](backlog-tarefas-humanas.md#ht-02--confirmar-versão-vigente-dos-originais)
5. ~~**[IMEDIATO — desbloqueada em 2026-09-17]** Implementar **BL-15** (RN-04)~~ — ✅ **concluída em 2026-09-20**: a Prioridade agora é derivada do Grau de Risco (Crítico=5, Médio=3, Mínimo=1) quando não informada, com sobrescrita explícita rastreável e "Prioridade 0" = não aplicável (migration `d3b7c9e4f1a2` + 5 testes em `tests/test_ocorrencias_prioridade.py`). Os Blocos 2 e 3 da [pauta de validação](pauta-validacao-lacunas.md) foram encerrados (DEC-29) e **B-01 deixou de existir**
5.1. ~~**[NOVA — DEC-27]** Implementar **BL-42**~~ — ✅ concluída em 2026-09-10 (perfil `auxiliar` + autoria `criado_por_id`). **Pendência operacional:** rodar `alembic upgrade head` em produção — ocorre automaticamente no próximo deploy, pois `RUN_MIGRATIONS_ON_STARTUP=true` no Render
6. Rodar `gh auth login` e aplicar a proteção das branches `main`/`main_back`/`main_front` (HT-05) — comando pronto em [backlog-tarefas-humanas.md](backlog-tarefas-humanas.md#ht-05--configurar-proteção-das-branches-mainmain_frontmain_back-no-github)
7. Rodar `python -m app.scripts.seed_admin` no ambiente de produção (Shell do Render) para criar o auditor de bootstrap — obrigatório desde DEC-24, pois `POST /auth/register` deixou de ser público
8. Confirmar no Dashboard Render que os recursos estão no project/grupo `garraengenharia` (ou mover para ele, se necessário)
9. Re-testar em UI o frontend de Visitas (BL-10), Upload de fotos (BL-11) e Ocorrências (BL-14); endpoints já existem — falta validação manual/end-to-end em navegador (BL-16 já revalidada via testes automatizados em 2026-08-12)
10. Definir o provedor de IA e a política de dados para desbloquear BL-34 e a extensão BL-36 a BL-39 (item do Bloco 4 da pauta)
11. Validar `00_docs/arquitetura.md` com o cliente (stack, modelo de dados)

> **Regra de atualização:** ao concluir qualquer tarefa do backlog, atualizar imediatamente o status em `backlog-tarefas.md`, `backlog-tarefas-humanas.md` (se aplicável) e neste arquivo, desbloqueando (🔴→🟢) toda tarefa dependente que tinha a tarefa concluída como pré-requisito.

---

## Métricas do Projeto

| Métrica | Valor |
|---|---|
| Tipos de documento suportados na v1.0 | 5 (RFO, LTIP, Vistoria Cautelar, Vistoria Residencial, RFIP) |
| Regras de negócio documentadas | 18 (RN-01 a RN-18) |
| Requisitos funcionais | 12 (RF-01 a RF-12) |
| Requisitos não funcionais | 8 (RNF-01 a RNF-08) |
| Lacunas [A ESCLARECER] | 13 registradas na seção 9 do estudo-do-contexto.md; **12 resolvidas** (#2/#3/#9 por DEC-26/27/28; #1/#4/#5/#7/#8/#10 por DEC-29; #6/#11/#12 por DEC-18) e 1 parcial (#13 — falta só o provedor de IA, bloqueio B-04) |
| Decisões arquiteturais registradas | 30 (DEC-01 a DEC-30) |
| Riscos identificados | 9 (R-01 a R-09) |
| Entidades no modelo ER | 14 |
| Endpoints de API definidos | 30+ |
| Tarefas no backlog | 39 (BL-01 a BL-39) |
| Tarefas concluídas | 18+ (fundação técnica + BL-08/BL-09/BL-12/BL-13/BL-15/BL-16/BL-20/BL-25/BL-26/BL-30/BL-31/BL-40/BL-41, com BL-10/BL-11/BL-14 já parcialmente integrados) |
| Tarefas desbloqueadas para início imediato | 0 (BL-15 — a última desbloqueada por DEC-29 — foi concluída em 2026-09-20; restam bloqueadas apenas BL-34 a BL-39 por B-04, provedor de IA) |
| Prompts de tarefas criados | 22 (`14-*` a `39-*`) |
