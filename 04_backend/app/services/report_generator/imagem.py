"""Tratamento de imagem comum a todos os pipelines de relatório (V1-02).

Sem dependência de WeasyPrint: importável em qualquer máquina, inclusive fora
do container. `rfo_pipeline` mantém um re-export de `otimizar_imagem` para os
chamadores antigos (benchmark BL-22, `report_generator.__getattr__`).
"""
from __future__ import annotations

import io

from PIL import Image


def otimizar_imagem(conteudo: bytes, *, max_lado: int = 1200, qualidade: int = 72) -> bytes:
    """Redimensiona (se necessário) e recomprime uma foto para uso em relatório.

    Mitiga o gargalo identificado no benchmark de BL-22: `app.services.image_processing`
    (BL-11) recodifica a imagem no upload mas NUNCA a redimensiona — fotos de
    câmera de celular em resolução total (vários MB) hoje são embutidas em
    PDF/DOCX sem nenhuma redução prévia.
    """
    imagem = Image.open(io.BytesIO(conteudo)).convert("RGB")
    if max(imagem.size) > max_lado:
        escala = max_lado / max(imagem.size)
        novo_tamanho = (max(1, int(imagem.width * escala)), max(1, int(imagem.height * escala)))
        imagem = imagem.resize(novo_tamanho, Image.LANCZOS)
    buffer = io.BytesIO()
    imagem.save(buffer, format="JPEG", quality=qualidade, optimize=True)
    return buffer.getvalue()
