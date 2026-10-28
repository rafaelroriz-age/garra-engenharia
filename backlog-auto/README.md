# backlog-auto

Backlog em Markdown executado por sessões em background do Claude Code: escolhe o lote que pode rodar em paralelo, dispara uma sessão por tarefa (modelo e teto de gasto pela dificuldade), integra o resultado na branch principal e mantém um painel de progresso. Inclui uma barreira configurável contra alteração de dados existentes.

Extraído do projeto ALS OilModel. Só usa a biblioteca padrão do Python (3.11+) e o CLI `claude`.

## Instalar (uma vez por máquina)

```powershell
pip install -e "C:\Users\dynatest\OneDrive - Dynatest Engenharia\Área de Trabalho\Novos_proj\backlog-auto"
```

O modo editável faz toda atualização do módulo valer em todos os projetos. Os hooks usam `python -m backlog_auto.hooks`, então o `python` do PATH precisa ser o mesmo em que o módulo foi instalado (o `doctor` confere).

## Usar num projeto novo

```powershell
cd <raiz-do-projeto>            # precisa ser um repositório git
backlog-auto init               # cria backlog.toml, BACKLOG.md, docs/BACKLOG-MANUAL.md, hooks e .gitignore
# edite backlog.toml e escreva as tarefas no BACKLOG.md
backlog-auto validar            # campos, dependências, ciclos
git add -A; git commit -m "backlog-auto"
claude --dangerously-skip-permissions    # uma vez por pasta: aceite a confiança e o aviso; saia com /exit
backlog-auto doctor
backlog-auto run --dry          # confere o lote
backlog-auto auto               # roda tudo
```

`docs/CELULAR.md` traz o guia para operar pelo celular (comandos para colar e o prompt de fechamento de lote).

O manual completo do dia a dia (acompanhar, parar, reiniciar, erros comuns) é copiado para `docs/BACKLOG-MANUAL.md` de cada projeto.

Prompts prontos para integrar o módulo a um projeto e iniciar a execução: [docs/PROMPTS.md](docs/PROMPTS.md).

## Comandos

| Comando | Faz |
|---|---|
| `init [pasta] [--nome N] [--force] [--sem-guard] [--sem-lembrete]` | Instala o sistema (não sobrescreve arquivos existentes sem `--force`; hooks e `.gitignore` são mesclados) |
| `doctor` | Diagnostica Python, CLI, git, backlog, hooks |
| `validar` | Confere o backlog |
| `list`, `next [--prompts]`, `show Txx`, `set Txx status` | Consultar e alterar status |
| `run [--ambiente X] [--model M] [--dry]` | Dispara o próximo lote |
| `colher [--dry]` | Commita (se faltar), faz merge na principal, marca `done`, remove worktree e branch |
| `restart [Txx ...] [--dry] [--forcar] [--auto]` | Recomeça tarefas travadas: encerra a sessão, apaga worktree e branch, volta para `todo`. Sem ids, só as `doing`/`blocked` que não estão trabalhando |
| `fechar [--dry]` | Fechamento de lote: sessão `claude -p` atualiza a documentação (texto de "Fechamento de lote" do `BACKLOG.md`) num worktree próprio; o merge só acontece se não houver mudança em código (`[fechamento] proibidas_extensoes`) |
| `avancar [--ambiente X] [--sem-fechamento]` | Um passo: `colher`, `fechar` se o lote acabou, `run` do próximo lote |
| `auto [--ambiente X] [--intervalo S] [--max-rodadas N] [--sem-fechamento]` | `avancar` em loop; para sozinho quando acaba, quando só restam tarefas esperando/bloqueadas ou quando o fechamento falha |
| `status` | Regenera e imprime o painel de progresso |
| `preparo [--refazer]` | Insere a fase de preparo da documentação (D01..D05); `--refazer` volta tudo para `todo` e reclassifica |

## Fechamento de lote automático

O lote termina quando o `colher` integra a última tarefa `doing`. Cada tarefa integrada é anotada em `.claude/logs/fechamento_pendente.json`; com `[fechamento] ativo = true`, o próximo `avancar`/`auto` (ou um `fechar` manual) roda uma sessão de documentação **antes** de disparar o lote seguinte. As tarefas de preparo (D01..D05) não geram fechamento. Se a sessão falhar ou mexer em código, nada é integrado, a pendência continua e o `auto` para; corrija e rode `backlog-auto fechar`. `--sem-fechamento` ignora a etapa.

## Preparo da documentação (antes de tudo)

Com `[preparo] ativo = true` (padrão do `init`), o primeiro `run`/`auto` insere no backlog o bloco **D01..D05**, que roda como sessões em
background e **trava todas as outras tarefas até terminar**:

