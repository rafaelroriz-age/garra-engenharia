# T106 — nginx: location própria para upload de documentos de edificação (R-25)

**Origem:** risco R-25. **Arquivo alterado:** `05_infra/nginx/nginx.conf` (stack VPS de fallback; produção oficial é o PC, DEC-57, sem nginx).
**Backend e frontend:** não alterados.

## Rota e limite (lidos do código, não presumidos)

- Rota: `POST /api/v1/edificacoes/{edificacao_id}/documentos` (`04_backend/app/api/v1/edificacoes.py:85`; prefixo do router em `:33`).
- Limite real: `_MAX_DOCUMENTO_SIZE_BYTES = 25 * 1024 * 1024` = **26_214_400 bytes** (`edificacoes.py:35`), checado em `:104`.

## Diff resumido

- Nova `location ~ ^/api/v1/edificacoes/[^/]+/documentos$` com `client_max_body_size 30m`, inserida antes de `location /api/v1/auth/login` e, portanto, antes da `location /api/` prefixada (regex tem precedência sobre prefixo comum).
- Diretivas de proxy copiadas da location de fotos (`proxy_pass http://backend_upstream` e os quatro `proxy_set_header`). Timeouts herdados do `http` (120s), como nas demais rotas.
- Padrão global `client_max_body_size 1m` mantido. Nada mais alterado.

## Validação

`nginx -t` rodou com Docker 26.1.4 e `nginx:1.27-alpine`. Como o arquivo referencia certificados e upstreams inexistentes no teste, usei cópia do `nginx.conf` em pasta de trabalho fora do repositório (`$CLAUDE_JOB_DIR/tmp`), com certificado autoassinado de teste e `--add-host frontend/backend`. Nada foi montado do repositório além do conteúdo idêntico.

```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

Não rodou teste de roteamento ponta a ponta com tráfego real; a validação é de sintaxe e de ordem de regex por leitura.

## Testes do projeto

Não se aplicam (só infra). Nenhum teste Python foi exigido; `04_backend` não foi tocado.

## Fechamento proposto do R-25 (para o integrador, não editado em riscos.md)

- Status sugerido: **mitigado**. A rota de documentos de edificação tem teto de 30m no proxy; o padrão continua 1m.
- Condição de fechamento: integrador aplica no fluxo de gestão e confirma que a stack VPS não é usada como produção (DEC-57).
- Decisão proposta: não há nova DEC; o complemento segue a linha da DEC-39 (teto por rota, não global).
