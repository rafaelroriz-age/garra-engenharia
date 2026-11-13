"""Testes do pipeline de templates da Vistoria Residencial (ADR-13/DEC-25, RF-06, RNF-03, A02).

Mesmo método de `test_ltip_templates.py`: nada aqui lê `01_output-context/`. Cada
teste usa um PDF sintético escrito à mão com a geometria medida no original —
A4, Times 12/14, logo no cabeçalho de todas as páginas, rodapé de 3 linhas com
o contato em azul, figuras 16 x 9 cm com legenda itálica, análise por sistema
com subtítulos marcados e bloco de assinatura alinhado à direita. Os dados
pessoais do PDF sintético são **fictícios** e servem para provar que nada do
exemplar chega ao `layout.json`.
"""
from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path

import pytest

from app.scripts.build_vistoria_residencial_templates import (
    DOCX_TEMPLATE,
    HTML_TEMPLATE,
    LAYOUT_JSON,
    PLACEHOLDERS,
    chave_secao,
    gerar_docx,
    gerar_html,
)
from app.scripts.vistoria_residencial_layout_extractor import (
    LayoutExtractionError,
    anonimizar,
    extrair_layout,
    verificar_sem_dados_pessoais,
)

A4_LARGURA = 595.28
A4_ALTURA = 841.89
ESQUERDA = 85.0  # 3,0 cm, como no original
DIREITA = 539.0  # 1,99 cm da borda direita
AZUL_LINK = (0.0196, 0.388, 0.757)  # #0563C1
CINZA_LEGENDA = (0.267, 0.329, 0.416)  # #44546A
BRANCO = (1.0, 1.0, 1.0)

#: Fontes base-14 do PDF sintético: nome do recurso -> BaseFont.
FONTES = {"F1": "Times-Roman", "F2": "Times-Bold", "F3": "Helvetica-Oblique", "F4": "Helvetica-Bold"}

#: Dados pessoais FICTÍCIOS plantados no exemplar sintético. Nenhum pode vazar.
NOME = "Fulano de Tal"
CREA = "Eng. Civil - CREA-GO nº 1234567890/D-GO"
CONTATO = "fulano.tal@example.com / (62) 99999-0000"
UNIDADE = "Ap. 101"
EMPREENDIMENTO = "Residencial Exemplo"
DADOS_PESSOAIS = ("Fulano", "1234567890", "example.com", "99999", "Ap. 101", "Apartamento 101",
                  "Residencial Exemplo", "Goiânia", "74000-000", "Rua Exemplo")


# --------------------------------------------------------------------- PDF sintético


def _largura(texto: str, fonte: str, corpo: float) -> float:
    from pdfminer.fontmetrics import FONT_METRICS  # métricas AFM das base-14 (via pdfplumber)

    larguras = FONT_METRICS[FONTES[fonte]][1]
    return sum(larguras.get(caractere, 500) for caractere in texto) * corpo / 1000


def _texto(x: float, topo: float, fonte: str, texto: str, corpo: float, cor: tuple[float, ...] | None = None) -> dict:
    """Linha de texto posicionada pelo **topo** (coordenada do pdfplumber)."""
    return {"x": x, "topo": topo, "fonte": fonte, "texto": texto, "corpo": corpo, "cor": cor}


def _a_direita(topo: float, fonte: str, texto: str, corpo: float) -> dict:
    return _texto(DIREITA - _largura(texto, fonte, corpo), topo, fonte, texto, corpo)


def _imagem(x: float, topo: float, largura: float, altura: float) -> tuple[float, float, float, float]:
    return (x, topo, largura, altura)


def _fluxo(pagina: dict, altura_pagina: float) -> bytes:
    partes = []
    for x, topo, largura, altura in pagina.get("imagens", []):
        partes.append(f"q {largura:.2f} 0 0 {altura:.2f} {x:.2f} {altura_pagina - topo - altura:.2f} cm /Im1 Do Q")
    partes.append("BT")
    for linha in pagina.get("linhas", []):
        escapado = linha["texto"].replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")
        cor = linha["cor"] or (0.0, 0.0, 0.0)
        # O topo da caixa do caractere fica ~0,9 corpo acima da linha de base.
        base = altura_pagina - linha["topo"] - linha["corpo"] * 0.9
        partes.append(
            f"{cor[0]} {cor[1]} {cor[2]} rg /{linha['fonte']} {linha['corpo']} Tf "
            f"1 0 0 1 {linha['x']:.2f} {base:.2f} Tm ({escapado}) Tj"
        )
    partes.append("ET")
    return "\n".join(partes).encode("cp1252", errors="replace")


