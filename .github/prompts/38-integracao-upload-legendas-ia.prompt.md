---
description: "Ativa os agentes Engenheiro Backend e Engenheiro Frontend para integrar o fluxo de upload/edição de fotos com a geração de legendas assistidas por IA."
---

## Contexto
Tarefa BL-38 do backlog em `00_docs/projeto/backlog-tarefas.md`. Esta tarefa conecta o fluxo existente de upload de fotos (BL-11) ao novo fluxo de legendas assistidas por IA, permitindo que o usuário faça upload/editoração da foto e então gere a legenda técnica com apoio de IA.

## Tarefa
Assuma os papéis de **Engenheiro Backend** e **Engenheiro Frontend**.

### Backend
1. Crie endpoints ou adapte os existentes para iniciar a geração da legenda a partir de uma foto já persistida.
2. Receba o contexto da foto e do prompt-sistema para gerar a legenda técnica.
3. Retorne o texto gerado, status, pendências e metadados associados.
4. Permita o fluxo de aprovação/rejeição manual da legenda.

### Frontend
1. Integre no fluxo de upload de fotos um botão para “Gerar legenda com IA”.
2. Exiba o resultado da legenda em um campo editável, com indicação de pendências.
3. Permita salvar a legenda gerada e/ou aprovar/rejeitar o texto antes de finalizar.
4. Preserve o fluxo já existente de upload manual e clipboard paste.

## Saída Esperada
- Fluxo completo de upload → geração de legenda → aprovação/rejeição integrado ao sistema.
- UI simples e funcional para o usuário trabalhar com a sugestão de legenda.
- Testes de ponta a ponta do fluxo básico.

## Restrições
- Não altere a arquitetura de upload já existente de forma incompatível.
- Não implemente ainda a lógica de IA complexa; use os pontos de integração já previstos pelo backend.
- Leia os arquivos antes de modificá-los.
