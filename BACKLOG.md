# Backlog executável — Garra Engenharia — Automação de Relatórios Prediais

Cada tarefa vira uma sessão em background do Claude Code. O bloco `Prompt` é copiável como está.
Comandos: `backlog-auto list`, `backlog-auto next`, `backlog-auto run`, `backlog-auto auto`. Manual: [00_docs/backlog-auto/BACKLOG-MANUAL.md](00_docs/backlog-auto/BACKLOG-MANUAL.md).

**Campos:** `Status` (todo, doing, done, blocked) · `Papel` (livre) · `Depende` (ids que precisam estar `done`, ou `—`) · `Ambiente` (veja `ambientes` em backlog.toml) · `Dificuldade` (baixa, media, alta: define modelo e teto de gasto) · `Toca` (arquivos/pastas que a tarefa escreve; tarefas com `Toca` sobreposto nunca rodam juntas) · `Doc` (onde registrar o resultado) · `Pronto` (critério verificável).

## Regra de pronto (vale para toda tarefa)

1. Com código: testes verdes, com testes novos para o que foi criado (`pytest` + `ruff check .` em `04_backend`; `npm run lint` + `npm run build` em `03_frontend`), como no checklist de `.github/pull_request_template.md`.
2. Registrar o resultado no doc indicado em `Doc` (fatos, números, caminhos, comandos e saída dos testes); decisão nova vai como proposta no `Doc`, não direto em `00_docs/projeto/decisoes.md`.
3. Em lote paralelo, **não editar este arquivo**: o status é atualizado por `backlog-auto`.
4. Nunca alterar nem apagar dados existentes; ler é livre (barreira configurada em `[guard]`).

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
- **Status:** doing
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
- **Status:** doing
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
- **Status:** doing
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
