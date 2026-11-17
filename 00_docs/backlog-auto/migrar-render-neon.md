# T88 · Migrar os dados do `garra-db` (Render) para o Neon (DEC-58)

`05_infra/local/importar-render.ps1` (T84) ganhou o modo **Neon**: `-DestinoUrl` (ou `-DestinoPrompt`) restaura o
dump do Render num Postgres **remoto** em vez do local. O modo local (`-DestinoDb`, `.env` local) continua igual.

## O que mudou no script

| Item | Comportamento |
|---|---|
| `-DestinoUrl` / `-DestinoPrompt` | URL `postgres://usuario:senha@host:porta/banco?sslmode=require`. Sem valor, pede por `Read-Host -AsSecureString` (digitação oculta). Nunca lida de arquivo, nunca gravada em disco; host e senha entram na lista de segredos mascarados do log. |
| Validações | Recusa host com `-pooler` (asyncpg/alembic não funcionam no PgBouncer), recusa origem == destino, exige conectar (mostra `tls=` ativo) antes de qualquer coisa. O banco do Neon já existe: o script não faz `create database` no modo remoto. |
| Restauração | `pg_dump -Fc` da origem (somente leitura), backup do destino se ele já tiver tabelas, `pg_restore --clean --if-exists --no-owner --no-privileges --exit-on-error`, `alembic upgrade head` (com `POSTGRES_SSL` derivado do `sslmode`), contagem por tabela dos dois lados e `OK`/`DIVERGENTE` (exit 0 / 2). |
| Destino já migrado | **Novo (achado do teste)**: se o destino já tem tabelas, o script faz `drop schema public cascade; create schema public;` (depois do backup e da confirmação `SIM`) antes do `pg_restore`. Sem isso o `--clean` falhava (`cannot drop constraint usuarios_pkey ... other objects depend on it`) quando o destino estava numa revisão mais nova que o dump, caso real do Neon se o dono rodar `garra-local.ps1 start` (T87) antes. Vale também para o modo local. |
| Bug corrigido no parser de URL | `-match` interno sobrescrevia `$Matches` quando a URL tinha `?sslmode=...` (host/usuário/banco saíam vazios). A T84 só testou URL sem query; toda URL do Neon tem `?sslmode=require`. |

## Passo a passo para o dono (ordem obrigatória)

Pré-requisitos: projeto criado no Neon (T87, conexão **direta**, sem `-pooler`); runtime local instalado
(`garra-local.ps1 setup`, que traz `pg_dump`/`pg_restore`/`psql` 16); o `garra-db` do Render **ainda ativo**.
Antes, no Render (somente leitura): `select inspecao_id, tipo, versao, count(*) from relatorios group by 1,2,3
having count(*) > 1;` — se voltar linha, a migration `e5a1f0c2b7d4` vai falhar no alembic (ver T84 §4.1).

1. **Pausar escritas**: avise a equipe para não gravar no app do Render; este é o dump final.
2. **Dump final do Render + restauração no Neon + conferência** (um comando, PowerShell 5.1, a partir da raiz):
   ```powershell
   .\05_infra\local\importar-render.ps1 -DestinoPrompt
   ```
   Cole primeiro a External Database URL do Render, depois a connection string direta do Neon (as duas ficam
   ocultas). Digite `SIM` quando perguntar. O dump final fica em `05_infra\local\backups\render-final-*.dump`.
3. **Conferência**: a saída termina com a tabela lado a lado e **`OK`** (exit 0). `DIVERGENTE` (exit 2) = não
   desligue nada; abra o log em `05_infra\local\logs\importar-render.log` (sem senhas). `-` na origem com `0` no
   destino é tabela nova criada pelo alembic, não é divergência.
4. **Login de teste**: no `05_infra/local/.env` use `POSTGRES_MODO=neon` (T87), rode `garra-local.ps1 start` e
   `status` (`neon: conectado ... tls=True`), abra o app e entre com o admin e com mais um usuário real; abra uma
   inspeção e um relatório. A tabela `usuarios` chega com os hashes intactos (provado no teste abaixo).
5. **Só então desligar o Render**: apague `garra-backend`/`garra-frontend` e, por último, o `garra-db`. Mantenha o
   dump `render-final-*.dump` (OneDrive) por algumas semanas como rede de segurança.

**Alternativa manual** (se o script não puder ser usado): no Render, `pg_dump -Fc` da External Database URL; no
console do Neon, *Import Data Assistant* (ou `pg_restore --no-owner --no-privileges -d <url direta>`), depois
`alembic upgrade head` com o `.env` em modo neon e conferir contagens por tabela (`select count(*)` nos dois lados),
inclusive `usuarios`. O script automatiza exatamente isso.

Observação: o Neon escala a zero; se a primeira conexão falhar, rode de novo em alguns segundos.

## O que rodou de verdade (sem tocar no Render nem no Neon)

Windows PowerShell 5.1, binários PostgreSQL 16 do T79, Postgres de dev em `localhost:5433` (`sslmode=disable`).
Origem = cópia descartável do banco de dev (com o duplicado de benchmark em `relatorios` removido, achado da T84),
destino = banco descartável no mesmo servidor, passado por `-DestinoUrl` (mesmo caminho de código do Neon, exceto TLS).

| Execução | Resultado |
|---|---|
| Remoto 1 (destino vazio) | **OK**, 23 tabelas conferidas, 31 s |
| Remoto 2 (destino já migrado, schema mais novo que o dump) | **OK**, 33 s (exercita o `drop schema`; antes da correção falhava no `pg_restore`) |
| Modo local (`-DestinoDb` + `-EnvLocal`, regressão) | **OK**, 33 s |
| `usuarios` (md5 de `id+email+senha_hash`) origem vs destino | idêntico: `b6e3af2e...` nos dois |
| Host com `-pooler` | recusado com mensagem clara, antes de qualquer conexão |
| Log | busca pela senha: 0 ocorrências |

Contagens (origem → destino, idênticas): usuarios 262, fotos 573, visitas 191, contratos 79, edificacoes 79,
responsaveis 125, subsistemas 113, visita_mao_obras 666, visita_medicoes 381, inspecoes 19, relatorios 1, etc.
A primeira tentativa (antes de remover o duplicado) falhou no alembic exatamente como previsto na T84 §4.1.

Limpeza: os dois bancos descartáveis foram apagados (`drop database`); o banco de dev `garra_engenharia` só foi lido.
Dumps de teste ficam em `05_infra/local/backups/` (no `.gitignore`).

## Não verificado / depende do dono

- Conexão real ao Render e ao Neon e TLS real (`sslmode=require`): o script só repassa `PGSSLMODE`; o teste usou `disable`.
- Versão do servidor do Render: `pg_dump` 16 recusa origem de versão maior (ver T84 §6.1).
- Saída `DIVERGENTE` (exit 2) não foi forçada. `pytest`/`ruff`/`npm`: nenhum arquivo de `04_backend/` ou `03_frontend/` foi tocado.
- `drop schema public cascade` no Neon exige que o usuário seja dono do schema `public` (é o padrão do usuário do projeto).

## Decisão proposta (fechamento de lote)

Acrescentar ao HT-15 a ordem acima (dump → Neon → conferência → login → desligar o Render) e referenciar este Doc na T89.
