# Prompts padrão do backlog-auto

Prompts para colar numa sessão do Claude Code aberta **na raiz do projeto**. Cada um é independente e segue a ordem de uso:
1 → 2 → 3 → 4 → 5. Os trechos entre `<...>` são o que você troca.

Caminho do módulo nesta máquina: `C:\Users\dynatest\OneDrive - Dynatest Engenharia\Área de Trabalho\Novos_proj\backlog-auto`

---

## 1. Instalar o módulo (uma vez por máquina)

```text
Instale o módulo backlog-auto nesta máquina com `pip install -e "C:\Users\dynatest\OneDrive - Dynatest Engenharia\Área de Trabalho\Novos_proj\backlog-auto"`. Depois confirme que `backlog-auto --help` funciona e que o `python` do PATH é o mesmo em que o módulo foi instalado (`python -c "import backlog_auto"`). Se não for, diga qual comando usar. Não altere nenhum arquivo do projeto.
```

## 2. Integrar o módulo ao projeto

```text
Integre o backlog-auto a este projeto. Siga esta ordem e pare se algum passo falhar:
1. Confirme que é um repositório git e em qual branch estamos (a principal deve ser <main>). Se não houver git, avise e pare.
2. Rode `backlog-auto init`. Não use --force.
3. Edite o backlog.toml para este projeto: `nome`, `branch_principal`, `ambientes` (liste os que existem aqui, por exemplo offline, banco, api, humano), `regras_extras` (regras que valem para toda tarefa: onde a documentação fica, o que nunca pode ser alterado) e os padrões do `[guard]` conforme o que o projeto tem de dados sensíveis. Em `[preparo]`, ajuste `pasta_docs` à pasta de documentação que o projeto já usa e preencha `objetivo` com: "<objetivo do sistema em uma ou duas frases, ou deixe vazio para inferir>".
4. Procure no projeto, sob qualquer nome, os arquivos que dizem como trabalhar nele e como documentar: AGENTS.md, CLAUDE.md, CONTRIBUTING, LEIA-ME, README de índice, guias, manuais, planos, "regra de documentação" ou "definição de pronto", em qualquer pasta (docs, docs_*, wiki, notas) e idioma. Não dependa do nome: busque pelo conteúdo (palavras como documentação, registrar, decisões, backlog, índice, pronto). Para cada um que achar, acrescente a `regras_extras` as regras dele, em frases curtas e com o caminho do arquivo (por exemplo "Registre decisões em docs/decisoes.md; novo doc entra no índice docs/LEIA-ME.md"), em vez de duplicar o texto. Ajuste `[preparo] pasta_docs` para a pasta onde essa documentação já vive e liste na resposta o que encontrou e como cada achado virou regra. Se não achar nada, diga isso.
5. Rode `backlog-auto validar` e `backlog-auto doctor` e corrija o que for FALHA.
6. Faça `git add -A` e um commit "backlog-auto: integração". Não faça push.
Ao final, liste o que foi criado e o que ficou para eu fazer à mão.
```

## 3. Escrever o backlog do projeto

```text
Leia o projeto (estrutura, código, testes, README, issues e TODOs) e substitua as tarefas de exemplo do BACKLOG.md por tarefas reais para: <objetivo da rodada, por exemplo "cobrir os módulos X e Y com testes e corrigir os bugs listados em TODO">.
Regras:
- Uma tarefa por sessão: pequena o bastante para caber numa sessão e com critério `Pronto` verificável.
- Preencha todos os campos: Status (todo), Papel, Depende, Ambiente (um dos de backlog.toml), Dificuldade (baixa, media ou alta), Toca, Doc, Pronto e Prompt.
- `Toca` lista os arquivos e pastas que a tarefa escreve. Tarefas que não dependem uma da outra e não compartilham `Toca` rodam em paralelo; use isso, mas nunca deixe duas tarefas paralelas editarem o mesmo arquivo.
- Cada Prompt é autossuficiente (a sessão não vê esta conversa), cita os arquivos que deve ler e termina com: Siga a "Regra de pronto" do BACKLOG.md.
- Não crie tarefas de preparo da documentação: o D01..D05 é inserido pelo módulo.
- Tarefas que exigem decisão ou ação humana vão com Ambiente `humano` e só preparam material.
Rode `backlog-auto validar` até passar e `backlog-auto next` para me mostrar o primeiro lote. Faça commit do BACKLOG.md. Não dispare nada.
```

