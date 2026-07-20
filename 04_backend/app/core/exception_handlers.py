"""Exception handlers globais — RFC 7807 Problem Details (ADR-07, DEC-11).

Registrados em `app.main` via `register_exception_handlers(app)`. Convertem:
- `DomainError` (e subclasses `NotFoundError`/`ConflictError`) — erros de regra de negócio.
- `RequestValidationError` — erros de validação de schema do FastAPI/Pydantic.
- `Exception` genérica — qualquer falha não tratada (500), sem vazar stack trace.

Todas as respostas usam `application/problem+json` com os campos `type`,
`title`, `status`, `detail`, `instance` e, quando aplicável, `errors`.
"""
import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.errors import DomainError

logger = logging.getLogger(__name__)

_PROBLEM_JSON_MEDIA_TYPE = "application/problem+json"
_BASE_TYPE_URI = "https://garra-engenharia/erros"


def _problem_response(
    *,
    request: Request,
    status_code: int,
    type_suffix: str,
    title: str,
    detail: str,
    errors: list[dict] | None = None,
) -> JSONResponse:
    body: dict = {
        "type": f"{_BASE_TYPE_URI}/{type_suffix}",
        "title": title,
        "status": status_code,
        "detail": detail,
        "instance": str(request.url.path),
    }
    if errors:
        body["errors"] = errors
    return JSONResponse(status_code=status_code, content=body, media_type=_PROBLEM_JSON_MEDIA_TYPE)


async def _handle_domain_error(request: Request, exc: DomainError) -> JSONResponse:
    return _problem_response(
        request=request,
        status_code=exc.status_code,
        type_suffix=exc.type_suffix,
        title=exc.title,
        detail=exc.detail,
        errors=exc.errors,
    )


async def _handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = [
        {"field": ".".join(str(part) for part in error["loc"] if part != "body"), "message": error["msg"]}
        for error in exc.errors()
    ]
    return _problem_response(
        request=request,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        type_suffix="erro-de-validacao",
        title="Erro de validação de dados de entrada",
        detail="Um ou mais campos enviados são inválidos.",
        errors=errors,
    )


async def _handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Erro não tratado ao processar %s %s", request.method, request.url.path)
    return _problem_response(
        request=request,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        type_suffix="erro-interno",
        title="Erro interno do servidor",
        detail="Ocorreu um erro inesperado. Tente novamente ou contate o suporte.",
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Registra os handlers globais de exceção (RFC 7807) na aplicação FastAPI."""
    app.add_exception_handler(DomainError, _handle_domain_error)
    app.add_exception_handler(RequestValidationError, _handle_validation_error)
    app.add_exception_handler(Exception, _handle_unexpected_error)
