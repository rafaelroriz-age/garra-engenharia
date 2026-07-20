---
title: Status do Projeto — Sistema de Automação de Relatórios Prediais
type: gestao
status: ativo
owner: Garra Engenharia
last_updated: 2026-07-20
---

# Status do Projeto

**Última atualização:** 2026-07-20  
**Fase atual:** Incremento RFO (Etapa 3) — backend de BL-08 a BL-11 concluído (Edificações, Contratos, Visitas, Fotos); frontend das mesmas tarefas pendente  
**Progresso geral:** ███████████░ 62%

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
| 7. Implementação Frontend | 🟡 Em andamento | 10% | Scaffold (BL-03) concluído; telas de CRUD (BL-08 a BL-11) 🟢 desbloqueadas (backend pronto) |
| 8. Integração + Testes | ⬜ Não iniciada | 0% | Testes E2E (BL-21) dependem das Etapas 3 e 4 |
| 9. Deploy + Documentação final | 🟡 Em andamento | 10% | Gestão de Configuração (DEC-14) e CI (BL-25, BL-26) concluídos; deploy real depende de B-03 |

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
| BL-08 (backend) — CRUD de Edificações + upload de documentos técnicos | `04_backend/app/api/v1/edificacoes.py`, `app/services/edificacao_service.py`, `app/repositories/edificacao_repository.py`, DEC-16 | 2026-07-20 | ✅ Implementado e validado (7 testes em `tests/test_edificacoes.py`); frontend pendente |
| BL-09 (backend) — CRUD de Contratos com executoras/NBRs em cascata + Inspeção 1:1 | `04_backend/app/api/v1/contratos.py`, `app/services/contrato_service.py`, `app/repositories/contrato_repository.py` | 2026-07-20 | ✅ Implementado e validado (6 testes em `tests/test_contratos.py`); frontend pendente |
| BL-10 (backend) — Registro de Visitas (equipe, serviços, medições) + detalhe de Inspeção | `04_backend/app/api/v1/visitas.py`, `app/api/v1/inspecoes.py`, `app/services/visita_service.py` | 2026-07-20 | ✅ Implementado e validado (6 testes em `tests/test_visitas.py`); frontend pendente |
| BL-11 (backend) — Upload de fotos (clipboard + manual) com reprocessamento Pillow (A08) | `04_backend/app/api/v1/fotos.py`, `app/services/foto_service.py`, `app/services/image_processing.py` | 2026-07-20 | ✅ Implementado e validado (8 testes em `tests/test_fotos.py`); frontend pendente |

---

## Bloqueios Ativos

| # | Bloqueio | Impacto | Responsável | Ação necessária |
|---|---|---|---|---|
| B-01 | 10 lacunas `[A ESCLARECER]` sem resposta do cliente | **Alto** — pode mudar arquitetura offline e multi-usuário | Gestor de Projeto | Agendar sessão de validação com Eng. Roniel — ver [HT-01](backlog-tarefas-humanas.md#ht-01--validar-as-10-lacunas-a-esclarecer-com-o-cliente) |
| B-02 | Templates Word originais não entregues pelo cliente | **Médio** — bloqueia geração de DOCX fiel | Gestor de Projeto | Solicitar ao cliente todos os arquivos `.docx` de modelo — ver [HT-02](backlog-tarefas-humanas.md#ht-02--solicitar-e-receber-os-arquivos-docx-de-template-e-logo) |
| B-03 | Preferência de hospedagem não definida | **Baixo** — Docker Compose é agnóstico | Gestor de Projeto | Definir em kickoff — ver [HT-03](backlog-tarefas-humanas.md#ht-03--decidir-a-preferência-de-hospedagem) |

> Detalhamento completo dessas ações (passo a passo, links, alternativas via agente/MCP) em [backlog-tarefas-humanas.md](backlog-tarefas-humanas.md).

---

## Próximos Passos (em ordem)

1. **[IMEDIATO]** Agendar reunião de validação com Eng. Roniel para resolver lacunas `[A ESCLARECER]` de `estudo-do-contexto.md` (especialmente: offline, multi-usuário, assinatura digital) — resolve B-01 (Etapa 1)
2. **[IMEDIATO]** Solicitar todos os arquivos `.docx` de template (RFO, LTIP, Vistoria Cautelar, RFIP) e logo em alta resolução — resolve B-02 (Etapa 2)
3. Implementar o frontend do Incremento RFO (Etapa 3 de `ciclo-de-vida.md`): telas de BL-08 (Edificações) → BL-09 (Contratos) → BL-10 (Visitas) → BL-11 (Upload de fotos) — backend das 4 já concluído
4. Validar `00_docs/arquitetura.md` com o cliente (stack, modelo de dados)
5. Configurar manualmente a proteção de branch `main` no GitHub (HT — ação humana, ver `backlog-tarefas-humanas.md`)
6. Acompanhar `00_docs/projeto/cronograma.md` e `00_docs/projeto/backlog-tarefas.md` para priorização contínua do backlog

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
| Tarefas no backlog | 29 (BL-01 a BL-29) |
| Tarefas concluídas | 9 (BL-01 a BL-07, BL-25, BL-26) — backend de BL-08 a BL-11 também concluído (frontend pendente) |
| Tarefas desbloqueadas para início imediato | 8 (BL-08 a BL-11, BL-14, BL-16, BL-27, BL-29) |
| Prompts de tarefas criados | 18 (`14-*` a `31-*`) |
