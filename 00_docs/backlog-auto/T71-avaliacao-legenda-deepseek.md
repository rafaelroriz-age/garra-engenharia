# T71 — Avaliação real da legenda IA com DeepSeek (BL-34)

**Status: NÃO EXECUTADA.** Tarefa humana; o job em background não tem as credenciais nem o ambiente necessários. Nenhum resultado foi inventado.

## O que bloqueou (verificado em 2026-11-12)

| Item | Situação |
|---|---|
| `DEEPSEEK_API_KEY` | Ausente no ambiente. Criar a chave na DeepSeek Platform e configurá-la só em env local e como secret no Render (`sync: false`). Passo humano (nunca no git). |
| PostgreSQL de teste | `docker compose` em `05_infra/` falhou: falta `POSTGRES_PASSWORD` em `05_infra/.env`. Banco não está no ar. |
| Código/Docs de IA | Esta branch (`worktree-backlog-T71`) não contém `00_docs/ia/plano-deepseek.md`, os Docs IA-01..IA-05 nem os scripts `app.scripts.seed_prompt_legenda` e `avaliar_legenda_ia`. Só o commit `21145c5` (RAG, BL-34) aparece em outra branch. É preciso integrar IA-01..IA-05 antes. |
| Preços/docs oficiais | Não consultados (sem rede/aprovação nesta sessão); preencher `DEEPSEEK_PRECO_*` a partir de api-docs.deepseek.com. |

## Roteiro para executar (interativo)

1. Chave DeepSeek: env local + secret no Render.
2. Conferir em api-docs.deepseek.com, por 1M tokens: entrada cache hit, cache miss, saída de `deepseek-flash` e `deepseek-v4-pro`; descontos fora de pico; fine-tuning; modelo com imagem. Preencher `DEEPSEEK_PRECO_*`.
3. LGPD: a API oficial processa dados fora do Brasil; com a minimização de IA-01 (sem cliente, endereço, pessoas) registrar decisão e risco residual. **Proposta de texto para DEC-XX** (a incluir no fechamento de lote): *"Uso da API oficial DeepSeek para legendas permitido apenas com payload minimizado (descrição técnica da foto, sem cliente, endereço ou pessoas); risco residual de transferência internacional aceito/mitigado por minimização; revisar se o payload voltar a incluir dados pessoais."* Atualizar R-10 em riscos.md.
4. `python -m app.scripts.seed_prompt_legenda` em banco de teste (a partir de 04_backend/).
5. `python -m app.scripts.avaliar_legenda_ia --modo live` em: baseline (RAG off), compacto (RAG off), compacto+RAG k=3, compacto+RAG k=5 — cada um em `deepseek-flash` e `deepseek-v4-pro` (pro limitado a 30 casos se o custo pedir). Repetir uma rodada para medir cache hit no 2º passe.

## Tabela de resultados (a preencher)

| Config | Modelo | Acurácia | Tokens hit | Tokens miss | Tokens saída | US$/legenda | US$/relatório 150 fotos | Latência |
|---|---|---|---|---|---|---|---|---|
| baseline | flash | — | — | — | — | — | — | — |
| baseline | v4-pro | — | — | — | — | — | — | — |
| compacto | flash | — | — | — | — | — | — | — |
| compacto | v4-pro | — | — | — | — | — | — | — |
| compacto+RAG k=3 | flash | — | — | — | — | — | — | — |
| compacto+RAG k=3 | v4-pro | — | — | — | — | — | — | — |
| compacto+RAG k=5 | flash | — | — | — | — | — | — | — |
| compacto+RAG k=5 | v4-pro | — | — | — | — | — | — | — |

## Configuração vencedora e escalonamento

Pendente. Hipótese a validar: flash por padrão; pro só com `nivel_certeza` baixo ou JSON inválido. Decidir após os dados se vale tarefa nova para implementar o escalonamento.
