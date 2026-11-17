"""Middlewares transversais de segurança e observabilidade (BL-23).

- `RequestIdMiddleware`: correlaciona logs e respostas de erro por `request_id`
  (ADR-08/DEC-12, OWASP A09).
- `SecurityHeadersMiddleware`: cabeçalhos de resposta defensivos (OWASP A05).
  Em VPS próprio o Nginx (`05_infra/nginx/nginx.conf`) também os aplica; aqui
  garantem a mesma proteção quando a API roda atrás de um proxy gerenciado
  (Render) que não permite customizar cabeçalhos.
"""
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

REQUEST_ID_HEADER = "X-Request-ID"

_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    # A API só devolve JSON/erros: nenhum recurso ativo precisa ser carregado.
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
}


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response


class RequestBaseUrlMiddleware(BaseHTTPMiddleware):
    """Expõe a base URL pública do request (DEC-57) a `LocalStorageClient`.

    O túnel cloudflared muda de URL a cada boot e envia `X-Forwarded-Proto` /
    `X-Forwarded-Host`; usados para montar URLs absolutas de download quando
    `PUBLIC_BASE_URL` está vazia. Sem esses cabeçalhos, usa a URL do próprio request.
    """

    async def dispatch(self, request: Request, call_next):
        proto = (request.headers.get("x-forwarded-proto") or request.url.scheme).split(",")[0].strip()
        host = (request.headers.get("x-forwarded-host") or request.headers.get("host") or "")
        host = host.split(",")[0].strip()
        token = None
        if proto in {"http", "https"} and host:
            from app.services.storage.local_client import request_base_url

            token = (request_base_url, request_base_url.set(f"{proto}://{host}"))
        try:
            return await call_next(request)
        finally:
            if token:
                token[0].reset(token[1])


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, hsts: bool = False):
        super().__init__(app)
        self._hsts = hsts

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        for header, valor in _SECURITY_HEADERS.items():
            response.headers.setdefault(header, valor)
        if self._hsts:
            response.headers.setdefault(
                "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
            )
        return response
