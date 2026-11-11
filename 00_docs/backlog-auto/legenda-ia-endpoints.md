# Endpoints de legenda por IA com cliente injetável (BL-34, sem adapter concreto)

- **Tarefa:** T25. BL-34 sem o adapter do provedor de LLM; DEC-37 DP-3, DP-4, DP-5 e DP-6 (RF-15, RN-16, RN-17, RN-18; ADR-12).
- **Base:** BL-36/T22 (colunas de IA em `fotos`, migration `f7c2a9d4e6b1`) e BL-37/T23 (`prompt_ia_service.py`, `LegendaIAClient`, `FakeLegendaIAClient`).
- **Branch:** `worktree-backlog-T25` (sem push). Commit: `feat(backend): endpoints de legenda por IA com cliente injetável (BL-34)`, `Refs BL-34`.
- **Sem** migration, sem mudança em models, sem frontend e sem chamada a provedor real. **Variáveis de ambiente novas:** nenhuma.
- **Documentos de gestão não editados:** `backlog-tarefas.md`, `backlog-kanban.md`, `status.md`, `decisoes.md`, `riscos.md`, `BACKLOG.md`.

---

## 1. Pré-requisito de ordem

| Verificação | Resultado |
|---|---|
| `git log --oneline -1` (início) | `14ead2f` (`backlog: disparo de D03`): a branch **não tinha** BL-36 nem BL-37 (`app/services/legenda_ia/` e `00_docs/backlog-auto/legenda-ia-modelo.md` ausentes) |
| Ação | `git merge --ff-only main` → `c402b86` (`backlog: disparo de T25`). Fast-forward, sem commit de merge |
| `alembic heads` | `f7c2a9d4e6b1 (head)`, uma única head |
| `alembic current` no banco local | `d3b7c9e4f1a2`: faltavam `e5a1c3f7b9d2` (BL-10) e `f7c2a9d4e6b1` (BL-36), ambas já em `main` e com `downgrade()`. Aplicadas com `alembic upgrade head` (sem migration nova desta tarefa) |

---

## 2. Contrato dos endpoints

### `POST /api/v1/fotos/{foto_id}/legenda-ia/gerar`

| Item | Valor |
|---|---|
| Perfil | `require_equipe` (`auditor`, `auxiliar`), igual às demais rotas de foto (RN-18/DEC-27) |
| Corpo (opcional) | `{"legenda_bruta": "texto"}` (`LegendaIAGerarPayload`, até 5000 caracteres). Ausente: reaproveita `fotos.legenda_bruta` gravada. Enviado: substitui a gravada (inclusive `null`) |
| Fluxo | foto (404) → prompt ativo de nome `legenda_foto` (422) → imagem pelo `StorageClient` de BL-07 → `LegendaIAClient.gerar_legenda(imagem, prompt.conteudo, legenda_bruta)` |
| Escreve | `legenda_ia_sugerida`, `legenda_bruta` (se enviada), `alertas_ia`, `pendencias_ia`, `prompt_ia_id`, `prompt_conteudo_hash` (SHA-256 do conteúdo), `legenda_ia_gerada_em`, `status_validacao_ia = "rascunho"` |
| Nunca escreve | `legenda`, `aprovado_por_id`, `aprovado_em`, `nivel_certeza_ia` (o `LegendaIAResultado` de BL-37 não traz nível de certeza) |
| Resposta | 200 + `FotoRead` |

| Status | `type` (sufixo) | Quando |
|---|---|---|
| 401 | — | sem token / token inválido (resolvido **antes** da dependência de IA) |
| 403 | `acesso-negado` | perfil fora da equipe (`cliente`, `contratante`) |
| 404 | `foto-nao-encontrada` | foto inexistente |
| 422 | `prompt-ia-sem-versao-ativa` | não há versão ativa de `legenda_foto` em `prompts_ia` |
| 422 | `storage-key-inexistente` | o objeto da foto não está no bucket |
| 503 | `legenda-ia-indisponivel` | nenhum cliente de IA configurado (dependência de produção, B-04 pendente) |

