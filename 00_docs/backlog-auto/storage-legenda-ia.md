# BL-07 — Storage x legendas/artefatos de IA

## 1. Cobertura do storage (`04_backend/app/services/storage/`)
| Capacidade | Situação | Onde |
|---|---|---|
| Upload | Coberto (limite 25 MB; override explícito para artefatos maiores) | `s3_client.py:72` |
| Download | Coberto (`ObjectNotFoundError`) | `s3_client.py:88` |
| Delete (idempotente) | Coberto | `s3_client.py:99` |
| URL pré-assinada de leitura, expiração curta | Coberto (default 15 min; `expires_in<=0` rejeitado) | `s3_client.py` `generate_presigned_url`; usada em `foto_service.py:43` |
| Checagem de existência | **Faltava** → `exists()` (HEAD; 404/NoSuchKey → False) | `s3_client.py`, `base.py` |
| Listagem por prefixo | **Faltava** → `list_keys(prefix)` (paginado) | `s3_client.py`, `base.py` |
| Órfãos | **Novo** → `listar_orfaos(chaves_registradas, prefix)` em `StorageClient`; só leitura | `base.py` |

`fotos.py` consome o storage via `Depends(get_storage_client)` (linhas 32-33, 41, 55, 118); o upload devolve `storage_key` + URL pré-assinada (46-47, 59-60); o delete remove vínculo e objeto (122). Conclusão: compatível com artefatos de IA (legendas/imagens geradas) usando a mesma interface e chaves com prefixo próprio (ex.: `ia/...`).

## 2. Mudanças necessárias em `fotos.py` (NÃO feitas — fora do escopo)
- Item E de BL-11 (URL de leitura): `fotos.py` só devolve URL no upload. Falta endpoint/campo de leitura (ex.: `url` na listagem de fotos da ocorrência) chamando `storage.generate_presigned_url(foto.storage_key, ...)`.
- Job de limpeza: chamar `storage.listar_orfaos(<select Foto.storage_key>, prefix=...)` (`app/models/foto.py:27`); hoje não há tarefa agendada.
- `StorageClient` ganhou 2 métodos abstratos (`exists`, `list_keys`); não há outras subclasses no repo, mas fakes futuros devem implementá-los.

## 3. Política proposta para órfãos (decisão do dono — nada é apagado automaticamente)
1. Rodar `listar_orfaos` periodicamente (ex.: semanal) só gerando relatório/log.
2. Considerar apagar apenas objetos com idade > 24 h (evita corrida upload → vínculo; exigirá expor `LastModified`, não incluído aqui).
3. Começar com dry-run; apagar só com aprovação manual da lista ou, se o dono decidir, automático após N dias.
4. Prefixos distintos para fotos e artefatos de IA, para listar/limpar separadamente.

## 4. Testes
- `04_backend/tests/test_storage_legenda_ia.py`: 5 testes com cliente S3 falso (sem MinIO/PostgreSQL): exists, propagação de erro, paginação+prefixo, órfãos sem apagar, presigned com expiração.
- Resultado: 5 passed; `ruff check` limpo nos arquivos tocados.
- Testes de integração (`tests/test_storage.py`, MinIO; PostgreSQL 5433) **não foram executados** nesta sessão.
- Nota: `fotos-correcoes.md` (citado na tarefa) não existe neste worktree; as pendências de BL-11 foram tratadas conforme o enunciado.
