# Correções — Fotos (BL-11, lacunas de T16, DEC-39)

Tarefa T19 do backlog automático. Corrige o mínimo por lacuna listada em `revisao-regras-fotos.md`, seguindo a proposta DEC-39 (ainda "Proposta"; este trabalho não altera `decisoes.md`). Sem migration, sem alteração de models, sem frontend.

## Tabela das 9 lacunas

"Antes" = situação descrita/prevista na revisão da T16 (por leitura; a linha de base **não foi medida**, ver Execução). "Depois" = resultado após a correção, com os testes rodados (ver Execução).

| # | Lacuna | Antes | Depois | Arquivo:linha | Teste |
|---|---|---|---|---|---|
| 1 | `storage_key` do vínculo vinda do cliente (A01) | Qualquer string aceita; `DELETE /fotos/{id}` apagaria qualquer objeto do bucket | Só chave no padrão do servidor (`fotos/<uuid>.<jpg\|png\|webp>`, `fullmatch`) **e** existente no bucket (`head_object`); senão 422 RFC 7807 (`storage-key-invalida` / `storage-key-inexistente`) | `app/services/foto_service.py:25-50`; `app/services/storage/base.py:37` e `s3_client.py:99` (`exists`); `app/api/v1/fotos.py` (injeta `storage` nos vínculos) | `test_lacuna_4` (×4), `test_lacuna_4b` — passam |
| 2 | Mesma chave em duas `Foto` | Aceito; apagar uma removia o objeto da outra | 409 `storage-key-ja-vinculada`, checado na aplicação (`get_by_storage_key`). **Sem `UNIQUE(storage_key)`**: exigiria migration (fora de escopo) | `app/services/foto_service.py:47`; `app/repositories/foto_repository.py:15` | `test_lacuna_4c` — passa |
| 3 | EXIF de orientação descartado sem `exif_transpose` | Foto de celular em pé gravada deitada | `ImageOps.exif_transpose` antes de converter/redimensionar/recodificar | `app/services/image_processing.py:85` | `test_lacuna_8c`, `test_lacuna_8b` (EXIF continua removido) — passam |
| 4 | `legenda`/`ordem`/`origem` sem validação | `ordem` negativa, `origem` livre, `legenda` de 1 MB aceitas | `origem` = `Literal["upload_manual","lightshot","clipboard"]`; `ordem >= 0`; `legenda <= 500`; `storage_key <= 255` (422 via Pydantic) | `app/schemas/foto.py:9, 63-66, 78-79` | `test_lacuna_6`, `6b`, `6d` — passam |
| 5 | `PUT` ignora `legenda: null` | Impossível limpar a legenda | `PUT` aplica só os campos enviados (`model_dump(exclude_unset=True)`); `null` explícito limpa | `app/api/v1/fotos.py:120`; `app/repositories/foto_repository.py:48`; `app/services/foto_service.py:135` | `test_lacuna_6c` — passa |
| 6 | Upload órfão sem descarte | Objeto ficava para sempre no MinIO | Novo `DELETE /fotos/upload` (corpo `{storage_key}`, 204): valida o padrão da chave, recusa chave já vinculada (409), apaga o objeto. Declarado antes de `/fotos/{foto_id}` | `app/api/v1/fotos.py:124`; `app/services/foto_service.py:151` | `test_lacuna_9b` — passa |
| 7 | Arquivo lido inteiro antes do limite de 25 MB; sem limite de corpo | `await arquivo.read()` sem teto; base64 sem teto | Multipart lido com teto (`read(MAX+1)`), excesso vira 422 `arquivo-excede-tamanho-maximo`; base64 com `max_length` = tamanho do base64 de 25 MiB (422). **Limite de corpo no proxy/Uvicorn ficou adiado** | `app/api/v1/fotos.py:49`; `app/schemas/foto.py:53` | `test_lacuna_2`, `2b` — passam |
| 8 | Imagem truncada → risco de 500 | Tratado por `OSError`; sem guarda de regressão | Sem mudança de código (já correto); teste mantido como guarda | `app/services/image_processing.py` | `test_lacuna_3` (PNG, JPEG) — passam |
| 9 | Sem teto de pixels | Só `DecompressionBombError` a ~179 Mpx | Teto explícito de 50 Mpx (`MAX_PIXELS_DECODIFICADOS`), checado pelo cabeçalho antes de `verify()`; 422 `imagem-excede-pixels-maximos` | `app/services/image_processing.py:36, 55` | Sem teste (exigiria imagem de >50 Mpx; não testado) |

## Ajustes fora da lista

