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
- **Status:** doing
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
- **Status:** doing
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
- **Status:** doing
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
- **Status:** todo
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
