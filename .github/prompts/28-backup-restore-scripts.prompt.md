---
description: "Ativa o agente Engenheiro DevOps para implementar os scripts de backup e restore do PostgreSQL/MinIO do Sistema de Automação de Relatórios Prediais."
---
## Contexto
Tarefa BL-29 do backlog em `00_docs/projeto/backlog-tarefas.md`, derivada de DEC-14 (`00_docs/projeto/decisoes.md`). Depende de BL-27 (`docker-compose.prod.yml`, `27-docker-compose-prod-nginx.prompt.md`).
Requisito RNF-08 de `00_docs/estudo-do-contexto.md`: dados devem ser persistidos com backup automático (frequência e destino ainda [A ESCLARECER], mas o mecanismo técnico não depende dessa resposta para ser implementado).
`00_docs/arquitetura.md` Seção 7 já reserva `05_infra/backup/` para esses scripts.

## Tarefa
Assuma o papel de **Engenheiro DevOps** e implemente:

1. `05_infra/backup/backup-db.sh`: dump do PostgreSQL (`pg_dump`) rodando dentro do container/serviço `postgres` do `docker-compose.prod.yml`, salvando arquivos compactados com timestamp (`backup_YYYYMMDD_HHMMSS.sql.gz`) em um diretório de destino configurável via variável de ambiente.
2. Implemente rotação/retenção configurável (ex.: manter os últimos N dias ou N arquivos), removendo backups mais antigos automaticamente.
3. `05_infra/backup/restore-db.sh`: procedimento de restore a partir de um arquivo de backup específico (parâmetro de linha de comando), com confirmação explícita antes de sobrescrever o banco (evitar restore acidental).
4. Documente (comentários no próprio script + `05_infra/README.md`) a estratégia de backup para o volume do MinIO (fotos e relatórios gerados) — pode ser via `mc mirror`/`rclone` ou snapshot do volume Docker; escolha uma abordagem simples e documente a alternativa descartada.
5. Adicione exemplo de agendamento via `cron` (ou `systemd timer`) no `05_infra/README.md`, sem assumir um destino de armazenamento externo específico (deixe configurável).
6. Teste `backup-db.sh` seguido de `restore-db.sh` localmente contra o PostgreSQL do `docker-compose.prod.yml` (ou do `docker-compose.yml` de desenvolvimento, se o de produção ainda não estiver validado em ambiente real) e valide que os dados são restaurados corretamente.

## Saída Esperada
- `05_infra/backup/backup-db.sh` e `restore-db.sh` funcionais e testados
- Estratégia de backup do MinIO documentada
- `05_infra/README.md` atualizado com instruções de backup/restore e exemplo de agendamento
- Resumo: como testar manualmente, o que ainda depende de decisão do cliente (frequência/destino externo do backup, RNF-08)

## Restrições
- NÃO execute `restore-db.sh` sem confirmação explícita do operador — é uma operação destrutiva.
- NÃO hardcode caminhos de destino de backup — sempre via variável de ambiente.
- NÃO assuma um provedor de armazenamento externo específico (S3 externo, etc.) sem registrar como decisão pendente de B-03.
- Leia os arquivos antes de modificá-los.
