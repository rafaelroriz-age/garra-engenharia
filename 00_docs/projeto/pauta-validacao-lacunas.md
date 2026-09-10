---
title: Pauta da sessão de validação das lacunas [A ESCLARECER] — HT-01 / BL-18
type: gestao
status: draft
owner: Garra Engenharia
related:
  - 00_docs/estudo-do-contexto.md
  - 00_docs/projeto/ata-validacao-lacunas.md
  - 00_docs/projeto/backlog-tarefas-humanas.md
last_updated: 2026-09-10
---

# Pauta — sessão de validação das lacunas com o cliente

> **Status em 2026-09-10:** o **Bloco 1 foi respondido** (#3 = a, #2 = b, #9 = a) e está registrado em [ata-validacao-lacunas.md](ata-validacao-lacunas.md), gerando DEC-26, DEC-27 e DEC-28. Restam os **Blocos 2, 3 e 4**.

**Objetivo:** fechar as lacunas remanescentes de [estudo-do-contexto.md §9](../estudo-do-contexto.md#9-lacunas-a-esclarecer) e destravar o bloqueio B-01 (que ainda prende BL-15 pela lacuna #10).

**Participantes:** Eng. Roniel Ribeiro Costa (cliente/responsável técnico) + gestor do projeto.
**Duração sugerida:** 45–60 min.
**Já resolvidas — não precisam de discussão:** #6, #11 e #12 (via DEC-18) e #13 parcialmente (prompt-sistema entregue pelo cliente; falta só a decisão de provedor de IA, item 10 abaixo).

---

## Bloco 1 — Alto impacto arquitetural — ✅ RESPONDIDO EM 2026-09-10

| # | Pergunta ao cliente | Resposta | Decisão |
|---|---|---|---|
| 3 | O registro de ocorrências/fotos precisa funcionar **sem internet** em campo? | **(a)** Não — sempre há 4G/Wi-Fi. Mantém a posição online-first (§10.8 de arquitetura.md). | DEC-26 / ADR-15 — RNF-02 fechado, risco R-07 encerrado |
| 2 | O engenheiro trabalha **sozinho** ou há auxiliares que também registram em campo? | **(b)** Equipe pequena — há auxiliares que registram em campo. | DEC-27 / ADR-14 — perfil `auxiliar` (RN-18), gera BL-42 |
| 9 | Os PDFs emitidos usam **assinatura digital ICP-Brasil** ou basta o CREA impresso no documento? | **(a)** CREA/ART impressos apenas. | DEC-28 — sem módulo de assinatura na v1.0; HT-08 sem efeito |

## Bloco 2 — Regras de negócio e modelo de dados (~20 min)

| # | Pergunta ao cliente | Por que importa | Opções a apresentar |
|---|---|---|---|
| 10 | O engenheiro pode **sobrescrever manualmente** a Prioridade calculada a partir do Grau de Risco CMM (RN-04)? E "Prioridade 0" significa "sem prioridade definida" ou "não aplicável"? | Desbloqueia BL-15 diretamente. | (a) Prioridade sempre derivada, sem edição; (b) Sugerida pelo sistema e editável, com registro de quem alterou. |
| 1 | Existe **periodicidade obrigatória de re-inspeção** por grau de risco (ex.: Crítico ≤ 90 dias, Médio ≤ 180, Mínimo ≤ 1 ano)? | Define se o sistema precisa de calendário/alertas (RN-13). | (a) Não é obrigatório; (b) Sim, com os prazos X/Y/Z → gera nova funcionalidade de agenda. |
| 8 | As **medições do RFO** têm unidade fixa (m²) ou variam por contrato (unidades, horas, verba)? | Define se o campo de medição é numérico simples ou precisa de unidade configurável. | (a) Sempre m²; (b) Unidade livre por item de medição. |
| 5 | O **DOCX** é rascunho editável antes da entrega, ou o **PDF** já é o documento definitivo? | Define se docxtpl (BL-13) é obrigatório ou se o pipeline pode ser só WeasyPrint. | (a) DOCX é obrigatório (posição atual, RNF-04); (b) PDF direto basta → simplifica o pipeline e reduz a dependência do template Word. |

## Bloco 3 — Integrações e operação (~10 min)

| # | Pergunta ao cliente | Por que importa | Opções a apresentar |
|---|---|---|---|
| 4 | As fotos são salvas automaticamente numa **pasta monitorada** ou ficam só na área de transferência? | Confirma se a Opção C do §6 de arquitetura.md (agente desktop) chega a ser necessária. Com o editor de anotação interno (BL-31, já pronto), a tendência é (b). | (a) Pasta fixa → avaliar cliente desktop no futuro; (b) Clipboard/upload manual + editor interno já resolve. |
| 7 | Há necessidade de **integração com o CREA** para consultar/validar ARTs? | Define se entra uma integração externa no escopo. | (a) Não, os números são digitados manualmente; (b) Sim → nova tarefa, sujeita à existência de API pública. |
| — | **Backup** (RNF-08): qual frequência e onde guardar a cópia fora do host de produção? | Desbloqueia BL-29 com parâmetros concretos. | Sugestão técnica: dump diário do Postgres + espelho das fotos, retenção 30 dias, cópia em provedor distinto do Render. |

## Bloco 4 — Decisão pendente sobre IA (~5 min)

| Item | Pergunta ao cliente | Por que importa |
|---|---|---|
| 13 (parcial) | Qual **provedor de LLM** usar para as legendas assistidas (RF-15) e qual a política aceitável de retenção/uso dos dados enviados? As fotos e descrições são de imóveis de clientes. | É o bloqueio B-04, que prende BL-34 e BL-36 a BL-39. Envolve custo por chamada (150+ fotos por laudo) e risco de privacidade/LGPD (R-10, OWASP A02). Recomenda-se exigir do provedor: sem uso dos dados para treinamento e retenção zero ou mínima. |

---

## Encaminhamento após a reunião

1. Registrar as respostas em [ata-validacao-lacunas.md](ata-validacao-lacunas.md), substituindo os itens hoje marcados como "Pendente". — *feito para o Bloco 1 em 2026-09-10.*
2. Atualizar [estudo-do-contexto.md §9](../estudo-do-contexto.md#9-lacunas-a-esclarecer) e as regras afetadas (RN-04, RN-13, RNF-02, RNF-08). — *feito para RNF-02, RN-07 e a nova RN-18; RN-04/RN-13/RNF-08 seguem pendentes dos Blocos 2 e 3.*
3. Rebaixar ou remover B-01 (e B-04, se o item 13 for decidido) em [status.md](status.md#bloqueios-ativos). — *B-01 rebaixado a impacto Médio em 2026-09-10; B-04 segue ativo.*
4. Desbloquear BL-15 e fechar BL-18/HT-01 em [backlog-tarefas.md](backlog-tarefas.md) e [backlog-tarefas-humanas.md](backlog-tarefas-humanas.md). — *BL-18/HT-01 passaram a parciais; BL-15 continua presa à lacuna #10 (Bloco 2).*