def _pdf_sintetico(paginas: list[dict]) -> bytes:
    """PDF mínimo válido (Type1 base-14, WinAnsi, uma imagem 1x1 reaproveitada)."""
    objetos: list[bytes] = []

    def adicionar(corpo: bytes) -> int:
        objetos.append(corpo)
        return len(objetos)

    ids_fontes = {
        nome: adicionar(b"<< /Type /Font /Subtype /Type1 /BaseFont /%s /Encoding /WinAnsiEncoding >>" % base.encode())
        for nome, base in FONTES.items()
    }
    id_imagem = adicionar(
        b"<< /Type /XObject /Subtype /Image /Width 1 /Height 1 /ColorSpace /DeviceGray "
        b"/BitsPerComponent 8 /Length 1 >>\nstream\n\x80\nendstream"
    )
    fontes = b" ".join(b"/%s %d 0 R" % (nome.encode(), ident) for nome, ident in ids_fontes.items())

    conteudos = []
    for pagina in paginas:
        largura, altura = pagina.get("tamanho", (A4_LARGURA, A4_ALTURA))
        fluxo = _fluxo(pagina, altura)
        conteudos.append((adicionar(b"<< /Length %d >>\nstream\n%s\nendstream" % (len(fluxo), fluxo)), largura, altura))

    id_pages = len(objetos) + len(paginas) + 1
    ids_paginas = [
        adicionar(
            b"<< /Type /Page /Parent %d 0 R /MediaBox [0 0 %.2f %.2f] "
            b"/Resources << /Font << %s >> /XObject << /Im1 %d 0 R >> >> /Contents %d 0 R >>"
            % (id_pages, largura, altura, fontes, id_imagem, conteudo)
        )
        for conteudo, largura, altura in conteudos
    ]
    kids = b" ".join(b"%d 0 R" % identificador for identificador in ids_paginas)
    assert adicionar(b"<< /Type /Pages /Kids [%s] /Count %d >>" % (kids, len(ids_paginas))) == id_pages
    id_catalogo = adicionar(b"<< /Type /Catalog /Pages %d 0 R >>" % id_pages)

    saida = bytearray(b"%PDF-1.4\n")
    offsets = []
    for numero, corpo in enumerate(objetos, start=1):
        offsets.append(len(saida))
        saida += b"%d 0 obj\n%s\nendobj\n" % (numero, corpo)
    inicio_xref = len(saida)
    saida += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objetos) + 1)
    for offset in offsets:
        saida += b"%010d 00000 n \n" % offset
    saida += b"trailer\n<< /Size %d /Root %d 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
        len(objetos) + 1,
        id_catalogo,
        inicio_xref,
    )
    return bytes(saida)


LOGO_CABECALHO = _imagem(448.5, 13.0, 109.4, 52.3)


def _moldura(numero_pagina: int) -> dict:
    """Cabeçalho (logo à direita) e rodapé (nome, CREA, contato em azul, número)."""
    return {
        "imagens": [LOGO_CABECALHO],
        "linhas": [
            _texto(246.0, 787.0, "F1", NOME, 10.0),
            _texto(196.0, 799.0, "F1", CREA, 10.0),
            _texto(196.0, 811.0, "F1", CONTATO, 10.0, AZUL_LINK),
            _texto(512.0, 824.0, "F1", str(numero_pagina), 9.0),
        ],
    }


def _pagina(numero_pagina: int, titulos: list[tuple[str, str, float]], *, corpo: str = "Texto corrido do laudo.",
            paragrafos: int = 10, extras: list[dict] | None = None, imagens: list | None = None) -> dict:
    pagina = _moldura(numero_pagina)
    topo = 73.0
    for numero, titulo, tamanho in titulos:
        # Número e título afastados: o `extract_words` não pode fundi-los numa palavra só.
        pagina["linhas"] += [_texto(ESQUERDA, topo, "F2", numero, tamanho), _texto(ESQUERDA + 40, topo, "F2", titulo, tamanho)]
        topo += 30
    for _ in range(paragrafos):
        # Linha justificada: começa na margem esquerda e termina na direita.
        pagina["linhas"] += [_texto(ESQUERDA, topo, "F1", corpo, 12.0), _a_direita(topo, "F1", "x", 12.0)]
        topo += 15
    pagina["linhas"] += extras or []
    pagina["imagens"] += imagens or []
    return pagina


