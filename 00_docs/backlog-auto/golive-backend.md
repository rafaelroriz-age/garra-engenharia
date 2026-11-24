# T110 · Go-live: backend verde (pytest + ruff) e prontidão de produção

Papel: Engenheiro Backend · Origem: DEC-59 · Data: 2026-11-24 · Branch: `worktree-backlog-T110`

Alvo: backend no Render com `04_backend/Dockerfile.render`, disco persistente montado,
`STORAGE_PROVEDOR=local` (ou `s3`) e front estático no GitHub Pages.

## 1. Resumo

| Item do Pronto | Situação |
|---|---|
| `ruff check .` em `04_backend` | **All checks passed!** |
| `pytest` em `04_backend` | **não está 100% verde**. Banco limpo: 865 passed, 24 failed, 0 erros (antes: 29 erros). 5 falhas corrigidas depois; as ~19 restantes são de ordem/event loop (passam isoladas) e de ambiente (container/zlib), com causa em §4. Nenhuma é falha do código de produção |
| `ENVIRONMENT=production` valida JWT/CORS | confirmado (`app/core/config.py`, `_validar_segredos_de_producao`) e coberto por teste novo |
| Migrations com `RUN_MIGRATIONS_ON_STARTUP=true` | confirmado no boot real da imagem `Dockerfile.render` (banco vazio → `d3e7a1c5f9b2`, head) |
| Storage local em diretório configurável por env | já era `STORAGE_LOCAL_DIR` (padrão `../05_infra/local/storage` mantido); documentado em `.env.example` com o caminho do disco do Render |
| `GET /health` sem auth | confirmado (200 sem token); agora também informa `storage` |
| Seed do admin | **não rodava no boot**; agora roda com `SEED_ON_STARTUP=true` (opcional) e o comando manual continua documentado |
| Variáveis do Render | §5 |

## 2. O que mudou (código)

| Arquivo | Mudança |
|---|---|
| `04_backend/app/core/config.py` | Novos campos `seed_on_startup`, `admin_email`, `admin_nome`, `admin_senha` (SecretStr) e constante `SENHA_ADMIN_PADRAO_DEV`. Fora de dev, `SEED_ON_STARTUP=true` exige `ADMIN_SENHA` com 12+ caracteres e diferente da senha padrão de dev (fail-closed, mesmo padrão do JWT). Sem `SEED_ON_STARTUP` nada muda para quem já roda produção. |
| `04_backend/app/core/bootstrap.py` (novo) | `semear_no_boot()` roda `seed_gabarito` (JSON embutido) e `seed_admin.criar_admin` (só com `ADMIN_SENHA`), ambos idempotentes. `verificar_storage_local()` testa criação/escrita em `STORAGE_LOCAL_DIR` (`ok` / `unavailable`; `nao_verificado` para s3, sem rede). |
| `04_backend/app/main.py` | `lifespan`: migrations → seeds (se `SEED_ON_STARTUP`) → log do estado do storage local. `/health` ganhou o campo `storage`; `status` vira `degraded` se o storage local não aceitar escrita. |
| `04_backend/app/scripts/seed_admin.py` | Sem `ADMIN_SENHA`, usa a senha padrão **só** em `ENVIRONMENT` de dev/teste (CI e E2E inalterados); fora disso sai com erro em vez de criar auditor com senha previsível (lacuna 6 de `00_docs/_preparo/01_sistema.md`). |
| `04_backend/Dockerfile.render` + `04_backend/render-start.sh` (novo) | **Bug real achado no smoke test**: o disco montado em tempo de execução tem dono root e o `USER appuser` não gravava nele (`/health` → `"storage":"unavailable"`). Agora o container inicia como root só para `mkdir` + `chown` de `STORAGE_LOCAL_DIR` e troca para `appuser` com `setpriv` (util-linux, já na imagem) antes do uvicorn. O uvicorn continua não-root (verificado: `Uid 1000`). |
| `04_backend/alembic/env.py` + `app/core/migrations.py` | Com migrations no boot, o `fileConfig` do Alembic baixava o root logger para WARN e desligava `app.*`: os logs do boot sumiam depois das migrations. `aplicar_migrations` passa `configure_logger=False` (padrão do Alembic); a CLI `alembic` segue igual. |
| `04_backend/.env.example` | Documentadas `RUN_MIGRATIONS_ON_STARTUP`, `SEED_ON_STARTUP`, `ADMIN_EMAIL`, `ADMIN_NOME`, `ADMIN_SENHA` e o uso de `STORAGE_LOCAL_DIR` absoluto no disco do Render. |