| Tarefa | Faz | Saída |
|---|---|---|
| D01 | Lê o sistema: objetivo (declarado em `[preparo] objetivo` ou inferido, com confiança), componentes, fluxo, como rodar e testar | `01_sistema.md` |
| D02 | Inventaria a documentação existente (ou declara que não há nenhuma) | `02_inventario.md` |
| D03 | Classifica cada documento: **efetiva**, **parcial**, **refazer** ou **ausente**, com evidência, e monta o plano de ação | `03_classificacao.md` |
| D04 | Cria o que falta e refaz o que não presta; documentos efetivos não são tocados; atualiza o índice e o README | `docs/` |
| D05 | Confere tudo contra o código (caminhos, links, comandos) e corrige | `04_relatorio.md` |

D01 e D02 rodam em paralelo. Sem documentação, D03 marca tudo como ausente e D04 cria do zero; com documentação, só o que foi
julgado ruim é refeito. Os arquivos de trabalho ficam em `[preparo] pasta_trabalho` (padrão `docs/_preparo`). Para reavaliar mais tarde
(depois de grandes mudanças no código): `backlog-auto preparo --refazer`. Para desligar: `ativo = false`.

## Formato da tarefa

```markdown
## Bloco A — Nome do bloco

### T07 · Título da tarefa
- **Status:** todo            # todo | doing | done | blocked
- **Papel:** livre
- **Depende:** T01, T02        # ou —
- **Ambiente:** offline        # um dos `ambientes` do backlog.toml
- **Dificuldade:** media       # baixa | media | alta (chaves de [rota.*])
- **Toca:** src/x.py, docs/y   # tarefas com Toca sobreposto nunca rodam juntas
- **Doc:** docs/y.md
- **Pronto:** critério verificável
- **Prompt:**
```text
Instrução completa e autocontida para a sessão.
```
```

## Adaptar a outro projeto (`backlog.toml`)

| Quero | Mexo em |
|---|---|
| Outros ambientes (ex.: `banco`, `api`) | `ambientes` |
| Outros modelos ou tetos de gasto | `[rota.baixa|media|alta]` (`model`, `effort`, `budget` em US$) |
| Regras que entram em todo prompt (ex.: "não toque em produção") | `[agente].regras_extras` ou `preambulo` |
| Proteger outro tipo de dado | `[guard]`: `presets` (`sql`, `delta`, `destrutivo`), `padroes` próprios (regex), `comando_gatilho`, `isentos`, `variavel_liberacao` |
| Lembrete de documentação após editar código | `[lembrete]` (`texto`, `extensoes`, `execucao`) |
| Branch principal diferente de `main`, outros nomes de arquivo, prefixo de id | `[projeto]` |
| `claude` fora do PATH | `[projeto].claude_exe` ou variável `CLAUDE_EXE` |

Papéis e documentos são livres: ficam nos campos `Papel`, `Doc` e nos prompts.

## O que o integrador garante

- Cada tarefa roda num worktree próprio; nada vai para a principal sem passar pelo `colher`.
- Nunca faz push.
- O `colher` recusa rodar se a principal tiver mudanças não commitadas (o arquivo de progresso é ignorado nessa checagem) ou se a branch atual não for a principal.
- Conflito de merge só é resolvido sozinho nos arquivos de controle (backlog e progresso); qualquer outro conflito cancela o merge e deixa a tarefa `doing`.
- Sessão que termina sem nenhum commit vira `blocked` (para o `auto` não esperar para sempre).

## Limites

- O guard lê o **texto** de arquivos escritos e comandos; não detecta escrita montada em tempo de execução. É uma rede de proteção, não uma garantia: mantenha credenciais de produção fora do alcance dos agentes quando o dano for grave.
- Falso positivo existe: um arquivo que contém exemplos de SQL destrutivo (como testes) pode ser bloqueado. Ajuste `isentos` ou `comando_gatilho`.
- Depende dos comandos `claude --bg`, `-w`, `--effort`, `--max-budget-usd`, `agents --json`, `stop` e `rm` do CLI 2.1.x; se uma versão futura mudar essas flags, ajuste `comando_sessao` em `runner.py`.
- Em Windows, `.claude/worktrees` dentro do OneDrive pode travar a remoção de pastas; se acontecer, `claude rm <id>` com a sessão parada resolve.

## Testes

```powershell
cd backlog-auto; pip install -e ".[dev]"; python -m pytest
```

Os testes cobrem parser, lotes, validação, rota de modelos, guard, hooks, `init` e o `colher` com repositórios git reais (a chamada ao `claude` é simulada).