def _pagina_de_fotos(numero_pagina: int, figuras: tuple[int, int]) -> dict:
    pagina = _moldura(numero_pagina)
    for indice, figura in enumerate(figuras):
        topo = 71.0 + indice * 276
        pagina["imagens"].append(_imagem(ESQUERDA, topo, 453.6, 255.1))
        pagina["linhas"].append(
            _texto(214.0, topo + 262, "F3", f"Figura {figura} - Sala do {UNIDADE}. Fonte: Autor.", 9.0, CINZA_LEGENDA)
        )
    return pagina


def _analise(numero_pagina: int) -> dict:
    extras = []
    topo = 260.0
    for numero, sistema in (("9.1.", "Estrutura e Laje"), ("9.2.", "Pisos")):
        extras += [_texto(ESQUERDA, topo, "F2", numero, 14.0), _texto(ESQUERDA + 40, topo, "F2", sistema, 14.0)]
        extras += [_texto(ESQUERDA, topo + 22, "F1", ">", 12.0), _texto(ESQUERDA + 18, topo + 22, "F2", "Constatações:", 12.0)]
        extras += [_texto(ESQUERDA + 10, topo + 42, "F1", "• Fissura aparente;", 12.0)]
        extras += [_texto(ESQUERDA, topo + 62, "F1", ">", 12.0), _texto(ESQUERDA + 18, topo + 62, "F2", "Fundamentação Técnica", 12.0)]
        extras += [_texto(ESQUERDA, topo + 82, "F1", "Texto da fundamentação.", 12.0)]
        topo += 120
    return _pagina(numero_pagina, [("9.", "ANÁLISE E CONSIDERAÇÕES TÉCNICAS", 14.0)], paragrafos=8, extras=extras)


def _encerramento(numero_pagina: int) -> dict:
    extras = [
        _a_direita(483.0, "F1", "_" * 40, 12.0),
        _a_direita(500.0, "F2", NOME, 12.0),
        _a_direita(517.0, "F1", "Eng. Civil - CREA nº 1234567890 D-GO;", 12.0),
        _a_direita(534.0, "F1", "Membro titular do IBAPE-GO;", 12.0),
        _a_direita(748.0, "F1", "Goiânia, 11 de maio de 2026.", 12.0),
    ]
    return _pagina(
        numero_pagina, [("11.", "ENCERRAMENTO", 14.0)], paragrafos=8, extras=extras,
        imagens=[_imagem(341.0, 443.0, 137.7, 79.7)],
    )


def _capa() -> dict:
    return {
        "imagens": [_imagem(0, 0, A4_LARGURA, A4_ALTURA), _imagem(372.8, 0.0, 222.8, 126.8)],
        "linhas": [
            _texto(46.0, 137.0, "F4", "VISTORIA TÉCNICA", 34.4, BRANCO),
            _texto(28.0, 177.0, "F4", "PARA RECEBIMENTO", 34.4, BRANCO),
            _texto(128.0, 218.0, "F4", "DE IMÓVEL", 34.4, BRANCO),
            _texto(195.0, 271.0, "F4", UNIDADE, 15.4, BRANCO),
            _texto(157.0, 289.0, "F4", EMPREENDIMENTO, 15.4, BRANCO),
            _texto(109.0, 769.0, "F4", "RESP. TÉCNICO:", 15.0, BRANCO),
            _texto(31.0, 786.0, "F4", "ENG. CIVIL FULANO DE TAL", 15.0, BRANCO),
            _texto(77.0, 804.0, "F4", "MAIO DE 2026 CREA: 1234567890-D/GO", 15.0, BRANCO),
        ],
    }


