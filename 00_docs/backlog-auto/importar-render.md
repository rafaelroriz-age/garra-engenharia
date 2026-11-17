# T84 · Importação do banco do Render para o Postgres local (DEC-57)

- Tarefa: T84 (papel devops), Bloco G do `BACKLOG.md`. Decisão de origem: DEC-57. Depende de T79 (runtime local).
- Data: 2026-11-17. Branch: `worktree-backlog-T84`.
- Entrega: `05_infra/local/importar-render.ps1` (Windows PowerShell 5.1, só ASCII).
- A sessão do agente **não conectou ao Render**. O fluxo foi testado com banco de dev como origem e banco descartável como destino (§4).

## 1. Passo a passo para o dono (HT-15)

Pré-requisito: `05_infra\local\garra-local.ps1 setup` e `start` já rodados (Postgres local no ar na porta do `.env`, padrão 5434).

1. No Dashboard do Render, abra o banco `garra-db` e copie a **External Database URL** (`postgres://usuario:senha@host:porta/banco`). Não cole em arquivo nem em chat.
2. Em PowerShell, na pasta do repositório:
   ```powershell
   .\05_infra\local\importar-render.ps1
   ```
3. Cole a URL no prompt (a digitação fica oculta). Digite `SIM` na confirmação.
4. Espere terminar (um banco deste porte leva menos de 1 min, mais o tempo de rede). A saída termina com a tabela lado a lado e:
   - `OK` (exit 0): todas as contagens batem. Pode seguir para `garra-local.ps1 install`.
   - `DIVERGENTE` (exit 2): alguma tabela difere. Não desligue o Render; veja o log e me avise.
5. Só **depois** do OK e de conferir o app no PC apague os serviços do Render (HT-16).

Parâmetros: `-OrigemUrl` (se omitido, pede de forma segura), `-DestinoDb` (padrão `garra_producao`), `-Forcar` (sem a confirmação `SIM`), `-EnvLocal` e `-Python` (só para testes).

O que o script grava:

| Arquivo | Conteúdo |
|---|---|
| `05_infra/local/backups/render-final-AAAAMMDD-HHmmss.dump` | dump `-Fc` da origem. Guarde: é o retrato final do Render. |
| `05_infra/local/backups/local-antes-import-<banco>-AAAAMMDD-HHmmss.dump` | backup do destino, só se ele já tinha tabelas |
| `05_infra/local/logs/importar-render.log` | comandos executados e saídas. A URL e a senha **nunca** vão para o log (a senha segue por variável de ambiente `PGPASSWORD` do processo filho, não por argumento) |

Tudo isso fica em pastas git-ignoradas (`05_infra/local/` no `.gitignore`, T79).

## 2. O que o script faz

1. Lê a URL (parâmetro ou `Read-Host -AsSecureString`), extrai host, porta, usuário, senha e banco. `sslmode` vem da URL; se faltar, é `require` para host remoto e `prefer` para localhost.
2. Lê `POSTGRES_*` do `05_infra/local/.env` (o mesmo do `garra-local.ps1`). Recusa destino que não seja localhost e origem igual ao destino. Exige o Postgres local no ar (`pg_isready`), cria o banco de destino se não existir.
3. `pg_dump -Fc --no-owner --no-privileges` da origem (somente leitura) e `pg_restore --list` para validar o arquivo.
4. Se o destino já tem tabelas, `pg_dump -Fc` dele antes de qualquer alteração.
5. `pg_restore --clean --if-exists --no-owner --no-privileges --exit-on-error` no destino.
6. `alembic upgrade head` (Python de `04_backend\.venv-prod`, senão `04_backend\.venv`) apontando para o destino.
7. `count(*)` de cada tabela de `public` nos dois lados, em uma consulta por lado. A tabela sai lado a lado. É divergência: tabela da origem ausente ou com contagem diferente no destino, ou tabela só do destino com linhas. Tabela criada só pelo alembic (a origem estava em migration mais antiga) e vazia no destino conta como `ok`, com `-` na coluna da origem.

Binários: `%LOCALAPPDATA%\garra\pgsql\bin` (junção ASCII do T79), com fallback em `05_infra\local\bin\pgsql\bin`.

