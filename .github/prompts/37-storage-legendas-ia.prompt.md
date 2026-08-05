---
description: "Ativa o agente Engenheiro Backend para integrar o armazenamento e a rastreabilidade dos artefatos do fluxo de legendas assistidas por IA."
---

## Contexto
Tarefa BL-37 do backlog em `00_docs/projeto/backlog-tarefas.md`. Após a extensão da modelagem (BL-36), é preciso garantir que os artefatos do fluxo de legendas assistidas por IA sejam armazenados e rastreados de forma confiável, sem comprometer o uso atual do MinIO/S3.

## Tarefa
Assuma o papel de **Engenheiro Backend**.

1. Revise o módulo de storage já implementado em `04_backend/app/services/storage/` e o fluxo atual de upload de fotos.
2. Defina como o sistema deve persistir os artefatos do fluxo de legendas assistidas por IA:
   - texto da legenda gerada;
   - versão aprovada/rejeitada;
   - metadados como prompt usado, data e status;
   - se houver necessidade, arquivos auxiliares em MinIO/S3.
3. Implemente a persistência necessária sem quebrar o fluxo atual de upload de fotos.
4. Garanta que o storage e a lógica de metadata funcionem com a mesma abordagem S3-compatível já usada para fotos.
5. Crie ou adapte testes para confirmar que a legenda e os metadados são persistidos corretamente e que o fluxo continua funcional após upload.

## Saída Esperada
- Fluxo de storage/metadata para o fluxo de legendas assistidas por IA implementado.
- Persistência rastreável dos artefatos sem regressão do fluxo atual de upload de fotos.
- Testes cobrindo o armazenamento e a recuperação dos metadados.

## Restrições
- Não altere a lógica de upload de fotos já existente de forma incompatível com o fluxo atual.
- Preserve a compatibilidade com MinIO/S3 e o modelo atual de URL pré-assinada.
- Leia os arquivos antes de modificá-los.
