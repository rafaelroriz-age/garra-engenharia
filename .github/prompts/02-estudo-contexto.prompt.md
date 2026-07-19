---
description: "Ativa o agente Estudo do Contexto para analisar os documentos convertidos e produzir o documento de entendimento consolidado do domínio."
---
## Contexto
Documentos convertidos disponíveis em `01_output-context/*.md`.
O domínio envolve relatórios de fiscalização de engenharia (Dynatest / Garra Engenharia).

## Tarefa
Assuma o papel de **Estudo do Contexto** e:

1. Leia todos os `.md` em `01_output-context/`.
2. Identifique o propósito do sistema, atores, entidades e seus atributos.
3. Extraia as regras de negócio (RN-01, RN-02...) implícitas nos documentos.
4. Liste requisitos funcionais (RF-01...) e não funcionais (RNF-01...).
5. Mapeie os fluxos de trabalho principais.
6. Registre lacunas como `[A ESCLARECER]`.
7. Salve o resultado em `00_docs/estudo-do-contexto.md`.

## Saída Esperada
`00_docs/estudo-do-contexto.md` com:
- Visão geral do domínio
- Atores e usuários
- Entidades e glossário
- Regras de negócio (RN-XX)
- Requisitos funcionais (RF-XX) e não funcionais (RNF-XX)
- Fluxos de trabalho principais
- Lacunas e questões em aberto

## Restrições
- NÃO assuma requisitos sem evidência nos documentos.
- NÃO escreva código ou arquitetura.
