---
title: Índice da documentação
type: knowledge
status: draft
owner: Garra Engenharia
related:
  - README.md
  - 00_docs/_preparo/03_classificacao.md
tags: [indice, documentacao, mapa]
last_updated: 2026-11-03
---

<!-- ai-summary
System: índice de toda a documentação do monorepo da Garra Engenharia, uma linha por documento.
Flow: visão geral -> arquitetura e dados -> operação -> requisitos -> gestão -> cliente -> insumos -> agentes e automação.
Owner: Garra Engenharia.
Status: draft — criado na D04 (2026-11-03); o veredito de cada documento está em _preparo/03_classificacao.md e a verificação final é a D05.
-->

# Índice da documentação

Sistema web (PWA) da Garra Engenharia para automatizar a produção de relatórios técnicos de engenharia predial (RFO, LTIP e relatório fotográfico). Visão geral e início rápido: [README da raiz](../README.md).

**Legenda:** **vivo** = mantido atualizado · **registro** = retrato de uma data, não se reescreve · **insumo** = material de origem, não se reescreve · † = documento de gestão compartilhado, atualizado só no fechamento de lote (`BACKLOG.md`).

## Visão geral e arquitetura

| Documento | Tipo | Conteúdo |
|---|---|---|
| [../README.md](../README.md) | vivo | Objetivo do sistema, mapa das pastas e início rápido |
| [arquitetura.md](arquitetura.md) | vivo | Estado da implementação (§0), stack, diagramas, ER, contratos de API, geração de relatório, estrutura de pastas, ADR-01 a ADR-16, system design |
| [dicionario-de-dados.md](dicionario-de-dados.md) | vivo | As 18 tabelas, coluna a coluna, e as 6 migrations Alembic |
| [configuracao.md](configuracao.md) | vivo | Variáveis de ambiente do backend, frontend, compose, E2E e Render |

## Desenvolvimento e operação

| Documento | Tipo | Conteúdo |
|---|---|---|
| [guia-desenvolvimento.md](guia-desenvolvimento.md) | vivo | Roteiro para instalar, rodar e testar o monorepo de ponta a ponta |
| [guia-contribuicao.md](guia-contribuicao.md) | vivo | Pastas, branches, commits, PR, convenções de documentação e fluxo do backlog-auto |
| [../04_backend/README.md](../04_backend/README.md) | vivo | Backend FastAPI: estrutura, migrations, seed do gabarito, templates, marca, auth, storage, testes |
| [../04_backend/alembic/README](../04_backend/alembic/README) | vivo | Texto padrão do Alembic (configuração assíncrona) |
| [../04_backend/templates/contracts/contrato_revisado_template.placeholders.md](../04_backend/templates/contracts/contrato_revisado_template.placeholders.md) | vivo | Os 23 campos do template `docxtpl` do contrato revisado |
| [../03_frontend/README.md](../03_frontend/README.md) | vivo | Frontend Next.js: estrutura, rotas, comandos, notas de marca e testes E2E |
| [../05_infra/README.md](../05_infra/README.md) | vivo | Docker Compose local, VPS com Nginx, backup/restore e deploy no Render |
| [../.github/pull_request_template.md](../.github/pull_request_template.md) | vivo | Checklist obrigatório de PR |
| [projeto/plano-gestao-configuracao.md](projeto/plano-gestao-configuracao.md) | vivo | Git, branches (DEC-22), CI/CD, deploy, rollback e backup |

## Requisitos e escopo

| Documento | Tipo | Conteúdo |
|---|---|---|
| [estudo-do-contexto.md](estudo-do-contexto.md) | vivo | Domínio, atores, entidades, glossário, RN/RF/RNF, fluxos e lacunas |
| [projeto/escopo.md](projeto/escopo.md) | vivo | Dentro e fora do escopo e critérios de aceite da v1.0 |
| [projeto/resumo-executivo.md](projeto/resumo-executivo.md) | vivo | Problema, solução, benefícios e estado atual, para público não técnico |

## Gestão do projeto