Arquivos fora do `Toca` da tarefa: `Dockerfile.render`, `render-start.sh` e `alembic/env.py`
(todos em `04_backend/`). Foram necessários para o boot de produção funcionar; registrado aqui
para o integrador.

### Testes (novos e corrigidos)

- **Novo** `tests/test_golive_boot.py` (13 funções, 15 casos com o parametrize): JWT/CORS em produção; `STORAGE_LOCAL_DIR`
  vindo do ambiente e padrão preservado; `SEED_ON_STARTUP` fail-closed (sem senha, curta, senha
  de dev); `seed_admin` recusa senha padrão fora de dev e mantém em dev; lifespan roda
  migrations + seeds só com as flags; `/health` sem auth com `storage` `ok`/`unavailable`;
  `semear_no_boot` sem senha só roda o gabarito.
- **Corrigidos (bugs dos próprios testes, nenhuma asserção relaxada):**
  - `test_ocorrencias_prioridade.py`: passava `headers=auth["Authorization"]` (string) ao
    `TestClient` → `ValueError: not enough values to unpack`. Agora `headers={"Authorization": ...}`.
  - `test_ocorrencias_regras.py`: a fixture criava duas inspeções no mesmo contrato, mas
    `inspecoes.contrato_id` é UNIQUE (1:1, `app/models/inspecao.py:29`) → 13 erros de setup.
    A segunda inspeção ganhou contrato próprio.
  - `test_relatorio_unicidade.py`: teardown fazia `session.delete(obj)` em objetos expirados após
    `rollback` → `MissingGreenlet`. Agora apaga por id, na ordem das FKs.
  - `test_legenda_ia_endpoints.py` (fixtures usadas também por `test_legenda_ia_aprovacao.py` e
    `test_seguranca_legenda_ia.py`): teardown não apagava `chamadas_ia` (telemetria BL-34, FK sem
    cascade para `usuarios` e `prompts_ia`) → `ForeignKeyViolationError` no teardown e lixo
    acumulado no banco de teste.
  - `test_seguranca_legenda_ia.py`: removidas 3 marcas `xfail(strict=True)` que viraram XPASS
    (SEG-IA-02, 03, 05 já corrigidas); `test_erro_de_arquivo_ausente…` liga o modo imagem no fake
    (único modo em que o arquivo é lido).
  - `test_seguranca.py::test_registro_publico_bloqueado…`: pré-condição explícita (garante um
    usuário antes de testar o bloqueio).

## 3. Verificação do boot de produção (smoke test)

Imagem `Dockerfile.render` construída deste worktree, rodando na rede do `05_infra`, banco novo
e descartável `garra_golive_t110b`, volume Docker novo montado em `/var/data` (simula o disco do
Render, dono root), sem nenhuma variável além das de §5:

```
ENVIRONMENT=production  JWT_SECRET_KEY=<64 hex>  BACKEND_CORS_ORIGINS=https://exemplo.invalid
POSTGRES_HOST/PORT/USER/PASSWORD/DB  RUN_MIGRATIONS_ON_STARTUP=true  SEED_ON_STARTUP=true
ADMIN_SENHA=<24 hex>  STORAGE_PROVEDOR=local  STORAGE_LOCAL_DIR=/var/data/storage  PORT=10000
```

Resultado (após a correção do `Dockerfile.render`):

