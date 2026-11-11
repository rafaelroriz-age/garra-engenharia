"""Fotos no DOCX do LTIP (BL-22, continuação da T20).

Sem banco e sem rede: as fotos são geradas com Pillow e entregues em `fotos_bytes`
(o chamador, não o pipeline, é quem busca no storage). O template usado é o
versionado em `templates/ltip/`, que agora traz `{{ ocorrencia.foto }}`.
"""
from __future__ import annotations

import copy
import io
import logging
import time
import zipfile
from pathlib import Path

import pytest
from docx import Document
from PIL import Image

from app.services.report_generator import ltip_pipeline


def _jpeg(tamanho: tuple[int, int], semente: int = 0, qualidade: int = 80, *, pior_caso: bool = False) -> bytes:
    """JPEG sintético único por `semente`.

    Por padrão, textura suave (ruído em 1/8 da resolução, ampliado): ~100-200 KB a 1200 px,
    parecido com uma foto de obra já recomprimida no upload. Com `pior_caso`, ruído em
    resolução total, que comprime muito mal (~600 KB) e é o limite superior de custo.
    """
    if pior_caso:
        base = Image.effect_noise(tamanho, 40 + semente % 50).convert("RGB")
    else:
        pequeno = (max(1, tamanho[0] // 8), max(1, tamanho[1] // 8))
        base = Image.effect_noise(pequeno, 40 + semente % 50).convert("RGB").resize(tamanho, Image.BICUBIC)
    ruido = base
    ruido.paste((semente % 256, (semente * 7) % 256, (semente * 13) % 256), (0, 0, 40, 40))
    buffer = io.BytesIO()
    ruido.save(buffer, format="JPEG", quality=qualidade)
    return buffer.getvalue()


def _ocorrencia(numero: int, chave: str | None, legenda: str | None = None) -> dict:
    fotos = [] if chave is None else [{"storage_key": chave, "legenda": legenda}]
    return {
        "seq_numero": numero,
        "sistema": "Estrutura",
        "sistema_ordem": 1,
        "subsistema": "Vigas",
        "subsistema_ordem": 1,
        "situacao": "Não conforme",
        "descricao": f"Ocorrência {numero}",
        "fotos": fotos,
    }


def _imagens(caminho: Path) -> list[Image.Image]:
    with zipfile.ZipFile(caminho) as pacote:
        # O template já traz o logo em PNG; as fotos do laudo são sempre JPEG.
        nomes = sorted(n for n in pacote.namelist() if n.startswith("word/media/") and n.endswith((".jpg", ".jpeg")))
        return [Image.open(io.BytesIO(pacote.read(n))) for n in nomes]


def _texto(caminho: Path) -> str:
    documento = Document(str(caminho))
    partes = [p.text for p in documento.paragraphs]
    for tabela in documento.tables:
        for linha in tabela.rows:
            partes.extend(c.text for c in linha.cells)
    return "\n".join(partes)


def test_template_versionado_embute_foto_reduzida_e_legenda(tmp_path: Path) -> None:
    fotos = {"a.jpg": _jpeg((1200, 900), 1), "b.jpg": _jpeg((900, 1200), 2)}
    contexto = {
        "ocorrencias": [_ocorrencia(1, "a.jpg", "Fissura na viga"), _ocorrencia(2, "b.jpg"), _ocorrencia(3, None)]
    }
    destino = tmp_path / "ltip.docx"
    ltip_pipeline.gerar_docx(contexto, fotos, destino)

    imagens = _imagens(destino)
    assert len(imagens) == 2
    for imagem in imagens:
        assert max(imagem.size) <= ltip_pipeline.LADO_MAX_FOTO_DOCX_PX
    assert destino.stat().st_size < len(fotos["a.jpg"]) + len(fotos["b.jpg"])
    texto = _texto(destino)
    assert "Fissura na viga" in texto
    assert "{{" not in texto and "{%" not in texto and "None" not in texto
    assert ltip_pipeline.TEXTO_FOTO_INDISPONIVEL not in texto  # ocorrência 3 simplesmente não tem foto


def test_legenda_de_ia_nao_entra_no_docx(tmp_path: Path) -> None:
    ocorrencia = _ocorrencia(1, "a.jpg")
    ocorrencia["fotos"][0]["legenda_ia_sugerida"] = "Sugestão da IA"
    destino = tmp_path / "ltip.docx"
    ltip_pipeline.gerar_docx({"ocorrencias": [ocorrencia]}, {"a.jpg": _jpeg((800, 600))}, destino)
    assert "Sugestão da IA" not in _texto(destino)


def test_foto_menor_que_o_limite_nao_e_recodificada() -> None:
    pequena = _jpeg((400, 300))
    assert ltip_pipeline.reduzir_foto_docx(pequena) is pequena


def test_foto_indisponivel_vira_placeholder_e_aviso(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    contexto = {"ocorrencias": [_ocorrencia(1, "ok.jpg"), _ocorrencia(2, "falta.jpg"), _ocorrencia(3, "ruim.jpg")]}
    fotos = {"ok.jpg": _jpeg((1200, 900)), "ruim.jpg": b"isto nao e uma imagem"}
    destino = tmp_path / "ltip.docx"
    with caplog.at_level(logging.WARNING, logger=ltip_pipeline.logger.name):
        ltip_pipeline.gerar_docx(contexto, fotos, destino)

    assert len(_imagens(destino)) == 1
    assert _texto(destino).count(ltip_pipeline.TEXTO_FOTO_INDISPONIVEL) == 2
    avisos = " ".join(r.getMessage() for r in caplog.records)
    assert "falta.jpg" in avisos and "ruim.jpg" in avisos


def test_normalizar_contexto_e_contexto_original_ficam_intactos(tmp_path: Path) -> None:
    contexto = {"ocorrencias": [_ocorrencia(1, "a.jpg", "Legenda")]}
    original = copy.deepcopy(contexto)
    normalizado = ltip_pipeline.normalizar_contexto(contexto)
    ltip_pipeline.gerar_docx(contexto, {"a.jpg": _jpeg((800, 600))}, tmp_path / "x.docx")

    assert contexto == original
    ocorrencia = normalizado["sistemas"][0]["ocorrencias"][0]
    assert "foto" not in ocorrencia and "legenda_foto" not in ocorrencia


def test_desempenho_com_239_fotos_sinteticas(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    n = 239
    fotos = {f"f/{i}.jpg": _jpeg((1200, 900), i) for i in range(n)}
    contexto = {"ocorrencias": [_ocorrencia(i + 1, f"f/{i}.jpg", f"Legenda {i + 1}") for i in range(n)]}
    destino = tmp_path / "ltip239.docx"

    inicio = time.perf_counter()
    metricas = ltip_pipeline.gerar_docx(contexto, fotos, destino)
    total = time.perf_counter() - inicio

    assert len(_imagens(destino)) == n
    bytes_originais = sum(len(c) for c in fotos.values())
    with capsys.disabled():
        print(
            f"\n[BL-22] {n} fotos 1200px: total={total:.2f}s montagem_fotos={metricas['montagem_fotos']:.2f}s "
            f"render_e_salvar={metricas['render_e_salvar']:.2f}s docx={metricas['tamanho_bytes'] / 1e6:.1f}MB "
            f"fotos_originais={bytes_originais / 1e6:.1f}MB"
        )
    # RNF-06: folga ampla sobre os ~2 s esperados; só pega regressões grosseiras.
    assert total < 30
    assert metricas["tamanho_bytes"] < bytes_originais
