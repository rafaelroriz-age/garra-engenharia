---
description: "Ativa o agente Engenheiro de Software para ler o escopo, escolher o modelo de ciclo de vida, definir etapas, documentar requisitos detalhados, montar cronograma, ordenar o backlog de tarefas de forma crescente e gerar os prompts das tarefas iniciais."
---
## Contexto
Projeto: Sistema de Automação de Relatórios Prediais — Garra Engenharia.
Documentação de gestão consolidada em `00_docs/projeto/`:
- [escopo.md](../../00_docs/projeto/escopo.md) — o que está dentro/fora do escopo, premissas, restrições e critérios de aceitação da v1.0
- [decisoes.md](../../00_docs/projeto/decisoes.md) — decisões arquiteturais já aprovadas (DEC-01 a DEC-07)
- [riscos.md](../../00_docs/projeto/riscos.md) — riscos identificados
- [status.md](../../00_docs/projeto/status.md) — fases já esboçadas (1 a 9) e bloqueios ativos (B-01, B-02, B-03)

Conhecimento de domínio em [estudo-do-contexto.md](../../00_docs/estudo-do-contexto.md) (regras de negócio RN-01 a RN-13, requisitos funcionais RF-01 a RF-12, requisitos não funcionais RNF-01 a RNF-08, lacunas `[A ESCLARECER]`).
Arquitetura técnica aprovada em [arquitetura.md](../../00_docs/arquitetura.md) (stack, modelo de dados, API, ADRs).

O projeto ainda não iniciou a implementação. Nenhum código existe em `04_backend/` ou `03_frontend/` até o momento.

## Tarefa
Assuma o papel de **Engenheiro de Software** e execute, nesta ordem, o planejamento de execução do projeto:

1. **Leia o escopo** (`escopo.md`) e os demais documentos de gestão e arquitetura listados no Contexto para entender o que deve ser entregue na v1.0, o que está fora de escopo e quais restrições/premissas se aplicam.
2. **Escolha o modelo de ciclo de vida de desenvolvimento** (ex.: incremental, iterativo/Scrum, cascata, V-model) mais adequado a este projeto, considerando: equipe pequena, existência de lacunas `[A ESCLARECER]` ainda não validadas com o cliente, dependência de templates Word ainda não entregues (bloqueios B-01/B-02), e a necessidade de entregar valor cedo (ex.: geração de relatório fiel ao template). Justifique a escolha por escrito e registre-a como nova entrada em `00_docs/projeto/decisoes.md`.
3. **Separe as etapas do ciclo de vida escolhido**, conciliando-as com as fases já esboçadas em `status.md` (validação de lacunas, prototipagem de templates, backend, frontend, integração/testes, deploy).
4. **Documente cada etapa com requisitos detalhados**, vinculando explicitamente cada etapa aos RF/RNF/RN correspondentes do `estudo-do-contexto.md` e aos ADRs/DEC relevantes de `arquitetura.md`/`decisoes.md`.
5. **Defina um cronograma**, com duração estimada por etapa, marcos (milestones) e dependências entre etapas (ex.: prototipagem de templates depende da entrega dos arquivos `.docx` do cliente — bloqueio B-02).
6. **Separe as tarefas de cada etapa em ordem crescente** de complexidade/dependência (das tarefas mais simples e desbloqueadas para as mais complexas e dependentes), formando um backlog sequencial e rastreável.
7. **Crie os prompts das tarefas iniciais** (as primeiras tarefas do backlog que já estão desbloqueadas, sem depender de validação do cliente) como novos arquivos em `.github/prompts/`, seguindo exatamente o mesmo padrão dos prompts existentes (frontmatter `description` + seções `## Contexto`, `## Tarefa`, `## Saída Esperada`, `## Restrições`), numerados sequencialmente a partir de `14-`. **Apenas crie esses prompts — não os execute.**

## Saída Esperada
- `00_docs/projeto/ciclo-de-vida.md` — modelo de ciclo de vida escolhido (com justificativa), etapas definidas e requisitos detalhados por etapa (RF/RNF/RN mapeados)
- `00_docs/projeto/cronograma.md` — cronograma com duração estimada, marcos e dependências por etapa
- `00_docs/projeto/backlog-tarefas.md` — lista de tarefas ordenada de forma crescente (complexidade/dependência), com identificação de quais estão bloqueadas (B-01/B-02/B-03) e quais estão prontas para iniciar
- Nova entrada `DEC-08` (ou próximo número disponível) em `00_docs/projeto/decisoes.md` registrando a escolha do modelo de ciclo de vida
- Novos arquivos `.github/prompts/14-*.prompt.md`, `15-*.prompt.md` etc. — um por tarefa inicial desbloqueada, prontos para serem executados posteriormente
- `00_docs/projeto/status.md` atualizado com a nova fase de planejamento concluída

## Restrições
- NÃO implemente código nesta tarefa — o objetivo é exclusivamente planejamento e criação de prompts.
- NÃO crie prompts para tarefas que dependam de lacunas `[A ESCLARECER]` ainda não validadas com o cliente (bloqueio B-01) ou de templates ainda não entregues (bloqueio B-02); priorize apenas tarefas já desbloqueadas.
- NÃO altere `00_docs/estudo-do-contexto.md` ou `00_docs/arquitetura.md` — apenas referencie-os.
- Mantenha o mesmo padrão de frontmatter e estrutura (Contexto/Tarefa/Saída Esperada/Restrições) usado nos prompts existentes em `.github/prompts/`.
- Leia os arquivos antes de modificá-los.
