# Manual do backlog automatizado

Como o fluxo de tarefas deste projeto funciona, como iniciar, acompanhar, parar e consertar. Configuração em `backlog.toml`; fila em `BACKLOG.md`.

## 1. Como funciona

```text
BACKLOG.md ──► backlog-auto run ──► uma sessão `claude --bg` por tarefa ──► commit no worktree
 (fila)         (escolhe o lote)      (worktree + modelo próprios)               │
    ▲                                                                            ▼
    └─────── marca done ◄──── backlog-auto colher ◄── merge na principal ◄───────┘
                                     ▲
                   `auto` = colher + run em loop até acabar
```

- **Lote:** `run` pega as tarefas `todo` cujas dependências estão `done` e escolhe as que não tocam nos mesmos arquivos (`Toca`), para rodarem em paralelo sem conflito.
- **Sessão:** cada tarefa roda em `.claude/worktrees/backlog-Txx` (branch `worktree-backlog-Txx`). O agente trabalha, testa, documenta e faz commit lá.
- **Colheita:** `colher` integra na branch principal o que terminou e marca `done`. Só com `done` as dependentes são liberadas.
- **Modelo por dificuldade:** o campo `Dificuldade` escolhe modelo, esforço e teto de gasto (tabela `[rota.*]` do `backlog.toml`). `--model X` força um modelo para o lote.

## 2. Regras

1. As sessões rodam sem aprovação manual (`bypassPermissions`) e fazem commit local. **Nunca fazem push.**
2. **Barreira de dados (`[guard]`):** um hook bloqueia código e comandos que alterem ou apaguem dados existentes (presets `sql`, `delta`, `destrutivo` e padrões próprios). Só uma pessoa libera, definindo a variável de `variavel_liberacao` como `1`. Limite: o guard lê o texto, não pega escrita montada dinamicamente em tempo de execução.
3. Agentes não editam o `BACKLOG.md`: o status só muda por `run`, `colher` ou `set`.
4. A "Regra de pronto" e o "Fechamento de lote" estão no topo do `BACKLOG.md`. Rode o fechamento depois de cada lote.
5. Ações visíveis a terceiros (e-mail, mensagem, PR, push) ficam para uma pessoa.

## 3. Pré-requisitos (uma vez por projeto)

```text
pip install -e <caminho>/backlog-auto      # uma vez por máquina
backlog-auto init                          # na raiz do projeto: cria backlog.toml, BACKLOG.md, este manual e os hooks
git add -A; git commit -m "backlog-auto"   # o integrador precisa do backlog versionado
claude --dangerously-skip-permissions      # na raiz: aceite a confiança da pasta e o aviso do modo sem aprovação; saia com /exit
backlog-auto doctor                        # confere tudo
```

Sem os dois avisos aceitos, os disparos falham e nada fica marcado como `doing`. Antes de colher, a branch principal precisa estar sem mudanças não commitadas.

## 4. Como começar

```text
backlog-auto validar     # confere campos, dependências e ciclos
backlog-auto run --dry   # mostra o lote, o modelo e o teto de cada tarefa; não dispara nada
backlog-auto auto        # totalmente automático (colher + run em loop)
```

Com `[preparo] ativo = true`, o primeiro `run`/`auto` começa pelo **preparo da documentação** (D01..D05: mapear o sistema, inventariar e classificar a documentação, criar ou refazer, verificar). As tarefas T só são liberadas quando ele termina; `backlog-auto preparo --refazer` reavalia depois.

Passo a passo: `backlog-auto run`, e depois `backlog-auto colher`. `--ambiente X` filtra por ambiente. `auto --max-rodadas N` limita as rodadas.

## 5. Como saber se está rodando

| Pergunta | Comando |
|---|---|
| Sessões ativas e estado | `claude agents` (`--json` em script) |
| O que uma sessão faz | `claude logs <id>` |
| Entrar nela | `claude attach <id>` |
| Painel por bloco (gera o arquivo de progresso) | `backlog-auto status` |
| Status de cada tarefa | `backlog-auto list` |
| O que está liberado | `backlog-auto next` |
| O prompt de uma tarefa | `backlog-auto show T01` |

Estados da sessão: `busy` (trabalhando), `idle` (terminou o turno; o `colher` integra), `waiting` (travada num pedido de permissão: `claude attach <id>` e aprovar, ou reiniciar).
Status da tarefa: `todo`, `doing` (sessão disparada), `done` (integrada), `blocked` (terminou sem mudança, ou parada à mão).

## 6. Como parar

| Quero | Comando |
|---|---|
| Parar o `auto` (as sessões continuam) | `Ctrl+C` |
| Parar uma sessão | `claude stop <id>` |
| Parar e apagar sessão e worktree | `claude rm <id>` |
| Devolver a tarefa à fila | `backlog-auto set T07 todo` |

**Reiniciar tarefas travadas** (sessão que morreu, ficou `waiting`, `blocked` ou terminou sem commit):

```text
backlog-auto restart --dry       # mostra o que seria reiniciado
backlog-auto restart             # reinicia as doing/blocked que NÃO estão trabalhando
backlog-auto restart T18 T20     # reinicia só essas
backlog-auto restart --auto      # reinicia e já retoma o fluxo automático
```

O `restart` encerra a sessão, apaga o worktree e o branch, devolve a tarefa para `todo` e commita o backlog. O trabalho parcial é descartado (ele avisa quantos commits não integrados serão perdidos). Sessões `busy` são poupadas, a menos que você cite o id ou use `--forcar`. Tarefa `done` não pode ser reiniciada.

## 7. Problemas comuns

| Sintoma | Causa e solução |
|---|---|
| `Workspace not trusted` | Faltou aceitar a confiança da pasta (seção 3). |
| `--bg with bypassPermissions requires accepting the disclaimer` | Faltou aceitar o aviso do modo sem aprovação (seção 3). |
| `Nenhuma tarefa liberada` | As `todo` dependem de tarefas ainda não `done`, ou a que bloqueia está `doing`. Rode `colher`. |
| `auto` parou dizendo que há tarefas esperando/bloqueadas | Veja `backlog-auto status`; aprove a sessão `waiting` ou reinicie a `blocked`. |
| `colher`: "terminou sem nenhuma mudança" | A sessão acabou sem commit; a tarefa vira `blocked`. Veja `claude logs`, depois reinicie. |
| `colher`: "mudanças não commitadas" | Commite ou guarde (`git stash`) e rode de novo. |
| `colher`: "conflito" | O merge foi cancelado e a tarefa segue `doing`. Resolva com `git merge worktree-backlog-Txx` e `backlog-auto set Txx done`. |
| Hook bloqueou um comando | Falso positivo comum (texto de teste com SQL, por exemplo). Reescreva, ajuste `comando_gatilho`/`isentos` ou peça a uma pessoa. |
| Hook não dispara | `python -m backlog_auto` precisa funcionar no `python` do PATH (`backlog-auto doctor` confere). |

## 8. Adaptar ao projeto

Tudo se adapta em `backlog.toml`: `ambientes`, `[rota.*]` (modelos e tetos), `[agente].regras_extras` (regras que entram em todo prompt), `[guard]` (presets, `padroes` próprios, `comando_gatilho`, `isentos`) e `[lembrete]`. Os papéis e documentos são livres: escreva-os nos campos `Papel`, `Doc` e nos prompts.