## 4. Pré-voo antes de rodar

```text
Faça o pré-voo do backlog-auto sem disparar nada: rode `backlog-auto doctor` e `backlog-auto run --dry`. Explique cada FALHA e AVISO e como resolver. Confirme se a branch principal está limpa e commitada. Lembre-me do que só eu posso fazer: rodar `claude --dangerously-skip-permissions` uma vez nesta pasta, aceitar os dois avisos e sair com /exit. Mostre o lote (tarefas, modelo, teto de gasto) e o custo máximo somado.
```

## 5. Iniciar a execução

```text
Inicie a execução automática do backlog-auto neste projeto:
1. Se `git status` tiver mudanças, pare e me diga (o módulo precisa da principal limpa).
2. Rode `backlog-auto auto --intervalo 120`. Ele começa pelo preparo da documentação (D01..D05) e só depois libera as tarefas do backlog.
3. Enquanto roda, a cada rodada mostre `backlog-auto status` resumido: concluídas, em andamento, esperando aprovação e bloqueadas.
4. Se parar, explique por quê (esperando aprovação, bloqueada, conflito de merge ou fim) e proponha a ação, sem resolver conflitos de merge nem editar o BACKLOG.md à mão.
Não faça push em nenhum momento.
```

---

## Uso do dia a dia

### Acompanhar

```text
Mostre o andamento do backlog-auto: rode `backlog-auto status`, `claude agents` e `git log --oneline -15`. Resuma o que terminou, o que está rodando, o que espera aprovação (com o comando `claude attach` de cada uma) e o que está bloqueado, com o motivo provável.
```

### Fechamento de lote

```text
Rode `git status` e `git log` para ver o que o último lote mudou. Para cada tarefa concluída, atualize a documentação do projeto (índice, plano, decisões) com os fatos novos e confira se o BACKLOG.md reflete os status reais (`backlog-auto list`). Não altere código.
```

### Tarefa bloqueada ou sessão que terminou sem commit

```text
A tarefa <Txx> ficou blocked. Veja `claude logs` da sessão backlog-<Txx> e o worktree em .claude/worktrees/backlog-<Txx>. Diga por que não produziu mudanças, proponha um Prompt melhor para ela e, se eu aprovar, rode `backlog-auto set <Txx> todo` para ela tentar de novo.
```

### Conflito de merge ao colher

```text
O `backlog-auto colher` reportou conflito na tarefa <Txx>. Mostre os arquivos em conflito e as duas versões. Proponha a resolução e, só depois da minha aprovação, aplique-a, faça o merge manual e rode `backlog-auto set <Txx> done`. Depois ajuste o campo Toca das tarefas envolvidas para que não colidam de novo.
```

### Reavaliar a documentação depois de mudanças grandes

```text
O código mudou bastante desde a última documentação. Rode `backlog-auto preparo --refazer` e depois `backlog-auto auto` para reclassificar cada documento (efetiva, parcial, refazer, ausente) e refazer só o que ficou desatualizado. Ao final, resuma o `04_relatorio.md`.
```

### Adicionar uma nova rodada de tarefas

```text
Acrescente ao BACKLOG.md uma nova rodada de tarefas para: <objetivo>. Mantenha as já concluídas, use ids novos em sequência, preencha todos os campos e valide com `backlog-auto validar`. Mostre o lote com `backlog-auto next` e faça commit. Não dispare.
```

### Adaptar o guard a um novo tipo de risco

```text
Este projeto lida com <banco/serviço/arquivos sensíveis>. Revise a seção [guard] do backlog.toml: escolha os presets (sql, delta, destrutivo), ajuste `comando_gatilho` e acrescente em [guard.padroes] regex próprias para o que nunca pode ser alterado. Teste cada regex com `python -c "from backlog_auto import guard, config; ..."` contra um exemplo que deve bloquear e um que deve passar. Lembre-me de que o guard lê só o texto dos comandos e arquivos, não escrita montada em tempo de execução.
```

---

## Observações

- Cada sessão de tarefa roda em background num worktree isolado e **não vê estas conversas**: tudo de que precisa está no `Prompt` da tarefa e no `backlog.toml`.
- O `auto` nunca faz push. Os commits são locais.
- Nunca edite o `BACKLOG.md` enquanto o `auto` roda, a não ser pelo `backlog-auto set`: o integrador também escreve nele.
