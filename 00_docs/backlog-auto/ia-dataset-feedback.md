# IA-06 (T70) — Export do dataset de feedback da legenda IA

**Tarefa:** T70 · **Item:** BL-34 (RF-15, RN-16, RN-17) · **Status:** integrada na `main` (commits `de9dc5c`, merge `fc7b02b`).

## O que foi entregue

- `04_backend/app/scripts/exportar_dataset_legenda.py` — CLI de **somente leitura** no banco.
- `04_backend/tests/test_exportar_dataset_legenda.py` — 7 testes (distância de edição; recusa/aceite de `--saida`; só aprovadas, JSONL e ausência de dados pessoais; métricas/CSV; filtros `--desde/--ate/--min-registros`; banco inalterado).

Uso, a partir de `04_backend/`:

```bash
python -m app.scripts.exportar_dataset_legenda --saida D:/dados/legenda \
    [--desde 2026-01-01] [--ate 2026-12-31] [--min-registros 500]
```

Atenção: `--saida` é uma **pasta** (gera dois arquivos), não um arquivo como dizia o texto "Pronto" do backlog.

## Formato

| Arquivo | Conteúdo |
|---|---|
| `dataset_legenda.jsonl` | uma linha por foto com `status_validacao_ia='aprovada'` e sugestão não nula: `{"messages":[system, user, assistant]}`. `system` = prompt da versão usada + instrução JSON do adapter; `user` = idêntico ao enviado pelo adapter DeepSeek (`ContextoLegenda` já sem dados pessoais); `assistant` = JSON de saída com a legenda **final** do auditor |
| `metricas_legenda.csv` | `foto_id, aprovado_em, distancia_edicao, aceita_sem_edicao, nivel_certeza_ia, modelo, modo, prompt_ia_id, prompt_versao, sistema, tipo_anomalia` |

`distancia_edicao` = Levenshtein(sugerida, final) / max(len), com espaços normalizados (0 = aceita sem edição; 1 = reescrita total). O comando imprime resumo (n, % aceitas sem edição, distância média por sistema).

## Salvaguardas

- `--saida` dentro de repositório git é **recusada** (`SaidaNoRepositorio`): dados de cliente não vão para o git.
- Todo texto livre passa de novo por `limpar_dados_pessoais` (CPF/CNPJ/e-mail/telefone). É rede de segurança por regex, **não** anonimização garantida — revisar a amostra antes de qualquer envio a terceiros (relevante para a decisão LGPD de T71/B-04).
- `--min-registros` impede gravar dataset abaixo do gate.

## Uso futuro

- **Harness de avaliação (IA-03):** a distância de edição e a taxa de aceitação sem edição são o sinal de acurácia em produção; o JSONL serve de conjunto rotulado.
- **Fine-tuning (gate T72, ≥500 aprovadas):** o formato chat é consumível diretamente por LoRA/SFT; `--min-registros 500` materializa o gate.

## Verificação neste fechamento

Esta sessão de fechamento roda em worktree sem o código da T70 e só altera documentação; **não reexecutei** `pytest` nem `ruff`. O resultado dos testes no PostgreSQL de 05_infra consta do registro do integrador na `main` e não foi conferido aqui.

## Decisão proposta

Nenhuma nova DEC. Pendência para T71/T72: política de retenção/privacidade do dataset exportado (fora do git, acesso restrito) — alinhar com B-04.
