# T91 · Gabarito embutido na imagem do backend (DEC-51)

## O que foi feito
- `04_backend/app/scripts/exportar_gabarito_embutido.py`: chama `build_gabarito_from_markdown()` e grava `04_backend/app/data/gabarito_rfo.json` (UTF-8, indent=2, chaves ordenadas, sem timestamp, LF).
- `rfo_gabarito_parser.py`: `build_gabarito()` prefere o Markdown; se `RFO_INSPECAO_MD` não existir, carrega o JSON (caminho relativo a `__file__`) e registra em log a fonte usada. A lógica antiga virou `build_gabarito_from_markdown()`. `seed_gabarito.py` não precisou mudar (usa `build_gabarito` e só consulta por nome).
- `tests/test_gabarito_embutido.py`: equivalência Markdown vs JSON, fallback (monkeypatch), erro sem nenhuma fonte, determinismo do exportador (tmp_path).

## Contagens do gabarito
sistemas 15 · subsistemas 113 · tipos de anomalia 6 · tipos de falha 9 · localizações 47.

## Docker
`04_backend/Dockerfile` usa `COPY . .` (linha 21), logo cobre `app/data/`. `04_backend/.dockerignore` não exclui `app/data` (só .git, .venv, caches, .env etc.). Nada editado.

## Comandos e resultados
- `python -m app.scripts.exportar_gabarito_embutido` → JSON gerado e commitado.
- `pytest tests/test_gabarito_embutido.py` → 4 passed.
- `ruff check .` → All checks passed.
- **Suíte completa de `pytest` NÃO rodou:** `docker` não está disponível neste ambiente (PostgreSQL de 05_infra em localhost:5433 não subiu), a execução ficou pendurada e foi interrompida; além disso `tests/test_rfo_contexto.py` falha na coleta (`libpango` ausente, não relacionado). Testes de banco e a idempotência de `seed_gabarito` não foram verificados aqui.
