---
description: "Ativa o agente Engenheiro Backend para estender a modelagem de dados do fluxo de legendas assistidas por IA no Sistema de Automação de Relatórios Prediais."
---

## Contexto
Tarefa BL-36 do backlog em `00_docs/projeto/backlog-tarefas.md`. Esta tarefa é uma extensão técnica do fluxo de legendas assistidas por IA iniciado em BL-34/BL-35, com base no prompt-sistema fornecido pelo cliente (RF-15, RN-16, RN-17, DEC-21).

A implementação precisa apoiar três necessidades principais:
1. persistir a legenda gerada por IA e o estado de aprovação;
2. registrar o prompt/versão/base de contexto usada para a geração;
3. permitir pendências e alertas de informação ausente sem perder rastreabilidade.

## Tarefa
Assuma o papel de **Engenheiro Backend**.

1. Revise os modelos `Foto`, `Ocorrencia` e, se necessário, `Relatorio` para identificar onde o fluxo de legenda assistida por IA deve ser persistido.
2. Crie ou adapte os campos/entidades necessários para armazenar:
   - `legenda_ia_texto` (texto gerado)
   - `legenda_ia_status` (ex.: pendente, gerada, aprovada, rejeitada, editada)
   - `legenda_ia_pendencias` (lista/JSON de itens pendentes)
   - `legenda_ia_gerada_em`
   - `legenda_ia_aprovada_em`
   - `legenda_ia_prompt_id` ou referência ao prompt/versão empregada
3. Crie a tabela/entidade `prompts_ia` com campos mínimos para rastrear:
   - `nome`
   - `versao`
   - `texto`
   - `criado_em`
   - `ativo` 
4. Gere e aplique a migration Alembic correspondente.
5. Atualize os schemas Pydantic para expor os novos campos no fluxo de leitura e aceitar os campos necessários no fluxo de atualização do status/aprovação.
6. Ajuste o service/repository da foto para que a leitura e a atualização desses campos sejam feitas de forma consistente.
7. Escreva testes de integração cobrindo: criação de foto sem legenda, geração de legenda, aprovação e rejeição da legenda, e persistência de pendências.

## Saída Esperada
- Migration aplicada com os campos/entidade necessários para o fluxo de legendas assistidas por IA.
- Schemas e services atualizados para leitura e atualização do estado da legenda.
- Testes cobrindo os estados principais da legenda.

## Restrições
- Mantenha a estrutura compatível com a arquitetura já existente em `04_backend/app/`.
- Não implemente a geração da legenda em si nesta tarefa; foque em persistência e estados.
- Leia os arquivos antes de modificá-los.