def _rosto() -> dict:
    pagina = _moldura(1)
    for topo, texto in ((139.0, "LAUDO TÉCNICO DE"), (187.0, "VISTORIA"), (234.0, "PARA RECEBIMENTO DE IMÓVEL"),
                        (390.0, UNIDADE), (439.0, EMPREENDIMENTO)):
        pagina["linhas"].append(_texto(120.0, topo, "F2", texto, 36.0))
    pagina["linhas"].append(_texto(260.0, 722.0, "F2", "Maio de 2026", 18.0))
    return pagina


def _sumario(numero_pagina: int) -> dict:
    pagina = _moldura(numero_pagina)
    pagina["linhas"] += [
        _texto(ESQUERDA, 73.0, "F2", "SUMÁRIO", 16.0),
        _texto(ESQUERDA, 100.0, "F2", "1. INTRODUÇÃO ....................... 4", 11.0),
    ]
    return pagina


def _paginas_do_laudo(*, com_fotos: bool = True) -> list[dict]:
    paginas = [_capa(), _rosto(), _sumario(2), _sumario(3)]
    paginas += [
        _pagina(4, [("1.", "INTRODUÇÃO", 14.0), ("1.1.", "Histórico", 14.0)],
                corpo=f"Vistoria do {UNIDADE}, Rua Exemplo, CEP 74000-000."),
        _pagina(5, [("2.", "CONSIDERAÇÕES PRELIMINARES", 14.0), ("2.1.", "Geral", 14.0)]),
        _pagina(6, [("4.", "OBJETO", 14.0), ("4.2.", "Identificação", 14.0), ("4.2.1.", "Projetos do Apartamento 101", 12.0)]),
        # Enxerto de projeto em A3 paisagem: fica fora das medidas da página A4.
        {"tamanho": (1190.55, 841.89), "imagens": [_imagem(78, 78, 900, 640)], "linhas": []},
        _pagina(8, [("8.", "RELATÓRIO FOTOGRÁFICO", 14.0)], paragrafos=6),
    ]
    if com_fotos:
        paginas += [_pagina_de_fotos(9, (1, 2)), _pagina_de_fotos(10, (3, 4))]
    paginas += [
        _analise(11),
        _pagina(12, [("10.", "CONCLUSÃO E CONSIDERAÇÕES FINAIS", 14.0)]),
        _encerramento(13),
        _pagina(14, [("12.", "REFERÊNCIAS BIBLIOGRÁFICAS", 14.0)]),
    ]
    return paginas


@pytest.fixture
def pdf_vistoria(tmp_path: Path) -> Path:
    destino = tmp_path / "vistoria_ap_101_sintetica.pdf"
    destino.write_bytes(_pdf_sintetico(_paginas_do_laudo()))
    return destino


@pytest.fixture
def layout(pdf_vistoria: Path) -> dict:
    return extrair_layout(pdf_vistoria)


def _contexto() -> dict:
    return {
        "fiscal": {"nome": "Responsável Exemplo", "crea": "000", "email": "r@exemplo.invalid", "telefone": "0",
                   "qualificacoes": ["Especialista em Perícias"]},
        "imovel": {"unidade": "Unidade 1"},
        "edificacao": {"nome": "Edifício X"},
        "data_emissao": "1 de janeiro de 2027",
        "local_emissao": "Cidade",
        "textos": {chave_secao("1."): ["Parágrafo de introdução."]},
        "fotos": [{"numero": 1, "legenda": "Sala", "fonte": None, "imagem": "", "data_uri": ""}],
        "sistemas": [{"nome": "Estrutura", "constatacoes": ["Fissura"], "fundamentacao_tecnica": ["Texto."]}],
    }


def _xml_docx(caminho: Path) -> str:
    with zipfile.ZipFile(caminho) as pacote:
        return "".join(
            pacote.read(nome).decode("utf-8")
            for nome in pacote.namelist()
            if nome.startswith("word/") and nome.endswith(".xml")
        )


def _texto_docx(caminho: Path) -> str:
    """Texto de corpo, cabeçalho e rodapé, sem as quebras de `run` do XML."""
    return re.sub(r"<[^>]+>", "", _xml_docx(caminho).replace("</w:p>", "\n"))


# --------------------------------------------------------------------- extrator


