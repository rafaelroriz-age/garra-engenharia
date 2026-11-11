# V1-07 — Cliente DeepSeek para legendas por IA

Papel: Engenheiro Backend. Branch do worktree: `worktree-backlog-T63` (fast-forward para `main` antes de
começar, pois a branch não continha `app/services/legenda_ia/`). Sem push.

## Passo 0 — documentação oficial (api-docs.deepseek.com, consultada em 2026-11-11)

- Base URL OpenAI-compatível: `https://api.deepseek.com`.
- Modelos vigentes: `deepseek-flash` (recomendado, DeepSeek-V4.1-Flash-1017) e `deepseek-v4-pro`. Os nomes
  `deepseek-v4-flash` e `deepseek-v4-flash-vision-exp` ainda são aceitos, mas os modelos estão aposentados
  (redirecionados ao Flash). `deepseek-chat` e `deepseek-reasoner` não aparecem mais na documentação.
- Imagem: o schema de `POST /chat/completions` aceita, em mensagens `user`, partes `image_url` (URL http(s) ou
  data URL base64; JPEG/PNG/GIF/WebP). **Porém a documentação não afirma que nenhum modelo da API processe
  imagem** (o único nome com "vision" foi aposentado). Conclusão: suporte a imagem **não confirmado**.
- `response_format: {"type":"json_object"}` exige instruir JSON no prompt; se a saída não for JSON válido a
  API devolve espaços, então conteúdo vazio deve ser tratado como inválido.
- A página só documenta HTTP 200/400; 401/429/500 são tratados genericamente (qualquer status ≠ 200).

Decisão de implementação: **modo `texto` por padrão** (prompt do cliente + legenda bruta delimitada, sem
imagem). O modo `imagem` (data URI JPEG ≤ 1024 px) está implementado e é ligado por `DEEPSEEK_ENVIAR_IMAGEM=true`
quando se confirmar um modelo com visão. O modo usado vai em `LegendaIAResultado.modo` e no log (sem imagem/chave).

## O que mudou

- `app/services/legenda_ia/deepseek.py` (novo): `DeepSeekLegendaIAClient`, `ProvedorIAIndisponivel` (502,
  `legenda-ia-indisponivel`), `reduzir_imagem_para_data_uri`. Saída inválida → `SaidaLegendaIAInvalida` (já usada no
  saneamento). O prompt vai em mensagem `system` (+ instrução de JSON); a legenda bruta delimitada em mensagem
  `user` separada (SEG-IA-08).
- `contrato.py`: `LegendaIAResultado.modo: str | None = None` (preservado por `sanear_resultado`, que usa `replace`).
- `config.py`: `LEGENDA_IA_PROVEDOR` (fake|deepseek, padrão fake), `DEEPSEEK_API_KEY` (`SecretStr`, opcional),
  `DEEPSEEK_BASE_URL`, `DEEPSEEK_MODELO` (padrão `deepseek-flash`), `DEEPSEEK_TIMEOUT_S` (30), e a extra
  `DEEPSEEK_ENVIAR_IMAGEM` (false). Fora de desenvolvimento, `deepseek` sem chave falha na inicialização.
- `obter_cliente_provedor()`: deepseek com chave → adapter; `fake` → `FakeLegendaIAClient` **só em
  desenvolvimento/test**; `fake` em produção e deepseek sem chave → 503 (evita servir legenda falsa em produção).
- Variáveis em `04_backend/.env.example`, `05_infra/.env.example`, `05_infra/docker-compose.yml` (backend) e
  `render.yaml` (`DEEPSEEK_API_KEY` com `sync: false`).
- Testes: `tests/test_legenda_ia_deepseek.py` (24, sem rede). Os dois testes existentes que esperavam 503 "sem
  provedor" (`test_legenda_ia_endpoints.py`, `test_legenda_ia_limites.py`) agora forçam `deepseek` sem chave via
  `monkeypatch`, pois o padrão passou a ser o fake.

## Resultados

- `pytest tests/test_legenda_ia_deepseek.py`: **24 passed**.
- `pytest tests/test_legenda_ia_limites.py`: 53 passed.
- Demais testes de legenda IA (`endpoints`, `seguranca`, `modelo`, `aprovacao`): 32 erros de *setup* neste ambiente
  (`passlib`/`bcrypt`: "password cannot be longer than 72 bytes" ao criar usuários nas fixtures) — problema de
  versão de `bcrypt` instalada, anterior a esta tarefa e sem relação com o código alterado; não foi possível
  validar por completo `test_gerar_sem_cliente_configurado_retorna_503` (erra no setup, antes do corpo). Os demais
  testes desses arquivos que rodam passaram (76 passed, 6 xfailed no conjunto).
- `ruff check` nos arquivos tocados: limpo. `ruff check .` completo: 10 erros pré-existentes em
  `alembic/versions/e5a1f0c2b7d4_*`, `tests/test_fotos_storage_key_unico.py`, `tests/test_portal_versoes_relatorio.py`,
  `tests/test_relatorio_unicidade.py` (não tocados).
- Não foi feita chamada real à DeepSeek (sem chave, sem rede).

## Para o fechamento de lote (00_docs/projeto/*, não editado aqui)

- Registrar B-04 como decidido (DeepSeek Platform API; modelo padrão `deepseek-flash`; modo texto até confirmar visão).
- Risco/decisão proposta: legendas sem imagem só usam a anotação do usuário; avaliar modelo com visão antes de
  ligar `DEEPSEEK_ENVIAR_IMAGEM`.
- Atualizar `00_docs/backlog-auto/legenda-ia-env-deploy.md` (T40) com as novas variáveis `DEEPSEEK_*`.