## 3. Fotos e arquivos: há algo além do banco para migrar?

Lido `render.yaml` (linhas 145–157): o Blueprint do Render tinha só frontend, backend e banco. O armazenamento de fotos/documentos (MinIO/S3, DEC-02) **ficou fora** (`# FICOU FORA do escopo deste Blueprint`) e as variáveis `MINIO_*` estavam comentadas, sem disco persistente. Conclusão: **não há arquivo de foto no Render para migrar**; o banco é a única fonte a importar.

Atenção ao que isso implica: a tabela `fotos` pode ter linhas (metadados, `storage_key`) cujos arquivos nunca existiram no Render. Elas vêm no dump e a contagem confere, mas a imagem só aparece se o arquivo existir no storage local (`STORAGE_LOCAL_DIR`, T80). Se o dono tiver fotos em outro lugar (computador de campo, S3 próprio), isso é à parte e não depende deste script. Não foi verificado o que o Dashboard do Render tem configurado manualmente além do `render.yaml`: vale o dono conferir em *Environment* se `MINIO_HOST` foi preenchido por fora.

## 4. Teste executado (sem tocar no Render)

Ambiente: Windows 11 Pro, Windows PowerShell 5.1, binários PostgreSQL 16.16 do T79.

- **Origem**: banco de dev `garra_engenharia` (Docker, `localhost:5433`), apenas via `pg_dump`.
- **Destino**: o cluster 5434 do runtime (`garra-local.ps1 setup`) não existe neste PC. Para não criar o runtime inteiro, subi um cluster Postgres 16 **descartável** na porta 5434 (diretório temporário do job, senha de teste) com os mesmos binários, e o `.env` de teste aponta para ele. Banco de destino: `garra_import_teste`.

### 4.1 Execução contra o banco de dev: falhou no alembic (achado)

`pg_dump` (0,2 MB), `pg_restore --list` e `pg_restore` passaram. O `alembic upgrade head` falhou na migration `e5a1f0c2b7d4` (unicidade de versão de relatório, DEC-48):

```text
RuntimeError: Existem 1 grupo(s) duplicado(s) em relatorios (inspecao_id, tipo, versao); a constraint uq_relatorios_inspecao_tipo_versao não pode ser criada.
  inspecao_id=22db6dc2-... tipo=RFO versao=BENCH-01 (2 registros: fddefc2c-..., fee39a87-...)
```

O script abortou com exit 1 e mostrou o erro, como deve. Causa: o banco de dev tem dois relatórios de benchmark com a mesma versão (dev estava na revisão `f7c2a9d4e6b1`, um ramo anterior ao merge `e5a1c7d9b3f4`). **Risco real para a importação de produção**: se o Render estiver numa revisão anterior a `e5a1f0c2b7d4` e tiver relatórios duplicados por `(inspecao_id, tipo, versao)`, o upgrade falha do mesmo jeito. Nesse caso o dump já está restaurado no destino (não se perde nada); basta corrigir os duplicados no destino com critério de negócio (a mensagem lista os ids) e rodar `alembic upgrade head` de novo, ou rodar o script outra vez. Sugestão: o dono consultar antes, no Render, `select inspecao_id, tipo, versao, count(*) from relatorios group by 1,2,3 having count(*) > 1;` (consulta de leitura).

### 4.2 Execução completa (OK)

Para completar o fluxo sem alterar o dev (somente leitura), restaurei o dump do dev em um segundo banco descartável `garra_origem_teste` do mesmo cluster 5434, renumerei a versão duplicada (`BENCH-01` → `BENCH-01-dup`, só nessa cópia) e usei esse banco como origem. O destino `garra_import_teste` já tinha as tabelas do passo anterior, o que exercitou também o backup do destino. Comando (senha de teste, não é credencial real):

```powershell
importar-render.ps1 -OrigemUrl postgresql://garra:***@localhost:5434/garra_origem_teste -DestinoDb garra_import_teste -Forcar -EnvLocal <env de teste> -Python 04_backend\.venv\Scripts\python.exe
```

Saída (resumo do log; 38 s):