def test_extrai_geometria_da_pagina(layout: dict) -> None:
    assert layout["tipo_documento"] == "VISTORIA_RESIDENCIAL"
    assert layout["pagina"]["tamanho"] == "A4"
    assert layout["pagina"]["orientacao"] == "portrait"
    margens = layout["pagina"]["margens_cm"]
    assert margens["esquerda"] == pytest.approx(3.0, abs=0.05)
    assert margens["direita"] == pytest.approx(1.99, abs=0.05)
    assert margens["superior"] == pytest.approx(2.58, abs=0.1)
    assert margens["inferior"] == pytest.approx(1.94, abs=0.1)
    assert layout["origem"]["paginas_fora_do_a4"] == 1


def test_mede_tipografia_e_cores(layout: dict) -> None:
    # Base-14 `Times-Roman` no sintético; `TimesNewRomanPSMT` no original.
    assert layout["tipografia"]["familia"] == "Times"
    assert layout["tipografia"]["corpo_pt"] == 12.0
    assert layout["tipografia"]["titulo_pt"] == 14.0
    assert layout["tipografia"]["legenda_pt"] == 9.0
    assert layout["cores"] == {"texto": "#000000", "legenda": "#44546A", "link": "#0563C1", "capa_texto": "#FFFFFF"}


def test_cabecalho_tem_logo_a_direita(layout: dict) -> None:
    logo = layout["cabecalho"]["logo"]
    assert logo["alinhamento"] == "direita"
    assert logo["largura_pt"] == pytest.approx(109.4, abs=0.2)
    assert logo["topo_pt"] == pytest.approx(13.0, abs=0.2)


def test_rodape_vira_placeholder_com_numeracao(layout: dict) -> None:
    rodape = layout["rodape"]
    assert rodape["papeis"] == ["nome", "registro", "contato"]
    assert rodape["linhas"][0] == "{{ fiscal.nome }}"
    assert "{{ fiscal.crea }}" in rodape["linhas"][1]
    assert rodape["linhas"][2] == "{{ fiscal.email }} / {{ fiscal.telefone }}"
    assert rodape["fonte_pt"] == 10.0
    assert rodape["cor_link"] == "#0563C1"
    assert rodape["numeracao_pagina"]["alinhamento"] == "direita"


def test_mapeia_secoes_fixas_na_ordem_do_laudo(layout: dict) -> None:
    numeros = [secao["numero"] for secao in layout["secoes"]]
    assert numeros == ["1.", "1.1.", "2.", "2.1.", "4.", "4.2.", "4.2.1.", "8.", "9.", "10.", "11.", "12."]
    tipos = {secao["numero"]: secao["tipo"] for secao in layout["secoes"]}
    assert tipos["8."] == "fotografico"
    assert tipos["9."] == "por_sistema"
    # As subseções do capítulo 9 são os sistemas do caso: viram laço, não título fixo.
    assert "9.1." not in numeros
    titulo_projetos = next(secao["titulo"] for secao in layout["secoes"] if secao["numero"] == "4.2.1.")
    assert titulo_projetos == "Projetos do {{ imovel.unidade }}"


def test_mede_grade_e_legenda_do_relatorio_fotografico(layout: dict) -> None:
    fotos = layout["relatorio_fotografico"]
    assert fotos["fotos_por_pagina"] == 2
    assert fotos["colunas"] == 1
    assert fotos["foto_largura_cm"] == pytest.approx(16.0, abs=0.05)
    assert fotos["foto_altura_cm"] == pytest.approx(9.0, abs=0.05)
    legenda = fotos["legenda"]
    assert legenda["italico"] is True
    assert legenda["posicao"] == "abaixo"
    assert legenda["separador"] == "-"
    assert legenda["fonte_padrao"] == "Autor"


def test_analise_por_sistema_tem_subtitulos_fixos(layout: dict) -> None:
    analise = layout["analise_por_sistema"]
    assert [(item["chave"], item["lista"]) for item in analise["subtitulos"]] == [
        ("constatacoes", True),
        ("fundamentacao_tecnica", False),
    ]
    assert analise["marcador"] == "➢"


def test_mede_bloco_de_assinatura(layout: dict) -> None:
    assinatura = layout["assinatura"]
    assert assinatura["secao"] == "11."
    assert assinatura["alinhamento"] == "direita"
    assert assinatura["nome_negrito"] is True
    assert assinatura["rubrica"] == {"largura_pt": 137.7, "altura_pt": 79.7}
    assert assinatura["local_data"] is True


