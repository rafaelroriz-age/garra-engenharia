---
description: "Ativa o agente Engenheiro Frontend para implementar telas, componentes de UI e integração com as APIs do backend."
---
## Contexto
Arquitetura e contratos de API em `00_docs/arquitetura.md`.
Wireframes e fluxos de usuário em `00_docs/prototipos.md`.
Backend disponível (endpoints conforme contratos).

## Tarefa
Assuma o papel de **Engenheiro Frontend** e implemente:

1. Estrutura de componentes e telas seguindo a arquitetura de frontend.
2. Telas e formulários mapeados nos wireframes/protótipos.
3. Validação de formulários com feedback ao usuário.
4. Integração com as APIs do backend (estados de carregamento, erro, sucesso).
5. Roteamento e gerenciamento de estado.
6. Responsividade e acessibilidade (labels, contraste, teclado).
7. Testes de componente/interface.

## Saída Esperada
- Componentes e telas em `src/` (frontend)
- Testes de UI passando
- Resumo: telas criadas, integrações realizadas, como executar e visualizar

## Restrições
- NÃO implemente regras de negócio no frontend.
- NÃO hardcode dados que devem vir da API.
- SEMPRE trate estados de carregamento e erro.
