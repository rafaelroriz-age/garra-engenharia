# T117 — Compose de produção (VPS): validar o YAML e fechar o R-16

**Tarefa:** T117 · **Papel:** Engenheiro DevOps · **Risco:** R-16 (item 1)
**Arquivos tocados:** `05_infra/docker-compose.prod.yml` (linha 89), `05_infra/README.md` (nota sobre `LEGENDA_IA_*`), este Doc.

## 1. Erro encontrado

Antes da correção, o parser YAML rejeitava o arquivo:

```
yaml.scanner.ScannerError: mapping values are not allowed here
  in "docker-compose.prod.yml", line 89, column 117
```

Causa: a `image:` do serviço `backend` era um escalar sem aspas que continha `: ` dentro do default do `${IMAGE_TAG:?...}` (`ex.: v1.0.0 ou staging-<sha>`). Em YAML, `: ` dentro de escalar plano é indicador de mapeamento.

## 2. Correção aplicada

Uma única mudança, sem alterar o comportamento do compose:

```diff
-    image: ghcr.io/${GITHUB_REPOSITORY:-rafaelroriz-age/garra-engenharia}/backend:${IMAGE_TAG:?defina IMAGE_TAG (ex.: v1.0.0 ou staging-<sha>)}
+    image: "ghcr.io/${GITHUB_REPOSITORY:-rafaelroriz-age/garra-engenharia}/backend:${IMAGE_TAG:?defina IMAGE_TAG (ex.: v1.0.0 ou staging-<sha>)}"
```

A `image:` do `frontend` não tinha o problema (`${IMAGE_TAG}` sem default de texto) e ficou igual.

## 3. Validação

Variáveis de teste em arquivo **fora do repositório** (`$CLAUDE_JOB_DIR/tmp/test-prod.env`, descartado ao fim do job), com valores fictícios: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`, `BACKEND_CORS_ORIGINS`, `JWT_SECRET_KEY`, `IMAGE_TAG=v0.0.0-teste`, `NEXT_PUBLIC_API_URL`. Nenhum container foi iniciado.

Comando (a partir de `05_infra/`):

```
docker compose --env-file <test-prod.env> -f docker-compose.prod.yml config -q
```

Resultado: **exit 0**, sem saída.

Verificações complementares:

- `yaml.safe_load` no arquivo: **ok** (após a correção; antes falhava na linha 89).
- Imagem renderizada: `ghcr.io/rafaelroriz-age/garra-engenharia/backend:v0.0.0-teste` e a do `frontend` com a mesma tag.
- Guarda de variável obrigatória: com `--env-file /dev/null`, o compose falha com `required variable POSTGRES_USER is missing a value: defina POSTGRES_USER no .env de produção`. Ou seja, os `:?` continuam ativos e não mascaram ausência de configuração.

Docker CLI usado: `C:/Program Files/Docker/Docker/resources/bin` (adicionado ao `PATH` só na sessão do comando).

## 4. Não verificado

- `IMAGE_TAG` real (imagem publicada no GHCR): o `config -q` não puxa imagens, então a existência da tag não foi checada.
- `nginx -t` e `shellcheck` não foram rodados nesta tarefa (fora do escopo de T117).
- Testes de backend/frontend (`pytest`, `ruff`, `npm run lint/build`): não se aplicam, porque nenhum código de aplicação foi alterado.

## 5. Estado do R-16 (proposta, não aplicada)

O R-16 tem quatro itens. Esta tarefa resolve só o item (1):

| Item | Situação |
|---|---|
| (1) YAML inválido na `image:` do backend | **Resolvido** por este Doc (validado com `config -q`). |
| (2) `restore-db.sh` segue após falha do `pre-restore` | Não tratado aqui. Já coberto pela DEC-45 (proposta). |
| (3) Lint do backend não bloqueia CI | Não tratado aqui. Depende da DEC-46. |
| (4) `docker compose config` e `shellcheck` não rodaram; variáveis `LEGENDA_IA_*` no Render | `config` agora rodou (ok). `shellcheck` segue pendente. Variáveis no Render: item de Dashboard (`LEGENDA_IA_*`), não verificável daqui. |

**Proposta ao integrador:** atualizar R-16 em `riscos.md` para refletir que o item (1) está resolvido e que o item (4) está parcialmente resolvido (compose validado; `shellcheck` e conferência das variáveis no Render pendentes). Esta tarefa não edita `riscos.md`.

## 6. Decisões

Nenhuma decisão nova foi tomada. Não há proposta para `decisoes.md`.

## 7. Próximo passo

Antes do primeiro `up` por VPS, a equipe precisa de um `.env` de produção com valores reais (fora do repositório) e a tag de imagem publicada. Esse é o gatilho de escalada do R-16 e segue como condição de deploy.
