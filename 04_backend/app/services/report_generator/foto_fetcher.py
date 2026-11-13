"""Entrega de fotos ao WeasyPrint por `url_fetcher` (DEC-41, item B).

Em vez de embutir cada foto como data URI base64 no HTML (que infla o HTML e
o parse), o pipeline registra os bytes num `RegistroDeFotos` e escreve no HTML
uma URL opaca `garra-foto:<índice>`; o fetcher devolve os bytes direto da
memória. Mesmo mecanismo do `ltip_pipeline` (T20), que não foi alterado.

Segurança (OWASP A10/SSRF): o fetcher resolve SOMENTE as URLs que o próprio
registro emitiu e os data URIs (autocontidos, sem I/O). Qualquer outra URL
(`file:`, `http(s):`, `garra-foto:` não registrada...) levanta
`UrlNaoPermitida`; nada é lido do disco nem da rede.

O WeasyPrint é importado de forma preguiçosa (GTK/Pango só existem no
container); `RegistroDeFotos` e `mime_da_imagem` funcionam em qualquer máquina.
"""
from __future__ import annotations

from typing import Any

ESQUEMA_FOTO = "garra-foto:"


class UrlNaoPermitida(ValueError):
    """URL pedida pelo WeasyPrint que o pipeline não registrou."""


def mime_da_imagem(conteudo: bytes) -> str:
    if conteudo.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    return "image/jpeg"


class RegistroDeFotos:
    """Mapa fechado `url -> bytes` das imagens que o HTML pode referenciar."""

    def __init__(self) -> None:
        self._fotos: list[bytes] = []

    def __len__(self) -> int:
        return len(self._fotos)

    def registrar(self, conteudo: bytes) -> str:
        self._fotos.append(conteudo)
        return f"{ESQUEMA_FOTO}{len(self._fotos) - 1}"

    def resolver(self, url: str) -> bytes:
        if not url.startswith(ESQUEMA_FOTO):
            raise UrlNaoPermitida(f"URL não permitida: {url[:80]!r}")
        indice = url[len(ESQUEMA_FOTO):]
        # só dígitos ASCII: rejeita sinais, espaços e índices negativos
        if not (indice.isascii() and indice.isdigit()) or int(indice) >= len(self._fotos):
            raise UrlNaoPermitida(f"Foto não registrada: {url[:80]!r}")
        return self._fotos[int(indice)]


def criar_url_fetcher(registro: RegistroDeFotos) -> Any | None:
    """`url_fetcher` do WeasyPrint restrito ao `registro`.

    Devolve `None` se a versão instalada do WeasyPrint não tem `URLFetcher`
    (API anterior); o chamador então volta aos data URIs.
    """
    try:
        from weasyprint.urls import URLFetcher, URLFetcherResponse
    except ImportError:  # pragma: no cover - depende da versão instalada
        return None

    class _FetcherRestrito(URLFetcher):
        def fetch(self, url: str, headers: Any = None) -> Any:
            if url.startswith("data:"):
                return super().fetch(url, headers)
            conteudo = registro.resolver(url)
            return URLFetcherResponse(url, conteudo, {"Content-Type": mime_da_imagem(conteudo)})

    return _FetcherRestrito()
