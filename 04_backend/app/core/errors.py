"""Exceções de domínio padronizadas (ADR-07, DEC-11 — RFC 7807 Problem Details).

Serviços/repositórios devem lançar `DomainError` (ou uma de suas subclasses)
em vez de `HTTPException` ad-hoc. O handler global registrado em
`app.core.exception_handlers` converte essas exceções (e `RequestValidationError`
do FastAPI/Pydantic) para `application/problem+json`.
"""


class DomainError(Exception):
    """Erro de regra de negócio (RN-XX). Vira HTTP 422 (padrão) em `problem+json`.

    `type_suffix` compõe a URI `https://garra-engenharia/erros/{type_suffix}`
    (ver ADR-07). `errors` é a lista opcional de violações campo a campo.
    `headers` são cabeçalhos HTTP extras da resposta (ex.: `Retry-After` em 429); o handler global os repassa.
    """

    def __init__(
        self,
        detail: str,
        *,
        type_suffix: str = "regra-de-negocio",
        title: str = "Violação de regra de negócio",
        status_code: int = 422,
        errors: list[dict] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(detail)
        self.detail = detail
        self.type_suffix = type_suffix
        self.title = title
        self.status_code = status_code
        self.errors = errors
        self.headers = headers


class NotFoundError(DomainError):
    """Recurso não encontrado. Vira HTTP 404."""

    def __init__(self, detail: str, *, type_suffix: str = "recurso-nao-encontrado") -> None:
        super().__init__(
            detail,
            type_suffix=type_suffix,
            title="Recurso não encontrado",
            status_code=404,
        )


class ConflictError(DomainError):
    """Conflito de estado (ex.: violação de unicidade). Vira HTTP 409."""

    def __init__(self, detail: str, *, type_suffix: str = "conflito") -> None:
        super().__init__(
            detail,
            type_suffix=type_suffix,
            title="Conflito de estado",
            status_code=409,
        )
