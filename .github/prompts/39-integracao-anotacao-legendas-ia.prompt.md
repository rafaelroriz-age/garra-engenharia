---
description: "Ativa o agente Engenheiro Frontend para integrar o editor de anotação de fotos ao fluxo de aprovação de legendas assistidas por IA."
---

## Contexto
Tarefa BL-39 do backlog em `00_docs/projeto/backlog-tarefas.md`. Esta tarefa conecta o editor de anotação de fotos (BL-31) ao fluxo de legendas assistidas por IA, de modo que o usuário possa marcar a foto, gerar/editar a legenda e aprovar o resultado em um único fluxo.

## Tarefa
Assuma o papel de **Engenheiro Frontend**.

1. Revise o componente de anotação de fotos já implementado em BL-31 e o fluxo de legendas assistidas por IA em BL-38.
2. Integre a experiência para que o usuário possa:
   - fazer a anotação sobre a foto;
   - gerar ou revisar a legenda sugerida por IA;
   - editar manualmente a legenda;
   - aprovar, rejeitar ou marcar pendências.
3. Garanta uma experiência consistente em mobile e desktop.
4. Exiba para o usuário o estado atual da legenda de forma clara (gerada, aprovada, rejeitada, editada).

## Saída Esperada
- Fluxo visual integrado entre anotação, legenda assistida por IA e aprovação manual.
- UI clara para o usuário concluir o ciclo de foto → marcação → legenda → aprovação.
- Teste manual documentado com cenário básico.

## Restrições
- Não crie um fluxo separado do já existente; o objetivo é integrar o componente já implementado.
- Preserve a responsividade básica da interface.
- Leia os arquivos antes de modificá-los.