| Documento | Tipo | Conteúdo |
|---|---|---|
| [projeto/status.md](projeto/status.md) † | vivo | Fase atual, progresso e bloqueios |
| [projeto/decisoes.md](projeto/decisoes.md) † | vivo | Decisões DEC-01 a DEC-30, datadas e justificadas |
| [projeto/backlog-tarefas.md](projeto/backlog-tarefas.md) † | vivo | Backlog de engenharia (BL-XX) |
| [projeto/backlog-kanban.md](projeto/backlog-kanban.md) † | vivo | Espelho local do board Kanban do Notion (DEC-20) |
| [projeto/riscos.md](projeto/riscos.md) † | vivo | Registro de riscos (R-XX) |
| [projeto/backlog-tarefas-humanas.md](projeto/backlog-tarefas-humanas.md) | vivo | Tarefas que só uma pessoa pode executar (HT-XX) |
| [projeto/cronograma.md](projeto/cronograma.md) | vivo | Cronograma por etapa (baseline de 2026-07-17; marcos M4-M7 vencidos, ver `_preparo/03_classificacao.md` §5.4) |
| [projeto/ciclo-de-vida.md](projeto/ciclo-de-vida.md) | vivo | Modelo de ciclo de vida e etapas 0-7 |
| [projeto/pauta-validacao-lacunas.md](projeto/pauta-validacao-lacunas.md) | registro | Pauta da validação das lacunas com o cliente |
| [projeto/ata-validacao-lacunas.md](projeto/ata-validacao-lacunas.md) | registro | Ata das sessões de 2026-09-10 e 2026-09-17 |
| [projeto/relatorio-benchmark-geracao-pdf-docx.md](projeto/relatorio-benchmark-geracao-pdf-docx.md) | registro | Benchmark de geração de PDF/DOCX do RFO (BL-22) |
| [projeto/revisao-seguranca-owasp.md](projeto/revisao-seguranca-owasp.md) | registro | Revisão OWASP Top 10:2021 (BL-23) |

## Material para o cliente

| Documento | Tipo | Conteúdo |
|---|---|---|
| [cliente/briefing-tecnico-para-ia.md](cliente/briefing-tecnico-para-ia.md) | vivo | Resumo técnico do projeto para o cliente colar em outras IAs |
| [cliente/proposta-comercial.md](cliente/proposta-comercial.md) | registro | Proposta comercial |
| [cliente/apresentacao-comercial.md](cliente/apresentacao-comercial.md) | registro | Roteiro dos slides comerciais |
| [cliente/relatorio-situacao-mvp.docx](cliente/relatorio-situacao-mvp.docx) | registro | Situação do MVP enviada ao cliente (atualizado em 12/08/2026); gerado por `cliente/gerar_relatorio_cliente.py` |
| [cliente/prompt-lado-cliente.md](cliente/prompt-lado-cliente.md) | insumo | Prompt-sistema do cliente para legendas fotográficas técnicas (ADR-12, RF-15) |
| [cliente/solicitacao-templates-docx.md](cliente/solicitacao-templates-docx.md) | registro | **Superado, não enviar**: pedido de templates e logo que perdeu o objeto (DEC-25, DEC-30) |

## Jurídico

| Documento | Tipo | Conteúdo |
|---|---|---|
| [contrato-prestacao-servicos-desenvolvimento.md](contrato-prestacao-servicos-desenvolvimento.md) | registro | Minuta do contrato de desenvolvimento e manutenção |
| [analise-comparativa-contratos.md](analise-comparativa-contratos.md) | registro | Comparação entre o contrato original e a versão revisada pela contratante |

## Insumos do cliente