- **`tests/test_rbac_auxiliar.py::test_auxiliar_vincula_foto_a_visita_com_autoria`**: o teste vinculava uma chave inventada (`fotos/<uuid>.jpg`, nunca enviada) com `origem="upload"`, o que a regra correta (lacuna 1 e 4) rejeita. O comportamento de RBAC do auxiliar (BL-42) testado ali, ou seja, o auxiliar vincula e vira autor, não mudou. Só a preparação do teste mudou: ele faz upload real e usa `origem="upload_manual"`. Nenhum `test_lacuna_*` foi alterado quanto à regra.
- **`app/repositories/ocorrencia_repository.py:9`**: o `main` estava com a importação quebrada (`Inspecao`, `SistemaPredial`, `Subsistema` sem import, ruff F821; `from app.models import Ocorrencia` só). O app não importava e nenhum teste de API rodava. Restaurei o import. Provável perda na integração da T08 (`f9c6f8d`). Fora do escopo de fotos, mas necessário para rodar qualquer teste.
- `tests/test_fotos_lacunas.py`: só `ruff --fix` da ordem dos imports (I001).
- A branch do worktree nasceu de um commit antigo (sem a T16); avancei-a por fast-forward até `main`.

## Adiado (fora do escopo / depende de decisão)

- **`UNIQUE(storage_key)`** no modelo (DEC-39 A): exige migration; a unicidade ficou só na aplicação, com janela de corrida entre duas requisições simultâneas.
- **Alternativa mais forte** da DEC-39 A (upload cria `Foto` pendente e o vínculo informa `foto_id`): não aplicada.
- **Leitura de fotos com URL pré-assinada** (DEC-39 E) e a pendência de endpoint público do MinIO (infra).
- **Limite de corpo no proxy/Uvicorn** (DEC-39 F): infra. Hoje o multipart é spooled pelo Starlette; o teto de leitura e a checagem de 25 MB já protegem a memória do processo.
- **Job de limpeza** de `fotos/*` órfãs com mais de 24 h (DEC-39 D, alternativa): só o endpoint de descarte foi feito.
- **Vínculo usuário↔contrato** (DEC-27/L15): qualquer membro da equipe ainda vincula, edita e descarta qualquer foto/upload. `DELETE /fotos/upload` herda essa limitação.
- **Teto de 50 Mpx**: câmeras de 108/200 Mpx de celular passam a ser recusadas. Valor sugerido pela DEC-39; revisar se o campo reclamar.
- Mudança de comportamento a notar: `PUT` com `ordem: null` explícito agora limpa `ordem` (antes era ignorado).

## Execução

Ambiente: PostgreSQL `localhost:5433` e MinIO `localhost:9000` respondiam (socket); `docker` não existe neste shell, então `docker compose ps` não foi executado. O banco estava **sem migrations**: rodei `python -m alembic upgrade head` (de `d3b7c9e4f1a2`, head atual). Não há `.env` no worktree, então o MinIO respondia 403 com credenciais vazias; os testes rodaram com `MINIO_ROOT_USER`/`MINIO_ROOT_PASSWORD` do `05_infra/.env.example` passados só por variável de ambiente do processo (nada foi gravado ou commitado).

- **Linha de base (antes da correção): não medida.** Quando a infra foi liberada, o código já estava alterado. A coluna "Antes" é a previsão da T16.
- `python -m pytest tests/test_fotos.py tests/test_fotos_lacunas.py tests/test_rbac_auxiliar.py -q`: **44 passed, 1 skipped** (72 s). O skip é `test_rbac_auxiliar.py:176` (gabarito de sistemas prediais não semeado, `app.scripts.seed_gabarito`), sem relação com fotos.
- `ruff check .` em `04_backend`: **10 erros restantes**, todos preexistentes e fora das áreas tocadas (`app/scripts/vistoria_cautelar_layout_extractor.py`, `tests/test_ocorrencias_regras.py`, `tests/test_visitas_lacunas.py`, `tests/test_vistoria_cautelar_*`). Os arquivos alterados estão limpos.
- `python -m pytest -q --continue-on-collection-errors` (suíte completa): 162 passed, 36 failed, 18 errors, 3 skipped. As falhas ficam em `test_edificacoes`, `test_models`, `test_ocorrencias_prioridade`, `test_ocorrencias_regras`, `test_visitas_lacunas` (`RuntimeError: There is no current event loop`, testes de lacuna de Visitas/Ocorrências ainda sem correção) e 5 módulos de templates sem `openpyxl`/`pdfplumber` instalados. Nenhuma toca fotos; **não comparei com uma linha de base** sem as minhas mudanças.
- Frontend não foi tocado: `npm run lint`/`build` não rodaram.