```
GET /health → {"status":"ok",...,"environment":"production","database":"ok","storage":"ok"}
GET /docs → 404 (docs desligadas em produção)
GET /api/v1/edificacoes sem token → 401
POST /api/v1/auth/register sem token → 403 (admin já semeado: a janela do 1º registro está fechada)
INFO:app.main:Migrations aplicadas com sucesso.
INFO:app.core.bootstrap:Seed do gabarito no boot: {'sistemas_prediais': 15, 'subsistemas': 113, 'tipos_anomalia': 6, 'tipos_falha': 9, 'localizacoes': 47}
INFO:app.core.bootstrap:Seed do admin no boot: Usuário auditor 'admin@garra-engenharia.com.br' criado.
INFO:app.main:Storage local em /var/data/storage: ok
```

Segundo boot (`docker restart`): migrations sem mudança, gabarito idempotente, admin
"já existe — nada a fazer", 1 usuário e 113 subsistemas no banco. `/var/data/storage` ficou
`appuser:appuser` e o processo uvicorn roda com `Uid 1000`.

Antes da correção, com o mesmo volume: `"storage":"unavailable"` (`/var/data` `root:root`,
processo `appuser`).

## 4. Testes

### Como rodei

- `ruff check .` (venv `04_backend/.venv`, Windows): **All checks passed!**
- `pytest` no Windows: a coleta para em `tests/test_rfo_contexto.py` com
  `OSError: cannot load library 'libpango-1.0-0'` (WeasyPrint sem Pango no Windows; já
  registrado em T109). **Ambiente Windows**, não código.
- Por isso a suíte roda num container Linux com a imagem `05_infra-backend` (tem Pango) e o
  código deste worktree montado em `/app`, na rede `garra-net`, com as variáveis do serviço
  `backend` do compose e `POSTGRES_DB` trocado.
- Testes novos no Windows: `pytest tests/test_golive_boot.py tests/test_health.py tests/test_config_postgres_ssl.py` → **21 passed**.

### Suíte completa no banco `garra_engenharia_test` (estado antes das correções)

`19 failed, 842 passed, 7 skipped, 10 xfailed, 29 errors in 976.67s`. Classificação:

