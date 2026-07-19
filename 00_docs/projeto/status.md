---
title: Status do Projeto — Sistema de Automação de Relatórios Prediais
type: gestao
status: ativo
owner: Garra Engenharia
last_updated: 2026-07-17
---

# Status do Projeto

**Última atualização:** 2026-07-17  
**Fase atual:** Planejamento de Ciclo de Vida e Backlog concluído — pronto para iniciar Fundação Técnica  
**Progresso geral:** ███████░░░ 40%

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
| 6. Implementação Backend (Fundação Técnica) | 🟡 Em andamento | 25% | BL-01, BL-02, BL-04 concluídas; BL-05 a BL-07 prontas para execução |
| 7. Implementação Frontend | ⬜ Não iniciada | 0% | Prompt `16-*` pronto para execução |
| 8. Integração + Testes | ⬜ Não iniciada | 0% | Testes E2E |
| 9. Deploy + Documentação final | ⬜ Não iniciada | 0% | Sistema em produção |

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
| BL-04 — Modelagem de dados (14 modelos SQLAlchemy 2 async + migration Alembic inicial + schemas Pydantic v2) | `04_backend/app/models/`, `04_backend/app/schemas/`, `04_backend/alembic/versions/` | 2026-07-17 | ✅ Implementado e validado (migration aplicada no PostgreSQL do docker-compose; 7 testes de integração passando) |

---

## Bloqueios Ativos

| # | Bloqueio | Impacto | Responsável | Ação necessária |
|---|---|---|---|---|
| B-01 | 10 lacunas `[A ESCLARECER]` sem resposta do cliente | **Alto** — pode mudar arquitetura offline e multi-usuário | Gestor de Projeto | Agendar sessão de validação com Eng. Roniel |
| B-02 | Templates Word originais não entregues pelo cliente | **Médio** — bloqueia geração de DOCX fiel | Gestor de Projeto | Solicitar ao cliente todos os arquivos `.docx` de modelo |
| B-03 | Preferência de hospedagem não definida | **Baixo** — Docker Compose é agnóstico | Gestor de Projeto | Definir em kickoff |

---

## Próximos Passos (em ordem)

1. **[IMEDIATO]** Agendar reunião de validação com Eng. Roniel para resolver lacunas `[A ESCLARECER]` de `estudo-do-contexto.md` (especialmente: offline, multi-usuário, assinatura digital) — resolve B-01 (Etapa 1)
2. **[IMEDIATO]** Solicitar todos os arquivos `.docx` de template (RFO, LTIP, Vistoria Cautelar, RFIP) e logo em alta resolução — resolve B-02 (Etapa 2)
3. Executar os prompts `14-setup-ambiente-desenvolvimento.prompt.md` a `19-autenticacao-jwt.prompt.md` (Etapa 0 — Fundação Técnica), em ordem, sem depender de B-01/B-02
4. Validar `00_docs/arquitetura.md` com o cliente (stack, modelo de dados)
5. Iniciar o Incremento RFO (Etapa 3 de `ciclo-de-vida.md`): CRUD de edificações/contratos, visitas, upload de fotos e prototipagem do template PDF
6. Acompanhar `00_docs/projeto/cronograma.md` e `00_docs/projeto/backlog-tarefas.md` para priorização contínua do backlog

---

## Métricas do Projeto

| Métrica | Valor |
|---|---|
| Tipos de documento suportados na v1.0 | 5 (RFO, LTIP, Vistoria Cautelar, Vistoria Residencial, RFIP) |
| Regras de negócio documentadas | 13 (RN-01 a RN-13) |
| Requisitos funcionais | 12 (RF-01 a RF-12) |
| Requisitos não funcionais | 8 (RNF-01 a RNF-08) |
| Lacunas [A ESCLARECER] | 10 (seção 9 do estudo-do-contexto.md) |
| Decisões arquiteturais registradas | 12 (DEC-01 a DEC-12) |
| Riscos identificados | 9 (R-01 a R-09) |
| Entidades no modelo ER | 14 |
| Endpoints de API definidos | 30+ |
| Tarefas no backlog | 24 (BL-01 a BL-24) |
| Tarefas desbloqueadas para início imediato | 13 |
| Prompts de tarefas iniciais criados | 6 (`14-*` a `19-*`) |
