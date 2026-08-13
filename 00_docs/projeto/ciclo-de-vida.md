---
title: Ciclo de Vida de Desenvolvimento — Sistema de Automação de Relatórios Prediais
type: gestao
status: aprovado
owner: Garra Engenharia
last_updated: 2026-07-17
---

# Ciclo de Vida de Desenvolvimento

> Referências: [escopo.md](escopo.md), [decisoes.md](decisoes.md) (DEC-01 a DEC-08), [riscos.md](riscos.md), [status.md](status.md), [estudo-do-contexto.md](../estudo-do-contexto.md) (RF/RNF/RN), [arquitetura.md](../arquitetura.md) (ADRs).

## 1. Modelo de Ciclo de Vida Escolhido

**Incremental por fatias verticais (vertical slices por tipo de documento), com gestão iterativa inspirada em Scrum leve** (sprints de 1-2 semanas, backlog único priorizado, sem cerimônias formais completas).

A decisão foi registrada como **DEC-08** em [decisoes.md](decisoes.md#dec-08--modelo-de-ciclo-de-vida-incremental-por-fatia-vertical-com-gestão-iterativa-leve).

## 2. Justificativa

| Fator do projeto | Por que descarta outros modelos | Por que favorece o incremental escolhido |
|---|---|---|
| Equipe pequena (1 engenheiro ou pequena equipe, sem PM dedicado) | Descarta Scrum formal completo (overhead de cerimônias/papéis desproporcional) e V-model (exige planos de teste e especificação formal muito extensos antes de codificar) | Sprints curtos e backlog único reduzem overhead de gestão, mantendo previsibilidade |
| 10 lacunas `[A ESCLARECER]` não validadas com o cliente (**bloqueio B-01**, risco **R-06**) | Descarta cascata pura — exigiria fechar 100% dos requisitos antes de iniciar qualquer construção, o que travaria o projeto indefinidamente | Permite iniciar imediatamente a fundação técnica e o incremento RFO (não depende das lacunas) enquanto a validação com o cliente ocorre em paralelo |
| Templates originais disponíveis apenas em `.xlsx`/`.xlsm`/PDF, nunca em `.docx` (**B-02 reclassificado**, risco **R-05** rebaixado) | Descarta qualquer modelo que assuma "templates prontos em Word" como pré-condição de início (ex.: waterfall clássico) | O incremento RFO deriva o template do próprio original do cliente por script determinístico (`openpyxl` para planilha, `pypdf`/`pdfplumber` para PDF → `layout.json`), do qual saem tanto o HTML/CSS do WeasyPrint (DEC-01) quanto o DOCX do docxtpl (DEC-04) — ver DEC-25/ADR-13 |
| Necessidade de entregar valor cedo (relatório fiel ao template é o principal ganho percebido pelo cliente) | Descarta modelos que só produzem um artefato utilizável no fim do projeto | A primeira fatia vertical entregável é o **RFO completo** (cadastro → visita → relatório PDF/DOCX), demonstrável ao cliente antes dos módulos mais complexos (LTIP) |
| Escopo já formalmente congelado para v1.0 (`escopo.md`) | Reduz o risco de scope creep que normalmente motiva controles pesados de mudança (cascata/V-model) | Incremental aceita ajustes pontuais por sprint sem necessidade de replanejamento formal completo |

## 3. Etapas do Ciclo de Vida

As etapas abaixo conciliam as fases já esboçadas em [status.md](status.md) (4 a 9) com o modelo incremental por fatia vertical.

### Etapa 0 — Fundação Técnica
Infraestrutura de desenvolvimento, scaffolding de backend/frontend, modelo de dados, autenticação, storage e dados mestre. **Não depende de B-01 nem B-02.**

| Requisitos/Decisões vinculados |
|---|
| RNF-05 (autenticação), RNF-07 (storage de imagens), RF-10 (gabarito de sistemas prediais), DEC-05 (FastAPI), DEC-06 (Next.js), DEC-07 (PostgreSQL), DEC-02 (MinIO) |

### Etapa 1 — Validação de Lacunas com o Cliente *(paralela, conduzida pelo Gestor de Projeto)*
Sessão de validação dos 10 itens `[A ESCLARECER]` da seção 9 de `estudo-do-contexto.md`, priorizando os de maior impacto arquitetural (offline, multi-usuário, assinatura digital). Resolve **B-01**/**R-06**/**R-07**.

### Etapa 2 — Obtenção e Validação dos Templates Word *(paralela, conduzida pelo Gestor de Projeto)*
Confirmação da versão vigente dos originais já arquivados (`.xlsx`/`.xlsm`/PDF) e obtenção da logo vetorial/transparente. Encerra **B-02**/**R-05**.

### Etapa 3 — Incremento RFO (Relatório de Fiscalização de Obra)
Primeira fatia vertical completa: cadastro de edificação/contrato → visitas diárias → geração de relatório PDF (e DOCX quando a Etapa 2 concluir).

| Requisitos/Decisões vinculados |
|---|
| RF-01, RF-02, RF-03, RF-05, RF-06, RF-09, RF-10, RF-12 · RN-01, RN-02, RN-06, RN-07, RN-09, RN-12 · RNF-01, RNF-03, RNF-04, RNF-06 · DEC-01 (WeasyPrint), DEC-04 (docxtpl), ADR-01 |

### Etapa 4 — Incremento LTIP + Dashboard de Saúde
Segunda fatia vertical: ocorrências classificadas (CMM + GUT), relatório fotográfico por sistema, dashboard de saúde por edificação. **Depende da resolução de RN-04/lacuna #10 (Etapa 1) para fechar a regra de prioridade.**

| Requisitos/Decisões vinculados |
|---|
| RF-04, RF-06, RF-07, RF-08, RF-11 · RN-03, RN-04, RN-05, RN-07, RN-08, RN-10, RN-11, RN-13 · RNF-06 |

### Etapa 5 — Incremento Vistoria Cautelar + Vistoria Residencial + RFIP
Reaproveita o motor de relatório (templates + pipeline) construído nas etapas 3 e 4, adaptando estrutura de dados e templates específicos.

| Requisitos/Decisões vinculados |
|---|
| Seções 2.3, 2.4, 2.5 de `estudo-do-contexto.md` · RN-11 (RFIP) · RF-06 |

### Etapa 6 — Integração, Testes e Hardening de Segurança
Testes E2E entre backend e frontend, testes de carga para geração de relatórios de 200 páginas (RNF-06/R-03), revisão de segurança (OWASP Top 10, autenticação, upload de arquivos).

### Etapa 7 — Deploy e Documentação Final
Configuração de infraestrutura de produção (Docker Compose ou nuvem — depende da resolução de **B-03**, mitigado por Docker Compose agnóstico), documentação operacional e handover ao cliente.

## 4. Regras de Governança do Ciclo de Vida

1. Nenhuma tarefa da Etapa 4 relacionada a RN-04 pode ser fechada (ex.: sobrescrita manual de prioridade) sem a validação da Etapa 1.
2. A geração DOCX (docxtpl) de qualquer tipo de documento parte do `layout.json` extraído do original correspondente (`.xlsx`/`.xlsm` ou PDF), garantindo que PDF e DOCX derivem da mesma especificação (DEC-25/ADR-13).
3. Cada incremento (Etapas 3, 4, 5) deve terminar com uma demonstração funcional ao cliente antes de iniciar o próximo.
4. Mudanças de escopo dentro de um incremento em andamento exigem registro em `decisoes.md`, não replanejamento formal completo.
