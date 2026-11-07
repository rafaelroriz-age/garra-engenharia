# BL-29 — Verificação automatizada dos scripts de backup e restore

Data: 2026-11-07 · Escopo: `05_infra/backup/backup-db.sh`, `05_infra/backup/restore-db.sh` (RNF-08).
Sem banco, MinIO ou docker reais; o restore nunca foi executado contra dados existentes.

## 1. Comandos externos mapeados

Ambos os scripts só chamam `docker compose` (nenhum `pg_dump`/`psql`/`mc` direto no host):

| Script | Chamadas |
|---|---|
| `backup-db.sh` | `docker compose -f $COMPOSE_FILE exec -T postgres pg_dump -U … -d … --format=custom --no-owner` (stdout → arquivo); `docker compose … ps --services` (detecta `minio`); `docker run --rm --network garra-net -v … minio/mc:latest mirror --overwrite --remove`; `find … -mtime +N -delete`; `du`, `cut`, `date`, `mkdir` |
| `restore-db.sh` | `read` (confirmação `RESTAURAR`); `docker compose … exec -T postgres pg_dump …` (dump `pre-restore`, com `\|\| true`); `docker compose … stop backend frontend`; `exec -T postgres pg_restore -U … -d … --clean --if-exists --no-owner < dump`; `docker compose … start backend frontend` |

## 2. Análise estática

- `bash -n backup-db.sh`: OK (após a correção). `bash -n restore-db.sh`: não pôde ser executado como comando isolado — o hook `backlog-auto` bloqueia qualquer comando Bash que cite o script de restore. Ele foi parseado implicitamente nas execuções do teste (bash o executou sem erro de sintaxe).
- `shellcheck`: **não instalado** neste ambiente; não rodou.

## 3. Teste

Arquivo: `05_infra/backup/tests/test_backup_scripts.sh` (shell puro). Cada cenário cria uma árvore em `mktemp -d` com cópia dos scripts (dumps/objetos nascem no tmp), stub de `docker` e de `pg_dump/pg_restore/psql/mc/aws/rclone` no início do PATH (chamada direta a esses é registrada e falha o teste), variáveis fictícias, e uma trava que aborta se `docker` não resolver para o stub.

Cenários: (a) backup feliz — dump criado, arquivo antigo ainda existia durante o `pg_dump` (retenção depois), antigo (60 dias) removido, recente (1 dia) mantido; (a2) com serviço `minio`, `mc mirror` acionado; (b1) `pg_dump` falha; (b2) dump vazio; (b3) `POSTGRES_USER` ausente — todos saem ≠ 0 e preservam os backups antigos; (c1–c4) restore com confirmação errada, `restaurar` minúsculo, EOF no stdin, sem argumento e arquivo inexistente — abortam sem nenhuma chamada ao docker; (d) restore com `RESTAURAR` — `pre-restore-*.dump` gerado, ordem `pg_dump` < `stop` < `pg_restore`, conteúdo do dump entra no stdin do `pg_restore`, flags `--clean --if-exists`.

Comando: `bash 05_infra/backup/tests/test_backup_scripts.sh` (Git Bash, Windows 11).

Saída final da execução: `Resumo: 45 ok, 0 falha(s)` (exit 0). Na primeira execução, 2 falhas: o defeito do item 4.1 e um erro do próprio teste (RC perdido em subshell por causa de `echo | função`, corrigido com here-string; esse erro tornava alguns `ok` do bloco (c) inválidos, por isso foram re-executados após a correção).

## 4. Defeitos e propostas

1. **Corrigido (mínimo, sem mudar comportamento documentado)** — `backup-db.sh`: se `pg_dump` falhava, o `set -e` abortava (retenção não rodava, correto), mas deixava um `garra-db-<carimbo>.dump` parcial/vazio no diretório, que parecia um backup válido (e é o "mais recente" para o restore). Agora o script remove o parcial, imprime erro e sai com 1.
2. **Proposta (não aplicada — muda comportamento visível)** — `restore-db.sh` linha do dump `pre-restore` termina com `|| true`: se o dump de segurança falhar ou sair vazio, o script ainda imprime "Estado anterior salvo" e segue para o `pg_restore --clean`, destruindo o banco sem rede de segurança. Sugestão: abortar (exit ≠ 0) quando o `pre-restore` falhar ou estiver vazio, com opção explícita (ex.: `FORCAR_SEM_PRE_RESTORE=1`) para ignorar. O teste traz um bloco INFO que documenta o comportamento atual e deverá virar asserção quando a proposta for aprovada.
3. **Observação** — a retenção usa `-mtime` e só considera `garra-db-*.dump`; os `pre-restore-*.dump` nunca são expirados (crescimento ilimitado de disco). Proposta: incluí-los na retenção.
4. **Observação** — `mc mirror --remove` em `objetos/` propaga ao espelho local a exclusão de objetos no MinIO (espelho, não histórico); não há versionamento dos objetos além do dump.

Destino externo do backup (cópia fora do host) segue `[A ESCLARECER]` (RNF-08) e está fora deste escopo.
