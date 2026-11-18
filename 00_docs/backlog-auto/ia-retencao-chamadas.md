# T94 — Retenção da coluna `resposta` em `chamadas_ia` (DEC-52)

Origem: DEC-52, consequência «a coluna `resposta` guarda a legenda saneada sem política de retenção». `resposta` é dado derivado de fotos de clientes e hoje fica guardada para sempre. Esta tarefa cria o script de expurgo. Ele não apaga linhas e não altera tokens, custo, latência, origem, chave de cache, modelo nem outras colunas. Riscos relacionados: R-10 (custo e retenção com 150+ fotos por relatório).

Papel: backend. Branch `worktree-backlog-T94`. Sem push.

## O que foi feito

- **`04_backend/app/scripts/limpar_chamadas_ia.py`** (novo), no estilo de `exportar_dataset_legenda.py` (argparse, `main(argv)`, `asyncio.run`, `NullPool`).
  - Padrão é **dry-run**: conta as linhas que teriam `resposta` anulada e não grava nada. `--aplicar` faz o UPDATE.
  - Critério: `resposta` com valor e `criado_em < agora - TTL`. Só `resposta` recebe `SQL NULL`.
  - `--ttl-horas N` (N ≥ 1) sobrescreve a configuração. Sem a flag, usa `LEGENDA_IA_CACHE_TTL_H`.
  - **Escolha para TTL 0:** `LEGENDA_IA_CACHE_TTL_H=0` significa cache desligado. Nesse caso o script usa o padrão de **720 h** e imprime aviso em stderr. Não anula tudo por engano. Para outro prazo, passe `--ttl-horas`. `--ttl-horas 0` é recusado (`argparse`).
- **`04_backend/app/services/legenda_ia/telemetria.py`** (ajuste de correção):
  - Novo helper `tem_resposta()`: `coalesce(jsonb_typeof(resposta), 'null') <> 'null'`. Cobre SQL `NULL` e JSON `null`.
  - `buscar_em_cache` usa esse helper e retorna `None` se a linha vier sem `resposta`. Antes, uma linha com JSON `null` era tratada como acerto e quebrava com `TypeError`.
- **`04_backend/tests/test_limpar_chamadas_ia.py`** (novo, 9 testes): resolução de TTL; dry-run não altera nada; `--aplicar` anula só as vencidas (e confere `IS NULL` em SQL); linhas recentes intactas; demais colunas preservadas e nenhuma linha apagada; idempotência (segunda execução devolve 0); cache não devolve resposta expurgada nem `resposta` nula dentro do TTL.
- **Variável de ambiente nova:** nenhuma. `.env.example` não foi alterado.
- **Migration:** nenhuma.
- **Originais em `01_output-context/`:** não tocados.
- Não foram editados `00_docs/projeto/*.md` nem o `BACKLOG.md`.

## Achado relevante: JSON `null` x SQL `NULL` em JSONB

Com coluna `JSONB`, o SQLAlchemy grava `None` como o JSON `null` (`'null'::jsonb`), não como SQL `NULL`. Isso tem duas consequências, ambas confirmadas por teste:

1. `resposta IS NOT NULL` continua casando essas linhas. Por isso a primeira versão do expurgo não era idempotente (a segunda rodada achou 4 linhas) e `buscar_em_cache` tentou ler `None["legenda_sugerida"]` (`TypeError`).
2. `registrar()` (existente, T68) grava `resposta=None` para falhas e cache de erro, então essas linhas ficam com JSON `null`. O helper `tem_resposta()` trata as duas formas, e o script grava SQL `NULL` (`values(resposta=null())`).

**Proposta (não decisão):** fazer `registrar()` gravar SQL `NULL` quando não há resultado, para que a coluna tenha um único estado vazio. Não foi feito aqui: fica para a revisão da DEC-52.

## Cache: resposta nula nunca é acerto (verificado)

Comportamento de `buscar_em_cache` após a correção: linha expurgada (SQL `NULL`), linha com JSON `null` e linha fora do TTL são **miss**. Cache vazio é miss. Coberto pelo teste `test_cache_nao_devolve_resposta_expurgada` e pelos 14 testes de `test_legenda_ia_telemetria.py`.

## Ambiente e banco (registro honesto)