| Documento | Tipo | Conteúdo |
|---|---|---|
| [convertidos/README.md](convertidos/README.md) | vivo | Índice das 9 conversões para Markdown |
| [convertidos/RFO_INSPECAO.md](convertidos/RFO_INSPECAO.md) | insumo | Modelo "RFO INSPEÇÃO"; fonte do seed do gabarito (`app/scripts/rfo_gabarito_parser.py`) |
| [convertidos/Relatorio_de_Fiscalizacao.md](convertidos/Relatorio_de_Fiscalizacao.md) | insumo | Relatório de Fiscalização |
| [convertidos/Relatorio_de_Fiscalizacao_1.md](convertidos/Relatorio_de_Fiscalizacao_1.md) | insumo | Relatório de Fiscalização 1 |
| [convertidos/Laudo_Tecnico_de_Inspecao_Predial_2026_-_Cond_Cortina_DAmpezzo.md](convertidos/Laudo_Tecnico_de_Inspecao_Predial_2026_-_Cond_Cortina_DAmpezzo.md) | insumo | LTIP 2026 do Cond. Cortina D'Ampezzo |
| [convertidos/Relatorio_Fotografico_de_Inspecao_Predial_-_CORTINA_DAMPAREZZO_-_Versao_Final.md](convertidos/Relatorio_Fotografico_de_Inspecao_Predial_-_CORTINA_DAMPAREZZO_-_Versao_Final.md) | insumo | Relatório fotográfico de inspeção predial (versão final) |
| [convertidos/Laudo_Tecnico_de_Vistoria_Cautelar_de_Recebimento_-_Reforma_New_York_-_V01.md](convertidos/Laudo_Tecnico_de_Vistoria_Cautelar_de_Recebimento_-_Reforma_New_York_-_V01.md) | insumo | Vistoria cautelar de recebimento (Reforma New York, V01) |
| [convertidos/Laudo_Tecnico_de_Vistoria_de_Imovel_Residencial_-_Ap_1404.md](convertidos/Laudo_Tecnico_de_Vistoria_de_Imovel_Residencial_-_Ap_1404.md) | insumo | Vistoria de imóvel residencial (Ap. 1404) |
| [convertidos/COND.md](convertidos/COND.md) | insumo | Conversão de `COND.pdf` |
| [convertidos/Contrato_Prestacao_Servicos_Software.md](convertidos/Contrato_Prestacao_Servicos_Software.md) | insumo | Contrato de prestação de serviços de software |
| [../01_output-context/README.md](../01_output-context/README.md) | insumo | Índice da pasta de originais do cliente (não alterar; binários fora do git) |
| [../02_prototipos/index.html](../02_prototipos/index.html) | registro | Protótipos HTML navegáveis das telas |

## Agentes e automação do backlog

| Documento | Tipo | Conteúdo |
|---|---|---|
| [../BACKLOG.md](../BACKLOG.md) | vivo | Backlog executável do `backlog-auto`, com a "Regra de pronto" e o "Fechamento de lote" |
| [backlog-auto/BACKLOG-MANUAL.md](backlog-auto/BACKLOG-MANUAL.md) | vivo | Manual da ferramenta `backlog-auto` |
| [backlog-auto/CELULAR.md](backlog-auto/CELULAR.md) | vivo | Uso do `backlog-auto` pelo celular |
| [../backlog-auto/README.md](../backlog-auto/README.md) | vivo | README do módulo `backlog-auto` (código da ferramenta) |
| [../.github/agents/](../.github/agents/) | vivo | 14 instruções de agente por papel (`*.agent.md`) e 2 guias de metodologia de base de conhecimento |
| [../.github/prompts/](../.github/prompts/) | registro | 45 prompts de ativação de tarefas (`*.prompt.md`) |

## Preparo da documentação (Bloco 0 do `BACKLOG.md`)

| Documento | Tipo | Conteúdo |
|---|---|---|
| [_preparo/01_sistema.md](_preparo/01_sistema.md) | registro | D01: mapa do sistema, objetivo × código, componentes, fluxo, testes e riscos |
| [_preparo/02_inventario.md](_preparo/02_inventario.md) | registro | D02: inventário da documentação existente |
| [_preparo/03_classificacao.md](_preparo/03_classificacao.md) | registro | D03: veredito de cada documento e plano de ação |

---

## Registro da tarefa D04 (2026-11-03)

Execução do "Plano de ação" de `_preparo/03_classificacao.md` §5. A branch `worktree-backlog-D04` foi avançada por fast-forward de `14ead2f` para `c5fee00` (`git merge --ff-only main`), porque a base não tinha o `03_classificacao.md`.

**Criados (§5.1, todos os itens):** `README.md` (raiz), `00_docs/README.md` (este índice), `guia-desenvolvimento.md`, `dicionario-de-dados.md`, `configuracao.md`, `guia-contribuicao.md`.

**Refeitos ou corrigidos (§5.2, todos os itens), preservando o que a D03 marcou como correto:**

