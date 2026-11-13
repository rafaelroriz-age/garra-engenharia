# Serviço de prompts de IA e contrato LegendaIAClient (BL-37)

## API criada
- `app/services/legenda_ia/__init__.py`: `LegendaIAResultado` (legenda_sugerida, alertas, pendencias), Protocol `LegendaIAClient.gerar_legenda(imagem, prompt, legenda_bruta=None)` e `FakeLegendaIAClient` determinístico (contador `chamadas`). Sem cliente de provedor real (B-04).
- `app/services/prompt_ia_service.py`: `calcular_hash` (SHA-256 hex), `criar_versao` (versão incremental por nome, como string "1", "2"…; inicia inativa; conflito de concorrência → 409), `ativar` (desativa as demais do nome na mesma transação), `obter_ativo` (sem ativo → DomainError `prompt-ia-sem-versao-ativa`), `alterar_conteudo` (sempre recusa, 409 `prompt-ia-imutavel`).

## Propostas (não implementadas)
- O model `PromptIA` não tem coluna de hash; o hash é calculado por `calcular_hash` e gravado em `fotos.prompt_conteudo_hash` na geração (BL-34). Sem alteração de model/schema.
- `versao` é VARCHAR; o serviço ignora versões não numéricas ao calcular a próxima.

## Comandos e saídas
- Postgres em localhost:5433 estava no ar (`docker` indisponível no shell; verificado por socket). A migration f7c2a9d4e6b1 não estava aplicada no banco local; rodei `alembic upgrade head`.
- `pytest tests/test_prompt_ia_service.py`: 8 passed.
- `ruff check app/services tests/test_prompt_ia_service.py`: All checks passed. `ruff check .` completo reportou 9 erros fora desta tarefa (não verificados um a um); suíte completa não rodada.