- **PostgreSQL de 05_infra:** no ar em `localhost:5433`. Usei `POSTGRES_HOST=127.0.0.1`, só nas variáveis do processo. `localhost` resolve para `::1` primeiro, e a porta 5433 só responde em IPv4. Com `localhost`, cada conexão ficava em `SynSent` até o timeout e o pytest travava. Nenhum arquivo foi alterado por isso.
- **Credenciais:** `POSTGRES_USER` e `POSTGRES_PASSWORD` vieram do `04_backend/.env` do checkout principal, carregadas só em variáveis de processo. O worktree não tem `.env`. Nenhum valor foi gravado nem impresso.
- **Banco `garra_engenharia_test` (o da Regra de pronto) NÃO foi usado.** Ele está em `alembic_version = d3e7a1c5f9b2`. Essa revisão não existe em nenhum arquivo do repositório (busca em todo o projeto, sem resultado). Com ela, `alembic upgrade head` falha com `Can't locate revision`. Não alterei nem migrei esse banco, porque ele pertence a outra linha de trabalho.
- **Banco usado:** `garra_engenharia_test_t94`, criado por mim com `CREATE DATABASE` (aditivo, nenhum dado existente foi tocado) e migrado do zero com `alembic upgrade head` até `c6f2a8d4e1b9 (head)`. **Pode ser removido à mão** (`DROP DATABASE garra_engenharia_test_t94`), já que a barreira do backlog-auto bloqueia `DROP DATABASE`.
- **`.venv`:** o `04_backend/.venv` não existe no worktree. Usei o venv do checkout principal, pelo caminho absoluto, sem criar nada novo.
- **Lentidão:** `tests/test_legenda_ia_endpoints.py` levou muito mais que os demais. Uma rodada foi interrompida por mim com `TaskStop`.

## Comandos

```text
# venv do checkout principal; variáveis do processo, sem arquivos novos
POSTGRES_DB=garra_engenharia_test_t94 POSTGRES_PORT=5433 POSTGRES_HOST=127.0.0.1
python -m alembic upgrade head        -> c6f2a8d4e1b9 (head)
python -m pytest tests/test_limpar_chamadas_ia.py tests/test_legenda_ia_telemetria.py -q
python -m ruff check .
```

## Resultados

Saída final, após a correção:

```text
tests/test_limpar_chamadas_ia.py ............ 9 passed in 5.28s
tests/test_legenda_ia_telemetria.py ......... 14 passed in 21.84s
23 passed in 24.97s                          (rodada combinada, ambos os arquivos)
ruff check .  -> All checks passed!
```

Antes da correção, na mesma execução: `2 failed, 7 passed` nos meus testes (idempotência e cache). Foi essa falha que levou ao achado do JSON `null`.

**Não concluído nesta sessão:** `tests/test_legenda_ia_endpoints.py` travou (mais de 25 min sem sair da primeira linha de saída, sem conexão ativa de lock no banco). Interrompi com `TaskStop`. `test_legenda_ia_limites.py` e `test_legenda_ia_aprovacao.py` não foram executados, porque a rodada parou no primeiro arquivo. A causa do travamento não foi investigada: é teste existente, fora do escopo, e parece ligado ao cliente HTTP de teste. Esses três arquivos ficam como verificação pendente. Não há número inventado aqui.

## Proposta de agendamento semanal (não é decisão)

Proposta para revisão da DEC-52:

- Agendar `python -m app.scripts.limpar_chamadas_ia --aplicar` uma vez por semana, com o TTL da configuração (720 h).
- Antes de ligar o agendamento, rodar o dry-run e conferir o número.
- Registrar a execução (data, contagem anulada) em log de operação, sem dados de cliente.
- Dono e local do agendamento (cron no ambiente de produção ou job do GitHub Actions) a definir pelo dono. Esta tarefa não cria agendamento.

## Próximos passos sugeridos

1. Dono decide o TTL definitivo (720 h hoje) e aprova a proposta de agendamento.
2. Decidir o item sobre `registrar()` gravar SQL `NULL` (ver achado acima).
3. Remover o banco `garra_engenharia_test_t94` quando não for mais útil.
4. Resolver a revisão órfã `d3e7a1c5f9b2` no banco `garra_engenharia_test` antes de a próxima tarefa rodar `alembic upgrade head` nele.
