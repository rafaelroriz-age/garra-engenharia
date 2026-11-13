# T44 · Restore: abortar sem pre-restore válido e expirar `pre-restore-*`

**Origem:** DEC-45 (proposta da T42, `00_docs/projeto/decisoes.md`) · **Papel:** Engenheiro DevOps · **Status da DEC-45:** **proposta — aguarda aprovação do dono.** Esta tarefa implementa a proposta; não a aprova.

## Problema (antes)

- `05_infra/backup/restore-db.sh` terminava o dump `pre-restore` com `|| true`. Se o `pg_dump` falhasse ou saísse vazio, o script ainda imprimia «Estado anterior salvo» e executava `pg_restore --clean`, sobrescrevendo o banco sem cópia.
- Os `pre-restore-*.dump` nunca expiravam (a retenção só olhava `garra-db-*.dump`).

## Comportamento novo (depois)

1. **Pre-restore obrigatório.** Se o `pg_dump` pre-restore falhar, ou o arquivo resultante tiver tamanho zero, o script:
   - remove o arquivo parcial/vazio;
   - imprime `ERRO: ... restore ABORTADO, nada foi alterado no banco.` em stderr;
   - sai com código 1, **antes** de parar `backend`/`frontend` e antes de qualquer `pg_restore`.
2. **Override explícito.** `FORCAR_SEM_PRE_RESTORE=1` pula a checagem, imprime aviso em stderr (`AVISO: FORCAR_SEM_PRE_RESTORE=1 — pulando o dump pre-restore...`) e segue o restore. Só o valor exato `1` ativa. Qualquer outro valor (ex.: `0`) mantém a checagem.
3. **Retenção dos pre-restore.** A variável já existente `RETENCAO_DIAS` (default 30) mora em `backup-db.sh`, que é onde a retenção roda. O `find` passou a cobrir `garra-db-*.dump` **e** `pre-restore-*.dump` com a mesma janela `-mtime`. Continua valendo a regra antiga: a retenção só roda depois de um dump válido.

## Arquivos alterados

| Arquivo | Mudança |
|---|---|
| `05_infra/backup/restore-db.sh` | bloco do pre-restore: checagem de falha e de tamanho zero, override `FORCAR_SEM_PRE_RESTORE=1` |
| `05_infra/backup/backup-db.sh` | `find` de retenção inclui `pre-restore-*.dump` |
| `05_infra/backup/tests/test_backup_scripts.sh` | bloco INFO convertido em asserções; novos casos (e1) falha, (e2) vazio, (e3) override, (e4) `FORCAR_SEM_PRE_RESTORE=0` não é override, (f) retenção |
| `05_infra/README.md` | seção «Backup e restauração»: comportamento de aborto, retenção e uso do override |
| `00_docs/backlog-auto/restore-pre-restore.md` | este doc |

## Variável de ambiente: por que não entrou no `.env.example`

`FORCAR_SEM_PRE_RESTORE` é um **override de uma execução**, não configuração do ambiente. Os scripts fazem `source .env`; se a variável estivesse lá, ficaria ativa para todo restore futuro, derrubando a rede de segurança sem que ninguém perceba. Por isso ela é documentada no README (seção de backup) e não no `.env.example`. Se o dono preferir o contrário, é uma decisão para ele.

## Verificação

Comando: `bash 05_infra/backup/tests/test_backup_scripts.sh` (a partir da raiz do worktree; usa stubs de `docker`, não toca em banco real nem em `.env`). Ambiente: Windows 11, Git Bash. Sintaxe checada antes com `bash -n` nos dois scripts (OK).

Resultado: **66 ok, 0 falha(s), exit 0.** Saída completa:

