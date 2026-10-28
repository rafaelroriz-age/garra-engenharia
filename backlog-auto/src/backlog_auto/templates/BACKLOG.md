# Backlog executável — {{nome}}

Cada tarefa vira uma sessão em background do Claude Code. O bloco `Prompt` é copiável como está.
Comandos: `backlog-auto list`, `backlog-auto next`, `backlog-auto run`, `backlog-auto auto`. Manual: [docs/BACKLOG-MANUAL.md](docs/BACKLOG-MANUAL.md).

**Campos:** `Status` (todo, doing, done, blocked) · `Papel` (livre) · `Depende` (ids que precisam estar `done`, ou `—`) · `Ambiente` (veja `ambientes` em backlog.toml) · `Dificuldade` (baixa, media, alta: define modelo e teto de gasto) · `Toca` (arquivos/pastas que a tarefa escreve; tarefas com `Toca` sobreposto nunca rodam juntas) · `Doc` (onde registrar o resultado) · `Pronto` (critério verificável).

## Regra de pronto (vale para toda tarefa)

1. Com código: testes verdes, com testes novos para o que foi criado.
2. Registrar o resultado no doc indicado em `Doc` (fatos, números, caminhos).
3. Em lote paralelo, **não editar este arquivo**: o status é atualizado por `backlog-auto`.
4. Nunca alterar nem apagar dados existentes; ler é livre (barreira configurada em `[guard]`).

## Fechamento de lote

Rodar depois que um lote terminar, antes do próximo:

```text
Rode `git status` e `git log` para ver o que o último lote mudou. Para cada tarefa concluída, atualize a documentação do projeto (índice, plano, decisões) com os fatos novos e confira se este backlog reflete os status reais (`backlog-auto list`). Não altere código.
```

---

## Bloco A — Exemplo

### T01 · Diagnosticar o ambiente
- **Status:** todo
- **Papel:** engenharia
- **Depende:** —
- **Ambiente:** offline
- **Dificuldade:** baixa
- **Toca:** docs/diagnostico.md
- **Doc:** docs/diagnostico.md
- **Pronto:** `docs/diagnostico.md` descreve versões, dependências e como rodar os testes.
- **Prompt:**
```text
Tarefa T01. Leia o README e a estrutura do projeto. Registre em docs/diagnostico.md as versões das ferramentas, as dependências principais e o comando que roda os testes, e rode os testes. Siga a "Regra de pronto" do BACKLOG.md.
```

### T02 · Cobrir o módulo principal com testes
- **Status:** todo
- **Papel:** engenharia
- **Depende:** T01
- **Ambiente:** offline
- **Dificuldade:** media
- **Toca:** src, tests
- **Doc:** docs/diagnostico.md
- **Pronto:** testes novos passando para o módulo principal.
- **Prompt:**
```text
Tarefa T02. Com base em docs/diagnostico.md, escreva testes para o módulo principal do projeto, rode a suíte e registre a cobertura obtida em docs/diagnostico.md. Siga a "Regra de pronto" do BACKLOG.md.
```