Com a dependência de produção, o 503 sai na resolução das dependências: 404/422 só aparecem quando há cliente configurado.

### `PUT /api/v1/fotos/{foto_id}` (ajuste)

| Campo | Regra |
|---|---|
| `legenda` | ausente preserva; `null` explícito limpa; texto substitui (DP-5, por `model_fields_set`) |
| `ordem` | ausente preserva; `null` limpa (inalterado desde T19) |
| `aprovar_legenda_ia` | novo, `bool`, default `false`. `true` aprova a sugestão: `legenda` = texto enviado ou, se ausente, `legenda_ia_sugerida`; `status_validacao_ia = "aprovada"`; `aprovado_por_id` = usuário do token; `aprovado_em` = agora (UTC) |
| `aprovado_por_id`, `aprovado_em`, `status_validacao_ia`, `legenda_ia_sugerida` | **não** fazem parte do payload; se enviados, são ignorados (extra ignorado pelo Pydantic) |

| Status | `type` (sufixo) | Quando |
|---|---|---|
| 422 | `legenda-ia-sem-sugestao` | `aprovar_legenda_ia: true` em foto com `status_validacao_ia = NULL` |
| 422 | `legenda-aprovada-vazia` | aprovação com `legenda` `null` ou só espaços |

Sem `aprovar_legenda_ia`, o `PUT` não toca nos campos de IA: edição manual numa foto sem sugestão mantém `status_validacao_ia = NULL`.

### Dependência injetável (DP-6)

`app/services/legenda_ia/__init__.py:get_legenda_ia_client` é a dependência FastAPI. Hoje ela lança `DomainError` 503 (RFC 7807). Os testes a sobrescrevem com `app.dependency_overrides[get_legenda_ia_client] = lambda: FakeLegendaIAClient()`. O adapter real de BL-34 passará a ser devolvido por ela, sem mudar o endpoint nem o serviço.

---

## 3. Regras DP-3, DP-4, DP-5 (e DP-6) no código

| Regra | O que garante | Arquivo:linha |
|---|---|---|
| DP-3 | aprovação só no `PUT`, com flag explícita | `04_backend/app/schemas/foto.py:112`, `04_backend/app/services/foto_service.py:155` |
| DP-3 | `aprovado_por_id` e `aprovado_em` vêm do token, nunca do payload | `04_backend/app/services/foto_service.py:171-172`; usuário passado ao serviço em `04_backend/app/api/v1/fotos.py:119,124` |
| DP-3 | aprovar exige sugestão e legenda não vazia | `04_backend/app/services/foto_service.py:158-168` |
| DP-3 | `status_validacao_ia = aprovada` | `04_backend/app/services/foto_service.py:170` |
| DP-4 | a geração escreve só os campos de sugestão e põe `rascunho` | `04_backend/app/services/foto_service.py:200-208` |
| DP-4 | `legenda` só muda no `PUT` (a geração não a toca) | `04_backend/app/services/foto_service.py:176-211` (nenhuma escrita em `foto.legenda`); `PUT` em `foto_service.py:169` e `foto_repository.py:50-52` |
| DP-2 (parte restante) | `prompt_conteudo_hash` gravado na geração | `04_backend/app/services/foto_service.py:206` |
| DP-5 | `legenda: null` limpa, ausente preserva (`model_fields_set`) | `04_backend/app/api/v1/fotos.py:123`; aplicação em `04_backend/app/repositories/foto_repository.py:50-52` |
| DP-6 | cliente injetado; sem provedor → 503 | `04_backend/app/services/legenda_ia/__init__.py:42-54`; `04_backend/app/api/v1/fotos.py:134` |
| RN-18 | `auxiliar` gera e aprova (mesmo perfil das rotas de foto) | `04_backend/app/api/v1/fotos.py:119,131` |

Testes correspondentes em `04_backend/tests/test_legenda_ia_endpoints.py`:

