# Plano — DeepSeek na legenda IA (RF-15): acurácia e custo

Data: 2026-11-11. Ponto de partida: T63 (V1-07, `00_docs/backlog-auto/v1-legenda-ia-deepseek.md`) já entregou
`DeepSeekLegendaIAClient` (modo texto, `deepseek-flash`, JSON mode). Este plano é a fase seguinte, executada pelo
**Bloco E** do `BACKLOG.md` (origens IA-01 a IA-08).

## Decisões de partida (do usuário)
- Provedor: **API oficial DeepSeek** (`https://api.deepseek.com`). Implica tráfego de dados para fora do Brasil →
  registrar DEC e atualizar R-10 (tarefa humana IA-07) e minimizar dados enviados (IA-01).
- **Só texto**: a foto não é enviada (a documentação não confirma modelo com visão). A acurácia vem do contexto
  textual: legenda bruta + ocorrência (tipo de anomalia, sistema, GUT, grau de risco, descrição) + NBRs do contrato.

## Por que não há fine-tuning agora
- A API DeepSeek não oferece fine-tuning; o V4 é grande demais para self-host econômico.
- Não há dados rotulados: as triplas `legenda_bruta → legenda_ia_sugerida → legenda` aprovada nascem com o uso.
- Substituto imediato: **"fine-tuning por contexto"** — few-shot dinâmico com legendas aprovadas parecidas (RAG).
- Caminho futuro: exportar o dataset (IA-06) e decidir num gate humano (IA-08), com ≥500 legendas aprovadas,
  entre manter few-shot ou LoRA num modelo aberto menor.

## Arquitetura
1. **Contexto só texto** (`legenda_ia/contexto.py`): `ContextoLegenda` montado a partir da foto/ocorrência/contrato,
   sem nome de cliente, endereço, CPF/CNPJ ou nomes de pessoas. `foto_service` deixa de baixar a imagem quando o
   modo é texto (economiza MinIO e latência).
2. **Saída completa**: mapear `nivel_certeza` e `status_validacao` do prompt do cliente para os enums do banco
   (`foto.py`), preencher `nivel_certeza_ia`; capturar `usage` (prompt, cache hit, cache miss, completion).
3. **Prefixo cacheável**: a DeepSeek cobra muito menos pelos tokens de entrada que batem no cache automático de
   prefixo. Ordem fixa das mensagens: `system` (prompt compacto + instrução JSON, idêntico em toda chamada) →
   few-shots → `user` com os dados variáveis (legenda bruta delimitada, SEG-IA-08). Nada variável (data, ids) no
   `system`.
4. **Prompt compacto**: o prompt do cliente (`00_docs/cliente/prompt-lado-cliente.md`, ~800 linhas) vira uma versão
   enxuta com as mesmas regras, versionada em `prompts_ia` (`legenda_foto`) por script de seed idempotente.
5. **Telemetria e cache local**: tabela `chamadas_ia` (modelo, modo, tokens, custo estimado, latência, hash do
   prompt, chave de cache, erro). Antes de chamar a API, reaproveita resultado com a mesma chave
   `sha256(prompt_hash + modelo + contexto canônico)` dentro do TTL.
6. **RAG por busca textual** (Postgres FTS `portuguese` + `pg_trgm`, sem embeddings — a DeepSeek não tem API de
   embeddings): (a) legendas aprovadas com mesmo tipo de anomalia/sistema → few-shot; (b) trechos dos relatórios
   históricos de `00_docs/convertidos/` (anonimizados) → referência; (c) `contrato_nbrs` do contrato.
   Embeddings/pgvector só se a avaliação mostrar ganho.
7. **Avaliação**: golden set extraído do Relatório Fotográfico convertido (situação, GUT, classificação, tipo de
   anomalia, grau de risco por foto) e harness com modo `replay` (offline, CI) e `live` (com chave). Métricas:
   JSON válido, ≤481 caracteres, termos preservados, acerto de classificação/grau, distância de edição para a
   legenda humana, tokens e US$/legenda.

## Tarefas (Bloco E do BACKLOG.md)
| Origem | Tarefa | Ambiente |
|---|---|---|
| IA-01 | Contexto só texto, minimização de dados, enums, usage e retry | offline |
| IA-02 | Prompt compacto com prefixo estável + seed de `legenda_foto` | offline |
| IA-03 | Golden set + harness de avaliação (replay/live) | offline |
| IA-04 | Telemetria `chamadas_ia` + cache local de resposta + resumo de uso | docker |
| IA-05 | RAG por FTS/pg_trgm (legendas aprovadas, relatórios históricos, NBRs) | docker |
| IA-06 | Export do dataset de feedback (JSONL, anonimizado) | docker |
| IA-07 | Rodada real: chave, preços, DEC/LGPD, baseline vs RAG, flash vs pro | humano |
| IA-08 | Gate de fine-tuning (≥500 aprovadas) | humano |
