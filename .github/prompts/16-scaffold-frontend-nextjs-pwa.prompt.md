---
description: "Ativa o agente Engenheiro Frontend para criar o scaffold inicial do frontend Next.js 14 PWA do Sistema de Automação de Relatórios Prediais."
---
## Contexto
Tarefa BL-03 do backlog em `00_docs/projeto/backlog-tarefas.md`, Etapa 0 (Fundação Técnica) de `00_docs/projeto/ciclo-de-vida.md`.
Estrutura de rotas definida em `00_docs/arquitetura.md` Seção 7. Stack: Next.js 14 App Router + Tailwind CSS + shadcn/ui (DEC-06), PWA em vez de app nativo (DEC-03).
Protótipos de referência (wireframes HTML estáticos) já existem em `02_prototipos/` (`01-dashboard.html` a `06-laudo-preview.html`). O código do frontend deve ficar em `03_frontend/`, não em `frontend/` na raiz.
Esta tarefa é 100% desbloqueada — não depende de B-01 nem B-02.

## Tarefa
Assuma o papel de **Engenheiro Frontend** e crie o scaffold inicial do frontend:

1. Inicialize o projeto em `03_frontend/` com Next.js 14 (App Router, TypeScript, Tailwind CSS).
2. Configure shadcn/ui com o tema base.
3. Crie a estrutura de rotas conforme `00_docs/arquitetura.md` Seção 7:
   ```
   03_frontend/app/
     (auth)/
     edificacoes/
     contratos/
     inspecoes/[id]/visitas/
     inspecoes/[id]/ocorrencias/
     inspecoes/[id]/relatorio/
     dashboard/
   frontend/components/
   frontend/public/
   ```
4. Configure `03_frontend/public/manifest.json` para PWA (`display: standalone`, ícones, nome do app) conforme RNF-01/DEC-03.
5. Crie uma página inicial simples navegável entre as rotas criadas (placeholders), usando como referência visual os wireframes em `02_prototipos/`.
6. Adicione o serviço `frontend` ao `05_infra/docker-compose.yml` (criado no prompt 14), com build a partir de um `Dockerfile` de desenvolvimento simples (contexto de build: `../03_frontend`).
7. Rode o projeto localmente e valide que as rotas carregam sem erro.

## Saída Esperada
- Projeto Next.js 14 criado em `03_frontend/` com estrutura de rotas do App Router
- `03_frontend/public/manifest.json` configurado para PWA
- Página inicial navegável entre as rotas placeholder
- `03_frontend/Dockerfile` e serviço `frontend` no `05_infra/docker-compose.yml`
- Resumo: como rodar o frontend localmente, rotas criadas e próximos passos

## Restrições
- NÃO implemente ainda formulários ou integração com a API — isso é feito em tarefas subsequentes.
- NÃO alterne para app nativo ou outra stack — segue DEC-03 e DEC-06.
- NÃO copie o CSS de `02_prototipos/` sem adaptar aos componentes shadcn/ui.
- NÃO desvie da estrutura de pastas definida em `00_docs/arquitetura.md` sem justificar (o código deve ficar em `03_frontend/`, não em `frontend/` na raiz).
- Leia os arquivos antes de modificá-los.
