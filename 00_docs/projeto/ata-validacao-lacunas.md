---
title: Ata de validação parcial das lacunas — Sistema de Automação de Relatórios Prediais
type: gestao
status: draft
owner: Garra Engenharia
last_updated: 2026-09-10
---

# Ata de validação parcial das lacunas

## Fonte de validação

Esta atualização considera:

- as **respostas do cliente ao Bloco 1 da [pauta de validação](pauta-validacao-lacunas.md)**, coletadas em 2026-09-10 (lacunas #2, #3 e #9);
- o arquivo [00_docs/cliente/prompt-lado-cliente.md](../cliente/prompt-lado-cliente.md), que contém o prompt-sistema universal para transcrição e redação de legendas fotográficas técnicas;
- as decisões de arquitetura já registradas em [00_docs/projeto/decisoes.md](decisoes.md) (DEC-18, DEC-21, DEC-26, DEC-27 e DEC-28);
- a documentação técnica em [00_docs/estudo-do-contexto.md](../estudo-do-contexto.md) e [00_docs/arquitetura.md](../arquitetura.md).

## Resumo executivo

O prompt do cliente fornecido em [00_docs/cliente/prompt-lado-cliente.md](../cliente/prompt-lado-cliente.md) esclarece, de forma técnica e operacional, o fluxo de geração assistida de legendas por IA para fotos de inspeção/vistoria. Esse conteúdo resolve parcialmente a lacuna #13 do estudo de contexto, porque define o comportamento esperado do prompt-sistema, as regras de não invenção, a necessidade de rastreabilidade e a exigência de aprovação humana antes de qualquer legenda compor um relatório emitido.

O mesmo conteúdo não define, porém, o provedor de IA a ser usado nem a política de retenção/privacidade dos dados enviados a terceiros. Essas duas decisões continuam pendentes.

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
| 1 | Pendente | Não há decisão formal sobre periodicidade de re-inspeção por grau de risco. |
| 2 | **Resolvida (2026-09-10)** | O engenheiro trabalha com auxiliares que registram em campo. Gera o perfil `auxiliar` no RBAC (DEC-27) e a tarefa BL-42. |
| 3 | **Resolvida (2026-09-10)** | Não há necessidade de operação offline: sempre há 4G/Wi-Fi em campo. Offline completo permanece fora do escopo da v1.0 (DEC-26); RNF-02 fechado; risco R-07 encerrado. |
| 4 | Pendente | O prompt do cliente não define se as fotos do Lightshot devem ser monitoradas automaticamente por pasta ou se o fluxo permanecerá por clipboard/upload manual. |
| 5 | Pendente | O prompt do cliente não resolve se o DOCX gerado deve ser editável e final ou se o PDF final será o formato definitivo. |
| 6 | Resolvida | Resolvida previamente por DEC-18: o cliente terá acesso a um Portal do Cliente separado do perfil do engenheiro fiscal. |
| 7 | Pendente | Não há decisão formal sobre integração com o CREA. |
| 8 | Pendente | O prompt do cliente não define a flexibilidade do formato de medições do RFO. |
| 9 | **Resolvida (2026-09-10)** | Assinatura digital ICP-Brasil não é necessária; basta CREA/ART impressos no documento (DEC-28). HT-08 (obtenção de e-CPF) fica sem efeito para a v1.0. |
| 10 | Pendente | O prompt do cliente não responde se a prioridade pode ser sobrescrita manualmente pelo engenheiro. |
| 11 | Resolvida interina | DEC-18 define onboarding manual do usuário Cliente, feito pelo engenheiro fiscal, sem auto-cadastro público. |
| 12 | Resolvida interina | DEC-18 assume o vínculo de acesso do cliente de forma escopada por Responsável/Contrato, sem necessidade de criar uma conta isolada por edificação. |
| 13 | Parcialmente resolvida | O cliente forneceu o prompt-sistema universal e as regras de aprovação/ rastreabilidade; falta definir o provedor de IA e a política de retenção/privacidade. |

## Ações remanescentes

1. Manter a lacuna #13 como parcialmente resolvida até a definição do provedor de IA e da política de dados (bloqueio B-04).
2. Conduzir os **Blocos 2, 3 e 4** da [pauta](pauta-validacao-lacunas.md) para fechar as lacunas ainda abertas (#1, #4, #5, #7, #8, #10) e o destino do backup (RNF-08). A lacuna #10 é a que ainda prende BL-15 (RN-04).
3. Implementar BL-42 (perfil `auxiliar` no RBAC), gerada pela resposta à lacuna #2.