| Teste | Regra |
|---|---|
| `test_gerar_escreve_apenas_campos_de_sugestao` | DP-4, DP-2 (hash), `legenda` intacta |
| `test_gerar_sem_legenda_bruta_preserva_a_existente` | DP-4 (`legenda_bruta` só se enviada) |
| `test_gerar_foto_inexistente_404` | 404 |
| `test_gerar_sem_prompt_ativo_retorna_erro_de_dominio` | 422 `prompt-ia-sem-versao-ativa`, cliente não chamado |
| `test_gerar_sem_cliente_configurado_retorna_503` | DP-6, dependência de produção |
| `test_aprovar_usa_usuario_do_token_e_ignora_campos_do_payload` | DP-3 |
| `test_aprovar_com_legenda_editada` | DP-3/DP-4 (texto revisado, sugestão preservada, RN-17) |
| `test_aprovar_sem_sugestao_ou_com_legenda_vazia_e_recusado` | DP-3 |
| `test_put_legenda_null_limpa_e_campo_ausente_preserva` | DP-5 |
| `test_edicao_manual_sem_sugestao_mantem_campos_de_ia_nulos` | DP-1/DP-5 |
| `test_auxiliar_gera_e_aprova[visita]`, `[ocorrencia]` | RN-18/DEC-27 |
| `test_usuario_sem_permissao_recebe_403` | perfil `cliente` → 403 nas duas rotas |
| `test_sem_token_recebe_401_antes_do_503` | ordem das dependências |

---

## 4. Escolhas onde DEC-37 não fixava o detalhe

1. **Nome do prompt:** `legenda_foto` (`foto_service.PROMPT_LEGENDA_IA_NOME`). Os testes trocam o nome por um único por teste (`monkeypatch`) para não depender de dados do banco.
2. **Sinal de aprovação:** campo `aprovar_legenda_ia: bool` no `PUT`, em vez de aceitar `status_validacao_ia` do cliente; assim os campos de aprovação nunca vêm do payload.
3. **Aprovar sem `legenda`:** aceita a sugestão como está. Com `legenda`, grava o texto revisado. A minuta (`legenda_ia_sugerida`) é preservada nos dois casos (RN-17).
4. **Regenerar uma foto já aprovada:** volta para `rascunho` e mantém `legenda` e `aprovado_por_id`/`aprovado_em` como estavam (a geração não escreve campos de aprovação). Pelo DP-9, o relatório continua usando `legenda`.
5. **Ordem 401/403 → 503:** o usuário é declarado antes do cliente na rota, para que um anônimo não descubra o estado do provedor.

### Ponto em aberto para o integrador (proposta, não registrada em `decisoes.md`)

- **DP-10 (proposta):** um `PUT` que altera `legenda` de foto já `aprovada` **sem** `aprovar_legenda_ia` mantém hoje `status_validacao_ia = aprovada` e o aprovador anterior. Pela L9 de T22 ("quem edita é quem aprova") o mais coerente seria tratar essa edição como nova aprovação pelo usuário do token, ou exigir a flag (422). Não foi implementado para manter a menor mudança; precisa de decisão do dono.

---

## 5. Comandos e saídas

Ambiente: PostgreSQL e MinIO de `05_infra/docker-compose.yml` no ar. `docker compose ps` a partir de `05_infra` não roda neste worktree (`required variable POSTGRES_PASSWORD is missing a value: defina POSTGRES_PASSWORD em 05_infra/.env`, porque o `.env` ignorado não existe no worktree); `docker ps` mostrou `garra-postgres` (healthy, `127.0.0.1:5433`) e `garra-minio` (healthy, `127.0.0.1:9000-9001`). Nenhum serviço subiu nem caiu. O `.env` ignorado de `04_backend` foi copiado do checkout principal (não commitado). Os testes rodaram com `POSTGRES_HOST=127.0.0.1` e `MINIO_HOST=127.0.0.1` porque `localhost` tenta `::1` primeiro no Windows e cada conexão demora ~2 s. O `.venv` de `04_backend` do checkout principal está quebrado (`No module named 'greenlet._greenlet'`); usei o `.venv` da raiz.

