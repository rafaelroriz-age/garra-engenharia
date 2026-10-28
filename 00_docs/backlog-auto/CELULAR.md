# Rodar pelo celular — Garra Engenharia — Automação de Relatórios Prediais

Guia curto. O manual completo está em [BACKLOG-MANUAL.md](BACKLOG-MANUAL.md).

## Antes de sair do PC

1. O PC precisa estar ligado, sem hibernar, com a sessão do Claude Code aberta na pasta do projeto (`Garra Engenharia — Automação de Relatórios Prediais`).
2. Confirme que a sessão aparece no app do celular (Claude, aba Code).
3. O GitHub só tem a versão enviada por `git push`. Se faltou push, o celular não vê os commits novos. Peça ao PC: "faça push da `main`" (só com sua confirmação).
4. Deixe a branch principal commitada: o `colher` recusa mudanças soltas quando `autocommit` está desligado.

## Comandos para colar na sessão

| O que quer | Cole isto |
|---|---|
| Ver o que está pronto | `backlog-auto list` |
| Ver o próximo lote | `backlog-auto next` |
| Ver o prompt de uma tarefa | `backlog-auto show T07` |
| Ver o painel | `backlog-auto status` |
| Ver como vai o lote | `claude agents` |
| Rodar tudo sozinho | `backlog-auto auto` |
| Integrar o que terminou | `backlog-auto colher` |
| Recomeçar tarefa travada | `backlog-auto restart T07` |
| Reavaliar a documentação | `backlog-auto preparo --refazer` e depois `backlog-auto auto` |
| Fechar um lote | o prompt abaixo |

Se uma tarefa estiver esperando aprovação, `backlog-auto status` mostra o comando `claude attach` dela.

## Prompt de fechamento de lote

Rode depois de cada lote, antes do próximo:

```text
Rode `git status` e `git log` para ver o que o último lote mudou. Para cada tarefa concluída, atualize a documentação do projeto (índice, plano, decisões) com os fatos novos, seguindo as regras de documentação do projeto (AGENTS.md, CLAUDE.md, LEIA-ME ou equivalente, sob qualquer nome), e confira se o BACKLOG.md reflete os status reais (`backlog-auto list`). Não altere código.
```

## Limites

- **Push:** o agente nunca faz push sozinho.
- **Dados:** a barreira `[guard]` do `backlog.toml` bloqueia escrita em dado existente; liberar só você, com `BACKLOG_ESCRITA=1`.
- **Ambientes:** tarefas que dependem de rede ou serviço específico só rodam onde o PC tem acesso; fora dele, use só as de ambiente `offline`.
- **Acrescente aqui** as restrições próprias deste projeto (produção, redes, credenciais).
