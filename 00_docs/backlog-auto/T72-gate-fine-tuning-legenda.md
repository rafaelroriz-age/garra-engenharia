# T72 — Gate de fine-tuning da legenda IA (BL-34)

**Status: TODO — gate não verificado; tarefa não iniciada.** Conforme a instrução da tarefa ("só iniciar quando o export de IA-06 tiver ≥500 legendas aprovadas; até lá, deixe em todo"), nenhum passo de fine-tuning foi executado. Nenhum resultado foi inventado.

## Por que o gate não pôde ser checado neste worktree

| Item | Situação (2026-11-12) |
|---|---|
| Código do export (IA-06) | `04_backend/app/scripts/exportar_dataset_legenda.py` existe só em `main` (commits `de9dc5c` / merge `fc7b02b`). Não está no branch `worktree-backlog-T72`. |
| Docs de referência | `00_docs/ia/plano-deepseek.md` e `00_docs/backlog-auto/ia-dataset-feedback.md` existem em `main`, não neste branch. Não foram integrados aqui. |
| Acesso ao banco | PostgreSQL responde em `localhost:5433`, mas não há `04_backend/.env` nem `DATABASE_URL` configurado neste ambiente. Credenciais não foram procuradas nem usadas. |
| Dependências | `psycopg` não instalado no Python disponível. Docker não está instalado, então `05_infra/docker-compose.yml` não pôde ser levantado. |
| Chave DeepSeek | `DEEPSEEK_API_KEY` ausente (também pendente em T71). |

Consequência: não há contagem confirmada de legendas aprovadas. O número de aprovadas no banco de produção/desenvolvimento é desconhecido para esta execução.

## Para destravar (passos humanos)

1. Integrar `main` (ou cherry-pick de `de9dc5c` e dos docs IA) no branch de trabalho, por decisão do integrador.
2. Configurar `04_backend/.env` local com `DATABASE_URL` apontando para o banco certo (fora do git).
3. Rodar, a partir de `04_backend/`, com saída **fora do repositório**:
   `python -m app.scripts.exportar_dataset_legenda --saida <pasta-fora-do-git> --min-registros 500`
   O próprio script recusa gravar se houver menos de 500 aprovadas, o que serve como gate.
4. Se o gate passar: seguir o roteiro da tarefa (teste 20%, comparação no harness IA-03 contra a configuração vencedora de IA-07, decisão go/no-go).

## Proposta de decisão (para o fechamento de lote)

Nenhuma DEC nova nesta execução. Pendência já registrada em `ia-dataset-feedback.md`: política de retenção/privacidade do dataset exportado (fora do git, acesso restrito), a alinhar com B-04.

## Verificação

Nenhum código foi alterado. Este commit contém apenas este documento. `pytest` e `ruff` não foram executados porque não há mudança de código.
