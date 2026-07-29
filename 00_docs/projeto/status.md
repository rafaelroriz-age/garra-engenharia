---
title: Status do Projeto — Sistema de Automação de Relatórios Prediais
type: gestao
status: ativo
owner: Garra Engenharia
last_updated: 2026-07-28
---

# Status do Projeto

**Última atualização:** 2026-07-28  
**Fase atual:** Incremento LTIP + Legendas Assistidas por IA — backend de BL-08 a BL-11 concluído; frontend de BL-08/BL-09 confirmado funcional; BL-10/BL-11 re-testes pendentes; BL-14/BL-16 aguardando integração; BL-34 a BL-39 adicionadas como próxima frente de evolução com base no prompt do cliente  
**Progresso geral:** ████████████░ 67%

---

## Progresso por Fase

| Fase | Status | % | Entregável |
|---|---|---|---|
| 1. Conversão de documentos | ✅ Concluída | 100% | `00_docs/convertidos/*.md` |
| 2. Estudo do Contexto | ✅ Concluída | 100% | `00_docs/estudo-do-contexto.md` |
| 3. Arquitetura de Software | ✅ Concluída | 100% | `00_docs/arquitetura.md` |
| 3.5 Planejamento de Ciclo de Vida e Backlog | ✅ Concluída | 100% | `00_docs/projeto/ciclo-de-vida.md`, `cronograma.md`, `backlog-tarefas.md` |
| 4. Validação com cliente (lacunas) | ⏳ Pendente | 0% | Sessão de validação agendada (Etapa 1) |
| 5. Prototipagem de templates PDF/DOCX | ⬜ Não iniciada | 0% | Bloqueada por B-02 (parcial — ver BL-12) |
| 6. Implementação Backend (Fundação Técnica) | ✅ Concluída | 100% | BL-01, BL-02, BL-04, BL-05, BL-06, BL-07 concluídas — ver [04_backend/README.md](../../04_backend/README.md) |
| 6.5 Implementação Backend (Incremento RFO) | 🟡 Em andamento | 40% | BL-08 a BL-11 (Edificações, Contratos, Visitas, Fotos) concluídas no backend — RFC 7807 global, Repository/Service Layer, 27 testes de integração novos |
| 7. Implementação Frontend | 🟡 Em andamento | 48% | Scaffold (BL-03) concluído; login funcional (2026-07-22); telas de Edificações e Contratos (BL-08/BL-09) confirmadas funcionais em teste manual de UI; Visitas/Fotos (BL-10/BL-11) implementadas mas não re-testadas; Dashboard (BL-16) e Ocorrências (BL-14) implementados no frontend mas bloqueados por endpoints de backend ainda inexistentes; fluxo de legendas assistidas por IA entra como próxima frente (BL-35, BL-39) |
| 8. Integração + Testes | 🟡 Em andamento | 10% | Testes E2E (BL-21) dependem das Etapas 3 e 4; integração do fluxo de fotos/legendas (BL-36 a BL-39) entra como prioridade de validação |
| 9. Deploy + Documentação final | 🟡 Em andamento | 25% | Gestão de Configuração (DEC-14) e CI (BL-25, BL-26) concluídos; hospedagem definida (Render, HT-03 ✅) e Blueprint IaC pronto (`render.yaml`); falta HT-04 (aplicar o Blueprint no Dashboard) |

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
| Login funcional (BL-06 frontend) | `03_frontend/app/(auth)/login/page.tsx`, `components/layout/app-shell.tsx` (guarda de rota + logout) | 2026-07-22 | ✅ Implementado e validado — antes era só um placeholder; fluxo login → dashboard → logout testado via browser automatizado |
| Fix: `NEXT_PUBLIC_API_URL` sem `/api/v1` (todas as chamadas do frontend voltavam 404) | `05_infra/.env`, `.env.example`, `docker-compose.yml`, `render.yaml`, `.env.render.example` | 2026-07-22 | ✅ Corrigido — bug afetava tanto dev local quanto o Blueprint de produção/staging do Render |

---

## Bloqueios Ativos