| Teste(s) | Causa | Tipo |
|---|---|---|
| `test_ocorrencias_regras.py` (13 erros de setup) | fixture com 2 inspeções no mesmo contrato (UNIQUE) | bug do teste → **corrigido** |
| `test_ocorrencias_prioridade.py` (5) | `headers=` com string | bug do teste → **corrigido** |
| `test_relatorio_unicidade.py::test_duplicata_levanta_integrity_error` (teardown) | `MissingGreenlet` no teardown | bug do teste → **corrigido** |
| `test_legenda_ia_aprovacao.py`, `test_legenda_ia_endpoints.py`, `test_seguranca_legenda_ia.py` (erros de teardown) | `chamadas_ia` não apagadas antes de `usuarios`/`prompts_ia` | bug do teste → **corrigido** |
| `test_legenda_ia_endpoints.py::test_gerar_escreve_apenas_campos_de_sugestao`, `test_seguranca_legenda_ia.py::test_erro_do_provedor_nao_vaza_detalhe_nem_grava_sugestao` | cache local da legenda IA (chave = prompt+modelo+contexto, sem a imagem no modo texto) acerta em `chamadas_ia` de execuções anteriores, deixadas porque o teardown quebrava: o fake não é chamado (`0 == 1`) | **poluição do banco de teste** (171 `chamadas_ia`, 153 usuários `bl34-*` sobrando). Passam no banco limpo |
| `test_seguranca_legenda_ia.py`: `test_regerar_apos_aprovar_limpa_aprovacao_anterior`, `test_editar_legenda_aprovada_nao_atribui_edicao_ao_aprovador_anterior`, `test_auxiliar_nao_aprova_legenda_ia` | **XPASS(strict)**: as lacunas SEG-IA-02/03/05 já foram corrigidas (T33/DEC-42), mas as marcas `xfail(strict=True)` ficaram | marcas obsoletas → **removidas** (o teste agora exige o comportamento correto; recomendação de `seguranca-legenda-ia-xfail-T107.md` §Próximos passos 2) |
| `test_seguranca_legenda_ia.py::test_erro_de_arquivo_ausente_nao_expoe_storage_key` (200) | o fake trabalha em modo texto, e nesse modo o serviço não lê o arquivo, por design (`legenda_ia/contrato.py:6`, `foto_service.py`); o caminho de erro `storage-key-inexistente` só existe no modo imagem | teste ajustado para ligar `fake_ia.enviar_imagem = True` e exercitar esse caminho; asserções iguais (4xx e chave não exposta) |
| `test_seguranca.py::test_registro_publico_bloqueado_quando_ja_existem_usuarios` (só no banco limpo: `201 == 403`) | dependia de já existir usuário no banco; num banco recém-migrado o 1º registro é aberto por design | pré-condição explícita (cria um usuário antes, aceitando 201/403); asserção final `403` mantida |
| `test_gabarito.py::test_endpoint_sistemas_prediais_lista_15_com_subsistemas` (`16 == 15`) | sobra `Sistema BL-34 …` de teardown quebrado | **poluição do banco de teste** |
| `test_snapshot.py::test_vetor_de_teste_recifra_igual_com_salt_e_iv_fixos` | o vetor fixo inclui `gzip`: zlib 1.3.2 (Windows, Python 3.14) gera bytes diferentes de zlib 1.3.1 (container, Python 3.12); decifrar o vetor passa | **ambiente** (passa no Windows: `2 passed`) |
| `test_exportar_dataset_legenda.py::test_recusa_saida_dentro_do_repositorio` | procura `.git` na raiz do repo; no container só `04_backend` está montado (`/.git` não existe) | **ambiente do container** |
| `test_legenda_ia_recuperacao.py::test_ingestao_le_somente_md_convertidos…` | lê `00_docs/convertidos`, fora do volume montado | **ambiente do container** |
| `test_ocorrencias_dashboard.py` (2), `test_portal_cliente.py` (3), `test_fotos_lacunas.py::…[JPEG]` (1) | `RuntimeError: … attached to a different loop` só na suíte completa; **passam isolados** (3, 7 e 27 passed) | interação de event loop entre módulos (engine global × loop de sessão do pytest-asyncio); não é regressão do código de produção |

Depois das correções de fixture, rodando só os arquivos afetados no mesmo banco:
`6 failed, 48 passed, 1 skipped, 3 xfailed`, 0 erros. Prioridade, regras, unicidade e aprovação
**verdes**; as 6 falhas restantes são as 2 de cache (poluição), os 3 XPASS(strict) e o
`arquivo_ausente`, todos tratados na tabela acima.

A barreira do backlog-auto (`[guard]`) proíbe apagar dados, então o lixo de
`garra_engenharia_test` **não foi limpo**. Ação humana sugerida (opcional): recriar o banco de teste
ou apagar as sobras de `chamadas_ia`, usuários `bl34-*` e `Sistema BL-34 *`.

### Suíte completa em banco limpo (`garra_t110_pytest`, criado por mim)

Banco novo `garra_t110_pytest`, `alembic upgrade head` + `python -m app.scripts.seed_gabarito`
(mesma ordem do CI), com as correções de fixture já aplicadas:

`24 failed, 865 passed, 7 skipped, 4 xfailed in 391.44s` e **0 erros** (antes: 29 erros).

| Falhas | Causa | Tipo |
|---|---|---|
| 15: `test_ocorrencias_dashboard` (2), `test_ocorrencias_prioridade` (3), `test_ocorrencias_regras` (6), `test_portal_cliente` (4) | `RuntimeError: … attached to a different loop` só na suíte completa; os mesmos arquivos passam isolados e juntos (prioridade + regras + unicidade + aprovação: verdes) | flakiness de event loop entre módulos (engine global com pool × loop de sessão do pytest-asyncio × loop próprio do `TestClient`); a contagem varia entre rodadas (6 na 1ª, 15 nesta) |
| `test_fotos_lacunas.py::…imagem_truncada…[JPEG]` | `201 == 422` só na suíte completa; isolado `27 passed` | dependente de ordem |
| 3 XPASS(strict) + `test_erro_de_arquivo_ausente…` + `test_registro_publico…` | ver tabela acima | **corrigidos** depois desta rodada |
| `test_snapshot` vetor, `test_exportar_dataset_legenda`, `test_legenda_ia_recuperacao` | zlib / volume do container | ambiente |

