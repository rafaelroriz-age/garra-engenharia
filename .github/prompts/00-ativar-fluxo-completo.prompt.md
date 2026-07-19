---
description: "Ativa o fluxo completo do projeto: invoca o Gestor de Projeto para orquestrar todos os agentes especializados na sequência correta, do contexto até a entrega final."
---
## Contexto
O projeto está localizado em `c:\Users\dynatest\OneDrive - Dynatest Engenharia\Área de Trabalho\Novos_proj\garra-engenharia`.
Documentos de origem disponíveis em `01_output-context/`.
Artefatos já convertidos podem estar em `01_output-context/*.md` e `00_docs/`.

## Tarefa
Assuma o papel de **Gestor de Projeto / Arquiteto de Soluções** e conduza o projeto completo:

1. Leia todos os artefatos disponíveis em `01_output-context/` e `00_docs/` para entender o estado atual.
2. Identifique em qual fase o projeto se encontra.
3. Execute o fluxo de agentes na sequência:
   - **Conversor de Documentos** → converta todos os documentos de `01_output-context/` para `.md`
   - **Estudo do Contexto** → extraia regras de negócio, entidades e requisitos
   - **Organizador de Pastas** → estruture o repositório
   - **Arquiteto de Software** → defina stack, modelo de dados e contratos de API
   - **Prototipagem e Documentação para Cliente** → gere wireframes e documentação para validação
   - **Engenheiro Backend** + **Engenheiro Frontend** → implemente a solução
   - **Engenheiro de Software** → integre e teste
   - **Prototipagem e Documentação para Cliente** → documentação final de entrega
4. Registre decisões em `00_docs/projeto/decisoes.md` e mantenha `00_docs/projeto/status.md` atualizado.

## Saída Esperada
- `00_docs/projeto/escopo.md` — escopo definido
- `00_docs/projeto/status.md` — progresso atualizado após cada fase
- `00_docs/projeto/decisoes.md` — log de decisões
- Todos os artefatos de cada agente nos seus respectivos diretórios

## Restrições
- Não pule fases sem registrar o motivo.
- Não implemente código sem arquitetura aprovada.
- Confirme com o usuário antes de avançar para implementação.
