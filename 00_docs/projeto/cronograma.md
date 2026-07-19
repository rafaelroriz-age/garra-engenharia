---
title: Cronograma — Sistema de Automação de Relatórios Prediais
type: gestao
status: aprovado
owner: Garra Engenharia
last_updated: 2026-07-17
---

# Cronograma

> Baseado no modelo de ciclo de vida definido em [ciclo-de-vida.md](ciclo-de-vida.md). Durações são estimativas em semanas úteis para equipe pequena (1 engenheiro full-stack ou 2 papéis compartilhados). Datas de início consideram início em 2026-07-17.

## 1. Visão Geral por Etapa

| Etapa | Duração estimada | Início | Fim estimado | Dependências |
|---|---|---|---|---|
| 0. Fundação Técnica | 2 semanas | 2026-07-20 | 2026-07-31 | Nenhuma |
| 1. Validação de Lacunas (paralela) | 1 semana | 2026-07-20 | 2026-07-24 | Agendamento com Eng. Roniel (Gestor de Projeto) |
| 2. Obtenção de Templates Word (paralela) | 1-2 semanas | 2026-07-20 | 2026-07-31 | Cliente enviar arquivos `.docx` |
| 3. Incremento RFO | 3 semanas | 2026-08-03 | 2026-08-21 | Etapa 0 concluída; DOCX final depende da Etapa 2 |
| 4. Incremento LTIP + Dashboard | 4 semanas | 2026-08-24 | 2026-09-18 | Etapa 3 concluída; regra RN-04 depende da Etapa 1 |
| 5. Vistoria Cautelar + Residencial + RFIP | 2 semanas | 2026-09-21 | 2026-10-02 | Etapa 4 concluída (reaproveita motor de relatório) |
| 6. Integração, Testes, Hardening | 2 semanas | 2026-10-05 | 2026-10-16 | Etapas 3, 4 e 5 concluídas |
| 7. Deploy e Documentação Final | 1 semana | 2026-10-19 | 2026-10-23 | Etapa 6 concluída; preferência de hospedagem definida (B-03) |

**Duração total estimada:** ~14 semanas (~3,5 meses), com Etapas 1 e 2 rodando em paralelo à Etapa 0 sem impacto na data de início da Etapa 3 caso concluídas a tempo.

## 2. Marcos (Milestones)

| Marco | Descrição | Etapa | Data estimada |
|---|---|---|---|
| **M1** | Fundação técnica pronta (infra, modelo de dados, auth, storage, gabarito carregado) | 0 | 2026-07-31 |
| **M2** | Lacunas `[A ESCLARECER]` de maior impacto resolvidas com o cliente | 1 | 2026-07-24 |
| **M3** | Templates `.docx` originais recebidos e validados | 2 | 2026-07-31 (melhor caso) |
| **M4** | RFO end-to-end funcional (cadastro → visita → PDF/DOCX) — primeira demonstração ao cliente | 3 | 2026-08-21 |
| **M5** | LTIP funcional com dashboard de saúde por edificação | 4 | 2026-09-18 |
| **M6** | Todos os 5 tipos de documento implementados (RFO, LTIP, Vistoria Cautelar, Vistoria Residencial, RFIP) | 5 | 2026-10-02 |
| **M7** | Sistema testado, seguro (OWASP) e em produção | 7 | 2026-10-23 |

## 3. Riscos de Cronograma

- Se a Etapa 2 (templates) não concluir até o fim da Etapa 3, o incremento RFO entrega apenas PDF fiel (via WeasyPrint prototipado a partir do documento já convertido) e adia a geração DOCX (docxtpl) para uma sprint adicional, sem bloquear o marco M4.
- Se a Etapa 1 atrasar, a Etapa 4 pode iniciar com a regra RN-04 usando o comportamento padrão documentado (Crítico=5, Médio=3, Mínimo=1) e ajustar depois, sem re-arquitetar o modelo de dados.
- R-03 (performance de geração de PDF) deve ser validado com benchmark real ao final da Etapa 3, antes de assumir o mesmo pipeline nas etapas 4 e 5.
