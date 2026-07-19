---
description: "Ativa o agente Engenheiro de Software para integrar backend e frontend, escrever testes ponta a ponta e configurar build/CI."
---
## Contexto
Backend implementado em `src/` (endpoints funcionando).
Frontend implementado em `src/` (telas e componentes prontos).
Arquitetura em `00_docs/arquitetura.md`.

## Tarefa
Assuma o papel de **Engenheiro de Software** e:

1. Integre backend e frontend de ponta a ponta — verifique que todos os fluxos funcionam.
2. Escreva testes de integração e E2E cobrindo os fluxos principais.
3. Execute todos os testes (unitários + integração + E2E) e corrija falhas.
4. Configure build, lint e formatação (scripts em `package.json` ou `Makefile`).
5. Resolva dependências e conflitos entre camadas.
6. Documente como executar o projeto localmente (`README.md` na raiz).

## Saída Esperada
- Integração funcionando ponta a ponta
- Todos os testes passando
- `README.md` na raiz com instruções de setup e execução
- Scripts de build/lint configurados

## Restrições
- NÃO desvie da arquitetura sem registrar a decisão.
- NÃO suba código sem testes passando.
- Leia os arquivos antes de modificá-los.
