# Revisão de regras — Fotos (BL-11, upload e vínculo a Visitas/Ocorrências)

Tarefa T16 do backlog automático. Revisão **por leitura** de `04_backend/app/api/v1/fotos.py`, `app/services/foto_service.py`, `app/services/image_processing.py`, `app/services/storage/s3_client.py`, `app/schemas/foto.py`, `app/models/foto.py` e `tests/test_fotos.py`, contra RF-05, RN-03/RN-11/RN-15/RN-18, RNF-05/RNF-07, DEC-19, DEC-27 e DEC-29 #4 e o achado S-10/S-11 de `00_docs/projeto/revisao-seguranca-owasp.md` (A08/A10, já conformes — não repetidos aqui). **Nenhum código de produção foi alterado.** Testes novos: `04_backend/tests/test_fotos_lacunas.py` (27 casos coletados, `test_lacuna_*`, afirmam o comportamento correto).

> Nota: o RNF-02 do `estudo-do-contexto.md` é "operação offline: não necessária" (DEC-26); "otimização de imagem no upload" não está nele. O requisito aplicável é RNF-06/R-03 (benchmark BL-22, redimensionamento a 2000 px), citado no docstring de `image_processing.py`. Os modelos `test_lacuna_*` de Ocorrências citados na tarefa não existem neste repositório (`grep test_lacuna` em `tests/` sem resultado; não há `revisao-regras-ocorrencias.md`), então o formato abaixo é próprio.

## O que já está correto (confirmado no código)

- Tipo real por magic bytes (`Image.open` + `verify`, só JPEG/PNG/WEBP) e recodificação que descarta EXIF/metadados (A08).
- Chave de **upload** gerada pelo servidor: `fotos/<uuid4>.<ext>`; o nome do arquivo do cliente nunca entra na chave.
- Limite de 25 MB (`MAX_UPLOAD_SIZE_BYTES`) checado em `_validar_tamanho`; arquivo vazio rejeitado; base64 inválido → 422.
- Redimensionamento a 2000 px no lado maior.
- RBAC: todos os endpoints usam `require_equipe` (auditor + auxiliar); `cliente` recebe 403; autoria vem do token (`criado_por_id`), não do payload.
- URL pré-assinada de 15 min; nenhuma URL externa aceita (A10).

## Lacunas encontradas

| # | Lacuna | Regra | Gravidade | Teste | Esperado hoje |
|---|---|---|---|---|---|
| 1 | `storage_key` do **vínculo** vem do cliente sem validação: aceita `../../x`, `/abs`, prefixo diferente de `fotos/` e chave que não existe no bucket. Um auditor/auxiliar pode apontar uma `Foto` para qualquer objeto do bucket (por exemplo, de outro contrato) e depois apagá-lo via `DELETE /fotos/{id}`. | A01/RNF-07, "chave controlada pelo servidor" | **Alta** | `test_lacuna_4` (4 parametrizações), `test_lacuna_4b` | falha |
| 2 | A mesma `storage_key` pode ser vinculada a duas `Foto`; apagar uma remove o objeto da outra (referência pendurada). Não há `UNIQUE(storage_key)` no modelo. | integridade RNF-07 | Média | `test_lacuna_4c` | falha |
| 3 | EXIF de orientação é descartado sem `ImageOps.exif_transpose`: foto de celular em pé (Orientation 6/8) é gravada deitada e sai girada nos PDF/DOCX. | RF-05, qualidade do relatório | **Alta** (uso principal é celular, DEC-26) | `test_lacuna_8c` | falha |
| 4 | `legenda`, `ordem` e `origem` sem validação de domínio: `ordem` negativa, `origem` texto livre (o doc fala em `upload_manual`/`lightshot`), `legenda` sem teto (1 MB aceito). | RN-03/RN-11, A04 | Média | `test_lacuna_6`, `6b`, `6d` | falham |
| 5 | `PUT /fotos/{id}` ignora `legenda: null` (o repositório só atualiza se `is not None`): não dá para apagar a legenda. | RN-03 (legenda editável) | Baixa | `test_lacuna_6c` | falha |
| 6 | Upload nunca vinculado deixa objeto órfão no MinIO para sempre; não existe descarte nem rotina de limpeza (o editor de anotação de DEC-19 gera vários uploads descartados). Teste assume `DELETE /fotos/upload` com `storage_key` (contrato **proposto**). | RNF-07 | Média | `test_lacuna_9b` | falha (rota não existe) |
| 7 | Arquivo grande é lido inteiro em memória (`await arquivo.read()`) antes da checagem de 25 MB; não há limite no corpo da requisição (Uvicorn/proxy). Base64 idem (+33%). | RNF-07, DoS | Média | `test_lacuna_2`, `2b` (26 MB) | pode passar (retorna 422 depois de ler tudo); falha se vier 500 |
| 8 | Imagem truncada: `verify()` pode passar e a recodificação falhar fora do `try` esperado. Está tratado por `OSError` hoje; o teste trava a regressão para 500. | A08 | Baixa | `test_lacuna_3` (PNG, JPEG) | provável passa |
| 9 | Sem teto de pixels explícito: `Image.MAX_IMAGE_PIXELS` padrão só dispara `DecompressionBombError` a ~179 Mpx (aviso a 89 Mpx); um PNG pequeno em bytes pode ocupar GBs ao descomprimir. **Não testável** de forma leve (exigiria gerar imagem de ~180 Mpx). | A08/DoS | Média | — | n/a |

