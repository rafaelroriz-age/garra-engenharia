---
title: Pauta da sessão de validação das lacunas [A ESCLARECER] — HT-01 / BL-18
type: gestao
status: draft
owner: Garra Engenharia
related:
  - 00_docs/estudo-do-contexto.md
  - 00_docs/projeto/ata-validacao-lacunas.md
  - 00_docs/projeto/backlog-tarefas-humanas.md
last_updated: 2026-09-17
---

# Pauta — sessão de validação das lacunas com o cliente

> **Status em 2026-09-17:** o **Bloco 1 foi respondido** em 2026-09-10 (#3 = a, #2 = b, #9 = a → DEC-26/27/28) e os **Blocos 2 e 3 foram encerrados** em 2026-09-17 (#10 = b, #1 = a, #8 = b, #5 = a, #4 = b, #7 = a → [DEC-29](decisoes.md#dec-29--fechamento-das-lacunas-remanescentes-blocos-2-e-3-encerramento-do-bloqueio-b-01)). Tudo registrado em [ata-validacao-lacunas.md](ata-validacao-lacunas.md). **O bloqueio B-01 está encerrado.** Resta apenas o **Bloco 4** (provedor de IA, bloqueio B-04).

**Objetivo:** fechar as lacunas remanescentes de [estudo-do-contexto.md §9](../estudo-do-contexto.md#9-lacunas-a-esclarecer) e destravar o bloqueio B-01 — *concluído em 2026-09-17; BL-15 desbloqueada*.

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

## Bloco 2 — Regras de negócio e modelo de dados — ✅ ENCERRADO EM 2026-09-17 (DEC-29)

| # | Pergunta ao cliente | Posição adotada | Efeito |
|---|---|---|---|
| 10 | O engenheiro pode **sobrescrever manualmente** a Prioridade calculada a partir do Grau de Risco CMM (RN-04)? E "Prioridade 0" significa "sem prioridade definida" ou "não aplicável"? | **(b)** Sugerida pelo sistema e editável, com registro de quem alterou. "Prioridade 0" = **não aplicável**. | **BL-15 desbloqueada**; RN-04 fechada |
| 1 | Existe **periodicidade obrigatória de re-inspeção** por grau de risco? | **(a)** Não é obrigatória — recomendação técnica caso a caso no laudo. | RN-13 fechada; sem agenda/alertas na v1.0 |
| 8 | As **medições do RFO** têm unidade fixa (m²) ou variam por contrato? | **(b)** Unidade livre por item de medição. | Zero mudança — `VisitaMedicao.unidade` já é texto livre |
| 5 | O **DOCX** é rascunho editável antes da entrega, ou o **PDF** já é o documento definitivo? | **(a)** DOCX obrigatório (mantém RNF-04). | BL-13 permanece válida |

## Bloco 3 — Integrações e operação — ✅ ENCERRADO EM 2026-09-17 (DEC-29), exceto backup

| # | Pergunta ao cliente | Posição adotada | Efeito |
|---|---|---|---|
| 4 | As fotos são salvas automaticamente numa **pasta monitorada** ou ficam só na área de transferência? | **(b)** Clipboard/upload manual + editor interno (RF-14/BL-31). | Agente desktop (Opção C do §6 de `arquitetura.md`) sai do escopo |
| 7 | Há necessidade de **integração com o CREA** para consultar/validar ARTs? | **(a)** Não — números digitados manualmente. | Sem integração externa na v1.0 |
| — | **Backup** (RNF-08): qual frequência e onde guardar a cópia fora do host de produção? | 🔴 **Ainda em aberto** — não integra B-01. Sugestão técnica: dump diário do Postgres + espelho das fotos, retenção 30 dias, cópia em provedor distinto do Render. | BL-29 já entregue; falta só escolher o destino externo |

## Bloco 4 — Decisão pendente sobre IA (~5 min)

| Item | Pergunta ao cliente | Por que importa |
|---|---|---|
| 13 (parcial) | Qual **provedor de LLM** usar para as legendas assistidas (RF-15) e qual a política aceitável de retenção/uso dos dados enviados? As fotos e descrições são de imóveis de clientes. | É o bloqueio B-04, que prende BL-34 e BL-36 a BL-39. Envolve custo por chamada (150+ fotos por laudo) e risco de privacidade/LGPD (R-10, OWASP A02). Recomenda-se exigir do provedor: sem uso dos dados para treinamento e retenção zero ou mínima. |

---

## Encaminhamento após a reunião

1. Registrar as respostas em [ata-validacao-lacunas.md](ata-validacao-lacunas.md), substituindo os itens marcados como "Pendente". — *concluído: Bloco 1 em 2026-09-10, Blocos 2 e 3 em 2026-09-17.*
2. Atualizar [estudo-do-contexto.md §9](../estudo-do-contexto.md#9-lacunas-a-esclarecer) e as regras afetadas (RN-04, RN-13, RNF-02, RNF-08). — *concluído para RN-04, RN-13, RNF-02, RN-07 e RN-18; só RNF-08 (destino do backup) segue aberto.*
3. Rebaixar ou remover B-01 (e B-04, se o item 13 for decidido) em [status.md](status.md#bloqueios-ativos). — *B-01 **encerrado** em 2026-09-17 (DEC-29); B-04 segue ativo.*
4. Desbloquear BL-15 e fechar BL-18/HT-01 em [backlog-tarefas.md](backlog-tarefas.md) e [backlog-tarefas-humanas.md](backlog-tarefas-humanas.md). — *concluído em 2026-09-17: BL-15 🟢 desbloqueada, BL-18 e HT-01 ✅.*
