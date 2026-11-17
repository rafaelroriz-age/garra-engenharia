# T89 · Backup do Neon e documentação do banco gerenciado (DEC-58)

O plano gratuito do Neon não substitui backup próprio. Esta tarefa faz o backup do banco de produção no PC
do dono (`pg_dump -Fc` contra o Neon, com TLS) e documenta a operação do banco no Neon. Nada foi conectado
ao Neon real nesta sessão.

## O que mudou

| Arquivo | Mudança |
|---|---|
| `05_infra/local/garra-local.ps1` | `backup` no modo `POSTGRES_MODO=neon`: não exige o Postgres local no ar; define `PGSSLMODE=require`; loga a versão do `pg_dump` usado. O restante (dump para `backups/`, `pg_restore --list` como verificação, retenção por `BACKUP_RETENCAO`) é o mesmo do modo local. No modo `neon`, `setup` instala os binários `pg_dump`/`pg_restore`/`psql` (`Install-PgBinarios`), sem initdb nem criação de banco. Cabeçalho e uso (`help`) atualizados. |
| `05_infra/README.md` | Nova seção "Banco no Neon (DEC-58)": criação do projeto, conexão direta × pooled, `POSTGRES_SSL`, cold start, backup, restauração em outro banco e aviso sobre dados pessoais nos dumps. A seção "Arquitetura" passa a apontar o Neon como banco de produção e o Postgres portátil como `POSTGRES_MODO=local`, opcional/fallback. |
| `00_docs/configuracao.md` | Seção 7: linhas para `POSTGRES_MODO`, `POSTGRES_SSL` e as variáveis de conexão do modo `neon`. |
| `00_docs/backlog-auto/neon-backup.md` | Este Doc. |

Não tocados: `garra-agente.ps1` (a rotina diária já chama `garra-local.ps1 backup`; agora ela também funciona
no modo neon), `04_backend/` (código de aplicação), `03_frontend/`, `decisoes.md`, `status.md`, `riscos.md`,
`BACKLOG.md` e os documentos de gestão.

## Decisões e comportamento

- **Retenção de 14** (`BACKUP_RETENCAO`, padrão já existente): cada `backup` apaga os dumps além dos 14 mais
  recentes, depois de confirmar que o novo dump é legível (`pg_restore --list`). Nada é apagado se o dump falhar.
- **TLS:** `PGSSLMODE=require` fixo no modo neon. A senha vem de `PGPASSWORD` (do `.env` local), como no modo local.
- **Sem segredos no log:** host e usuário já entram em `Hide-Segredos` desde a T87. O comando do `pg_dump` não
  recebe senha na linha de comando.
- **Dumps são dados pessoais** (usuários, hashes, fotos, documentos). Ficam em `05_infra/local/backups/`
  (`.gitignore`), dentro da pasta sincronizada pelo OneDrive. Isto está documentado no README.

## O que rodou de verdade

| Verificação | Resultado |
|---|---|
| Parse do `garra-local.ps1` (PowerShell `Parser::ParseFile`) | 0 erros |
| Arquivo só ASCII (exigência de `.ps1` do T82) | 0 bytes não ASCII |
| `ruff check .` em `04_backend` (venv do checkout principal, `04_backend/.venv`) | `All checks passed!` |
| `alembic upgrade head` em `garra_engenharia_test` (localhost:5433) | sem erro; migrations já aplicadas |
| `pytest` em `04_backend` (banco `garra_engenharia_test`, localhost:5433) | ver seção "Resultado do pytest" |

Não rodou (e por quê):

- **`backup` no modo neon, de ponta a ponta:** exige `POSTGRES_HOST` diferente de `localhost` e um Neon real.
  Sem o Neon, não há como exercitar esse caminho. O modo `local` do `backup` depende do Postgres portátil
  (`05_infra/local/bin/pgsql`), que não está instalado neste worktree.
- **`npm run lint` / `npm run build`:** não rodados. Esta tarefa não tocou `03_frontend/`.
- **Restauração de um dump do Neon:** depende de dump real.

## O que depende do dono (HT)

1. Criar o projeto no Neon e preencher `05_infra/local/.env` conforme o README (seção "Banco no Neon (DEC-58)").
   Não colar host, usuário ou senha em nenhum arquivo versionado nem neste Doc.
2. Rodar `garra-local.ps1 setup` (instala os binários do `pg_dump`), `start` e `status`.
3. Rodar `garra-local.ps1 backup` uma vez e conferir que o dump aparece em `05_infra\local\backups\` e que
   `pg_restore --list` lista os itens. Se o `pg_dump` recusar por versão, o log mostra as duas versões.
4. Fazer um teste de restauração num banco descartável do Neon antes de confiar no backup.

## Decisão proposta (fechamento de lote, para a DEC-58)

- Acrescentar à DEC-58: o backup diário do banco de produção é um `pg_dump -Fc` do Neon feito pelo PC do dono
  (`garra-local.ps1 backup`, rotina do agente), com retenção de 14 dumps em `05_infra/local/backups/`. O plano
  gratuito do Neon não substitui esse backup.
- Registrar que a DEC-57 P1 (Postgres portátil) passa a ser opcional e fallback (`POSTGRES_MODO=local`).
- Referenciar este Doc e a seção "Banco no Neon (DEC-58)" do `05_infra/README.md`.

## Resultado do pytest

- **Execução 1** (`pytest -q` em `04_backend`, banco `garra_engenharia_test`): parou na coleta com
  `ERROR tests/test_rfo_contexto.py - OSError: cannot load library 'libpango-1.0...'` (`Interrupted: 1 error during
  collection`, exit 0 do script de wrapper, mas a suíte não rodou). Causa: a biblioteca Pango do WeasyPrint não
  está instalada neste ambiente. Não tem relação com as alterações desta tarefa (que não tocam `04_backend/`).
- **Execução 2** (mesmo comando com `--continue-on-collection-errors`): **interrompida pelo sistema por pouca
  memória** antes de imprimir o resumo. Não há número de passed/failed válido. Não foi reiniciada nesta sessão.
- Portanto, o pytest completo **não foi concluído**. Para fechar: instalar o Pango neste PC (ou rodar
  `garra-local.ps1 setup` sem `-PularPango`) e rodar `pytest` de novo com memória livre.
- Esta tarefa não altera código Python nem testes; a suíte do backend não é afetada pelas mudanças aqui.
