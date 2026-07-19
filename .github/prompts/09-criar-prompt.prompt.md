---
description: "Ativa o agente Criador de Prompts para gerar, refinar ou adaptar um prompt para qualquer agente especializado do projeto."
---
## Contexto
Agentes disponíveis em `.github/agents/`:
- `gestor-projeto-arquiteto-solucoes.agent.md`
- `conversor-documentos-md.agent.md`
- `estudo-contexto.agent.md`
- `organizador-pastas.agent.md`
- `arquiteto-software.agent.md`
- `prototipagem-documentacao-cliente.agent.md`
- `backend.agent.md`
- `frontend.agent.md`
- `engenheiro-software.agent.md`
- `criador-de-prompts.agent.md`

Prompts existentes em `.github/prompts/`.

## Tarefa
Assuma o papel de **Criador de Prompts** e:

1. Leia o `.agent.md` do agente-alvo solicitado.
2. Colete o contexto atual do projeto (artefatos em `00_docs/` e `01_output-context/`).
3. Crie um prompt rico e estruturado com: **Contexto**, **Tarefa**, **Saída Esperada**, **Restrições**.
4. Salve em `.github/prompts/<numero>-<nome>.prompt.md`.

## Saída Esperada
- Arquivo `.prompt.md` salvo em `.github/prompts/`
- Preview do prompt criado

## Restrições
- NÃO invente capacidades que os agentes não possuem.
- O prompt deve ser autocontido — quem o ler deve entender o contexto sem histórico anterior.