## Verificações que devem passar (guardas contra regressão)

`test_lacuna_1` (GIF como `.png`), `1b` (HTML como `.jpg`), `5` (visita inexistente → 404), `7` (cliente → 403 em todos os endpoints), `7b` (401 sem token), `7c` (auxiliar envia/vincula e vira autor), `7d` (autoria não forjável), `8` (redimensionamento ≤ 2000 px), `8b` (EXIF removido), `9` (DELETE apaga o objeto), `10` (URL expira ≤ 15 min e não contém a senha do storage).

## Lacunas não testadas (só Doc)

- **Foto "de outro contexto"/autorização por contrato:** DEC-27 diz que o auxiliar atua "nos contratos em que atua", mas o modelo não relaciona usuário↔contrato; qualquer membro da equipe edita/apaga qualquer foto e vincula a qualquer visita. Depende de decisão (ver propostas).
- **Sem leitura de URL:** `FotoRead` devolve `storage_key` e `url_publica` (sempre `None`); só o upload devolve URL pré-assinada. Não há endpoint nem campo para obter URL de uma foto já vinculada, e o frontend (`03_frontend/src`) não referencia fotos. Respeita RNF-07, mas deixa BL-11 sem fluxo de exibição; é o que explica o "🟢 parcial".
- **URL pré-assinada e chave:** a URL contém `bucket/<storage_key>` e o host interno do `MINIO_ENDPOINT_URL`. A chave aleatória não é segredo; já a URL com host interno (`localhost:9000`/rede docker) não funciona em produção sem endpoint público. Registrar como pendência de infra, não de teste.
- **Remoção parcial:** `remover()` apaga o objeto e depois o registro; se o commit falhar, a `Foto` fica apontando para objeto inexistente. Raro, baixo impacto.
- **RN-15:** o sistema não retém a versão sem marcação (decisão assumida em DEC-19); nenhum teste necessário.
- **Reprocessamento sem teto de qualidade:** JPEG regravado com qualidade padrão do Pillow (75); PNG grandes de screenshot não ficam menores. Aceitável, mas sem requisito numérico.

## Decisões propostas (não aplicadas; para o fechamento de lote)

1. **DEC-proposta A:** o vínculo deve aceitar apenas `storage_key` que (a) case `^fotos/[0-9a-f-]{36}\.(jpg|png|webp)$`, (b) exista no bucket (`head_object`) e (c) ainda não esteja vinculada (`UNIQUE(storage_key)` + migration com `downgrade()`). Alternativa mais forte: o upload grava um registro `Foto` "pendente" e o vínculo só informa `foto_id`, eliminando a chave vinda do cliente.
2. **DEC-proposta B:** aplicar `ImageOps.exif_transpose` em `reprocessar_imagem` antes de descartar o EXIF.
3. **DEC-proposta C:** enum fechado para `origem` (`upload_manual`, `lightshot`, `clipboard`), `ordem >= 0`, `legenda` com `max_length` (sugestão 500) e `PUT` com campos "presentes" (`model_fields_set`) para permitir limpar a legenda.
4. **DEC-proposta D:** descarte de upload órfão (endpoint `DELETE /fotos/upload` ou job de limpeza de `fotos/*` sem `Foto` com mais de 24 h).
5. **DEC-proposta E:** leitura de fotos com URL pré-assinada gerada na resposta (campo `url`), para fechar o fluxo de exibição de BL-11.
6. Definir o limite de corpo (proxy/Uvicorn) e `Image.MAX_IMAGE_PIXELS` explícito (ex.: 50 Mpx).

## Execução

- `pytest tests/test_fotos.py tests/test_fotos_lacunas.py`: **não rodou.** Ao tentar conectar (socket, 2 s), `localhost:5433` (PostgreSQL) e `localhost:9000` (MinIO) não responderam; `docker` não existe neste ambiente. Os testes de fotos exigem os dois serviços reais. Nenhum resultado foi inventado; a tabela "Esperado hoje" é uma **previsão por leitura do código**, a confirmar no primeiro `pytest` com a infra no ar (`docker compose up -d` em `05_infra/`).
- `pytest --collect-only tests/test_fotos_lacunas.py`: 27 testes coletados sem erro de importação.
- `ruff check tests/test_fotos_lacunas.py`: sem erros. `ruff check .` em `04_backend`: 246 erros **preexistentes** (alembic/versions, etc.), nenhum no arquivo novo; fora do escopo desta tarefa.
