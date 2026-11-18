# Limite de corpo no nginx para upload de fotos (DEC-39, BL-11 / BL-27)

**Tarefa:** lacuna "limite de corpo da requisição no proxy" deixada pendente pela T19 (BL-11, DEC-39).
**Arquivo alterado:** `05_infra/nginx/nginx.conf` (stack de produção em VPS, BL-27).
**Backend e frontend:** não alterados.

## Limite do backend (fonte do teto)

- `04_backend/app/services/storage/s3_client.py:27`: `MAX_UPLOAD_SIZE_BYTES = 25 * 1024 * 1024` (25 MiB por foto).
- `04_backend/app/api/v1/fotos.py:53`: `arquivo.read(MAX_UPLOAD_SIZE_BYTES + 1)` no `POST /fotos/upload` (multipart).
- `04_backend/app/services/foto_service.py:64-71`: `_validar_tamanho` recusa acima do teto (422).
- `04_backend/app/schemas/foto.py:13`: no clipboard (`POST /fotos/upload-clipboard`) o corpo é JSON com base64 de até `IMAGEM_BASE64_MAX_LENGTH` = 34_952_536 caracteres, que equivale a 25 MiB em base64.

## Valores escolhidos no nginx

| Escopo | Valor | Motivo |
|---|---|---|
| `http` (padrão, todo o `/api/` e demais rotas) | `1m` | Pedido da tarefa: limite baixo para o restante da API. Acima disso o nginx responde 413. |
| `location ~ ^/api/v1/fotos/upload(-clipboard)?$` | `40m` | Acima do teto de 25 MiB do multipart e da base64 do clipboard (34,95 MB) com folga para o overhead do multipart. |

A regex cobre `POST /fotos/upload`, `DELETE /fotos/upload` e `POST /fotos/upload-clipboard`. A regex tem prioridade sobre o prefixo `/api/`. O `location /api/v1/auth/login` (rate limit `login_zone`) não foi tocado. HSTS, CSP/cabeçalhos de segurança, `server_tokens off`, timeouts e demais `location` foram preservados. O rate limit do login não foi aplicado ao upload de propósito, pois 5 r/min quebraria o upload.

## Ponto de atenção (decisão para o integrador)

Com `1m` no padrão, outras rotas de upload do backend passam a receber 413 no proxy de produção:
- `04_backend/app/api/v1/edificacoes.py:35`: `_MAX_DOCUMENTO_SIZE_BYTES = 25 * 1024 * 1024` (documentos de edificação).
- `04_backend/app/scripts/benchmark_relatorio_geracao.py:46` (150 MiB) é só script de benchmark, não rota de produção.

Se o upload de documentos de edificação for usado em produção, é preciso uma `location` própria com teto de ~25 MB, ou elevar o padrão. Esta mudança não a fez por não estar no escopo pedido. **Proposta a decidir:** adicionar `location` para a rota de documentos de edificação com `client_max_body_size 30m`.

## Validação

Comando pedido: `nginx -t` com `nginx:alpine` montando o arquivo, a partir de `05_infra/`.

Resultado: **não rodou.** O Docker não está disponível no ambiente desta sessão (`docker: command not found` no bash e no PowerShell), e não há `nginx` local. Validar com:

```
cd 05_infra
docker run --rm -v "$PWD/nginx/nginx.conf:/etc/nginx/nginx.conf:ro" nginx:alpine nginx -t
```

A sintaxe foi revisada só por leitura. Espera-se `nginx: configuration file /etc/nginx/nginx.conf test is successful`. Os `ssl_certificate` apontam para `SEU.DOMINIO`, então `nginx -t` pode falhar por certificado ausente, como já acontece no arranjo atual. Nesse caso, a validação de sintaxe deve ser feita com o bloco 443 comentado, como indica o cabeçalho do arquivo.

## Testes do projeto

Não se aplicam: a alteração é só de infra (`05_infra/nginx/nginx.conf`). Nenhum código de backend ou frontend foi tocado, então `pytest`, `ruff check .`, `npm run lint` e `npm run build` não foram executados.

## Decisão proposta (não registrada em decisoes.md)

- **Proposta DEC-39 (complemento):** teto de corpo no proxy = `40m` na rota de fotos e `1m` no padrão da API, com rota dedicada para documentos de edificação, se o upload de documentos for mantido em produção.