Todos os comandos a partir de `04_backend`.

| Comando | Saída |
|---|---|
| `alembic upgrade head` | `Running upgrade d3b7c9e4f1a2 -> e5a1c3f7b9d2` e `Running upgrade e5a1c3f7b9d2 -> f7c2a9d4e6b1` |
| `pytest tests/test_legenda_ia_endpoints.py` | **14 passed**, 1 warning in 495.72s (rodado ainda com `localhost`, daí a lentidão) |
| `pytest tests/test_legenda_ia_endpoints.py tests/test_fotos.py tests/test_fotos_lacunas.py tests/test_rbac_auxiliar.py tests/test_rbac_portal.py tests/test_legenda_ia_modelo.py tests/test_prompt_ia_service.py` | 22 failed, **73 passed** in 148.03s. **Todos** os testes de fotos (BL-11, T19), de RBAC e os 14 novos passaram. As 22 falhas são de `test_legenda_ia_modelo.py` (14) e `test_prompt_ia_service.py` (8): `RuntimeError: There is no current event loop in thread 'MainThread'` |
| `pytest tests/test_legenda_ia_modelo.py tests/test_prompt_ia_service.py` (isolados) | **32 passed** in 8.76s |
| `pytest tests/test_fotos.py tests/test_prompt_ia_service.py` (sem o arquivo novo) | 8 failed, 8 passed: a falha **já existe** em `main` |
| `pytest` (suíte completa) | **não concluído.** 1ª tentativa: 5 erros de coleta (`ModuleNotFoundError: openpyxl`/`pdfplumber` no `.venv` da raiz, em `test_{ltip,rfip,rfo,vistoria_cautelar,vistoria_residencial}_templates.py`). 2ª tentativa, ignorando esses 5 módulos: interrompida pelo sistema por falta de memória, sem saída. Não foi relançada |
| `ruff check .` | `Found 9 errors`, todos em arquivos fora desta tarefa e já presentes em `main` (`app/scripts/vistoria_cautelar_layout_extractor.py`, `tests/test_ocorrencias_regras.py`, `tests/test_vistoria_cautelar_*.py`; ruff 0.15.1) |
| `ruff check` nos 5 arquivos tocados | `All checks passed!` |
| `npm run lint` / `npm run build` | não se aplica (frontend não tocado) |

**Falha preexistente (não corrigida, fora do escopo):** os módulos de teste síncronos que usam `asyncio.run` (`test_fotos.py`, `test_rbac_auxiliar.py` e, por seguir o mesmo padrão, `test_legenda_ia_endpoints.py`) deixam o loop de evento da thread principal em `None`. Os testes `async def` rodados depois deles, com o loop de sessão do pytest-asyncio 0.26 (`asyncio_default_test_loop_scope = session` em `pytest.ini`), quebram. Isolados, passam. Proposta: trocar `asyncio.run` nesses módulos por fixtures async ou por um runner próprio, numa tarefa separada.

---

## 6. Pendências

| Pendência | Depende de | Observação |
|---|---|---|
| Adapter concreto de `LegendaIAClient` (BL-34, L12/L22) | B-04 (escolha do provedor de LLM) | Implementar a classe e devolvê-la em `get_legenda_ia_client`; variável de ambiente nova (chave/modelo) entra em `04_backend/.env.example`. Mapear `nivel_certeza_ia` se o provedor devolver o nível |
| Retenção e privacidade dos dados enviados ao provedor (L13, R-10) | decisão do cliente + B-04 | Imagem e `legenda_bruta` saem do sistema na geração. Sem política aprovada, a rota não deve ser habilitada em produção (a dependência continua 503) |
| Edição de legenda já aprovada sem nova aprovação | dono (DP-10 proposta) | Ver §4 |
| Outros pipelines chamarem `legenda_para_relatorio` (DP-9) | BL-38 | Já registrado em T24; fora do escopo |
| Frontend (campo editável, botão "aprovar") | tarefa de frontend | Contrato na §2 |
