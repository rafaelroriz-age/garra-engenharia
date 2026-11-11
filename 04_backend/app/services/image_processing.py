"""Reprocessamento de imagens via Pillow (mitigação A08 OWASP, BL-11, ADR/Seção 10.1).

Toda foto recebida (upload manual ou clipboard paste) passa por aqui antes de
ser persistida no storage: o mime-type real é validado pelos magic bytes
(`PIL.Image.open`, não pela extensão/`Content-Type` declarado pelo cliente) e
a imagem é recodificada do zero, o que descarta metadados/EXIF e qualquer
payload embutido no arquivo original.

Redimensiona fotos maiores que `MAX_LADO_ARMAZENADO_PX` (achado do benchmark
de BL-22, RNF-06/R-03: fotos de câmera de celular em resolução total, sem
nenhum redimensionamento, fazem a geração de relatório de pior caso
ultrapassar os 60s exigidos quando embutidas em PDF/DOCX — ver
`00_docs/projeto/relatorio-benchmark-geracao-pdf-docx.md`). O limite escolhido
(2000px no lado maior) ainda preserva qualidade suficiente para zoom/edição
no editor de anotação (BL-31); a compressão adicional específica para
embutir em relatório (mais agressiva) fica em
`app.services.report_generator.rfo_pipeline.otimizar_imagem`.
"""
import io

from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.errors import DomainError

# Formato detectado (magic bytes) -> (extensão de arquivo, content-type de saída).
_FORMATOS_PERMITIDOS: dict[str, tuple[str, str]] = {
    "JPEG": ("jpg", "image/jpeg"),
    "PNG": ("png", "image/png"),
    "WEBP": ("webp", "image/webp"),
}

MAX_LADO_ARMAZENADO_PX = 2000
# Teto explícito de pixels decodificados (DEC-39 F, A08/DoS): evita que um arquivo pequeno em
# bytes (PNG muito comprimido) ocupe GBs ao ser descomprimido. 50 Mpx cobre câmeras de celular
# de 48/50 Mpx; o padrão do Pillow só reage a ~179 Mpx.
MAX_PIXELS_DECODIFICADOS = 50_000_000

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
        if imagem_verificacao.width * imagem_verificacao.height > MAX_PIXELS_DECODIFICADOS:
            raise DomainError(
                f"A imagem excede o limite de {MAX_PIXELS_DECODIFICADOS // 1_000_000} megapixels.",
                type_suffix="imagem-excede-pixels-maximos",
                title="Foto inválida",
            )
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

        # Aplica a orientação do EXIF (celular em pé: Orientation 6/8) ANTES de recodificar sem
        # EXIF; do contrário a foto sai deitada nos relatórios (DEC-39 B, RF-05).
        imagem = ImageOps.exif_transpose(imagem)
        imagem_para_salvar = imagem.convert("RGB") if formato == "JPEG" else imagem
        if max(imagem_para_salvar.size) > MAX_LADO_ARMAZENADO_PX:
            escala = MAX_LADO_ARMAZENADO_PX / max(imagem_para_salvar.size)
            novo_tamanho = (
                max(1, round(imagem_para_salvar.width * escala)),
                max(1, round(imagem_para_salvar.height * escala)),
            )
            imagem_para_salvar = imagem_para_salvar.resize(novo_tamanho, Image.LANCZOS)

        buffer = io.BytesIO()
        imagem_para_salvar.save(buffer, format=formato)
        return buffer.getvalue(), extensao, content_type
    except _ERROS_DE_IMAGEM_INVALIDA as exc:
        raise DomainError(
            "O arquivo enviado não é uma imagem válida.",
            type_suffix="arquivo-nao-e-imagem",
            title="Foto inválida",
        ) from exc