def test_capa_e_folha_de_rosto_guardam_so_rotulos_fixos(layout: dict) -> None:
    capa = layout["capa"]
    assert capa["titulo"]["texto"] == "VISTORIA TÉCNICA PARA RECEBIMENTO DE IMÓVEL"
    assert capa["rotulo_responsavel"] == "RESP. TÉCNICO:"
    assert capa["imagem_de_fundo"] is True
    assert capa["logo"]["alinhamento"] == "direita"
    rosto = layout["folha_de_rosto"]
    assert rosto["titulo"]["linhas"] == ["LAUDO TÉCNICO DE", "VISTORIA", "PARA RECEBIMENTO DE IMÓVEL"]
    assert rosto["identificacao"]["linhas_no_exemplar"] == 2
    assert rosto["data"]["fonte_pt"] == 18.0


def test_layout_nao_carrega_dado_pessoal_do_exemplar(layout: dict) -> None:
    """Regressão de privacidade (OWASP A02): o layout.json é versionado."""
    serializado = json.dumps(layout, ensure_ascii=False)
    vazados = [dado for dado in DADOS_PESSOAIS if dado in serializado]
    assert vazados == []
    assert "vistoria_ap_101" not in serializado
    assert "arquivo" not in layout["origem"]
    assert len(layout["origem"]["sha256"]) == 64


def test_anonimizar_troca_dado_pessoal_por_placeholder() -> None:
    assert anonimizar(CREA) == "Eng. Civil - CREA nº {{ fiscal.crea }}"
    assert anonimizar(CONTATO) == "{{ fiscal.email }} / {{ fiscal.telefone }}"
    assert anonimizar("Projetos do Apartamento 101") == "Projetos do {{ imovel.unidade }}"
    assert anonimizar("CPF 123.456.789-09, CEP 74000-000") == "CPF {{ contratante.cpf_cnpj }}, CEP {{ edificacao.cep }}"


def test_guarda_final_recusa_layout_com_dado_pessoal(layout: dict) -> None:
    layout["secoes"][0]["titulo"] = "Contato: fulano.tal@example.com"
    with pytest.raises(LayoutExtractionError, match="Nada foi gravado"):
        verificar_sem_dados_pessoais(layout)


def test_original_ausente_falha_explicitamente(tmp_path: Path) -> None:
    with pytest.raises(LayoutExtractionError, match="não encontrado"):
        extrair_layout(tmp_path / "inexistente.pdf")


def test_pdf_sem_relatorio_fotografico_falha(tmp_path: Path) -> None:
    destino = tmp_path / "sem_fotos.pdf"
    destino.write_bytes(_pdf_sintetico(_paginas_do_laudo(com_fotos=False)))
    with pytest.raises(LayoutExtractionError, match="Nenhuma foto"):
        extrair_layout(destino)


# --------------------------------------------------------------------- templates


def _tags_jinja(texto: str) -> str:
    return " ".join(re.findall(r"\{\{.*?\}\}|\{%.*?%\}", texto))


def test_html_tem_placeholders_e_medidas(layout: dict) -> None:
    html = gerar_html(layout)
    tags = _tags_jinja(html)
    faltando = [variavel for variavel in PLACEHOLDERS if variavel not in tags]
    assert faltando == []
    margens = layout["pagina"]["margens_cm"]
    assert "size: A4 portrait" in html
    assert f"margin: {margens['superior']}cm {margens['direita']}cm {margens['inferior']}cm {margens['esquerda']}cm" in html
    assert "color: #44546A" in html
    assert "{% for foto in fotos %}" in html
    assert "{% for sistema in sistemas %}" in html
    assert "9.{{ loop.index }}. {{ sistema.nome }}" in html


def test_docx_tem_placeholders_e_blocos_balanceados(layout: dict, tmp_path: Path) -> None:
    from docxtpl import DocxTemplate

    destino = tmp_path / "vistoria.docx"
    gerar_docx(layout, destino)
    template = DocxTemplate(destino)
    template.init_docx()
    xml = template.patch_xml(template.get_xml())
    tags = _tags_jinja(_texto_docx(destino))
    faltando = [variavel for variavel in PLACEHOLDERS if variavel not in tags]
    assert faltando == []
    blocos = re.findall(r"\{%[^%]*%\}", xml)
    assert sum(1 for tag in blocos if " for " in tag) == sum(1 for tag in blocos if "endfor" in tag)


