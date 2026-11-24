"""Foto truncada é recusada mesmo com a flag global do Pillow ligada (T113).

O `weasyprint` define `ImageFile.LOAD_TRUNCATED_IMAGES = True` ao ser importado.
"""
import io
import os

import pytest
from PIL import Image, ImageFile

from app.core.errors import DomainError
from app.services.image_processing import reprocessar_imagem


@pytest.mark.parametrize("formato", ["PNG", "JPEG"])
def test_truncada_e_recusada_com_flag_do_weasyprint_ligada(monkeypatch, formato):
    monkeypatch.setattr(ImageFile, "LOAD_TRUNCATED_IMAGES", True)
    buffer = io.BytesIO()
    Image.frombytes("RGB", (200, 200), os.urandom(200 * 200 * 3)).save(buffer, format=formato)
    completo = buffer.getvalue()

    with pytest.raises(DomainError):
        reprocessar_imagem(completo[: len(completo) // 2])