Depois das últimas correções, no mesmo banco limpo:
`pytest tests/test_seguranca.py tests/test_seguranca_legenda_ia.py tests/test_golive_boot.py tests/test_health.py`
→ `1 failed, 37 passed, 3 xfailed` (o `arquivo_ausente`), e após ajustá-lo
`pytest tests/test_seguranca_legenda_ia.py` → **`14 passed, 3 xfailed`**.

**A suíte completa não foi rodada de novo depois dessas últimas correções**: o shell da rodada
limpa foi encerrado pelo Claude Code por falta de memória na máquina (o container terminou sozinho e
a saída veio de `docker logs`). Esperado na próxima rodada completa, em banco limpo, neste
container: ~19 falhas = 16 de ordem/event loop + 2 do volume do container + 1 zlib.

**CI** (não verificado): `ci.yml` roda `pytest --maxfail=1` em Ubuntu com o repo inteiro, então as
2 falhas de volume não devem ocorrer lá; a do zlib depende da versão do runner; a flakiness de event
loop pode ocorrer e, com `--maxfail=1`, para a suíte na primeira.

## 5. Variáveis de ambiente do Render

Serviço web Docker com `Dockerfile Path = 04_backend/Dockerfile.render` e
`Docker Build Context = 04_backend`. Disco persistente montado em `/var/data`.
Nomes são case-insensitive (pydantic-settings). Não existe suporte a `DATABASE_URL`: use as
partes da Internal Connection String do Postgres do Render.

### Obrigatórias

| Variável | Valor no Render | Por quê |
|---|---|---|
| `ENVIRONMENT` | `production` | liga a validação fail-closed, HSTS e desliga `/docs` |
| `JWT_SECRET_KEY` | aleatória, 32+ caracteres (ex.: `openssl rand -hex 32`) | recusada se default/curta. Também assina as URLs de download do storage local: trocar invalida links já emitidos |
| `BACKEND_CORS_ORIGINS` | origem do GitHub Pages, ex.: `https://<conta>.github.io` (sem caminho, sem barra final; várias separadas por vírgula) | `*` é recusado em produção |
| `POSTGRES_HOST` | hostname interno do Postgres do Render | |
| `POSTGRES_PORT` | `5432` | o padrão do código já é 5432 |
| `POSTGRES_USER` | usuário do banco | |
| `POSTGRES_PASSWORD` | senha do banco | |
| `POSTGRES_DB` | nome do banco | padrão `garra_engenharia` |
| `RUN_MIGRATIONS_ON_STARTUP` | `true` | Render sem Pre-Deploy Command: `alembic upgrade head` no boot |
| `STORAGE_PROVEDOR` | `local` (disco) ou `s3` | padrão do código é `s3` |
| `STORAGE_LOCAL_DIR` | `/var/data/storage` (absoluto, dentro do disco) | **obrigatória com `local`**: o padrão relativo `../05_infra/local/storage` resolveria para `/05_infra/...`, fora do disco, e os arquivos sumiriam a cada deploy |

### Recomendadas para o go-live

| Variável | Valor | Por quê |
|---|---|---|
| `SEED_ON_STARTUP` | `true` | cria gabarito + admin antes de servir tráfego. Sem isso, o 1º `POST /api/v1/auth/register` (aberto enquanto não há usuários) vira auditor |
| `ADMIN_SENHA` | 12+ caracteres, segredo | **obrigatória se `SEED_ON_STARTUP=true`** (boot falha sem ela). Trocar a senha no 1º acesso |
| `ADMIN_EMAIL` | padrão `admin@garra-engenharia.com.br` | |
| `PUBLIC_BASE_URL` | `https://<servico>.onrender.com` | opcional: sem ela a URL de download é montada de `X-Forwarded-Proto/Host`, que o proxy do Render envia |

