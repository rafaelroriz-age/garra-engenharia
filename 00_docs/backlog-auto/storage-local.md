# T80 — Storage em disco local com download assinado (DEC-57)

## O que foi feito
- `app/services/storage/local_client.py`: `LocalStorageClient` (upload/download/exists/delete/list_keys/list_objects/generate_presigned_url), mais `assinar_token`/`validar_token`.
- `base.py`: `validate_key` extraída e compartilhada (S3 e local).
- `s3_client.get_storage_client` escolhe o provedor por `STORAGE_PROVEDOR` (import tardio do local, evita ciclo).
- `app/api/v1/arquivos.py`: `GET /api/v1/arquivos/{token}` sem JWT; router registrado em `main.py`.
- `RequestBaseUrlMiddleware` (`app/core/middleware.py`) para montar URL absoluta.
- Testes: `tests/test_storage_local.py` (13 casos, sem banco, `tmp_path`).

## Decisões
1. **Content-type**: inferido pela extensão da chave (mapa explícito + `mimetypes`), sem `.meta.json`. Todas as chaves do sistema têm extensão (fotos `.jpg/.png`, relatórios `.pdf/.docx`); evita arquivos laterais nas listagens. Desconhecida ⇒ `application/octet-stream`.
2. **Gravação atômica**: `tempfile.mkstemp` no mesmo diretório (`.tmp-*`, ignorado nas listagens) + `os.replace`.
3. **Path traversal**: `(raiz / chave).resolve()` precisa estar dentro de `raiz`; senão `ValueError`. No endpoint, chave assinada fora da raiz ⇒ 404.
4. **Token**: `base64url(json{k,e}).base64url(HMAC-SHA256)`; chave HMAC = `HMAC(JWT_SECRET_KEY, "garra-storage-download-v1")` (separada do uso JWT). Comparação `hmac.compare_digest`; inválido/adulterado/vencido ⇒ 403; arquivo inexistente ⇒ 404; provedor não local ⇒ 404.
5. **Resposta**: `FileResponse` com `Content-Disposition: inline; filename=<nome>` (o S3 não definia disposition, o navegador exibia inline; o filename só ajuda ao salvar), `Cache-Control: private, no-store` e CSP própria `frame-ancestors 'none'` (a CSP `default-src 'none'` global quebraria o visualizador de PDF).
6. **URL absoluta** (`generate_presigned_url` é chamado em services sem acesso ao request, e o cliente é singleton): ordem `PUBLIC_BASE_URL` → base do request corrente via contextvar preenchida pelo middleware (`X-Forwarded-Proto`/`X-Forwarded-Host` do cloudflared, senão `Host`) → **URL relativa** `/api/v1/arquivos/<token>` (só ocorre fora de request, ex.: scripts). Não é preciso ajuste no front enquanto houver request. Risco aceito: um cliente pode forjar `X-Forwarded-Host` e receber de volta uma URL com o host que ele mesmo enviou; o token só é devolvido a quem o pediu, então não há ganho de ataque. Se o front for tratar URL relativa (T-front), basta prefixar com a base da API.

## Variáveis (`04_backend/.env.example`)
| Variável | Padrão | Uso |
|---|---|---|
| `STORAGE_PROVEDOR` | `s3` | `s3` (MinIO/AWS) ou `local` |
| `STORAGE_LOCAL_DIR` | `../05_infra/local/storage` | raiz dos arquivos (relativa a `04_backend/` ou absoluta; já fora do git por `05_infra/local/`, DEC-57) |
| `PUBLIC_BASE_URL` | vazio | URL pública fixa do backend; vazio = derivar do request |

## Resultados
- `pytest tests/test_storage_local.py`: 13 passed.
- `ruff check .`: limpo (1 ordenação de imports corrigida).
- Suíte completa: ver seção "Suíte completa" abaixo.
- `tests/test_rfo_contexto.py` não coleta neste Windows (`OSError: cannot load library 'libpango-1.0'`, WeasyPrint) — falha de ambiente pré-existente, alheia a esta tarefa.

## Suíte completa
**Não rodou.** Com `POSTGRES_DB=garra_engenharia_test`, a porta 5433 aceita TCP mas a conexão é derrubada
(`ConnectionResetError: [WinError 64]` já no primeiro teste com banco, `test_auth.py`), então a suíte com
banco não pôde ser validada neste ambiente. Nenhum resultado foi inventado. A mudança é aditiva (padrão
`STORAGE_PROVEDOR=s3` inalterado; `S3StorageClient` só passou a usar `validate_key` compartilhada), mas
convém rodar `pytest` completo com o PostgreSQL de `05_infra/docker-compose.yml` no ar antes de integrar.
