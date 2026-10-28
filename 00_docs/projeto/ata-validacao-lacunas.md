---
title: Ata de validação parcial das lacunas — Sistema de Automação de Relatórios Prediais
type: gestao
status: draft
owner: Garra Engenharia
last_updated: 2026-09-17
---

# Ata de validação das lacunas

## Fonte de validação

Esta atualização considera:

- o **encerramento dos Blocos 2 e 3 da [pauta de validação](pauta-validacao-lacunas.md)** em 2026-09-17 (lacunas #1, #4, #5, #7, #8 e #10), registrado em [DEC-29](decisoes.md#dec-29--fechamento-das-lacunas-remanescentes-blocos-2-e-3-encerramento-do-bloqueio-b-01) — **bloqueio B-01 encerrado**;
- as **respostas do cliente ao Bloco 1 da [pauta de validação](pauta-validacao-lacunas.md)**, coletadas em 2026-09-10 (lacunas #2, #3 e #9);
- o arquivo [00_docs/cliente/prompt-lado-cliente.md](../cliente/prompt-lado-cliente.md), que contém o prompt-sistema universal para transcrição e redação de legendas fotográficas técnicas;
- as decisões de arquitetura já registradas em [00_docs/projeto/decisoes.md](decisoes.md) (DEC-18, DEC-21, DEC-26, DEC-27, DEC-28 e DEC-29);
- a documentação técnica em [00_docs/estudo-do-contexto.md](../estudo-do-contexto.md) e [00_docs/arquitetura.md](../arquitetura.md).

## Resumo executivo

O prompt do cliente fornecido em [00_docs/cliente/prompt-lado-cliente.md](../cliente/prompt-lado-cliente.md) esclarece, de forma técnica e operacional, o fluxo de geração assistida de legendas por IA para fotos de inspeção/vistoria. Esse conteúdo resolve parcialmente a lacuna #13 do estudo de contexto, porque define o comportamento esperado do prompt-sistema, as regras de não invenção, a necessidade de rastreabilidade e a exigência de aprovação humana antes de qualquer legenda compor um relatório emitido.

O mesmo conteúdo não define, porém, o provedor de IA a ser usado nem a política de retenção/privacidade dos dados enviados a terceiros. Essas duas decisões continuam pendentes (bloqueio **B-04**, fora de B-01).

## Sessão de 2026-09-17 — fechamento dos Blocos 2 e 3 (DEC-29)

O gestor do projeto declarou as lacunas remanescentes encerradas e determinou o desbloqueio de B-01. Para cada uma foi adotada a opção de **menor impacto sobre o que já está entregue** — nenhuma exige refazer código existente. Justificativa completa em [DEC-29](decisoes.md#dec-29--fechamento-das-lacunas-remanescentes-blocos-2-e-3-encerramento-do-bloqueio-b-01).

| # | Pergunta | Posição adotada | Efeito |
|---|---|---|---|
| 10 | A Prioridade derivada do Grau de Risco pode ser sobrescrita? O que é "Prioridade 0"? | **(b)** Sugerida pelo sistema (Crítico=5, Médio=3, Mínimo=1) e **editável** pelo engenheiro, com registro de quem alterou e do valor sugerido. **Prioridade 0 = "não aplicável"** (ocorrência Conforme ou sistema "Não se Aplica" por RN-10). | Desbloqueia **BL-15**; RN-04 fechada |
| 1 | Há periodicidade obrigatória de re-inspeção por grau de risco? | **(a)** Não. O prazo de retorno é recomendação técnica escrita pelo engenheiro no laudo, caso a caso. | RN-13 fechada; sem módulo de agenda/alertas na v1.0 |
| 8 | As medições do RFO têm unidade fixa (m²)? | **(b)** Unidade **livre por item** (m², unidade, hora, verba). | Nenhuma mudança — `VisitaMedicao.unidade` já é texto livre |
| 5 | O DOCX é rascunho editável obrigatório ou o PDF já é definitivo? | **(a)** DOCX **obrigatório** como rascunho editável. | RNF-04 mantido; BL-13 permanece válida |
| 4 | As fotos vêm de pasta monitorada ou de clipboard/upload? | **(b)** Clipboard/upload manual + editor de anotação interno (RF-14/BL-31). | Agente desktop sai do escopo (§6 de `arquitetura.md`) |
| 7 | Há integração com o CREA para validar ARTs? | **(a)** Não — números digitados manualmente. | Integração externa fora do escopo |

## Sessão de 2026-09-10 — respostas ao Bloco 1 da pauta (alto impacto arquitetural)

O cliente respondeu às três perguntas de maior impacto arquitetural da [pauta](pauta-validacao-lacunas.md#bloco-1--alto-impacto-arquitetural-prioridade-máxima-25-min). Os Blocos 2, 3 e 4 continuam pendentes.

| # | Pergunta | Resposta do cliente | Decisão gerada |
|---|---|---|---|
| 3 | O registro de ocorrências/fotos precisa funcionar sem internet em campo? | **(a) Não** — há sempre 4G/Wi-Fi no campo. A posição arquitetural atual (Seção 10.8 de `arquitetura.md`) é mantida: sem Service Worker de escrita, sem IndexedDB, sem fila de sincronização. | [DEC-26](decisoes.md#dec-26--operação-offline-completa-fora-do-escopo-da-v10-pwa-online-first) |
| 2 | O engenheiro trabalha sozinho ou há auxiliares que também registram em campo? | **(b) Equipe pequena** — existem auxiliares que também registram ocorrências e fotos em campo. É necessário um terceiro perfil, com escrita limitada e sem poder emitir relatório nem administrar usuários. | [DEC-27](decisoes.md#dec-27--rbac-terceiro-perfil-auxiliar-com-escrita-limitada-e-autoria-rastreável) → BL-42 |
| 9 | Os PDFs emitidos usam assinatura digital ICP-Brasil ou basta o CREA impresso? | **(a) CREA impresso apenas** — a responsabilidade técnica é registrada pelo número do CREA e pela ART no corpo do documento. ICP-Brasil não é exigido pelos contratantes atuais. | [DEC-28](decisoes.md#dec-28--assinatura-dos-pdfs-emitidos-creaart-impressos-sem-icp-brasil-na-v10) |

## Status das lacunas

| # | Status | Observação |
|---|---|---|
| 1 | **Resolvida (2026-09-17)** | Não há periodicidade obrigatória de re-inspeção; o prazo de retorno é recomendação técnica caso a caso, escrita no laudo (DEC-29). RN-13 fechada. |
| 2 | **Resolvida (2026-09-10)** | O engenheiro trabalha com auxiliares que registram em campo. Gera o perfil `auxiliar` no RBAC (DEC-27) e a tarefa BL-42. |
| 3 | **Resolvida (2026-09-10)** | Não há necessidade de operação offline: sempre há 4G/Wi-Fi em campo. Offline completo permanece fora do escopo da v1.0 (DEC-26); RNF-02 fechado; risco R-07 encerrado. |
| 4 | **Resolvida (2026-09-17)** | O fluxo permanece por clipboard/upload manual, com a marcação feita no editor interno (RF-14/BL-31). Sem monitoramento de pasta (DEC-29). |
| 5 | **Resolvida (2026-09-17)** | O DOCX continua obrigatório como rascunho editável antes da entrega; RNF-04 inalterado (DEC-29). |
| 6 | Resolvida | Resolvida previamente por DEC-18: o cliente terá acesso a um Portal do Cliente separado do perfil do engenheiro fiscal. |
| 7 | **Resolvida (2026-09-17)** | Sem integração com o CREA — os números de CREA/ART são digitados manualmente (DEC-29). |
| 8 | **Resolvida (2026-09-17)** | A unidade da medição do RFO é livre por item (m², unidade, hora, verba) — `VisitaMedicao.unidade` já suporta (DEC-29). |
| 9 | **Resolvida (2026-09-10)** | Assinatura digital ICP-Brasil não é necessária; basta CREA/ART impressos no documento (DEC-28). HT-08 (obtenção de e-CPF) fica sem efeito para a v1.0. |
| 10 | **Resolvida (2026-09-17)** | A Prioridade é sugerida pelo Grau de Risco e permanece editável pelo engenheiro, com registro do ajuste; "Prioridade 0" significa "não aplicável" (DEC-29). **Desbloqueia BL-15.** |
| 11 | Resolvida interina | DEC-18 define onboarding manual do usuário Cliente, feito pelo engenheiro fiscal, sem auto-cadastro público. |
| 12 | Resolvida interina | DEC-18 assume o vínculo de acesso do cliente de forma escopada por Responsável/Contrato, sem necessidade de criar uma conta isolada por edificação. |
| 13 | Parcialmente resolvida | O cliente forneceu o prompt-sistema universal e as regras de aprovação/ rastreabilidade; falta definir o provedor de IA e a política de retenção/privacidade. |

## Ações remanescentes

1. Manter a lacuna #13 como parcialmente resolvida até a definição do provedor de IA e da política de dados (bloqueio **B-04**, único bloqueio de requisitos ainda ativo — Bloco 4 da pauta).
2. Definir o destino externo do backup (RNF-08), item avulso do Bloco 3 que não integra B-01 — os scripts de BL-29 já rodam com dump diário e retenção, falta só escolher o provedor da cópia externa.
3. Implementar **BL-15** (prioridade sugerida + sobrescrita rastreável), desbloqueada por DEC-29.
4. ~~Implementar BL-42 (perfil `auxiliar` no RBAC)~~ — concluída em 2026-09-10.
