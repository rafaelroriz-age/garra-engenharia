# IA-05 / BL-34 — Telemetria de custo e cache local da legenda IA (T68)

Plano: `00_docs/ia/plano-deepseek.md` item 5. Risco: R-10 (custo com 150+ fotos por relatório).

## O que mudou
- **Migration `b8d4f2a6c1e7`** (`alembic/versions/b8d4f2a6c1e7_chamadas_ia_telemetria_bl_34.py`, `down_revision a9c3e5f7b1d2`):
  tabela `chamadas_ia` (id uuid, criado_em, usuario_id FK null, foto_id FK null **ON DELETE SET NULL**, finalidade
  `legenda_foto`, provedor, modelo, modo, prompt_ia_id FK null, prompt_conteudo_hash, chave_cache (índice), origem
  `api`|`cache_local`, sucesso, erro_tipo, tokens_prompt/cache_hit/cache_miss/saida, custo_estimado_usd Numeric(12,6) null,
  latencia_ms, resposta JSONB null) com CHECK de finalidade e origem. `downgrade()` remove índice e tabela.
  Modelo em `app/models/chamada_ia.py` (`ChamadaIA`, exportado em `app.models`).
- **`app/services/legenda_ia/telemetria.py`**: `chave_cache(prompt_hash, modelo, contexto, extra="")` (sha256 do JSON canônico;
  `extra` separa modo texto/imagem — em imagem entra a `storage_key`), `buscar_em_cache(db, chave, ttl_h)` (só `origem='api'`,
  `sucesso`, `resposta` não nula, dentro do TTL; `ttl<=0` desliga), `registrar(db, ...)`, `custo(uso, Precos)`,
  `Precos.de_settings`. Custo = (hit·p_hit + miss·p_miss + saída·p_saída)/1e6; `miss` sai de `prompt_tokens − hit` se faltar;
  sem `uso` ou sem os 3 preços → `None`.
- **Config** (`Settings`): `LEGENDA_IA_CACHE_TTL_H` (720), `DEEPSEEK_PRECO_ENTRADA_CACHE_HIT_USD`,
  `DEEPSEEK_PRECO_ENTRADA_CACHE_MISS_USD`, `DEEPSEEK_PRECO_SAIDA_USD` (USD/1M tokens; vazio = `None`, validador converte `""`).
  Repassadas em `04_backend/.env.example`, `05_infra/.env.example`, `05_infra/docker-compose.yml` e `render.yaml`.
  Os preços reais ficam para a tarefa humana IA-07 (página oficial de preços).
- **`foto_service.gerar_legenda_ia`** (novo parâmetro opcional `usuario_id`, passado por `fotos.py`): calcula a chave → consulta o
  cache → *hit*: usa o resultado, registra `cache_local` (tokens 0, latência 0) e **não chama o cliente nem baixa a imagem**;
  *miss*: chama o cliente, mede latência (`perf_counter`) e registra `api` com `uso`/custo/`resposta`; erro do provedor é
  registrado (`erro_tipo` = `type_suffix` ou nome da classe; sem mensagem, sem chave) e relançado. O resultado do cache é
  gravado na foto como antes e passa por `_invalidar_aprovacao` (DEC-42 inalterado). A telemetria do sucesso entra na mesma
  transação do commit da foto (`commit=False`); a do erro faz commit próprio.
- **`GET /api/v1/ia/uso?de=&ate=`** (`app/api/v1/ia_uso.py`, router incluído em `app/main.py`, `require_auditor`): linhas por
  dia (UTC) e modelo com chamadas, `chamadas_api`, `chamadas_cache_local`, erros, tokens, `pct_tokens_cache_hit`
  (hit/(hit+miss) dos tokens de entrada, `null` sem tokens) e `custo_estimado_usd` (`null` se nenhum preço). Padrão: últimos
  30 dias; `de > ate` → 422. 403 para auxiliar, 401 sem token.

## Validação da migration (banco temporário, não o de dev)
Banco `garra_bl34_tmp2` criado em `garra-postgres` (localhost:5433) com `CREATE DATABASE`; `POSTGRES_DB` apontado para ele.
`alembic heads` antes: único head `a9c3e5f7b1d2`; depois: único head `b8d4f2a6c1e7`.
`alembic upgrade head` → `downgrade -1` → `upgrade head` sem erro; `alembic current` = `b8d4f2a6c1e7 (head)`.
O banco `garra_bl34_tmp2` **não foi apagado** (a barreira do backlog-auto bloqueia `DROP DATABASE`): pode ser removido à mão.
O banco de dev (`garra_engenharia`) não foi tocado; ele precisa de `alembic upgrade head` antes de usar o recurso.