def test_pdf_e_docx_derivam_do_mesmo_layout(layout: dict, tmp_path: Path) -> None:
    from docx import Document

    destino = tmp_path / "vistoria.docx"
    gerar_docx(layout, destino)
    html = gerar_html(layout)
    texto_docx = _texto_docx(destino)
    for secao in layout["secoes"]:
        rotulo = f"{secao['numero']} {secao['titulo']}"
        assert rotulo in html, rotulo
        assert rotulo in texto_docx, rotulo
    for subtitulo in layout["analise_por_sistema"]["subtitulos"]:
        assert subtitulo["rotulo"] in html and subtitulo["rotulo"] in texto_docx
    for linha in layout["rodape"]["linhas"]:
        assert linha in html and linha in texto_docx

    secao_docx = Document(destino).sections[0]
    margens = layout["pagina"]["margens_cm"]
    assert secao_docx.left_margin.cm == pytest.approx(margens["esquerda"], abs=0.01)
    assert secao_docx.top_margin.cm == pytest.approx(margens["superior"], abs=0.01)

    # Mudou o layout, mudam os dois formatos.
    layout["tipografia"]["corpo_pt"] = 11.0
    layout["secoes"][0]["titulo"] = "APRESENTAÇÃO"
    outro = tmp_path / "outro.docx"
    gerar_docx(layout, outro)
    assert "font-size: 11.0pt" in gerar_html(layout)
    assert "1. APRESENTAÇÃO" in gerar_html(layout)
    assert Document(outro).styles["Normal"].font.size.pt == 11.0
    assert "1. APRESENTAÇÃO" in _texto_docx(outro)


def test_geracao_e_deterministica(layout: dict, tmp_path: Path) -> None:
    assert gerar_html(layout) == gerar_html(layout)
    primeiro, segundo = tmp_path / "a.docx", tmp_path / "b.docx"
    gerar_docx(layout, primeiro)
    gerar_docx(layout, segundo)
    assert _xml_docx(primeiro) == _xml_docx(segundo)


def test_templates_renderizam_com_contexto_de_exemplo(layout: dict, tmp_path: Path) -> None:
    import jinja2
    from docxtpl import DocxTemplate

    html = jinja2.Environment(autoescape=True).from_string(gerar_html(layout)).render(**_contexto())
    assert "Figura 1 - Sala. Fonte: Autor." in html
    assert "9.1. Estrutura" in html
    assert "Cidade, 1 de janeiro de 2027." in html

    destino = tmp_path / "vistoria.docx"
    gerar_docx(layout, destino)
    template = DocxTemplate(destino)
    template.render(_contexto())
    renderizado = tmp_path / "renderizado.docx"
    template.save(renderizado)
    texto = _texto_docx(renderizado)
    assert "Figura 1 - Sala. Fonte: Autor." in texto
    assert "• Fissura" in texto
    assert "{%" not in texto and "{{" not in texto


def test_pdf_renderiza_com_weasyprint(layout: dict) -> None:
    try:
        from weasyprint import HTML
    except (ImportError, OSError) as erro:  # GTK/Pango ausentes
        pytest.skip(f"WeasyPrint indisponível neste ambiente (não roda no Windows local, só no container): {erro}")
    import jinja2

    html = jinja2.Environment(autoescape=True).from_string(gerar_html(layout)).render(**_contexto())
    pdf = HTML(string=html).write_pdf()
    assert pdf.startswith(b"%PDF")


def test_artefatos_versionados_estao_em_dia_com_o_layout() -> None:
    """`layout.json` versionado: sem dado pessoal e com os dois templates regenerados a partir dele."""
    if not LAYOUT_JSON.is_file():
        pytest.skip("layout.json ainda não gerado nesta máquina.")
    layout_versionado = json.loads(LAYOUT_JSON.read_text(encoding="utf-8"))
    assert layout_versionado["tipo_documento"] == "VISTORIA_RESIDENCIAL"
    assert "arquivo" not in layout_versionado["origem"]
    verificar_sem_dados_pessoais(layout_versionado)
    assert HTML_TEMPLATE.read_text(encoding="utf-8") == gerar_html(layout_versionado)
    assert DOCX_TEMPLATE.is_file()