| # | Bloqueio | Impacto | Responsável | Ação necessária |
|---|---|---|---|---|
| B-01 | 10 lacunas `[A ESCLARECER]` sem resposta do cliente | **Alto** — pode mudar arquitetura offline e multi-usuário | Gestor de Projeto | Agendar sessão de validação com Eng. Roniel — ver [HT-01](backlog-tarefas-humanas.md#ht-01--validar-as-10-lacunas-a-esclarecer-com-o-cliente) |
| B-02 | Templates Word originais não entregues pelo cliente | **Médio** — bloqueia geração de DOCX fiel | Gestor de Projeto | Solicitar ao cliente todos os arquivos `.docx` de modelo — ver [HT-02](backlog-tarefas-humanas.md#ht-02--solicitar-e-receber-os-arquivos-docx-de-template-e-logo) |
| B-04 | Provedor de IA/LLM para geração assistida de legendas técnicas (RF-15, DEC-21) ainda não escolhido (lacuna #13) | **Médio** — bloqueia BL-34 a BL-39; envolve custo por chamada e política de retenção/privacidade dos dados enviados a terceiros (fotos/descrições de imóveis) | Gestor de Projeto | Definir provedor (OpenAI, Azure OpenAI, Anthropic, outro) e política de dados antes de iniciar BL-34/BL-36 a BL-39 |

> B-03 (preferência de hospedagem) resolvido em 2026-07-21 — hospedagem definida como Render. Falta apenas a ação humana [HT-04](backlog-tarefas-humanas.md#ht-04--aplicar-o-blueprint-do-render-ou-provisionar-servidorvps-alternativo-e-registrar-domínio) (criar conta/aplicar o Blueprint), já não é mais um bloqueio de decisão.
>
> **Impacto adicional do prompt do cliente (2026-07-28):** o fluxo de legendas assistidas por IA não reabre a base técnica já concluída, mas exige revisão de integração em BL-04, BL-07, BL-11 e BL-31 para acomodar o novo fluxo de geração/ aprovação junto ao upload e à anotação de fotos.

> Detalhamento completo dessas ações (passo a passo, links, alternativas via agente/MCP) em [backlog-tarefas-humanas.md](backlog-tarefas-humanas.md).

---

## Próximos Passos (em ordem)

1. **[IMEDIATO]** Agendar reunião de validação com Eng. Roniel para resolver lacunas `[A ESCLARECER]` de `estudo-do-contexto.md` (especialmente: offline, multi-usuário, assinatura digital) — resolve B-01 (Etapa 1)
2. **[IMEDIATO]** Solicitar todos os arquivos `.docx` de template (RFO, LTIP, Vistoria Cautelar, RFIP) e logo em alta resolução — resolve B-02 (Etapa 2)
3. Re-testar em UI o frontend de Visitas (BL-10) e Upload de fotos (BL-11) — Edificações e Contratos (BL-08/BL-09) já confirmados funcionais em 2026-07-22; implementar os endpoints de backend pendentes de Ocorrências (BL-14) e agregação do Dashboard (BL-16) para desbloquear os frontends já prontos dessas telas
4. Definir o provedor de IA e a política de dados para desbloquear BL-34 e a extensão BL-36 a BL-39 do fluxo de legendas assistidas por IA
5. Validar `00_docs/arquitetura.md` com o cliente (stack, modelo de dados)
6. Configurar manualmente a proteção de branch `main` no GitHub (HT — ação humana, ver `backlog-tarefas-humanas.md`)
7. Acompanhar `00_docs/projeto/cronograma.md` e `00_docs/projeto/backlog-tarefas.md` para priorização contínua do backlog

> **Regra de atualização:** ao concluir qualquer tarefa do backlog, atualizar imediatamente o status em `backlog-tarefas.md`, `backlog-tarefas-humanas.md` (se aplicável) e neste arquivo, desbloqueando (🔴→🟢) toda tarefa dependente que tinha a tarefa concluída como pré-requisito.

---

## Métricas do Projeto

| Métrica | Valor |
|---|---|
| Tipos de documento suportados na v1.0 | 5 (RFO, LTIP, Vistoria Cautelar, Vistoria Residencial, RFIP) |
| Regras de negócio documentadas | 13 (RN-01 a RN-13) |
| Requisitos funcionais | 12 (RF-01 a RF-12) |
| Requisitos não funcionais | 8 (RNF-01 a RNF-08) |
| Lacunas [A ESCLARECER] | 10 (seção 9 do estudo-do-contexto.md) |
| Decisões arquiteturais registradas | 16 (DEC-01 a DEC-16) |
| Riscos identificados | 9 (R-01 a R-09) |
| Entidades no modelo ER | 14 |
| Endpoints de API definidos | 30+ |
| Tarefas no backlog | 39 (BL-01 a BL-39) |
| Tarefas concluídas | 12+ (fundação técnica + BL-08/BL-09/BL-20/BL-25/BL-26, com BL-10/BL-11 já parcialmente integrados) |
| Tarefas desbloqueadas para início imediato | 10 (BL-08 a BL-11, BL-14, BL-16, BL-27, BL-29, BL-30, BL-31) |
| Prompts de tarefas criados | 22 (`14-*` a `39-*`) |
