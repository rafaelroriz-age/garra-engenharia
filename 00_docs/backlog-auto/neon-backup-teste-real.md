# Teste real de backup e restore do Neon (R-24)

**Status: NÃO EXECUTADO.** A sessão não tinha a string de conexão do Neon.

## O que foi verificado
- Variáveis de ambiente `DATABASE_URL` / `NEON_DATABASE_URL`: ausentes.
- `05_infra/local/.env` e `04_backend/.env`: inexistentes (nem no worktree nem no checkout principal); `05_infra/local/backups/` também não existe.
- Sem credencial, nenhum dos passos abaixo foi tentado; nenhum resultado foi inventado.

## Passos pendentes (para o dono do projeto, na máquina com o `.env`)
1. `powershell -NoProfile -ExecutionPolicy Bypass -File .\05_infra\local\garra-local.ps1 backup`. Anotar o arquivo `garra-AAAAMMDD-HHmm.dump` e o tamanho.
2. Criar banco descartável (Postgres local de `05_infra`, porta 5433, ou branch do Neon) e restaurar com `05_infra/backup/restore-db.sh`. Nunca sobre o banco de produção.
3. Comparar `SELECT count(*)` das tabelas do critério de pronto de `neon-backup.md` entre Neon e o restaurado.
4. Conferir se `05_infra/local/backups/` está sob o OneDrive (o repositório está em `...\OneDrive - Dynatest Engenharia\...`, então a pasta de dumps provavelmente está).
5. Apagar o banco descartável.

## Proposta (a decidir; `decisoes.md` não foi editado)
Como os dumps têm dados pessoais e ficam sincronizados no OneDrive: (a) apontar `backups/` para fora do OneDrive, ou (b) cifrar o dump antes de gravar (ex.: `age`/`gpg` simétrico, chave fora do OneDrive). Recomendação: (a) mais (b) para cópias que precisem sair da máquina.

## Resultado
Pendente. R-24 segue aberto.
