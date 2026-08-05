---
title: Ata de validação parcial das lacunas — Sistema de Automação de Relatórios Prediais
type: gestao
status: draft
owner: Garra Engenharia
last_updated: 2026-07-29
---

# Ata de validação parcial das lacunas

## Fonte de validação

Esta atualização considera:

- o arquivo [00_docs/cliente/prompt-lado-cliente.md](../cliente/prompt-lado-cliente.md), que contém o prompt-sistema universal para transcrição e redação de legendas fotográficas técnicas;
- as decisões de arquitetura já registradas em [00_docs/projeto/decisoes.md](decisoes.md) (DEC-18 e DEC-21);
- a documentação técnica em [00_docs/estudo-do-contexto.md](../estudo-do-contexto.md) e [00_docs/arquitetura.md](../arquitetura.md).

## Resumo executivo

O prompt do cliente fornecido em [00_docs/cliente/prompt-lado-cliente.md](../cliente/prompt-lado-cliente.md) esclarece, de forma técnica e operacional, o fluxo de geração assistida de legendas por IA para fotos de inspeção/vistoria. Esse conteúdo resolve parcialmente a lacuna #13 do estudo de contexto, porque define o comportamento esperado do prompt-sistema, as regras de não invenção, a necessidade de rastreabilidade e a exigência de aprovação humana antes de qualquer legenda compor um relatório emitido.

O mesmo conteúdo não define, porém, o provedor de IA a ser usado nem a política de retenção/privacidade dos dados enviados a terceiros. Essas duas decisões continuam pendentes.

## Status das lacunas

| # | Status | Observação |
|---|---|---|
| 1 | Pendente | Não há decisão formal sobre periodicidade de re-inspeção por grau de risco. |
| 2 | Pendente | O prompt do cliente não responde se o engenheiro trabalha sozinho ou com auxiliares. A decisão de multiusuário ainda precisa ser confirmada. |
| 3 | Pendente | O prompt do cliente não resolve a necessidade de operação offline completa em campo. |
| 4 | Pendente | O prompt do cliente não define se as fotos do Lightshot devem ser monitoradas automaticamente por pasta ou se o fluxo permanecerá por clipboard/upload manual. |
| 5 | Pendente | O prompt do cliente não resolve se o DOCX gerado deve ser editável e final ou se o PDF final será o formato definitivo. |
| 6 | Resolvida | Resolvida previamente por DEC-18: o cliente terá acesso a um Portal do Cliente separado do perfil do engenheiro fiscal. |
| 7 | Pendente | Não há decisão formal sobre integração com o CREA. |
| 8 | Pendente | O prompt do cliente não define a flexibilidade do formato de medições do RFO. |
| 9 | Pendente | Não há decisão formal sobre uso de assinatura digital ICP-Brasil. |
| 10 | Pendente | O prompt do cliente não responde se a prioridade pode ser sobrescrita manualmente pelo engenheiro. |
| 11 | Resolvida interina | DEC-18 define onboarding manual do usuário Cliente, feito pelo engenheiro fiscal, sem auto-cadastro público. |
| 12 | Resolvida interina | DEC-18 assume o vínculo de acesso do cliente de forma escopada por Responsável/Contrato, sem necessidade de criar uma conta isolada por edificação. |
| 13 | Parcialmente resolvida | O cliente forneceu o prompt-sistema universal e as regras de aprovação/ rastreabilidade; falta definir o provedor de IA e a política de retenção/privacidade. |

## Ações remanescentes

1. Manter a lacuna #13 como parcialmente resolvida até a definição do provedor de IA e da política de dados.
2. Reabrir a validação formal das lacunas de negócio/arquitetura que ainda não foram respondidas (#1, #2, #3, #4, #5, #7, #8, #9, #10).
3. Atualizar o estudo de contexto e o backlog quando houver respostas formais do cliente.