### Opcionais (têm padrão seguro)

`ADMIN_NOME` (`Administrador`), `POSTGRES_SSL` (`false`; só para conexão externa/Neon),
`JWT_ALGORITHM` (`HS256`), `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` (`60`), `LEGENDA_IA_PROVEDOR`
(`fake`; com `deepseek` exige `DEEPSEEK_API_KEY`), `DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`,
`DEEPSEEK_MODELO`, `DEEPSEEK_TIMEOUT_S`, `DEEPSEEK_ENVIAR_IMAGEM`, `DEEPSEEK_PRECO_*`,
`LEGENDA_IA_*` (limites, cache, RAG). `PORT` é injetada pelo Render (padrão 8000 no script).

### Só com `STORAGE_PROVEDOR=s3`

`MINIO_HOST` (host do endpoint S3, sem esquema), `MINIO_API_PORT` (ex.: `443`),
`MINIO_USE_SSL=true`, `MINIO_ROOT_USER` (access key), `MINIO_ROOT_PASSWORD` (secret key),
`MINIO_BUCKET_NAME` (padrão `relatorios-prediais`). Região fixa `us-east-1` em
`app/services/storage/s3_client.py`.

### Não usar no Render

`SNAPSHOT_SENHA`/`SNAPSHOT_USUARIO_EMAIL` (agente do PC, DEC-57) e as variáveis de `05_infra/.env`.

## 6. Seeds e comandos manuais

- Com `SEED_ON_STARTUP=true` + `ADMIN_SENHA`, nada manual é necessário (idempotente a cada boot).
- Sem isso, pelo Shell do serviço no Render (a partir de `/app`):
  `ADMIN_SENHA='<segredo>' python -m app.scripts.seed_admin` e `python -m app.scripts.seed_gabarito`.
  Fora de dev, `seed_admin` sem `ADMIN_SENHA` agora sai com erro.
- `seed_prompt_legenda` **não** roda no boot: lê `00_docs/ia/prompt-legenda-compacto.md`, que não
  está na imagem (contexto de build `04_backend`). Só importa com `LEGENDA_IA_PROVEDOR=deepseek`;
  com `fake` (padrão) o go-live não depende dele. Se precisar, use
  `python -m app.scripts.seed_prompt_legenda --arquivo <md copiado>`.

## 7. Riscos e pendências para o fechamento de lote

1. **Permissão do disco do Render**: verificado com volume Docker de dono root, não no Render
   real. Depois do deploy, conferir `GET /health` → `"storage":"ok"`. Se vier `unavailable`, o log
   do boot mostra `Storage local indisponível para escrita em …`.
2. `garra_engenharia_test` está poluído (§4); bancos descartáveis criados por mim neste servidor:
   `garra_golive_t110`, `garra_golive_t110b`, `garra_t110_pytest` e volumes `t110-disk`,
   `t110-disk2`, container parado `t110-render`, imagem `garra-render-t110`. A barreira impede que
   eu os apague; podem ser removidos à mão.
3. Flakiness de event loop na suíte completa (6 testes que passam isolados): candidata a tarefa
   própria (engine por loop ou `NullPool` nos testes).
4. `test_snapshot` vetor fixo depende da versão do zlib: proposta de tarefa para comparar o texto
   claro decifrado em vez dos bytes do envelope.
5. Para `00_docs/` no fechamento: README de `04_backend` (seção de deploy) e `05_infra/README.md`
   devem citar `SEED_ON_STARTUP`, `STORAGE_LOCAL_DIR=/var/data/storage` e o `render-start.sh`.

### Decisão proposta (para `decisoes.md`, não aplicada)

**P-T110**: no Render, o container inicia como root só para preparar o diretório do disco e roda o
uvicorn como `appuser` via `setpriv`; seeds idempotentes no boot com `SEED_ON_STARTUP`, que fora de
dev exige `ADMIN_SENHA` forte; `seed_admin` nunca usa senha padrão fora de dev/teste.