```text
[INFO] === importar-render: inicio (destino=garra_import_teste) ===
[INFO] origem: localhost:5434/garra_origem_teste (usuario garra, sslmode prefer)
[INFO] pg_dump da origem -> ...\backups\render-final-20261117-185804.dump
[INFO] dump da origem ok: 0,2 MB
[INFO] backup do destino -> ...\backups\local-antes-import-garra_import_teste-20261117-185804.dump
[INFO] pg_restore --clean --if-exists --no-owner em garra_import_teste
[INFO] alembic upgrade head

Tabela                  Origem Destino Status
alembic_version         1      1       ok
chamadas_ia             -      0       ok
contrato_executores     9      9       ok
contrato_nbrs           7      7       ok
contratos               79     79      ok
edificacoes             79     79      ok
fotos                   573    573     ok
inspecoes               19     19      ok
localizacoes            47     47      ok
ocorrencias             2      2       ok
prompts_ia              0      0       ok
relatorio_conteudos     -      0       ok
relatorios              2      2       ok
responsaveis            125    125     ok
sistemas_prediais       15     15      ok
subsistemas             113    113     ok
tipos_anomalia          6      6       ok
tipos_falha             9      9       ok
trechos_conhecimento_ia -      0       ok
usuarios                260    260     ok
visita_mao_obras        666    666     ok
visita_medicoes         381    381     ok
visitas                 191    191     ok

[INFO] RESULTADO: OK (23 tabelas conferidas, 38s).
OK        (exit 0)
```

As linhas com `-` na origem são tabelas criadas pelo `alembic upgrade head` (a origem estava numa revisão anterior); o script as trata como `ok` por estarem vazias.

### 4.3 Limpeza

Apaguei `garra_import_teste` e `garra_origem_teste` (`dropdb`), parei e removi o cluster 5434 descartável e os dumps de teste. O banco de dev (5433) não foi alterado (só leitura). O log do teste não contém URL nem senha (verificado com busca por `postgresql://` e pela senha: 0 ocorrências).

## 5. Verificações

- Parser do PowerShell 5.1 sem erros; script só ASCII; execução real em `powershell.exe` 5.1 (§4).
- Não foi testada na prática a saída `DIVERGENTE` (exit 2): não havia como forçar divergência sem alterar a origem. A lógica é a comparação da §2 passo 7; fica como lacuna. Também não foi testado origem remota com TLS (`sslmode=require`) porque a sessão não pode conectar ao Render; o script apenas repassa `PGSSLMODE` ao `pg_dump`.
- `pytest`, `ruff`, `npm lint/build` não foram rodados: nenhum arquivo de `04_backend/` ou `03_frontend/` foi tocado.

## 6. Limitações e riscos

1. **Versão do servidor**: `pg_dump` 16 recusa origem com versão maior que 16. Não verifiquei a versão do banco no Render; se der `server version mismatch`, é preciso um `pg_dump` 17 (baixar os binários da EDB 17 só para esse passo) ou conferir a versão no Dashboard. Origem mais antiga que 16 funciona.
2. **Banco de origem pode estar suspenso/expirado** (plano gratuito do Render expira em 30 dias): se a conexão falhar, o dono precisa reativar o banco antes.
3. **Extensões**: se a origem usar extensões não incluídas no pacote portátil da EDB (ex.: `pgvector`), o `pg_restore --exit-on-error` para no primeiro erro. O backend atual usa busca textual (BL-34), então não é esperado.
4. **Dumps do Render ficam em `backups/`**, pasta que o OneDrive sincroniza (DEC-57: dumps sincronizados é desejado). O dump contém dados reais (inclui hashes de senha de `usuarios`): é aceitável por estar na conta do dono, mas não o copie para fora.
5. **`--clean` apaga e recria** os objetos do destino: reimportar substitui qualquer dado novo criado no PC desde a última importação. O backup `local-antes-import-*` cobre isso.

## 7. Proposta (para o fechamento de lote; não aplicada)

- **T85/HT-15**: acrescentar ao passo 2 do HT-15 a consulta de duplicados em `relatorios` (§4.1) e o aviso da versão do `pg_dump` (§6.1).
