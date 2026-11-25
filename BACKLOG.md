# Backlog executável — Garra Engenharia — Automação de Relatórios Prediais

Cada tarefa vira uma sessão em background do Claude Code. O bloco `Prompt` é copiável como está.
Comandos: `backlog-auto list`, `backlog-auto next`, `backlog-auto run`, `backlog-auto auto`. Manual: [00_docs/backlog-auto/BACKLOG-MANUAL.md](00_docs/backlog-auto/BACKLOG-MANUAL.md).

**Campos:** `Status` (todo, doing, done, blocked) · `Papel` (livre) · `Depende` (ids que precisam estar `done`, ou `—`) · `Ambiente` (veja `ambientes` em backlog.toml) · `Dificuldade` (baixa, media, alta: define modelo e teto de gasto) · `Toca` (arquivos/pastas que a tarefa escreve; tarefas com `Toca` sobreposto nunca rodam juntas) · `Doc` (onde registrar o resultado) · `Pronto` (critério verificável).

## Regra de pronto (vale para toda tarefa)

1. Com código: testes verdes, com testes novos para o que foi criado (`pytest` + `ruff check .` em `04_backend`; `npm run lint` + `npm run build` em `03_frontend`), como no checklist de `.github/pull_request_template.md`.
2. Registrar o resultado no doc indicado em `Doc` (fatos, números, caminhos, comandos e saída dos testes); decisão nova vai como proposta no `Doc`, não direto em `00_docs/projeto/decisoes.md`.
3. Em lote paralelo, **não editar este arquivo**: o status é atualizado por `backlog-auto`.
4. Nunca alterar nem apagar dados existentes; ler é livre (barreira configurada em `[guard]`).
5. Antes de qualquer outra coisa, rode `git merge --ff-only main` no worktree (ou `git merge main` se o ff falhar): o worktree pode nascer de `origin/main`, que está atrás da `main` local.
6. Testes do backend rodam no banco isolado `garra_engenharia_test` (já migrado), nunca no `garra_engenharia` de dev: em PowerShell `$env:POSTGRES_DB='garra_engenharia_test'`, em bash `export POSTGRES_DB=garra_engenharia_test`; rode `alembic upgrade head` nele antes do `pytest`. Use o venv `04_backend/.venv` (o `ruff` está instalado nele). O Docker fica em `C:/Program Files/Docker/Docker/resources/bin`.

## Fechamento de lote

Rodar depois que um lote terminar, antes do próximo:

```text
Rode `git status` e `git log` para ver o que o último lote mudou. Para cada tarefa concluída, atualize a documentação do projeto com os fatos novos — status do item em 00_docs/projeto/backlog-tarefas.md e backlog-kanban.md, 00_docs/projeto/status.md, decisões propostas como DEC-XX em 00_docs/projeto/decisoes.md, riscos em riscos.md e o README da pasta tocada (04_backend/README.md, 03_frontend/README.md, 05_infra/README.md) — e confira se este backlog reflete os status reais (`backlog-auto list`). Não altere código.
```

---

## Bloco 0 — Preparo da documentação (automático)

Gerado por `backlog-auto preparo`. Enquanto estas tarefas não estiverem `done`, nenhuma outra é liberada.

### D01 · Mapear o sistema e seu objetivo
- **Status:** done
- **Fase:** preparo
- **Papel:** analista
- **Depende:** —
- **Ambiente:** offline
- **Dificuldade:** alta
- **Toca:** 00_docs/_preparo/01_sistema.md
- **Doc:** 00_docs/_preparo/01_sistema.md
- **Pronto:** `00_docs/_preparo/01_sistema.md` descreve objetivo, componentes, fluxo e como instalar, rodar e testar, com evidências.
- **Prompt:**
```text
Tarefa D01. Leia o sistema deste repositório (estrutura, código-fonte, configuração, testes, dependências, histórico do git) e escreva 00_docs/_preparo/01_sistema.md com: (1) objetivo do sistema e quem o usa; O dono declara o objetivo do sistema como: «Sistema web (PWA) da Garra Engenharia que automatiza a produção de relatórios técnicos de engenharia predial (RFO, LTIP e relatório fotográfico): o engenheiro registra edificações, contratos, visitas e ocorrências com fotos pelo celular e gera PDF e DOCX fiéis aos modelos do cliente, com classificação de anomalias (CMM/GUT), dashboard de saúde da edificação e portal do cliente.». Use-o como referência e aponte qualquer divergência com o que o código realmente faz. (2) entradas e saídas; (3) tabela de componentes (caminho → responsabilidade); (4) fluxo principal de dados ou de execução; (5) como instalar, rodar e testar (rode os testes se existirem e registre o resultado); (6) dependências e serviços externos; (7) riscos e lacunas visíveis no código. Escreva em português do Brasil. Só altere arquivos de documentação (nunca código-fonte, testes ou dados). O projeto pode já ter documentação ou regras de documentação sob qualquer nome (AGENTS.md, CLAUDE.md, LEIA-ME, CONTRIBUTING, índice, plano, guia, manual, pastas docs_* ou wiki): procure por conteúdo, não só pelo nome, e siga as convenções de pasta, formato e índice que encontrar. Não invente: cada afirmação precisa de um caminho de arquivo ou comando que você verificou. Onde não der para saber, escreva 'não determinado' em vez de supor. Siga a "Regra de pronto" do BACKLOG.md.
```

### D02 · Inventariar a documentação existente
- **Status:** done
- **Fase:** preparo
- **Papel:** analista
- **Depende:** —
- **Ambiente:** offline
- **Dificuldade:** media
- **Toca:** 00_docs/_preparo/02_inventario.md
- **Doc:** 00_docs/_preparo/02_inventario.md
- **Pronto:** `00_docs/_preparo/02_inventario.md` lista todo documento existente ou declara explicitamente que não há nenhum.
- **Prompt:**
```text
Tarefa D02. Encontre toda a documentação que já existe no repositório: arquivos .md/.rst/.txt/.docx, READMEs em qualquer pasta, wiki, docstrings de módulo, cabeçalhos de scripts, notebooks com texto explicativo, AGENTS.md/CLAUDE.md. Escreva 00_docs/_preparo/02_inventario.md com uma tabela (caminho, tema, tamanho, data do último commit que o tocou via `git log -1 --format=%cs -- <arquivo>`, uma linha de resumo do que ele diz). Se não houver nenhuma documentação além do código, escreva exatamente 'Nenhuma documentação existente.' no topo. Não avalie a qualidade aqui (isso é a próxima etapa). Escreva em português do Brasil. Só altere arquivos de documentação (nunca código-fonte, testes ou dados). O projeto pode já ter documentação ou regras de documentação sob qualquer nome (AGENTS.md, CLAUDE.md, LEIA-ME, CONTRIBUTING, índice, plano, guia, manual, pastas docs_* ou wiki): procure por conteúdo, não só pelo nome, e siga as convenções de pasta, formato e índice que encontrar. Não invente: cada afirmação precisa de um caminho de arquivo ou comando que você verificou. Onde não der para saber, escreva 'não determinado' em vez de supor. Siga a "Regra de pronto" do BACKLOG.md.
```

### D03 · Classificar a documentação: efetiva ou refazer
- **Status:** done
- **Fase:** preparo
- **Papel:** analista
- **Depende:** D01, D02
- **Ambiente:** offline
- **Dificuldade:** alta
- **Toca:** 00_docs/_preparo/03_classificacao.md
- **Doc:** 00_docs/_preparo/03_classificacao.md
- **Pronto:** `00_docs/_preparo/03_classificacao.md` dá um veredito com evidência para cada documento e lista o que criar e refazer.
- **Prompt:**
```text
Tarefa D03. Leia 00_docs/_preparo/01_sistema.md e 00_docs/_preparo/02_inventario.md e confronte cada documento com o código real. Dê a cada um um veredito: **efetiva** (correta, atual e cobre o seu tema: não será tocada), **parcial** (correta em parte; aponte as seções obsoletas ou faltantes) ou **refazer** (obsoleta, contradiz o código ou é vaga demais para ser útil). Critérios verificáveis: os caminhos e comandos citados existem e funcionam; os nomes batem com o código; o objetivo do sistema está dito; a data é compatível com as mudanças recentes no código. Cada veredito leva a evidência (arquivo e trecho). Depois liste as lacunas, isto é, documentos que deveriam existir e não existem (veredito **ausente**): no mínimo visão geral e objetivo, arquitetura, como instalar/rodar/testar, e, quando o projeto tiver, dicionário de dados, decisões e guia de contribuição. Se o inventário disser que não há documentação, todos os itens são **ausente**. Escreva 00_docs/_preparo/03_classificacao.md com a tabela de vereditos e, no fim, o 'Plano de ação': a lista exata de arquivos a criar e a refazer, cada um com o que deve conter. Escreva em português do Brasil. Só altere arquivos de documentação (nunca código-fonte, testes ou dados). O projeto pode já ter documentação ou regras de documentação sob qualquer nome (AGENTS.md, CLAUDE.md, LEIA-ME, CONTRIBUTING, índice, plano, guia, manual, pastas docs_* ou wiki): procure por conteúdo, não só pelo nome, e siga as convenções de pasta, formato e índice que encontrar. Não invente: cada afirmação precisa de um caminho de arquivo ou comando que você verificou. Onde não der para saber, escreva 'não determinado' em vez de supor. Siga a "Regra de pronto" do BACKLOG.md.
```

### D04 · Criar e refazer a documentação
- **Status:** done
- **Fase:** preparo
- **Papel:** analista
- **Depende:** D03
- **Ambiente:** offline
- **Dificuldade:** alta
- **Toca:** 00_docs, README.md
- **Doc:** 00_docs/README.md
- **Pronto:** Todo item do plano de ação de 03_classificacao.md foi criado ou refeito; documentos efetivos ficaram intactos.
- **Prompt:**
```text
Tarefa D04. Execute o 'Plano de ação' de 00_docs/_preparo/03_classificacao.md. Crie os documentos **ausente** e refaça os **refazer** e **parcial** (nas parciais, preserve o que está correto). Não altere os **efetiva**, só acrescente link para eles no índice. Baseie-se em 00_docs/_preparo/01_sistema.md e no código. Ao substituir um documento, não deixe a versão antiga ao lado (o git guarda o histórico). Crie ou atualize um índice em 00_docs/README.md que liste todos os documentos com uma linha cada, e garanta que o README.md da raiz diga o objetivo do sistema e aponte para o índice. Escreva em português do Brasil. Só altere arquivos de documentação (nunca código-fonte, testes ou dados). O projeto pode já ter documentação ou regras de documentação sob qualquer nome (AGENTS.md, CLAUDE.md, LEIA-ME, CONTRIBUTING, índice, plano, guia, manual, pastas docs_* ou wiki): procure por conteúdo, não só pelo nome, e siga as convenções de pasta, formato e índice que encontrar. Não invente: cada afirmação precisa de um caminho de arquivo ou comando que você verificou. Onde não der para saber, escreva 'não determinado' em vez de supor. Siga a "Regra de pronto" do BACKLOG.md.
```

### D05 · Verificar a documentação contra o código
- **Status:** done
- **Fase:** preparo
- **Papel:** analista
- **Depende:** D04
- **Ambiente:** offline
- **Dificuldade:** media
- **Toca:** 00_docs, 00_docs/_preparo/04_relatorio.md, README.md
- **Doc:** 00_docs/_preparo/04_relatorio.md
- **Pronto:** `00_docs/_preparo/04_relatorio.md` confirma que a documentação final bate com o código e lista o que sobrou.
- **Prompt:**
```text
Tarefa D05. Confira a documentação final contra o código: abra cada caminho citado, siga cada link relativo, rode os comandos documentados que forem seguros (instalar, testar, ajuda do CLI) e compare nomes de funções, parâmetros e configurações. Corrija direto o que estiver errado. Escreva 00_docs/_preparo/04_relatorio.md com: o veredito final de cada documento (todos devem ficar **efetiva**), o que foi corrigido nesta verificação e as pendências que exigem decisão humana (por exemplo objetivo inferido com confiança baixa). Escreva em português do Brasil. Só altere arquivos de documentação (nunca código-fonte, testes ou dados). O projeto pode já ter documentação ou regras de documentação sob qualquer nome (AGENTS.md, CLAUDE.md, LEIA-ME, CONTRIBUTING, índice, plano, guia, manual, pastas docs_* ou wiki): procure por conteúdo, não só pelo nome, e siga as convenções de pasta, formato e índice que encontrar. Não invente: cada afirmação precisa de um caminho de arquivo ou comando que você verificou. Onde não der para saber, escreva 'não determinado' em vez de supor. Siga a "Regra de pronto" do BACKLOG.md.
```

---

## Bloco A — Verificação do ambiente

### T01 · Diagnosticar o ambiente de desenvolvimento
- **Status:** done
- **Papel:** devops
- **Depende:** —
- **Ambiente:** docker
- **Dificuldade:** baixa
- **Toca:** 00_docs/backlog-auto/diagnostico.md
- **Doc:** 00_docs/backlog-auto/diagnostico.md
- **Pronto:** `00_docs/backlog-auto/diagnostico.md` registra versões, serviços do `05_infra/docker-compose.yml` no ar e o resultado de `pytest` (04_backend) e de `npm run lint` (03_frontend), com a saída resumida.
- **Prompt:**
```text
Tarefa T01. Leia 04_backend/README.md, 03_frontend/README.md e 05_infra/README.md. Registre em 00_docs/backlog-auto/diagnostico.md: versões de Python, Node e Docker; se o PostgreSQL e o MinIO de 05_infra/docker-compose.yml estão no ar (`docker compose ps` a partir de 05_infra; não suba nem derrube serviços); o resultado de `pytest -q` e `ruff check .` a partir de 04_backend e de `npm run lint` a partir de 03_frontend (instale dependências só se faltarem). Não altere código. Siga a "Regra de pronto" do BACKLOG.md.
```

### T02 · Corrigir incompatibilidade pytest × pytest-asyncio no backend
- **Status:** done
- **Origem:** DEC-31
- **Papel:** backend
- **Depende:** T01
- **Ambiente:** offline
- **Dificuldade:** baixa
- **Toca:** 04_backend/requirements.txt, 00_docs/backlog-auto/pytest-compat.md
- **Doc:** 00_docs/backlog-auto/pytest-compat.md
- **Pronto:** `pytest --collect-only -q` em 04_backend, usando um venv Python 3.12, coleta todos os testes sem INTERNALERROR. `requirements.txt` fixa uma combinação compatível de pytest e pytest-asyncio. O doc registra versões antes e depois e a saída da coleta.
- **Prompt:**
```text
Tarefa A (DEC-31 / risco R-11). Contexto: 00_docs/backlog-auto/diagnostico.md §3.1 mostra que `pytest -q` em 04_backend falha na coleta com `AttributeError: 'Package' object has no attribute 'obj'` em pytest_asyncio/plugin.py. A causa provável é pytest 9.2.0 combinado com pytest-asyncio 0.23.3. 04_backend/requirements.txt (linhas 41-42) aceita `pytest>=9.1.1,<10.0` e `pytest-asyncio>=0.23,<1.0`. Passos: (1) Use ou crie um venv Python 3.12 em 04_backend/.venv (por exemplo `uv venv --python 3.12 .venv`). O Python 3.14 do sistema não instala o pillow, então não o use. Instale `requirements.txt` nele. (2) Reproduza o erro com `python -m pytest --collect-only -q`. (3) Corrija com a menor mudança em 04_backend/requirements.txt. Prefira subir o pytest-asyncio para uma versão compatível com pytest 9, verificando qual versão resolve de fato. Se não resolver, fixe `pytest<9`. Não use `>=` aberto: fixe um intervalo estreito. (4) Rode `python -m pytest --collect-only -q`. Os testes de integração precisam de PostgreSQL em localhost:5433 e MinIO; Docker não existe nesta máquina, então registre que a suíte completa não rodou, sem inventar resultado. Rode também os testes que não dependem de banco, como test_health, test_brand_assets, test_rfo_templates e test_ltip_templates, e registre a saída resumida. (5) Registre em 00_docs/backlog-auto/pytest-compat.md as versões antes e depois, os comandos e as saídas, e proponha o texto de ajuste da DEC-31 como proposta no próprio doc. Não edite 00_docs/projeto/decisoes.md. Não altere nenhum outro arquivo. Siga a "Regra de pronto" do BACKLOG.md.
```

### T03 · Avaliar vulnerabilidades do npm audit no frontend
- **Status:** done
- **Origem:** DEC-31
- **Papel:** frontend
- **Depende:** T01
- **Ambiente:** offline
- **Dificuldade:** baixa
- **Toca:** 00_docs/backlog-auto/npm-audit.md
- **Doc:** 00_docs/backlog-auto/npm-audit.md
- **Pronto:** `00_docs/backlog-auto/npm-audit.md` classifica os 30 achados do `npm audit` (2 críticos, 11 altos, 17 moderados) como dependência direta ou transitiva, de produção ou de desenvolvimento. O doc diz quais têm correção sem breaking change e traz um plano priorizado. Nenhum arquivo de código ou de dependências foi alterado.
- **Prompt:**
```text
Tarefa B (T01 §4 item 5). Contexto: 00_docs/backlog-auto/diagnostico.md §3.3 relata que `npm ci` em 03_frontend reportou 30 vulnerabilidades (17 moderadas, 11 altas, 2 críticas) e não foram tratadas. Esta tarefa é só análise, sem alterar código nem package*.json. Passos: (1) Em 03_frontend, instale as dependências só se faltarem (`npm ci`). (2) Rode `npm audit --json` e `npm audit --omit=dev` e registre a contagem de cada um. (3) Para cada pacote vulnerável, indique a severidade, se a dependência é direta (em package.json) ou transitiva, se é de produção ou de dev, e se o `fix` disponível é breaking (`npm audit fix --dry-run`; nunca rode `npm audit fix` sem --dry-run e não toque em package.json nem package-lock.json). (4) Avalie a exposição real: uma vulnerabilidade só de build/lint (dev) pesa menos que uma em runtime do Next.js. Não invente exploração; baseie-se no texto do advisory. (5) Escreva 00_docs/backlog-auto/npm-audit.md em português, com uma tabela e um plano priorizado de correções, indicando quais exigem upgrade de major do Next.js, o que é decisão a tomar à parte. Registre também os comandos executados. Siga a "Regra de pronto" do BACKLOG.md.
```

### T04 · Configurar o ruff e limpar os 214 achados do backend
- **Status:** done
- **Origem:** DEC-31
- **Papel:** backend
- **Depende:** T02
- **Ambiente:** docker
- **Dificuldade:** media
- **Toca:** 04_backend/pyproject.toml, 04_backend/ruff.toml, 04_backend/app, 04_backend/alembic, 04_backend/tests, 00_docs/backlog-auto/ruff.md
- **Doc:** 00_docs/backlog-auto/ruff.md
- **Pronto:** `ruff check .` em 04_backend sai com exit 0, com configuração do ruff versionada e justificada. Os F821 foram analisados e classificados (falso positivo de TYPE_CHECKING ou erro real). Nenhum `# noqa` global foi usado para esconder erro real. `pytest` roda como na tarefa A. Se o PostgreSQL de 05_infra estiver no ar, a suíte não regride; se não estiver, o doc registra que não rodou.
- **Prompt:**
```text
Tarefa C (DEC-31 / R-11). Contexto: 00_docs/backlog-auto/diagnostico.md §3.2: `ruff check .` em 04_backend dá 214 erros e não há configuração do ruff em 04_backend nem na raiz. Os erros são B008 (87, Depends em default de argumento, idiomático do FastAPI), F821 (38, nomes de relacionamento em app/models/), I001 (36), UP007 (18), UP017 (8), F401 (7), UP035 (6), B905 (4), RUF007 (2), RUF022 (2), RUF100 (2), F541 (1), RUF003, RUF005 e UP046 (1 cada). O CI (.github/workflows/ci.yml) roda `pip install ruff` e `ruff check .`. Antes de editar, leia a seção de lint de .github/pull_request_template.md e o step de ruff do ci.yml. Passos: (1) Use o venv Python 3.12 de 04_backend/.venv, criado conforme a tarefa A, e instale ruff nele. Registre a versão usada. (2) Descubra quais regras o projeto escolheu: procure `[tool.ruff]` ou ruff.toml em qualquer lugar e leia a documentação do backend. Se não houver nada, crie 04_backend/ruff.toml (não crie arquivos na raiz) com `extend-immutable-calls` para fastapi.Depends, fastapi.Query e fastapi.Security em vez de ignorar a B008 globalmente. Justifique cada ignore no próprio arquivo. (3) Investigue os F821 um a um: confirme se vêm de referências por string a classes importadas só sob TYPE_CHECKING (falso positivo, resolvido importando sob TYPE_CHECKING) ou de nome realmente inexistente (erro real, que você deve corrigir e relatar). Valide com `python -c 'import app.models'` e `alembic heads`. (4) Aplique `ruff check . --fix` apenas nas regras seguras e revise o diff, pois não pode mudar comportamento. Corrija à mão B905, RUF007, RUF003 e RUF005 conforme a regra. (5) Não modifique migrations já aplicadas além de ordenação de imports, se necessário; exclua alembic/versions do lint só se a mudança alterar semântica, e justifique. (6) Rode `ruff check .` (deve dar exit 0) e `pytest`. Os testes de integração exigem PostgreSQL em localhost:5433 (`docker compose ps` em 05_infra); se não estiver no ar, registre que não rodou em vez de inventar resultado. (7) Registre em 00_docs/backlog-auto/ruff.md a configuração adotada e o porquê, a tabela de F821 com o veredito de cada um, o antes/depois de erros por regra e os comandos executados. Proponha mudanças no ci.yml no doc; não as aplique. Siga a "Regra de pronto" do BACKLOG.md.
```

### T05 · Pipeline de renderização do LTIP (ltip_pipeline.py)
- **Status:** done
- **Origem:** BL-17
- **Papel:** backend
- **Depende:** T04
- **Ambiente:** docker
- **Dificuldade:** alta
- **Toca:** 04_backend/app/services/report_generator/ltip_pipeline.py, 04_backend/app/services/report_generator/__init__.py, 04_backend/tests/test_ltip_pipeline.py, 00_docs/backlog-auto/ltip-pipeline.md
- **Doc:** 00_docs/backlog-auto/ltip-pipeline.md
- **Pronto:** Existe `ltip_pipeline.py` equivalente ao `rfo_pipeline.py`, que renderiza PDF (WeasyPrint) e DOCX (docxtpl) a partir dos templates derivados de `templates/ltip/layout.json`. `tests/test_ltip_pipeline.py` tem testes novos que passam; os de PDF são pulados com motivo explícito quando o WeasyPrint não estiver disponível. `pytest` e `ruff check .` em 04_backend estão verdes, ou o doc registra o que não rodou e por quê.
- **Prompt:**
```text
Tarefa D (BL-17, pendência 'pipeline de renderização'). Contexto: BL-17 gerou os templates do LTIP em 04_backend/templates/ltip/ (layout.json, ltip_template.html.j2, ltip_template.docx) via app/scripts/build_ltip_templates.py, mas não o pipeline que os renderiza com dados. O equivalente do RFO existe em 04_backend/app/services/report_generator/rfo_pipeline.py, e seus testes em tests/test_rfo_templates.py. Leia esses arquivos, tests/test_ltip_templates.py e a arquitetura em 00_docs/arquitetura.md (ADR-13, seção do gerador de relatórios; leia só essa seção). Passos: (1) Estude a API pública do rfo_pipeline.py (entrada, saída, uso de storage, tratamento de fotos) e espelhe-a em ltip_pipeline.py, reaproveitando funções comuns por import em vez de copiar. Se precisar extrair código comum de rfo_pipeline.py, não o faça: está fora do escopo de `toca`, então duplique o mínimo e registre a sugestão de refatoração no doc. (2) O pipeline deve montar o contexto do template LTIP (capa, dados da edificação, ocorrências agrupadas por sistema, relatório fotográfico com 2 fichas por página, RN-11, rodapé do emitente) a partir dos campos que o template realmente usa; leia os placeholders do ltip_template.html.j2 e não invente campos. (3) Gere PDF via WeasyPrint e DOCX via docxtpl. O WeasyPrint não roda no Windows local; importe-o de forma preguiçosa e escreva os testes de PDF com `pytest.importorskip`/skip e motivo explícito. Os testes de DOCX devem rodar em qualquer lugar. Não dependa de 01_output-context/; use dados sintéticos como em test_ltip_templates.py. Nunca altere esse diretório. (4) Crie tests/test_ltip_pipeline.py com testes do contexto e do DOCX, e do PDF quando houver WeasyPrint. (5) Rode `pytest tests/test_ltip_pipeline.py tests/test_ltip_templates.py` e `ruff check .`. Os testes de integração geral exigem PostgreSQL em localhost:5433; se não estiver no ar, registre que não rodou. (6) Registre em 00_docs/backlog-auto/ltip-pipeline.md a API criada, os campos do contexto, o que ficou fora (conferência visual do PDF depende de HT-09) e os comandos com suas saídas. Siga a "Regra de pronto" do BACKLOG.md.
```

### T06 · Revisar regras de negócio e enums de Ocorrências (BL-14)
- **Status:** done
- **Origem:** BL-14
- **Papel:** backend
- **Depende:** T04
- **Ambiente:** docker
- **Dificuldade:** media
- **Toca:** 04_backend/app/api/v1/ocorrencias.py, 04_backend/app/services/ocorrencia_service.py, 04_backend/app/schemas/ocorrencia.py, 04_backend/tests/test_ocorrencias_regras.py, 00_docs/backlog-auto/ocorrencias-revisao.md
- **Doc:** 00_docs/backlog-auto/ocorrencias-revisao.md
- **Pronto:** `00_docs/backlog-auto/ocorrencias-revisao.md` confronta o backend de Ocorrências com RF-04, RN-03, RN-05 e RN-10 e lista as lacunas encontradas. Cada lacuna corrigida tem teste novo em `tests/test_ocorrencias_regras.py`. `pytest tests/test_ocorrencias_dashboard.py tests/test_ocorrencias_prioridade.py tests/test_ocorrencias_regras.py` passa com PostgreSQL no ar, ou o doc registra que não rodou.
- **Prompt:**
```text
Tarefa E (BL-14, pendência 'revisão das regras de negócio/enum no backend'). Contexto: 00_docs/projeto/backlog-tarefas.md descreve BL-14 como parcial: existem 04_backend/app/api/v1/ocorrencias.py e a tela 03_frontend/app/inspecoes/[id]/ocorrencias/page.tsx, mas falta revisar as regras de negócio e os enums no backend. A BL-15 (Prioridade derivada do Grau de Risco, Prioridade 0 = não aplicável, migration d3b7c9e4f1a2) e a BL-16 (validação de intervalo 0 a 5) já estão concluídas; não as refaça. Leia só as seções de RF-04, RN-03, RN-05, RN-10 e DEC-29 em 00_docs/estudo-do-contexto.md e 00_docs/projeto/decisoes.md, além de ocorrencias.py, ocorrencia_service.py, app/schemas/ocorrencia.py, app/models/ocorrencia.py e dos testes test_ocorrencias_dashboard.py e test_ocorrencias_prioridade.py. Passos: (1) Monte no doc uma tabela com cada regra aplicável (classificação CMM/GUT, valores válidos de enums, sistema/subsistema/localização coerentes entre si, 'Não se Aplica' = prioridade 0, relação com Visita/Inspeção, permissões do perfil auxiliar) e marque se o backend a impõe, com caminho e linha. (2) Para cada lacuna real, escreva primeiro o teste que falha em tests/test_ocorrencias_regras.py e depois corrija o mínimo no service/schema/endpoint. Não crie migration nem altere models; se uma lacuna exigir isso, apenas registre-a no doc como proposta. Erros de domínio seguem o padrão RFC 7807 já existente (DomainError). (3) Não toque no frontend. (4) Rode `pytest tests/test_ocorrencias_dashboard.py tests/test_ocorrencias_prioridade.py tests/test_ocorrencias_regras.py` e `ruff check .` em 04_backend. Os testes exigem o PostgreSQL de 05_infra/docker-compose.yml em localhost:5433; se ele não estiver no ar, registre que não rodou e entregue só a análise e os testes escritos, sem inventar resultado. (5) Registre no doc as lacunas, as correções, os comandos e as saídas. Siga a "Regra de pronto" do BACKLOG.md.
```

### T07 · Aplicar npm audit fix sem --force nos 5 pacotes sem major do frontend
- **Status:** done
- **Origem:** DEC-32
- **Papel:** frontend
- **Depende:** T03
- **Ambiente:** offline
- **Dificuldade:** baixa
- **Toca:** 03_frontend/package-lock.json, 03_frontend/package.json, 00_docs/backlog-auto/npm-audit-fix.md
- **Doc:** 00_docs/backlog-auto/npm-audit-fix.md
- **Pronto:** `00_docs/backlog-auto/npm-audit-fix.md` registra a contagem do `npm audit` antes e depois e os pacotes atualizados. Foram corrigidos apenas os pacotes sem upgrade de major (brace-expansion, js-yaml, nanoid, postcss-selector-parser, source-map-js), sem `--force`. `npm run lint` e `npm run build` em 03_frontend passam. `next`, `fabric`, `react` e `eslint` ficaram nas mesmas versões major de antes.
- **Prompt:**
```text
Tarefa A (DEC-32, item 1 da decisão proposta). Contexto: 00_docs/backlog-auto/npm-audit.md (resultado da T03) classificou os 30 achados do `npm audit` em 03_frontend. DEC-32 em 00_docs/projeto/decisoes.md propõe rodar `npm audit fix` SEM `--force` nos 5 pacotes que têm correção sem major: brace-expansion, js-yaml, nanoid, postcss-selector-parser e source-map-js. Leia o npm-audit.md e a seção DEC-32 (só ela) antes de começar. Passos: (1) A partir de 03_frontend, rode `npm ci` se faltarem dependências, depois `npm audit --json` e `npm audit --omit=dev` e guarde as contagens 'antes' (por severidade). Anote também as versões instaladas de next, react, react-dom, fabric, eslint e eslint-config-next. (2) Rode `npm audit fix --dry-run` e leia o que seria alterado. Nunca use `--force`. Se o dry-run propuser qualquer upgrade de major ou downgrade de next, fabric, react, eslint ou eslint-config-next, NÃO aplique o fix global: atualize apenas os 5 pacotes citados com `npm update <pacote>` (ou `npm install <pacote>@<versão-corrigida> --save-exact` se o pacote for dependência direta) e registre o motivo. (3) Aplique a correção e confira com `git diff --stat` que só package-lock.json (e package.json, se algum dos 5 for dependência direta) mudaram. (4) Rode `npm audit` e `npm audit --omit=dev` de novo e registre as contagens 'depois'. (5) Rode `npm run lint` e `npm run build` em 03_frontend; ambos devem passar. Se o build falhar por causa da mudança, reverta com `git checkout -- package.json package-lock.json` e registre a falha no doc. (6) Escreva 00_docs/backlog-auto/npm-audit-fix.md em português: comandos executados com a saída resumida, tabela antes/depois por severidade e por pacote, versões antes/depois, o que continua pendente (upgrade do Next, fabric 7) e o status do lint/build. Não altere nenhum outro arquivo e não edite 00_docs/projeto/decisoes.md; qualquer decisão nova vai como proposta no doc. Siga a "Regra de pronto" do BACKLOG.md.
```

### T08 · Corrigir as lacunas L1–L7 de validação de Ocorrências (DEC-34)
- **Status:** done
- **Origem:** DEC-34
- **Papel:** backend
- **Depende:** T06
- **Ambiente:** docker
- **Dificuldade:** media
- **Toca:** 04_backend/app/api/v1/ocorrencias.py, 04_backend/app/services/ocorrencia_service.py, 04_backend/app/schemas/ocorrencia.py, 04_backend/tests/test_ocorrencias_regras.py, 00_docs/backlog-auto/ocorrencias-correcoes.md
- **Doc:** 00_docs/backlog-auto/ocorrencias-correcoes.md
- **Pronto:** Cada lacuna L1 a L7 do documento de revisão tem correção aplicada, e os testes `test_lacuna_*` de `tests/test_ocorrencias_regras.py` passam com o PostgreSQL de 05_infra no ar. `pytest tests/test_ocorrencias_dashboard.py tests/test_ocorrencias_prioridade.py tests/test_ocorrencias_regras.py` e `ruff check .` em 04_backend estão verdes. Se o PostgreSQL não estiver no ar, o doc registra que os testes não rodaram e entrega só as correções com a análise. P1 a P4 continuam sem alteração e listadas como pendentes de decisão.
- **Prompt:**
```text
Tarefa B (DEC-34 / risco R-13, continuação da T06). Contexto: 00_docs/projeto/revisao-regras-ocorrencias.md (revisão da T06) e 00_docs/backlog-auto/ocorrencias-revisao.md listam 7 lacunas no backend de Ocorrências: L1 situação sem enum; L2 classificação sem enum; L3 sistema inexistente vira 500; L4 subsistema inexistente ou incoerente com o sistema vira 500; L5 inspeção inexistente vira 500; L6 `PUT` sobrescreve `inspecao_id` e `seq_numero`; L7 filtro `sistema_id` inválido vira 500. Os testes `test_lacuna_*` já existem em 04_backend/tests/test_ocorrencias_regras.py, mas nunca rodaram por falta de PostgreSQL. Leia o doc de revisão, a seção DEC-34 de 00_docs/projeto/decisoes.md e os arquivos 04_backend/app/api/v1/ocorrencias.py, app/services/ocorrencia_service.py, app/schemas/ocorrencia.py e app/models/ocorrencia.py. Passos: (1) Verifique se o PostgreSQL de 05_infra/docker-compose.yml está no ar (`docker compose ps` a partir de 05_infra; não suba nem derrube serviços). Rode a linha de base `pytest tests/test_ocorrencias_dashboard.py tests/test_ocorrencias_prioridade.py tests/test_ocorrencias_regras.py` a partir de 04_backend e registre quais `test_lacuna_*` falham. Se o banco não estiver no ar, registre isso e siga só com a análise estática. (2) Corrija o mínimo para cada lacuna: valide os enums com `DomainError` (RFC 7807, padrão que já existe, 422) usando os valores de RN-03 e do modelo; cheque existência de sistema, subsistema (e pertencimento ao sistema) e inspeção com `NotFoundError`/`DomainError`; exclua `inspecao_id` e `seq_numero` do `PUT`; tipe `sistema_id` do filtro como UUID. Se algum teste `test_lacuna_*` estiver errado em relação à regra, corrija o teste e explique no doc. (3) NÃO resolva P1 a P4 (restringir ocorrência a Inspeção LTIP, auxiliar excluir, enums no banco, autoria de `prioridade_ajustada_*`): são decisões do dono e P3 exigiria migration. Não crie migration, não altere models e não toque no frontend. (4) Mantenha o comportamento de BL-15 (derivação da prioridade pelo Grau de Risco, prioridade 0 = não aplicável) e de BL-16 (intervalo 0 a 5): os testes dessas tarefas precisam continuar verdes. (5) Rode os três arquivos de teste e `ruff check .` em 04_backend; não relate resultado que não rodou. (6) Escreva 00_docs/backlog-auto/ocorrencias-correcoes.md com: tabela L1 a L7 (antes, depois, arquivo e linha, teste), P1 a P4 como pendentes, comandos e saídas. Não edite 00_docs/projeto/decisoes.md nem o revisao-regras-ocorrencias.md. Siga a "Regra de pronto" do BACKLOG.md.
```

### T09 · Templates PDF/DOCX da Vistoria Cautelar de Recebimento a partir do PDF original
- **Status:** done
- **Origem:** DEC-25
- **Papel:** backend
- **Depende:** T04
- **Ambiente:** offline
- **Dificuldade:** alta
- **Toca:** 04_backend/templates/vistoria_cautelar, 04_backend/app/scripts/vistoria_cautelar_layout_extractor.py, 04_backend/app/scripts/build_vistoria_cautelar_templates.py, 04_backend/tests/test_vistoria_cautelar_templates.py, 00_docs/backlog-auto/vistoria-cautelar-templates.md
- **Doc:** 00_docs/backlog-auto/vistoria-cautelar-templates.md
- **Pronto:** Existem `04_backend/templates/vistoria_cautelar/layout.json` (só geometria medida, sem dados pessoais do exemplar), `vistoria_cautelar_template.html.j2` e `vistoria_cautelar_template.docx`, gerados por `python -m app.scripts.build_vistoria_cautelar_templates`. Os dois templates derivam do mesmo `layout.json`. `tests/test_vistoria_cautelar_templates.py` roda sobre PDF sintético, sem `01_output-context/`, e passa. `pytest` desse arquivo e `ruff check .` em 04_backend estão verdes. O doc registra as medidas, o que ficou pendente e a conferência visual como pendência de HT-09.
- **Prompt:**
```text
Tarefa C (DEC-25 / ADR-13, fatia 'Vistoria Cautelar' do modelo incremental; mesmo método do LTIP em BL-17). Contexto: o original do cliente é o PDF `01_output-context/Laudo Técnico de Vistoria Cautelar de Recebimento - Reforma New York - V01.pdf`. NUNCA altere nem apague nada em 01_output-context/. O layout do LTIP já foi derivado assim: 04_backend/app/scripts/ltip_layout_extractor.py (pdfplumber) → 04_backend/templates/ltip/layout.json → app/scripts/build_ltip_templates.py → ltip_template.html.j2 (WeasyPrint) + ltip_template.docx (docxtpl), com 11 testes em 04_backend/tests/test_ltip_templates.py sobre um PDF sintético. Leia esses quatro arquivos antes de escrever qualquer coisa e leia a seção de ADR-13 em 00_docs/arquitetura.md (só ela) e as seções do §2 de 00_docs/projeto/status.md que descrevem os tipos de documento. Passos: (1) Crie app/scripts/vistoria_cautelar_layout_extractor.py espelhando o do LTIP: meça com pdfplumber o tamanho de página, margens, famílias e corpos tipográficos, cores dos cabeçalhos, estrutura de seções, grade de fotos, cabeçalho/rodapé e bloco de assinaturas. Reaproveite funções do extrator do LTIP por import quando possível, sem editá-lo. Mapeie também a ordem e os títulos das seções do laudo (extraia só os títulos fixos, não o conteúdo do caso). (2) O `layout.json` guarda APENAS geometria e rótulos fixos: descarte nomes de pessoas, CPF, CREA, e-mails, endereços e telefones do exemplar antes de gravar (OWASP A02); troque-os por placeholders Jinja2 nomeados. (3) Crie app/scripts/build_vistoria_cautelar_templates.py que gera, de forma determinística e só a partir do layout.json, o .html.j2 e o .docx em 04_backend/templates/vistoria_cautelar/. Use a marca de 04_backend/templates/assets/ como o LTIP faz. (4) Crie tests/test_vistoria_cautelar_templates.py com um PDF sintético gerado no próprio teste (não leia 01_output-context/): teste o extrator, o JSON sem dados pessoais, a presença dos placeholders nos dois templates e que PDF e DOCX derivam do mesmo layout. Testes que exigem WeasyPrint usam skip com motivo explícito, pois ele não roda no Windows local. (5) Rode `pytest tests/test_vistoria_cautelar_templates.py` e `ruff check .` a partir de 04_backend. Este arquivo não exige banco; não rode a suíte completa de integração. (6) Escreva 00_docs/backlog-auto/vistoria-cautelar-templates.md: medidas obtidas, seções mapeadas, lista de placeholders, comandos e saídas, pendências (conferência visual do PDF depende de HT-09; pipeline de renderização é tarefa à parte, como o ltip_pipeline.py). Não toque em outros templates nem na pasta do LTIP e do RFO. Siga a "Regra de pronto" do BACKLOG.md.
```

### T10 · Templates PDF/DOCX da Vistoria de Imóvel Residencial a partir do PDF original
- **Status:** done
- **Origem:** DEC-25
- **Papel:** backend
- **Depende:** T04
- **Ambiente:** offline
- **Dificuldade:** alta
- **Toca:** 04_backend/templates/vistoria_residencial, 04_backend/app/scripts/vistoria_residencial_layout_extractor.py, 04_backend/app/scripts/build_vistoria_residencial_templates.py, 04_backend/tests/test_vistoria_residencial_templates.py, 00_docs/backlog-auto/vistoria-residencial-templates.md
- **Doc:** 00_docs/backlog-auto/vistoria-residencial-templates.md
- **Pronto:** Existem `04_backend/templates/vistoria_residencial/layout.json` (só geometria medida, sem dados pessoais do exemplar), `vistoria_residencial_template.html.j2` e `vistoria_residencial_template.docx`, gerados por `python -m app.scripts.build_vistoria_residencial_templates`. Os dois templates derivam do mesmo `layout.json`. `tests/test_vistoria_residencial_templates.py` roda sobre PDF sintético, sem `01_output-context/`, e passa. `pytest` desse arquivo e `ruff check .` em 04_backend estão verdes. O doc registra as medidas, o que ficou pendente e a conferência visual como pendência de HT-09.
- **Prompt:**
```text
Tarefa D (DEC-25 / ADR-13, fatia 'Vistoria Residencial' do modelo incremental; mesmo método do LTIP em BL-17). Contexto: o original do cliente é o PDF `01_output-context/Laudo Técnico de Vistoria de Imóvel Residencial - Ap. 1404.pdf`. NUNCA altere nem apague nada em 01_output-context/. O layout do LTIP já foi derivado assim: 04_backend/app/scripts/ltip_layout_extractor.py (pdfplumber) → 04_backend/templates/ltip/layout.json → app/scripts/build_ltip_templates.py → ltip_template.html.j2 (WeasyPrint) + ltip_template.docx (docxtpl), com 11 testes em 04_backend/tests/test_ltip_templates.py sobre um PDF sintético. Leia esses quatro arquivos antes de escrever qualquer coisa e leia a seção de ADR-13 em 00_docs/arquitetura.md (só ela) e as seções do §2 de 00_docs/projeto/status.md que descrevem os tipos de documento. Passos: (1) Crie app/scripts/vistoria_residencial_layout_extractor.py espelhando o do LTIP: meça com pdfplumber o tamanho de página, margens, famílias e corpos tipográficos, cores dos cabeçalhos, estrutura de seções, grade de fotos, cabeçalho/rodapé e bloco de assinaturas. Reaproveite funções do extrator do LTIP por import quando possível, sem editá-lo, e não importe nada da tarefa paralela da Vistoria Cautelar (arquivos ainda inexistentes). Mapeie a ordem e os títulos das seções do laudo (só títulos fixos, não o conteúdo do caso). (2) O `layout.json` guarda APENAS geometria e rótulos fixos: descarte nomes de pessoas, CPF, CREA, e-mails, endereços, número do apartamento e telefones do exemplar antes de gravar (OWASP A02); troque-os por placeholders Jinja2 nomeados. (3) Crie app/scripts/build_vistoria_residencial_templates.py que gera, de forma determinística e só a partir do layout.json, o .html.j2 e o .docx em 04_backend/templates/vistoria_residencial/. Use a marca de 04_backend/templates/assets/ como o LTIP faz. (4) Crie tests/test_vistoria_residencial_templates.py com um PDF sintético gerado no próprio teste (não leia 01_output-context/): teste o extrator, o JSON sem dados pessoais, a presença dos placeholders nos dois templates e que PDF e DOCX derivam do mesmo layout. Testes que exigem WeasyPrint usam skip com motivo explícito, pois ele não roda no Windows local. (5) Rode `pytest tests/test_vistoria_residencial_templates.py` e `ruff check .` a partir de 04_backend. Este arquivo não exige banco; não rode a suíte completa de integração. (6) Escreva 00_docs/backlog-auto/vistoria-residencial-templates.md: medidas obtidas, seções mapeadas, lista de placeholders, comandos e saídas, pendências (conferência visual do PDF depende de HT-09; pipeline de renderização é tarefa à parte, como o ltip_pipeline.py). Não toque em outros templates nem na pasta do LTIP, do RFO e da Vistoria Cautelar. Siga a "Regra de pronto" do BACKLOG.md.
```

### T11 · Pipeline de renderização da Vistoria Cautelar (vistoria_cautelar_pipeline.py)
- **Status:** done
- **Origem:** DEC-35
- **Papel:** Engenheiro Backend
- **Depende:** —
- **Ambiente:** docker
- **Dificuldade:** media
- **Toca:** 04_backend/app/services/report_generator/vistoria_cautelar_pipeline.py, 04_backend/tests/test_vistoria_cautelar_pipeline.py, 00_docs/backlog-auto/vistoria-cautelar-pipeline.md
- **Doc:** 00_docs/backlog-auto/vistoria-cautelar-pipeline.md
- **Pronto:** O módulo vistoria_cautelar_pipeline.py expõe renderizar_html, gerar_pdf e gerar_docx, no mesmo formato de ltip_pipeline.py. Cada função consome os templates de templates/vistoria_cautelar/. test_vistoria_cautelar_pipeline.py cobre HTML, DOCX, campo vazio como '—' e foto ausente. pytest e ruff check . passam em 04_backend, e o teste de PDF roda no container Docker ou é registrado como não executado. O resultado está em 00_docs/backlog-auto/vistoria-cautelar-pipeline.md.
- **Prompt:**
```text
Contexto: T09 entregou o extrator, o layout.json e os templates PDF (WeasyPrint) e DOCX (docxtpl) da Vistoria Cautelar de Recebimento em 04_backend/templates/vistoria_cautelar/ (ver 00_docs/backlog-auto/vistoria-cautelar-templates.md e DEC-35). O pipeline de renderização ainda não existe. T05 fez isso para o LTIP; use 04_backend/app/services/report_generator/ltip_pipeline.py e 00_docs/backlog-auto/ltip-pipeline.md como modelo estrutural. Trabalhe em 04_backend/.

Tarefa: crie 04_backend/app/services/report_generator/vistoria_cautelar_pipeline.py com `renderizar_html(contexto, fotos_bytes) -> str`, `gerar_pdf(contexto, fotos_bytes, destino) -> dict` e `gerar_docx(contexto, fotos_bytes, destino, *, template_path=None) -> dict`. Siga as mesmas convenções do ltip_pipeline: Jinja2/docxtpl com autoescape, fotos como data URI no HTML, o módulo não acessa o MinIO (quem chama entrega `fotos_bytes` por `storage_key`), mesmas chaves de métricas, `KeyError` para foto referenciada e ausente, campos vazios como '—' (DEC-33). Descubra as variáveis do contexto lendo o template .html.j2 e o layout.json, e documente a tabela de campos no Doc.

Testes: crie 04_backend/tests/test_vistoria_cautelar_pipeline.py com contexto sintético, sem depender de 01_output-context/. O teste de PDF deve usar `pytest.importorskip` ou skip se o WeasyPrint não carregar no Windows. Rode no Docker quando possível (docker compose a partir de 05_infra/). Rode `pytest` e `ruff check .` em 04_backend. O PostgreSQL fica em localhost:5433. Se não estiver no ar, registre que não rodou em vez de inventar resultado.

Não altere os templates gerados (se achar defeito neles, registre no Doc como proposta). Não altere nem apague 01_output-context/. Siga a 'Regra de pronto' do BACKLOG.md: registre fatos, comandos e saída dos testes em 00_docs/backlog-auto/vistoria-cautelar-pipeline.md. Não edite os documentos de gestão em 00_docs/projeto/ nem o BACKLOG.md. Commit: `feat(backend): pipeline de renderização da Vistoria Cautelar (DEC-35)` com `Refs DEC-35`. Não faça push.
```

### T12 · Pipeline de renderização da Vistoria de Imóvel Residencial (vistoria_residencial_pipeline.py)
- **Status:** done
- **Origem:** DEC-35
- **Papel:** Engenheiro Backend
- **Depende:** —
- **Ambiente:** docker
- **Dificuldade:** media
- **Toca:** 04_backend/app/services/report_generator/vistoria_residencial_pipeline.py, 04_backend/tests/test_vistoria_residencial_pipeline.py, 00_docs/backlog-auto/vistoria-residencial-pipeline.md
- **Doc:** 00_docs/backlog-auto/vistoria-residencial-pipeline.md
- **Pronto:** O módulo vistoria_residencial_pipeline.py expõe renderizar_html, gerar_pdf e gerar_docx, no mesmo formato de ltip_pipeline.py. Cada função consome os templates de templates/vistoria_residencial/. test_vistoria_residencial_pipeline.py cobre HTML, DOCX, campo vazio como '—' e foto ausente. pytest e ruff check . passam em 04_backend, e o teste de PDF roda no container Docker ou é registrado como não executado. O resultado está em 00_docs/backlog-auto/vistoria-residencial-pipeline.md.
- **Prompt:**
```text
Contexto: T10 entregou o extrator, o layout.json e os templates PDF (WeasyPrint) e DOCX (docxtpl) da Vistoria de Imóvel Residencial em 04_backend/templates/vistoria_residencial/ (ver 00_docs/backlog-auto/vistoria-residencial-templates.md e DEC-35). O pipeline de renderização ainda não existe. T05 fez isso para o LTIP; use 04_backend/app/services/report_generator/ltip_pipeline.py e 00_docs/backlog-auto/ltip-pipeline.md como modelo estrutural. Trabalhe em 04_backend/.

Tarefa: crie 04_backend/app/services/report_generator/vistoria_residencial_pipeline.py com `renderizar_html(contexto, fotos_bytes) -> str`, `gerar_pdf(contexto, fotos_bytes, destino) -> dict` e `gerar_docx(contexto, fotos_bytes, destino, *, template_path=None) -> dict`. Siga as mesmas convenções do ltip_pipeline: Jinja2/docxtpl com autoescape, fotos como data URI no HTML, o módulo não acessa o MinIO (quem chama entrega `fotos_bytes` por `storage_key`), mesmas chaves de métricas, `KeyError` para foto referenciada e ausente, campos vazios como '—' (DEC-33). Descubra as variáveis do contexto lendo o template .html.j2 e o layout.json, e documente a tabela de campos no Doc.

Testes: crie 04_backend/tests/test_vistoria_residencial_pipeline.py com contexto sintético, sem depender de 01_output-context/. O teste de PDF deve usar skip se o WeasyPrint não carregar no Windows. Rode no Docker quando possível (docker compose a partir de 05_infra/). Rode `pytest` e `ruff check .` em 04_backend. O PostgreSQL fica em localhost:5433. Se não estiver no ar, registre que não rodou em vez de inventar resultado.

Não altere os templates gerados (se achar defeito neles, registre no Doc como proposta). Não altere nem apague 01_output-context/. Siga a 'Regra de pronto' do BACKLOG.md: registre fatos, comandos e saída dos testes em 00_docs/backlog-auto/vistoria-residencial-pipeline.md. Não edite os documentos de gestão em 00_docs/projeto/ nem o BACKLOG.md. Commit: `feat(backend): pipeline de renderização da Vistoria Residencial (DEC-35)` com `Refs DEC-35`. Não faça push.
```

### T13 · Extrator e templates PDF/DOCX do RFIP (planilha de 479 MB)
- **Status:** done
- **Origem:** BL-12
- **Papel:** Engenheiro Backend
- **Depende:** —
- **Ambiente:** offline
- **Dificuldade:** alta
- **Toca:** 04_backend/app/scripts/rfip_layout_extractor.py, 04_backend/app/scripts/build_rfip_templates.py, 04_backend/templates/rfip/, 04_backend/tests/test_rfip_templates.py, 00_docs/backlog-auto/rfip-templates.md
- **Doc:** 00_docs/backlog-auto/rfip-templates.md
- **Pronto:** Existem templates/rfip/layout.json (só geometria e rótulos fixos), rfip_template.html.j2 e rfip_template.docx, todos gerados por build_rfip_templates.py a partir do mesmo layout.json. O extrator lê o xlsx em modo read_only/streaming. test_rfip_templates.py roda sobre uma planilha sintética, sem depender de 01_output-context/. pytest e ruff check . passam em 04_backend, ou o doc registra por que não rodaram. O resultado está em 00_docs/backlog-auto/rfip-templates.md.
- **Prompt:**
```text
Contexto: o RFIP (Relatório Fotográfico de Inspeção Predial) é o último dos 5 modelos sem template. O original é a planilha `Relatório Fotográfico de Inspeção Predial - CORTINA D'AMPAREZZO - Versão Final.xlsx` (~479 MB) em 01_output-context/. Nunca altere nem apague nada em 01_output-context/. O método é o ADR-13/DEC-25 (00_docs/arquitetura.md): medir o layout do original, gravá-lo em layout.json e derivar dele o .html.j2 (WeasyPrint) e o .docx (docxtpl), de modo que PDF e DOCX nunca divirjam. Referências de implementação: 04_backend/app/scripts/rfo_layout_extractor.py e build_rfo_templates.py (origem planilha, openpyxl) e os scripts equivalentes da Vistoria Cautelar (origem PDF), descritos em 00_docs/backlog-auto/vistoria-cautelar-templates.md. Leia também DEC-35 em 00_docs/projeto/decisoes.md: o layout.json guarda só geometria e rótulos fixos. Descarte nomes, CPF, e-mails e outros valores preenchidos do exemplar do cliente antes de gravar qualquer coisa no Git (OWASP A02). Trabalhe em 04_backend/.

Passos:
1. Escreva app/scripts/rfip_layout_extractor.py usando openpyxl com `read_only=True` (streaming). Não carregue o arquivo inteiro na memória e não extraia as imagens embutidas. Extraia dimensões de página, margens, tipografia, cores, grade fotográfica e rótulos fixos, medidos do original. Limite o trabalho às primeiras planilhas/linhas necessárias e documente o tempo e o pico de memória observados.
2. Grave 04_backend/templates/rfip/layout.json. Escreva build_rfip_templates.py, que gera rfip_template.html.j2 e rfip_template.docx do mesmo layout.json em um único comando (`python -m app.scripts.build_rfip_templates`).
3. Testes em 04_backend/tests/test_rfip_templates.py usando uma planilha SINTÉTICA criada no teste (tmp_path), sem depender de 01_output-context/. Cubra: o extrator lê em read_only, o layout.json não contém dado pessoal, o HTML e o DOCX derivam do mesmo layout.json, o .j2 compila e o DOCX abre com docxtpl.
4. Se o original não puder ser lido (arquivo ausente, memória insuficiente), registre o motivo no Doc e entregue o extrator e os testes sintéticos, sem inventar medidas.
5. Rode `pytest` e `ruff check .` em 04_backend. O PostgreSQL fica em localhost:5433. Se não estiver no ar, registre que não rodou em vez de inventar resultado.

Siga a 'Regra de pronto' do BACKLOG.md: registre fatos, números, comandos e saída dos testes em 00_docs/backlog-auto/rfip-templates.md, com decisões propostas como proposta. Não edite os documentos de gestão em 00_docs/projeto/ nem o BACKLOG.md. Commit: `feat(backend): extrator e templates do RFIP pelo método do ADR-13 (BL-12)` com `Refs BL-12`. Não faça push.
```

### T39 · Tornar o lint (ruff) bloqueante no CI
- **Status:** done
- **Origem:** BL-26
- **Papel:** devops
- **Depende:** —
- **Ambiente:** offline
- **Dificuldade:** baixa
- **Toca:** .github/workflows/ci.yml, 00_docs/backlog-auto/ci-lint-bloqueante.md
- **Doc:** 00_docs/backlog-auto/ci-lint-bloqueante.md
- **Pronto:** No passo «Lint (ruff)» de `.github/workflows/ci.yml` não há mais `continue-on-error: true` nem o comentário «Lint ainda não é bloqueante». A versão do ruff está fixada com a mesma versão registrada em `04_backend/ruff.toml` ou no doc `00_docs/backlog-auto/ruff.md`. `ruff check .` em `04_backend` sai com exit 0, e o YAML é válido (`python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"`). O doc registra o antes e o depois do trecho alterado, e diz explicitamente que o CI real não foi executado aqui.
- **Prompt:**
```text
Tarefa (BL-26, proposta da T04). Contexto: `00_docs/backlog-auto/ruff.md` (seção de propostas, perto da linha 95) propõe, para `.github/workflows/ci.yml`, remover `continue-on-error: true` do passo «Lint (ruff)» e o comentário «Lint ainda não é bloqueante», e fixar a versão do ruff para o resultado ser reprodutível. A T04 deixou `ruff check .` limpo em `04_backend` com a configuração versionada em `04_backend/ruff.toml`. Hoje o `ci.yml` tem `pip install ruff` (sem versão) perto da linha 77 e `continue-on-error: true` nas linhas ~83 e ~109.

Passos: (1) Leia `00_docs/backlog-auto/ruff.md` e `.github/workflows/ci.yml` inteiro, e `.github/pull_request_template.md`. (2) Descubra a versão de ruff usada na T04 (consulte o ruff.md; confirme com `ruff --version` a partir de `04_backend`, usando `04_backend/.venv` se existir). Fixe essa versão exata no `pip install` do passo de lint. (3) No passo «Lint (ruff)» remova `continue-on-error: true` e o comentário que diz que o lint não é bloqueante. Altere SÓ esse passo. O `continue-on-error: true` da linha ~109 pertence a outro passo: leia-o, explique no doc do que se trata e deixe como está, a menos que seja evidentemente o mesmo lint do backend duplicado. (4) Rode `ruff check .` a partir de `04_backend` e confirme exit 0. Se acusar erros, NÃO corrija código nesta tarefa: registre os erros no doc e mantenha o passo bloqueante apenas se o resultado for limpo; caso contrário, reverta a edição do CI e registre o motivo. (5) Valide o YAML com `python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"` (a partir da raiz do repositório). (6) Registre em `00_docs/backlog-auto/ci-lint-bloqueante.md`: trecho antes/depois, versão fixada, comandos e saídas, e a observação de que o workflow não foi executado no GitHub. Não altere `04_backend/requirements.txt` nem nenhum outro workflow. Não edite `00_docs/projeto/*`. Commit: `ci: torna o lint do backend bloqueante (BL-26)` com rodapé `Refs BL-26`. Não faça push. Siga a «Regra de pronto» do BACKLOG.md.
```

### T41 · Testes E2E (API mockada) do Portal do Cliente
- **Status:** done
- **Origem:** BL-32
- **Papel:** frontend
- **Depende:** —
- **Ambiente:** offline
- **Dificuldade:** media
- **Toca:** 03_frontend/e2e/portal.spec.ts, 00_docs/backlog-auto/portal-e2e.md
- **Doc:** 00_docs/backlog-auto/portal-e2e.md
- **Pronto:** Existe `03_frontend/e2e/portal.spec.ts` com testes Playwright e API mockada cobrindo: listagem de edificações do portal, dashboard/acompanhamento de uma edificação, listagem de documentos e download por URL pré-assinada (nunca a chave do storage), e redirecionamento/ocultação para perfil que não é `cliente`. Os testes passam com `npx playwright test e2e/portal.spec.ts`, e `npm run lint` e `npm run build` em `03_frontend` passam. O doc registra comandos, saídas e o que não foi coberto.
- **Prompt:**
```text
Tarefa (BL-32/BL-33 — o Portal do Cliente não tem teste E2E). Contexto: o Portal do Cliente está implementado em `03_frontend/app/portal/page.tsx` e `03_frontend/app/portal/documentos/page.tsx`, com navegação em `03_frontend/components/layout/nav-items.ts`; o backend correspondente é `04_backend/app/api/v1/portal.py` (`GET /portal/edificacoes`, `/portal/edificacoes/{id}/dashboard`, `/acompanhamento`, `GET /portal/relatorios`, `GET /portal/relatorios/{id}/download/{formato}`, que devolve URL pré-assinada). Já existem specs com API mockada que servem de modelo de estilo: `03_frontend/e2e/legenda-ia.spec.ts`, `foto-origem.spec.ts`, `anotacao-legenda-ia.spec.ts` e o auxiliar `03_frontend/e2e/helpers.ts`; leia-os primeiro, e `03_frontend/playwright.config.ts`.

Passos: (1) Leia as duas páginas do portal, `lib/api-client.ts` (funções do portal), `lib/types.ts` e `lib/use-usuario-atual.ts` para descobrir os formatos exatos das respostas e como o perfil é obtido. Não invente campos: use os que o código consome. (2) Crie `03_frontend/e2e/portal.spec.ts` com API mockada via `page.route` (como nos specs existentes; nenhum backend real): (a) cliente vê a lista de edificações do portal; (b) abre o dashboard/acompanhamento de uma edificação e vê os números mockados; (c) a página de documentos lista relatórios e o clique em baixar chama o endpoint de download e usa a URL pré-assinada devolvida (assert que a chave do storage não aparece na interface); (d) estados vazio e de erro (404/403 do mock) mostram a mensagem esperada; (e) perfil `auditor` ou `auxiliar` não vê o item de navegação do portal, ou é redirecionado, conforme o código atual fizer (descreva o comportamento real; se o código não faz nada, registre como lacuna no doc em vez de alterar a UI). (3) Não altere código de produção; se um teste revelar defeito, marque o teste com `test.fixme` e descreva no doc. Não adicione dependências nem variáveis de ambiente. (4) Rode a partir de `03_frontend`: `npx playwright test e2e/portal.spec.ts`, `npm run lint` e `npm run build`. Se o navegador do Playwright não estiver instalado, rode `npx playwright install chromium` e registre. Não relate resultado que não rodou. (5) Registre em `00_docs/backlog-auto/portal-e2e.md`: cenários, comandos, saídas, lacunas. Não edite `00_docs/projeto/*`. Commit: `test(frontend): E2E do Portal do Cliente com API mockada (BL-32)` com `Refs BL-32`. Não faça push. Siga a «Regra de pronto» do BACKLOG.md.
```

### T42 · Verificar os scripts de backup e restore com comandos simulados
- **Status:** done
- **Origem:** BL-29
- **Papel:** devops
- **Depende:** —
- **Ambiente:** offline
- **Dificuldade:** media
- **Toca:** 05_infra/backup, 00_docs/backlog-auto/backup-verificacao.md
- **Doc:** 00_docs/backlog-auto/backup-verificacao.md
- **Pronto:** Existe um teste de shell em `05_infra/backup/tests/` que roda `backup-db.sh` e `restore-db.sh` com `pg_dump`, `pg_restore`/`psql` e o cliente do MinIO substituídos por stubs no PATH, sem tocar em banco ou bucket reais, e verifica: dump válido antes da retenção apagar backups antigos, retenção preservada quando o dump falha, e o restore pedir confirmação explícita e gerar o dump `pre-restore`. `bash -n` passa nos dois scripts (e `shellcheck`, se instalado). O doc registra os comandos, saídas e qualquer defeito encontrado e corrigido.
- **Prompt:**
```text
Tarefa (BL-29 — scripts de backup nunca foram exercitados por teste automatizado). Contexto: `05_infra/backup/backup-db.sh` faz dump `pg_dump --format=custom` + espelho do bucket MinIO e só aplica retenção depois de um dump válido; `05_infra/backup/restore-db.sh` exige confirmação explícita e faz um dump `pre-restore` antes de restaurar. O cron sugerido está em `05_infra/README.md`. Esta tarefa NÃO usa banco nem MinIO reais e nunca deve rodar o restore contra dados existentes.

Passos: (1) Leia os dois scripts por inteiro, a seção de backup de `05_infra/README.md` e RNF-08 em `00_docs/estudo-do-contexto.md` (só essa seção). Anote quais comandos externos cada script chama (pg_dump, pg_restore, psql, mc/aws/rclone, docker exec etc.). (2) Rode `bash -n` em cada script e `shellcheck` se estiver instalado (registre se não estiver). (3) Crie `05_infra/backup/tests/test_backup_scripts.sh` (shell puro, sem dependência nova; pode usar um diretório temporário de `mktemp -d`) que coloca stubs dos comandos externos num diretório no início do PATH e variáveis de ambiente fictícias, e verifica: (a) backup feliz cria o arquivo de dump e executa a retenção só depois; (b) quando o stub de `pg_dump` falha ou produz arquivo vazio, o script sai com código ≠ 0 e NÃO apaga backups antigos (crie arquivos antigos falsos no diretório temporário); (c) restore sem a confirmação explícita aborta sem chamar `pg_restore`/`psql`; (d) restore com confirmação chama primeiro o dump `pre-restore`. Adapte-se ao que os scripts realmente fazem (nomes de variáveis, flags, formato da confirmação); não suponha. Use sempre diretórios temporários. (4) Se o teste revelar defeito real nos scripts, corrija o mínimo neles, mantendo o comportamento documentado, e descreva no doc. Se a correção mudar comportamento visível, registre-a como proposta em vez de aplicá-la. (5) Execute o teste (`bash 05_infra/backup/tests/test_backup_scripts.sh`) e registre a saída; no Windows use Git Bash. Não relate resultado que não rodou. (6) Registre em `00_docs/backlog-auto/backup-verificacao.md`: comandos externos mapeados, cenários, comandos, saídas, defeitos e propostas; destino externo do backup segue `[A ESCLARECER]` e fica fora. Não altere `.env`, nem crie pastas fora de `05_infra/backup/`. Não edite `00_docs/projeto/*`. Commit: `test(infra): verifica scripts de backup e restore com stubs (BL-29)` com `Refs BL-29`. Não faça push. Siga a «Regra de pronto» do BACKLOG.md.
```

### T43 · Zerar os 11 erros do ruff no backend e fixar a versão do ruff no CI
- **Status:** done
- **Origem:** DEC-46
- **Papel:** Engenheiro Backend
- **Depende:** —
- **Ambiente:** offline
- **Dificuldade:** baixa
- **Toca:** 04_backend/ (somente os arquivos com achados do ruff, listados no Doc), .github/workflows/ci.yml, 00_docs/backlog-auto/lint-backend-limpeza.md
- **Doc:** 00_docs/backlog-auto/lint-backend-limpeza.md
- **Pronto:** `ruff check .` em 04_backend sai com código 0 e sem achados; `ci.yml` instala `ruff==0.17.3` (ou a versão que o ruff local reportar); nenhuma mudança de comportamento (os testes que já passavam continuam passando, ou o Doc registra que o PostgreSQL não estava no ar); o Doc lista cada arquivo corrigido e a regra (RUF001, I001, RUF043, RUF005).
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md (raiz do repositório). Papel: Engenheiro Backend (.github/agents/backend.agent.md). Contexto: a DEC-46 (00_docs/projeto/decisoes.md, proposta da T39) registra que `ruff check .` em 04_backend (config em 04_backend/ruff.toml) acusa 11 erros em arquivos criados depois da T04: 2 RUF001 (caracteres ambíguos), 4 I001 (imports desordenados), 2 RUF043 e 3 RUF005 (concatenação de listas). Passos: (1) em 04_backend, rode `ruff check .` e anote cada achado (a lista pode ter mudado; vale o que o ruff reportar). (2) Corrija: use `ruff check . --fix` apenas para I001 e outros fixes seguros; RUF005 e RUF043 corrija à mão preservando o comportamento (ex.: `[*a, x]` no lugar de `a + [x]`; string de `pytest.raises(match=...)` como raw string); RUF001 troque o caractere ambíguo pelo equivalente ASCII sem alterar o sentido de mensagens exibidas ao usuário (se estiver em texto pt-BR legítimo, prefira `# noqa: RUF001` com justificativa curta ao invés de mudar o texto). Não altere lógica, nem o `ruff.toml`, nem arquivos sem achado. (3) Em .github/workflows/ci.yml troque a instalação do ruff por versão fixa igual à do ruff local (`ruff --version`; a DEC-46 cita 0.17.3). NÃO remova `continue-on-error` do passo de lint: isso depende da aprovação da DEC-46 pelo dono. (4) Se o PostgreSQL de 05_infra/docker-compose.yml (localhost:5433) estiver no ar, rode `pytest` em 04_backend; se não, registre que não rodou. (5) Registre no Doc 00_docs/backlog-auto/lint-backend-limpeza.md: achados antes/depois, arquivos alterados, versão fixada, o que fica para o dono (remover continue-on-error, status check obrigatório). Não edite decisoes.md nem outros documentos de gestão. Commit em Conventional Commits, ex.: `chore(backend): zera achados do ruff e fixa versão no CI (DEC-46)` com rodapé `Refs DEC-46`. Nunca faça push.
```

### T44 · Restore: abortar quando o dump pre-restore falhar e aplicar retenção aos pre-restore-*
- **Status:** done
- **Origem:** DEC-45
- **Papel:** Engenheiro DevOps
- **Depende:** —
- **Ambiente:** offline
- **Dificuldade:** baixa
- **Toca:** 05_infra/backup/restore-db.sh, 05_infra/backup/backup-db.sh (somente se a retenção morar nele), 05_infra/backup/tests/test_backup_scripts.sh, 00_docs/backlog-auto/restore-pre-restore.md
- **Doc:** 00_docs/backlog-auto/restore-pre-restore.md
- **Pronto:** `bash 05_infra/backup/tests/test_backup_scripts.sh` roda com stubs e passa: (a) `restore-db.sh` sai com código ≠ 0 e NÃO chama `pg_restore` quando o dump `pre-restore` falha ou sai vazio; (b) `FORCAR_SEM_PRE_RESTORE=1` permite seguir, com aviso explícito; (c) arquivos `pre-restore-*.dump` mais antigos que a retenção são removidos e os recentes permanecem; o bloco INFO do teste que documentava o problema virou asserção; o Doc descreve o novo comportamento.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md (raiz do repositório). Papel: Engenheiro DevOps (.github/agents/devops.agent.md). Contexto: a DEC-45 (00_docs/projeto/decisoes.md, proposta da T42, ainda aguardando aprovação do dono) aponta que 05_infra/backup/restore-db.sh termina o dump `pre-restore` com `|| true`: se ele falhar ou sair vazio, o script diz «Estado anterior salvo» e executa `pg_restore --clean`, destruindo o banco sem rede de segurança; além disso os `pre-restore-*.dump` nunca expiram. O teste com stubs está em 05_infra/backup/tests/test_backup_scripts.sh (45 verificações; leia como os stubs de pg_dump/pg_restore/psql/cliente do MinIO funcionam e o bloco INFO que registra o problema). Implemente a decisão proposta: (1) abortar com exit ≠ 0, antes de qualquer `pg_restore`, se o dump `pre-restore` falhar ou tiver tamanho zero, com a mensagem clara; a variável `FORCAR_SEM_PRE_RESTORE=1` ignora a checagem de forma explícita, emitindo aviso. (2) incluir os `pre-restore-*.dump` na retenção por `-mtime` já usada para os dumps normais (reutilize a variável de retenção existente; leia backup-db.sh e restore-db.sh para ver onde ela vive). Atualize o teste: converta o bloco INFO em asserções e adicione casos para falha do pre-restore, dump vazio, override e retenção. Rode o teste com `bash` (Git Bash no Windows serve; não precisa de Docker). Se uma variável de ambiente nova for documentada, registre-a em 05_infra/.env.example e na seção de backup de 05_infra/README.md só se já existir seção equivalente (não crie pastas). Registre no Doc 00_docs/backlog-auto/restore-pre-restore.md o comportamento novo, a saída do teste e a observação de que a DEC-45 continua proposta até o dono aprovar. Não edite decisoes.md, riscos.md ou status.md. Commit: `fix(infra): restore aborta sem pre-restore valido e expira pre-restore-* (DEC-45)` com rodapé `Refs DEC-45`. Nunca faça push.
```

---

## Bloco B — Revisão de regras e lacunas (pré-requisitos de B-04)

### T14 · Análise de lacunas do modelo de dados para o fluxo de legendas por IA (revisão de integração do BL-04)
- **Status:** done
- **Origem:** BL-04
- **Papel:** arquiteto-software
- **Depende:** —
- **Ambiente:** offline
- **Dificuldade:** baixa
- **Toca:** 00_docs/backlog-auto/modelagem-legendas-ia-lacunas.md
- **Doc:** 00_docs/backlog-auto/modelagem-legendas-ia-lacunas.md
- **Pronto:** O arquivo 00_docs/backlog-auto/modelagem-legendas-ia-lacunas.md existe e traz: (1) tabela do que já existe hoje em Foto, Anotacao e Storage (campo, tipo, arquivo de origem); (2) tabela de campos/entidades que faltam para RF-15/RN-16/RN-17/DEC-21, separando o que independe do provedor de LLM do que depende dele; (3) esboço da interface do adapter `LegendaIAClient` sem escolher fornecedor; (4) propostas de DEC (não gravadas em decisoes.md). Nenhum arquivo de código foi alterado e `git status` mostra só este arquivo novo.
- **Prompt:**
```text
Você está no monorepo Garra Engenharia. Tarefa SOMENTE de análise e documentação; não altere código, migrations nem os documentos de gestão compartilhados.

Contexto: BL-04 (modelagem de dados) está concluída, mas precisa de revisão de integração para o fluxo de legendas assistidas por IA (BL-34 a BL-39, bloqueadas pela escolha do provedor, B-04). Queremos deixar pronto tudo o que independe do provedor.

Passos:
1. Leia em 00_docs/estudo-do-contexto.md os requisitos RF-15, RN-16 e RN-17; em 00_docs/projeto/decisoes.md leia DEC-21 e DEC-19; em 00_docs/arquitetura.md leia a seção de modelo de dados (§3) e a do storage.
2. Leia os modelos em 04_backend/app/models/ (Foto e entidades relacionadas), os schemas de fotos em 04_backend/app/schemas/, 04_backend/app/api/v1/fotos.py e o serviço de storage em 04_backend/app/services/. Veja também as migrations em 04_backend/alembic/versions/ apenas para ler.
3. Escreva 00_docs/backlog-auto/modelagem-legendas-ia-lacunas.md com: (a) inventário do que existe hoje (campo, tipo, arquivo:linha); (b) lacunas para RF-15/RN-16/RN-17 (legenda gerada, status rascunho/aprovada, pendências/alertas, prompt e versão usados, quem aprovou e quando, tabela `prompts_ia`), marcando cada uma como 'independe do provedor' ou 'depende do provedor'; (c) esboço, em pseudo-código Python, da interface do adapter `LegendaIAClient` e de um cliente fake para testes; (d) ordem sugerida de implementação de BL-36, BL-37, BL-34, BL-38, BL-39, BL-35; (e) decisões propostas (texto), sem editar decisoes.md.
4. Siga a 'Regra de pronto' do BACKLOG.md (registrar fatos, caminhos e comandos no Doc). Não há testes a rodar, pois não há código; diga isso no Doc.
5. Commit opcional em Conventional Commits: `docs(00_docs): lacunas de modelagem para legendas por IA (BL-04)` com rodapé `Refs BL-04`. Nunca faça push.
```

### T15 · Revisão das regras de negócio de Visitas (RN-01/RN-02) com testes de lacuna
- **Status:** done
- **Origem:** BL-10
- **Papel:** backend
- **Depende:** —
- **Ambiente:** docker
- **Dificuldade:** media
- **Toca:** 04_backend/tests/test_visitas_lacunas.py, 00_docs/backlog-auto/revisao-regras-visitas.md
- **Doc:** 00_docs/backlog-auto/revisao-regras-visitas.md
- **Pronto:** Existe 00_docs/backlog-auto/revisao-regras-visitas.md com a matriz regra x código x teste (RF-03, RN-01, RN-02) e a lista de lacunas numeradas V1..Vn, e existe 04_backend/tests/test_visitas_lacunas.py com um teste `test_lacuna_*` por lacuna encontrada. Se o PostgreSQL (localhost:5433) estava no ar, a saída do pytest dos testes novos e da suíte test_visitas.py está colada no Doc; se não estava, o Doc diz explicitamente que os testes não rodaram. `ruff check .` em 04_backend passa. Nenhum código de produção foi alterado.
- **Prompt:**
```text
Você está no monorepo Garra Engenharia e atua como engenheiro backend (siga .github/agents/ backend). Esta tarefa é uma REVISÃO: encontrar e provar lacunas com testes, sem corrigi-las (uma tarefa posterior corrige).

Contexto: BL-10 (Registro de Visitas do RFO: equipe, serviços, medições) está 🟢 parcial. Já existe 04_backend/app/api/v1/visitas.py e 04_backend/tests/test_visitas.py. O mesmo método foi aplicado a Ocorrências (BL-14): veja 00_docs/backlog-auto/revisao-regras-ocorrencias.md (ou 00_docs/projeto/revisao-regras-ocorrencias.md, onde estiver) e o arquivo de testes `test_lacuna_*` correspondente em 04_backend/tests/ como modelo de formato.

Passos:
1. Em 00_docs/estudo-do-contexto.md leia RF-03, RN-01 e RN-02 (e RN-06/RN-18 se tocarem visitas); em 00_docs/projeto/decisoes.md leia DEC-27 (perfil auxiliar) e DEC-28 se relevantes.
2. Leia visitas.py, os modelos de Visita/VisitaMedicao/equipe em 04_backend/app/models/, os schemas em 04_backend/app/schemas/ e qualquer serviço usado; leia test_visitas.py.
3. Monte a matriz regra -> onde é imposta no código -> teste que cobre. Identifique lacunas: validação de enums, existência de FKs (inspeção, responsáveis), datas incoerentes, unidade de medição (DEC-29: livre por item), PUT sobrescrevendo campos imutáveis, permissões por papel (auxiliar x auditor x cliente), paginação/filtros sem validação.
4. Escreva 04_backend/tests/test_visitas_lacunas.py com um teste `test_lacuna_<n>_<assunto>` por lacuna, reutilizando as fixtures de conftest.py; o teste afirma o comportamento CORRETO (então falhará hoje) e cada um leva docstring com a regra violada. Se alguma lacuna não for testável, descreva-a no Doc.
5. Se o PostgreSQL de 05_infra/docker-compose.yml estiver no ar (localhost:5433), rode a partir de 04_backend: `pytest tests/test_visitas.py tests/test_visitas_lacunas.py` e cole a saída (falhas dos `test_lacuna_*` são esperadas; as de test_visitas.py não). Se não estiver no ar, registre que não rodou, sem inventar resultado. Rode `ruff check .`.
6. Registre tudo em 00_docs/backlog-auto/revisao-regras-visitas.md seguindo a 'Regra de pronto' do BACKLOG.md. Propostas de DEC vão apenas nesse Doc.
7. Commit: `test(backend): lacunas de regras de visitas (BL-10)` com rodapé `Refs BL-10`. Não altere código de produção, nem os documentos de gestão compartilhados. Nunca faça push.
```

### T16 · Revisão de segurança e regras do upload de fotos (RF-05/RNF-02) com testes de lacuna
- **Status:** done
- **Origem:** BL-11
- **Papel:** backend
- **Depende:** —
- **Ambiente:** docker
- **Dificuldade:** media
- **Toca:** 04_backend/tests/test_fotos_lacunas.py, 00_docs/backlog-auto/revisao-regras-fotos.md
- **Doc:** 00_docs/backlog-auto/revisao-regras-fotos.md
- **Pronto:** Existe 00_docs/backlog-auto/revisao-regras-fotos.md com a matriz requisito x código x teste (RF-05, RNF-02, OWASP A01/A03/A04 aplicáveis a upload) e lacunas F1..Fn, e existe 04_backend/tests/test_fotos_lacunas.py com um `test_lacuna_*` por lacuna testável. O Doc traz a saída do pytest se o PostgreSQL (localhost:5433) estava no ar, ou declara que não rodou. `ruff check .` em 04_backend passa. Nenhum código de produção foi alterado.
- **Prompt:**
```text
Você está no monorepo Garra Engenharia e atua como engenheiro backend (siga .github/agents/ backend). Esta tarefa é uma REVISÃO com testes de lacuna, sem corrigir código de produção.

Contexto: BL-11 (upload de fotos por clipboard e arquivo manual, vinculado a Visitas) está 🟢 parcial. Código: 04_backend/app/api/v1/fotos.py, serviço de storage (MinIO/S3 via boto3) em 04_backend/app/services/, testes em 04_backend/tests/test_fotos.py. Use como modelo de formato o relatório e os testes `test_lacuna_*` de Ocorrências (00_docs/backlog-auto/revisao-regras-ocorrencias.md ou 00_docs/projeto/revisao-regras-ocorrencias.md).

Passos:
1. Leia em 00_docs/estudo-do-contexto.md os requisitos RF-05, RNF-02, RN-15 e RNF-05/RNF-07; em 00_docs/projeto/revisao-seguranca-owasp.md a parte sobre upload (para não repetir achados já corrigidos); DEC-19 e DEC-29 (#4) em 00_docs/projeto/decisoes.md.
2. Leia fotos.py, o modelo Foto, os schemas e test_fotos.py.
3. Verifique, por leitura do código e do teste, lacunas como: validação do tipo real do arquivo (magic bytes, não só Content-Type/extensão), limite de tamanho, imagem corrompida, nome de arquivo/chave de storage controlado pelo servidor (path traversal), foto de visita inexistente ou de outro contexto, ordenação/legenda editável, permissões por papel (auxiliar pode enviar; cliente não; DEC-27), otimização de imagem no upload (RNF-02), exclusão que deixa objeto órfão no storage, e URL pré-assinada que vaza a chave.
4. Escreva 04_backend/tests/test_fotos_lacunas.py com um `test_lacuna_<n>_<assunto>` por lacuna testável, afirmando o comportamento CORRETO, com docstring da regra violada; use fixtures de conftest.py e o mesmo mecanismo de storage falso/real dos testes existentes. Lacunas não testáveis vão só para o Doc.
5. Se o PostgreSQL de 05_infra/docker-compose.yml estiver no ar (localhost:5433), rode a partir de 04_backend `pytest tests/test_fotos.py tests/test_fotos_lacunas.py` e cole a saída (falhas dos `test_lacuna_*` são esperadas). Se não estiver, registre que não rodou, sem inventar resultado. Rode `ruff check .`.
6. Escreva 00_docs/backlog-auto/revisao-regras-fotos.md conforme a 'Regra de pronto' do BACKLOG.md; decisões propostas ficam só nesse Doc.
7. Commit: `test(backend): lacunas de upload de fotos (BL-11)` com rodapé `Refs BL-11`. Não toque em app/, nos docs de gestão compartilhados nem em 01_output-context/. Nunca faça push.
```

### T17 · Re-medir o benchmark de geração PDF/DOCX com os pipelines finais
- **Status:** done
- **Origem:** BL-22
- **Papel:** arquiteto-software
- **Depende:** —
- **Ambiente:** docker
- **Dificuldade:** alta
- **Toca:** 00_docs/backlog-auto/benchmark-pipelines-finais.md
- **Doc:** 00_docs/backlog-auto/benchmark-pipelines-finais.md
- **Pronto:** 00_docs/backlog-auto/benchmark-pipelines-finais.md traz, para cada pipeline existente (RFO, LTIP, Vistoria Cautelar, Vistoria Residencial), tempo e memória de pico de PDF e DOCX com ao menos 150 fotos sintéticas e ~200 páginas, comparados com a meta de RNF-06 e com o resultado anterior (191 páginas/570 fotos em 44,2 s), ou declara explicitamente que o Docker/WeasyPrint não estava disponível e o que ficou sem medir. Os comandos usados e a saída bruta estão no Doc. Nenhum arquivo de código ou de dados do repositório foi alterado além do Doc.
- **Prompt:**
```text
Você está no monorepo Garra Engenharia. Tarefa de MEDIÇÃO e documentação; não altere código de produção.

Contexto: BL-22 mediu em 2026-08-05 a geração de 191 páginas/570 fotos em 44,2 s (ver 00_docs/projeto/relatorio-benchmark-geracao-pdf-docx.md) e dizia para re-medir quando os pipelines finais existissem. Agora existem os pipelines em 04_backend/app/services/report_generator/: rfo_pipeline.py, ltip_pipeline.py, vistoria_cautelar_pipeline.py e vistoria_residencial_pipeline.py (o do RFIP ainda não existe; não o inclua). O WeasyPrint não roda no Windows local: o PDF só pode ser gerado dentro do container do backend (docker compose, a partir de 05_infra/).

Passos:
1. Leia o relatório de benchmark anterior e o script que o gerou (procure em 04_backend/app/scripts/ e 04_backend/tests/ por 'benchmark'), a meta de RNF-06 em 00_docs/estudo-do-contexto.md e a API pública de cada pipeline (assinatura, dados de entrada, como o teste de cada um os alimenta, por exemplo tests/test_ltip_pipeline.py).
2. Verifique se o Docker está disponível (`docker version`) e suba, a partir de 05_infra/, apenas o necessário (backend; PostgreSQL só se o pipeline exigir). Se o Docker ou o WeasyPrint não estiver disponível, NÃO invente números: faça só o DOCX (docxtpl roda no host), meça-o e declare no Doc que o PDF não foi medido e por quê.
3. Escreva um script de medição FORA de qualquer pasta rastreada pelo Git de produção, em um diretório temporário (por exemplo o temp do sistema) ou em 00_docs/backlog-auto/ apenas se pequeno, gerando fotos sintéticas (JPEG com Pillow, tamanho realista) e entradas sintéticas para ~200 páginas e 150+ fotos. Meça tempo (perf_counter) e memória de pico (tracemalloc ou resource/psutil) por pipeline e formato, 3 execuções cada, reportando mediana.
4. Registre em 00_docs/backlog-auto/benchmark-pipelines-finais.md: ambiente (versões, CPU/RAM), tabela de resultados, comparação com a meta e com a medição de 2026-08-05, gargalos observados e recomendações. Comandos e saída bruta devem constar. Siga a 'Regra de pronto' do BACKLOG.md. Propostas de DEC ficam só no Doc.
5. Não leia nem altere arquivos de 01_output-context/ (use só dados sintéticos). Commit opcional: `docs(00_docs): benchmark dos pipelines finais (BL-22)` com rodapé `Refs BL-22`. Nunca faça push.
```

### T18 · Pipeline de renderização do RFIP (rfip_pipeline.py)
- **Status:** done
- **Origem:** DEC-36
- **Papel:** Engenheiro Backend
- **Depende:** T13, T05
- **Ambiente:** docker
- **Dificuldade:** media
- **Toca:** 04_backend/app/services/report_generator/rfip_pipeline.py, 04_backend/tests/test_rfip_pipeline.py, 00_docs/backlog-auto/rfip-pipeline.md
- **Doc:** 00_docs/backlog-auto/rfip-pipeline.md
- **Pronto:** rfip_pipeline.py expõe normalizar_contexto, renderizar_html, gerar_pdf e gerar_docx, com a mesma convenção de ltip_pipeline.py e consumindo templates/rfip/. tests/test_rfip_pipeline.py cobre HTML, DOCX, campo vazio como '—', foto ausente (KeyError) e o quadro-resumo; o teste de PDF é pulado com motivo explícito se o WeasyPrint não carregar. pytest dos arquivos de pipeline/templates do RFIP e ruff check . passam em 04_backend. O resultado está em 00_docs/backlog-auto/rfip-pipeline.md.
- **Prompt:**
```text
Contexto: a T13 entregou extrator e templates do RFIP em 04_backend/templates/rfip/ (layout.json, rfip_template.html.j2, rfip_template.docx; ver 00_docs/backlog-auto/rfip-templates.md e DEC-36 em 00_docs/projeto/decisoes.md). Falta o pipeline de renderização, que já existe para LTIP, Vistoria Cautelar e Vistoria Residencial. Modelo estrutural: 04_backend/app/services/report_generator/ltip_pipeline.py e vistoria_cautelar_pipeline.py, mais 00_docs/backlog-auto/ltip-pipeline.md e vistoria-cautelar-pipeline.md. Trabalhe a partir de 04_backend/.

Tarefa: crie app/services/report_generator/rfip_pipeline.py com `normalizar_contexto`, `renderizar_html(contexto, fotos_bytes) -> str`, `gerar_pdf(contexto, fotos_bytes, destino) -> dict` e `gerar_docx(contexto, fotos_bytes, destino, *, template_path=None) -> dict`. Convenções: Jinja2/docxtpl com autoescape, fotos como data URI no HTML, o módulo não acessa o MinIO (quem chama entrega `fotos_bytes` por `storage_key`), mesmas chaves de métricas dos outros pipelines, `KeyError` para foto referenciada e ausente, campos vazios como '—' (DEC-33). Descubra as variáveis do contexto lendo rfip_template.html.j2 e layout.json (incluindo o quadro-resumo e a numeração de páginas de DEC-36); não invente campos. Reaproveite helpers dos outros pipelines por import; não edite os arquivos deles nem os templates (defeito encontrado vira proposta no Doc).

Testes: crie tests/test_rfip_pipeline.py com contexto sintético, sem depender de 01_output-context/ (nunca altere nem apague esse diretório). O teste de PDF usa skip com motivo se o WeasyPrint não carregar. Rode `pytest tests/test_rfip_pipeline.py tests/test_rfip_templates.py` e `ruff check .`. A suíte completa exige o PostgreSQL de 05_infra em localhost:5433; se não estiver no ar, registre que não rodou em vez de inventar resultado.

Registre em 00_docs/backlog-auto/rfip-pipeline.md: API, tabela de campos do contexto, pendências (PDF real no container/HT-09, mapeamento banco → contexto), comandos e saídas. Não edite documentos de gestão em 00_docs/projeto/ nem o BACKLOG.md. Commit: `feat(backend): pipeline de renderização do RFIP (BL-12)` com `Refs DEC-36`. Siga a "Regra de pronto" do BACKLOG.md. Não faça push.
```

### T19 · Corrigir as lacunas do upload de fotos (storage_key, EXIF, validações)
- **Status:** done
- **Origem:** DEC-39
- **Papel:** Engenheiro Backend
- **Depende:** T16
- **Ambiente:** docker
- **Dificuldade:** media
- **Toca:** 04_backend/app/api/v1/fotos.py, 04_backend/app/services/image_processing.py, 04_backend/app/schemas/foto.py, 04_backend/tests/test_fotos_lacunas.py, 00_docs/backlog-auto/fotos-correcoes.md
- **Doc:** 00_docs/backlog-auto/fotos-correcoes.md
- **Pronto:** Cada lacuna das 9 de 00_docs/backlog-auto/revisao-regras-fotos.md está corrigida ou explicitamente adiada no doc com motivo. Em especial: o storage_key do vínculo é gerado/validado pelo servidor (rejeita '../', prefixo fora do esperado e objeto inexistente) e reprocessar_imagem aplica exif_transpose. Os testes test_lacuna_* passam com PostgreSQL e MinIO no ar, ou o doc registra que não rodaram. ruff check . passa. Sem migration e sem alteração no frontend.
- **Prompt:**
```text
Contexto: a T16 revisou o upload de fotos (BL-11) e deixou 00_docs/backlog-auto/revisao-regras-fotos.md (9 lacunas) e 04_backend/tests/test_fotos_lacunas.py (27 testes test_lacuna_*, que afirmam o comportamento correto e nunca rodaram por falta de PostgreSQL/MinIO). DEC-39 em 00_docs/projeto/decisoes.md é a proposta de correção (leia só ela). As lacunas graves: (1) `POST /ocorrencias|visitas/{id}/fotos` aceita `storage_key` do cliente sem validação (permite apontar para qualquer objeto do bucket e `DELETE /fotos/{id}` o apagaria, OWASP A01); (2) `reprocessar_imagem` descarta o EXIF sem `exif_transpose`, então foto de celular em pé sai deitada. Também faltam validação de `ordem`/`origem`/`legenda`, descarte de upload órfão e limite de corpo. Leia o doc de revisão, 04_backend/app/api/v1/fotos.py, app/services/image_processing.py, app/schemas/foto.py, app/services/storage/ e o teste.

Passos: (1) A partir de 04_backend, verifique se o PostgreSQL (localhost:5433) e o MinIO (localhost:9000) de 05_infra/docker-compose.yml estão no ar (`docker compose ps` em 05_infra; não suba nem derrube serviços). Se estiverem, rode `pytest tests/test_fotos.py tests/test_fotos_lacunas.py` e registre a linha de base; se não, siga com análise estática e registre que não rodou. (2) Corrija o mínimo por lacuna, na ordem de gravidade: a chave de storage passa a ser validada contra o prefixo esperado do contrato/visita/ocorrência e checada no storage (ou gerada pelo servidor), com erro de domínio RFC 7807 (DomainError, padrão existente); aplique `ImageOps.exif_transpose` antes do reprocessamento; valide os demais campos. Se algum test_lacuna_* estiver errado em relação à regra, corrija o teste e explique no doc. (3) Não crie migration, não altere models, não toque no frontend e não resolva o vínculo usuário↔contrato (fora de escopo, DEC-27/L15). (4) O comportamento de RBAC do auxiliar (BL-42) e os testes de tests/test_fotos.py e tests/test_rbac_auxiliar.py devem continuar verdes. (5) Rode `ruff check .` e os testes citados; não relate resultado que não rodou.

Registre em 00_docs/backlog-auto/fotos-correcoes.md: tabela das 9 lacunas (antes, depois, arquivo:linha, teste), o que ficou adiado, comandos e saídas. Não edite 00_docs/projeto/decisoes.md nem revisao-regras-fotos.md. Commit: `fix(backend): corrige lacunas de segurança e EXIF no upload de fotos (BL-11)` com `Refs DEC-39`. Siga a "Regra de pronto" do BACKLOG.md. Não faça push.
```

### T20 · Diagnosticar e reduzir o tempo de PDF do LTIP (RNF-06)
- **Status:** done
- **Origem:** DEC-40
- **Papel:** Engenheiro de Software
- **Depende:** T17, T05
- **Ambiente:** docker
- **Dificuldade:** alta
- **Toca:** 04_backend/app/services/report_generator/ltip_pipeline.py, 04_backend/app/scripts/build_ltip_templates.py, 04_backend/templates/ltip/, 04_backend/tests/test_ltip_pipeline.py, 04_backend/tests/test_ltip_templates.py, 00_docs/backlog-auto/ltip-desempenho.md
- **Doc:** 00_docs/backlog-auto/ltip-desempenho.md
- **Pronto:** 00_docs/backlog-auto/ltip-desempenho.md traz o perfil do PDF do LTIP (onde o WeasyPrint gasta o tempo), pelo menos uma otimização aplicada no pipeline ou no gerador de templates (templates/ltip/ regerado por `python -m app.scripts.build_ltip_templates`), e o antes/depois medido (mesmo cenário, ≥3 execuções, mediana) ou o registro de que o PDF não pôde ser renderizado. PDF e DOCX continuam derivando do mesmo layout.json; testes de LTIP passam; ruff check . passa.
- **Prompt:**
```text
Contexto: a T17 (00_docs/backlog-auto/benchmark-pipelines-finais.md; DEC-40 em 00_docs/projeto/decisoes.md, risco R-03) mediu o LTIP em 63,2 s para PDF+DOCX com só 137 páginas e 239 fotos, violando RNF-06 (200 páginas/150+ fotos em tempo aceitável); a conversão do WeasyPrint responde por 98–99,7 % do PDF, enquanto RFO e Vistoria Cautelar atendem. O WeasyPrint não roda no Windows local: use o container Docker de 04_backend (docker compose a partir de 05_infra; não derrube serviços existentes) ou registre que não foi possível. Leia o benchmark, 04_backend/app/services/report_generator/ltip_pipeline.py, app/scripts/build_ltip_templates.py, templates/ltip/ltip_template.html.j2 e, para comparação, o template/CSS do RFO (que é rápido).

Passos: (1) Reproduza a medição do LTIP com o mesmo gerador de dados sintéticos da T17 (procure o script/teste usado no doc de benchmark; se não existir como arquivo, crie dados sintéticos dentro de um teste ou script em /tmp, nunca em 01_output-context/). Meça 3 execuções e use a mediana. (2) Perfile onde o WeasyPrint gasta tempo (cProfile ou cronometragem por fase: parse HTML/CSS, layout, render) e liste hipóteses verificáveis: tabelas com `page-break-inside: avoid` aninhadas, fichas fotográficas em tabela vs. flex/grid, `position: running()` de cabeçalho/rodapé, `box-shadow`/`border-radius`, SVG da marca repetido por página, imagens data URI repetidas, CSS universal. (3) Aplique as otimizações que o perfil justificar, no gerador (build_ltip_templates.py) e/ou no pipeline (ex.: imagens decodificadas uma vez, `optimize_images`, estilo mais simples), sem mudar a aparência medida (margens, fontes, 2 fichas por página, RN-11) nem o layout.json. Regere os templates com `python -m app.scripts.build_ltip_templates` para manter PDF e DOCX derivados do mesmo layout. (4) Meça de novo no mesmo cenário e registre antes/depois. (5) Rode `pytest tests/test_ltip_pipeline.py tests/test_ltip_templates.py` e `ruff check .`; a suíte completa exige PostgreSQL em localhost:5433, e se não estiver no ar registre que não rodou. Não altere pipelines de outros tipos de relatório nem 01_output-context/.

Registre em 00_docs/backlog-auto/ltip-desempenho.md: perfil, hipóteses confirmadas/descartadas, mudanças com arquivo:linha, tabela antes/depois, o que continua acima do limite, comandos e saídas. Proposta de decisão nova vai no Doc, não em decisoes.md. Commit: `perf(backend): reduz o tempo de PDF do LTIP (RNF-06)` com `Refs DEC-40`. Siga a "Regra de pronto" do BACKLOG.md. Não faça push.
```

### T21 · Corrigir as lacunas de regras de Visitas (unicidade, domínio, CRUD de itens)
- **Status:** done
- **Origem:** DEC-38
- **Papel:** Engenheiro Backend
- **Depende:** T15, T19
- **Ambiente:** docker
- **Dificuldade:** alta
- **Toca:** 04_backend/app/api/v1/visitas.py, 04_backend/app/services/, 04_backend/app/schemas/visita.py, 04_backend/app/models/visita.py, 04_backend/alembic/versions/, 04_backend/tests/test_visitas_lacunas.py, 00_docs/backlog-auto/visitas-correcoes.md
- **Doc:** 00_docs/backlog-auto/visitas-correcoes.md
- **Pronto:** As 18 lacunas de 00_docs/backlog-auto/revisao-regras-visitas.md estão corrigidas ou adiadas com motivo no doc. Migration Alembic nova (com downgrade(), down_revision = head atual) adiciona o UNIQUE de seq_numero por inspeção e trata duplicatas existentes sem apagar dados. test_visitas_lacunas.py e test_visitas.py passam com PostgreSQL (schema migrado) no ar, ou o doc registra que não rodaram. `alembic upgrade head` seguido de `alembic downgrade -1` funciona quando o banco está disponível. ruff check . passa.
- **Prompt:**
```text
Contexto: a T15 revisou as regras de Visitas (BL-10, RN-01/RN-02) e deixou 00_docs/backlog-auto/revisao-regras-visitas.md (18 lacunas L1–L18) e 04_backend/tests/test_visitas_lacunas.py (26 funções que afirmam o comportamento correto e nunca rodaram: o banco respondia em localhost:5433 mas sem schema). DEC-38 em 00_docs/projeto/decisoes.md é a proposta de correção (leia só ela, e as seções de RN-01/RN-02 de 00_docs/estudo-do-contexto.md). Problemas: `seq_numero` sem UNIQUE (corrida gera duplicata), sem regra de uma visita por dia, data futura aceita, visita aceita em inspeção que não é RFO, quantidades sem restrição (500 acima de int32), `PUT` apaga `observacoes` omitida, e ausência de GET/PUT/DELETE dos itens (equipe, serviços, medições). Leia o doc de revisão, app/api/v1/visitas.py, app/models/visita.py, app/schemas/visita.py, tests/test_visitas.py e o teste de lacunas.

Passos: (1) A partir de 04_backend, verifique o PostgreSQL de 05_infra (`docker compose ps` em 05_infra; não suba nem derrube serviços). Se estiver no ar, rode `alembic upgrade head` UMA vez para criar o schema no banco de desenvolvimento (isto não apaga dados), depois `pytest tests/test_visitas.py tests/test_visitas_lacunas.py` e registre a linha de base. Se não estiver, siga com análise estática e registre que não rodou. (2) Corrija o mínimo por lacuna, com DomainError/NotFoundError (RFC 7807, padrão existente, 422/404/409): validações de domínio no schema/service; `PUT` com semântica de atualização parcial correta; endpoints GET/PUT/DELETE dos itens; mantenha RBAC do auxiliar (BL-42). (3) Migration nova: confira `alembic heads` (hoje d3b7c9e4f1a2, salvo se outra tarefa tiver acrescentado), use esse como down_revision, inclua `downgrade()`, e antes de criar o UNIQUE renumere duplicatas existentes de forma determinística em vez de apagá-las. A migration NÃO pode alterar tabelas de fotos nem de ocorrências. (4) NÃO resolva decisões em aberto do dono: vínculo usuário↔contrato (L15, DEC-27), regra de status da inspeção e mão de obra duplicada na mesma visita; registre-as como pendentes. Não toque no frontend. Se algum teste de lacuna estiver errado em relação à regra, corrija o teste e explique. (5) Rode `ruff check .` e os testes; não relate resultado que não rodou.

Registre em 00_docs/backlog-auto/visitas-correcoes.md: tabela L1–L18 (antes, depois, arquivo:linha, teste), a migration e o tratamento de duplicatas, pendências, comandos e saídas. Não edite 00_docs/projeto/decisoes.md nem revisao-regras-visitas.md. Commit: `fix(backend): corrige lacunas de regras de Visitas (BL-10)` com `Refs DEC-38`. Siga a "Regra de pronto" do BACKLOG.md. Não faça push.
```

### T22 · Extensão do modelo de dados para legendas por IA (prompts_ia e colunas em fotos)
- **Status:** done
- **Origem:** DEC-37
- **Papel:** Engenheiro Backend
- **Depende:** T14, T19, T21
- **Ambiente:** docker
- **Dificuldade:** alta
- **Toca:** 04_backend/app/models/foto.py, 04_backend/app/models/prompt_ia.py, 04_backend/app/models/__init__.py, 04_backend/app/schemas/foto.py, 04_backend/app/schemas/prompt_ia.py, 04_backend/alembic/versions/, 04_backend/tests/test_legenda_ia_modelo.py, 00_docs/backlog-auto/legenda-ia-modelo.md
- **Doc:** 00_docs/backlog-auto/legenda-ia-modelo.md
- **Pronto:** Existe migration Alembic nova (down_revision = head atual após a tarefa de Visitas, com downgrade()) que cria a tabela prompts_ia e as colunas de legenda IA em fotos conforme as lacunas de modelagem independentes do provedor de LLM (todas exceto L12, L13 e L22), incluindo unicidade parcial de `ativo` por `nome`. Modelos e schemas Pydantic atualizados. tests/test_legenda_ia_modelo.py cobre as constraints e passa com PostgreSQL no ar, ou o doc registra que não rodou. `alembic heads` tem uma única head. Nenhuma chamada a LLM, nenhuma dependência de provedor e nenhum endpoint de geração criados. ruff check . passa.
- **Prompt:**
```text
Contexto: a T14 (00_docs/backlog-auto/modelagem-legendas-ia-lacunas.md; DEC-37 em 00_docs/projeto/decisoes.md; BL-36 em 00_docs/projeto/backlog-tarefas.md; RF-15/RN-16/RN-17 em 00_docs/estudo-do-contexto.md e arquitetura.md §3 e ADR-12 — leia só essas seções) achou 22 lacunas entre o código e o modelo de dados previsto para legendas assistidas por IA: não existe a tabela `prompts_ia` nem as colunas de legenda IA em `fotos`. Só 3 lacunas (L12, L13, L22) dependem do provedor de LLM (B-04); as outras 19 podem ser feitas agora, com o Adapter testado por fake no futuro. Esta tarefa cobre SÓ a persistência (BL-36): migration, modelos e schemas.

Pré-requisito de ordem: esta tarefa roda depois da correção de Fotos e da de Visitas, que também mexem em app/api/v1/fotos.py e em migrations. Antes de começar, rode `git log --oneline -15` e `alembic heads` em 04_backend e use a head atual como down_revision; se houver mais de uma head, pare e registre no doc em vez de fazer merge de migrations.

Passos: (1) Leia o doc da T14 e implemente as 19 lacunas independentes do provedor: tabela `prompts_ia` (nome, versão, texto do prompt, `ativo`, auditoria; unicidade parcial de `ativo` por `nome`) e, em `fotos`, as colunas de legenda IA (texto gerado, status de validação com os estados propostos na DEC-37, pendências/alertas, referência ao prompt/versão usados, quem aprovou e quando, e a distinção entre legenda minuta e legenda aprovada, respeitando RN-16/RN-17). Use exatamente os nomes e estados propostos no doc/DEC-37; se houver ambiguidade, escolha a opção mais simples e registre. Migration com `downgrade()` completo; colunas novas anuláveis ou com default, sem apagar nem reescrever dados existentes. (2) Atualize app/models/foto.py, crie app/models/prompt_ia.py (registre em app/models/__init__.py) e os schemas Pydantic v2 em app/schemas/foto.py e app/schemas/prompt_ia.py, sem expor ainda endpoint de geração e sem alterar a lógica de app/api/v1/fotos.py além do necessário para os schemas continuarem válidos. (3) NÃO implemente L12, L13 e L22, o Adapter `LegendaIAClient`, a chamada a qualquer LLM, endpoints `/legenda-ia/gerar` ou frontend; registre-os como pendentes. Variável de ambiente nova, se alguma for indispensável, entra no .env.example correspondente (esperado: nenhuma). (4) Testes em tests/test_legenda_ia_modelo.py: constraints (unicidade parcial, estados válidos, FK do prompt), defaults e round-trip dos schemas. Se o PostgreSQL de 05_infra (localhost:5433) estiver no ar, rode `alembic upgrade head`, `alembic downgrade -1`, `alembic upgrade head` e `pytest tests/test_legenda_ia_modelo.py tests/test_fotos.py`; se não, registre que não rodou, sem inventar resultado. Rode `ruff check .`.

Registre em 00_docs/backlog-auto/legenda-ia-modelo.md: tabela das 22 lacunas (feita / pendente e por quê), DDL resultante, comandos e saídas. Não edite 00_docs/projeto/decisoes.md. Commit: `feat(backend): modelo de dados para legendas assistidas por IA (BL-36)` com `Refs DEC-37`. Siga a "Regra de pronto" do BACKLOG.md. Não faça push.
```

### T23 · Serviço de versões de prompt de IA e contrato LegendaIAClient com Fake (BL-37)
- **Status:** done
- **Origem:** BL-37
- **Papel:** Engenheiro Backend
- **Depende:** —
- **Ambiente:** docker
- **Dificuldade:** media
- **Toca:** 04_backend/app/services/prompt_ia_service.py, 04_backend/app/services/legenda_ia/, 04_backend/tests/test_prompt_ia_service.py, 00_docs/backlog-auto/legenda-ia-servico.md
- **Doc:** 00_docs/backlog-auto/legenda-ia-servico.md
- **Pronto:** `pytest tests/test_prompt_ia_service.py` e `ruff check .` em 04_backend passam (ou o doc registra que o PostgreSQL localhost:5433 não estava no ar e os testes não rodaram). Existem o serviço de versões imutáveis de `prompts_ia` com hash SHA-256, o Protocol `LegendaIAClient` e o `FakeLegendaIAClient`, todos com testes. Nenhuma migration criada. O doc está escrito com comandos e saídas.
- **Prompt:**
```text
Tarefa (BL-37, DEC-37 DP-2 e DP-6). Contexto: a T22 já criou a tabela `prompts_ia` e as colunas de legenda IA em `fotos` (migration f7c2a9d4e6b1), o model em 04_backend/app/models/ e o schema em 04_backend/app/schemas/prompt_ia.py. A DEC-37 em 00_docs/projeto/decisoes.md e os docs 00_docs/backlog-auto/legenda-ia-modelo.md e modelagem-legendas-ia-lacunas.md descrevem as regras. Leia só essas seções, mais o model de `PromptIA` e o de `Foto`, e um serviço existente como 04_backend/app/services/foto_service.py para seguir o padrão (DomainError RFC 7807, sessão assíncrona). A escolha do provedor de LLM (B-04) NÃO é necessária: não implemente cliente de provedor real. Passos: (1) Crie 04_backend/app/services/legenda_ia/__init__.py com o Protocol `LegendaIAClient` (método assíncrono que recebe a imagem em bytes, o conteúdo do prompt e a legenda bruta opcional, e devolve legenda sugerida, alertas e pendências) e `FakeLegendaIAClient` determinístico para testes. (2) Crie 04_backend/app/services/prompt_ia_service.py: criar nova versão do prompt (nome, conteúdo, versão incremental por nome, `prompt_conteudo_hash` = SHA-256 do conteúdo), ativar uma versão desativando as demais do mesmo nome na mesma transação (a unicidade parcial de `ativo` por nome já existe no banco), obter o prompt ativo, e recusar alterar o conteúdo de versão já criada (imutabilidade no serviço). (3) Escreva primeiro os testes em 04_backend/tests/test_prompt_ia_service.py (versões incrementais, hash estável, ativação exclusiva, imutabilidade, ausência de prompt ativo gera erro de domínio, Fake determinístico) e depois o código. (4) Não crie migration, não altere models nem schemas existentes, não crie endpoints e não toque no frontend. Se faltar algo no schema ou no model, registre como proposta no doc. (5) Rode `pytest tests/test_prompt_ia_service.py` e `ruff check .` a partir de 04_backend; os testes precisam do PostgreSQL de 05_infra/docker-compose.yml em localhost:5433 (`docker compose ps` a partir de 05_infra; não suba nem derrube serviços). Se não estiver no ar, registre que não rodou, sem inventar resultado. (6) Registre em 00_docs/backlog-auto/legenda-ia-servico.md a API criada, decisões propostas, comandos e saídas. Não edite os documentos de gestão em 00_docs/projeto/. Commit: `feat(backend): serviço de prompts de IA e contrato LegendaIAClient (BL-37)` com `Refs BL-37`. Não faça push. Siga a "Regra de pronto" do BACKLOG.md.
```

### T24 · Regra «só legenda aprovada entra no relatório» nos pipelines de PDF/DOCX (BL-38, DP-9)
- **Status:** done
- **Origem:** BL-38
- **Papel:** Engenheiro Backend
- **Depende:** —
- **Ambiente:** offline
- **Dificuldade:** media
- **Toca:** 04_backend/app/services/report_generator/, 04_backend/tests/test_legenda_relatorio.py, 00_docs/backlog-auto/legenda-relatorio.md
- **Doc:** 00_docs/backlog-auto/legenda-relatorio.md
- **Pronto:** `pytest tests/test_legenda_relatorio.py` e os testes existentes dos pipelines (test_rfo_templates, test_ltip_pipeline, test_ltip_templates e os demais test_*_pipeline.py) passam sem regressão, e `ruff check .` dá exit 0 em 04_backend. Existe um helper único de seleção de legenda usado por todos os pipelines, com testes cobrindo NULL, rascunho e aprovada. O doc está escrito.
- **Prompt:**
```text
Tarefa (BL-38, parte backend de relatório; DEC-37 DP-9, proposta ainda não aprovada pelo dono, então registre isso no doc). Contexto: a T22 acrescentou em `fotos` as colunas `legenda`, `legenda_ia_sugerida` e `status_validacao_ia` (NULL = sem sugestão; `rascunho`; `aprovada`). Hoje os pipelines em 04_backend/app/services/report_generator/ (rfo_pipeline.py, ltip_pipeline.py, rfip_pipeline.py, vistoria_cautelar_pipeline.py, vistoria_residencial_pipeline.py) montam a legenda da foto sem considerar esse status. Regra a implementar (DEC-37 DP-9): foto com `status_validacao_ia` NULL (manual ou legada) entra com `legenda`; `aprovada` entra com `legenda`; `rascunho` entra com `legenda` (a manual/anterior) e NUNCA com `legenda_ia_sugerida`. Leia a seção DEC-37 de 00_docs/projeto/decisoes.md, os cinco pipelines e o model 04_backend/app/models/foto.py. Passos: (1) Crie 04_backend/app/services/report_generator/legenda_foto.py com uma função pura de seleção da legenda a imprimir (sem acesso a banco) e uma função que sinaliza fotos de origem IA ainda em rascunho. (2) Escreva primeiro 04_backend/tests/test_legenda_relatorio.py (objetos simples sintéticos, sem banco): NULL, rascunho com e sem `legenda`, aprovada, legenda vazia. (3) Aplique o helper nos pipelines onde a legenda da foto é lida, com a menor mudança, sem alterar templates, layout.json, nem outros campos de contexto. (4) Não crie migration, não altere models e não toque no frontend nem em 01_output-context/. (5) Rode `pytest tests/test_legenda_relatorio.py` e os testes de templates e pipelines existentes que não exigem banco, e `ruff check .` a partir de 04_backend. Testes que exigem WeasyPrint ficam em skip com motivo (não roda no Windows local); registre isso. (6) Registre em 00_docs/backlog-auto/legenda-relatorio.md o que mudou por pipeline, as saídas dos testes e as pendências (integração com upload/edição e anotação no frontend ficam para BL-35/BL-39). Não edite os documentos de gestão em 00_docs/projeto/. Commit: `feat(backend): relatório usa só legenda aprovada de origem IA (BL-38)` com `Refs BL-38`. Não faça push. Siga a "Regra de pronto" do BACKLOG.md.
```

### T25 · Endpoints de geração e aprovação de legenda por IA com cliente Fake (BL-34)
- **Status:** done
- **Origem:** BL-34
- **Papel:** Engenheiro Backend
- **Depende:** T23
- **Ambiente:** docker
- **Dificuldade:** alta
- **Toca:** 04_backend/app/api/v1/fotos.py, 04_backend/app/services/foto_service.py, 04_backend/app/schemas/foto.py, 04_backend/app/api/deps.py, 04_backend/tests/test_legenda_ia_endpoints.py, 00_docs/backlog-auto/legenda-ia-endpoints.md
- **Doc:** 00_docs/backlog-auto/legenda-ia-endpoints.md
- **Pronto:** `pytest tests/test_legenda_ia_endpoints.py` mais os testes de fotos e RBAC já existentes (test_fotos*, test_rbac_auxiliar) e `ruff check .` passam em 04_backend com o PostgreSQL localhost:5433 no ar; senão o doc registra que não rodou. `POST /fotos/{id}/legenda-ia/gerar` grava só os campos de sugestão e `PUT /fotos/{id}` aprova com usuário e data vindos do token. Sem adapter de provedor real. Doc escrito.
- **Prompt:**
```text
Tarefa (BL-34 sem o adapter concreto; DEC-37 DP-3, DP-4, DP-5, DP-6). Contexto: a tarefa A (BL-37) entregou 04_backend/app/services/prompt_ia_service.py e 04_backend/app/services/legenda_ia/ com o Protocol `LegendaIAClient` e o `FakeLegendaIAClient`. A T22 criou as colunas de legenda IA em `fotos`. A escolha do provedor de LLM (B-04) continua pendente: o cliente é injetado por dependência (FastAPI Depends) e, enquanto não houver provedor real, a dependência de produção deve retornar 503 com DomainError claro (RFC 7807) quando não houver cliente configurado; os testes sobrescrevem a dependência com o Fake. Leia a seção DEC-37 de 00_docs/projeto/decisoes.md, 00_docs/backlog-auto/legenda-ia-modelo.md, 04_backend/app/api/v1/fotos.py, app/services/foto_service.py, app/schemas/foto.py e app/api/deps.py (perfis `require_auditor`/`require_equipe`). Passos: (1) Escreva primeiro tests/test_legenda_ia_endpoints.py. Cubra: gerar escreve apenas `legenda_ia_sugerida`, `legenda_bruta` (se enviada), alertas/pendências, `prompt_ia_id`, `prompt_conteudo_hash`, `legenda_ia_gerada_em` e `status_validacao_ia = rascunho`, e nunca altera `legenda`; foto inexistente 404; sem prompt ativo erro de domínio; aprovação via `PUT /fotos/{id}` define `status_validacao_ia = aprovada`, `aprovado_por_id` e `aprovado_em` a partir do token e ignora esses campos no payload; `legenda: null` explícito limpa a legenda e campo ausente preserva (use `model_fields_set`); edição manual sem sugestão mantém NULL; perfil `auxiliar` pode gerar e aprovar foto de visita/ocorrência (RN-18/DEC-27) conforme as regras já existentes em fotos; usuário sem permissão recebe 403. (2) Implemente `POST /fotos/{foto_id}/legenda-ia/gerar` e o ajuste de `PUT /fotos/{foto_id}` com a menor mudança, passando o usuário ao serviço. A imagem vem do storage service já existente (BL-07). (3) Não crie migration, não altere models e não toque no frontend nem implemente chamada a provedor real. (4) Mantenha verdes os testes de fotos (BL-11, T19) e de RBAC. (5) Rode `pytest tests/test_legenda_ia_endpoints.py`, os testes de fotos/RBAC existentes e `ruff check .` a partir de 04_backend; os testes exigem o PostgreSQL e o MinIO de 05_infra/docker-compose.yml (localhost:5433); verifique com `docker compose ps` a partir de 05_infra, não suba nem derrube serviços, e se não estiver no ar registre que não rodou, sem inventar resultado. (6) Registre em 00_docs/backlog-auto/legenda-ia-endpoints.md contrato dos endpoints, tabela de regras DP-3/4/5 com arquivo e linha, comandos e saídas, e a pendência do adapter concreto e da retenção de dados (R-10). Não edite os documentos de gestão em 00_docs/projeto/. Commit: `feat(backend): endpoints de legenda por IA com cliente injetável (BL-34)` com `Refs BL-34`. Não faça push. Siga a "Regra de pronto" do BACKLOG.md.
```

### T26 · Frontend: botão «Gerar legenda com IA» e aprovação no upload/edição de foto (BL-35)
- **Status:** done
- **Origem:** BL-35
- **Papel:** Engenheiro Frontend
- **Depende:** T25
- **Ambiente:** offline
- **Dificuldade:** alta
- **Toca:** 03_frontend/components/foto-upload.tsx, 03_frontend/components/legenda-ia-painel.tsx, 03_frontend/lib/types.ts, 03_frontend/lib/api-client.ts, 00_docs/backlog-auto/legenda-ia-frontend.md
- **Doc:** 00_docs/backlog-auto/legenda-ia-frontend.md
- **Pronto:** `npm run lint` e `npm run build` passam em 03_frontend. O componente `legenda-ia-painel.tsx` é usado em `foto-upload.tsx`: botão gerar, campo editável, alertas/pendências e confirmação explícita de aprovação, ocultos conforme o perfil. O doc descreve o contrato usado e registra que a verificação visual no navegador não foi feita, se for o caso.
- **Prompt:**
```text
Tarefa (BL-35, RF-15, RN-16, RN-17, DEC-21). Contexto: a tarefa C (BL-34) criou `POST /fotos/{foto_id}/legenda-ia/gerar` e o `PUT /fotos/{foto_id}` de aprovação (leia 00_docs/backlog-auto/legenda-ia-endpoints.md para o contrato real, e use só ele; não invente campos). A legenda gerada por IA é sempre um rascunho que o humano revisa e aprova (RN-16/RN-17). O backend pode responder 503 enquanto não houver provedor de LLM configurado; a UI deve tratar isso com mensagem clara. Leia 03_frontend/README.md, 03_frontend/components/foto-upload.tsx, components/photo-annotation-editor.tsx (somente leitura, o editor é da BL-39), lib/api-client.ts, lib/types.ts, lib/use-usuario-atual.ts e components/api-error-alert.tsx para reaproveitar padrões e componentes shadcn/ui existentes. Passos: (1) Acrescente os tipos da legenda IA em lib/types.ts e as chamadas em lib/api-client.ts. (2) Crie components/legenda-ia-painel.tsx: botão «Gerar legenda com IA» (estado de carregamento, erro via ApiErrorAlert), campo de texto editável com a sugestão, lista de alertas e pendências retornadas, texto de aviso de que a legenda só entra no relatório após aprovação, e botão «Aprovar legenda» que só habilita com texto não vazio e exige confirmação. (3) Integre o painel em foto-upload.tsx depois do upload, sem alterar o fluxo de upload, colagem e anotação existente. (4) Respeite o perfil via use-usuario-atual (o portal do cliente não vê o painel). Não toque em app/portal, no editor de anotação nem no backend. (5) Rode `npm run lint` e `npm run build` a partir de 03_frontend (instale dependências só se faltarem). Não rode `npm audit fix`. (6) Registre em 00_docs/backlog-auto/legenda-ia-frontend.md o contrato consumido, os estados da UI, comandos com saídas e o que não foi verificado no navegador. Não edite os documentos de gestão em 00_docs/projeto/. Commit: `feat(frontend): painel de legenda por IA com aprovação humana (BL-35)` com `Refs BL-35`. Não faça push. Siga a "Regra de pronto" do BACKLOG.md.
```

### T27 · Frontend: corrigir a origem 'upload' enviada ao vincular foto (backend aceita 'upload_manual')
- **Status:** done
- **Origem:** BL-31
- **Papel:** Engenheiro Frontend
- **Depende:** —
- **Ambiente:** offline
- **Dificuldade:** baixa
- **Toca:** 03_frontend/components/foto-upload.tsx, 03_frontend/lib/types.ts, 03_frontend/e2e/foto-origem.spec.ts, 00_docs/backlog-auto/frontend-origem-foto.md
- **Doc:** 00_docs/backlog-auto/frontend-origem-foto.md
- **Pronto:** `linkFoto` em foto-upload.tsx nunca envia 'upload' e usa 'upload_manual' (arquivo) ou 'lightshot'/'clipboard' conforme o backend aceita (DEC-39 C); `OrigemFoto` em types.ts cobre exatamente `upload_manual|lightshot|clipboard`; teste Playwright com API mockada confirma o corpo do POST de vínculo; `npm run lint` e `npm run build` em 03_frontend sem erro; Doc registra o resultado.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md (raiz do repositório). Papel: Engenheiro Frontend (.github/agents/frontend.agent.md). Contexto: a tarefa T26 (BL-35) achou um bug fora do seu escopo. Em 03_frontend/components/foto-upload.tsx (linhas ~56, 92-99, 109-123, 156, 320) o upload manual vincula a foto com `origem: "upload"`, mas o backend (04_backend/app/api/v1/fotos.py, DEC-39 C em 00_docs/projeto/decisoes.md) só aceita `upload_manual|lightshot|clipboard`, o que provavelmente gera 422 no vínculo. Confirme lendo fotos.py a lista exata de valores aceitos e como o clipboard é tratado (hoje o código mapeia clipboard → 'lightshot'; verifique se isso corresponde ao esperado e documente). Corrija o frontend: use um tipo `OrigemFoto` único em 03_frontend/lib/types.ts, mapeie a origem do editor ('upload' interno → 'upload_manual') apenas na chamada ao backend e remova qualquer string inválida. Crie 03_frontend/e2e/foto-origem.spec.ts (Playwright com a API mockada, no estilo de 03_frontend/e2e/legenda-ia.spec.ts) que intercepta o POST de vínculo e verifica o valor de `origem` no upload manual. Não altere o backend. Rode, a partir de 03_frontend: `npm run lint` e `npm run build` e o spec novo (se o Playwright não rodar, registre). Registre o resultado, os valores confirmados e o que não foi rodado em 00_docs/backlog-auto/frontend-origem-foto.md. Não edite os documentos de gestão compartilhados (backlog-tarefas.md, status.md, decisoes.md, riscos.md). Commit em Conventional Commits: `fix(frontend): ... (BL-31)` com rodapé `Refs BL-31`. Não faça push.
```

### T28 · Estender a entrega de fotos por url_fetcher ao RFO, Vistoria Cautelar e Vistoria Residencial
- **Status:** done
- **Origem:** DEC-41
- **Papel:** Engenheiro Backend
- **Depende:** —
- **Ambiente:** offline
- **Dificuldade:** media
- **Toca:** 04_backend/app/services/report_generator/rfo_pipeline.py, 04_backend/app/services/report_generator/vistoria_cautelar_pipeline.py, 04_backend/app/services/report_generator/vistoria_residencial_pipeline.py, 04_backend/tests/test_pipelines_url_fetcher.py, 00_docs/backlog-auto/pipelines-url-fetcher.md
- **Doc:** 00_docs/backlog-auto/pipelines-url-fetcher.md
- **Pronto:** Os três pipelines entregam as fotos ao WeasyPrint por `url_fetcher` como o `ltip_pipeline.py` já faz, mantendo `renderizar_html` autocontido (data URI) para testes e pré-visualização; os testes existentes de cada pipeline continuam passando; `tests/test_pipelines_url_fetcher.py` verifica, sem WeasyPrint, que o fetcher devolve os bytes da foto e recusa URLs fora do mapa; `ruff check` limpo nos arquivos tocados; o Doc registra o que rodou e o que não rodou (WeasyPrint não roda no Windows; PDF real não foi renderizado).
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md (raiz do repositório). Papel: Engenheiro Backend (.github/agents/backend.agent.md). Contexto: DEC-41 (00_docs/projeto/decisoes.md, proposta de T20) fez o `ltip_pipeline.py` (04_backend/app/services/report_generator/) entregar as fotos ao WeasyPrint por `url_fetcher` em vez de data URI, o que reduziu tempo e memória (ver 00_docs/backlog-auto/ltip-desempenho.md). O item (B) da decisão deixou estender o mesmo mecanismo aos demais pipelines para tarefa própria. Esta é essa tarefa, para `rfo_pipeline.py`, `vistoria_cautelar_pipeline.py` e `vistoria_residencial_pipeline.py` (NÃO o `rfip_pipeline.py`, que precisa ser medido com dados reais, nem o LTIP). Passos: (1) leia como o ltip_pipeline.py implementa o `url_fetcher` e reaproveite essa lógica; se ela for duplicada nos três, extraia um helper compartilhado num módulo novo em report_generator/ (e então inclua-o em `toca` no Doc), sem alterar o comportamento do LTIP; (2) mantenha `renderizar_html` autocontido com data URI; só `gerar_pdf` usa o fetcher; (3) o fetcher deve resolver apenas as URLs que o próprio pipeline registrou e levantar erro para qualquer outra (nada de ler arquivos arbitrários do disco ou da rede — OWASP A10/SSRF); (4) escreva 04_backend/tests/test_pipelines_url_fetcher.py com testes que não precisam de WeasyPrint nem de PostgreSQL. Rode a partir de 04_backend: `pytest` nos testes de cada pipeline (tests/test_rfo_templates.py, os de cautelar/residencial e o novo) e `ruff check` nos arquivos tocados. Os testes de PDF são pulados sem WeasyPrint; registre isso. Se o PostgreSQL de 05_infra (localhost:5433) não estiver no ar, registre que a suíte completa não rodou, sem inventar resultado. Registre resultado, medições (se houver) e decisões propostas em 00_docs/backlog-auto/pipelines-url-fetcher.md; não edite os documentos de gestão compartilhados. Commit: `perf(backend): ... (DEC-41)` com rodapé `Refs DEC-41`. Não faça push.
```

### T29 · Revisão de segurança OWASP dos endpoints novos de legenda por IA, fotos e visitas
- **Status:** done
- **Origem:** BL-23
- **Papel:** Engenheiro de Software
- **Depende:** —
- **Ambiente:** offline
- **Dificuldade:** media
- **Toca:** 00_docs/backlog-auto/seguranca-legenda-ia.md, 04_backend/tests/test_seguranca_legenda_ia.py
- **Doc:** 00_docs/backlog-auto/seguranca-legenda-ia.md
- **Pronto:** Relatório lista cada endpoint novo (`POST /fotos/{id}/legenda-ia/gerar`, `PUT /fotos/{id}` com aprovação, `DELETE /fotos/upload`, CRUD de visitas) com RBAC aplicado, riscos (A01 acesso, injeção de prompt, SSRF, vazamento de chave do storage, log de dados) e severidade; cada achado tem evidência (arquivo:linha); testes de lacuna só afirmam o comportamento correto e rodam ou têm a razão de não rodar registrada. Nenhum código de produção alterado.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md (raiz do repositório). Papel: Engenheiro de Software (revisão de segurança; consulte .github/prompts/31-revisao-seguranca-owasp.prompt.md e o relatório anterior 00_docs/projeto/revisao-seguranca-owasp.md, BL-23). Contexto: depois de BL-23 (2026-08-07) entraram endpoints novos, sem revisão de segurança: `POST /fotos/{id}/legenda-ia/gerar` e `PUT /fotos/{id}` com `aprovar_legenda_ia` (T25, 00_docs/backlog-auto/legenda-ia-endpoints.md), a dependência `get_legenda_ia_client` (503 até existir adapter), o serviço de prompts (`prompt_ia_service.py`, T23), `DELETE /fotos/upload` e as validações de storage_key (T19), e o CRUD de visitas/mão de obra/medições (T21). Esta tarefa é SOMENTE de revisão: não altere código de produção (04_backend/app). Verifique: RBAC por endpoint (`require_auditor`/`require_equipe` em app/api/deps.py; o perfil `cliente` não deve acessar nada disso; auxiliar não deve aprovar legenda se a regra RN-16/RN-17 proibir — confirme em 00_docs/estudo-do-contexto.md e DEC-37); IDOR entre contratos (usuário só age em fotos que pode ver; vínculo usuário↔contrato DEC-27 está aberto, registre como risco); o aprovador vir do token e não do corpo; injeção de prompt (texto livre do usuário chegando ao LLM e a resposta do LLM gravada sem sanitização; limite de tamanho); limite de taxa/custo do endpoint de geração (abuso gera custo); logs sem chave de storage nem conteúdo sensível; URLs pré-assinadas; mensagens de erro. Escreva em 04_backend/tests/test_seguranca_legenda_ia.py testes que afirmam o comportamento correto para as lacunas que consiga demonstrar com o `FakeLegendaIAClient` (use os fixtures existentes de tests/conftest.py e o estilo de tests/test_seguranca.py). Tente rodar a partir de 04_backend `pytest tests/test_seguranca_legenda_ia.py` com o PostgreSQL de 05_infra (localhost:5433); se não estiver no ar ou a suíte falhar por memória/greenlet, registre isso e NÃO invente resultado. Registre achados (ID, severidade, evidência, correção sugerida) e decisões propostas em 00_docs/backlog-auto/seguranca-legenda-ia.md; não edite os documentos de gestão compartilhados. Commit: `docs(backend): ... (BL-23)` com rodapé `Refs BL-23`. Não faça push.
```

### T30 · Confirmar a compatibilidade do storage com os artefatos de legenda por IA e a limpeza de órfãos
- **Status:** done
- **Origem:** BL-07
- **Papel:** Engenheiro Backend
- **Depende:** T28
- **Ambiente:** offline
- **Dificuldade:** media
- **Toca:** 04_backend/app/services/storage_service.py, 04_backend/tests/test_storage_legenda_ia.py, 00_docs/backlog-auto/storage-legenda-ia.md
- **Doc:** 00_docs/backlog-auto/storage-legenda-ia.md
- **Pronto:** Doc responde, com evidência, se o storage service atende o fluxo de legendas (chave determinística, URL pré-assinada de leitura DEC-39 E, listagem de órfãos); entrega uma função de listagem de objetos órfãos (chaves no bucket sem registro em `fotos`) testada com cliente S3 falso, sem apagar nada; `ruff check` limpo nos arquivos tocados; o que não rodou fica registrado.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md (raiz do repositório). Papel: Engenheiro Backend (.github/agents/backend.agent.md). Contexto: BL-07 (storage MinIO/S3, 04_backend/app/services/storage_service.py) foi concluída com a ressalva de que deve ser confirmada como compatível com o fluxo de legendas/artefatos gerados por IA. Pendências relacionadas de BL-11 (00_docs/backlog-auto/fotos-correcoes.md, DEC-39): URL pré-assinada de leitura (item E) e job de limpeza de órfãos. Faça: (1) leia o storage service e 04_backend/app/api/v1/fotos.py e responda no Doc, com arquivo:linha, se o service cobre: upload, download, URL pré-assinada de leitura com expiração curta, checagem de existência e listagem por prefixo; (2) acrescente SOMENTE o que faltar e for pequeno: uma função `listar_orfaos(chaves_registradas)` (ou nome coerente com o módulo) que devolve as chaves do bucket sem registro, SEM apagar nada (a exclusão automática exige decisão do dono; proponha a política no Doc); (3) teste em 04_backend/tests/test_storage_legenda_ia.py com cliente S3 falso/stub (sem MinIO e sem PostgreSQL); (4) NÃO altere fotos.py (a tarefa B altera pipelines, esta depende dela só para evitar conflito de execução; fotos.py fica fora do escopo — registre no Doc a mudança necessária no router em vez de fazê-la). Rode a partir de 04_backend: `pytest tests/test_storage_legenda_ia.py` e `ruff check` nos arquivos tocados. Se o PostgreSQL de 05_infra (localhost:5433) ou o MinIO não estiverem no ar, registre que não rodou os testes de integração. Registre resultado e decisões propostas em 00_docs/backlog-auto/storage-legenda-ia.md; não edite os documentos de gestão compartilhados. Commit: `feat(backend): ... (BL-07)` com rodapé `Refs BL-07`. Não faça push.
```

### T52 · Rodar no PostgreSQL de 05_infra as suítes de Ocorrências, Visitas, Fotos e emissão do RFO que nunca executaram
- **Status:** done
- **Origem:** R-14
- **Papel:** Engenheiro de Software
- **Depende:** —
- **Ambiente:** docker
- **Dificuldade:** baixa
- **Toca:** 00_docs/backlog-auto/execucao-testes-banco.md
- **Doc:** 00_docs/backlog-auto/execucao-testes-banco.md
- **Pronto:** O doc lista, por arquivo de teste (test_ocorrencias_regras, test_visitas*, test_fotos*, test_relatorios_rfo_api, test_rfo_contexto, test_portal_cliente), a contagem passed/failed/skipped/xfail e a saída literal dos comandos, ou registra que o PostgreSQL (localhost:5433) não respondeu. Nenhum arquivo fora do doc foi alterado.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md (raiz do repositório). Papel: Engenheiro de Software. Contexto: várias tarefas anteriores (T08, T15, T16, T45, T46, T50, T51) registraram que os testes com banco NÃO rodaram (riscos R-13/R-14 em 00_docs/projeto/riscos.md). Esta tarefa só EXECUTA e REGISTRA, sem corrigir código. Passos: (1) a partir de 05_infra/ confira com `docker compose ps` se PostgreSQL (localhost:5433) e MinIO estão no ar; se não estiverem, tente `docker compose up -d`; se não houver Docker, escreva isso no doc e pare, sem inventar resultado. (2) A partir de 04_backend/, rode `alembic upgrade head` apenas se o banco estiver sem schema, anotando o resultado. (3) Rode, um arquivo por vez para evitar a queda por `asyncio.run` descrita em R-15: tests/test_ocorrencias_regras.py, tests/test_visitas*.py, tests/test_fotos*.py, tests/test_relatorios_rfo_api.py, tests/test_rfo_contexto.py, tests/test_portal_cliente.py. (4) Em 00_docs/backlog-auto/execucao-testes-banco.md registre data, versões, comandos, contagens e a lista de falhas com a causa provável de cada uma (ambiente x código), e proponha, sem aplicar, as correções. Não edite código, testes, nem os documentos de gestão (00_docs/projeto/*) nem o BACKLOG.md. Não altere 01_output-context/. Commit: `docs(00_docs): resultado dos testes com banco (R-14)` com `Refs R-14`. Não faça push.
```

### T53 · RFO: tratar ART de execução ausente no contexto e no template
- **Status:** done
- **Origem:** T50
- **Papel:** Engenheiro Backend
- **Depende:** —
- **Ambiente:** offline
- **Dificuldade:** baixa
- **Toca:** 04_backend/app/services/report_generator/rfo_contexto.py, 04_backend/templates/rfo/rfo_template.html.j2, 04_backend/tests/test_rfo_art_execucao.py, 00_docs/backlog-auto/rfo-art-execucao.md
- **Doc:** 00_docs/backlog-auto/rfo-art-execucao.md
- **Pronto:** Com `executores[].art_execucao` nulo ou vazio, o contexto do RFO traz '—' (padrão DEC-33) e o PDF/DOCX nunca imprime 'None'; testes novos em test_rfo_art_execucao.py (sem banco, com contexto sintético) passam; `pytest` do arquivo e `ruff check .` limpos em 04_backend.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md (raiz do repositório). Papel: Engenheiro Backend (.github/agents/backend.agent.md). Contexto: a T50 (00_docs/backlog-auto/rfo-validacao-completude.md) deixou uma lacuna: `executores[].art_execucao` pode ser nulo no banco (04_backend/app/models/contrato_executor.py) e o template `04_backend/templates/rfo/rfo_template.html.j2` (linha ~94) imprime `None`. Em 04_backend/app/services/report_generator/rfo_contexto.py a função `_executor_ctx` (linha ~76) repassa o valor cru. Leia também a DEC-33 em 00_docs/projeto/decisoes.md (campos vazios viram '—'). Implemente: valor nulo/vazio/só espaços vira '—' no contexto, sem alterar o formato dos demais campos; confira que o DOCX (rfo_pipeline.py, só leitura) também imprime '—'. Crie 04_backend/tests/test_rfo_art_execucao.py com testes que não dependam de banco (chame a função auxiliar diretamente e renderize o template com contexto sintético; se o WeasyPrint não existir, teste só o HTML e o DOCX). Rode, a partir de 04_backend, `pytest tests/test_rfo_art_execucao.py tests/test_rfo_pipeline.py` e `ruff check .`; se algum teste com banco não rodar, registre. Registre fatos e saídas em 00_docs/backlog-auto/rfo-art-execucao.md. Não edite 00_docs/projeto/* nem BACKLOG.md; não altere 01_output-context/. Commit: `fix(backend): RFO imprime — quando a ART de execução falta (DEC-47)` com `Refs DEC-47`. Não faça push.
```

---

## Bloco C — Endurecimento de legendas por IA e storage (DEC-42/43/44)

### T31 · Impor enum fechado de `origem` da foto no payload de vínculo (backend)
- **Status:** done
- **Origem:** DEC-43
- **Papel:** backend
- **Depende:** —
- **Ambiente:** docker
- **Dificuldade:** baixa
- **Toca:** 04_backend/app/schemas/foto.py, 04_backend/tests/test_foto_origem_enum.py, 00_docs/backlog-auto/foto-origem-enum.md
- **Doc:** 00_docs/backlog-auto/foto-origem-enum.md
- **Pronto:** `FotoVincularPayload.origem` aceita só `upload_manual|lightshot|clipboard` (422 para qualquer outro valor). `tests/test_foto_origem_enum.py` cobre valores válidos, inválido e ausente (se houver default) e passa; `pytest` dos testes de fotos e `ruff check .` em 04_backend estão verdes, ou o doc registra o que não rodou e por quê. Nenhuma migration criada.
- **Prompt:**
```text
Tarefa (DEC-43, proposta da T27). Contexto: em 04_backend/app/schemas/foto.py o campo `origem` de `FotoVincularPayload` é `str` livre e não há CHECK no banco; o único contrato (`upload_manual|lightshot|clipboard`) existe no frontend (`OrigemFoto` em 03_frontend/lib/types.ts) e o seed usa `upload_manual`. Leia a seção DEC-43 de 00_docs/projeto/decisoes.md, 00_docs/backlog-auto/frontend-origem-foto.md, 04_backend/app/schemas/foto.py, 04_backend/app/api/v1/fotos.py (só para ver como o payload é usado) e 04_backend/tests/test_fotos.py e test_fotos_lacunas.py (para não quebrar testes que enviam `origem`). Passos: (1) Procure em todo 04_backend (app/, tests/, scripts de seed) qualquer valor de `origem` usado hoje (`grep`); liste-os no doc. Se algum teste ou seed usar valor fora do enum, NÃO edite arquivos fora de `toca`: registre-o no doc como pendência e escolha a implementação que não os quebre sem motivo (se um teste existente enviar valor inválido, descreva-o no doc). (2) Troque o tipo por `Literal["upload_manual","lightshot","clipboard"]` (ou Enum equivalente) apenas no payload de vínculo, mantendo o default atual se existir; a resposta de leitura (`FotoRead`) deve continuar aceitando valores antigos já gravados (não valide na saída). (3) Crie tests/test_foto_origem_enum.py: testes de schema (Pydantic puro, sem banco) para válidos/ inválido, e um teste de endpoint (422 em `POST` de vínculo com `origem` inválida) que só roda com PostgreSQL. (4) NÃO crie migration nem CHECK no banco (a normalização de dados antigos é tarefa à parte); registre isso como pendência. (5) Rode `pytest tests/test_foto_origem_enum.py tests/test_fotos.py tests/test_fotos_lacunas.py` e `ruff check .` a partir de 04_backend; o PostgreSQL fica em localhost:5433 (`docker compose ps` a partir de 05_infra; não suba nem derrube serviços); se não estiver no ar, registre que os testes de endpoint não rodaram em vez de inventar resultado. (6) Registre no doc os valores encontrados, a mudança, os comandos e as saídas. Commit: `feat(backend): enum fechado de origem da foto (DEC-43)` com `Refs DEC-43`. Não edite os documentos de gestão em 00_docs/projeto/ nem o BACKLOG.md. Siga a "Regra de pronto" do BACKLOG.md.
```

### T32 · Storage: expor `LastModified` e script de relatório de órfãos em dry-run
- **Status:** done
- **Origem:** DEC-44
- **Papel:** backend
- **Depende:** —
- **Ambiente:** offline
- **Dificuldade:** media
- **Toca:** 04_backend/app/services/storage_service.py, 04_backend/app/scripts/relatorio_orfaos.py, 04_backend/tests/test_relatorio_orfaos.py, 00_docs/backlog-auto/orfaos-relatorio.md
- **Doc:** 00_docs/backlog-auto/orfaos-relatorio.md
- **Pronto:** `storage_service.py` expõe a data de modificação dos objetos (sem quebrar `list_keys`/`listar_orfaos`), e `python -m app.scripts.relatorio_orfaos` gera, em dry-run, a lista de órfãos com idade > 24 h sem apagar nada. `tests/test_relatorio_orfaos.py` usa S3 falso e passa; `tests/test_storage_legenda_ia.py` continua verde; `ruff check .` em 04_backend verde.
- **Prompt:**
```text
Tarefa (DEC-44, proposta da T30, itens 1-3). Contexto: a T30 adicionou `exists`, `list_keys` e `listar_orfaos` (só leitura) em 04_backend/app/services/storage_service.py, com testes em 04_backend/tests/test_storage_legenda_ia.py usando um S3 falso. Não existe rotina de limpeza e `LastModified` não é exposto. Leia a seção DEC-44 de 00_docs/projeto/decisoes.md, 00_docs/backlog-auto/storage-legenda-ia.md, storage_service.py, test_storage_legenda_ia.py e um script existente em 04_backend/app/scripts/ (para seguir o padrão de CLI). Passos: (1) Acrescente ao storage uma forma de listar chaves COM `LastModified` (ex.: `list_objects(prefix)` devolvendo chave e data), sem mudar a assinatura nem o comportamento de `list_keys` e `listar_orfaos`; atualize o S3 falso do teste existente só se indispensável — e como test_storage_legenda_ia.py não está em `toca`, crie o seu próprio falso em test_relatorio_orfaos.py. (2) Crie app/scripts/relatorio_orfaos.py (`python -m app.scripts.relatorio_orfaos [--idade-minima-horas 24] [--prefixo fotos/]`): consulta as chaves de foto vinculadas no banco (use a sessão síncrona/assíncrona já existente no projeto; isole a consulta em função injetável para testar sem banco), compara com `listar_orfaos`, filtra por idade > limite e imprime/escreve um relatório (tabela e contagem). É SOMENTE dry-run: o script NÃO pode ter nenhuma chamada de exclusão nem flag que apague; registre no doc que apagar exige aprovação manual da lista (DEC-44 item 3) e fica para tarefa futura. (3) Não crie variável de ambiente nova sem registrá-la no .env.example correspondente; não crie pastas na raiz. (4) Crie tests/test_relatorio_orfaos.py com S3 falso e consulta de vínculos injetada: objeto novo (<24 h) não aparece, antigo e sem vínculo aparece, antigo e vinculado não aparece, nada é apagado (verifique que o falso não recebeu delete). Os testes não podem exigir banco nem MinIO. (5) Rode `pytest tests/test_relatorio_orfaos.py tests/test_storage_legenda_ia.py` e `ruff check .` a partir de 04_backend. (6) Registre no doc a API, o formato do relatório, o que ficou fora (exclusão, prefixos `fotos/` x `ia/` do item 4 de DEC-44) e os comandos com saídas. Commit: `feat(backend): relatório de órfãos do storage em dry-run (DEC-44)` com `Refs DEC-44`. Não edite os documentos de gestão em 00_docs/projeto/ nem o BACKLOG.md. Siga a "Regra de pronto" do BACKLOG.md.
```

### T33 · Legenda por IA: aprovação só por auditor e invalidação ao editar ou regerar (backend)
- **Status:** done
- **Origem:** DEC-42
- **Papel:** backend
- **Depende:** T31
- **Ambiente:** docker
- **Dificuldade:** media
- **Toca:** 04_backend/app/api/v1/fotos.py, 04_backend/app/services/foto_service.py, 04_backend/tests/test_legenda_ia_endpoints.py, 04_backend/tests/test_legenda_ia_aprovacao.py, 00_docs/backlog-auto/legenda-ia-aprovacao.md
- **Doc:** 00_docs/backlog-auto/legenda-ia-aprovacao.md
- **Pronto:** Só `auditor` consegue aprovar legenda IA (auxiliar recebe 403 ao enviar `aprovar_legenda_ia`, mas continua gerando e editando rascunho); regerar legenda ou mudar `legenda` de foto aprovada zera `aprovado_por_id/aprovado_em` e volta o status a `rascunho`. `tests/test_legenda_ia_aprovacao.py` cobre os quatro casos, `test_legenda_ia_endpoints.py` foi ajustado ao novo comportamento e `pytest tests/test_legenda_ia_endpoints.py tests/test_legenda_ia_aprovacao.py` e `ruff check .` passam com PostgreSQL no ar, ou o doc registra que não rodaram.
- **Prompt:**
```text
Tarefa (DEC-42 itens A e B, proposta da T29; SEG-IA-03, SEG-IA-04, SEG-IA-05 de 00_docs/backlog-auto/seguranca-legenda-ia.md). Contexto: os endpoints `POST /fotos/{id}/legenda-ia/gerar` e `PUT /fotos/{id}` (campo `aprovar_legenda_ia`) foram feitos pela T25 (ver 00_docs/backlog-auto/legenda-ia-endpoints.md) com `FakeLegendaIAClient`. Hoje o auxiliar também aprova, regerar legenda aprovada mantém `aprovado_*` e editar `legenda` de foto aprovada mantém a aprovação (DP-10 de DEC-37). RN-16 e RN-18 reservam a aprovação ao responsável. Leia: seção DEC-42 e DEC-37 de 00_docs/projeto/decisoes.md (só elas), seguranca-legenda-ia.md, legenda-ia-endpoints.md, 04_backend/app/api/v1/fotos.py, app/services/foto_service.py, app/api/deps.py (`require_auditor`, `require_equipe`), tests/test_legenda_ia_endpoints.py. Passos: (1) Escreva primeiro os testes novos em tests/test_legenda_ia_aprovacao.py: auxiliar com `aprovar_legenda_ia` → 403 (RFC 7807, padrão existente); auxiliar gera e edita rascunho normalmente; auditor aprova; regerar legenda de foto aprovada → `aprovado_por_id/aprovado_em` nulos e status `rascunho`; `PUT` que muda `legenda` de foto aprovada → mesma invalidação; `PUT` que não altera `legenda` (ex.: só `ordem`) NÃO invalida. (2) Implemente o mínimo em fotos.py/foto_service.py. Não crie migration, não altere models/schemas (não estão em `toca`); se faltar campo, registre no doc como proposta. (3) Ajuste em test_legenda_ia_endpoints.py o teste que hoje faz o auxiliar aprovar (`test_auxiliar_gera_e_aprova` ou equivalente) para o novo contrato, explicando a mudança no doc. (4) NÃO implemente limite de taxa nem saneamento da saída do LLM (DEC-42 C e D, tarefa à parte) e não toque no frontend (tarefa à parte). (5) Rode `pytest tests/test_legenda_ia_endpoints.py tests/test_legenda_ia_aprovacao.py tests/test_fotos.py` e `ruff check .` a partir de 04_backend. O PostgreSQL de 05_infra/docker-compose.yml fica em localhost:5433 (`docker compose ps`; não suba nem derrube serviços); se não estiver no ar, registre que não rodou em vez de inventar resultado. (6) Registre no doc: tabela antes/depois, arquivos e linhas, testes, comandos e saídas, e a consequência para a UI da T26 (o painel precisa esconder «Aprovar» do auxiliar). Commit: `fix(backend): aprovação de legenda IA só por auditor e invalidação ao editar (DEC-42)` com `Refs DEC-42`. Não edite os documentos de gestão em 00_docs/projeto/ nem o BACKLOG.md. Siga a "Regra de pronto" do BACKLOG.md.
```

### T34 · Frontend: ocultar «Aprovar» legenda IA para auxiliar e refletir invalidação ao editar
- **Status:** done
- **Origem:** DEC-42
- **Papel:** frontend
- **Depende:** T33
- **Ambiente:** offline
- **Dificuldade:** baixa
- **Toca:** 03_frontend/components/legenda-ia-painel.tsx, 03_frontend/e2e/legenda-ia-aprovacao.spec.ts, 00_docs/backlog-auto/legenda-ia-frontend-aprovacao.md
- **Doc:** 00_docs/backlog-auto/legenda-ia-frontend-aprovacao.md
- **Pronto:** No painel «Gerar legenda com IA», o perfil `auxiliar` vê gerar/editar mas não vê o botão de aprovar (mostra aviso de que a aprovação é do auditor); ao editar o texto de uma legenda já aprovada o painel avisa que a aprovação será desfeita e volta a «rascunho». `e2e/legenda-ia-aprovacao.spec.ts` (API mockada) passa; `npm run lint` e `npm run build` em 03_frontend limpos.
- **Prompt:**
```text
Tarefa (DEC-42 itens A e B, lado frontend; depende da tarefa C do lote, que impõe a regra no backend). Contexto: a T26 criou 03_frontend/components/legenda-ia-painel.tsx (ver 00_docs/backlog-auto/legenda-ia-frontend.md) com aprovação em duas etapas para `auditor`/`auxiliar`. Pelo DEC-42 proposto, só `auditor` aprova legenda IA; auxiliar gera e edita rascunho; editar ou regerar legenda aprovada zera a aprovação e volta a `rascunho` (ver 00_docs/backlog-auto/legenda-ia-aprovacao.md, escrito pela tarefa anterior; se ainda não existir, leia a seção DEC-42 de 00_docs/projeto/decisoes.md). Leia legenda-ia-painel.tsx, 03_frontend/lib/use-usuario-atual.ts (papel do usuário), os testes e2e da T26 (procure por `legenda` em 03_frontend/e2e/) e o README de 03_frontend. Passos: (1) No painel, esconda a ação de aprovar quando o papel não for `auditor` e mostre texto explicativo acessível («A aprovação é feita pelo auditor responsável»). (2) Se a legenda estiver aprovada e o usuário editar o texto ou pedir nova geração, mostre aviso claro de que a aprovação será desfeita; após salvar, reflita o status `rascunho` com a resposta do backend (não presuma localmente). (3) Crie e2e/legenda-ia-aprovacao.spec.ts com API mockada (mesmo padrão dos specs existentes): auxiliar não vê «Aprovar»; auditor vê e aprova; editar legenda aprovada exibe o aviso e o estado volta a rascunho. Não altere outros componentes, nem types.ts/api-client.ts (fora de `toca`; se faltar tipo, registre como proposta no doc). (4) Rode `npm run lint`, `npm run build` e o novo spec (`npx playwright test e2e/legenda-ia-aprovacao.spec.ts`) a partir de 03_frontend; specs que exigem stack real/docker não devem ser inventados — registre o que não rodou. (5) Registre no doc o comportamento, comandos e saídas. Commit: `feat(frontend): aprovação de legenda IA restrita ao auditor (DEC-42)` com `Refs DEC-42`. Não edite os documentos de gestão em 00_docs/projeto/ nem o BACKLOG.md. Siga a "Regra de pronto" do BACKLOG.md.
```

### T35 · Legenda por IA: limite de taxa em `gerar`, teto e saneamento da saída do LLM
- **Status:** done
- **Origem:** DEC-42
- **Papel:** backend
- **Depende:** T33
- **Ambiente:** docker
- **Dificuldade:** alta
- **Toca:** 04_backend/app/services/legenda_ia/, 04_backend/app/api/deps.py, 04_backend/app/core/config.py, 04_backend/.env.example, 05_infra/.env.example, 04_backend/tests/test_legenda_ia_limites.py, 00_docs/backlog-auto/legenda-ia-limites.md
- **Doc:** 00_docs/backlog-auto/legenda-ia-limites.md
- **Pronto:** Existe limite de taxa configurável por usuário e por foto para a geração de legenda IA (excedido → 429 RFC 7807), a saída do cliente de IA (`legenda_ia_sugerida`, alertas, pendências) passa por saneamento com tamanho máximo, e o `legenda_bruta` entra delimitado no prompt do contrato do adapter. `tests/test_legenda_ia_limites.py` (com `FakeLegendaIAClient`) passa; variáveis novas estão nos `.env.example`; `ruff check .` em 04_backend verde; o doc diz o que não rodou.
- **Prompt:**
```text
Tarefa (DEC-42 itens C e D, proposta da T29; SEG-IA-01, SEG-IA-02, SEG-IA-06 de 00_docs/backlog-auto/seguranca-legenda-ia.md). Contexto: `POST /fotos/{id}/legenda-ia/gerar` (T25) não tem limite de taxa nem de custo, a saída do LLM não tem limite de tamanho, e `legenda_bruta` pode virar injeção de prompt no adapter. O contrato `LegendaIAClient` e o `FakeLegendaIAClient` estão em 04_backend/app/services/legenda_ia/ (T23, ver 00_docs/backlog-auto/legenda-ia-servico.md). Não existe adapter real (B-04, provedor ainda não escolhido): não crie nem escolha provedor. Leia a seção DEC-42 e DEC-24 de 00_docs/projeto/decisoes.md (só elas), seguranca-legenda-ia.md, legenda-ia-endpoints.md, app/services/legenda_ia/, app/api/deps.py (inclusive `get_legenda_ia_client` e o rate limit de login da DEC-24, para reaproveitar o mecanismo se já existir), app/core/config.py e os dois .env.example. Este item precisa de um ponto de integração no endpoint, que está em app/api/v1/fotos.py (arquivo da tarefa anterior C, já concluída); para ficar dentro de `toca`, implemente o limite como dependência FastAPI em deps.py e o saneamento como função/decorador em app/services/legenda_ia/, e registre no doc as 1-2 linhas que o endpoint precisará chamar — se não for possível ligar sem editar fotos.py, ligue-as por uma dependência em deps.py que o endpoint já usa (`get_legenda_ia_client`), envolvendo o cliente retornado em um wrapper que sanea e delimita. Passos: (1) Escreva primeiro tests/test_legenda_ia_limites.py: N+1-ésima geração do mesmo usuário na janela → 429; limite por foto; saída acima do teto é truncada/rejeitada conforme decidir (documente a escolha); caracteres de controle e marcação perigosa saneados; `legenda_bruta` com texto tipo «ignore as instruções anteriores» é entregue ao cliente dentro de delimitadores fixos. Use relógio injetável (sem sleep real). (2) Implemente: janela em memória por processo é aceitável e deve ser descrita como limitação (multi-instância → proposta de Redis/banco no doc); limites e tamanho máximo por variáveis de ambiente com default seguro, registradas em 04_backend/.env.example e 05_infra/.env.example (sem segredos). (3) Não crie migration, não altere models/schemas, não toque no frontend. (4) Rode `pytest tests/test_legenda_ia_limites.py tests/test_legenda_ia_endpoints.py tests/test_prompt_ia_service.py` e `ruff check .` a partir de 04_backend; PostgreSQL em localhost:5433 (`docker compose ps` em 05_infra; não suba nem derrube serviços); se não estiver no ar, registre que os testes de endpoint não rodaram. (5) Registre no doc: parâmetros, escolhas, limitações, o que continua bloqueando produção (B-04, L15/SEG-IA-07) e comandos com saídas. Commit: `feat(backend): limites e saneamento da legenda por IA (DEC-42)` com `Refs DEC-42`. Não edite os documentos de gestão em 00_docs/projeto/ nem o BACKLOG.md. Siga a "Regra de pronto" do BACKLOG.md.
```

### T36 · LTIP e RFIP: só legenda aprovada entra no relatório (helper legenda_para_relatorio)
- **Status:** done
- **Origem:** BL-36
- **Papel:** Engenheiro Backend
- **Depende:** T24
- **Ambiente:** offline
- **Dificuldade:** media
- **Toca:** 04_backend/app/services/report_generator/ltip_pipeline.py, 04_backend/app/services/report_generator/rfip_pipeline.py, 04_backend/tests/test_legenda_relatorio_ltip_rfip.py, 00_docs/backlog-auto/legenda-relatorio-ltip-rfip.md
- **Doc:** 00_docs/backlog-auto/legenda-relatorio-ltip-rfip.md
- **Pronto:** ltip_pipeline.py e rfip_pipeline.py usam legenda_para_relatorio (PDF e DOCX) no lugar da legenda crua; testes novos provam que legenda IA não aprovada não aparece e que legenda manual/aprovada aparece; `pytest` nos testes ltip/rfip/legenda e `ruff check .` verdes; resultado registrado no Doc.
- **Prompt:**
```text
Tarefa: estender aos pipelines do LTIP e do RFIP a regra «só legenda aprovada entra no relatório» (RN-16/RN-17, DP-9 de DEC-37), já aplicada ao RFO. Contexto: 04_backend/app/services/report_generator/legenda_foto.py expõe `legenda_para_relatorio(foto)`, `foto_ia_em_rascunho` e `sinalizar_fotos_ia_em_rascunho`. Só `rfo_pipeline.py` (linha ~32, import) o usa; veja como ele aplica o helper no contexto de PDF e DOCX e replique o padrão. Leia antes 00_docs/backlog-auto/legenda-relatorio.md (resultado do T24) para o contrato e as pendências. Passos: (1) em 04_backend/app/services/report_generator/ltip_pipeline.py e rfip_pipeline.py, passe toda legenda de foto por `legenda_para_relatorio` ao montar o contexto, tanto no caminho de PDF quanto no de DOCX; não altere layout.json nem templates; (2) crie 04_backend/tests/test_legenda_relatorio_ltip_rfip.py cobrindo: foto com legenda IA em rascunho/não aprovada → legenda vazia ou a definida pelo helper; legenda IA aprovada → aparece; legenda manual → aparece; use objetos simples (SimpleNamespace) sem banco; testes que exijam WeasyPrint/GTK devem ser pulados com skipif, não inventados; (3) a rodar a partir de 04_backend: `pytest tests/test_legenda_relatorio_ltip_rfip.py tests/test_ltip_pipeline.py tests/test_rfip_pipeline.py tests/test_legenda_relatorio.py` e `ruff check .`, registrando a saída real (inclusive o que foi pulado). Registre fatos, comandos e saída em 00_docs/backlog-auto/legenda-relatorio-ltip-rfip.md; qualquer decisão nova vai como proposta nesse doc, sem editar 00_docs/projeto/*. Não toque nos pipelines de RFO, Cautelar e Residencial. Siga a «Regra de pronto» do BACKLOG.md e as regras do projeto (Conventional Commits com escopo backend e rodapé `Refs BL-36`, sem push).
```

### T37 · Vistoria Cautelar e Residencial: só legenda aprovada entra no relatório
- **Status:** done
- **Origem:** BL-36
- **Papel:** Engenheiro Backend
- **Depende:** T24, T28
- **Ambiente:** offline
- **Dificuldade:** media
- **Toca:** 04_backend/app/services/report_generator/vistoria_cautelar_pipeline.py, 04_backend/app/services/report_generator/vistoria_residencial_pipeline.py, 04_backend/tests/test_legenda_relatorio_vistorias.py, 00_docs/backlog-auto/legenda-relatorio-vistorias.md
- **Doc:** 00_docs/backlog-auto/legenda-relatorio-vistorias.md
- **Pronto:** Os dois pipelines de vistoria passam toda legenda de foto por legenda_para_relatorio (PDF e DOCX); testes novos passam e `ruff check .` está verde; resultado registrado no Doc.
- **Prompt:**
```text
Tarefa: aplicar aos pipelines da Vistoria Cautelar e da Vistoria Residencial a regra «só legenda aprovada entra no relatório» (RN-16/RN-17, DP-9 de DEC-37). Contexto: 04_backend/app/services/report_generator/legenda_foto.py tem `legenda_para_relatorio(foto)`; o `rfo_pipeline.py` é a referência de uso. Leia 00_docs/backlog-auto/legenda-relatorio.md (T24) e 00_docs/backlog-auto/pipelines-url-fetcher.md (T28, que mexeu nesses mesmos pipelines para o fetcher de fotos, então preserve esse comportamento). Passos: (1) em vistoria_cautelar_pipeline.py e vistoria_residencial_pipeline.py, passe cada legenda de foto por `legenda_para_relatorio` no contexto de PDF e de DOCX, sem alterar templates nem layout.json; (2) crie 04_backend/tests/test_legenda_relatorio_vistorias.py com casos para os dois pipelines: IA em rascunho não aparece, IA aprovada aparece, manual aparece; sem banco, e com `skipif` explícito onde faltar WeasyPrint/GTK (não invente resultado); (3) a partir de 04_backend rode `pytest tests/test_legenda_relatorio_vistorias.py tests/test_vistoria_cautelar_pipeline.py tests/test_vistoria_residencial_pipeline.py tests/test_pipelines_url_fetcher.py` e `ruff check .`; registre saída real e itens pulados. Registre tudo em 00_docs/backlog-auto/legenda-relatorio-vistorias.md (decisões novas só como proposta; não edite 00_docs/projeto/*). Não toque em ltip, rfip nem rfo. Siga a «Regra de pronto» do BACKLOG.md; commit `feat(backend): ... (BL-36)` com `Refs BL-36`, sem push.
```

### T38 · Frontend: editor de anotação de fotos integrado ao fluxo de aprovação de legenda IA
- **Status:** done
- **Origem:** BL-39
- **Papel:** Engenheiro Frontend
- **Depende:** T26, T34
- **Ambiente:** offline
- **Dificuldade:** media
- **Toca:** 03_frontend/components/photo-annotation-editor.tsx, 03_frontend/e2e/anotacao-legenda-ia.spec.ts, 00_docs/backlog-auto/anotacao-legenda-ia-frontend.md
- **Doc:** 00_docs/backlog-auto/anotacao-legenda-ia-frontend.md
- **Pronto:** photo-annotation-editor.tsx integra com o fluxo de legenda IA conforme o prompt 39 (sem alterar legenda-ia-painel.tsx); spec Playwright novo existe; `npm run lint` e `npm run build` em 03_frontend verdes; resultado e o que não pôde rodar registrados no Doc.
- **Prompt:**
```text
Tarefa (BL-39, RF-15, RN-16, RN-17): integrar o editor de anotação de fotos ao fluxo de aprovação de legendas assistidas por IA, no frontend. Leia primeiro .github/prompts/39-integracao-anotacao-legendas-ia.prompt.md (escopo original), 03_frontend/components/photo-annotation-editor.tsx, 03_frontend/components/legenda-ia-painel.tsx (somente leitura: o T26/T34 já tratam aprovação, ocultar «Aprovar» para auxiliar e invalidação ao editar) e 00_docs/backlog-auto/legenda-ia-frontend-aprovacao.md. Regras a respeitar: a legenda IA só entra no relatório depois de aprovada por auditor; ao salvar uma anotação que altera a imagem/legenda de uma foto com legenda IA, o estado de aprovação deve refletir a invalidação já implementada no backend (T33), mostrando ao usuário que a legenda voltou a pendente; o editor não pode aprovar legenda nem expor ação de aprovar a auxiliar (use o hook de usuário atual, 03_frontend/lib/use-usuario-atual.ts). Reaproveite 03_frontend/lib/api-client.ts e 03_frontend/lib/types.ts apenas por leitura; se faltar um tipo ou chamada, registre a lacuna no Doc em vez de editar esses arquivos (eles pertencem a outras tarefas). Crie o spec 03_frontend/e2e/anotacao-legenda-ia.spec.ts seguindo o padrão de 03_frontend/e2e/legenda-ia-aprovacao.spec.ts e helpers.ts. A partir de 03_frontend rode `npm run lint` e `npm run build`; rode o Playwright só se o ambiente permitir e, se não rodar, diga isso explicitamente. Registre fatos, comandos e saída em 00_docs/backlog-auto/anotacao-legenda-ia-frontend.md; decisões novas como proposta no Doc, sem editar 00_docs/projeto/*. Siga a «Regra de pronto» do BACKLOG.md; commit `feat(frontend): ... (BL-39)` com `Refs BL-39`, sem push.
```

### T40 · Repassar as variáveis LEGENDA_IA_* ao compose e ao render.yaml
- **Status:** done
- **Origem:** BL-24
- **Papel:** devops
- **Depende:** —
- **Ambiente:** offline
- **Dificuldade:** baixa
- **Toca:** 05_infra/docker-compose.yml, 05_infra/docker-compose.prod.yml, render.yaml, 00_docs/backlog-auto/legenda-ia-env-deploy.md
- **Doc:** 00_docs/backlog-auto/legenda-ia-env-deploy.md
- **Pronto:** As variáveis `LEGENDA_IA_*` presentes em `05_infra/.env.example` e `04_backend/.env.example` chegam ao serviço do backend em `05_infra/docker-compose.yml`, `05_infra/docker-compose.prod.yml` e `render.yaml`, com valores padrão iguais aos do `.env.example`. Nenhum valor secreto foi escrito. `docker compose -f <arquivo> config` valida os dois compose (ou o doc registra que o Docker não estava disponível) e `render.yaml` carrega como YAML válido. O doc traz uma tabela variável × arquivo × padrão.
- **Prompt:**
```text
Tarefa (BL-24 / pendência da T35, DEC-42). Contexto: a T35 criou variáveis de limite do fluxo de legenda por IA, lidas pelo backend em `04_backend/app/core/config.py` (procure `LEGENDA_IA_`) e documentadas em `04_backend/.env.example` e `05_infra/.env.example` (LEGENDA_IA_LIMITE_POR_USUARIO, LEGENDA_IA_JANELA_USUARIO_SEGUNDOS, LEGENDA_IA_LIMITE_DIARIO_POR_USUARIO, LEGENDA_IA_LIMITE_POR_FOTO, LEGENDA_IA_JANELA_FOTO_SEGUNDOS, LEGENDA_IA_SAIDA_MAX_CARACTERES, LEGENDA_IA_SAIDA_MAX_ITENS, LEGENDA_IA_SAIDA_MAX_CARACTERES_ITEM). A pendência registrada é que elas não são repassadas ao container do backend em `05_infra/docker-compose.yml`, `05_infra/docker-compose.prod.yml` nem em `render.yaml` (arquivo que já existe na raiz; não crie outros arquivos na raiz).

Passos: (1) Leia `04_backend/app/core/config.py` e confirme a lista COMPLETA e os tipos/padrões das variáveis `LEGENDA_IA_*` (a lista acima pode estar incompleta ou desatualizada; vale o código). Leia os dois `.env.example` e `00_docs/backlog-auto/` docs da T35 (procure por `limite` e `legenda` com Grep). (2) Em cada um dos três arquivos, localize o serviço do backend e o bloco `environment`; siga o estilo já usado para as demais variáveis (por ex. `${VAR:-padrao}` nos compose; `value:` ou `sync: false` no render.yaml conforme o padrão de variáveis não secretas). Use como padrão o mesmo valor do `.env.example`. Não coloque segredos. (3) Se alguma variável nova estiver no código mas faltar em algum `.env.example`, acrescente-a (`.env.example` só em `04_backend` e `05_infra`; se faltar, tocar neles é permitido nesta tarefa e deve ser listado no doc). (4) Valide: `docker compose -f docker-compose.yml config` e `docker compose -f docker-compose.prod.yml config` a partir de `05_infra` (o prod pode exigir variáveis obrigatórias: passe valores fictícios via ambiente só para a validação, sem gravar arquivo `.env`); se o Docker não existir, registre isso. Valide `render.yaml` com `python -c "import yaml; yaml.safe_load(open('render.yaml'))"` a partir da raiz. (5) Registre em `00_docs/backlog-auto/legenda-ia-env-deploy.md` uma tabela variável × arquivo × padrão, os comandos e as saídas. Não toque em código Python nem nos testes. Não edite `00_docs/projeto/*`. Commit: `chore(infra): repassa LEGENDA_IA_* ao compose e ao render.yaml (BL-24)` com `Refs BL-24`. Não faça push. Siga a «Regra de pronto» do BACKLOG.md.
```

### T45 · Montar o contexto do RFO a partir do banco (inspeção → contexto do rfo_pipeline)
- **Status:** done
- **Origem:** BL-13
- **Papel:** Engenheiro Backend
- **Depende:** T43
- **Ambiente:** docker
- **Dificuldade:** media
- **Toca:** 04_backend/app/services/report_generator/rfo_contexto.py, 04_backend/tests/test_rfo_contexto.py, 00_docs/backlog-auto/rfo-contexto-banco.md
- **Doc:** 00_docs/backlog-auto/rfo-contexto-banco.md
- **Pronto:** Existe `montar_contexto_rfo(db, inspecao_id)` em `rfo_contexto.py` que devolve o dicionário aceito por `rfo_pipeline.normalizar_contexto` a partir de Inspeção, Edificação, Contrato, Visitas (equipe, serviços, medições), Ocorrências e Fotos; levanta erro de domínio (404/409) para inspeção inexistente ou não-RFO; `pytest tests/test_rfo_contexto.py` passa contra o PostgreSQL (localhost:5433) e um teste de integração leve passa o contexto por `renderizar_html` sem exceção; `ruff check .` limpo; se o PostgreSQL não estiver no ar, o Doc registra que não rodou.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md (raiz do repositório). Papel: Engenheiro Backend (.github/agents/backend.agent.md). Contexto: o BL-13 gerou os templates PDF/DOCX do RFO e 04_backend/app/services/report_generator/rfo_pipeline.py renderiza um contexto (funções `normalizar_contexto`, `renderizar_html`, `gerar_pdf`, `gerar_docx`), mas NÃO existe código que monte esse contexto a partir do banco: hoje só os testes montam dicionários à mão. Esta tarefa cria apenas a camada de montagem, sem endpoint (o endpoint é a tarefa seguinte). Passos: (1) leia rfo_pipeline.py (formato esperado do contexto, campos obrigatórios, tratamento de fotos e `legenda_para_relatorio` de legenda_foto.py, regra DEC-37 DP-9: só legenda aprovada entra) e os modelos em 04_backend/app/models/ (Inspecao, Edificacao, Contrato, Visita, MaoDeObra/medições, Ocorrencia, Foto, Responsavel) mais as regras RF-03, RF-04, RF-05, RF-06 e RN-01/RN-02 de 00_docs/estudo-do-contexto.md (leia só essas seções). (2) Crie 04_backend/app/services/report_generator/rfo_contexto.py com `montar_contexto_rfo(db, inspecao_id)` (Session/AsyncSession conforme o padrão dos serviços existentes; confira em app/services/ de visitas ou ocorrências), carregando relações com eager loading para evitar N+1, ordenando visitas por `seq_numero`, ocorrências por `seq_numero` e fotos por `ordem`. Fotos entram só com referência/`storage_key`; a entrega do binário continua com o url_fetcher/foto_fetcher existente (não baixe imagens aqui). Inspeção inexistente → 404 com o DomainError do projeto; `tipo != 'RFO'` → 409. (3) Escreva 04_backend/tests/test_rfo_contexto.py usando as fixtures de banco existentes (veja conftest.py): cenário completo (2 visitas, equipe, medições, 3 ocorrências, fotos com legenda aprovada e pendente), inspeção sem visitas, inspeção inexistente, inspeção não-RFO, e um teste que passa o resultado por `normalizar_contexto` + `renderizar_html` sem exceção. (4) Requer o PostgreSQL de 05_infra/docker-compose.yml (localhost:5433); se não estiver no ar, escreva os testes, registre que não rodaram e não invente resultado. Rode `pytest` e `ruff check .` em 04_backend. Registre no Doc 00_docs/backlog-auto/rfo-contexto-banco.md o mapeamento campo a campo (banco → contexto), lacunas encontradas (campos do template sem origem no banco) e propostas de decisão. Não edite documentos de gestão compartilhados. Commit: `feat(backend): monta contexto do RFO a partir do banco (BL-13)` com rodapé `Refs BL-13`. Nunca faça push.
```

### T46 · Endpoint de emissão do RFO (PDF/DOCX) que grava no storage e registra o Relatorio
- **Status:** done
- **Origem:** BL-13
- **Papel:** Engenheiro Backend
- **Depende:** T45
- **Ambiente:** docker
- **Dificuldade:** alta
- **Toca:** 04_backend/app/api/v1/relatorios.py, 04_backend/app/api/v1/__init__.py, 04_backend/app/schemas/relatorio.py, 04_backend/tests/test_relatorios_rfo_api.py, 00_docs/backlog-auto/rfo-endpoint-emissao.md
- **Doc:** 00_docs/backlog-auto/rfo-endpoint-emissao.md
- **Pronto:** `POST /api/v1/inspecoes/{id}/relatorios/rfo` (apenas `auditor`; auxiliar e cliente recebem 403, anônimo 401) monta o contexto via `montar_contexto_rfo`, gera PDF e DOCX com `rfo_pipeline`, grava no storage com chave determinística, cria/atualiza o `Relatorio` com `pdf_key`/`docx_key` e devolve 201 com os metadados (nunca a chave crua do storage na resposta pública); inspeção inexistente 404, não-RFO 409; o relatório gerado aparece em `GET /portal/relatorios` para o cliente do contrato; `pytest tests/test_relatorios_rfo_api.py` passa (storage e renderizador injetáveis/fakes, sem exigir WeasyPrint nativo); `pytest` completo e `ruff check .` em 04_backend sem regressão; se o PostgreSQL não estiver no ar, o Doc registra que não rodou.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md (raiz do repositório). Papel: Engenheiro Backend (.github/agents/backend.agent.md). Contexto: a tarefa C criou `montar_contexto_rfo(db, inspecao_id)` em 04_backend/app/services/report_generator/rfo_contexto.py (leia-o e 00_docs/backlog-auto/rfo-contexto-banco.md). O `rfo_pipeline.py` já gera PDF e DOCX. O Portal do Cliente (04_backend/app/api/v1/portal.py, BL-33) lista e baixa qualquer `Relatorio` com `pdf_key`/`docx_key`, mas nenhum endpoint EMITE o relatório. Crie o endpoint de emissão. Passos: (1) Leia o modelo `Relatorio` em 04_backend/app/models/, o storage_service (04_backend/app/services/storage_service.py: upload, chave, URL pré-assinada), deps.py (`require_auditor`, RN-18/DEC-27: só o auditor emite relatório) e o padrão de routers/schemas/erros de inspecoes.py e fotos.py. (2) Crie 04_backend/app/schemas/relatorio.py (resposta com id, inspecao_id, tipo, versao, tem_pdf, tem_docx, criado_em; `extra=forbid` nos payloads) e 04_backend/app/api/v1/relatorios.py com `POST /inspecoes/{inspecao_id}/relatorios/rfo`; registre o router em app/api/v1/__init__.py. Fluxo: valida inspeção (404/409 via contexto) → monta contexto → gera PDF e DOCX (renderizador e storage injetáveis por dependência, para testes usarem fakes; WeasyPrint indisponível no Windows deve virar 503 claro, não 500) → grava no storage em chave determinística do servidor (ex.: `relatorios/{inspecao_id}/rfo-v{versao}.pdf|docx`) → persiste/atualiza o `Relatorio` com nova versão a cada emissão. Se faltar coluna no modelo `Relatorio` (ex.: versão), crie migration Alembic nova com `downgrade()` a partir de 04_backend/ (`alembic revision`), sem editar migrations antigas. (3) Escreva 04_backend/tests/test_relatorios_rfo_api.py: auditor 201 (storage e renderizador fake gravam as chaves), segunda emissão incrementa a versão, auxiliar 403, cliente 403, sem token 401, inspeção 404, não-RFO 409, e o cliente do contrato vê o relatório em GET /portal/relatorios. (4) Requer o PostgreSQL de 05_infra/docker-compose.yml (localhost:5433); se não estiver no ar, registre que não rodou. Rode `pytest` e `ruff check .` em 04_backend. (5) Registre no Doc 00_docs/backlog-auto/rfo-endpoint-emissao.md o contrato do endpoint, a convenção de chaves, o que ficou pendente (frontend do botão «Emitir relatório», emissão de LTIP/RFIP/vistorias, geração assíncrona para relatórios de 200 páginas, RNF-06) e propostas de decisão. Não edite documentos de gestão compartilhados. Commit: `feat(backend): endpoint de emissao do RFO (PDF/DOCX) (BL-13)` com rodapé `Refs BL-13`. Nunca faça push.
```

### T47 · Verificar e repassar MAX_RELATORIO_SIZE_BYTES (e demais env da emissão) aos .env.example, compose e render.yaml
- **Status:** done
- **Origem:** DEC-48
- **Papel:** Engenheiro DevOps
- **Depende:** —
- **Ambiente:** offline
- **Dificuldade:** baixa
- **Toca:** 05_infra/.env.example, 04_backend/.env.example, 05_infra/docker-compose.yml, 05_infra/docker-compose.prod.yml, render.yaml, 00_docs/backlog-auto/relatorio-env-deploy.md
- **Doc:** 00_docs/backlog-auto/relatorio-env-deploy.md
- **Pronto:** Toda variável de ambiente lida pelo código de emissão de relatórios (no mínimo MAX_RELATORIO_SIZE_BYTES, DEC-48 P5) consta nos dois .env.example e é repassada ao serviço backend em docker-compose.yml, docker-compose.prod.yml e render.yaml; `docker compose -f docker-compose.yml config` e `-f docker-compose.prod.yml config` (a partir de 05_infra/) validam sem erro, ou o Doc registra que não rodou; nenhum segredo commitado; o Doc lista o antes/depois de cada arquivo.
- **Prompt:**
```text
Siga o agente .github/agents do DevOps e a 'Regra de pronto' do BACKLOG.md (raiz do repositório). Contexto: a T46 (BL-13) criou o endpoint de emissão do RFO, com teto de tamanho por arquivo `MAX_RELATORIO_SIZE_BYTES` (200 MB, DEC-48 P5, ver 00_docs/projeto/decisoes.md, seção DEC-48, e 00_docs/backlog-auto/rfo-endpoint-emissao.md). Faça: (1) em 04_backend/app/services/relatorio_service.py, 04_backend/app/core/config.py e arredores, descubra todas as variáveis de ambiente introduzidas pela emissão de relatórios (grep por `MAX_RELATORIO` e por campos novos em Settings); (2) verifique se cada uma está em 05_infra/.env.example e 04_backend/.env.example (se existir) com comentário e valor padrão seguro; adicione as que faltam; (3) verifique se são repassadas ao serviço backend em 05_infra/docker-compose.yml, 05_infra/docker-compose.prod.yml e render.yaml (raiz), seguindo o padrão já usado para as variáveis `LEGENDA_IA_*` (T40); adicione as que faltam, sem inventar valores secretos; (4) rode `docker compose -f docker-compose.yml config` e `-f docker-compose.prod.yml config` a partir de 05_infra/ (com um .env temporário apenas se necessário, nunca commitado); se o Docker não estiver disponível, registre que não rodou. Não crie pastas na raiz. Registre no Doc 00_docs/backlog-auto/relatorio-env-deploy.md: variáveis encontradas, o que já existia, o que foi adicionado, comandos e saída. Não edite os documentos de gestão em 00_docs/projeto/ nem o BACKLOG.md. Nunca faça push nem toque em main_back, main_front, staging_back, staging_front. Commit: `chore(infra): repassa variaveis da emissao de relatorios ao deploy (DEC-48)` com rodapé `Refs DEC-48`.
```

### T48 · RFO: trocar legenda_aprovada por legenda_para_relatorio no contexto do banco
- **Status:** done
- **Origem:** DEC-47
- **Papel:** Engenheiro Backend
- **Depende:** —
- **Ambiente:** docker
- **Dificuldade:** baixa
- **Toca:** 04_backend/app/services/report_generator/rfo_contexto.py, 04_backend/tests/test_rfo_contexto.py, 00_docs/backlog-auto/rfo-contexto-legenda.md
- **Doc:** 00_docs/backlog-auto/rfo-contexto-legenda.md
- **Pronto:** `legenda_aprovada` não existe mais em rfo_contexto.py; as fotos do contexto usam `legenda_para_relatorio` (nunca imprimem `legenda_ia_sugerida`); teste novo com foto de legenda IA pendente/rejeitada cobre o caso e usa objeto real do banco; `pytest tests/test_rfo_contexto.py` passa com PostgreSQL em localhost:5433 (ou o Doc registra que não rodou e por quê); `ruff check .` limpo em 04_backend.
- **Prompt:**
```text
Siga o agente backend de .github/agents/ e a 'Regra de pronto' do BACKLOG.md. Contexto: DEC-47 item 1 (00_docs/projeto/decisoes.md; leia também 00_docs/backlog-auto/rfo-contexto-banco.md, seção 'Correção do fechamento de lote'). Em 04_backend/app/services/report_generator/rfo_contexto.py a função `legenda_aprovada(foto)` é permissiva (código morto, escrita num worktree defasado) e diverge dos demais pipelines. Existe `04_backend/app/services/report_generator/legenda_foto.py` com `legenda_para_relatorio` (imprime sempre `legenda`, nunca `legenda_ia_sugerida`; estado da IA em `status_validacao_ia`, DEC-37; `Foto` NÃO tem `legenda_status`; não crie migration nem essa coluna). Veja como rfo_pipeline.py, ltip_pipeline.py e as vistorias usam o helper (T24/T36/T37) e replique o mesmo padrão em `montar_contexto_rfo`. Remova `legenda_aprovada` e seus usos. Atualize 04_backend/tests/test_rfo_contexto.py: remova o teste com objeto simulado de 'pendente' e acrescente testes com Fotos reais persistidas (legenda manual, legenda IA ainda não aprovada, legenda IA aprovada) conferindo o que sai no contexto. Rode a partir de 04_backend/: `python -m pytest tests/test_rfo_contexto.py tests/test_legenda_relatorio.py` (ajuste ao nome real dos testes do helper) e `ruff check .`. O PostgreSQL de 05_infra/docker-compose.yml (localhost:5433) precisa estar no ar; se não estiver, registre que não rodou — não invente resultado. No Windows o WeasyPrint pode faltar (Pango); se importar `app.services.report_generator` falhar por isso, registre e rode no container. Registre no Doc 00_docs/backlog-auto/rfo-contexto-legenda.md: o que mudou, comandos e saída. Não edite documentos de gestão em 00_docs/projeto/ nem o BACKLOG.md. Commit: `fix(backend): contexto do RFO usa legenda_para_relatorio (DEC-47)` com `Refs DEC-47`. Nunca faça push.
```

### T49 · Migration UNIQUE (inspecao_id, tipo, versao) em relatorios com checagem prévia de duplicatas
- **Status:** done
- **Origem:** DEC-48
- **Papel:** Engenheiro Backend
- **Depende:** —
- **Ambiente:** docker
- **Dificuldade:** media
- **Toca:** 04_backend/app/models/relatorio.py, 04_backend/alembic/versions/, 04_backend/tests/test_relatorio_unicidade.py, 00_docs/backlog-auto/relatorio-unicidade.md
- **Doc:** 00_docs/backlog-auto/relatorio-unicidade.md
- **Pronto:** Nova migration com `upgrade()` e `downgrade()` cria/remove a constraint única (inspecao_id, tipo, versao) em `relatorios`; a migration falha com mensagem clara se já houver duplicatas (não apaga dados); `alembic upgrade head`, `alembic downgrade -1` e `alembic upgrade head` rodam sem erro; teste prova que inserir duas linhas iguais levanta IntegrityError e que duas emissões concorrentes do RFO resultam em V01/V02 sem violar a constraint; `pytest` e `ruff check .` passam em 04_backend (ou o Doc registra que não rodou).
- **Prompt:**
```text
Siga o agente backend de .github/agents/ e a 'Regra de pronto' do BACKLOG.md. Contexto: DEC-48 P3 (00_docs/projeto/decisoes.md; leia 00_docs/backlog-auto/rfo-endpoint-emissao.md). A emissão do RFO (04_backend/app/services/relatorio_service.py, `emitir_rfo`) cria um `Relatorio` novo por emissão (V01, V02…), e hoje a unicidade de (inspecao_id, tipo, versao) depende só do lock `FOR NO KEY UPDATE`, sem constraint no banco. Faça, a partir de 04_backend/: (1) localize o modelo `Relatorio` (app/models/) e o nome da coluna de versão; (2) crie migration Alembic nova (`alembic revision`, down_revision = head atual; confira com `alembic heads`) que, no upgrade, primeiro consulta duplicatas de (inspecao_id, tipo, versao) e, se houver, levanta erro listando-as e orientando a limpeza manual (NUNCA apague nem renumere dados), e então cria `UniqueConstraint` com nome explícito; `downgrade()` remove a constraint; (3) declare a mesma constraint em `__table_args__` do modelo; (4) escreva tests/test_relatorio_unicidade.py: duplicata → IntegrityError; versões diferentes e tipos diferentes coexistem; emissão sequencial dupla do RFO (use o cliente de storage/gerador fake que os testes de emissão já usam) gera V01 e V02. Rode `alembic upgrade head && alembic downgrade -1 && alembic upgrade head`, `python -m pytest` e `ruff check .`. O PostgreSQL de 05_infra/docker-compose.yml (localhost:5433) precisa estar no ar; se não estiver, registre que não rodou em vez de inventar resultado. Registre em 00_docs/backlog-auto/relatorio-unicidade.md: decisões, comandos, saída e riscos (dados existentes em produção). Não edite documentos de gestão em 00_docs/projeto/ nem o BACKLOG.md. Commit: `feat(backend): constraint unica de versao em relatorios (DEC-48)` com `Refs DEC-48`. Nunca faça push.
```

### T50 · RFO: validar campos obrigatórios do template antes de gerar e responder 422
- **Status:** done
- **Origem:** DEC-47
- **Papel:** Engenheiro Backend
- **Depende:** T48
- **Ambiente:** docker
- **Dificuldade:** media
- **Toca:** 04_backend/app/services/report_generator/rfo_contexto.py, 04_backend/app/services/relatorio_service.py, 04_backend/tests/test_rfo_validacao_contexto.py, 00_docs/backlog-auto/rfo-validacao-completude.md
- **Doc:** 00_docs/backlog-auto/rfo-validacao-completude.md
- **Pronto:** Existe função de validação que lista os campos obrigatórios ausentes (fiscal.nome/crea, contrato.art_fiscalizacao/objeto/data_inicio/prazo_dias e os demais que o template RFO imprime); `POST` de emissão do RFO com contrato incompleto responde 422 com a lista de campos faltantes e NÃO cria `Relatorio` nem sobe arquivo ao storage; contrato completo continua emitindo (201); testes novos passam; `pytest` e `ruff check .` limpos em 04_backend (ou o Doc registra que não rodou).
- **Prompt:**
```text
Siga o agente backend de .github/agents/ e a 'Regra de pronto' do BACKLOG.md. Contexto: DEC-47 item 2 (00_docs/projeto/decisoes.md; leia 00_docs/backlog-auto/rfo-contexto-banco.md, lacuna 4, e rfo-endpoint-emissao.md). Hoje o RFO é gerado mesmo com `fiscal.crea`, `contrato.art_fiscalizacao`, `objeto`, `data_inicio`, `prazo_dias` nulos, e o template imprime vazio/`None`. Esta tarefa vem depois da tarefa B (mesmo arquivo rfo_contexto.py): confirme com `git log` que a troca por `legenda_para_relatorio` já está na main antes de começar; se não estiver, pare e registre no Doc. Faça: (1) leia o template do RFO (04_backend/templates/rfo/, HTML Jinja2) e levante os campos que ele imprime sem fallback; defina a lista de obrigatórios (só os realmente exigidos pelo template; documente o critério); (2) em rfo_contexto.py crie `validar_contexto_rfo(contexto) -> list[str]` (caminhos como `contrato.objeto`); (3) em `emitir_rfo` (relatorio_service.py) chame a validação logo após montar o contexto e ANTES de baixar fotos, renderizar, subir ao storage ou criar o `Relatorio`; se faltar algo, levante o erro de validação do projeto que resulta em HTTP 422 (veja app/core/exceptions e como os outros erros 4xx são mapeados; ex.: código `rfo-contexto-incompleto`, com `campos_faltantes` no detalhe); (4) testes em tests/test_rfo_validacao_contexto.py: contrato completo → ok; cada campo ausente → listado; endpoint → 422 sem Relatorio criado nem upload (use o storage fake dos testes existentes de emissão). Não altere o template nem a regra de ocorrências no RFO (DEC-47 item 3 é decisão do dono). Rode a partir de 04_backend/ `python -m pytest` e `ruff check .`; PostgreSQL em localhost:5433 (05_infra/docker-compose.yml) precisa estar no ar, senão registre que não rodou. Registre no Doc 00_docs/backlog-auto/rfo-validacao-completude.md: lista de campos e critério, comandos e saída. Não edite documentos de gestão em 00_docs/projeto/ nem o BACKLOG.md. Commit: `feat(backend): valida completude do contexto do RFO antes de emitir (DEC-47)` com `Refs DEC-47`. Nunca faça push.
```

### T51 · Portal do Cliente: testes de lacuna para versões múltiplas de relatório (V01, V02…)
- **Status:** done
- **Origem:** DEC-48
- **Papel:** Engenheiro Backend
- **Depende:** —
- **Ambiente:** docker
- **Dificuldade:** media
- **Toca:** 04_backend/tests/test_portal_versoes_relatorio.py, 00_docs/backlog-auto/portal-versoes-relatorio.md
- **Doc:** 00_docs/backlog-auto/portal-versoes-relatorio.md
- **Pronto:** Testes novos fixam o comportamento atual de `GET /portal/relatorios` e do download quando a mesma inspeção tem V01 e V02 do mesmo tipo (quantas versões aparecem, ordem, escopo por contratante, URL pré-assinada sem expor chave); passam com PostgreSQL em localhost:5433; o Doc responde com fatos se o Portal mostra todas as versões ou só a mais recente e propõe (sem aplicar) a decisão para DEC-48 P1; `ruff check .` limpo; nenhum código de produção alterado.
- **Prompt:**
```text
Siga o agente backend de .github/agents/ e a 'Regra de pronto' do BACKLOG.md. Contexto: DEC-48 P1 (00_docs/projeto/decisoes.md) deixou em aberto se o Portal do Cliente deve mostrar só a emissão mais recente de cada relatório, já que cada emissão cria um `Relatorio` novo (V01, V02…). Portal: 04_backend/app/api/v1/portal.py e app/services/portal_service.py (`GET /portal/relatorios`, `GET /portal/relatorios/{id}/download/{formato}`, URL pré-assinada de 15 min); veja os testes existentes do portal em 04_backend/tests/ para reaproveitar fixtures (usuário cliente, contrato com contratante, Relatorio com pdf_key/docx_key). Esta é tarefa de TESTE e DIAGNÓSTICO: NÃO altere código de produção. Escreva 04_backend/tests/test_portal_versoes_relatorio.py cobrindo: (a) uma inspeção com RFO V01 e V02 → o que a listagem retorna (contagem, ordem, campo de versão exposto); (b) cliente de outro contratante não vê nem baixa nenhuma versão (404); (c) download devolve URL pré-assinada e nunca a chave do storage; (d) relatório sem pdf_key/docx_key não gera download. Onde o comportamento atual contrariar o esperado, marque o teste com `pytest.mark.xfail(strict=True, reason=...)` e descreva no Doc. Rode a partir de 04_backend/: `python -m pytest tests/test_portal_versoes_relatorio.py` e `ruff check .`. O PostgreSQL de 05_infra/docker-compose.yml (localhost:5433) precisa estar no ar; se não estiver, registre que não rodou em vez de inventar resultado. Registre em 00_docs/backlog-auto/portal-versoes-relatorio.md: fatos observados, tabela de casos, comandos/saída e uma proposta de decisão para DEC-48 P1 (marcada como proposta). Não edite documentos de gestão em 00_docs/projeto/ nem o BACKLOG.md. Commit: `test(backend): testes de versoes de relatorio no portal (DEC-48)` com `Refs DEC-48`. Nunca faça push.
```

### T54 · Portal do Cliente: tratar o perfil na interface (redirecionar quem não é cliente)
- **Status:** done
- **Origem:** T41
- **Papel:** Engenheiro Frontend
- **Depende:** —
- **Ambiente:** offline
- **Dificuldade:** baixa
- **Toca:** 03_frontend/app/portal, 03_frontend/e2e/portal-perfil.spec.ts, 00_docs/backlog-auto/portal-perfil-ui.md
- **Doc:** 00_docs/backlog-auto/portal-perfil-ui.md
- **Pronto:** Em 03_frontend/app/portal/, usuário autenticado com role diferente de `cliente` é redirecionado para a área interna (sem listar relatórios) e `cliente` vê o portal; 4 ou mais testes Playwright novos com API mockada (`page.route`) em e2e/portal-perfil.spec.ts passam; `npm run lint` e `npm run build` limpos em 03_frontend.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md (raiz do repositório). Papel: Engenheiro Frontend (.github/agents/frontend.agent.md). Contexto: a T41 (00_docs/backlog-auto/portal-e2e.md, spec 03_frontend/e2e/portal.spec.ts) apontou uma lacuna de UX: o portal em 03_frontend/app/portal/ não controla o perfil na UI (sem link para `cliente`, sem redirecionamento por `role`). O perfil do usuário vem do endpoint de sessão/usuário já usado pelo restante do frontend; leia como o `role` é obtido nas telas existentes (ex.: 03_frontend/app/inspecoes) e reutilize. Implemente: (1) quem não é `cliente` ao abrir /portal vai para a home interna sem ver dados do portal; (2) `cliente` vê o portal normalmente; (3) sem sessão vai para o login, como nas demais rotas. Não altere o backend nem o portal.spec.ts existente (só leia; se um teste dele quebrar com a mudança, ajuste a causa no código e registre no Doc). Crie e2e/portal-perfil.spec.ts com a API mockada. Rode, a partir de 03_frontend, `npm run lint`, `npm run build` e o Playwright dos dois specs do portal; se o Playwright não puder rodar, registre. Registre fatos e saídas em 00_docs/backlog-auto/portal-perfil-ui.md. Não edite 00_docs/projeto/* nem BACKLOG.md. Commit: `feat(frontend): portal só para o perfil cliente (BL-32)` com `Refs BL-32`. Não faça push.
```

### T55 · UNIQUE(storage_key) em fotos com checagem prévia de duplicatas
- **Status:** done
- **Origem:** R-15
- **Papel:** Engenheiro Backend
- **Depende:** —
- **Ambiente:** docker
- **Dificuldade:** media
- **Toca:** 04_backend/app/models/foto.py, 04_backend/alembic/versions, 04_backend/tests/test_fotos_storage_key_unico.py, 00_docs/backlog-auto/fotos-storage-key-unico.md
- **Doc:** 00_docs/backlog-auto/fotos-storage-key-unico.md
- **Pronto:** Nova migration Alembic (parte do único head, com downgrade() validado em banco descartável) cria a unicidade de `storage_key` em `fotos`, abortando com mensagem clara se houver duplicatas; `alembic check` sem divergência; testes novos passam (ou o doc registra que o PostgreSQL não rodou); `pytest` e `ruff check .` limpos em 04_backend.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md (raiz do repositório). Papel: Engenheiro Backend (.github/agents/backend.agent.md). Contexto: o risco R-15 (00_docs/projeto/riscos.md) lista `UNIQUE(storage_key)` como aberto. A T19 (00_docs/backlog-auto/fotos-correcoes.md) já devolve 409 para chave já vinculada, mas só a aplicação garante isso. Modelo: 04_backend/app/models/foto.py. Passos: (1) rode `alembic heads` em 04_backend e crie uma migration nova com `down_revision` no head atual (confira que continua um único head); nunca altere migrations antigas. (2) No `upgrade()`, antes de criar a restrição, consulte `storage_key` duplicadas (ignorando nulos); se houver, `raise` com a lista das chaves e NÃO apague nem altere dados; depois crie a unicidade (índice único parcial onde `storage_key IS NOT NULL`, se a coluna aceitar nulo) e declare o mesmo no modelo. (3) `downgrade()` obrigatório e validado: upgrade → downgrade → upgrade em banco descartável (não use o banco de dados reais de dev; crie um banco temporário no PostgreSQL de 05_infra, localhost:5433). (4) Crie tests/test_fotos_storage_key_unico.py: segundo vínculo da mesma chave falha com 409 no endpoint e com IntegrityError direto no banco. Rode `alembic check`, `pytest tests/test_fotos_storage_key_unico.py tests/test_fotos*.py` e `ruff check .` a partir de 04_backend; se o PostgreSQL não estiver no ar, registre que não rodou. Registre fatos e saídas em 00_docs/backlog-auto/fotos-storage-key-unico.md. Não edite 00_docs/projeto/* nem BACKLOG.md. Commit: `feat(backend): unicidade de storage_key em fotos (R-15)` com `Refs R-15`. Não faça push.
```

### T56 · Fotos no DOCX do LTIP
- **Status:** done
- **Origem:** T20
- **Papel:** Engenheiro Backend
- **Depende:** —
- **Ambiente:** offline
- **Dificuldade:** media
- **Toca:** 04_backend/app/services/report_generator/ltip_pipeline.py, 04_backend/tests/test_ltip_docx_fotos.py, 00_docs/backlog-auto/ltip-docx-fotos.md
- **Doc:** 00_docs/backlog-auto/ltip-docx-fotos.md
- **Pronto:** `ltip_pipeline.gerar_docx` embute as fotos das ocorrências (com legenda via `legenda_para_relatorio`) no DOCX; teste novo com fotos sintéticas confere por inspeção do .docx (word/media e texto da legenda) e passa; tempo do DOCX com 239 fotos sintéticas registrado; `pytest` e `ruff check .` limpos em 04_backend.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md (raiz do repositório). Papel: Engenheiro Backend (.github/agents/backend.agent.md). Contexto: a T20 (00_docs/backlog-auto/ltip-desempenho.md) deixou pendente 'foto no DOCX do LTIP'. Arquivo: 04_backend/app/services/report_generator/ltip_pipeline.py (`gerar_docx`); o PDF já usa fotos por `url_fetcher` (DEC-41, 00_docs/projeto/decisoes.md) e a legenda vem de `legenda_foto.py` (T36). Veja como `rfo_pipeline.py` (somente leitura) embute fotos no DOCX e como `foto_fetcher.py` obtém os bytes; siga o mesmo padrão, reduzindo a imagem para a largura útil da página (fotos de 1200 px, DEC-40) para não inflar o arquivo. Mantenha o contrato de `normalizar_contexto` e o PDF intactos; foto indisponível não derruba o DOCX (placeholder de texto e aviso no log). Crie tests/test_ltip_docx_fotos.py sem banco e sem rede (fetcher injetado/monkeypatch, imagens geradas com Pillow) e meça o tempo com ~239 fotos sintéticas. Rode, a partir de 04_backend, `pytest tests/test_ltip_docx_fotos.py tests/test_ltip_pipeline.py` e `ruff check .`. Registre fatos, tempos e saídas em 00_docs/backlog-auto/ltip-docx-fotos.md. Não edite 00_docs/projeto/* nem BACKLOG.md; não altere 01_output-context/. Commit: `feat(backend): fotos no DOCX do LTIP (BL-22)` com `Refs BL-22`. Não faça push.
```

### T102 · Limite de corpo no proxy para o upload de fotos
- **Status:** done
- **Origem:** T19
- **Papel:** Engenheiro DevOps
- **Depende:** —
- **Ambiente:** offline
- **Dificuldade:** baixa
- **Toca:** 05_infra/nginx/nginx.conf, 05_infra/nginx/, 00_docs/backlog-auto/fotos-limite-corpo-proxy.md
- **Doc:** 00_docs/backlog-auto/fotos-limite-corpo-proxy.md
- **Pronto:** O nginx de produção tem `client_max_body_size` explícito: valor alinhado ao teto de upload do backend na rota de upload de fotos e valor menor nas demais rotas da API; a configuração foi validada com `nginx -t` (se houver nginx/Docker disponível) ou o Doc diz que não foi possível; o Doc cita o limite do backend com arquivo:linha.
- **Prompt:**
```text
Contexto: a T19 (BL-11, DEC-39) deixou pendente o limite de corpo da requisição no proxy para o upload de fotos. A stack alternativa de produção em VPS usa 05_infra/nginx/nginx.conf (BL-27). Tarefa: leia o limite de tamanho de upload aplicado no backend (procure em 04_backend/app/api/v1/fotos.py e em app/core/config.py, por exemplo o máximo de bytes por foto) e em 05_infra/nginx/nginx.conf defina `client_max_body_size` com um valor um pouco acima do teto do backend na location do upload de fotos (ex.: `location = /api/v1/fotos/upload`) e um valor baixo (ex.: 1m) para o restante da API, retornando 413. Preserve rate limit, HSTS, CSP e as demais regras já existentes. Se houver nginx ou Docker disponível, valide com `nginx -t` (container `nginx:alpine` montando o arquivo, a partir de 05_infra/); se não, registre que não foi possível. Não altere o backend nem o frontend. Documente no Doc o limite do backend (arquivo:linha), o valor escolhido e por quê, e o comando e a saída da validação. Siga a 'Regra de pronto' do BACKLOG.md. Não edite os documentos de gestão em 00_docs/projeto/ nem o BACKLOG.md. Commit: `feat(infra): limite de corpo no nginx para upload de fotos (DEC-39)` com `Refs DEC-39`. Não faça push.
```

### T107 · Legenda IA: limpar os xfail estritos de test_seguranca_legenda_ia.py que o código já cumpre
- **Status:** done
- **Origem:** T35
- **Papel:** Engenheiro Backend
- **Depende:** —
- **Ambiente:** docker
- **Dificuldade:** baixa
- **Toca:** 04_backend/tests/test_seguranca_legenda_ia.py, 00_docs/backlog-auto/legenda-ia-xfail-limpeza.md
- **Doc:** 00_docs/backlog-auto/legenda-ia-xfail-limpeza.md
- **Pronto:** pytest tests/test_seguranca_legenda_ia.py com PostgreSQL localhost:5433 sem nenhum teste XPASS(strict) nem falha: cada `xfail` cuja lacuna (SEG-IA-01..06) já foi corrigida (limite de taxa 429, aprovação limpa ao regerar/editar, teto de 500 caracteres, 403 ao auxiliar) vira teste normal passando; os que seguem lacuna real permanecem `xfail(strict=True)` com motivo atualizado; Doc lista, por teste, a decisão e a evidência (saída do pytest); ruff check . limpo.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md (raiz) e as regras do projeto: comandos Python a partir de 04_backend/ no venv 04_backend/.venv, banco isolado garra_engenharia_test (veja a regra de pronto item 6), commits Conventional Commits com escopo 'test(backend)' e rodapé 'Refs T35', sem push, sem tocar nas branches main_back/main_front/staging_back/staging_front, sem editar documentos de gestão compartilhados. Papel: Engenheiro Backend. Antes de tudo rode `git merge --ff-only main`.

Contexto: 04_backend/tests/test_seguranca_legenda_ia.py nasceu da T29 com testes `@pytest.mark.xfail(strict=True)` que afirmam o comportamento correto das lacunas SEG-IA-01..06 (limite de taxa em /legenda-ia/gerar, aprovador mantido ao regerar/editar, sugestão do LLM acima de 500 caracteres, auxiliar removendo foto aprovada etc.). As tarefas T33 e T35 depois implementaram limite de taxa (429), teto de 500 caracteres, saneamento e aprovação só pelo auditor (DEC-42). A pendência registrada na T35 é remover as marcas xfail que deixaram de valer. Detalhes em 00_docs/backlog-auto/seguranca-legenda-ia.md e nos Docs da T33/T35 (procure em 00_docs/backlog-auto/ com Grep por 'DEC-42' e 'limite').

Tarefa: (1) Suba o PostgreSQL de 05_infra (docker compose a partir de 05_infra/, porta 5433) se não estiver no ar, aplique `alembic upgrade head` no garra_engenharia_test e rode `pytest tests/test_seguranca_legenda_ia.py -v -rxX`. (2) Para cada teste xfail: se aparece XPASS/ falha por strict, a lacuna foi corrigida — remova a marca `xfail`, ajuste o teste só se o contrato correto mudou (ex.: status/mensagem), e confira que ele passa de verdade; se continua XFAIL, mantenha a marca e atualize o `reason` com o estado atual (cite o SEG-IA-xx). NÃO altere código de produção nem enfraqueça asserções para fazer passar; se um teste revelar bug real, mantenha xfail e descreva no Doc como proposta. (3) Rode também `pytest -k legenda` e `ruff check .` para garantir que nada quebrou. (4) Registre no Doc a tabela teste → decisão → evidência e a saída literal do pytest. Se o PostgreSQL não subir, registre que não rodou e não altere nenhum teste às cegas.
```

### T108 · Legenda IA: devolver o cabeçalho Retry-After no 429 de /legenda-ia/gerar
- **Status:** done
- **Origem:** T35
- **Papel:** Engenheiro Backend
- **Depende:** T107
- **Ambiente:** docker
- **Dificuldade:** media
- **Toca:** 04_backend/app/core/errors.py, 04_backend/app/core/exception_handlers.py, 04_backend/app/services/legenda_ia/limites.py, 04_backend/tests/test_legenda_ia_retry_after.py, 00_docs/backlog-auto/legenda-ia-retry-after.md
- **Doc:** 00_docs/backlog-auto/legenda-ia-retry-after.md
- **Pronto:** Resposta 429 de POST /api/v1/fotos/{id}/legenda-ia/gerar carrega o header `Retry-After` (inteiro > 0, em segundos) além do corpo RFC 7807 atual (que continua com `retry_after_segundos` em `errors`); outras DomainError continuam sem esse header; teste novo cobre header presente no 429 de legenda, ausente em um 4xx comum e o login (que já tem Retry-After) intacto; pytest -k 'legenda or seguranca' e ruff check . verdes com PostgreSQL localhost:5433.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md (raiz) e as regras do projeto: comandos Python a partir de 04_backend/ no venv 04_backend/.venv, banco isolado garra_engenharia_test, commits Conventional Commits com escopo 'feat(backend)' e rodapé 'Refs T35', sem push, sem tocar nas branches main_back/main_front/staging_back/staging_front, sem editar documentos de gestão compartilhados. Papel: Engenheiro Backend. Antes de tudo rode `git merge --ff-only main`. Não use nova variável de ambiente nem migration.

Contexto: 04_backend/app/services/legenda_ia/limites.py define `LimiteLegendaIAExcedido(DomainError)` (429, atributo `retry_after`), e o docstring admite que 'o handler global não repassa headers' — por isso o tempo de espera só vai no corpo. O handler global é `_handle_domain_error` em 04_backend/app/core/exception_handlers.py (registrado na linha ~85); `DomainError` está em 04_backend/app/core/errors.py. O login (04_backend/app/api/v1/auth.py, ~linha 67-75) já devolve 429 com Retry-After de forma própria — veja como e não quebre. A T35 deixou 'Retry-After no header' como pendência.

Tarefa: (1) Leia os três arquivos e os testes existentes de limite (Grep por 'legenda-ia-limite-excedido' em 04_backend/tests). (2) Faça o `DomainError` poder carregar `headers: dict[str,str] | None` (ou equivalente mínimo e retrocompatível) e o `_handle_domain_error` repassá-los à resposta; faça `LimiteLegendaIAExcedido` preencher `Retry-After` com `str(retry_after)` (garanta inteiro >= 1). Mantenha o corpo RFC 7807 idêntico. (3) Escreva tests/test_legenda_ia_retry_after.py reaproveitando as fixtures/ helpers dos testes de limite existentes (cliente fake, usuário auditor/auxiliar, foto): estoure o limite configurando valores pequenos, confira status 429, header Retry-After inteiro > 0 igual ao `retry_after_segundos` do corpo, e que um erro 404/422 comum não tem Retry-After. (4) Rode `pytest -k 'legenda or seguranca or auth'` e `ruff check .`; se o PostgreSQL (localhost:5433) não estiver no ar, suba-o via docker compose em 05_infra ou registre que não rodou. (5) Registre no Doc o diff resumido, a saída dos testes e eventuais propostas (ex.: limitador compartilhado entre workers continua pendente, não faça agora).
```

---

## Bloco D — Entrega v1.0: emissão dos 5 relatórios

### T57 · Fundação de dados da emissão: tipo de serviço normalizado, conteúdo narrativo do relatório e campos do responsável
- **Status:** done
- **Origem:** V1-01
- **Papel:** Engenheiro Backend
- **Depende:** —
- **Ambiente:** docker
- **Dificuldade:** alta
- **Toca:** 04_backend/app/models, 04_backend/app/schemas, 04_backend/alembic/versions, 04_backend/app/api/v1/conteudos.py, 04_backend/app/main.py, 04_backend/app/services/relatorio_conteudo_service.py, 04_backend/app/services/report_generator/textos_padrao, 04_backend/tests/test_relatorio_conteudo.py, 00_docs/backlog-auto/v1-fundacao-dados.md
- **Doc:** 00_docs/backlog-auto/v1-fundacao-dados.md
- **Pronto:** Uma migration nova (único head, downgrade validado upgrade→downgrade→upgrade em banco descartável) normaliza `contratos.tipo_servico` e `inspecoes.tipo` para maiúsculas, cria `relatorio_conteudos` (inspecao_id, tipo, dados JSONB, atualizado_por_id, atualizado_em, UNIQUE(inspecao_id,tipo)) e adiciona `titulo_profissional`, `qualificacoes` (JSONB) e `assinatura_storage_key` em `responsaveis`; enum `TipoServico` validado nos schemas; `GET/PUT /api/v1/inspecoes/{id}/conteudo/{tipo}` funcionando (GET mescla padrões + salvo; PUT só auditor); textos padrão JSON de LTIP, Vistoria Cautelar e Vistoria Residencial extraídos dos convertidos; testes novos passam no PostgreSQL de 05_infra; `pytest` dos arquivos tocados e `ruff check .` limpos.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md (raiz do repositório). Papel: Engenheiro Backend (.github/agents/backend.agent.md). Contexto: plano de entrega v1.0 — os 5 relatórios (RFO, LTIP, RFIP, VISTORIA_CAUTELAR, VISTORIA_RESIDENCIAL) precisam ser emitidos a partir do banco, mas LTIP e as duas vistorias exigem textos narrativos e dados que não existem no modelo (veja 00_docs/backlog-auto/{ltip,rfip,vistoria-cautelar,vistoria-residencial}-pipeline.md e as funções `normalizar_contexto` em 04_backend/app/services/report_generator/*_pipeline.py). Hoje `inspecao.tipo` e `contrato.tipo_servico` são String livre (há valores minúsculos como 'ltip'); a inspeção copia o tipo do contrato em app/repositories/contrato_repository.py:74; o frontend usa `TipoServico` em 03_frontend/lib/types.ts:66. Implemente: (1) enum `TipoServico` (RFO, LTIP, RFIP, VISTORIA_CAUTELAR, VISTORIA_RESIDENCIAL) validado em schemas/contrato.py e schemas/inspecao.py (aceite minúsculas na entrada convertendo para maiúsculas); ajuste `visita_service.py` e `rfo_contexto.py` para comparar com o enum. (2) Rode `alembic heads` (deve haver um único head) e crie UMA migration nova com: UPDATE upper() em contratos.tipo_servico e inspecoes.tipo; tabela `relatorio_conteudos` (id uuid, inspecao_id FK, tipo, dados JSONB not null default '{}', atualizado_por_id FK usuarios nullable, atualizado_em, UNIQUE(inspecao_id, tipo)); colunas em `responsaveis`: titulo_profissional (String null), qualificacoes (JSONB null), assinatura_storage_key (String null). downgrade() obrigatório (não reverte o upper). Valide upgrade→downgrade→upgrade num banco temporário criado no PostgreSQL de 05_infra (localhost:5433), nunca no banco de dev. (3) Modelo `RelatorioConteudo`, schemas e serviço `relatorio_conteudo_service.py` com `obter(db, inspecao_id, tipo)` que retorna padrões do tipo mesclados (deep merge) com o salvo, e `salvar(...)`. Os campos aceitos em `dados`: textos narrativos por chave do pipeline, `data_emissao`, `local_emissao`, `parecer`, `unidade`, `datas_vistorias`, `incluir_resumo`, `metodologia_corretiva` (mapa ocorrencia_id→texto) e `fundamentacao_tecnica` (mapa sistema_id→lista de parágrafos). Valide tamanho (teto por texto e total) para não aceitar payload gigante. (4) Rotas em NOVO arquivo app/api/v1/conteudos.py: `GET /api/v1/inspecoes/{id}/conteudo/{tipo}` (auditor e auxiliar) e `PUT` (só auditor, `require_auditor`); inclua o router em app/main.py. Também exponha os 3 campos novos do responsável nos schemas de Responsavel (create/update/read). (5) Textos padrão: crie app/services/report_generator/textos_padrao/{ltip,vistoria_cautelar,vistoria_residencial}.json com as chaves EXATAS que cada pipeline espera (LTIP: introducao, consideracoes_preliminares, objetivo, metodologia, documentacao_analisada, conclusao; Cautelar: as chaves de `conteudo.*`; Residencial: as chaves de `textos.*`), com texto extraído dos originais convertidos em 00_docs/convertidos/ (Laudo_Tecnico_de_Inspecao_Predial_2026..., Laudo_Tecnico_de_Vistoria_Cautelar..., Laudo_Tecnico_de_Vistoria_de_Imovel_Residencial...), substituindo nomes de cliente/endereço/datas específicos por texto genérico ou placeholders `{edificacao_nome}` que o serviço preenche. (6) tests/test_relatorio_conteudo.py: enum normaliza minúsculas; GET devolve padrões; PUT de auditor salva e GET mescla; PUT de auxiliar 403; payload acima do teto 422. O Docker está em `C:\Program Files\Docker\Docker\resources\bin` (adicione ao PATH) e o PostgreSQL/MinIO de 05_infra já estão no ar. Rode, a partir de 04_backend, `alembic heads`, `pytest tests/test_relatorio_conteudo.py tests/test_relatorios_rfo_api.py tests/test_rfo_contexto.py` e `ruff check .`. Registre fatos e saídas em 00_docs/backlog-auto/v1-fundacao-dados.md (inclua o contrato final de `dados` por tipo, pois as tarefas seguintes dependem dele). Não edite 00_docs/projeto/* nem BACKLOG.md; não altere 01_output-context/. Commit: `feat(backend): conteúdo narrativo do relatório e tipo de serviço normalizado (V1-01)` com `Refs V1-01`. Não faça push.
```

### T58 · Emissão genérica por tipo: registro de emissores, rota por tipo, listagem de versões e download interno
- **Status:** done
- **Origem:** V1-02
- **Papel:** Engenheiro Backend
- **Depende:** —
- **Ambiente:** docker
- **Dificuldade:** alta
- **Toca:** 04_backend/app/services/relatorio_service.py, 04_backend/app/services/report_generator/imagem.py, 04_backend/app/api/v1/relatorios.py, 04_backend/app/schemas/relatorio.py, 04_backend/tests/test_relatorios_emissao_generica.py, 00_docs/backlog-auto/v1-emissao-generica.md
- **Doc:** 00_docs/backlog-auto/v1-emissao-generica.md
- **Pronto:** `relatorio_service` usa um registro {tipo: Emissor(montar_contexto, validar, pipeline, extrair_fotos)} com o RFO como única entrada (comportamento idêntico, testes do RFO passam); chave de storage `relatorios/{inspecao_id}/{tipo_minusculo}-{versao}.{ext}`; `otimizar_imagem` num módulo comum; rotas `POST /api/v1/inspecoes/{id}/relatorios/{tipo}` (tipo não registrado → 422 claro; `/rfo` continua funcionando), `GET /api/v1/inspecoes/{id}/relatorios` e `GET /api/v1/inspecoes/{id}/relatorios/{relatorio_id}/download/{formato}` (URL pré-assinada, auditor e auxiliar); testes novos passam no PostgreSQL de 05_infra; `ruff check .` limpo.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md (raiz do repositório). Papel: Engenheiro Backend (.github/agents/backend.agent.md). Contexto: plano de entrega v1.0 — hoje só o RFO é emitido. Em 04_backend/app/services/relatorio_service.py o RFO está fixo em: imports de `montar_contexto_rfo`/`validar_contexto_rfo`/`TIPO_RFO` (~:28-32, :152-155), `RfoContextoIncompletoError` (:45-56), `RenderizadorRFOPadrao._pipeline()` (:83) e `pipeline.otimizar_imagem` (:94, só existe em rfo_pipeline.py:73), `chave_relatorio` (:107-109), `storage_keys_das_fotos` só lê `visitas[].fotos` (:118-121) e a contagem de versão por `TIPO_RFO` (:165, :186). Lock, versão, upload e rollback (:156-199) já são agnósticos. A rota única está em app/api/v1/relatorios.py. Download hoje só existe no portal (app/api/v1/portal.py:81-94 → portal_service.gerar_url_download :224-257, filtrando por contratante). Implemente, SEM adicionar outros tipos além do RFO (outras tarefas fazem isso): (1) dataclass `Emissor` e registro `EMISSORES: dict[str, Emissor]` com função `registrar_emissor(tipo, emissor)`; RFO registrado; `extrair_fotos(contexto) -> set[str]` por tipo; `RenderizadorRFO` vira `Renderizador` genérico que recebe o módulo do pipeline (mantenha alias para não quebrar testes existentes e o `get_renderizador_rfo`). (2) mova `otimizar_imagem` para app/services/report_generator/imagem.py e importe dali (rfo_pipeline mantém um re-export). (3) Erro de contexto incompleto genérico (`ContextoIncompletoError` com o tipo), mantendo `RfoContextoIncompletoError` como subclasse/alias. (4) chave `relatorios/{inspecao_id}/{tipo.lower()}-{versao}.{ext}`; para o RFO preserve o formato atual. (5) Rotas: `POST /{inspecao_id}/relatorios/{tipo}` (tipo normalizado para maiúsculas; não registrado → 422 com a lista de tipos disponíveis; o tipo pedido precisa bater com `inspecao.tipo`, senão 409), mantendo `POST .../relatorios/rfo`; `GET /{inspecao_id}/relatorios` lista versões (tipo, versao, status, emitido_em, tem_pdf, tem_docx); `GET /{inspecao_id}/relatorios/{relatorio_id}/download/{formato}` (pdf|docx) devolve URL pré-assinada reutilizando a lógica de portal_service sem o filtro de contratante, para `auditor` e `auxiliar` (cliente → 403; relatório de outra inspeção → 404). (6) tests/test_relatorios_emissao_generica.py com renderizador fake: tipo inexistente 422; tipo ≠ inspeção 409; listagem; download por papel (auditor 200, auxiliar 200, cliente 403) e relatório de outra inspeção 404; registrar um emissor fake 'TESTE' em teste e emitir por ele. O Docker está em `C:\Program Files\Docker\Docker\resources\bin` (adicione ao PATH) e o PostgreSQL/MinIO de 05_infra já estão no ar. Rode, a partir de 04_backend, `pytest tests/test_relatorios_emissao_generica.py tests/test_relatorios_rfo_api.py tests/test_rfo_contexto.py tests/test_rfo_pipeline.py` e `ruff check .`. Registre em 00_docs/backlog-auto/v1-emissao-generica.md o contrato do `Emissor` e como registrar um tipo novo (as tarefas de LTIP/RFIP/vistorias dependem disso). Não edite 00_docs/projeto/* nem BACKLOG.md; não altere 01_output-context/. Commit: `refactor(backend): emissão de relatório genérica por tipo (V1-02)` com `Refs V1-02`. Não faça push.
```

### T59 · LTIP e RFIP: contexto a partir do banco e registro na emissão
- **Status:** done
- **Origem:** V1-03
- **Papel:** Engenheiro Backend
- **Depende:** T57, T58
- **Ambiente:** docker
- **Dificuldade:** media
- **Toca:** 04_backend/app/services/report_generator/ltip_contexto.py, 04_backend/app/services/report_generator/rfip_contexto.py, 04_backend/app/services/report_generator/contexto_comum.py, 04_backend/app/services/relatorio_service.py, 04_backend/tests/test_ltip_rfip_contexto.py, 00_docs/backlog-auto/v1-ltip-rfip-contexto.md
- **Doc:** 00_docs/backlog-auto/v1-ltip-rfip-contexto.md
- **Pronto:** `montar_contexto_ltip` e `montar_contexto_rfip` montam, a partir do banco, contextos aceitos por `ltip_pipeline.normalizar_contexto`/`rfip_pipeline.normalizar_contexto`; ambos registrados como emissores (POST .../relatorios/LTIP e /RFIP emitem com renderizador fake nos testes); só legenda aprovada entra (`legenda_para_relatorio`); ocorrências ordenadas por sistema/subsistema; textos do LTIP vêm de `relatorio_conteudos` com padrão; validação de completude devolve 422 por campo; testes novos passam no PostgreSQL de 05_infra e o PDF real é gerado ao menos uma vez dentro do container backend; `ruff check .` limpo.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md (raiz do repositório). Papel: Engenheiro Backend (.github/agents/backend.agent.md). Leia antes os Docs 00_docs/backlog-auto/v1-fundacao-dados.md (contrato de `relatorio_conteudos.dados` e textos padrão) e 00_docs/backlog-auto/v1-emissao-generica.md (como registrar um `Emissor`). Referências: app/services/report_generator/rfo_contexto.py (padrão de montagem; `_ocorrencia_ctx` ~:105-120 não leva gut_* nem as ordens), ltip_pipeline.py (:54-77, :193-215) e rfip_pipeline.py (:89-112) para as chaves exigidas; Docs 00_docs/backlog-auto/ltip-pipeline.md e rfip-pipeline.md; helper `legenda_para_relatorio` (app/services/report_generator/legenda_foto.py); fixtures de contexto em tests/test_ltip_pipeline.py:34 e tests/test_rfip_pipeline.py:36. Implemente: (1) contexto_comum.py com funções reutilizáveis: carregar inspeção+contrato+edificação+fiscal, ocorrências com sistema/subsistema (incluindo `ordem`), gut_gravidade/urgencia/tendencia, grau de risco, prioridade, localização e fotos com legenda via `legenda_para_relatorio`; campos vazios viram '—' (DEC-33); refatore rfo_contexto para usar o comum só onde for trivial, sem mudar a saída do RFO. (2) ltip_contexto.py: edificacao, fiscal, contrato.art_fiscalizacao, data_emissao (do conteúdo ou hoje), sistemas/ocorrências, textos do conteúdo (`objeto` padrão = contrato.objeto; `documentacao_analisada` padrão montado de contrato.nbrs e edificacao.documentos_tecnicos). (3) rfip_contexto.py: responsavel (fiscal, com titulo_profissional), ocorrências, `incluir_resumo` do conteúdo (padrão true). (4) `validar_contexto_*` com a lista de obrigatórios de cada template (422 com campos faltantes, como a T50 fez para o RFO). (5) Registre LTIP e RFIP no registro de emissores com `extrair_fotos` correto (fotos das ocorrências). (6) tests/test_ltip_rfip_contexto.py com dados no banco: contexto passa no normalizar_contexto de cada pipeline; legenda não aprovada não aparece; ordem por sistema; 422 sem fiscal; emissão via POST com renderizador fake cria Relatorio tipo LTIP/RFIP versão 1. (7) Gere uma vez o PDF e o DOCX reais de cada tipo dentro do container: `cd 05_infra; docker compose build backend; docker compose run --rm backend python -c ...` (ou script equivalente) e registre páginas, tempo e tamanho. O Docker está em `C:\Program Files\Docker\Docker\resources\bin` (adicione ao PATH). Rode, a partir de 04_backend, `pytest tests/test_ltip_rfip_contexto.py tests/test_ltip_pipeline.py tests/test_rfip_pipeline.py tests/test_rfo_contexto.py tests/test_relatorios_rfo_api.py` e `ruff check .`. Registre fatos e saídas em 00_docs/backlog-auto/v1-ltip-rfip-contexto.md. Não edite 00_docs/projeto/* nem BACKLOG.md; não altere 01_output-context/. Commit: `feat(backend): emissão do LTIP e do RFIP a partir do banco (V1-03)` com `Refs V1-03`. Não faça push.
```

### T60 · Vistoria Cautelar: contexto a partir do banco e registro na emissão
- **Status:** done
- **Origem:** V1-04
- **Papel:** Engenheiro Backend
- **Depende:** T57, T58
- **Ambiente:** docker
- **Dificuldade:** alta
- **Toca:** 04_backend/app/services/report_generator/vistoria_cautelar_contexto.py, 04_backend/app/services/relatorio_service.py, 04_backend/tests/test_vistoria_cautelar_contexto.py, 00_docs/backlog-auto/v1-vistoria-cautelar-contexto.md
- **Doc:** 00_docs/backlog-auto/v1-vistoria-cautelar-contexto.md
- **Pronto:** `montar_contexto_vistoria_cautelar` monta, a partir do banco e de `relatorio_conteudos`, um contexto aceito por `vistoria_cautelar_pipeline.normalizar_contexto`; registrado como emissor VISTORIA_CAUTELAR; testes novos passam no PostgreSQL de 05_infra; PDF e DOCX reais gerados uma vez no container backend sem 'None' nem chave Jinja crua; `ruff check .` limpo.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md (raiz do repositório). Papel: Engenheiro Backend (.github/agents/backend.agent.md). Leia antes 00_docs/backlog-auto/v1-fundacao-dados.md (contrato de `relatorio_conteudos.dados`, textos padrão em app/services/report_generator/textos_padrao/vistoria_cautelar.json, campos novos do responsável) e 00_docs/backlog-auto/v1-emissao-generica.md (registro de `Emissor`). Referências: app/services/report_generator/vistoria_cautelar_pipeline.py (:49-58, :117-167), 00_docs/backlog-auto/vistoria-cautelar-pipeline.md, fixture tests/test_vistoria_cautelar_pipeline.py:35-72, rfo_contexto.py como padrão, e o módulo contexto_comum.py se já existir na main (se não existir, não o crie: escreva as consultas no próprio arquivo). Mapeamento: responsavel ← fiscal do contrato (nome, crea, email, telefone, titulo_profissional, qualificacoes); obra.descricao ← contrato.objeto; edificacao.nome; data_emissao/local_emissao ← conteúdo (padrão hoje / cidade da edificação); conteudo.* ← textos do conteúdo com padrão; complementos.parecer_tecnico ← conteúdo.parecer; tabelas.identificacao ← Edificacao (endereço, CEP, tipologia, sistema construtivo, pavimentos, área total); tabelas.plano_de_correcoes_remanescentes ← ocorrências (seq_numero, localizacao, descricao) + conteúdo.metodologia_corretiva[ocorrencia_id] ('—' se ausente); sistemas[] ← ocorrências agrupadas por sistema (constatacoes = descrições) + conteúdo.fundamentacao_tecnica[sistema_id]; figuras[] ← fotos das ocorrências com `legenda_para_relatorio`, numeradas; assinatura_storage_key ← responsavel.assinatura_storage_key (opcional); capa opcional. Implemente `validar_contexto_vistoria_cautelar` (422 por campo: fiscal, parecer) e registre o emissor com `extrair_fotos` incluindo figuras e assinatura. tests/test_vistoria_cautelar_contexto.py com dados no banco: contexto passa no normalizar_contexto; legenda não aprovada não entra; metodologia por ocorrência aparece; sem parecer → 422; POST .../relatorios/VISTORIA_CAUTELAR com renderizador fake cria versão 1. Gere uma vez o PDF e o DOCX reais dentro do container (`cd 05_infra; docker compose build backend; docker compose run --rm backend ...`) e confira que não há 'None' nem `{{` no texto (extraia o texto do PDF com pypdf/pdfplumber). O Docker está em `C:\Program Files\Docker\Docker\resources\bin` (adicione ao PATH). Rode, a partir de 04_backend, `pytest tests/test_vistoria_cautelar_contexto.py tests/test_vistoria_cautelar_pipeline.py tests/test_relatorios_rfo_api.py` e `ruff check .`. Registre fatos e saídas em 00_docs/backlog-auto/v1-vistoria-cautelar-contexto.md. Não edite 00_docs/projeto/* nem BACKLOG.md; não altere 01_output-context/. Commit: `feat(backend): emissão da Vistoria Cautelar a partir do banco (V1-04)` com `Refs V1-04`. Não faça push.
```

### T61 · Vistoria Residencial: contexto a partir do banco e registro na emissão
- **Status:** done
- **Origem:** V1-05
- **Papel:** Engenheiro Backend
- **Depende:** T57, T58
- **Ambiente:** docker
- **Dificuldade:** alta
- **Toca:** 04_backend/app/services/report_generator/vistoria_residencial_contexto.py, 04_backend/app/services/relatorio_service.py, 04_backend/tests/test_vistoria_residencial_contexto.py, 00_docs/backlog-auto/v1-vistoria-residencial-contexto.md
- **Doc:** 00_docs/backlog-auto/v1-vistoria-residencial-contexto.md
- **Pronto:** `montar_contexto_vistoria_residencial` monta, a partir do banco e de `relatorio_conteudos`, um contexto aceito por `vistoria_residencial_pipeline.normalizar_contexto`; registrado como emissor VISTORIA_RESIDENCIAL; assinatura e capa convertidas para data URI quando existirem; testes novos passam no PostgreSQL de 05_infra; PDF e DOCX reais gerados uma vez no container backend sem 'None' nem chave Jinja crua; `ruff check .` limpo.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md (raiz do repositório). Papel: Engenheiro Backend (.github/agents/backend.agent.md). Leia antes 00_docs/backlog-auto/v1-fundacao-dados.md (contrato de `relatorio_conteudos.dados`, textos padrão em app/services/report_generator/textos_padrao/vistoria_residencial.json, campos novos do responsável) e 00_docs/backlog-auto/v1-emissao-generica.md (registro de `Emissor`). Referências: app/services/report_generator/vistoria_residencial_pipeline.py (:48-61, :103-138), 00_docs/backlog-auto/vistoria-residencial-pipeline.md (item aberto 1, ~linha 88), fixture tests/test_vistoria_residencial_pipeline.py:32-71, rfo_contexto.py como padrão, e o módulo contexto_comum.py se já existir na main (se não existir, não o crie: escreva as consultas no próprio arquivo). Mapeamento: imovel.unidade ← conteúdo.unidade ('—' se ausente); edificacao.nome; fiscal ← fiscal do contrato (nome, crea, email, telefone, qualificacoes); data_emissao/local_emissao ← conteúdo (padrão hoje / cidade da edificação); textos.* ← conteúdo com padrão, sendo s4_2_1 (tipologia), s4_2_2 (caracterização: sistema construtivo, pavimentos, área) e s4_2_3 (localização: endereço, CEP) gerados da Edificacao quando o conteúdo não os trouxer, s5_1 gerado do fiscal e s5_2 de conteúdo.datas_vistorias; fotos[] ← fotos das ocorrências com `legenda_para_relatorio`, numeradas, `fonte` padrão 'Autor'; sistemas[] ← ocorrências por sistema + conteúdo.fundamentacao_tecnica[sistema_id]; assinatura_data_uri/capa_fundo_data_uri ← bytes do storage convertidos para data URI (opcionais; erro do storage não derruba a emissão, só registra aviso). Implemente `validar_contexto_vistoria_residencial` (422 por campo: fiscal, unidade) e registre o emissor com `extrair_fotos`. tests/test_vistoria_residencial_contexto.py com dados no banco: contexto passa no normalizar_contexto; s4_2_x gerados da edificação; legenda não aprovada não entra; sem unidade → 422; POST .../relatorios/VISTORIA_RESIDENCIAL com renderizador fake cria versão 1. Gere uma vez o PDF e o DOCX reais dentro do container (`cd 05_infra; docker compose build backend; docker compose run --rm backend ...`) e confira que não há 'None' nem `{{` no texto. O Docker está em `C:\Program Files\Docker\Docker\resources\bin` (adicione ao PATH). Rode, a partir de 04_backend, `pytest tests/test_vistoria_residencial_contexto.py tests/test_vistoria_residencial_pipeline.py tests/test_relatorios_rfo_api.py` e `ruff check .`. Registre fatos e saídas em 00_docs/backlog-auto/v1-vistoria-residencial-contexto.md. Não edite 00_docs/projeto/* nem BACKLOG.md; não altere 01_output-context/. Commit: `feat(backend): emissão da Vistoria Residencial a partir do banco (V1-05)` com `Refs V1-05`. Não faça push.
```

### T62 · Frontend: tela de relatório (textos, emissão, versões e download)
- **Status:** done
- **Origem:** V1-06
- **Papel:** Engenheiro Frontend
- **Depende:** T57, T58
- **Ambiente:** offline
- **Dificuldade:** alta
- **Toca:** 03_frontend/app/inspecoes/[id]/relatorio, 03_frontend/components/relatorio, 03_frontend/lib/api-client.ts, 03_frontend/lib/types.ts, 03_frontend/app/responsaveis, 03_frontend/e2e/relatorio.spec.ts, 00_docs/backlog-auto/v1-frontend-relatorio.md
- **Doc:** 00_docs/backlog-auto/v1-frontend-relatorio.md
- **Pronto:** O placeholder de app/inspecoes/[id]/relatorio/page.tsx é substituído por uma tela funcional: formulário de textos do conteúdo (pré-preenchido com o padrão, salvar), botão 'Emitir nova versão' (só auditor), tabela de versões com download de PDF e DOCX, erros 422 de completude exibidos por campo; campos novos do responsável (título profissional, qualificações, upload de assinatura) no cadastro de responsáveis; usável em tela de 5,5"; 5 ou mais testes Playwright com API mockada em e2e/relatorio.spec.ts passam; `npm run lint` e `npm run build` limpos.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md (raiz do repositório). Papel: Engenheiro Frontend (.github/agents/frontend.agent.md). Leia antes os Docs 00_docs/backlog-auto/v1-fundacao-dados.md (rotas `GET/PUT /api/v1/inspecoes/{id}/conteudo/{tipo}`, contrato de `dados` por tipo, campos novos do responsável) e 00_docs/backlog-auto/v1-emissao-generica.md (rotas `POST /api/v1/inspecoes/{id}/relatorios/{tipo}`, `GET /api/v1/inspecoes/{id}/relatorios`, `GET /api/v1/inspecoes/{id}/relatorios/{relatorio_id}/download/{formato}`), e os schemas reais em 04_backend/app/schemas (só leitura). Contexto: 03_frontend/app/inspecoes/[id]/relatorio/page.tsx é placeholder (`UnderConstruction`), linkado de app/contratos/[id]/page.tsx:136; o cliente HTTP é 03_frontend/lib/api-client.ts (api.get/post/put/delete) e os tipos ficam em lib/types.ts (`TipoServico` :66); o portal já faz download por URL pré-assinada em app/portal/documentos/page.tsx (reuse o padrão); o papel do usuário vem do mesmo mecanismo usado nas telas existentes (veja a T54, 00_docs/backlog-auto/portal-perfil-ui.md). Implemente: (1) helpers tipados em lib/api-client.ts (relatorios.listar/emitir/download, conteudo.obter/salvar) e tipos em lib/types.ts. (2) Tela de relatório: tipo vem da inspeção/contrato; seção 'Textos do relatório' com um textarea por chave do conteúdo (rótulos legíveis; agrupados/colapsáveis; salvar com feedback), campos simples (data/local de emissão; parecer para cautelar; unidade e datas das vistorias para residencial; incluir resumo para RFIP); 'Emitir nova versão' visível só para auditor, com estado de carregamento (a emissão pode levar dezenas de segundos) e exibição dos campos faltantes quando a API devolver 422; tabela de versões (versão, data, status) com botões PDF e DOCX. (3) No cadastro/edição de responsável (localize a tela atual em app/), campos título profissional, qualificações (lista) e upload da imagem de assinatura usando o fluxo de upload existente de fotos/documentos, se houver um reaproveitável; se não houver rota de upload adequada no backend, deixe só os campos de texto e registre a lacuna no Doc. (4) Layout responsivo para 5,5" (sem rolagem horizontal). (5) e2e/relatorio.spec.ts com `page.route` mockando a API: carrega padrões; salva texto; auditor emite e vê nova versão; auxiliar não vê 'Emitir'; 422 mostra campos faltantes; download chama a rota certa. Não altere o backend. Rode, a partir de 03_frontend, `npm run lint`, `npm run build` e o Playwright do spec novo e dos specs do portal; se o Playwright não puder rodar, registre. Registre fatos e saídas em 00_docs/backlog-auto/v1-frontend-relatorio.md. Não edite 00_docs/projeto/* nem BACKLOG.md. Commit: `feat(frontend): tela de emissão e download de relatórios (V1-06)` com `Refs V1-06`. Não faça push.
```

### T63 · Legenda por IA: cliente real da DeepSeek Platform API
- **Status:** done
- **Origem:** V1-07
- **Papel:** Engenheiro Backend
- **Depende:** —
- **Ambiente:** offline
- **Dificuldade:** media
- **Toca:** 04_backend/app/services/legenda_ia, 04_backend/app/core/config.py, 04_backend/.env.example, 05_infra/.env.example, 05_infra/docker-compose.yml, render.yaml, 04_backend/tests/test_legenda_ia_deepseek.py, 00_docs/backlog-auto/v1-legenda-ia-deepseek.md
- **Doc:** 00_docs/backlog-auto/v1-legenda-ia-deepseek.md
- **Pronto:** `DeepSeekLegendaIAClient` implementa o protocolo `LegendaIAClient` (app/services/legenda_ia/contrato.py) chamando a DeepSeek Platform API (compatível com OpenAI, via httpx) e é selecionado em `obter_cliente_provedor()` quando o provedor configurado for 'deepseek'; sem chave configurada continua o Fake; timeout, erro HTTP e resposta inválida viram erro de domínio tratado (sem vazar a chave em log); testes sem rede (httpx MockTransport) passam; variáveis novas em .env.example, compose e render.yaml (chave como segredo `sync: false`); `pytest` dos testes de legenda IA e `ruff check .` limpos.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md (raiz do repositório). Papel: Engenheiro Backend (.github/agents/backend.agent.md). Contexto: o provedor de IA para legendas (B-04) foi decidido: DeepSeek Platform API. Hoje só existe `FakeLegendaIAClient` (04_backend/app/services/legenda_ia/contrato.py); a seleção fica em `obter_cliente_provedor()` (app/services/legenda_ia/__init__.py:31); limites e saneamento já existem (limites.py, saneamento.py, `ClienteLegendaIAProtegido`); variáveis `LEGENDA_IA_*` em app/core/config.py e repassadas por T40 (00_docs/backlog-auto/legenda-ia-env-deploy.md). O prompt do cliente está em 00_docs/cliente/prompt-lado-cliente.md e as versões de prompt em `prompts_ia` (T23). Passo 0 (obrigatório, registrar no Doc): consulte a documentação oficial da DeepSeek (api-docs.deepseek.com) para confirmar base URL, nomes de modelo vigentes e se algum modelo da API aceita imagem (content parts `image_url`). Implemente `DeepSeekLegendaIAClient` em app/services/legenda_ia/deepseek.py: POST {base_url}/chat/completions com Bearer, modelo e timeout configuráveis; se o modelo aceitar imagem, envie a imagem como data URI (JPEG reduzido a no máx. 1024 px com Pillow); se NÃO aceitar, envie só texto (prompt do cliente + legenda bruta delimitada) e registre esse modo (`modo='texto'`) no resultado/log; peça resposta em JSON e converta para `LegendaIAResultado`, rejeitando saída inválida com o erro de domínio já usado pelo saneamento. Configuração nova em config.py: `LEGENDA_IA_PROVEDOR` (fake|deepseek, padrão fake), `DEEPSEEK_API_KEY` (SecretStr, opcional), `DEEPSEEK_BASE_URL` (padrão https://api.deepseek.com), `DEEPSEEK_MODELO`, `DEEPSEEK_TIMEOUT_S`; em produção com provedor deepseek e sem chave, falhar na inicialização com mensagem clara. Nunca logue a chave nem a imagem. Adicione as variáveis em 04_backend/.env.example, 05_infra/.env.example, 05_infra/docker-compose.yml (serviço backend) e render.yaml (`DEEPSEEK_API_KEY` com `sync: false`). tests/test_legenda_ia_deepseek.py sem rede (httpx.MockTransport): resposta válida → resultado; JSON inválido → erro de domínio; HTTP 401/429/500 e timeout → erro tratado; seleção do provedor por config (fake sem chave, deepseek com chave); modo texto não envia imagem. Rode, a partir de 04_backend, `pytest tests/test_legenda_ia_deepseek.py` e os demais testes de legenda IA que não exigem banco, e `ruff check .`. Registre fatos (incluindo o resultado do Passo 0) e saídas em 00_docs/backlog-auto/v1-legenda-ia-deepseek.md. Não edite 00_docs/projeto/* nem BACKLOG.md; nunca commite chaves. Commit: `feat(backend): cliente DeepSeek para legendas por IA (V1-07)` com `Refs V1-07`. Não faça push.
```

### T64 · Seed de demonstração dos 5 tipos e amostras reais de PDF/DOCX para a conferência visual (HT-09)
- **Status:** done
- **Origem:** V1-08
- **Papel:** Engenheiro Backend
- **Depende:** T59, T60, T61
- **Ambiente:** docker
- **Dificuldade:** media
- **Toca:** 04_backend/app/scripts/seed_demo.py, 04_backend/tests/test_seed_demo.py, 00_docs/backlog-auto/v1-amostras-ht09.md
- **Doc:** 00_docs/backlog-auto/v1-amostras-ht09.md
- **Pronto:** `python -m app.scripts.seed_demo` (idempotente) cria um contrato de cada um dos 5 tipos com edificação, fiscal, ocorrências/visitas, fotos sintéticas no MinIO com legendas aprovadas e conteúdo padrão; os 5 relatórios são emitidos pela API dentro do container backend e os PDF/DOCX ficam em 01_output-context/_amostras_ht09/v1/ (pasta nova, sem tocar em nenhum outro arquivo de 01_output-context); o Doc traz, por tipo, páginas, tempo, tamanho e uma folha de conferência (itens a comparar com o original); suíte completa do backend rodada no container com contagens registradas; `ruff check .` limpo.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md (raiz do repositório). Papel: Engenheiro Backend (.github/agents/backend.agent.md). Contexto: com V1-03/04/05 os 5 tipos são emitidos a partir do banco (Docs 00_docs/backlog-auto/v1-*.md). Falta material para a conferência visual humana (HT-09, 00_docs/projeto/backlog-tarefas-humanas.md) e uma execução completa da suíte com banco e WeasyPrint (riscos R-14/R-15). Referência de seed: app/scripts/seed_benchmark_rfo.py. Implemente app/scripts/seed_demo.py idempotente (marca os registros com prefixo 'DEMO'): edificação com endereço completo; fiscal com CREA, título e qualificações; um contrato por tipo (RFO, LTIP, RFIP, VISTORIA_CAUTELAR, VISTORIA_RESIDENCIAL); para RFO 2 visitas com mão de obra, medições e fotos; para os demais ~8 ocorrências em 4 sistemas com GUT e grau de risco; fotos sintéticas (Pillow, 1200 px) enviadas ao MinIO de 05_infra com legendas aprovadas; conteúdo padrão salvo (parecer e unidade preenchidos). Teste tests/test_seed_demo.py: rodar duas vezes não duplica. Depois, no container (o Docker está em `C:\Program Files\Docker\Docker\resources\bin`, adicione ao PATH): `cd 05_infra; docker compose build backend; docker compose up -d`; rode alembic upgrade head e o seed dentro do container; emita os 5 relatórios pela API (auditor de seed_admin ou criado pelo seed) e baixe PDF/DOCX para 01_output-context/_amostras_ht09/v1/<tipo>-v1.pdf|docx — crie SOMENTE essa pasta nova; não altere nem apague nada mais em 01_output-context/. Rode a suíte completa `pytest` dentro do container backend (um arquivo por vez se aparecer o problema de event loop do R-15) e registre contagens passed/failed/error/skipped e a lista de falhas com causa provável; não corrija código fora do Toca, só proponha. No Doc 00_docs/backlog-auto/v1-amostras-ht09.md: tabela por tipo (páginas, tempo, tamanho), folha de conferência por tipo (cabeçalho/logo, rodapé e paginação, tabelas, fotos e legendas, quebras de página, tipografia) apontando o original correspondente em 01_output-context/, e as saídas literais dos comandos. Não edite 00_docs/projeto/* nem BACKLOG.md. Commit: `feat(backend): seed de demonstração e amostras dos 5 relatórios (V1-08)` com `Refs V1-08` (não commite os PDF/DOCX se 01_output-context estiver no .gitignore). Não faça push.
```

### T73 · Re-medir o desempenho dos 5 pipelines depois do url_fetcher da T28 (Vistoria Residencial com 5 % de margem)
- **Status:** done
- **Origem:** R-03
- **Papel:** arquiteto-software
- **Depende:** T17, T20, T28, T56
- **Ambiente:** docker
- **Dificuldade:** baixa
- **Toca:** 00_docs/backlog-auto/benchmark-pos-t28.md
- **Doc:** 00_docs/backlog-auto/benchmark-pos-t28.md
- **Pronto:** O Doc tem uma tabela com mediana de 3 execuções (PDF e DOCX, separados) para RFO, LTIP, RFIP, Vistoria Cautelar e Vistoria Residencial, com nº de fotos/páginas, tempo e margem sobre o limite de RNF-06. Cada tipo recebe o veredito 'atende' ou 'viola', com comando e saída reais. Se não houver ambiente Docker/Pango, o Doc diz que não mediu. Nenhum código de produção foi alterado.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md (raiz do repositório). Papel: arquiteto-software (.github/agents/arquiteto-software.agent.md). Tarefa de MEDIÇÃO e documentação; não altere código de produção nem testes. Contexto: o risco R-03 (00_docs/projeto/riscos.md) diz que a Vistoria Residencial passou no RNF-06 com só 5 % de margem na medição da T17, que a T28 estendeu o `url_fetcher` (entrega de fotos) a RFO, Cautelar e Residencial sem medir, e que o DOCX do LTIP ficou sem foto até a T56. Leia 00_docs/backlog-auto/benchmark-pipelines-finais.md (método e limite de RNF-06), 00_docs/backlog-auto/ltip-desempenho.md e a seção do RNF-06 em 00_docs/estudo-do-contexto.md. A ferramenta de medição é 04_backend/app/scripts/benchmark_relatorio_geracao.py (veja `--help`; os seeds estão em seed_benchmark_rfo.py e seed_demo.py). Passos: (1) suba o PostgreSQL com `docker compose up -d` em 05_infra/ e use o banco isolado `garra_engenharia_test` (regra 6 do BACKLOG.md), rodando `alembic upgrade head` a partir de 04_backend/; (2) repita o benchmark da T17 com o mesmo método e volume de fotos para os 5 tipos, PDF e DOCX separados, mediana de 3 execuções; (3) compare com a T17 e a T20 e destaque a Vistoria Residencial (PDF), onde a margem era 5 %; (4) registre em 00_docs/backlog-auto/benchmark-pos-t28.md: ambiente (CPU, RAM, versões), comandos, tabela de resultados, veredito por tipo e, se algum tipo violar ou ficar a menos de 20 % de margem, o gargalo provável (foto, fonte, tabela) sem corrigir. Se o Docker/Pango não estiver disponível, escreva isso no Doc em vez de inventar números. Não edite os documentos de gestão compartilhados; proponha ajuste de R-03 no próprio Doc. Commit: `docs(backlog-auto): re-medicao pos-T28 dos pipelines (R-03)` com rodapé `Refs R-03`.
```

### T76 · Reduzir o tempo do PDF da Vistoria Residencial e travar a margem com teste
- **Status:** done
- **Origem:** R-03
- **Papel:** backend
- **Depende:** T73
- **Ambiente:** docker
- **Dificuldade:** alta
- **Toca:** 04_backend/app/services/report_generator/vistoria_residencial_pipeline.py, 04_backend/tests/test_vistoria_residencial_desempenho.py, 00_docs/backlog-auto/vistoria-residencial-desempenho.md
- **Doc:** 00_docs/backlog-auto/vistoria-residencial-desempenho.md
- **Pronto:** Se o Doc da tarefa A mostrar a Vistoria Residencial (PDF) com menos de 20 % de margem sobre o limite de RNF-06, o tempo fica com pelo menos 20 % de margem, medido antes e depois com a mediana de 3 execuções, sem mudar o HTML visual (mesmo número de páginas e mesmas fotos). Há teste que trava a regressão (contagem de fotos redimensionadas/buscadas e ausência de trabalho repetido). `pytest` e `ruff check .` passam em 04_backend. Se a margem da A já for de 20 % ou mais, nada é alterado e o Doc registra por quê. Se o PostgreSQL ou o Pango não estiver disponível, o Doc diz que não rodou.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md (raiz do repositório). Papel: Engenheiro Backend (.github/agents/backend.agent.md). Contexto: R-03 em 00_docs/projeto/riscos.md. A Vistoria Residencial passou no RNF-06 com 5 % de margem (00_docs/backlog-auto/benchmark-pipelines-finais.md) e a T28 estendeu o `url_fetcher` a esse pipeline. A tarefa A mediu de novo em 00_docs/backlog-auto/benchmark-pos-t28.md: leia-o primeiro. REGRA DE PARADA: se a margem da Vistoria Residencial (PDF) já for de 20 % ou mais sobre o limite de RNF-06, não altere código; só registre no Doc novo 00_docs/backlog-auto/vistoria-residencial-desempenho.md e encerre. Caso contrário, aplique para este pipeline o método que a T20 usou no LTIP: leia 00_docs/backlog-auto/ltip-desempenho.md e o código de 04_backend/app/services/report_generator/ (vistoria_residencial_pipeline.py, ltip_pipeline.py, legenda_foto.py). Passos: (1) perfile a geração (cProfile ou tempos por etapa) com o benchmark de 04_backend/app/scripts/benchmark_relatorio_geracao.py; (2) corrija só o gargalo medido (por exemplo, reencode/redimensionamento de fotos, leitura repetida do storage, CSS ou fontes recarregados), reaproveitando o que a T20 fez no LTIP; não mude o layout nem os textos do relatório; (3) escreva 04_backend/tests/test_vistoria_residencial_desempenho.py com testes determinísticos, sem relógio, que travem a causa corrigida; (4) re-meça com a mediana de 3 execuções e registre antes e depois no Doc. Rode `pytest` e `ruff check .` a partir de 04_backend, com o banco isolado `garra_engenharia_test` (regra 6 do BACKLOG.md) e o PostgreSQL de 05_infra no ar. Não use `git add -A`; adicione só os arquivos de `toca`. Commit: `perf(backend): pdf da vistoria residencial (R-03)` com rodapé `Refs R-03`.
```

### T91 · Embutir o gabarito de sistemas prediais na imagem do backend (seed sem depender de 00_docs/)
- **Status:** done
- **Origem:** DEC-51
- **Papel:** Engenheiro Backend
- **Depende:** —
- **Ambiente:** docker
- **Dificuldade:** media
- **Toca:** 04_backend/app/scripts/rfo_gabarito_parser.py, 04_backend/app/scripts/seed_gabarito.py, 04_backend/app/scripts/exportar_gabarito_embutido.py, 04_backend/app/data/gabarito_rfo.json, 04_backend/tests/test_gabarito_embutido.py, 00_docs/backlog-auto/gabarito-embutido.md
- **Doc:** 00_docs/backlog-auto/gabarito-embutido.md
- **Pronto:** O gabarito (sistemas, subsistemas, tipos de anomalia/falha, localizações) parseado de 00_docs/convertidos/RFO_INSPECAO.md está salvo em 04_backend/app/data/gabarito_rfo.json, gerado por 04_backend/app/scripts/exportar_gabarito_embutido.py (determinístico: rodar duas vezes dá arquivo idêntico). O parser/seed usa o Markdown quando existir e cai para o JSON quando não existir, produzindo exatamente os mesmos dados. Teste novo (tests/test_gabarito_embutido.py) comprova a equivalência Markdown × JSON e o fallback com o caminho do Markdown inexistente (monkeypatch). Rodar `python -m app.scripts.seed_gabarito` continua idempotente. `pytest` e `ruff check .` passam em 04_backend (com PostgreSQL de 05_infra em localhost:5433); se o banco não estiver no ar, o Doc diz que os testes de banco não rodaram e os testes sem banco passam.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md (raiz do repositório). Papel: Engenheiro Backend (.github/agents/backend.agent.md). Contexto: DEC-51 em 00_docs/projeto/decisoes.md registra que, em ambiente novo, o gabarito de sistemas prediais precisa do arquivo 00_docs/convertidos/RFO_INSPECAO.md, que não está na imagem do backend (o Dockerfile copia só 04_backend). Hoje 04_backend/app/scripts/rfo_gabarito_parser.py lê esse Markdown por caminho relativo (RFO_INSPECAO_MD, parents[3]) e levanta FileNotFoundError se faltar; seed_gabarito.py usa o parser; seed_demo.py e ingerir_conhecimento_ia.py dependem dos nomes do gabarito (apenas leia, não edite). Passos: (1) leia o parser e o seed_gabarito.py e identifique a estrutura de dados que o parser devolve; (2) crie 04_backend/app/scripts/exportar_gabarito_embutido.py que chama o parser e grava 04_backend/app/data/gabarito_rfo.json (UTF-8, indent=2, chaves ordenadas, sem timestamps, para ser determinístico) e crie app/data/ se necessário (já dentro de 04_backend/app, portanto dentro da estrutura do monorepo; não crie pastas na raiz); (3) em rfo_gabarito_parser.py, faça a leitura preferir o Markdown e, se ele não existir, carregar o JSON embutido (caminho relativo a __file__, não ao cwd), devolvendo estrutura idêntica; registre em log qual fonte foi usada; (4) escreva tests/test_gabarito_embutido.py: equivalência Markdown × JSON, fallback com monkeypatch do caminho, determinismo do exportador (grava em tmp_path); (5) confirme que o Dockerfile (04_backend/Dockerfile) copia app/data (COPY . . já cobre; só registre, não edite) e que o .dockerignore não o exclui; (6) rode `python -m app.scripts.exportar_gabarito_embutido` e commite o JSON. Rode `pytest` e `ruff check .` a partir de 04_backend, com o PostgreSQL de 05_infra no ar (docker compose a partir de 05_infra) e o banco isolado de testes conforme a regra do BACKLOG.md. Registre no Doc: contagens do gabarito (sistemas/subsistemas/anomalias/localizações), comandos e saída dos testes. Não edite 00_docs/projeto/*.md nem 01_output-context/. Não use `git add -A`; adicione só os arquivos de `toca`. Commit: `feat(backend): gabarito embutido para seed em ambiente novo (DEC-51)` com rodapé `Refs DEC-51`. Não faça push.
```

### T92 · Cabeçalho corrido das Vistorias (Cautelar e Residencial) com logo raster em vez de SVG (DEC-54)
- **Status:** done
- **Origem:** DEC-54
- **Papel:** Engenheiro Backend
- **Depende:** —
- **Ambiente:** docker
- **Dificuldade:** alta
- **Toca:** 04_backend/app/scripts/build_vistoria_cautelar_templates.py, 04_backend/app/scripts/build_vistoria_residencial_templates.py, 04_backend/templates/vistoria_cautelar/, 04_backend/templates/vistoria_residencial/, 04_backend/tests/test_vistoria_cabecalho_raster.py, 00_docs/backlog-auto/vistoria-cabecalho-raster.md
- **Doc:** 00_docs/backlog-auto/vistoria-cabecalho-raster.md
- **Pronto:** Nos templates da Vistoria Cautelar e da Vistoria Residencial regenerados pelos scripts build_vistoria_*_templates.py, o elemento corrido do cabeçalho (position: running(cabecalho)) e o do rodapé não referenciam `image/svg+xml` nem `.svg` (usam o PNG de 04_backend/templates/assets/logo-garra.png ou raster equivalente a ≥ 300 dpi na largura usada); o SVG segue permitido só na capa. Teste determinístico novo (tests/test_vistoria_cabecalho_raster.py) trava isso nos dois templates e confirma que o PNG é a mesma arte do SVG (mesma proporção, tolerância declarada). O Doc traz a medição antes/depois do `write_pdf` da Vistoria Residencial (mediana de 3, mesmo número de páginas) e, se o WeasyPrint/Pango não estiver disponível, diz que o tempo não foi medido. Os testes existentes de templates e pipelines das duas vistorias continuam passando (`pytest` e `ruff check .` em 04_backend). Layout visual inalterado (mesmas dimensões do logo).
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md (raiz do repositório). Papel: Engenheiro Backend (.github/agents/backend.agent.md). Contexto: DEC-54 em 00_docs/projeto/decisoes.md (proposta da T76) e 00_docs/backlog-auto/vistoria-residencial-desempenho.md: o WeasyPrint 70 redesenha o logo SVG vetorizado (76 KB) em cada página do cabeçalho corrido (`position: running(cabecalho)`): ~26 s de write_pdf contra ~1,4 s sem o logo e ~2,5 s com PNG. O template da Cautelar tem o mesmo padrão e nunca foi medido. As mudanças vão nos GERADORES de template (ADR-13/DEC-25), não à mão nos .html.j2/.docx: leia 04_backend/app/scripts/build_vistoria_residencial_templates.py, build_vistoria_cautelar_templates.py, o layout extraído (templates/*/layout.json) e 04_backend/templates/assets/ (logo-garra.png, logo-garra.svg, marca.json; ver 04_backend/app/scripts/build_brand_assets.py). Passos: (1) localize como cada gerador emite o logo no cabeçalho/rodapé corrido e confirme com grep no .html.j2 gerado; (2) altere os geradores para usar o PNG (data URI ou caminho resolvido pelo mesmo mecanismo que o pipeline já usa para assets) com a mesma largura/altura; mantenha o SVG apenas na capa, se houver; (3) regenere os templates (`python -m app.scripts.build_vistoria_cautelar_templates` e `..._residencial_templates` a partir de 04_backend) e confira que layout.json e o DOCX não mudam de modo indevido (git diff); (4) escreva tests/test_vistoria_cabecalho_raster.py: nos dois .html.j2, extraia o CSS/HTML dos elementos `.cabecalho` e `.rodape` e assevere ausência de `image/svg+xml` e `.svg`; compare proporção do PNG com a do SVG (viewBox) com tolerância declarada; (5) meça antes/depois o write_pdf da Residencial com o benchmark de 04_backend/app/scripts/benchmark_relatorio_geracao.py (mediana de 3 execuções) e da Cautelar com um contexto sintético equivalente; se Pango/WeasyPrint faltar, registre que não rodou; (6) verifique (somente leitura) se RFO, LTIP e RFIP têm o mesmo padrão e liste no Doc como achado, sem editá-los. Não edite 00_docs/projeto/*.md nem 01_output-context/. Rode `pytest` e `ruff check .` a partir de 04_backend (PostgreSQL de 05_infra no ar, banco isolado de testes conforme a regra do BACKLOG.md); registre no Doc os comandos, números e a saída. Não use `git add -A`; adicione só os arquivos de `toca`. Commit: `perf(backend): logo raster no cabecalho corrido das vistorias (DEC-54)` com rodapé `Refs DEC-54`. Não faça push.
```

---

## Bloco E — IA DeepSeek: acurácia e custo da legenda (RF-15)

### T65 · Legenda IA: contexto técnico só texto, minimização de dados, enums de certeza/status, usage e retry
- **Status:** done
- **Origem:** IA-01
- **Papel:** Engenheiro Backend
- **Depende:** —
- **Ambiente:** offline
- **Dificuldade:** media
- **Toca:** 04_backend/app/services/legenda_ia/contrato.py, 04_backend/app/services/legenda_ia/contexto.py, 04_backend/app/services/legenda_ia/deepseek.py, 04_backend/app/services/legenda_ia/saneamento.py, 04_backend/app/services/foto_service.py, 04_backend/tests/test_legenda_ia_contexto.py, 04_backend/tests/test_legenda_ia_deepseek.py, 04_backend/tests/test_legenda_ia_endpoints.py, 04_backend/tests/test_seguranca_legenda_ia.py, 00_docs/backlog-auto/ia-contexto-legenda.md
- **Doc:** 00_docs/backlog-auto/ia-contexto-legenda.md
- **Pronto:** `ContextoLegenda` (legenda bruta + ocorrência + sistema + NBRs, sem dados pessoais) substitui `imagem: bytes` no protocolo `LegendaIAClient`; `foto_service.gerar_legenda_ia` não baixa a foto no modo texto; `nivel_certeza_ia` é preenchido e os valores do prompt do cliente são mapeados para os enums de `foto.py`; `LegendaIAResultado.uso` traz tokens (prompt, cache hit, cache miss, completion); retry com backoff só para 429/5xx/timeout (máx. 2); testes sem rede passam; `pytest` dos testes de legenda IA que não exigem banco e `ruff check` dos arquivos tocados limpos.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md (raiz do repositório). Papel: Engenheiro Backend (.github/agents/backend.agent.md). Contexto: leia 00_docs/ia/plano-deepseek.md (itens 1 a 3) e 00_docs/backlog-auto/v1-legenda-ia-deepseek.md (T63, que criou `DeepSeekLegendaIAClient` em app/services/legenda_ia/deepseek.py em modo texto). Decisão do usuário: API oficial DeepSeek e SÓ TEXTO (a foto não é enviada). Hoje o modelo recebe só o prompt e a legenda bruta, sem o contexto técnico da ocorrência. Implemente: (1) app/services/legenda_ia/contexto.py com dataclass `ContextoLegenda` (legenda_bruta, tipo_anomalia, sistema/ambiente, descricao da ocorrência, notas GUT e grau_risco, lista de NBRs do contrato (codigo + descricao), tipo de relatório) e `async montar_contexto(db, foto)` que lê ocorrência/inspeção/contrato pelas relações existentes (veja app/models/foto.py, ocorrencia.py, contrato_nbr.py). Minimização de dados (risco R-10): NÃO incluir nome de cliente, endereço, CPF/CNPJ, nomes de pessoas, ids ou datas; aplique também uma limpeza simples por regex de CPF/CNPJ/e-mail/telefone no texto livre. Inclua `ContextoLegenda.canonico()` (JSON ordenado, estável) para uso futuro como chave de cache. (2) Troque a assinatura do protocolo para `gerar_legenda(contexto: ContextoLegenda, prompt: str)`; mantenha o modo imagem de T63 recebendo os bytes por parâmetro opcional apenas quando `DEEPSEEK_ENVIAR_IMAGEM=true` (só então `foto_service` baixa a foto). Atualize `FakeLegendaIAClient`, `ClienteLegendaIAProtegido` (o delimitador SEG-IA-08 continua envolvendo só a legenda bruta, na mensagem user separada; o restante do contexto vai como bloco 'DADOS DA OCORRÊNCIA' na mesma mensagem user, nunca no system). (3) Mensagens: o `system` deve ser byte a byte idêntico entre chamadas com o mesmo prompt (nada variável nele) para aproveitar o cache automático de prefixo da DeepSeek; documente isso em docstring. (4) Saída: mapeie `nivel_certeza` e `status_validacao` do JSON do prompt do cliente (00_docs/cliente/prompt-lado-cliente.md, ver blocos de saída) para os valores permitidos em app/models/foto.py (NIVEIS_CERTEZA_IA; status sempre 'rascunho' na geração) e preencha `foto.nivel_certeza_ia`; valor desconhecido vira None + alerta. Adicione `LegendaIAResultado.uso` (dict com prompt_tokens, prompt_cache_hit_tokens, prompt_cache_miss_tokens, completion_tokens, quando a resposta trouxer `usage`) e `modelo`. (5) Retry no adapter: até 2 novas tentativas com backoff exponencial curto só para 429, 5xx e timeout; 4xx restantes falham na hora. Testes: crie tests/test_legenda_ia_contexto.py (montagem sem dados pessoais, canonico estável, regex de CPF/CNPJ/e-mail) e ajuste tests/test_legenda_ia_deepseek.py (system idêntico entre duas chamadas, contexto na mensagem user, mapeamento de enums, usage, retry com httpx.MockTransport) e os demais testes de legenda IA que quebrarem com a nova assinatura. Rode, a partir de 04_backend, `pytest tests/test_legenda_ia_contexto.py tests/test_legenda_ia_deepseek.py tests/test_legenda_ia_limites.py` (e os de endpoints/segurança se o banco de 05_infra estiver disponível) e `ruff check` dos arquivos tocados. Registre fatos e saídas em 00_docs/backlog-auto/ia-contexto-legenda.md. Não edite 00_docs/projeto/* nem BACKLOG.md; não altere 01_output-context/; nunca commite chaves. Commit: `feat(backend): contexto técnico só texto na legenda IA (BL-34)` com `Refs BL-34`. Não faça push.
```

### T66 · Legenda IA: prompt compacto com prefixo estável e seed versionado de `legenda_foto`
- **Status:** done
- **Origem:** IA-02
- **Papel:** Engenheiro Backend
- **Depende:** T65
- **Ambiente:** offline
- **Dificuldade:** alta
- **Toca:** 00_docs/ia/prompt-legenda-compacto.md, 04_backend/app/scripts/seed_prompt_legenda.py, 04_backend/tests/test_seed_prompt_legenda.py, 00_docs/backlog-auto/ia-prompt-compacto.md
- **Doc:** 00_docs/backlog-auto/ia-prompt-compacto.md
- **Pronto:** 00_docs/ia/prompt-legenda-compacto.md contém a versão enxuta do prompt do cliente com tabela de rastreabilidade (regra original → onde ficou ou por que saiu) e estimativa de tokens antes/depois; `python -m app.scripts.seed_prompt_legenda` cria/ativa a versão em `prompts_ia` de forma idempotente (mesmo hash não duplica); teste do seed com sessão falsa/monkeypatch passa; `ruff check` limpo.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md (raiz do repositório). Papel: Engenheiro Backend (.github/agents/backend.agent.md). Contexto: leia 00_docs/ia/plano-deepseek.md (itens 3 e 4) e 00_docs/backlog-auto/ia-contexto-legenda.md (IA-01). O prompt do cliente (00_docs/cliente/prompt-lado-cliente.md, 'PROMPT-SISTEMA UNIVERSAL', ~800 linhas) é enviado inteiro em toda chamada; os tokens de entrada dominam o custo, e na DeepSeek o prefixo repetido sai bem mais barato quando bate no cache automático. Hoje NÃO existe seed para o prompt ativo `legenda_foto` (app/services/foto_service.py usa `PROMPT_LEGENDA_IA_NOME`; serviço em app/services/prompt_ia_service.py: `criar_versao`, `ativar`, `obter_ativo`, `calcular_hash`). Faça: (1) 00_docs/ia/prompt-legenda-compacto.md com uma versão compacta do prompt (alvo: ≤35% do tamanho original) que preserve TODAS as regras normativas, proibições (não inventar causa, não afirmar o que a foto não mostra, termos técnicos preservados), o limite de 481 caracteres e o formato JSON de saída (campos `legenda_tecnica`, `nivel_certeza`, `status_validacao`, `alertas`, `pendencias`, `termos_preservados`, `necessita_revisao_profissional`), ajustado para modo SÓ TEXTO (o modelo não vê a foto; deve se apoiar na legenda bruta e nos 'DADOS DA OCORRÊNCIA'). Inclua no topo uma tabela de rastreabilidade regra original → seção do compacto (ou justificativa de remoção) e a estimativa de tokens antes/depois (caracteres/3,5 se não houver tokenizer; diga qual método usou). O texto não pode ter nada variável (datas, nomes, ids), para o prefixo ser idêntico entre chamadas. (2) app/scripts/seed_prompt_legenda.py: lê o bloco do prompt do .md (entre marcadores claros que você definir), cria nova versão de `legenda_foto` só se o hash for diferente do ativo e ativa; opção `--dry-run`; idempotente. (3) tests/test_seed_prompt_legenda.py sem banco real (monkeypatch do prompt_ia_service): extrai o bloco, não duplica com mesmo hash, ativa versão nova quando muda. Rode, a partir de 04_backend, `pytest tests/test_seed_prompt_legenda.py tests/test_prompt_ia_service.py` (o segundo se o banco de 05_infra estiver no ar) e `ruff check` dos arquivos tocados. A comparação de acurácia original vs compacto será feita no harness (IA-03) e na rodada real (IA-07); registre no Doc o que precisa ser comparado. Registre fatos e saídas em 00_docs/backlog-auto/ia-prompt-compacto.md. Não edite 00_docs/projeto/*, 00_docs/cliente/* nem BACKLOG.md. Commit: `feat(backend): prompt compacto e seed de legenda_foto (BL-34)` com `Refs BL-34`. Não faça push.
```

### T67 · Legenda IA: golden set do Relatório Fotográfico e harness de avaliação (replay/live)
- **Status:** done
- **Origem:** IA-03
- **Papel:** Engenheiro Backend
- **Depende:** T65
- **Ambiente:** offline
- **Dificuldade:** alta
- **Toca:** 04_backend/app/scripts/extrair_golden_legenda.py, 04_backend/app/scripts/avaliar_legenda_ia.py, 04_backend/tests/fixtures/ia, 04_backend/tests/test_avaliar_legenda_ia.py, 00_docs/backlog-auto/ia-avaliacao-harness.md
- **Doc:** 00_docs/backlog-auto/ia-avaliacao-harness.md
- **Pronto:** tests/fixtures/ia/golden_legenda.jsonl com ≥60 casos anonimizados extraídos do Relatório Fotográfico convertido (entrada `ContextoLegenda` + esperado); `python -m app.scripts.avaliar_legenda_ia --modo replay` roda offline sobre respostas gravadas e imprime métricas (JSON válido, ≤481 caracteres, termos preservados, acerto de grau de risco/classificação citados, distância de edição normalizada, tokens e US$ estimados); `--modo live` usa o cliente DeepSeek configurado e grava as respostas para replay; testes do harness passam; `ruff check` limpo.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md (raiz do repositório). Papel: Engenheiro Backend (.github/agents/backend.agent.md). Contexto: leia 00_docs/ia/plano-deepseek.md (item 7) e 00_docs/backlog-auto/ia-contexto-legenda.md (IA-01, `ContextoLegenda`). Sem medir não dá para saber se prompt compacto, RAG ou troca de modelo melhoram ou pioram. Fonte do golden set: 00_docs/convertidos/Relatorio_Fotografico_de_Inspecao_Predial_-_CORTINA_DAMPAREZZO_-_Versao_Final.md (por foto: situação/descrição, gravidade, urgência, tendência, pontuação GUT, classificação, tipo de anomalia, grau de risco); use também o LTIP convertido para as legendas técnicas finais quando houver correspondência. Somente leitura em 00_docs/convertidos e NUNCA leia/altere 01_output-context/. Implemente: (1) app/scripts/extrair_golden_legenda.py que gera tests/fixtures/ia/golden_legenda.jsonl (≥60 casos, variados por sistema e grau de risco): `entrada` = ContextoLegenda (legenda_bruta sintetizada a partir da situação descrita, como um técnico anotaria em campo, curta e informal) e `esperado` = legenda de referência + grau_risco + tipo_anomalia + termos que devem aparecer. Anonimize (sem nome do condomínio, endereço, pessoas). (2) app/scripts/avaliar_legenda_ia.py com `--modo replay|live`, `--prompt <arquivo|ativo>`, `--limite N`, `--saida <dir>`: no live chama o `DeepSeekLegendaIAClient` (via settings; aborta com mensagem clara sem chave) e grava as respostas brutas + usage em tests/fixtures/ia/respostas/<rotulo>.jsonl; no replay lê essas respostas. Métricas por caso e agregadas: JSON válido, tamanho ≤481, termos esperados presentes, grau de risco/tipo de anomalia coerentes, distância de edição normalizada vs referência, nivel_certeza, tokens (hit/miss/saída) e custo estimado usando preços passados por argumento ou env (`DEEPSEEK_PRECO_*` por 1M tokens; se ausentes, reporta só tokens). Saída: tabela no terminal + JSON de resumo, comparável entre rótulos (ex.: baseline vs compacto vs rag). (3) Grave um arquivo de respostas sintéticas pequeno (5 casos, feitas à mão) para o modo replay rodar no CI. (4) tests/test_avaliar_legenda_ia.py: métricas em casos controlados, replay com o arquivo sintético, live aborta sem chave. Rode, a partir de 04_backend, `pytest tests/test_avaliar_legenda_ia.py` e `ruff check` dos arquivos tocados. Registre no Doc 00_docs/backlog-auto/ia-avaliacao-harness.md: como gerar e rodar, definição de cada métrica e limitações (referência humana única, legenda bruta sintetizada). Não edite 00_docs/projeto/* nem BACKLOG.md. Commit: `feat(backend): golden set e harness de avaliação da legenda IA (BL-34)` com `Refs BL-34`. Não faça push.
```

### T68 · Legenda IA: telemetria de custo (`chamadas_ia`), cache local de resposta e resumo de uso
- **Status:** done
- **Origem:** IA-04
- **Papel:** Engenheiro Backend
- **Depende:** T65, T57, T58
- **Ambiente:** docker
- **Dificuldade:** media
- **Toca:** 04_backend/app/models/chamada_ia.py, 04_backend/app/models/__init__.py, 04_backend/alembic/versions, 04_backend/app/services/legenda_ia/telemetria.py, 04_backend/app/services/legenda_ia/__init__.py, 04_backend/app/services/foto_service.py, 04_backend/app/api/v1/ia_uso.py, 04_backend/app/main.py, 04_backend/app/core/config.py, 04_backend/.env.example, 05_infra/.env.example, 05_infra/docker-compose.yml, render.yaml, 04_backend/tests/test_legenda_ia_telemetria.py, 00_docs/backlog-auto/ia-telemetria-cache.md
- **Doc:** 00_docs/backlog-auto/ia-telemetria-cache.md
- **Pronto:** Migration nova (único head; upgrade→downgrade→upgrade validado em banco descartável) cria `chamadas_ia`; toda geração grava uma linha (sucesso, erro ou cache local) com modelo, modo, tokens hit/miss/saída, custo estimado, latência, hash do prompt e chave de cache; cache local reaproveita resultado de mesma chave dentro de `LEGENDA_IA_CACHE_TTL_H` sem chamar a API; `GET /api/v1/ia/uso` (só auditor) devolve totais por dia/modelo e taxa de cache hit; variáveis novas em .env.example, compose e render.yaml; testes no PostgreSQL de 05_infra passam; `ruff check` limpo.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md (raiz do repositório). Papel: Engenheiro Backend (.github/agents/backend.agent.md). Contexto: leia 00_docs/ia/plano-deepseek.md (item 5), 00_docs/backlog-auto/ia-contexto-legenda.md (IA-01: `LegendaIAResultado.uso`, `modelo`, `ContextoLegenda.canonico()`) e o risco R-10 (00_docs/projeto/riscos.md, custo com 150+ fotos por relatório). Hoje não há registro de tokens nem de custo, e regerar a mesma legenda chama a API de novo. Implemente: (1) Rode `alembic heads` (deve haver um único head; se não, pare e registre no Doc) e crie UMA migration com a tabela `chamadas_ia`: id uuid, criado_em, usuario_id FK null, foto_id FK null (ON DELETE SET NULL), finalidade ('legenda_foto'), provedor, modelo, modo, prompt_ia_id FK null, prompt_conteudo_hash, chave_cache (index), origem ('api'|'cache_local'), sucesso bool, erro_tipo null, tokens_prompt, tokens_cache_hit, tokens_cache_miss, tokens_saida, custo_estimado_usd Numeric(12,6) null, latencia_ms, resposta JSONB null (resultado saneado, para o cache). downgrade() obrigatório. Valide upgrade→downgrade→upgrade em banco temporário no PostgreSQL de 05_infra (localhost:5433), nunca no banco de dev. (2) app/services/legenda_ia/telemetria.py: `chave_cache(prompt_hash, modelo, contexto)` = sha256 do JSON canônico; `buscar_em_cache(db, chave, ttl)` (só sucesso, dentro do TTL); `registrar(db, ...)`; `custo(uso, precos)` com preços por 1M tokens vindos de config. (3) Config nova: `LEGENDA_IA_CACHE_TTL_H` (padrão 720), `DEEPSEEK_PRECO_ENTRADA_CACHE_HIT_USD`, `DEEPSEEK_PRECO_ENTRADA_CACHE_MISS_USD`, `DEEPSEEK_PRECO_SAIDA_USD` (por 1M tokens; padrão vazio = custo null; os valores reais serão preenchidos na tarefa humana IA-07 a partir da página oficial de preços). Repasse em 04_backend/.env.example, 05_infra/.env.example, 05_infra/docker-compose.yml e render.yaml. (4) Em `foto_service.gerar_legenda_ia`: calcula a chave, consulta o cache (hit → usa o resultado e registra origem 'cache_local', sem chamar a API); miss → chama o cliente, mede latência e registra; erro do provedor também é registrado (sem conteúdo sensível, sem chave) e relançado. O comportamento de aprovação/invalidação (DEC-42) não muda. (5) `GET /api/v1/ia/uso?de=&ate=` em NOVO app/api/v1/ia_uso.py, só auditor (`require_auditor`): totais por dia e modelo (chamadas, cache local, tokens, % de tokens com cache hit da DeepSeek, custo); inclua o router em app/main.py. (6) tests/test_legenda_ia_telemetria.py: cálculo de custo; chave estável; segunda geração idêntica vem do cache sem chamar o cliente (Fake contador); TTL expirado chama de novo; erro registrado; endpoint 403 para auxiliar. O Docker está em `C:\Program Files\Docker\Docker\resources\bin` (adicione ao PATH) e o PostgreSQL/MinIO de 05_infra devem estar no ar. Rode, a partir de 04_backend, `alembic heads`, `pytest tests/test_legenda_ia_telemetria.py tests/test_legenda_ia_endpoints.py` e `ruff check` dos arquivos tocados. Registre fatos e saídas em 00_docs/backlog-auto/ia-telemetria-cache.md. Não edite 00_docs/projeto/* nem BACKLOG.md; nunca commite chaves. Commit: `feat(backend): telemetria de custo e cache local da legenda IA (BL-34)` com `Refs BL-34`. Não faça push.
```

### T69 · Legenda IA: RAG por busca textual no Postgres (legendas aprovadas, relatórios históricos e NBRs)
- **Status:** done
- **Origem:** IA-05
- **Papel:** Engenheiro Backend
- **Depende:** T68, T66, T67
- **Ambiente:** docker
- **Dificuldade:** alta
- **Toca:** 04_backend/app/models/trecho_conhecimento_ia.py, 04_backend/app/models/__init__.py, 04_backend/alembic/versions, 04_backend/app/services/legenda_ia/recuperacao.py, 04_backend/app/services/legenda_ia/deepseek.py, 04_backend/app/services/legenda_ia/contexto.py, 04_backend/app/services/foto_service.py, 04_backend/app/core/config.py, 04_backend/.env.example, 05_infra/.env.example, 05_infra/docker-compose.yml, render.yaml, 04_backend/app/scripts/ingerir_conhecimento_ia.py, 04_backend/tests/test_legenda_ia_recuperacao.py, 00_docs/backlog-auto/ia-rag-fts.md
- **Doc:** 00_docs/backlog-auto/ia-rag-fts.md
- **Pronto:** Migration nova (único head, downgrade validado) habilita `pg_trgm`, cria `trechos_conhecimento_ia` com tsvector `portuguese` + índices GIN e índice de busca nas legendas aprovadas de `fotos`; `ingerir_conhecimento_ia` carrega trechos anonimizados de 00_docs/convertidos de forma idempotente; `recuperacao.buscar(contexto, k)` devolve few-shots (legendas aprovadas parecidas) e referências; o adapter insere os few-shots DEPOIS do system fixo; `LEGENDA_IA_RAG_ATIVO`/`LEGENDA_IA_RAG_K` controlam; harness (IA-03) rodado em replay com e sem RAG e resultado registrado; testes no PostgreSQL de 05_infra passam; `ruff check` limpo.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md (raiz do repositório). Papel: Engenheiro Backend (.github/agents/backend.agent.md). Contexto: leia 00_docs/ia/plano-deepseek.md (itens 3 e 6) e os Docs de IA-01 (ia-contexto-legenda.md), IA-02 (ia-prompt-compacto.md), IA-03 (ia-avaliacao-harness.md) e IA-04 (ia-telemetria-cache.md) em 00_docs/backlog-auto/. Objetivo: subir a acurácia sem fine-tuning, com 'fine-tuning por contexto': exemplos reais aprovados pelo auditor como few-shot e trechos de laudos anteriores como referência. A DeepSeek não tem API de embeddings, então use busca textual do PostgreSQL (FTS 'portuguese' + pg_trgm), sem pgvector e sem novo provedor. Implemente: (1) `alembic heads` (único head; senão pare e registre) e UMA migration: `CREATE EXTENSION IF NOT EXISTS pg_trgm`; tabela `trechos_conhecimento_ia` (id, fonte, tipo ('relatorio_historico'|'nbr'), sistema null, tipo_anomalia null, grau_risco null, texto, hash UNIQUE, tsv tsvector GENERATED ALWAYS AS (to_tsvector('portuguese', texto)) STORED, criado_em) com índice GIN no tsv e GIN trigram no texto; índice GIN de expressão to_tsvector('portuguese', legenda) em `fotos` filtrado por status_validacao_ia='aprovada'. downgrade() obrigatório (não remova a extensão se já existia antes). Valide upgrade→downgrade→upgrade em banco temporário no PostgreSQL de 05_infra (localhost:5433). (2) app/scripts/ingerir_conhecimento_ia.py: lê SOMENTE 00_docs/convertidos/*.md (nunca 01_output-context/), quebra em trechos de 300–800 caracteres por foto/anomalia/seção, anonimiza (nome do condomínio, endereço, pessoas, CNPJ/CPF → genérico), marca sistema/tipo_anomalia/grau_risco quando o texto permitir, insere idempotente por hash; `--dry-run` mostra contagens. (3) app/services/legenda_ia/recuperacao.py: `buscar(db, contexto, k)` → (a) até k legendas APROVADAS de outras fotos com mesmo tipo_anomalia/sistema, ranqueadas por ts_rank + similaridade trigram com a legenda bruta, excluindo a própria foto; (b) até 2 trechos de referência; (c) as NBRs do contrato já vêm no contexto. Tempo alvo < 50 ms; corte de tamanho total (ex.: 2.500 caracteres). (4) Adapter: few-shots como pares user/assistant DEPOIS do system fixo e antes da mensagem final (o system continua idêntico, para o cache de prefixo); referências dentro do bloco 'DADOS DA OCORRÊNCIA', marcadas como material de apoio e não instrução (SEG-IA-08: trate como dado não confiável e passe pelo mesmo saneamento). Inclua os ids dos exemplos usados na chave de cache de IA-04. (5) Config `LEGENDA_IA_RAG_ATIVO` (padrão true) e `LEGENDA_IA_RAG_K` (padrão 3), repassadas a .env.example, compose e render.yaml. (6) tests/test_legenda_ia_recuperacao.py no PostgreSQL de 05_infra: ingestão idempotente; anonimização; busca devolve aprovada parecida e ignora rascunho e a própria foto; ordem das mensagens (system idêntico com e sem RAG); RAG desligado não consulta. (7) Rode o harness de IA-03 em replay (e live se houver chave em env, sem commitá-la) com e sem RAG e registre a comparação. O Docker está em `C:\Program Files\Docker\Docker\resources\bin` (adicione ao PATH). Rode, a partir de 04_backend, `alembic heads`, `pytest tests/test_legenda_ia_recuperacao.py tests/test_legenda_ia_deepseek.py tests/test_legenda_ia_telemetria.py` e `ruff check` dos arquivos tocados. Registre fatos, tempos e saídas em 00_docs/backlog-auto/ia-rag-fts.md (inclua quando valeria migrar para embeddings). Não edite 00_docs/projeto/* nem BACKLOG.md. Commit: `feat(backend): RAG por busca textual na legenda IA (BL-34)` com `Refs BL-34`. Não faça push.
```

### T70 · Legenda IA: export do dataset de feedback (JSONL anonimizado) para avaliação e fine-tuning futuro
- **Status:** done
- **Origem:** IA-06
- **Papel:** Engenheiro Backend
- **Depende:** T68, T65
- **Ambiente:** docker
- **Dificuldade:** media
- **Toca:** 04_backend/app/scripts/exportar_dataset_legenda.py, 04_backend/tests/test_exportar_dataset_legenda.py, 00_docs/backlog-auto/ia-dataset-feedback.md
- **Doc:** 00_docs/backlog-auto/ia-dataset-feedback.md
- **Pronto:** `python -m app.scripts.exportar_dataset_legenda --saida <arquivo>` exporta as fotos com legenda IA aprovada em JSONL (formato chat: system/user/assistant, com o `ContextoLegenda` anonimizado e a legenda FINAL aprovada como resposta) mais um CSV de métricas (distância de edição sugerida→final, nivel_certeza, modelo, prompt); só leitura no banco; recusa caminho de saída dentro do repositório; teste no PostgreSQL de 05_infra passa; `ruff check` limpo.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md (raiz do repositório). Papel: Engenheiro Backend (.github/agents/backend.agent.md). Contexto: leia 00_docs/ia/plano-deepseek.md (seção 'Por que não há fine-tuning agora') e os Docs de IA-01 e IA-04 em 00_docs/backlog-auto/. Cada legenda IA aprovada pelo auditor gera uma tripla (contexto → sugestão → final). Esse é o único dado rotulado do sistema: serve para medir o quanto o auditor edita (sinal de acurácia em produção) e, no futuro, para fine-tuning (gate IA-08). Implemente app/scripts/exportar_dataset_legenda.py: (1) consulta SOMENTE LEITURA as fotos com status_validacao_ia='aprovada' e legenda_ia_sugerida não nula, junto com o `ContextoLegenda` montado por `montar_contexto` (IA-01, já sem dados pessoais) e o prompt usado (prompt_ia_id); (2) grava JSONL no formato chat ({messages:[system, user, assistant]}, com o system = prompt da versão usada, user = mesmo formato do adapter, assistant = JSON de saída com a legenda FINAL do auditor) e um CSV de métricas por foto: distância de edição normalizada sugestão→final, flag 'aceita sem edição', nivel_certeza_ia, modelo/prompt (via `chamadas_ia` de IA-04 quando houver), sistema, tipo_anomalia; (3) filtros `--desde`, `--ate`, `--min-registros`; (4) recusa `--saida` dentro do repositório git (dados de cliente não vão para o git) e imprime um resumo (n, % aceitas sem edição, distância média por sistema). Passe todo texto livre de novo pela limpeza de dados pessoais de IA-01. tests/test_exportar_dataset_legenda.py no PostgreSQL de 05_infra: só aprovadas entram; formato JSONL válido; métrica de edição correta; recusa saída no repositório; nenhum CPF/e-mail sobrevive. O Docker está em `C:\Program Files\Docker\Docker\resources\bin` (adicione ao PATH). Rode, a partir de 04_backend, `pytest tests/test_exportar_dataset_legenda.py` e `ruff check` dos arquivos tocados. Registre fatos e saídas em 00_docs/backlog-auto/ia-dataset-feedback.md, incluindo o formato e como ele serve tanto ao harness (IA-03) quanto a um fine-tuning futuro. Não edite 00_docs/projeto/* nem BACKLOG.md. Commit: `feat(backend): export do dataset de feedback da legenda IA (BL-34)` com `Refs BL-34`. Não faça push.
```

### T71 · Rodada real da legenda IA: chave, preços, decisão LGPD e comparação baseline × compacto × RAG × flash/pro
- **Status:** done
- **Origem:** IA-07
- **Papel:** Responsável técnico (humano)
- **Depende:** T66, T67, T68, T69
- **Ambiente:** humano
- **Dificuldade:** media
- **Toca:** 00_docs/backlog-auto/ia-deepseek-avaliacao.md
- **Doc:** 00_docs/backlog-auto/ia-deepseek-avaliacao.md
- **Pronto:** Chave DeepSeek configurada fora do git (env/secret do Render); preços oficiais vigentes preenchidos em `DEEPSEEK_PRECO_*`; decisão de uso da API oficial (dados fora do Brasil, LGPD, R-10) registrada como DEC no fechamento de lote; harness live rodado no golden set para baseline (prompt original, sem RAG), compacto e compacto+RAG, em `deepseek-flash` e `deepseek-v4-pro`; tabela com acurácia, taxa de cache hit e US$/legenda e US$/relatório (150 fotos) no Doc; configuração vencedora definida (prompt ativo, RAG k, modelo).
- **Prompt:**
```text
Tarefa humana (pode ser feita com o Claude Code interativo). Contexto: 00_docs/ia/plano-deepseek.md e os Docs de IA-01 a IA-05 em 00_docs/backlog-auto/. Passos: (1) Criar a chave na DeepSeek Platform e configurá-la só em env local e como secret no Render (`DEEPSEEK_API_KEY`, `sync: false`); nunca no git. (2) Conferir na documentação oficial (api-docs.deepseek.com) os preços vigentes por 1M tokens (entrada com cache hit, entrada com cache miss, saída) de `deepseek-flash` e `deepseek-v4-pro`, se há descontos fora de pico, se a API oferece fine-tuning e se algum modelo aceita imagem; preencher `DEEPSEEK_PRECO_*`. (3) Decisão LGPD: a API oficial processa dados fora do Brasil; com a minimização de IA-01 (sem cliente, endereço, pessoas), registrar a decisão e o risco residual — texto para DEC-XX em 00_docs/projeto/decisoes.md e atualização de R-10 em riscos.md (no fechamento de lote). (4) Ativar o prompt compacto com `python -m app.scripts.seed_prompt_legenda` num banco de teste. (5) Rodar `python -m app.scripts.avaliar_legenda_ia --modo live` nas combinações: baseline (prompt original, RAG off), compacto (RAG off), compacto + RAG k=3, compacto + RAG k=5, cada uma em `deepseek-flash` e `deepseek-v4-pro` (limite o pro a 30 casos se o custo pedir). Repetir uma rodada para medir a taxa de cache hit da DeepSeek no 2º passe. (6) Tabela no Doc: métricas de acurácia, tokens hit/miss/saída, US$/legenda e US$/relatório de 150 fotos, latência. (7) Escolher a configuração vencedora e definir a regra de escalonamento (ex.: flash por padrão; pro só quando nivel_certeza baixo ou JSON inválido), registrando se vale uma tarefa nova para implementar o escalonamento. Commit só do Doc: `docs: avaliação real da legenda IA DeepSeek (BL-34)`.
```

### T72 · Gate de fine-tuning da legenda IA (≥500 legendas aprovadas): LoRA em modelo menor × manter few-shot
- **Status:** done
- **Origem:** IA-08
- **Papel:** Responsável técnico (humano)
- **Depende:** T70, T71
- **Ambiente:** humano
- **Dificuldade:** baixa
- **Toca:** 00_docs/backlog-auto/ia-finetuning-gate.md
- **Doc:** 00_docs/backlog-auto/ia-finetuning-gate.md
- **Pronto:** Com ≥500 legendas aprovadas exportadas por IA-06, o Doc compara (dataset real, harness IA-03) a configuração vencedora de IA-07 com as opções de fine-tuning disponíveis na época (fine-tuning na própria DeepSeek, se existir; LoRA em modelo aberto menor hospedado) em acurácia, US$/relatório, latência, privacidade e esforço de operação, e termina com decisão go/no-go e, se go, as tarefas propostas.
- **Prompt:**
```text
Tarefa humana. Só iniciar quando o export de IA-06 tiver ≥500 legendas aprovadas (até lá, deixe em todo). Contexto: 00_docs/ia/plano-deepseek.md, 00_docs/backlog-auto/ia-dataset-feedback.md e ia-deepseek-avaliacao.md. Passos: (1) Exportar o dataset (IA-06) para fora do repositório e olhar a % de legendas aceitas sem edição e a distância média por sistema: se o few-shot (RAG) já entrega ≥85% aceitas com edição leve, provavelmente não compensa fine-tuning. (2) Levantar as opções da época: fine-tuning oferecido pela própria DeepSeek (se houver), LoRA/QLoRA num modelo aberto menor (ex.: destilado de 7–14B) hospedado em GPU sob demanda, e o custo de manter isso. (3) Separar 20% do dataset como teste, treinar/avaliar a opção mais promissora fora do sistema (com dados anonimizados) e comparar no harness IA-03 com a configuração vencedora de IA-07: acurácia, US$/relatório de 150 fotos, latência, privacidade (dados ficam no Brasil?) e esforço de operação. (4) Decidir go/no-go; se go, escrever no Doc as tarefas propostas (adapter do novo provedor, roteamento por sistema, retreino periódico). Commit só do Doc: `docs: gate de fine-tuning da legenda IA (BL-34)`.
```

---

## Bloco F — Validação ponta a ponta da interface (E2E)

### T74 · E2E Playwright de Edificações, Contratos e Dashboard de saúde
- **Status:** done
- **Origem:** BL-21
- **Papel:** frontend
- **Depende:** —
- **Ambiente:** docker
- **Dificuldade:** media
- **Toca:** 03_frontend/e2e/edificacoes-contratos.spec.ts, 03_frontend/e2e/dashboard.spec.ts, 00_docs/backlog-auto/e2e-edificacoes-contratos-dashboard.md
- **Doc:** 00_docs/backlog-auto/e2e-edificacoes-contratos-dashboard.md
- **Pronto:** Dois specs novos (edificacoes-contratos.spec.ts e dashboard.spec.ts) rodam com `npx playwright test` e passam contra backend e frontend locais. Cobrem listagem, busca e criação de edificação, listagem com filtros e criação de contrato, e o dashboard de saúde com dados semeados. `npm run lint` e `npm run build` passam. O Doc traz o comando e a saída reais, ou diz que não rodou e por quê. Nenhum arquivo existente em e2e/ foi alterado.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md (raiz do repositório). Papel: Engenheiro Frontend (.github/agents/frontend.agent.md). Contexto: status.md (próximos passos, item 9) pede validação ponta a ponta em navegador do frontend. Já existem specs Playwright em 03_frontend/e2e/ (rfo.spec.ts, ltip.spec.ts, relatorio.spec.ts, portal.spec.ts e helpers.ts): leia helpers.ts e rfo.spec.ts para copiar o padrão de login, de criação de dados via API e de limpeza, e 03_frontend/playwright.config.ts para a configuração. As telas estão em 03_frontend/app/edificacoes/, 03_frontend/app/contratos/ e 03_frontend/app/dashboard/. Os endpoints e as regras estão em 04_backend/app/api/ (edificacoes, contratos, dashboard) e em RF-01, RF-02, RF-07, RN-06 e RN-09 de 00_docs/estudo-do-contexto.md; o conteúdo de BL-08, BL-09 e BL-16 está em 00_docs/projeto/backlog-tarefas.md. Crie, SEM alterar os specs existentes: (1) 03_frontend/e2e/edificacoes-contratos.spec.ts: login como auditor, listar e buscar edificações, criar uma edificação pela UI e vê-la na lista; listar contratos, aplicar filtros e criar um contrato com mais de uma empresa executora e NBRs (RN-06/RN-09); (2) 03_frontend/e2e/dashboard.spec.ts: com uma edificação e ocorrências semeadas via API ou `seed_demo` (04_backend/app/scripts/seed_demo.py, dados com prefixo DEMO), abrir o dashboard de saúde e checar que os indicadores por sistema predial aparecem e batem com os dados criados. Use nomes únicos por execução e limpe o que criar. Para rodar: PostgreSQL de 05_infra (`docker compose up -d` em 05_infra/), `alembic upgrade head` e backend a partir de 04_backend/, depois `npx playwright test` a partir de 03_frontend/. Se algum passo falhar por ambiente, registre no Doc em vez de inventar o resultado; se achar bug real na UI, não corrija: descreva-o no Doc. Rode `npm run lint` e `npm run build` em 03_frontend. Registre no Doc o que foi coberto, os comandos e as saídas. Commit: `test(frontend): e2e de edificacoes, contratos e dashboard (BL-21)` com rodapé `Refs BL-21`.
```

### T75 · E2E Playwright de Visitas, Ocorrências e upload de fotos pela UI
- **Status:** done
- **Origem:** BL-21
- **Papel:** frontend
- **Depende:** T74
- **Ambiente:** docker
- **Dificuldade:** media
- **Toca:** 03_frontend/e2e/visitas-ocorrencias.spec.ts, 03_frontend/e2e/fotos-upload.spec.ts, 00_docs/backlog-auto/e2e-visitas-ocorrencias-fotos.md
- **Doc:** 00_docs/backlog-auto/e2e-visitas-ocorrencias-fotos.md
- **Pronto:** Os specs visitas-ocorrencias.spec.ts e fotos-upload.spec.ts passam com `npx playwright test`. Cobrem criar visita (e a rejeição de data futura e de segunda visita no mesmo dia, DEC-38), criar ocorrência com sistema/subsistema/localização/classificação, e subir foto por upload manual e por colagem, vinculada à visita. `npm run lint` e `npm run build` passam. O Doc registra a saída real, ou diz que não rodou e por quê. Nenhum spec existente foi alterado.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md (raiz do repositório). Papel: Engenheiro Frontend (.github/agents/frontend.agent.md). Contexto: status.md (próximos passos, item 9) pede re-testar em navegador os frontends de Visitas (BL-10), Upload de fotos (BL-11) e Ocorrências (BL-14), cujas regras mudaram nas tarefas T19, T21 e T08 (data futura e segunda visita no mesmo dia rejeitadas, `storage_key` controlada pelo servidor, enums de ocorrência). Leia 03_frontend/e2e/helpers.ts, rfo.spec.ts e foto-origem.spec.ts (padrão de login, criação de dados via API, mock de upload), e o spec 03_frontend/e2e/edificacoes-contratos.spec.ts da tarefa B, que você pode reaproveitar. As telas estão em 03_frontend/app/inspecoes/[id]/ (subpastas visitas/, ocorrencias/) e os endpoints em 04_backend/app/api/ (visitas, ocorrencias, fotos). Regras: 00_docs/backlog-auto/visitas-correcoes.md, ocorrencias-correcoes.md e fotos-correcoes.md, e RF-03, RF-04, RF-05, RN-01 a RN-05 de 00_docs/estudo-do-contexto.md. Crie, sem alterar os specs existentes: (1) 03_frontend/e2e/visitas-ocorrencias.spec.ts: criar visita pela UI; tentar data futura e segunda visita no mesmo dia e checar a mensagem de erro; criar ocorrência com sistema, subsistema, localização e classificação; editar e confirmar; (2) 03_frontend/e2e/fotos-upload.spec.ts: subir uma imagem pequena por upload manual e outra por colagem (clipboard) vinculada à visita, e confirmar que aparecem na lista (use imagem gerada no teste; não use arquivos de 01_output-context/). Use nomes únicos por execução e limpe o que criar. Rode o PostgreSQL de 05_infra (`docker compose up -d` em 05_infra/), `alembic upgrade head` e o backend a partir de 04_backend/, e `npx playwright test` a partir de 03_frontend/. Se algum passo falhar por ambiente, registre no Doc; se achar bug real, descreva-o sem corrigir. Rode `npm run lint` e `npm run build` em 03_frontend. Commit: `test(frontend): e2e de visitas, ocorrencias e upload de fotos (BL-21)` com rodapé `Refs BL-21`.
```

### T77 · PWA: Service Worker de cache só de leitura e página de fallback sem rede (DEC-26)
- **Status:** done
- **Origem:** DEC-26
- **Papel:** Engenheiro Frontend
- **Depende:** —
- **Ambiente:** offline
- **Dificuldade:** media
- **Toca:** 03_frontend/public/sw.js, 03_frontend/public/offline.html, 03_frontend/components/sw-register.tsx, 03_frontend/lib/sw-cache.ts, 03_frontend/lib/sw-cache.test.ts, 03_frontend/app/layout.tsx, 00_docs/backlog-auto/pwa-service-worker.md
- **Doc:** 00_docs/backlog-auto/pwa-service-worker.md
- **Pronto:** Existe 03_frontend/public/sw.js, registrado em produção por um componente cliente, que só cacheia GET de leitura de baixa volatilidade (gabarito de dados mestre e contratos em andamento) e responde offline.html para navegação sem rede. O SW nunca intercepta nem cacheia POST/PUT/PATCH/DELETE, nem /auth/*, nem /portal/*, nem URLs de fotos ou relatórios. A lógica de decisão de cache fica em lib/sw-cache.ts e tem teste unitário. `npm run lint` e `npm run build` em 03_frontend passam. O Doc 00_docs/backlog-auto/pwa-service-worker.md registra as rotas cacheadas, a estratégia, a invalidação e as limitações.
- **Prompt:**
```text
Tarefa: implementar o Service Worker da PWA conforme DEC-26 (00_docs/projeto/decisoes.md, seção DEC-26) e ADR-03/ADR-15 de 00_docs/arquitetura.md. Leia só essas seções. Siga as regras do projeto: frontend em 03_frontend/, comandos npm rodam a partir de 03_frontend/. Não crie pastas na raiz. Papel: Engenheiro Frontend; siga .github/agents/ (frontend) se existir. Não altere regras de negócio nem o visual existente.

Contexto: o app é Next.js (App Router) PWA online-first. O cliente confirmou que operação offline NÃO é necessária (DEC-26). O que está decidido: o Service Worker cacheia SOMENTE dados de leitura de baixa volatilidade (gabarito de sistemas prediais/dados mestre e contratos em andamento); escritas (visita, ocorrência, foto) exigem conectividade e falham com erro explícito, SEM fila local. Hoje 03_frontend/public/ tem só manifest.json, icon.svg e brand/; não há service worker.

Passos:
1. Antes de codar, leia 03_frontend/app/layout.tsx, a camada de chamadas à API em 03_frontend/lib/ e 03_frontend/public/manifest.json para achar as URLs reais dos endpoints de dados mestre e contratos (confira também 04_backend/app/api/v1/dados_mestre.py e contratos.py). Não invente rotas.
2. Crie 03_frontend/lib/sw-cache.ts com funções puras (sem acesso a `self`/DOM) que decidem: (a) se uma requisição é cacheável (método GET, URL em lista allowlist de leitura); (b) nunca cacheável: qualquer método diferente de GET, /auth/*, /portal/*, URLs de fotos/downloads de relatório e qualquer resposta com cabeçalho Authorization sensível a outro usuário (se o cache de contratos depender do token, use cache de curta duração e limpe-o no logout; documente a escolha). Crie sw-cache.test.ts cobrindo essas regras (use o runner já configurado no projeto; se não houver runner unitário no 03_frontend, adicione o teste na forma que o projeto já usa ou cubra a lógica com um script verificado por `npm run build`, e registre isso no Doc).
3. Crie 03_frontend/public/sw.js (JavaScript simples, sem dependência nova) com: versão de cache explícita e limpeza de caches antigos no activate; stale-while-revalidate para a allowlist; para navegações sem rede, responder 03_frontend/public/offline.html (página simples em português do Brasil, com a identidade visual mínima já usada e a mensagem de que o registro de dados exige conexão); para qualquer não-GET, não interceptar (deixar a rede falhar com o erro nativo). Como sw.js não pode importar TypeScript, mantenha a allowlist duplicada em constante no sw.js e referencie no Doc que lib/sw-cache.ts é a fonte de teste; alternativamente gere o sw.js a partir do mesmo módulo se houver mecanismo simples sem nova dependência. Não adicione next-pwa/workbox/serwist sem necessidade.
4. Crie 03_frontend/components/sw-register.tsx (client component) que registra /sw.js apenas quando `process.env.NODE_ENV === 'production'` e `'serviceWorker' in navigator`, e desregistra/limpa os caches no logout se o projeto tiver ponto único de logout. Inclua o componente em app/layout.tsx com alteração mínima (NÃO mexa em theme-provider.tsx nem theme-toggle.tsx, que são de outra frente).
5. Verifique em 03_frontend: `npm run lint` e `npm run build`. Se não puder abrir o navegador, diga isso; não invente teste manual.
6. Escreva o resultado em 00_docs/backlog-auto/pwa-service-worker.md: rotas cacheadas, estratégia, versionamento/invalidação, o que NÃO é cacheado e por quê (privacidade/portal), limitações conhecidas e qualquer decisão proposta (não edite decisoes.md, status.md, backlog-tarefas.md, backlog-kanban.md nem riscos.md).

Commit em Conventional Commits, ex.: `feat(frontend): service worker de leitura e fallback offline (DEC-26)` com rodapé `Refs DEC-26`. Nunca commite .env/chaves; nunca faça push nem toque em main_back, main_front, staging_back, staging_front. Siga a "Regra de pronto" do BACKLOG.md.
```

### T78 · E2E Playwright: escrita sem rede falha com erro explícito e sem fila local (DEC-26)
- **Status:** done
- **Origem:** DEC-26
- **Papel:** Engenheiro Frontend
- **Depende:** T77
- **Ambiente:** docker
- **Dificuldade:** media
- **Toca:** 03_frontend/e2e/offline-dec26.spec.ts, 00_docs/backlog-auto/e2e-offline-dec26.md
- **Doc:** 00_docs/backlog-auto/e2e-offline-dec26.md
- **Pronto:** Existe o spec 03_frontend/e2e/offline-dec26.spec.ts (ou na pasta de E2E já usada pelo projeto; confirme o caminho real) que, com `context.setOffline(true)`: (1) mostra a página offline em navegação sem cache; (2) tenta criar uma visita, ocorrência ou vincular foto e verifica que a UI exibe erro explícito e que nada é gravado em IndexedDB/localStorage como fila de escrita; (3) ao voltar online, a mesma ação funciona. O spec roda contra o stack local (PostgreSQL 05_infra, backend e frontend) e o resultado, ou o motivo de não ter rodado, fica registrado no Doc 00_docs/backlog-auto/e2e-offline-dec26.md.
- **Prompt:**
```text
Tarefa: cobrir com E2E Playwright o comportamento online-first decidido em DEC-26 (00_docs/projeto/decisoes.md, seção DEC-26): escritas exigem conectividade e falham com erro explícito, sem fila local. Pré-requisito: a tarefa A (Service Worker em 03_frontend/public/sw.js e offline.html) já está integrada; confirme que os arquivos existem antes de começar e, se não existirem, pare e registre no Doc.

Siga as regras do projeto: npm a partir de 03_frontend/; o backend precisa do PostgreSQL de 05_infra/docker-compose.yml (localhost:5433), com docker compose rodando a partir de 05_infra/. Se o PostgreSQL ou o stack não subir, registre que não rodou em vez de inventar resultado. Não crie pastas na raiz.

Passo a passo: (1) Descubra como os E2E existentes (tarefas T74/T75, Playwright) estão organizados: pasta de specs, playwright.config, fixtures de login, seed e comando de execução em 03_frontend/package.json; reutilize as fixtures e o seed, não duplique. Se T74/T75 ainda não estiverem no repositório, crie o mínimo de configuração necessário e registre isso. (2) Escreva o spec offline-dec26: login online como `auditor`; abrir uma tela de leitura com dados cacheáveis para popular o cache do SW (a navegação precisa ocorrer em build de produção `npm run build && npm run start`, porque o SW só registra em produção — configure o webServer do Playwright de acordo, sem alterar o config usado pelos outros specs, usando um projeto/config separado se preciso); `context.setOffline(true)`; navegar para uma rota não cacheada e verificar a página offline.html; tentar criar uma ocorrência ou visita e verificar a mensagem de erro visível ao usuário; verificar via `page.evaluate` que não há fila de escrita local (IndexedDB vazio de filas, localStorage/sessionStorage sem payload pendente); `setOffline(false)` e repetir a ação com sucesso. (3) Se a UI não mostrar erro explícito ao falhar a escrita por falta de rede, NÃO corrija código de produção além do mínimo de apresentação do erro; registre a lacuna no Doc como proposta. (4) Rode `npx playwright test <spec>` e `npm run lint` em 03_frontend. (5) Registre no Doc 00_docs/backlog-auto/e2e-offline-dec26.md: o que foi testado, comandos, saída resumida, o que não rodou e por quê, lacunas encontradas. Não edite decisoes.md, status.md, backlog-tarefas.md, backlog-kanban.md nem riscos.md.

Commit em Conventional Commits: `test(frontend): e2e de escrita sem rede (DEC-26)` com rodapé `Refs DEC-26`. Nunca commite .env/chaves; nunca faça push nem toque em main_back, main_front, staging_back, staging_front. Siga a "Regra de pronto" do BACKLOG.md.
```

### T90 · E2E do Service Worker no export estático com basePath do Pages (fecha R-22)
- **Status:** done
- **Origem:** R-22
- **Papel:** Engenheiro Frontend
- **Depende:** T77, T83
- **Ambiente:** offline
- **Dificuldade:** media
- **Toca:** 03_frontend/e2e/sw-basepath.spec.ts, 03_frontend/playwright.sw.config.ts, 00_docs/backlog-auto/sw-e2e-basepath.md
- **Doc:** 00_docs/backlog-auto/sw-e2e-basepath.md
- **Pronto:** Existe spec Playwright que serve o export estático (build de produção com NEXT_PUBLIC_BASE_PATH=/garra-engenharia) e comprova em Chromium real: (1) o SW registra com scope /garra-engenharia/; (2) uma rota da allowlist de leitura (/sistemas-prediais, com API mockada por page.route) é servida do cache dentro do TTL; (3) depois do logout o cache de dados é apagado (DEC-56 P3); (4) rotas /auth/*, /portal/* e não-GET nunca são cacheadas. `npm run lint` e `npm run build` passam em 03_frontend, e o Doc traz a saída do Playwright (passed/failed) e o estado de R-22 (resolvido ou o que falta). Se o Chromium do Playwright não estiver instalado, o Doc diz que não rodou.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md (raiz do repositório). Papel: Engenheiro Frontend (.github/agents/frontend.agent.md). Contexto: R-22 em 00_docs/projeto/riscos.md diz que o Service Worker (T77, DEC-56) nunca foi exercitado em navegador real e que o registro precisava respeitar o basePath do GitHub Pages (DEC-55). O registro já usa withBasePath (03_frontend/components/sw-register.tsx), mas falta a prova em navegador. Leia primeiro: 00_docs/backlog-auto/pwa-service-worker.md, 03_frontend/public/sw.js, 03_frontend/lib/sw-cache.ts, 03_frontend/next.config.mjs, 03_frontend/playwright.config.ts e playwright.modo-leitura.config.ts (modelo de config com servidor estático) e e2e/modo-leitura-dec57.spec.ts. Passos: (1) crie 03_frontend/playwright.sw.config.ts que builda com `NEXT_PUBLIC_BASE_PATH=/garra-engenharia` e serve a pasta `out/` sob o prefixo /garra-engenharia/ (por exemplo, com um servidor estático mínimo em Node ou `npx serve` já instalado; não adicione dependência nova sem necessidade, e se adicionar, justifique no Doc); o SW só registra com NODE_ENV=production; (2) escreva 03_frontend/e2e/sw-basepath.spec.ts cobrindo os 4 pontos do critério de pronto, mockando a API com page.route e usando um token falso no localStorage; para (3) dispare o logout pelo fluxo real da UI ou chamando clearAuthToken; (4) rode o spec, corrija só o que o teste revelar de defeito real em sw-register.tsx/sw.js se for pequeno (se for maior, registre como proposta no Doc e marque o teste como test.fixme com motivo). NÃO edite arquivos fora de `toca`, exceto o que o item (4) exigir, e nesse caso liste no Doc. Não mexa nos specs de T78 (escrita sem rede) se existirem. Rode `npm run lint` e `npm run build` a partir de 03_frontend. Registre no Doc: comandos, saída, o que foi provado e o novo estado de R-22. Não use `git add -A`; adicione só os arquivos tocados. Commit: `test(frontend): e2e do service worker com basePath (R-22)` com rodapé `Refs R-22`. Não faça push.
```

### T101 · Reabrir E2E da DEC-26: escrita sem rede falha com erro explícito
- **Status:** done
- **Origem:** T78
- **Papel:** Engenheiro Frontend
- **Depende:** —
- **Ambiente:** docker
- **Dificuldade:** media
- **Toca:** 03_frontend/e2e/offline-dec26.spec.ts, 03_frontend/playwright.offline.config.ts, 00_docs/backlog-auto/e2e-offline-dec26.md
- **Doc:** 00_docs/backlog-auto/e2e-offline-dec26.md
- **Pronto:** Existe 03_frontend/e2e/offline-dec26.spec.ts que, contra `next build && next start` com Service Worker ativo, prova: (a) leituras da allowlist continuam dentro do TTL sem rede; (b) uma gravação sem rede mostra erro explícito e nada fica em fila local; o spec foi executado e a saída consta no Doc, ou o Doc diz explicitamente que não rodou e por quê.
- **Prompt:**
```text
Contexto: a T78 foi marcada `done` mas o Doc 00_docs/backlog-auto/e2e-offline-dec26.md registra que NÃO foi executada e nenhum spec offline existe em 03_frontend/e2e/ (a branch do worktree não continha o Service Worker da T77). Agora o Service Worker existe em main: 03_frontend/public/sw.js, 03_frontend/lib/sw-cache.ts, offline.html (DEC-26, DEC-56). Tarefa: leia o Doc antigo, 03_frontend/playwright.config.ts e os specs atuais (ex.: sw-basepath.spec.ts, helpers.ts) e crie 03_frontend/e2e/offline-dec26.spec.ts com uma configuração separada 03_frontend/playwright.offline.config.ts que sobe `npm run build && npm run start` (o SW só vale em build de produção; não altere o playwright.config.ts existente). Cenários: (1) após carregar dados mestre/contratos online, `context.setOffline(true)` e a leitura dentro do TTL segue funcionando e fora da allowlist cai no `offline.html`; (2) com a rede cortada, uma gravação (ex.: criar edificação) exibe erro explícito ao usuário e nenhum mecanismo de fila é criado (verifique que `localStorage`/IndexedDB não guardam requisição pendente). Mocke a API com `page.route` se o backend não estiver disponível, e diga no Doc o que foi mockado. Se não conseguir executar o Playwright aqui (navegadores ausentes), registre isso sem inventar resultado. Rode `npm run lint` e `npm run build` em 03_frontend. Atualize o Doc existente (substitua o status de 'não executada' pelo real). Siga a 'Regra de pronto' do BACKLOG.md. Não edite os documentos de gestão em 00_docs/projeto/ nem o BACKLOG.md. Commit: `test(frontend): E2E offline da DEC-26 com Service Worker (R-22)` com `Refs T78`. Não faça push.
```

## Bloco G — Sair do Render: backend no PC, front no Pages público, snapshot cifrado (DEC-57)

Contexto comum (DEC-57 em 00_docs/projeto/decisoes.md): o repositório `garra-engenharia` é **público** (desde 2026-11-17). O site estático continua no GitHub Pages do próprio repositório (`https://rafaelroriz-age.github.io/garra-engenharia/`, `deploy-pages.yml` com `GITHUB_TOKEN`), e a branch órfã `snapshot` do mesmo repositório guarda com `api.json` (URL atual do túnel + heartbeat) e `snapshot.enc` (dados de leitura da equipe cifrados com AES-256-GCM). Backend FastAPI, PostgreSQL e arquivos rodam no PC do dono, com dados fora do git; sobe sozinho no logon do Windows e é exposto por `cloudflared tunnel --url` (URL aleatória por boot, publicada em `api.json`). PC desligado → site abre em modo leitura com o snapshot; nenhuma gravação.

### T79 · Runtime local de produção no PC sem Docker (PostgreSQL portátil + venv + .env)
- **Status:** done
- **Origem:** DEC-57
- **Papel:** devops
- **Depende:** —
- **Ambiente:** offline
- **Dificuldade:** alta
- **Toca:** 05_infra/local/, .gitignore, 00_docs/backlog-auto/runtime-local-pc.md
- **Doc:** 00_docs/backlog-auto/runtime-local-pc.md
- **Pronto:** Existe `05_infra/local/garra-local.ps1` (Windows PowerShell 5.1) com os subcomandos `setup`, `start`, `stop`, `status` e `backup`, e `05_infra/local/.env.example`. `setup` baixa o PostgreSQL 16 portátil (zip de binários EDB) para `05_infra/local/bin/`, faz `initdb` em `%LOCALAPPDATA%\garra\pgdata` (porta 5434, fora do OneDrive), cria o banco `garra_producao`, cria o venv `04_backend/.venv-prod` e instala `requirements.txt`. `start` sobe Postgres e uvicorn (porta 8000, sem reload), roda `alembic upgrade head` e os seeds idempotentes; `stop` encerra limpo; `status` mostra o que está no ar; `backup` faz `pg_dump -Fc` para `05_infra/local/backups/` com retenção de 14. Os dados (bin, backups, storage, logs, run, .env) estão no .gitignore. O Doc traz os comandos realmente executados e a saída, ou diz o que não rodou e por quê.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md. Papel: devops (.github/agents/devops.agent.md). Leia DEC-57 em 00_docs/projeto/decisoes.md e o contexto do Bloco G do BACKLOG.md. Objetivo: rodar o backend de produção no PC Windows do dono, sem Docker e sem Render, com os dados fora do git.

Leia antes: 04_backend/app/core/config.py, 04_backend/.env.example, 05_infra/.env.render.example, 05_infra/README.md, os scripts de seed em 04_backend/app/scripts/ (descubra quais são idempotentes e a ordem usada em .github/workflows/ci.yml ou na documentação) e o Dockerfile.render do backend (dependências de sistema do WeasyPrint: no Windows confira se GTK/Pango é necessário e como o projeto resolve isso hoje em dev; se precisar de instalação extra, deixe o passo em `setup` e no Doc).

Crie em 05_infra/local/ (não crie pastas na raiz):
1. garra-local.ps1 compatível com Windows PowerShell 5.1 (sem `&&`, sem `??`), com subcomandos setup|start|stop|status|backup e uma função de log em 05_infra/local/logs/garra-local.log. Caminhos sempre relativos ao próprio script ($PSScriptRoot), pois o repo fica numa pasta com espaços e acentos.
2. setup: baixa o zip de binários do PostgreSQL 16 para Windows x64 (EDB) para 05_infra/local/bin/pgsql (pule se já existir), initdb em $env:LOCALAPPDATA\garra\pgdata com auth scram e senha vinda do .env, porta 5434, cria o banco garra_producao; cria 04_backend/.venv-prod e instala 04_backend/requirements.txt; copia .env.example para .env se não existir e gera JWT_SECRET_KEY e senhas aleatórias só se ausentes (nunca sobrescreva valores existentes; SNAPSHOT_SENHA fica vazia para o dono definir, HT-14).
3. start: pg_ctl start (se não estiver no ar), espera aceitar conexão, `alembic upgrade head` e seeds idempotentes com o venv-prod e as variáveis do .env local (POSTGRES_HOST=localhost, POSTGRES_PORT=5434, POSTGRES_DB=garra_producao, BACKEND_CORS_ORIGINS incluindo https://rafaelroriz-age.github.io e http://localhost:3000, RUN_MIGRATIONS_ON_STARTUP=false, STORAGE_PROVEDOR=local, STORAGE_LOCAL_DIR=05_infra/local/storage absoluto), depois uvicorn app.main:app --host 127.0.0.1 --port 8000 em segundo plano, gravando o PID em 05_infra/local/run/. Saída do uvicorn em logs/.
4. stop: encerra uvicorn pelo PID e pg_ctl stop -m fast. status: mostra Postgres/uvicorn e GET http://127.0.0.1:8000/health.
5. backup: pg_dump -Fc para 05_infra/local/backups/garra-AAAAMMDD-HHmm.dump e apaga os mais antigos que os 14 mais recentes.
6. 05_infra/local/.env.example documentado (sem segredos reais) e entradas no .gitignore: 05_infra/local/bin/, backups/, storage/, logs/, run/ (o padrão `.env` já cobre o .env, confirme).

Não use o banco garra_engenharia de dev nem o Docker. Não toque no Render. Rode de verdade `setup`, `start`, `status`, `backup` e `stop` no PC (o banco garra_producao é novo e vazio, é seguro); se o download ou algo falhar, registre no Doc em vez de inventar. Registre no Doc: arquitetura, variáveis, comandos, saídas e limitações. Commit: `feat(infra): runtime local de producao no PC sem Docker (DEC-57)` com rodapé `Refs DEC-57`.
```

### T80 · Storage em disco local com download assinado pelo próprio FastAPI
- **Status:** done
- **Origem:** DEC-57
- **Papel:** backend
- **Depende:** —
- **Ambiente:** docker
- **Dificuldade:** media
- **Toca:** 04_backend/app/services/storage/, 04_backend/app/core/config.py, 04_backend/app/api/v1/arquivos.py, 04_backend/app/main.py, 04_backend/.env.example, 04_backend/tests/test_storage_local.py, 00_docs/backlog-auto/storage-local.md
- **Doc:** 00_docs/backlog-auto/storage-local.md
- **Pronto:** Existe `LocalStorageClient` que implementa a mesma interface de `app/services/storage/base.py` gravando em `STORAGE_LOCAL_DIR`, selecionado por `STORAGE_PROVEDOR=local` (padrão continua `s3`, nada muda para quem usa MinIO). `generate_presigned_url` devolve URL absoluta para `GET /api/v1/arquivos/{token}` com token HMAC (chave derivada de JWT_SECRET_KEY) contendo a chave e a expiração; o endpoint serve o arquivo com Content-Type correto, recusa token adulterado/vencido (403) e path traversal. Testes novos passam; `pytest` e `ruff check .` verdes.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md. Papel: backend (.github/agents/backend.agent.md). Leia DEC-57 em 00_docs/projeto/decisoes.md. Com o backend saindo do Render para o PC do dono (exposto por um único túnel cloudflared), não haverá MinIO/S3: fotos, documentos e relatórios gerados vão para disco local fora do git.

Leia 04_backend/app/services/storage/base.py, s3_client.py (incl. get_storage_client), app/core/config.py e todos os usos de generate_presigned_url (grep) para entender como as URLs de download chegam ao front. Implemente:
1. app/services/storage/local_client.py: LocalStorageClient(StorageClient) com upload/download/exists/delete/list_keys/list_objects/generate_presigned_url, mesma validação de chave do S3 (reuse _validate_key ou extraia para base), gravação atômica (arquivo temporário + replace), proteção contra path traversal (a chave resolvida tem de ficar dentro de STORAGE_LOCAL_DIR). Guarde o content-type num arquivo lateral `.meta.json` ou infira por extensão; documente a escolha.
2. Config: STORAGE_PROVEDOR (s3|local, padrão s3), STORAGE_LOCAL_DIR, PUBLIC_BASE_URL (URL pública do backend para montar a URL absoluta). O túnel muda a cada boot: prefira montar a URL a partir do request (cabeçalhos X-Forwarded-Host/Proto do cloudflared) quando PUBLIC_BASE_URL estiver vazia — veja o que é viável dado onde generate_presigned_url é chamado (ou devolva URL relativa à API e documente o ajuste necessário no front). get_storage_client escolhe pelo provedor.
3. app/api/v1/arquivos.py: GET /api/v1/arquivos/{token} sem autenticação JWT (o token assinado é a autorização, como uma presigned URL), HMAC-SHA256 com chave derivada de JWT_SECRET_KEY, expiração respeitada, 403 para token inválido/vencido, 404 se não existir; FileResponse com Content-Disposition coerente com o que o S3 devolve hoje. Registre o router em app/main.py.
4. Variáveis novas em 04_backend/.env.example. Testes em tests/test_storage_local.py (tmp_path): ida e volta de upload/download, exists/delete/list, traversal recusado, URL assinada válida baixa, adulterada e vencida dão 403.
Rode pytest (banco garra_engenharia_test, Regra de pronto item 6) e ruff. Doc com decisões, variáveis e saídas. Commit: `feat(backend): storage em disco local com download assinado (DEC-57)` com rodapé `Refs DEC-57`.
```

### T81 · Gerador de snapshot cifrado da leitura da equipe
- **Status:** done
- **Origem:** DEC-57
- **Papel:** backend
- **Depende:** —
- **Ambiente:** docker
- **Dificuldade:** alta
- **Toca:** 04_backend/app/scripts/gerar_snapshot.py, 04_backend/app/services/snapshot/, 04_backend/tests/test_snapshot.py, 04_backend/requirements.txt, 00_docs/backlog-auto/snapshot-cifrado.md
- **Doc:** 00_docs/backlog-auto/snapshot-cifrado.md
- **Pronto:** `python -m app.scripts.gerar_snapshot --saida <arq>` gera um arquivo JSON `{v:1, kdf:{alg:"PBKDF2-SHA256", iter:600000, salt}, iv, ct, gerado_em}` com AES-256-GCM cuja chave vem de `SNAPSHOT_SENHA`. O texto claro é `{gerado_em, rotas: {"/api/v1/...?query": corpo_json}}` com as respostas reais de todos os GETs de leitura da equipe (listas e detalhes), obtidas em processo pelo app FastAPI (httpx ASGITransport) autenticado como um auditor de serviço. Fotos, documentos, downloads de relatório, /auth/login e /portal ficam fora. Há uma função de decifrar usada no teste e um vetor de teste (senha, salt, iv, texto) gravado no Doc para o front validar a mesma cifra. Testes verdes.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md. Papel: backend. Leia DEC-57 em 00_docs/projeto/decisoes.md. Com o PC desligado, o site estático precisa mostrar os dados em modo leitura a partir de um snapshot cifrado público. Esta tarefa gera o snapshot; o front (T83) decifra com WebCrypto.

1. Leia app/main.py, app/api/v1/*.py (todos os GET) e 03_frontend/lib/api-client.ts + as telas em 03_frontend/app/ para saber exatamente quais URLs GET (com as query strings padrão de paginação/filtro) o front chama ao navegar. Monte a lista de rotas a capturar: dados mestre/gabarito, edificações (lista + detalhe + dashboard), contratos (lista + detalhe), responsáveis, inspeções (detalhe), visitas (detalhe + mão de obra + medições), ocorrências (lista por inspeção + detalhe), conteúdo de relatórios por tipo, lista de relatórios, /auth/me do auditor, /ia/uso. Descubra os IDs iterando as listas. Não inclua bytes de fotos/documentos/relatórios nem /portal.
2. app/services/snapshot/: coletor que usa httpx.AsyncClient(transport=ASGITransport(app)) com token JWT de um usuário auditor de serviço (crie-o se não existir, e-mail configurável `SNAPSHOT_USUARIO_EMAIL`, senha aleatória; não altere outros usuários). Chave da rota = path+query exatamente como o front chamará (sem host). Cifrador: PBKDF2-HMAC-SHA256 600000 iterações, salt 16 bytes, AES-256-GCM iv 12 bytes, texto gzip+JSON UTF-8 (o front usará DecompressionStream). Use a lib `cryptography` (adicione a requirements.txt se faltar).
3. app/scripts/gerar_snapshot.py com --saida e --somente-se-mudou (compara hash do texto claro, sem o gerado_em, com um .sha256 ao lado e sai com código 3 se nada mudou).
4. tests/test_snapshot.py: cifrar/decifrar ida e volta, senha errada falha, a coleta contra o banco de teste com dados semeados contém rotas esperadas e não contém /portal nem downloads. Gere um vetor de teste fixo e grave no Doc.
pytest (garra_engenharia_test) e ruff verdes. Doc com formato do arquivo, lista de rotas, tamanho típico e vetor de teste. Commit: `feat(backend): snapshot cifrado da leitura da equipe (DEC-57)` com rodapé `Refs DEC-57`.
```

### T82 · Agente de inicialização: túnel, publicação de api.json/snapshot e tarefa agendada
- **Status:** done
- **Origem:** DEC-57
- **Papel:** devops
- **Depende:** T79, T81
- **Ambiente:** offline
- **Dificuldade:** media
- **Toca:** 05_infra/local/garra-local.ps1, 05_infra/local/garra-agente.ps1, 05_infra/local/.env.example, 00_docs/backlog-auto/agente-inicializacao.md
- **Doc:** 00_docs/backlog-auto/agente-inicializacao.md
- **Pronto:** `garra-local.ps1 install` registra a tarefa agendada "Garra Local" (no logon do usuário, sem admin se possível, reinício automático em falha) que roda `garra-agente.ps1`. O agente: `git pull --ff-only` em `main` (só se a árvore estiver limpa), reinstala dependências se requirements.txt mudou, `start`, sobe `cloudflared tunnel --url http://127.0.0.1:8000`, extrai a URL `https://*.trycloudflare.com` do log, publica `api.json` `{url, api_base, online:true, desde, heartbeat}` na branch `snapshot` de `GARRA_PUBLIC_REPO`, gera e publica `snapshot.enc` (T81), e em laço: heartbeat a cada 10 min, snapshot a cada 30 min só se mudou, backup diário. Ao encerrar (stop/desligamento) publica `online:false`. `uninstall` remove a tarefa. Publicação usa um clone raso dedicado fora do repo (`%LOCALAPPDATA%\garra\publico`) e force-push de um commit único na branch órfã, com a credencial git já configurada no PC (Git Credential Manager) ou, se definido, o token `GARRA_PUBLIC_TOKEN` do .env local. Nenhum workflow do Actions dispara em push na branch `snapshot` (confira os filtros de branch de ci.yml, sync-deploy-branches.yml e deploy-pages.yml). Testado de verdade, ou o Doc explica o que faltou.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md. Papel: devops. Leia DEC-57 em 00_docs/projeto/decisoes.md, o Bloco G do BACKLOG.md, e os Docs de T79 (00_docs/backlog-auto/runtime-local-pc.md) e T81 (00_docs/backlog-auto/snapshot-cifrado.md). cloudflared já está instalado em C:\Program Files (x86)\cloudflared\cloudflared.exe (aceite também do PATH).

Implemente 05_infra/local/garra-agente.ps1 (PowerShell 5.1) e os subcomandos install|uninstall|agente em garra-local.ps1 conforme o campo Pronto desta tarefa. Detalhes:
- Variáveis novas no .env.example: GARRA_PUBLIC_REPO (padrão rafaelroriz-age/garra-engenharia), GARRA_PUBLIC_TOKEN (opcional; fine-grained PAT só com Contents read/write; nunca logar; sem ele usa a credencial git do PC), SNAPSHOT_SENHA, intervalos.
- Publicação: clone/fetch raso em $env:LOCALAPPDATA\garra\publico, checkout --orphan snapshot, escreve api.json e snapshot.enc, commit único e push forçado via URL com token montada em memória (não grave o token no .git/config). Este push é do script do PC, não de um agente; não faça push para o GitHub nesta sessão (o guard bloqueia e o repo público pode não existir ainda): teste a publicação contra um remoto bare local em pasta temporária (parâmetro de remoto alternativo) e documente.
- Atualizações: `git -C <repo> pull --ff-only origin main` só se `git status --porcelain` vazio e branch atual main; senão loga e segue com o código atual.
- Robustez: se o cloudflared cair, reinicia e republica a nova URL; se o backend cair, `start` de novo; tudo logado em 05_infra/local/logs/ com rotação simples.
- Tarefa agendada via Register-ScheduledTask (gatilho AtLogOn do usuário atual, RestartCount/RestartInterval, sem janela visível: powershell -WindowStyle Hidden -ExecutionPolicy Bypass -File ...). Não registre a tarefa nesta sessão; implemente e valide com um modo --dry que imprime o que seria registrado. O dono roda `install` (HT-15).
Rode o que for seguro localmente (túnel cloudflared real por alguns segundos para validar a extração da URL, publicação no remoto bare). Doc com fluxos, variáveis, comandos e saídas. Commit: `feat(infra): agente de inicializacao com tunel e snapshot (DEC-57)` com rodapé `Refs DEC-57`.
```

### T83 · Front: descoberta da API por api.json, modo leitura com snapshot e deploy no repo público
- **Status:** done
- **Origem:** DEC-57
- **Papel:** frontend
- **Depende:** T81
- **Ambiente:** offline
- **Dificuldade:** alta
- **Toca:** 03_frontend/lib/api-client.ts, 03_frontend/lib/api-descoberta.ts, 03_frontend/lib/modo-leitura.ts, 03_frontend/lib/modo-leitura.test.ts, 03_frontend/components/modo-leitura-banner.tsx, 03_frontend/components/sw-register.tsx, 03_frontend/public/sw.js, 03_frontend/lib/sw-cache.ts, 03_frontend/lib/sw-cache.test.ts, 03_frontend/app/, 03_frontend/next.config.mjs, .github/workflows/deploy-pages.yml, 00_docs/backlog-auto/front-modo-leitura.md
- **Doc:** 00_docs/backlog-auto/front-modo-leitura.md
- **Pronto:** A URL da API deixa de ser fixa no build: o front lê `api.json` de `NEXT_PUBLIC_API_DISCOVERY_URL` (cache em memória 60 s; em dev cai em `NEXT_PUBLIC_API_URL`). Com `online:false`, heartbeat > 20 min, ou falha de rede/502/503/530 do túnel, entra em modo leitura: pede a senha da equipe (guardada só em sessionStorage), baixa e decifra `snapshot.enc` com WebCrypto (formato e vetor de teste do Doc de T81), responde os GETs de `apiFetch` pelo mapa de rotas e qualquer escrita lança erro claro "Servidor desligado — modo leitura". Faixa fixa "Modo leitura — dados de <data>" e hook `useModoLeitura()` usado para desabilitar ações de gravação nas telas principais. SW registrado com basePath (fecha R-22) e nunca cacheia api.json/snapshot.enc. `deploy-pages.yml` continua publicando no Pages do próprio repositório (basePath `/garra-engenharia`), sem nenhuma referência a onrender.com. Teste unitário (node --test) decifra o vetor de T81. `npm run lint`, `npm run build` e os testes unitários passam.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md. Papel: frontend (.github/agents/frontend.agent.md). Leia DEC-57 em 00_docs/projeto/decisoes.md, o Bloco G do BACKLOG.md e 00_docs/backlog-auto/snapshot-cifrado.md (formato e vetor de teste do snapshot). Leia 03_frontend/lib/api-client.ts, lib/sw-cache.ts, public/sw.js, components/sw-register.tsx, app/layout.tsx, next.config.mjs e .github/workflows/deploy-pages.yml.

Implemente conforme o campo Pronto desta tarefa:
1. lib/api-descoberta.ts: obtém {url, api_base, online, heartbeat} de NEXT_PUBLIC_API_DISCOVERY_URL (https://raw.githubusercontent.com/rafaelroriz-age/garra-engenharia/snapshot/api.json), com cache-buster e cache em memória de 60 s; fallback NEXT_PUBLIC_API_URL (dev). api-client passa a resolver a base de forma assíncrona antes de cada fetch, sem mudar a assinatura pública de apiFetch/uploadImagem nem das funções exportadas usadas pelas telas (grep os usos). Confira em 00_docs/backlog-auto/storage-local.md (T80) se as URLs de download vêm relativas e ajuste a montagem se preciso.
2. lib/modo-leitura.ts: estado global (store simples + evento) com entrar/sair, decifrar (PBKDF2 600000 + AES-GCM via crypto.subtle; DecompressionStream('gzip')), resolver GET pela chave path+query igual à do T81, e erro tipado para escrita. Senha só em sessionStorage; pedido de senha num diálogo simples com os componentes ui/ já existentes. A cada 60 s tenta a API de novo e sai do modo leitura sozinho quando o PC voltar.
3. components/modo-leitura-banner.tsx no layout; hook useModoLeitura() aplicado para desabilitar botões de criar/editar/excluir/upload/emitir nas telas principais (edificações, contratos, inspeções, visitas, ocorrências, fotos, relatórios). Imagens/downloads em modo leitura mostram placeholder "disponível com o servidor ligado". Não mude o visual além disso.
4. SW: registrar `${basePath}/sw.js` com scope `${basePath}/`, OFFLINE_URL relativo ao scope, nunca interceptar raw.githubusercontent.com; mantenha a paridade sw.js ⇔ sw-cache.ts e o teste de paridade.
5. deploy-pages.yml: manter o deploy atual no Pages do próprio repositório (basePath /garra-engenharia), trocar NEXT_PUBLIC_API_URL do Render por NEXT_PUBLIC_API_DISCOVERY_URL e garantir que não dispara em push na branch `snapshot`.
6. lib/modo-leitura.test.ts com node --test: decifra o vetor de teste de T81 e resolve rota; senha errada falha.
Rode npm run lint, npm run build, os testes unitários existentes e o novo; confirme com grep que out/ não contém onrender.com. Doc com o fluxo, decisões e saídas. Commit: `feat(frontend): descoberta da API e modo leitura com snapshot cifrado (DEC-57)` com rodapé `Refs DEC-57`.
```

### T84 · Script de importação dos dados do Render para o Postgres local
- **Status:** done
- **Origem:** DEC-57
- **Papel:** devops
- **Depende:** T82
- **Ambiente:** offline
- **Dificuldade:** media
- **Toca:** 05_infra/local/importar-render.ps1, 00_docs/backlog-auto/importar-render.md
- **Doc:** 00_docs/backlog-auto/importar-render.md
- **Pronto:** Existe `05_infra/local/importar-render.ps1`, para o **dono** rodar (o guard bloqueia agentes na produção), que lê a External Database URL do Render de um prompt seguro (`Read-Host -AsSecureString`, nunca de arquivo versionado), faz `pg_dump -Fc` com os binários de 05_infra/local/bin para 05_infra/local/backups/render-final-*.dump, faz backup do local, restaura com `pg_restore --clean --if-exists --no-owner` no garra_producao local, roda `alembic upgrade head` e imprime a contagem por tabela dos dois lados lado a lado, terminando com OK/DIVERGENTE. A sessão do agente NÃO executa o script contra o Render; testa o fluxo com um banco de dev como origem e um banco descartável como destino, e registra no Doc.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md. Papel: devops. Leia DEC-57 em 00_docs/projeto/decisoes.md e 00_docs/backlog-auto/runtime-local-pc.md (T79). Escreva 05_infra/local/importar-render.ps1 (PowerShell 5.1) conforme o campo Pronto desta tarefa, com parâmetros -OrigemUrl (opcional; sem ele pede de forma segura) e -DestinoDb (padrão garra_producao). Nunca conecte ao Render nesta sessão nem escreva hosts ou URLs reais do Render no código ou no Doc (o guard bloqueia). Teste o fluxo com origem = banco de dev garra_engenharia (localhost:5433, só leitura via pg_dump; suba o Postgres de 05_infra se precisar) e destino = um banco descartável garra_import_teste no Postgres local da porta 5434; depois apague só esse banco descartável. Fotos: confirme lendo render.yaml se o Render tinha storage configurado e registre no Doc se há algo a migrar além do banco. Doc com passo a passo para o dono e saídas do teste. Commit: `feat(infra): importacao do banco do Render para o PC (DEC-57)` com rodapé `Refs DEC-57`.
```

### T85 · Documentação do novo deploy e aposentadoria dos artefatos do Render
- **Status:** done
- **Origem:** DEC-57
- **Papel:** devops
- **Depende:** T80, T82, T83, T84
- **Ambiente:** offline
- **Dificuldade:** baixa
- **Toca:** 05_infra/README.md, 00_docs/configuracao.md, render.yaml, 03_frontend/Dockerfile.render, 04_backend/Dockerfile.render, .github/workflows/sync-deploy-branches.yml, 00_docs/backlog-auto/aposentar-render.md
- **Doc:** 00_docs/backlog-auto/aposentar-render.md
- **Pronto:** `05_infra/README.md` tem a seção "Produção no PC (DEC-57)" com arquitetura, instalação do zero (setup → .env → install), operação diária, restauração de backup em outro PC e o que acontece com o PC desligado; a seção antiga do Render vira nota histórica curta. `00_docs/configuracao.md` lista as variáveis novas. `render.yaml` e os `Dockerfile.render` são removidos; `sync-deploy-branches.yml` deixa de sincronizar `main_front`/`main_back` (desativado com comentário, não apagado). `grep -ri onrender` no repo só encontra notas históricas em 00_docs/. `npm run build` e `pytest` continuam verdes.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md. Papel: devops. Leia DEC-57 em 00_docs/projeto/decisoes.md e os Docs de T79 a T84 em 00_docs/backlog-auto/ (runtime-local-pc.md, storage-local.md, snapshot-cifrado.md, agente-inicializacao.md, front-modo-leitura.md, importar-render.md). Faça o que o campo Pronto desta tarefa pede, sem alterar código de aplicação. Confira com grep todas as referências a render.yaml, Dockerfile.render, onrender.com e main_front/main_back em .github/, 03_frontend/, 04_backend/ e 05_infra/ e trate cada uma (ajuste ou registre por que fica). Não edite decisoes.md, status.md, riscos.md (fechamento de lote). Commit: `docs(infra): producao no PC e aposentadoria do Render (DEC-57)` com rodapé `Refs DEC-57`.
```

### T86 · Teste ponta a ponta: online pelo túnel e modo leitura com o PC desligado
- **Status:** done
- **Origem:** DEC-57
- **Papel:** frontend
- **Depende:** T80, T83, T82
- **Ambiente:** docker
- **Dificuldade:** media
- **Toca:** 03_frontend/e2e/modo-leitura-dec57.spec.ts, 03_frontend/playwright.modo-leitura.config.ts, 00_docs/backlog-auto/e2e-modo-leitura.md
- **Doc:** 00_docs/backlog-auto/e2e-modo-leitura.md
- **Pronto:** Um spec Playwright, com config próprio que serve o build estático (`out/`, basePath de produção) e um `api.json`/`snapshot.enc` locais (servidor estático de teste, sem depender do GitHub), prova: (1) com api.json online apontando para o backend local, login e criação de uma ocorrência funcionam; (2) com api.json `online:false` e um snapshot gerado por `gerar_snapshot` depois da criação, ao recarregar aparece a faixa de modo leitura, a senha é pedida, a ocorrência criada aparece e os botões de gravação estão desabilitados; (3) uma escrita forçada mostra o erro "Servidor desligado — modo leitura". Saída real registrada no Doc.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md. Papel: frontend. Leia DEC-57 em 00_docs/projeto/decisoes.md, 00_docs/backlog-auto/front-modo-leitura.md e snapshot-cifrado.md, e os specs/helpers existentes em 03_frontend/e2e/ (reuse login e criação via API). Escreva o spec e o config conforme o campo Pronto desta tarefa, sem alterar os specs nem o playwright.config.ts existentes. Use o backend e o Postgres de dev de 05_infra (banco de teste da Regra de pronto, item 6) e `python -m app.scripts.gerar_snapshot` com uma SNAPSHOT_SENHA de teste. Se algo não subir por ambiente, registre no Doc em vez de inventar. Se achar bug real no modo leitura, corrija o mínimo em 03_frontend/lib/modo-leitura.ts ou api-descoberta.ts e explique no Doc. npm run lint e build verdes. Commit: `test(frontend): e2e do modo leitura com snapshot (DEC-57)` com rodapé `Refs DEC-57`.
```

### T87 · Neon como banco de produção (opção C): runtime local aponta para o Neon com TLS (DEC-58)
- **Status:** done
- **Origem:** DEC-58 (proposta; ajusta DEC-57 P1)
- **Papel:** devops
- **Depende:** T79
- **Ambiente:** offline
- **Dificuldade:** media
- **Toca:** 05_infra/local/garra-local.ps1, 05_infra/local/garra-agente.ps1, 05_infra/local/.env.example, 04_backend/app/core/config.py, 04_backend/tests/, 00_docs/backlog-auto/neon-banco.md
- **Doc:** 00_docs/backlog-auto/neon-banco.md
- **Pronto:** O backend continua rodando no PC do dono (túnel, `api.json`, snapshot, front no Pages: DEC-57 intacto), mas o PostgreSQL passa a ser o **Neon** (projeto do dono, conexão **direta**, sem `-pooler`, por causa do asyncpg). `config.py` já tem `POSTGRES_SSL` (acrescenta `?ssl=require` à `database_url`); esta tarefa adiciona teste unitário cobrindo `POSTGRES_SSL=true/false` e confirma que `alembic/env.py` e `core/migrations.py` usam a mesma URL. `garra-local.ps1` ganha o modo `POSTGRES_MODO=neon` (ou equivalente documentado): `setup`/`start`/`stop` não sobem nem derrubam o Postgres portátil, `status` testa a conexão ao Neon, e o `.env.example` documenta `POSTGRES_HOST/PORT/USER/DB`, `POSTGRES_SSL=true` (a senha só no `.env` local, que está no .gitignore). `start` roda `alembic upgrade head` contra o Neon. O agente (T82) continua igual. O Doc registra o que rodou de verdade e o que dependeu do dono.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md. Papel: devops. Leia DEC-57 em 00_docs/projeto/decisoes.md, 00_docs/backlog-auto/runtime-local-pc.md (T79), 04_backend/app/core/config.py (campo `postgres_ssl` já existe) e 05_infra/local/garra-local.ps1. Objetivo: o dono quer o Neon (Postgres gerenciado, grátis, escala a zero e não expira) como banco, mantendo backend no PC. Implemente o campo Pronto desta tarefa. Nunca escreva host, usuário ou senha reais do Neon em arquivo versionado, no Doc ou em log: o repositório é público e o guard bloqueia. Para testar sem o Neon real, use o Postgres de dev de 05_infra com POSTGRES_SSL=false e prove com teste unitário que a URL com TLS sai correta; o teste contra o Neon real é do dono (HT). Se faltar a connection string, registre no Doc e pare, sem inventar. Commit: `feat(infra): neon como banco de producao com backend no PC (DEC-58)` com rodapé `Refs DEC-58`.
```

### T88 · Migrar os dados do `garra-db` (Render) para o Neon
- **Status:** done
- **Origem:** DEC-58
- **Papel:** devops
- **Depende:** T84, T87
- **Ambiente:** offline
- **Dificuldade:** media
- **Toca:** 05_infra/local/importar-render.ps1, 00_docs/backlog-auto/migrar-render-neon.md
- **Doc:** 00_docs/backlog-auto/migrar-render-neon.md
- **Pronto:** `importar-render.ps1` (T84) aceita `-DestinoUrl` (prompt seguro, `Read-Host -AsSecureString`, nunca arquivo versionado) para restaurar o dump do `garra-db` do Render **no Neon** em vez do Postgres local, com `pg_restore --clean --if-exists --no-owner`, `alembic upgrade head` e a contagem por tabela dos dois lados terminando em OK/DIVERGENTE. A execução contra o Render e o Neon reais é do **dono** (o guard bloqueia agentes); a sessão do agente testa o fluxo com bancos de dev descartáveis e registra a saída no Doc, incluindo o passo manual alternativo (Import Data Assistant do console do Neon) e a recomendação de só apagar o `garra-db` no Render depois do OK. A tabela `usuarios` e os hashes devem chegar intactos (login do admin funciona contra o Neon).
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md. Papel: devops. Leia DEC-57, 00_docs/backlog-auto/importar-render.md (T84) e 00_docs/backlog-auto/neon-banco.md (T87). Estenda 05_infra/local/importar-render.ps1 conforme o campo Pronto desta tarefa, sem remover o modo de destino local. Nunca conecte ao Render nem ao Neon reais nesta sessão e nunca escreva hosts, URLs ou senhas reais em arquivo ou Doc. Teste com origem = banco de dev e destino = banco descartável (apague só o descartável). O Doc tem o passo a passo para o dono, com a ordem: dump final do Render, restauração no Neon, conferência, login de teste, e só então desligar o Render. Commit: `feat(infra): importar banco do Render no Neon (DEC-58)` com rodapé `Refs DEC-58`.
```

### T89 · Backup do Neon e documentação do banco gerenciado (DEC-58)
- **Status:** done
- **Origem:** DEC-58
- **Papel:** devops
- **Depende:** T87, T88
- **Ambiente:** offline
- **Dificuldade:** baixa
- **Toca:** 05_infra/local/garra-local.ps1, 05_infra/README.md, 00_docs/configuracao.md, 00_docs/backlog-auto/neon-backup.md
- **Doc:** 00_docs/backlog-auto/neon-backup.md
- **Pronto:** O subcomando `backup` e a rotina diária do agente fazem `pg_dump -Fc` contra o Neon (com `PGSSLMODE=require`) para `05_infra/local/backups/`, com retenção de 14, porque o plano gratuito do Neon não substitui backup próprio. `05_infra/README.md` ganha a seção "Banco no Neon (DEC-58)" (criação do projeto, conexão direta × pooled, `POSTGRES_SSL`, cold start de ~1-2 s após 5 min ocioso, restauração em outro banco) e `00_docs/configuracao.md` lista `POSTGRES_SSL` e `POSTGRES_MODO`. Registra em nota que DEC-57 P1 (Postgres portátil) passa a ser opcional/fallback. `pytest` continua verde.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md. Papel: devops. Leia DEC-57, os Docs de T79, T82, T87 e T88. Faça o que o campo Pronto desta tarefa pede. Não edite decisoes.md, status.md, riscos.md (fechamento de lote: a DEC-58 será registrada lá pelo dono). Nunca escreva credenciais reais. Commit: `docs(infra): backup e documentacao do banco no Neon (DEC-58)` com rodapé `Refs DEC-58`.
```

### T93 · Exercitar backup e restauração contra o Neon real antes de desligar o garra-db (R-24)
- **Status:** done
- **Origem:** R-24
- **Papel:** Engenheiro DevOps
- **Depende:** T89
- **Ambiente:** humano
- **Dificuldade:** media
- **Toca:** 00_docs/backlog-auto/neon-backup-teste-real.md
- **Doc:** 00_docs/backlog-auto/neon-backup-teste-real.md
- **Pronto:** O Doc registra, com data e saída (sem segredos): `garra-local.ps1 backup` gerou um dump `pg_dump -Fc` do Neon com tamanho > 0 e retenção de 14 aplicada; o restore desse dump em banco descartável (não o de produção) terminou sem erro e a contagem de linhas de `usuarios`, `contratos`, `edificacoes`, `inspecoes`, `ocorrencias` e `fotos` confere com o Neon; a pasta de dumps foi avaliada quanto ao OneDrive (dados pessoais) com a decisão registrada como proposta. Nenhuma string de conexão, senha ou token aparece no Doc ou em commit.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md (raiz do repositório). Esta tarefa exige credencial do Neon e acesso à máquina do dono: só a pessoa dona do projeto (ou sessão com a string de conexão no ambiente local, nunca no repositório) pode executá-la; um agente sem essa credencial deve apenas registrar no Doc que não rodou e encerrar. Contexto: R-24 em 00_docs/projeto/riscos.md e DEC-58: o backup diário do Neon (T89, 00_docs/backlog-auto/neon-backup.md) nunca foi exercitado contra o Neon real, e os dumps ficam numa pasta do OneDrive com dados pessoais. Leia 00_docs/backlog-auto/neon-backup.md, a seção «Banco no Neon» de 05_infra/README.md e 05_infra/backup/ (backup-db.sh, restore-db.sh). Passos: (1) rode `garra-local.ps1 backup` (veja o caminho do script no README de infra) e confirme o arquivo gerado e o tamanho; (2) crie um banco descartável (PostgreSQL local de 05_infra ou branch do Neon) e restaure o dump com restore-db.sh, jamais sobre o banco de produção; (3) compare contagens de linhas nas tabelas citadas no critério de pronto entre Neon e o banco restaurado; (4) verifique se a pasta de dumps está sob o OneDrive e proponha (no Doc, como proposta, sem editar decisoes.md) cifrar o dump ou movê-lo para fora do OneDrive; (5) apague o banco descartável. Escreva o resultado no Doc novo 00_docs/backlog-auto/neon-backup-teste-real.md, sem imprimir segredos. Não edite os documentos de gestão compartilhados. Commit só do Doc: `docs(infra): teste real de backup e restore do Neon (R-24)` com rodapé `Refs R-24`. Não faça push.
```

---

## Bloco H — Acabamento das consequências abertas das decisões propostas (DEC-50/51/52/56)

### T94 · Legenda IA: expurgo de `resposta` expirada em `chamadas_ia` (script com dry-run)
- **Status:** done
- **Origem:** DEC-52
- **Papel:** backend
- **Depende:** —
- **Ambiente:** docker
- **Dificuldade:** baixa
- **Toca:** 04_backend/app/scripts/limpar_chamadas_ia.py, 04_backend/tests/test_limpar_chamadas_ia.py, 00_docs/backlog-auto/ia-retencao-chamadas.md
- **Doc:** 00_docs/backlog-auto/ia-retencao-chamadas.md
- **Pronto:** Existe `python -m app.scripts.limpar_chamadas_ia` com `--dry-run` por padrão e `--aplicar` para executar. O script anula a coluna `resposta` das linhas de `chamadas_ia` mais antigas que `LEGENDA_IA_CACHE_TTL_H` e preserva tokens, custo, latência e origem. Os testes novos passam no banco `garra_engenharia_test`, `ruff check .` está limpo e o Doc registra o resultado.
- **Prompt:**
```text
Tarefa (origem DEC-52, consequência «a coluna `resposta` guarda a legenda saneada sem política de retenção»). Siga a "Regra de pronto" do BACKLOG.md, inclusive o `git merge --ff-only main` inicial e o uso do banco `garra_engenharia_test`. Papel: backend (.github/agents/backend.agent.md).

Contexto: a T68 criou a tabela `chamadas_ia` (migration `b8d4f2a6c1e7`) e o cache local da legenda IA, com TTL de `LEGENDA_IA_CACHE_TTL_H` (padrão 720 h; `0` desliga o cache). Leia a seção DEC-52 em 00_docs/projeto/decisoes.md, o doc 00_docs/backlog-auto/ia-telemetria-cache.md e o modelo/serviço de telemetria em 04_backend/app (procure por `chamadas_ia` e `LEGENDA_IA_CACHE_TTL_H`). Hoje a coluna `resposta` fica guardada para sempre. Isso é dado derivado de fotos de clientes.

Faça: crie 04_backend/app/scripts/limpar_chamadas_ia.py, seguindo o estilo dos outros scripts de `app/scripts/` (argparse, `python -m app.scripts.limpar_chamadas_ia`). Por padrão é dry-run: conta e imprime quantas linhas teriam `resposta` anulada, sem escrever. Com `--aplicar` executa um UPDATE que põe `resposta = NULL` nas linhas com `resposta IS NOT NULL` e `criado_em` anterior a agora menos o TTL (aceite `--ttl-horas` para sobrescrever). NUNCA apague linhas nem altere tokens, custo, latência ou origem. Se o TTL for 0, o script deve usar o padrão de 720 h ou exigir `--ttl-horas`, e documentar a escolha. Garanta que o cache local não devolva `resposta` nula como acerto, ou registre no Doc o comportamento verificado (cache vazio é miss). Crie 04_backend/tests/test_limpar_chamadas_ia.py: dry-run não altera nada, `--aplicar` anula só as vencidas, linhas recentes ficam intactas, idempotência e preservação das demais colunas. Variável de ambiente nova: nenhuma prevista; se criar, ponha no .env.example. Rode `pytest` dos testes novos mais `tests/test_ia_*` relacionados e `ruff check .` em 04_backend. Se o PostgreSQL de 05_infra (localhost:5433) não estiver no ar, diga isso no Doc em vez de inventar resultado. Registre no Doc 00_docs/backlog-auto/ia-retencao-chamadas.md: o que foi feito, comandos, saída dos testes e uma proposta (não decisão) de agendamento semanal. Não edite 00_docs/projeto/*.md. Commit: `feat(backend): script de expurgo de resposta expirada em chamadas_ia (DEC-52)` com rodapé `Refs DEC-52`. Nunca faça push.
```

### T95 · Rota `PUT /responsaveis/{id}` usando o `ResponsavelUpdate` já existente
- **Status:** done
- **Origem:** DEC-50
- **Papel:** backend
- **Depende:** —
- **Ambiente:** docker
- **Dificuldade:** baixa
- **Toca:** 04_backend/app/api/v1/responsaveis.py, 04_backend/tests/test_responsaveis_update.py, 00_docs/backlog-auto/responsaveis-update.md
- **Doc:** 00_docs/backlog-auto/responsaveis-update.md
- **Pronto:** `PUT /api/v1/responsaveis/{id}` existe, aceita atualização parcial via `ResponsavelUpdate` e é restrito ao auditor (403 para auxiliar e cliente). Responde 404 para id inexistente e 422 para dados inválidos. Os testes novos passam no banco de testes, `ruff check .` está limpo e o Doc registra o resultado.
- **Prompt:**
```text
Tarefa (origem DEC-50, consequência «`ResponsavelUpdate` existe sem rota»). Siga a "Regra de pronto" do BACKLOG.md, inclusive o `git merge --ff-only main` inicial e o banco `garra_engenharia_test`. Papel: backend (.github/agents/backend.agent.md).

Contexto: o schema `ResponsavelUpdate` foi criado pela T57 em 04_backend/app/schemas/ mas nenhum endpoint o usa; hoje só existem `POST` e `GET /responsaveis` (DEC-23). Leia a seção DEC-50 de 00_docs/projeto/decisoes.md e 00_docs/backlog-auto/v1-fundacao-dados.md. Leia também 04_backend/app/api/v1/responsaveis.py, o modelo `Responsavel`, `app/api/deps.py` (`require_auditor`/`require_equipe`, BL-42) e como os outros routers (ex.: edificacoes.py) fazem `PUT` parcial (`model_dump(exclude_unset=True)`).

Faça: adicione `PUT /api/v1/responsaveis/{responsavel_id}` em responsaveis.py. Só o auditor pode (use a dependência já existente). Atualização parcial: campo omitido não muda. Campos sem validação de unicidade/formatos já existentes no `POST` devem seguir as mesmas regras do `POST` (reaproveite validações; se houver unicidade de e-mail/CPF, responda 409). Não permita alterar `usuario_id` por esta rota se isso abrir escalada de privilégio: confira como o vínculo do Portal do Cliente (`Responsavel.usuario_id`, DEC-18) é feito e, se `ResponsavelUpdate` o expõe, bloqueie-o ou justifique no Doc. Não altere os schemas fora do estritamente necessário. Escreva 04_backend/tests/test_responsaveis_update.py: auditor atualiza (200 e persiste), parcial preserva campos, id inexistente 404, auxiliar e cliente 403, sem token 401, payload inválido 422, e conflito se aplicável. Rode esses testes, os testes de responsáveis/RBAC já existentes (`pytest tests -k "responsave or rbac"`) e `ruff check .` em 04_backend. Se o PostgreSQL (localhost:5433) estiver fora do ar, registre que não rodou. Registre tudo no Doc 00_docs/backlog-auto/responsaveis-update.md (contrato da rota, decisões tomadas como proposta, saída dos testes). Não edite 00_docs/projeto/*.md. Commit: `feat(backend): PUT /responsaveis/{id} (DEC-50)` com rodapé `Refs DEC-50`. Nunca faça push.
```

### T96 · Service Worker: logout em uma aba limpa o cache de dados nas outras abas
- **Status:** done
- **Origem:** DEC-56
- **Papel:** frontend
- **Depende:** —
- **Ambiente:** offline
- **Dificuldade:** media
- **Toca:** 03_frontend/lib/sw-cache.ts, 03_frontend/lib/auth-token.ts, 03_frontend/public/sw.js, 03_frontend/lib/tests/, 00_docs/backlog-auto/pwa-logout-multiaba.md
- **Doc:** 00_docs/backlog-auto/pwa-logout-multiaba.md
- **Pronto:** Fazer logout (`clearAuthToken`) em uma aba apaga o cache de dados do Service Worker também quando outra aba está aberta, via evento `storage` ou BroadcastChannel, sem quebrar o caso de uma aba só. Há teste unitário de lógica pura com `node --test`. `npm run lint` e `npm run build` passam e o Doc registra o resultado.
- **Prompt:**
```text
Tarefa (origem DEC-56, consequência «Logout em outra aba não limpa o cache da aba atual (TTL limita a exposição)»). Siga a "Regra de pronto" do BACKLOG.md, inclusive o `git merge --ff-only main` inicial. Papel: frontend (.github/agents/frontend.agent.md). Comandos npm a partir de 03_frontend/.

Contexto: a T77 (DEC-56) criou o Service Worker de cache só de leitura: 03_frontend/public/sw.js e 03_frontend/lib/sw-cache.ts. Leia a seção DEC-56 de 00_docs/projeto/decisoes.md e 00_docs/backlog-auto/pwa-service-worker.md. O logout (`clearAuthToken`, procure por essa função em 03_frontend/lib/) já manda apagar o cache de dados, mas só na aba que fez o logout. O token fica em `localStorage`, então o evento `storage` dispara nas outras abas do mesmo origin quando a chave do token é removida. O app é export estático com `basePath` (DEC-55): qualquer caminho deve respeitar `NEXT_PUBLIC_BASE_PATH`. Isso pode não ser o caso do canal de mensagens, mas confira.

Faça: faça as outras abas apagarem o cache de dados ao detectar o logout (remoção/limpeza da chave do token, ou mensagem em BroadcastChannel), reaproveitando a função que já limpa o cache; não duplique a lógica nem mude a allowlist, TTLs ou o que é cacheado. Cuide de: ouvinte registrado uma só vez (sem vazamento em re-render do React/Next), cleanup do listener, e nenhum erro quando `localStorage`/`BroadcastChannel`/Service Worker não existem (SSR do build, navegador sem suporte). A lógica de decisão («este evento representa logout?») deve ficar em função pura exportada para ser testada por `node --test`, no padrão dos testes unitários que a T77 criou (descubra onde estão e siga a mesma convenção). Não toque em `e2e/` nem em `next.config.mjs`. Escreva os testes unitários (evento do token removido → limpa; outra chave → ignora; valor trocado por outro token → não limpa; ambiente sem API → sem erro). Rode os testes unitários existentes mais os novos, `npm run lint` e `npm run build`. Playwright é opcional; se não rodar, diga. Registre no Doc 00_docs/backlog-auto/pwa-logout-multiaba.md o mecanismo escolhido, a limitação restante (ex.: aba fechada, navegador sem suporte) e a saída dos comandos. Não edite 00_docs/projeto/*.md. Commit: `feat(frontend): logout limpa o cache do Service Worker em todas as abas (DEC-56)` com rodapé `Refs DEC-56`. Nunca faça push.
```

### T97 · Edificação com `cidade` e `uf` próprios e uso na cidade da emissão dos relatórios
- **Status:** done
- **Origem:** DEC-50
- **Papel:** backend
- **Depende:** —
- **Ambiente:** docker
- **Dificuldade:** alta
- **Toca:** 04_backend/app/models/edificacao.py, 04_backend/app/schemas/edificacao.py, 04_backend/alembic/versions/, 04_backend/app/services/report_generator/contexto_comum.py, 04_backend/tests/test_edificacao_cidade_uf.py, 00_docs/backlog-auto/edificacao-cidade-uf.md
- **Doc:** 00_docs/backlog-auto/edificacao-cidade-uf.md
- **Pronto:** `Edificacao` tem `cidade` e `uf` opcionais, com migration de `upgrade()` e `downgrade()` testados e um único head do Alembic. Os schemas de criação, atualização e leitura aceitam os campos (`uf` validado com 2 letras maiúsculas). O contexto comum dos relatórios usa `cidade/uf` quando existirem e, caso contrário, mantém o fallback atual (cidade extraída do endereço). Testes novos passam, os testes de emissão não regridem, `ruff check .` está limpo e o Doc registra o resultado.
- **Prompt:**
```text
Tarefa (origem DEC-50, P5: «A cidade da emissão sai do endereço (`Cidade-UF`) até existir `cidade`/`uf` em `Edificacao`»). Siga a "Regra de pronto" do BACKLOG.md, inclusive o `git merge --ff-only main` inicial e o banco `garra_engenharia_test` (rode `alembic upgrade head` nele). Papel: backend (.github/agents/backend.agent.md). Comandos Python/alembic a partir de 04_backend/.

Contexto: leia a seção DEC-50 em 00_docs/projeto/decisoes.md e 00_docs/backlog-auto/v1-emissao-generica.md. Hoje a cidade da emissão dos relatórios é extraída do campo livre `endereco` da `Edificacao` (formato esperado `Cidade-UF`) no montador compartilhado 04_backend/app/services/report_generator/contexto_comum.py (procure pela função que deriva a cidade). Os montadores `rfo_contexto.py`, `ltip_contexto.py`, `rfip_contexto.py` e os de vistorias usam esse comum. Não crie nenhum campo obrigatório: dados antigos continuam válidos.

Faça: (1) adicione `cidade` (String, nullable, até 120) e `uf` (String(2), nullable) ao modelo `Edificacao` e aos schemas Create/Update/Read em 04_backend/app/schemas/edificacao.py; `uf` é normalizada para maiúsculas e validada (2 letras); string vazia vira `None`. (2) Crie migration Alembic nova (com `downgrade()`) cujo `down_revision` seja o único head atual: rode `alembic heads` ANTES. Se houver mais de um head (R-17), NÃO faça merge sem registrar: descreva a situação no Doc e use um `alembic merge` apenas se for necessário para os testes, dizendo isso claramente. A migration não reescreve dados nem faz backfill automático. Valide upgrade, downgrade e novo upgrade no banco de testes, e `alembic check`. (3) No `contexto_comum.py`, use `cidade` e `uf` quando preenchidas (formato de saída idêntico ao de hoje, ex. `Cidade-UF` ou o que o template já espera: confira nos testes existentes) e mantenha o fallback pelo endereço quando ausentes. Não mude os templates nem o `layout.json`. (4) Não altere o frontend; registre no Doc que o formulário de edificação (03_frontend/app/edificacoes/) ainda precisa expor os campos, como pendência para uma próxima tarefa. (5) Testes em 04_backend/tests/test_edificacao_cidade_uf.py: criação/atualização/leitura com e sem os campos, `uf` inválida → 422, normalização, e o contexto comum com cidade/uf preenchidas, só uma delas, e ausentes (fallback). Rode esses testes, os de edificações e `pytest tests -k "contexto or emissao or relatorio"` e `ruff check .`. Registre tudo que não rodar por falta de PostgreSQL ou WeasyPrint em vez de inventar resultado. Documente no Doc 00_docs/backlog-auto/edificacao-cidade-uf.md: o que mudou, a revisão do migration, o fallback e a saída dos testes. Não edite 00_docs/projeto/*.md. Commit: `feat(backend): cidade e uf em Edificacao usadas na emissao (DEC-50)` com rodapé `Refs DEC-50`. Nunca faça push.
```

### T98 · Frontend: enviar e exibir cidade e UF na Edificação
- **Status:** done
- **Origem:** T97
- **Papel:** Engenheiro Frontend
- **Depende:** —
- **Ambiente:** offline
- **Dificuldade:** baixa
- **Toca:** 03_frontend/app/edificacoes/, 00_docs/backlog-auto/edificacao-cidade-uf-frontend.md
- **Doc:** 00_docs/backlog-auto/edificacao-cidade-uf-frontend.md
- **Pronto:** O formulário de edificação (criar e editar) tem os campos Cidade (texto, máx. 120) e UF (2 letras, convertida para maiúsculas) e os envia no payload; a página de detalhe e a lista exibem cidade/UF quando preenchidos; `npm run lint` e `npm run build` em 03_frontend passam; o Doc registra os comandos e a saída.
- **Prompt:**
```text
Contexto: a T97 (migration `d3e7a1c5f9b2`) adicionou `cidade` (str|None, máx. 120) e `uf` (str|None, 2 letras A-Z, normalizada para maiúsculas, 422 se inválida) a Edificação no backend (`04_backend/app/schemas/edificacao.py`, DEC-50 P5). O frontend ainda não envia nem mostra esses campos. Tarefa: em 03_frontend/app/edificacoes/ (`edificacao-form.tsx`, `page.tsx` e `detalhe/page.tsx`) adicione os campos Cidade e UF ao formulário de criação/edição, inclua-os no payload (envie `null` quando vazios), mostre-os na lista e no detalhe quando existirem, e ajuste os tipos TypeScript da edificação. Trate o erro 422 de UF com mensagem clara em português. Use apenas os componentes e o estilo já existentes. Não mexa no backend nem em outros diretórios além do listado em `toca`. Rode `npm run lint` e `npm run build` a partir de 03_frontend/. Registre em 00_docs/backlog-auto/edificacao-cidade-uf-frontend.md o que mudou (arquivo:linha), os comandos e a saída e o que não foi testado. Siga a 'Regra de pronto' do BACKLOG.md. Não edite os documentos de gestão em 00_docs/projeto/ nem o BACKLOG.md. Commit: `feat(frontend): campos cidade e UF na edificação (DEC-50)` com rodapé `Refs DEC-50`. Não faça push.
```

### T99 · Backend: alertar na geração do relatório quando há fotos com legenda IA em rascunho
- **Status:** done
- **Origem:** T36
- **Papel:** Engenheiro Backend
- **Depende:** —
- **Ambiente:** docker
- **Dificuldade:** media
- **Toca:** 04_backend/app/services/relatorio_service.py, 04_backend/app/schemas/relatorio.py, 04_backend/tests/test_relatorio_alerta_ia_rascunho.py, 00_docs/backlog-auto/relatorio-alerta-ia-rascunho.md
- **Doc:** 00_docs/backlog-auto/relatorio-alerta-ia-rascunho.md
- **Pronto:** A resposta da emissão/geração do relatório traz um campo de alerta (lista de ids ou contagem de fotos com legenda IA ainda em rascunho) calculado por `sinalizar_fotos_ia_em_rascunho`; a geração NÃO é bloqueada; testes novos cobrem com e sem rascunhos e passam; `ruff check .` passa; o Doc registra a saída do pytest ou que o PostgreSQL não estava no ar.
- **Prompt:**
```text
Contexto: `sinalizar_fotos_ia_em_rascunho(fotos)` existe em 04_backend/app/services/report_generator/legenda_foto.py (devolve os índices das fotos com legenda IA em rascunho) e é testada em tests/test_legenda_relatorio.py, mas não é usada em nenhum fluxo de geração (pendência da T36/BL-38; DEC-37 DP-9 é proposta: só legenda aprovada entra no relatório). Tarefa: localize onde o relatório é gerado/emitido (comece por 04_backend/app/services/relatorio_service.py e pelo endpoint correspondente em app/api/v1/), chame a função sobre as fotos usadas e devolva no schema de resposta (04_backend/app/schemas/relatorio.py) um campo opcional e retrocompatível, por exemplo `fotos_ia_em_rascunho: list[int]` (use ids de foto se os índices não forem estáveis; documente a escolha). A geração continua normalmente: é alerta, não bloqueio. Não altere os pipelines (rfo/ltip/rfip/vistorias) nem legenda_foto.py, salvo se estritamente necessário, e nesse caso justifique no Doc. Crie tests/test_relatorio_alerta_ia_rascunho.py com ao menos: sem rascunhos (lista vazia), com rascunhos e com legenda aprovada ignorada. Rode a partir de 04_backend/: `pytest tests/test_relatorio_alerta_ia_rascunho.py tests/test_legenda_relatorio.py` e `ruff check .`. O PostgreSQL de 05_infra/docker-compose.yml (localhost:5433) é necessário; se não estiver no ar, registre que não rodou, sem inventar resultado. Registre em 00_docs/backlog-auto/relatorio-alerta-ia-rascunho.md o formato do campo, arquivo:linha, comandos e saída. Siga a 'Regra de pronto' do BACKLOG.md. Não edite os documentos de gestão em 00_docs/projeto/ nem o BACKLOG.md. Commit: `feat(backend): alerta de fotos com legenda IA em rascunho na geração do relatório (BL-38)` com `Refs BL-38`. Não faça push.
```

### T100 · Frontend: mostrar na tela de relatório o aviso de fotos com legenda IA em rascunho
- **Status:** done
- **Origem:** T36
- **Papel:** Engenheiro Frontend
- **Depende:** T99
- **Ambiente:** offline
- **Dificuldade:** media
- **Toca:** 03_frontend/app/inspecoes/relatorio/page.tsx, 00_docs/backlog-auto/relatorio-alerta-ia-rascunho-frontend.md
- **Doc:** 00_docs/backlog-auto/relatorio-alerta-ia-rascunho-frontend.md
- **Pronto:** A tela de relatório exibe aviso não bloqueante, com a contagem, quando a resposta da geração traz fotos com legenda IA em rascunho, e nada quando o campo vem vazio ou ausente; `npm run lint` e `npm run build` passam; o Doc registra os comandos e a saída.
- **Prompt:**
```text
Contexto: a tarefa B (Doc 00_docs/backlog-auto/relatorio-alerta-ia-rascunho.md) acrescentou ao schema de resposta da geração/emissão do relatório um campo de alerta com as fotos cuja legenda IA ainda está em rascunho (leia o Doc para o nome e o formato exatos e confira em 04_backend/app/schemas/relatorio.py). Tarefa: em 03_frontend/app/inspecoes/relatorio/page.tsx, trate esse campo após gerar/emitir: se houver itens, mostre um aviso visível e não bloqueante (ex.: «N foto(s) com legenda IA ainda em rascunho; só legendas aprovadas aparecem no relatório»), com o estilo de alertas já usado no app; se vier vazio ou ausente, não mostre nada. Atualize o tipo TypeScript da resposta. Não altere o backend. Rode `npm run lint` e `npm run build` a partir de 03_frontend/. Registre em 00_docs/backlog-auto/relatorio-alerta-ia-rascunho-frontend.md o que mudou (arquivo:linha), os comandos, a saída e o que não foi testado em navegador. Siga a 'Regra de pronto' do BACKLOG.md. Não edite os documentos de gestão em 00_docs/projeto/ nem o BACKLOG.md. Commit: `feat(frontend): aviso de legendas IA em rascunho na tela de relatório (BL-38)` com `Refs BL-38`. Não faça push.
```

### T103 · POST /responsaveis com usuario_id já vinculado deve devolver 409 em vez de 500
- **Status:** done
- **Origem:** DEC-59
- **Papel:** Engenheiro Backend
- **Depende:** —
- **Ambiente:** docker
- **Dificuldade:** baixa
- **Toca:** 04_backend/app/api/v1/responsaveis.py, 04_backend/tests/test_responsaveis.py, 00_docs/backlog-auto/responsaveis-409-usuario.md
- **Doc:** 00_docs/backlog-auto/responsaveis-409-usuario.md
- **Pronto:** pytest tests/test_responsaveis.py tests/test_responsaveis_update.py verde (PostgreSQL de 05_infra em localhost:5433 no ar), com teste novo que cria dois responsáveis com o mesmo usuario_id e espera 409 no segundo POST; usuario_id inexistente no POST devolve 422, como no PUT; ruff check . limpo; Doc registra o resultado e o que foi decidido.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md (raiz do repositório) e as regras do projeto: monorepo (docs em 00_docs/, backend em 04_backend/), comandos Python a partir de 04_backend/, commits Conventional Commits com escopo e rodapé 'Refs DEC-59', sem push, sem tocar nas branches main_back/main_front/staging_back/staging_front, e sem editar backlog-tarefas.md, backlog-kanban.md, status.md, decisoes.md e riscos.md. Papel: Engenheiro Backend (siga .github/agents/backend.agent.md se existir).

Contexto: DEC-59 (00_docs/projeto/decisoes.md, ~linha 785) registra como lacuna conhecida que `POST /responsaveis` com `usuario_id` já vinculado a outro Responsável resulta em erro 500 (violação de unicidade no banco). O `PUT /responsaveis/{id}` já trata o caso: 422 se o usuário não existe e 409 se já está vinculado. Veja a implementação em 04_backend/app/api/v1/responsaveis.py (funções `criar_responsavel`, linha ~52, e `atualizar_responsavel`, linha ~66), e os testes existentes em 04_backend/tests/test_responsaveis.py e test_responsaveis_update.py.

Tarefa: faça o POST se comportar como o PUT nesse ponto, reutilizando a mesma verificação/helper em vez de duplicar código (422 para usuario_id inexistente; 409 para usuario_id já vinculado, com mensagem em Problem Details no mesmo formato do PUT). Não mude o contrato nos demais casos. Adicione testes em tests/test_responsaveis.py cobrindo 409 e 422 no POST. Rode `pytest` e `ruff check .` em 04_backend com o PostgreSQL de 05_infra/docker-compose.yml (localhost:5433); se ele não estiver no ar, registre que não rodou em vez de inventar resultado. Registre o resultado, os comandos rodados e qualquer decisão proposta em 00_docs/backlog-auto/responsaveis-409-usuario.md.
```

### T104 · PUT /edificacoes/{id} não pode zerar cidade/uf quando o corpo não os envia
- **Status:** done
- **Origem:** DEC-59
- **Papel:** Engenheiro Backend
- **Depende:** —
- **Ambiente:** docker
- **Dificuldade:** baixa
- **Toca:** 04_backend/app/repositories/edificacao_repository.py, 04_backend/app/services/edificacao_service.py, 04_backend/app/schemas/edificacao.py, 04_backend/tests/test_edificacao_cidade_uf.py, 00_docs/backlog-auto/edificacao-put-preserva-cidade-uf.md
- **Doc:** 00_docs/backlog-auto/edificacao-put-preserva-cidade-uf.md
- **Pronto:** pytest tests/test_edificacoes.py tests/test_edificacao_cidade_uf.py verde (PostgreSQL localhost:5433 no ar), com teste novo: PUT sem cidade/uf em edificação que já os tem mantém os valores; PUT com cidade/uf os altera; ruff check . limpo; Doc registra o comportamento escolhido.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md (raiz) e as regras do projeto: comandos Python a partir de 04_backend/, commits Conventional Commits com escopo e rodapé 'Refs DEC-59', sem push, sem tocar nas branches main_back/main_front/staging_back/staging_front, sem editar os documentos de gestão compartilhados (backlog-tarefas.md, backlog-kanban.md, status.md, decisoes.md, riscos.md). Papel: Engenheiro Backend.

Contexto: DEC-59 (00_docs/projeto/decisoes.md, ~linha 785) registra que `PUT /edificacoes/{id}` sem os campos `cidade`/`uf` zera os dois (campos adicionados por T96 em Edificacao; ver 00_docs/backlog-auto/edificacao-cidade-uf.md). Arquivos: 04_backend/app/schemas/edificacao.py (EdificacaoUpdate), app/repositories/edificacao_repository.py (`update`, linha ~62), app/services/edificacao_service.py (`atualizar`, linha ~51), testes em tests/test_edificacao_cidade_uf.py e tests/test_edificacoes.py.

Tarefa: faça a atualização distinguir 'campo ausente' de 'campo enviado como null/vazio' (por exemplo `model_dump(exclude_unset=True)` no update), de modo que cidade/uf ausentes no corpo sejam preservados e enviados explicitamente (inclusive null) sejam gravados. Não altere o comportamento dos demais campos além do estritamente necessário e confirme com os testes existentes que nada regride (se algum teste existente dependia de campos ausentes virarem null, ajuste-o e explique no Doc). Adicione testes novos. Rode `pytest` e `ruff check .` em 04_backend com o PostgreSQL de 05_infra (localhost:5433); se não estiver no ar, registre que não rodou. Registre o resultado e decisões propostas em 00_docs/backlog-auto/edificacao-put-preserva-cidade-uf.md.
```

### T105 · Telemetria da IA: gravar SQL NULL (não JSON null) em chamadas_ia.resposta
- **Status:** done
- **Origem:** DEC-59
- **Papel:** Engenheiro Backend
- **Depende:** —
- **Ambiente:** docker
- **Dificuldade:** media
- **Toca:** 04_backend/app/services/legenda_ia/telemetria.py, 04_backend/tests/test_limpar_chamadas_ia.py, 00_docs/backlog-auto/ia-resposta-sql-null.md
- **Doc:** 00_docs/backlog-auto/ia-resposta-sql-null.md
- **Pronto:** pytest tests/test_limpar_chamadas_ia.py e os testes de legenda_ia/telemetria (pytest -k 'legenda or telemetria or chamadas') verdes com PostgreSQL localhost:5433; teste novo comprova que registrar() sem resposta grava SQL NULL (IS NULL) e que o cache continua sem tratar resposta nula como acerto; ruff check . limpo.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md (raiz) e as regras do projeto: comandos Python a partir de 04_backend/, commits Conventional Commits com escopo e rodapé 'Refs DEC-59', sem push, sem tocar nas branches main_back/main_front/staging_back/staging_front, sem editar os documentos de gestão compartilhados. Papel: Engenheiro Backend.

Contexto: DEC-59 P1 (00_docs/projeto/decisoes.md, ~linha 785) sugere que `registrar()` em 04_backend/app/services/legenda_ia/telemetria.py (linha ~120) grave SQL NULL em `chamadas_ia.resposta` quando não há resposta, em vez de JSON `null` (o campo é JSON/JSONB; sem `none_as_null`/`null()` o SQLAlchemy grava JSON null). A limpeza de retenção (`python -m app.scripts.limpar_chamadas_ia`) anula a coluna em SQL NULL, e o cache nunca deve tratar resposta nula (SQL NULL ou JSON null) como acerto. Veja 00_docs/backlog-auto/ia-retencao-chamadas.md e os testes em 04_backend/tests/test_limpar_chamadas_ia.py.

Tarefa: faça `registrar()` gravar SQL NULL de forma consistente com o script de limpeza (ex.: `sqlalchemy.null()` ou `none_as_null=True` no tipo, sem exigir migration; se exigir, a migration precisa de downgrade()). Mantenha a proteção do cache contra resposta nula e adicione teste(s) que verifiquem `resposta IS NULL` no banco e que registros antigos com JSON null continuam sendo ignorados pelo cache. Rode `pytest` (ao menos os testes da legenda IA e da telemetria) e `ruff check .` em 04_backend com o PostgreSQL de 05_infra (localhost:5433); se não estiver no ar, registre que não rodou. Registre resultado e decisões propostas em 00_docs/backlog-auto/ia-resposta-sql-null.md.
```

### T106 · nginx: location própria para o upload de documentos de edificação (limite de corpo)
- **Status:** done
- **Origem:** R-25
- **Papel:** Engenheiro DevOps
- **Depende:** —
- **Ambiente:** docker
- **Dificuldade:** baixa
- **Toca:** 05_infra/nginx/nginx.conf, 00_docs/backlog-auto/nginx-upload-documentos.md
- **Doc:** 00_docs/backlog-auto/nginx-upload-documentos.md
- **Pronto:** nginx.conf tem location própria (client_max_body_size ~30m, acima dos 25 MiB do backend) para o POST de documento de edificação, sem afetar o teto de 1m das demais rotas nem o de 40m do upload de fotos; `nginx -t` executado com a config (via container nginx) e saída registrada no Doc, ou registro explícito de que o Docker não estava disponível; Doc lista a rota exata e o limite escolhido.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md (raiz) e as regras do projeto: não crie pastas na raiz, commits Conventional Commits com escopo e rodapé 'Refs R-25', sem push, sem tocar nas branches main_back/main_front/staging_back/staging_front, sem editar os documentos de gestão compartilhados (riscos.md, decisoes.md, status.md, backlog-tarefas.md, backlog-kanban.md). Papel: Engenheiro DevOps (siga .github/agents/ correspondente se existir). Antes de tudo rode `git merge --ff-only main` no worktree.

Contexto: o risco R-25 (00_docs/projeto/riscos.md) registra que a T102 passou o `client_max_body_size` padrão do nginx a `1m` em 05_infra/nginx/nginx.conf (linha ~33) e liberou `40m` só para `location ~ ^/api/v1/fotos/upload(-clipboard)?$` (linha ~95). O POST de documento de edificação aceita até 25 MiB (04_backend/app/api/v1/edificacoes.py, constante perto da linha 35) e, atrás desse nginx, recebe 413. A stack VPS (05_infra/docker-compose.prod.yml) é caminho alternativo; a produção oficial é o PC (DEC-57), sem nginx, então a mudança é de baixo risco e só vale para o fallback.

Tarefa: (1) Leia edificacoes.py e descubra o caminho exato (método e rota) do upload de documento e o limite real em bytes; não suponha. (2) Em 05_infra/nginx/nginx.conf adicione uma `location` com regex específica para essa rota, com `client_max_body_size` ligeiramente acima do limite do backend (ex.: 30m), copiando as diretivas de proxy (proxy_pass, headers, timeouts) da location `/api/` ou da de upload de fotos — não duplique de forma divergente e mantenha a ordem para que a regex vença a `/api/` prefixada. Não aumente o padrão global de 1m. (3) Valide a sintaxe com `docker run --rm -v <caminho absoluto de 05_infra/nginx/nginx.conf>:/etc/nginx/nginx.conf:ro nginx:1.27-alpine nginx -t` (o Docker fica em C:/Program Files/Docker/Docker/resources/bin; se o nginx.conf referenciar certificados/upstream inexistentes no teste, monte stubs temporários FORA do repositório, no scratchpad, ou registre a limitação). Se o Docker não estiver no ar, registre que `nginx -t` não rodou. (4) Registre no Doc: rota, limite, diff resumido, saída do `nginx -t`. Proponha no Doc (não em riscos.md) o fechamento do R-25. Nenhum teste Python é necessário; não toque em 04_backend.
```

### T109 · Portal do Cliente: sinalizar a versão vigente de cada relatório na listagem (fecha o xfail da T51)
- **Status:** done
- **Origem:** T51
- **Papel:** Engenheiro Backend
- **Depende:** —
- **Ambiente:** docker
- **Dificuldade:** media
- **Toca:** 04_backend/app/services/portal_service.py, 04_backend/app/schemas/portal.py, 04_backend/tests/test_portal_versoes_relatorio.py, 00_docs/backlog-auto/portal-versao-vigente.md
- **Doc:** 00_docs/backlog-auto/portal-versao-vigente.md
- **Pronto:** GET /api/v1/portal/relatorios devolve, em cada item, um booleano `vigente` verdadeiro só para a maior `versao` de cada par (inspecao_id, tipo); o teste `test_listagem_sinaliza_qual_versao_e_a_vigente` perde o `xfail` e passa; demais testes de test_portal_versoes_relatorio.py e test_portal_cliente.py continuam verdes; sem migration (campo calculado); pytest -k portal e ruff check . verdes com PostgreSQL localhost:5433.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md (raiz) e as regras do projeto: comandos Python a partir de 04_backend/ no venv 04_backend/.venv, banco isolado garra_engenharia_test, commits Conventional Commits com escopo 'feat(backend)' e rodapé 'Refs T51', sem push, sem tocar nas branches main_back/main_front/staging_back/staging_front, sem editar documentos de gestão compartilhados. Papel: Engenheiro Backend. Antes de tudo rode `git merge --ff-only main`.

Contexto: a T51 criou 04_backend/tests/test_portal_versoes_relatorio.py com um `xfail(strict=True)` em `test_listagem_sinaliza_qual_versao_e_a_vigente` (linhas ~135-145): a listagem do Portal do Cliente (rota `GET /portal/relatorios` em 04_backend/app/api/v1/portal.py, lógica em `portal_service.listar_relatorios`) devolve V01 e V02 em pé de igualdade, sem distinguir a vigente (DEC-48 P1; a unicidade `(inspecao_id, tipo, versao)` já existe via migration da T49). Veja 00_docs/backlog-auto/portal-versoes-relatorio.md. O teste aceita o campo `vigente` ou `mais_recente`; use `vigente`.

Tarefa: (1) Leia portal_service.listar_relatorios, o schema de resposta do portal (localize com Grep por 'RelatorioPortal' em 04_backend/app/schemas) e o teste. (2) Acrescente ao schema o campo `vigente: bool` calculado no serviço: vigente = a versão máxima do mesmo (inspecao_id, tipo) entre os relatórios visíveis a esse cliente (calcule em Python sobre a lista já filtrada por `Responsavel.usuario_id`, sem nova query e sem vazar versões de outro contratante). Não mude a ordenação nem o filtro existentes e não altere o download. (3) Remova o `xfail` do teste, ajuste-o só se necessário (sem enfraquecer a asserção) e acrescente testes: dois tipos distintos na mesma inspeção têm cada um sua vigente; relatório com uma só versão é vigente. (4) Verifique se o frontend consome o tipo (Grep 'portal/relatorios' em 03_frontend); NÃO altere o frontend — apenas registre no Doc, como proposta, o uso do campo (selo 'vigente') em 03_frontend/app/portal/documentos/page.tsx. (5) Rode `pytest -k portal` e `ruff check .` com PostgreSQL localhost:5433 (suba via docker compose em 05_infra se necessário; se não for possível, registre que não rodou). (6) Registre resultado e saída dos testes no Doc.
```

---

## Bloco GL — Go-live no Render + GitHub Pages (DEC-59)

Alvo: backend e banco no Render (Dockerfile.render), front estático no GitHub Pages com NEXT_PUBLIC_API_URL fixa. Sem Neon, sem PC local. Push e painel do Render ficam para uma pessoa.

### T110 · Go-live: backend verde (pytest + ruff) e prontidão de produção
- **Status:** done
- **Origem:** DEC-59
- **Papel:** Engenheiro Backend
- **Depende:** —
- **Ambiente:** docker
- **Dificuldade:** alta
- **Toca:** 04_backend/app, 04_backend/tests, 04_backend/.env.example, 00_docs/backlog-auto/golive-backend.md
- **Doc:** 00_docs/backlog-auto/golive-backend.md
- **Pronto:** `pytest` e `ruff check .` em 04_backend verdes (ou falhas restantes listadas com causa); com ENVIRONMENT=production o app sobe com RUN_MIGRATIONS_ON_STARTUP=true e STORAGE_PROVEDOR=local em diretório configurável por env (documentado em .env.example); `GET /health` responde; Doc lista as variáveis obrigatórias do Render.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md e as regras do projeto (sem push, commits Conventional Commits com 'Refs DEC-59'). Papel: Engenheiro Backend. Rode `git merge --ff-only main` primeiro.
Contexto: go-live amanhã no Render (Dockerfile.render, disco persistente montado, STORAGE_PROVEDOR=local ou s3) com front no GitHub Pages. Tarefa: (1) suba o PostgreSQL de 05_infra (localhost:5433) e rode pytest e ruff em 04_backend no banco garra_engenharia_test; corrija falhas reais do código (não enfraqueça testes) ou liste as que são de ambiente Windows. (2) Confirme em app/core/config.py e app/main.py que: ENVIRONMENT=production valida JWT/CORS, migrations rodam com RUN_MIGRATIONS_ON_STARTUP=true, e o diretório do storage local vem de variável de ambiente (se for fixo, torne configurável com padrão atual; documente em .env.example). (3) Confirme que /health funciona sem auth e que o seed do admin roda no boot ou documente o comando. (4) Registre no Doc a lista exata de variáveis de ambiente do Render (obrigatórias/opcionais) e o resultado dos testes.
```

### T111 · Go-live: frontend verde (lint, build, testes) com API fixa do Render
- **Status:** done
- **Origem:** DEC-59
- **Papel:** Engenheiro Frontend
- **Depende:** —
- **Ambiente:** offline
- **Dificuldade:** media
- **Toca:** 03_frontend, 00_docs/backlog-auto/golive-frontend.md
- **Doc:** 00_docs/backlog-auto/golive-frontend.md
- **Pronto:** `npm run lint`, `npm run test:unit` e `npm run build` em 03_frontend verdes com NEXT_PUBLIC_API_URL=https://garra-backend.onrender.com/api/v1 e NEXT_PUBLIC_BASE_PATH=/garra-engenharia (sem NEXT_PUBLIC_API_DISCOVERY_URL); `out/` gerado; o front usa a API fixa e NUNCA entra em modo leitura quando a URL fixa está definida; login e rotas principais funcionam sob o basePath; Doc registra comandos e saída.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md e as regras do projeto (sem push, 'Refs DEC-59'). Papel: Engenheiro Frontend. Rode `git merge --ff-only main` primeiro. Em bash use MSYS_NO_PATHCONV=1 ao passar NEXT_PUBLIC_BASE_PATH (senão o Git Bash converte /garra-engenharia em caminho do Windows); o build pode demorar vários minutos no OneDrive: rode em background com timeout alto.
Tarefa: valide o front para o go-live no GitHub Pages com API fixa (lib/api-client.ts e lib/api-descoberta.ts). Rode lint, test:unit e build conforme o Pronto; corrija erros reais. Confirme que links, assets e service worker respeitam o basePath. Registre no Doc o resultado e o tamanho de out/.
```

### T112 · Go-live: runbook, checklist e script de smoke-test pós-deploy
- **Status:** done
- **Origem:** DEC-59
- **Papel:** Engenheiro DevOps
- **Depende:** —
- **Ambiente:** offline
- **Dificuldade:** media
- **Toca:** 00_docs/backlog-auto/golive-runbook.md, 05_infra/smoke/smoke.sh, 05_infra/.env.render.example
- **Doc:** 00_docs/backlog-auto/golive-runbook.md
- **Pronto:** runbook com passos numerados (dump do banco, env do Render, serviço Docker apontando para a branch main e Dockerfile.render, Render Disk persistente em STORAGE, Pages com Source=GitHub Actions e variável de repositório API_URL_PROD, CORS com https://rafaelroriz-age.github.io, rollback); .env.render.example sem segredos; smoke.sh (curl, parametrizado por API_URL, ADMIN_EMAIL e ADMIN_SENHA lidos de variáveis) testa /health, login, listagem e CORS preflight, saindo com código != 0 em falha, validado com `bash -n`.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md (sem push, 'Refs DEC-59'). Papel: Engenheiro DevOps. Rode `git merge --ff-only main` primeiro. Leia .github/workflows/deploy-pages.yml, 04_backend/Dockerfile.render, 04_backend/.env.example e 00_docs/backlog-auto/aposentar-render.md. O render.yaml antigo está em `git show 20930f5^:render.yaml`: use como referência de variáveis (sem recriar o arquivo na raiz; se útil, crie 05_infra/render.yaml.example). Produza os arquivos do Pronto. Não escreva segredos. Não chame o Render nem a rede.
```

### T113 · Go-live: enviar main para origin e acompanhar CI, Pages e sync de main_back
- **Status:** done
- **Origem:** DEC-59
- **Papel:** Engenheiro DevOps
- **Depende:** T110, T111, T112
- **Ambiente:** offline
- **Dificuldade:** media
- **Toca:** 00_docs/backlog-auto/golive-envio.md
- **Doc:** 00_docs/backlog-auto/golive-envio.md
- **Pronto:** a `main` local foi enviada à origin (sem --force); `git rev-list --count origin/main..main` = 0; workflows ci.yml, deploy-pages.yml e sync-deploy-branches.yml acompanhados com `gh run list` e `gh run watch`, status final no Doc; main_back contém main; falhas de CI causadas pelo código corrigidas em commits pequenos e reenviadas.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md. Papel: Engenheiro DevOps. O DONO AUTORIZOU explicitamente, nesta tarefa e só nela, enviar a branch main à origin (comando `git push origin main`, sem --force) e liberou a barreira com BACKLOG_ESCRITA=1. Passos: `git status` limpo; revise `git log origin/main..main --oneline`; confirme que não há .env, chaves ou dumps no diff; envie a main; acompanhe ci.yml, deploy-pages.yml e sync-deploy-branches.yml (a mudança em sync-deploy-branches.yml propaga main para main_back via API de merge). Se o Pages falhar porque Source não está em GitHub Actions, registre como ação humana. Se o sync reportar conflito, registre no Doc. Corrija falhas de CI causadas pelo código e reenvie. Nunca toque em main_front/staging_*, nunca force, não mexa no Render.
```

### T114 · Go-live: reproduzir e deixar verdes os jobs E2E e Trivy do CI
- **Status:** doing
- **Origem:** T113
- **Papel:** Engenheiro DevOps
- **Depende:** —
- **Ambiente:** docker
- **Dificuldade:** alta
- **Toca:** .github/workflows/ci.yml, 03_frontend/e2e, 04_backend/Dockerfile, 04_backend/requirements.txt, 00_docs/backlog-auto/golive-ci-e2e-trivy.md
- **Doc:** 00_docs/backlog-auto/golive-ci-e2e-trivy.md
- **Pronto:** os jobs `e2e` e `docker-build-scan` do ci.yml foram reproduzidos localmente; falhas causadas pelo código ou pelo workflow corrigidas; o que não puder ser reproduzido está registrado no Doc com a causa.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md. Papel: Engenheiro DevOps. Não envie nada à origem. Contexto: esses dois jobs vinham sendo pulados porque o backend falhava (veja 00_docs/backlog-auto/golive-envio.md), e agora o sync para main_back só roda com o CI verde. Leia .github/workflows/ci.yml, reproduza `docker-build-scan` (build e Trivy com a mesma severidade) e `e2e` com containers descartáveis, corrija o que for defeito real sem silenciar achados nem enfraquecer testes (se um achado do Trivy não tiver correção, registre e proponha a exceção no Doc). Registre comandos e saídas no Doc.
```

### T115 · Go-live: conferir variáveis de ambiente entre config.py, exemplo do Render e runbook
- **Status:** doing
- **Origem:** DEC-59
- **Papel:** Engenheiro DevOps
- **Depende:** —
- **Ambiente:** offline
- **Dificuldade:** baixa
- **Toca:** 05_infra/.env.render.example, 00_docs/backlog-auto/golive-runbook.md, 00_docs/backlog-auto/golive-env-checklist.md
- **Doc:** 00_docs/backlog-auto/golive-env-checklist.md
- **Pronto:** toda variável obrigatória em produção de app/core/config.py e do golive-backend.md consta no .env.render.example e no runbook; divergências corrigidas e listadas no Doc, incluindo SEED_ON_STARTUP e ADMIN_SENHA.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md. Papel: Engenheiro DevOps. Compare 04_backend/app/core/config.py, 04_backend/render-start.sh, 00_docs/backlog-auto/golive-backend.md (seção 5), 05_infra/.env.render.example e 00_docs/backlog-auto/golive-runbook.md. Corrija só o exemplo e o runbook, sem segredos. O serviço do Render observa a branch main_back. Registre o resultado no Doc.
```

### T116 · Portal do Cliente: selo "vigente" na lista de documentos
- **Status:** doing
- **Origem:** T109
- **Papel:** Engenheiro Frontend
- **Depende:** —
- **Ambiente:** offline
- **Dificuldade:** baixa
- **Toca:** 03_frontend/app/portal, 03_frontend/lib, 00_docs/backlog-auto/portal-selo-vigente.md
- **Doc:** 00_docs/backlog-auto/portal-selo-vigente.md
- **Pronto:** a página de documentos do portal mostra um selo quando o item vem com `vigente: true`; `npm run lint`, `npm run test:unit` e `npm run build` verdes.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md. Papel: Engenheiro Frontend. GET /portal/relatorios agora devolve `vigente` (00_docs/backlog-auto/T109-portal-versao-vigente.md). Em 03_frontend/app/portal/documentos/page.tsx e no tipo correspondente, mostre um selo 'Vigente' reaproveitando os componentes existentes, sem mudar regras nem ordenação. Em Git Bash use MSYS_NO_PATHCONV=1 se definir NEXT_PUBLIC_BASE_PATH. Registre no Doc.
```

### T117 · Compose de produção (VPS): validar o YAML e fechar o R-16
- **Status:** doing
- **Origem:** R-16
- **Papel:** Engenheiro DevOps
- **Depende:** —
- **Ambiente:** docker
- **Dificuldade:** baixa
- **Toca:** 05_infra/docker-compose.prod.yml, 05_infra/README.md, 00_docs/backlog-auto/compose-prod-yaml.md
- **Doc:** 00_docs/backlog-auto/compose-prod-yaml.md
- **Pronto:** `docker compose -f docker-compose.prod.yml config -q` passa com variáveis de teste; Doc propõe o fechamento do R-16 ou descreve o erro restante.
- **Prompt:**
```text
Siga a 'Regra de pronto' do BACKLOG.md. Papel: Engenheiro DevOps. Leia o R-16 em 00_docs/projeto/riscos.md. Valide 05_infra/docker-compose.prod.yml com `docker compose ... config -q` usando variáveis de teste fora do repositório, sem subir containers. Corrija se preciso e ajuste a nota correspondente no 05_infra/README.md. Não edite riscos.md. Registre no Doc.
```