```text
== (a) backup feliz: cria dump e aplica retenção só depois
  ok    - sai com código 0
  ok    - dump novo criado e não vazio
  ok    - dump foi gerado ANTES da retenção (arquivo antigo ainda existia durante o pg_dump)
  ok    - backup antigo (60 dias) removido pela retenção
  ok    - backup recente (1 dia) preservado
  ok    - sem minio no compose: espelho pulado (nenhum 'docker run')
  ok    - nenhum comando externo chamado diretamente (só via docker)
== (a2) backup feliz com serviço minio presente: espelho é acionado
  ok    - sai com código 0
  ok    - 'docker run' do mc mirror executado
  ok    - retenção aplicada (antigo removido)
== (b1) pg_dump falha: sai ≠ 0 e NÃO apaga backups antigos
  ok    - sai com código ≠ 0
  ok    - backup antigo (60 dias) NÃO foi apagado
  ok    - backup recente preservado
  ok    - não deixa dump parcial/vazio com nome garra-db-<carimbo>.dump
== (b2) pg_dump produz arquivo vazio: sai ≠ 0 e NÃO apaga backups antigos
  ok    - sai com código ≠ 0
  ok    - mensagem de erro de dump vazio em stderr
  ok    - backup antigo (60 dias) NÃO foi apagado
  ok    - backup recente preservado
  ok    - não deixa dump vazio
  ok    - espelho do MinIO não foi executado
== (b3) POSTGRES_USER ausente: aborta sem apagar nada
  ok    - sai com código ≠ 0
  ok    - backup antigo preservado
  ok    - nenhuma chamada ao docker
== (c1) restore com confirmação errada: aborta sem pg_restore/psql
  ok    - sai com código ≠ 0
  ok    - imprime 'Cancelado.'
  ok    - nenhuma chamada ao docker (nem pg_restore, nem pre-restore, nem stop)
  ok    - nenhum pre-restore criado
  ok    - nenhum pg_restore/psql direto
== (c2) restore com 'restaurar' em minúsculas: aborta (confirmação exata)
  ok    - sai com código ≠ 0
  ok    - nenhuma chamada ao docker
== (c3) restore com stdin vazio (EOF): aborta
  ok    - sai com código ≠ 0
  ok    - nenhuma chamada ao docker
== (c4) restore sem argumento / arquivo inexistente: aborta
  ok    - sem argumento: sai ≠ 0
  ok    - sem argumento: nenhuma chamada ao docker
  ok    - arquivo inexistente: sai ≠ 0
  ok    - arquivo inexistente: nenhuma chamada ao docker
== (d) restore com confirmação RESTAURAR: dump pre-restore vem primeiro
  ok    - sai com código 0
  ok    - arquivo pre-restore-*.dump criado
  ok    - pg_dump (pre-restore) executado
  ok    - pg_restore executado
  ok    - ordem: pg_dump(pre-restore) < pg_restore
  ok    - ordem: stop de backend/frontend antes do pg_restore
  ok    - pg_restore recebeu o conteúdo do dump informado via stdin
  ok    - pg_restore usa --clean --if-exists
  ok    - nenhum comando externo direto
== (e1) pre-restore falha: aborta ANTES de qualquer pg_restore (DEC-45)
  ok    - sai com código ≠ 0
  ok    - mensagem clara de pre-restore falhou em stderr
  ok    - nenhum pg_restore executado
  ok    - nenhum stop/start de backend/frontend (abortou antes)
  ok    - nenhum pre-restore vazio/parcial deixado no disco
  ok    - não anuncia 'Estado anterior salvo'
== (e2) pre-restore produz arquivo vazio: aborta ANTES de qualquer pg_restore (DEC-45)
  ok    - sai com código ≠ 0
  ok    - mensagem clara de dump pre-restore vazio em stderr
  ok    - nenhum pg_restore executado
  ok    - nenhum pre-restore vazio deixado no disco
== (e3) FORCAR_SEM_PRE_RESTORE=1 com pre-restore falhando: override explícito
  ok    - sai com código 0
  ok    - aviso explícito de override em stderr
  ok    - pg_dump pre-restore NÃO foi chamado
  ok    - pg_restore executado mesmo sem pre-restore
  ok    - nenhum pre-restore criado
== (e4) FORCAR_SEM_PRE_RESTORE=0 não é override: checagem continua valendo
  ok    - sai com código ≠ 0
  ok    - nenhum pg_restore executado
== (f) retenção: pre-restore-* antigos expiram com RETENCAO_DIAS; recentes ficam
  ok    - backup sai com código 0
  ok    - pre-restore antigo (60 dias) removido
  ok    - pre-restore recente (1 dia) preservado
  ok    - garra-db antigo continua expirando junto

Resumo: 66 ok, 0 falha(s)
```

Os casos (e1) e (e2) cobrem a regressão original: no código antigo o `pg_restore` era chamado mesmo com o pre-restore falho, e a asserção «nenhum pg_restore executado» falharia.

## Escopo não verificado

- Não rodei a restauração contra PostgreSQL/MinIO reais (não há Docker neste ambiente de tarefa). O teste cobre a lógica dos scripts com stubs; o comportamento com `docker compose` real continua a ser validado no ambiente de deploy.
- `pytest`, `ruff check .`, `npm run lint` e `npm run build` **não se aplicam**: a mudança é só em `05_infra/` (shell) e documentação; nenhum arquivo de `04_backend/` ou `03_frontend/` foi tocado.
- Nenhuma migration, nenhum segredo, nenhum arquivo em `01_output-context/`.

## Decisão proposta (para o dono)

- **DEC-45** permanece **Proposta (aguarda aprovação do dono)** em `00_docs/projeto/decisoes.md`. Este lote não alterou esse arquivo. A aprovação, se vier, deve ser registrada no fechamento de lote.
- Sugestão de registro no fechamento: anotar que o override `FORCAR_SEM_PRE_RESTORE=1` é de uso único e que o `.env` não deve recebê-lo.