## Testes
Todos os comandos com `POSTGRES_DB=garra_bl34_tmp2`, `POSTGRES_PORT=5433` (PostgreSQL e MinIO de 05_infra no ar).
- `tests/test_legenda_ia_telemetria.py` (novo, 14 testes): custo (com preços, miss derivado, nulo sem uso/preços, config vazia →
  None), chave estável e sensível a prompt/modelo/contexto/extra, 2ª geração idêntica vem do cache (Fake contador: 1 chamada),
  custo registrado com preços da env, TTL expirado chama de novo, contexto diferente não usa cache, erro registrado sem conteúdo e
  não vira cache, endpoint (403 auxiliar, 401, 422 período inválido, agregação por dia/modelo e `pct_tokens_cache_hit == 60.0`).
  Resultado: **14 passed**.
- `tests/test_legenda_ia_limites.py`: o `_BancoFalso` ganhou `execute/add/flush` (sem cache, sem persistir) porque o serviço agora
  consulta e grava telemetria; sem isso 13 testes quebravam com `AttributeError`.
- Resultados medidos: `telemetria` **14 passed**; `limites + seguranca + aprovacao` (com o `_BancoFalso` corrigido) **54 passed, 6 xfailed,
  17 errors** (todos `passlib×bcrypt`, fixtures de usuário); `limites + deepseek + contexto + prompt_ia_service` antes do ajuste do
  `_BancoFalso`: 106 passed, 13 failed (corrigidos depois; `limites`/`seguranca`/`aprovacao` rodaram no 54 passed acima).
- **NÃO verificado:** `tests/test_legenda_ia_endpoints.py` e os testes de banco de `aprovacao` (regerar invalida aprovação, DEC-42)
  não rodaram de verdade. Com o contorno de bcrypt a execução apareceu com vários `F`/`E` (causa não inspecionada) e foi
  encerrada pelo sistema por falta de memória; não reexecutei. Rodar de novo em máquina com o bcrypt corrigido
  (`pip install "bcrypt<4.1"`) e conferir `test_legenda_ia_endpoints.py` e `test_legenda_ia_aprovacao.py`.
- `ruff check .` em `04_backend`: **All checks passed** (sem erros; os 10 preexistentes citados na T65 já não aparecem).

## Ambiente
- Bug do ambiente `passlib × bcrypt>=4.1` (`ValueError: password cannot be longer than 72 bytes`) derruba as fixtures de usuário
  dos testes antigos (`hash_password`). Meus testes usam hash fixo. Para rodar os antigos de verdade usei
  `pip install --target <tmp> "bcrypt<4.1"` + `PYTHONPATH`, sem alterar o ambiente global (o `requirements.txt` já fixa `bcrypt<4.1`).
- Sem `.env` no worktree: as credenciais foram lidas do `.env` do checkout principal só em variáveis de processo.

## Decisões propostas (não gravadas em `decisoes.md`)
- **DEC-?? cache local da legenda IA:** chave = sha256(prompt_hash, modelo, contexto canônico [+ storage_key em modo imagem]);
  só resultado de sucesso da API, TTL 720 h por padrão, `0` desliga. Cache hit continua exigindo aprovação (volta a `rascunho`).
- `chamadas_ia.foto_id` é `SET NULL`: o histórico de custo sobrevive à exclusão da foto; `resposta` guarda a legenda saneada
  (dado do relatório; sem retenção definida — avaliar política/expurgo junto de R-10).
- O limite de taxa (DEC-42 C) continua contando o `cache_local` (a dependência roda antes do serviço); avaliar se hits devem poupar cota.

## Para o fechamento de lote
`backlog-tarefas.md`/`kanban`/`status.md` (BL-34 telemetria), `decisoes.md` (propostas acima), `riscos.md` (R-10: custo agora
medido; cache local mitiga regeração), `04_backend/README.md` (tabela `chamadas_ia`, endpoint `/api/v1/ia/uso`, 4 variáveis novas),
`05_infra/README.md` (variáveis no compose/render).
