"""Reprocessamento de imagens via Pillow (mitigação A08 OWASP, BL-11, ADR/Seção 10.1).

Toda foto recebida (upload manual ou clipboard paste) passa por aqui antes de
ser persistida no storage: o mime-type real é validado pelos magic bytes
(`PIL.Image.open`, não pela extensão/`Content-Type` declarado pelo cliente) e
a imagem é recodificada do zero, o que descarta metadados/EXIF e qualquer
payload embutido no arquivo original.
"""
import io

from PIL import Image, UnidentifiedImageError

from app.core.errors import DomainError

# Formato detectado (magic bytes) -> (extensão de arquivo, content-type de saída).
_FORMATOS_PERMITIDOS: dict[str, tuple[str, str]] = {
    "JPEG": ("jpg", "image/jpeg"),
    "PNG": ("png", "image/png"),
    "WEBP": ("webp", "image/webp"),
}

_ERROS_DE_IMAGEM_INVALIDA: tuple[type[Exception], ...] = (
    UnidentifiedImageError,
    OSError,
    ValueError,
    Image.DecompressionBombError,
)


def reprocessar_imagem(conteudo: bytes) -> tuple[bytes, str, str]:
    """Valida (magic bytes) e recodifica uma imagem, removendo EXIF/metadados.

    Retorna `(bytes_recodificados, extensao, content_type)`.
    Lança `DomainError` (422) se o conteúdo não for uma imagem válida ou se o
    formato detectado não estiver entre os aceitos (JPEG, PNG, WEBP).
    """
    try:
        imagem_verificacao = Image.open(io.BytesIO(conteudo))
        imagem_verificacao.verify()
    except _ERROS_DE_IMAGEM_INVALIDA as exc:
        raise DomainError(
            "O arquivo enviado não é uma imagem válida.",
            type_suffix="arquivo-nao-e-imagem",
            title="Foto inválida",
        ) from exc

    # `verify()` invalida o objeto para leitura de pixels — reabrir para recodificar.
    try:
        imagem = Image.open(io.BytesIO(conteudo))
        formato = (imagem.format or "").upper()
        if formato not in _FORMATOS_PERMITIDOS:
            raise DomainError(
                f"Formato de imagem '{formato or 'desconhecido'}' não suportado. "
                f"Formatos aceitos: {', '.join(_FORMATOS_PERMITIDOS)}.",
                type_suffix="formato-de-imagem-nao-suportado",
                title="Foto inválida",
            )

        extensao, content_type = _FORMATOS_PERMITIDOS[formato]

        buffer = io.BytesIO()
        imagem_para_salvar = imagem.convert("RGB") if formato == "JPEG" else imagem
        imagem_para_salvar.save(buffer, format=formato)
        return buffer.getvalue(), extensao, content_type
    except _ERROS_DE_IMAGEM_INVALIDA as exc:
        raise DomainError(
            "O arquivo enviado não é uma imagem válida.",
            type_suffix="arquivo-nao-e-imagem",
            title="Foto inválida",
        ) from exc
