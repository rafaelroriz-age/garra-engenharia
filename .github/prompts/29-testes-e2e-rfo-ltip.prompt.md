---
description: "Ativa o agente Engenheiro de Software para implementar os testes E2E dos fluxos RFO e LTIP do Sistema de Automação de Relatórios Prediais."
---
## Contexto
Tarefa BL-21 do backlog em `00_docs/projeto/backlog-tarefas.md`, Etapa 6/7 (Integração, Testes e Deploy) de `00_docs/projeto/ciclo-de-vida.md`. Depende das Etapas 3 e 4 estarem implementadas (BL-08 a BL-11, BL-14, BL-16).
Requisito RNF-06 de `00_docs/estudo-do-contexto.md`: performance de geração de relatório e, de forma mais ampla, confiabilidade dos fluxos ponta a ponta.
Fluxos principais documentados em `00_docs/estudo-do-contexto.md` Seção 8 (Fluxo 1 — RFO, Fluxo 2 — LTIP). Diagramas de sequência dos fluxos críticos em `00_docs/arquitetura.md` Seção 10.6.
Frontend em `03_frontend/` (Next.js 14), backend em `04_backend/` (FastAPI).

## Tarefa
Assuma o papel de **Engenheiro de Software** e:

1. Escolha e configure a ferramenta de teste E2E para o frontend (ex.: Playwright, já presente no ecossistema de ferramentas do projeto) apontando para uma instância local do sistema (`05_infra/docker-compose.yml`).
2. Implemente o teste E2E do **Fluxo 1 — RFO** (`00_docs/estudo-do-contexto.md` Seção 8): cadastra edificação → cadastra contrato RFO → cria visita com equipe/serviços/medições → anexa foto → dispara geração de relatório → valida que o job conclui e o download fica disponível.
3. Implemente o teste E2E do **Fluxo 2 — LTIP**: cadastra edificação → cadastra contrato LTIP → registra ocorrências em múltiplos sistemas prediais com fotos → valida o dashboard de saúde (BL-16) → dispara geração de laudo → valida conclusão do job.
4. Rode os testes contra o ambiente local (`docker-compose.yml`) e corrija falhas de integração encontradas entre backend e frontend.
5. Adicione os testes E2E ao workflow `ci.yml` (ou a um workflow dedicado), documentando o comando de execução.
6. Documente no `README.md` da raiz (ou em `03_frontend/README.md`/`04_backend/README.md`) como rodar os testes E2E localmente.

## Saída Esperada
- Testes E2E dos Fluxos 1 (RFO) e 2 (LTIP) implementados e passando localmente
- Integração ao CI (ou instruções claras de execução manual, caso a integração ao CI seja adiada)
- Resumo: ferramenta escolhida, comandos de execução, falhas de integração encontradas e corrigidas

## Restrições
- NÃO suba testes E2E quebrados ou instáveis (flaky) sem investigar a causa raiz.
- NÃO desvie da arquitetura documentada sem registrar a decisão em `00_docs/projeto/decisoes.md`.
- Leia os arquivos antes de modificá-los.
