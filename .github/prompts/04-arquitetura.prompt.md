---
description: "Ativa o agente Arquiteto de Software para definir stack, modelo de dados, contratos de API e blueprint técnico da solução."
---
## Contexto
Estudo do contexto disponível em `00_docs/estudo-do-contexto.md`.
Domínio: sistema de fiscalização de obras/serviços de engenharia (relatórios, registros diários, medições).

## Tarefa
Assuma o papel de **Arquiteto de Software** e:

1. Revise `00_docs/estudo-do-contexto.md` para entender requisitos (RF/RNF) e entidades.
2. Defina a stack tecnológica com justificativas (ex.: Next.js + FastAPI + PostgreSQL, ou outra adequada).
3. Projete a arquitetura em camadas (ex.: MVC, hexagonal) com diagrama Mermaid.
4. Modele os dados: diagrama ER e descrição de cada entidade.
5. Especifique os contratos de API (endpoints, métodos, payloads, status codes).
6. Defina a estrutura de pastas do `src/`.
7. Registre as decisões como ADR-01, ADR-02...
8. Salve em `00_docs/arquitetura.md`.

## Saída Esperada
`00_docs/arquitetura.md` com stack, diagrama de arquitetura (Mermaid), modelo ER, tabela de endpoints, estrutura de pastas e ADRs.

## Restrições
- NÃO implemente código.
- NÃO escolha tecnologias sem justificar o trade-off em relação aos RNFs.
