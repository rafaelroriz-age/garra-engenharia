---
description: "Ativa o agente Engenheiro Backend para implementar APIs, modelos de banco de dados e regras de negócio."
---
## Contexto
Arquitetura definida em `00_docs/arquitetura.md` (stack, modelo de dados, contratos de API).
Regras de negócio em `00_docs/estudo-do-contexto.md`.
Estrutura de pastas do backend conforme `00_docs/arquitetura.md`.

## Tarefa
Assuma o papel de **Engenheiro Backend** e implemente:

1. Modelos/entidades e migrações de banco de dados.
2. Serviços com regras de negócio (RN-XX do estudo do contexto).
3. Endpoints da API conforme os contratos definidos (métodos, payloads, status codes).
4. Validação de entrada nos limites do sistema.
5. Autenticação/autorização se especificado.
6. Testes unitários e de integração para cada serviço/endpoint.

## Saída Esperada
- Código de backend em `src/` (modelos, serviços, controladores, migrações)
- Testes passando
- Resumo: endpoints criados, contratos atendidos, como executar e testar

## Restrições
- NÃO exponha dados sensíveis; siga OWASP Top 10.
- NÃO desvie dos contratos de API sem registrar a decisão.
- SEMPRE valide entradas.
