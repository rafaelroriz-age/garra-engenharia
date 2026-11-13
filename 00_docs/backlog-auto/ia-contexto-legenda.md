# IA-01 / BL-34 — Contexto técnico só texto na legenda IA (T65)

Plano: `00_docs/ia/plano-deepseek.md` itens 1–3. Provedor: API oficial DeepSeek, **só texto** (decisão do usuário).

## O que mudou
- **`legenda_ia/contexto.py`** (novo): `ContextoLegenda` (legenda bruta, tipo de anomalia, sistema/subsistema,
  ambiente, descrição, GUT, grau de risco, NBRs `codigo+descricao`, tipo de relatório), `canonico()` (JSON ordenado,
  NBRs ordenadas, estável — chave de cache futura), `bloco_dados()` e `async montar_contexto(db, foto, legenda_bruta=...)`.
  Lê ocorrência → inspeção → contrato (NBRs) por consultas explícitas; foto só de visita usa a inspeção da visita.
  Minimização (R-10): nenhum nome de cliente/endereço/pessoa/id/data; `limpar_dados_pessoais` troca CPF, CNPJ,
  e-mail e telefone por `[CPF]`/`[CNPJ]`/`[EMAIL]`/`[TELEFONE]` na legenda bruta, descrição, localização e descrição de NBR.
  É rede de segurança por regex, **não** anonimização garantida (nome de pessoa em texto livre não é detectado).
- **Protocolo**: `gerar_legenda(contexto, prompt, imagem=None)`. `FakeLegendaIAClient` e `ClienteLegendaIAProtegido`
  atualizados; o protegido delimita (SEG-IA-08) só `legenda_bruta` via `replace(contexto, ...)`.
  Clientes expõem `enviar_imagem`; `foto_service` só baixa a foto do storage quando é `True`
  (`DEEPSEEK_ENVIAR_IMAGEM=true`) — modo texto não toca o MinIO.
- **Mensagens**: `system = prompt + instrução JSON` (nada variável; docstring explica o cache de prefixo da DeepSeek);
  `user = bloco "DADOS DA OCORRÊNCIA" + "LEGENDA BRUTA" + legenda delimitada` (no modo imagem, parte `image_url` + texto).
- **Saída**: aceita `legenda_sugerida` ou `legenda_tecnica` (prompt do cliente). `nivel_certeza`:
  `causa_documentalmente_comprovada`→`causa_comprovada`; `nao_aplicavel`→None; desconhecido→None + alerta.
  `status_validacao` do modelo não é gravado (sempre `rascunho`); `aprovada_com_ressalva`/`revisar`/`informacao_insuficiente`
  e valores desconhecidos viram alerta. `foto.nivel_certeza_ia` é preenchido.
  `LegendaIAResultado` ganhou `nivel_certeza`, `uso` (prompt_tokens, prompt_cache_hit_tokens, prompt_cache_miss_tokens,
  completion_tokens, quando há `usage`) e `modelo`.
- **Retry**: até 2 novas tentativas, backoff `0,5·2^n` s (`backoff_s` configurável), só 429, 5xx e timeout; demais 4xx e erro de rede falham na hora.

## Testes
- Novo `tests/test_legenda_ia_contexto.py`; `test_legenda_ia_deepseek.py` ampliado (system byte a byte idêntico,
  contexto só no user, enums, usage, retry com `httpx.MockTransport`); ajustados `test_legenda_ia_limites.py`
  (+ teste de que o modo texto não baixa imagem), `test_seguranca_legenda_ia.py`, `test_prompt_ia_service.py`.
- `pytest tests/test_legenda_ia_contexto.py tests/test_legenda_ia_deepseek.py tests/test_legenda_ia_limites.py tests/test_prompt_ia_service.py` → **119 passed**.
- Com o Postgres de 05_infra (5433 no ar) + endpoints/segurança/fotos: 128 passed, 6 xfailed, **38 errors** — todos por
  fixture de usuário: `passlib`×`bcrypt` do ambiente (`ValueError: password cannot be longer than 72 bytes`), anteriores a esta tarefa;
  **os testes de banco de endpoints (`test_legenda_ia_endpoints`, `aprovacao`, `test_seguranca_legenda_ia` parcial, `test_fotos`) não rodaram de fato**.
  Coleta de `test_ltip_templates`, `test_rfo_contexto`, `test_vistoria_*_templates` falha por falta de `pdfplumber`/`libpango` no ambiente.
- `ruff check` nos arquivos tocados: limpo. `ruff check .` tem 10 erros preexistentes (migration e5a1f0c2b7d4,
  `test_fotos_storage_key_unico`, `test_portal_versoes_relatorio`, `test_relatorio_unicidade`), fora do escopo.
- Não rodei `npm` (frontend intocado).

## Observações / decisões propostas
- A branch do worktree não tinha a T63; foi feito `git merge main` local (sem push) para obtê-la.
- IA-02: o adapter aceita `legenda_sugerida` e `legenda_tecnica`; o prompt compacto pode usar qualquer uma.
- Reexecutar os testes de endpoint após corrigir o ambiente (ex.: `pip install "bcrypt<4.1"`).