| Arquivo | O que mudou |
|---|---|
| `arquitetura.md` | nova §0 "Estado da implementação"; §1 marca Redis/Celery como planejados; §2 ganha o diagrama do implementado ao lado do alvo; §3 com `prioridade_sugerida`, `prioridade_ajustada_por_id`, `prioridade_ajustada_em`, `criado_por_id` e os campos de IA/`PROMPT_IA` marcados como planejados; §4 com Autenticação, `GET /ocorrencias/{id}`, `POST /edificacoes/{id}/documentos`, o download real do portal e as rotas de relatório, `/legenda-ia/gerar` e `/gabarito/funcoes-mao-obra` marcadas como planejadas; §5 com nota sobre os templates reais; §7 com a árvore real e a lista do previsto; §10.5 com a topologia real do Render; frontmatter e `ai-summary` |
| `projeto/plano-gestao-configuracao.md` | §1.1, §1.4, §2 e §3.1-§3.2 reescritas pela DEC-22 e pelo `ci.yml` real (sem `mypy`, sem `pip-audit`/`npm audit`, lint não bloqueante); §6 deixou de chamar os scripts de backup de "a implementar". Registrado que `cd-staging.yml` checa `/health/ready`, rota que não existe |
| `projeto/resumo-executivo.md` | tabela de fases trocada por "Estado Atual"; nota de que a geração de PDF/DOCX é a entrega pendente; as 5 perguntas ao cliente aparecem como respondidas (DEC-18, DEC-26, DEC-27, DEC-28, Render) |
| `cliente/briefing-tecnico-para-ia.md` | §5: três perfis e Redis/Celery como previstos; §6: duas branches de deploy, sem staging nem `garra-db-staging`, storage de produção não configurado; §7: o que funciona e o que falta |
| `cliente/solicitacao-templates-docx.md` | `status: superado` e nota "não enviar" no topo; corpo mantido como histórico, só com os 3 links do checklist corrigidos de `status.md` etc. para `../projeto/...` (estavam quebrados) |

**Não alterados:** os documentos **efetiva** (só entraram como link neste índice), o `cronograma.md` (parcial, mas replanejar datas é decisão humana, §5.4 item 2), código, testes, dados, `01_output-context/`, `BACKLOG.md` e os documentos de gestão †.

**Fora do `Toca` da D04 (§5.3), pendentes para o integrador:** `04_backend/README.md`, `03_frontend/README.md` e `05_infra/README.md` (parciais), `03_frontend/e2e/README.md` (ausente, citado em `playwright.config.ts:10`), `.github/agents/engenheiro-ia.agent.md` e os prompts `03`, `04`, `06`, `07`, `08` de `.github/prompts/`. Os READMEs de pasta seguem com as falhas listadas na D03; os documentos novos citam a informação correta.

**Correções aos insumos encontradas nesta tarefa:**

1. `03_classificacao.md` diz "20 módulos `test_*.py`"; `ls 04_backend/tests | grep -c "^test_"` → **19**.
2. `03_classificacao.md` (§3, "Referência de configuração") diz que `NEXT_PUBLIC_API_URL` não está em nenhum `.env.example`; ela está em `05_infra/.env.example`. O que não existe é o `03_frontend/.env.example`.
3. `cd-staging.yml` faz o healthcheck em `/health/ready`, que não existe no backend (`app/main.py` só tem `/health`), e não tem passo de rollback.
4. O job `backend` do `ci.yml` roda `pytest` sem `alembic upgrade head` antes; se os testes que dependem de tabela passam no Actions: **não determinado**.

**Propostas para o fechamento de lote (não aplicadas):**

- Atualizar os 3 READMEs de pasta e criar `03_frontend/e2e/README.md` (§5.3 da D03).
- Ajustar o healthcheck do `cd-staging.yml` para `/health` ou criar `/health/ready` (código; decisão do time).
- Atualizar o `status.md` † se o time quiser registrar a existência deste índice e dos guias novos.

**Testes:** não rodaram e não se aplicam: a tarefa só altera documentação (item 1 da "Regra de pronto" vale para tarefas com código). O PostgreSQL (`localhost:5433`) e o MinIO (`localhost:9000`) estavam fora do ar (`Test-NetConnection` → `False`) e o comando `docker` não está no PATH, então `pytest` não teria resultado válido. `ruff`, `npm run lint` e `npm run build` não foram executados porque nenhum arquivo de `04_backend/` ou `03_frontend/` foi tocado. Último resultado registrado: `_preparo/01_sistema.md` §5.2.
