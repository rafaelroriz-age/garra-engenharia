"""Testes dos templates da Vistoria Cautelar (ADR-13/DEC-25, RF-06, RNF-03, OWASP A02).

Não dependem de `01_output-context/`: o PDF sintético é montado no próprio teste
com a geometria medida no original (A4, Times 12/14, logo no cabeçalho à
direita, rodapé de 3 linhas + número de página, 2 fotos por página com legenda
itálica, tabela com cabeçalho sombreado e bloco de assinatura à direita) e com
dados pessoais **fictícios** em capa, folha de rosto, rodapé e assinatura — que
precisam sumir do `layout.json`.
"""

from __future__ import annotations

import io
import json
import re
import zipfile
from pathlib import Path

import pytest

from app.scripts.build_vistoria_cautelar_templates import (
    DOCX_TEMPLATE,
    HTML_TEMPLATE,
    LAYOUT_JSON,
    gerar_docx,
    gerar_html,
)
from app.scripts.vistoria_cautelar_layout_extractor import (
    PH_CONTATO,
    PH_DATA_MES_ANO,
    PH_NOME,
    PH_OBRA,
    PH_REGISTRO,
    LayoutExtractionError,
    _garantir_sem_dados_pessoais,
    extrair_layout,
)

LARGURA = 595.28
ALTURA = 841.89
AZUL_LINK = (0.0196, 0.388, 0.757)
CINZA_LEGENDA = (0.267, 0.329, 0.416)
AZUL_CAPA = (0.2863, 0.3373, 0.498)
FUNDO_TABELA = (0.871, 0.918, 0.965)
BRANCO = (1.0, 1.0, 1.0)
PRETO = (0.0, 0.0, 0.0)

#: Dados pessoais fictícios espalhados pelo PDF sintético; nenhum pode chegar ao layout.
DADOS_PESSOAIS = (
    "Fulano de Tal",
    "FULANO DE TAL",
    "1234567890",
    "fulano.teste@exemplo.com",
    "98888-7777",
    "Condomínio Fictício",
    "Cond. Residencial Fictício",
    "Cidade Fictícia",
    "IBAPE-XX",
    "Retrofit do Pav",
    "22 de junho de 2026",
    "JUNHO DE 2026",
)

FONTES = {
    "F1": "Times-Roman",
    "F2": "Times-Bold",
    "F3": "Helvetica-Oblique",
    "F4": "Helvetica-Bold",
}


# --------------------------------------------------------------------------------------
# PDF sintético (escrito à mão: WeasyPrint não roda no Windows e o teste não lê o original)
# --------------------------------------------------------------------------------------


def _texto(x: float, topo: float, fonte: str, corpo: float, texto: str, cor=PRETO) -> tuple:
    return ("t", x, topo, fonte, corpo, texto, cor)


def _imagem(x: float, topo: float, largura: float, altura: float) -> tuple:
    return ("img", x, topo, largura, altura)


def _retangulo(x: float, topo: float, largura: float, altura: float, cor) -> tuple:
    return ("rect", x, topo, largura, altura, cor)


def _fluxo(elementos: list[tuple]) -> bytes:
    partes = []
    for elemento in elementos:
        if elemento[0] == "img":
            _, x, topo, largura, altura = elemento
            partes.append(f"q {largura:.2f} 0 0 {altura:.2f} {x:.2f} {ALTURA - topo - altura:.2f} cm /Im1 Do Q")
        elif elemento[0] == "rect":
            _, x, topo, largura, altura, cor = elemento
            partes.append(f"{cor[0]} {cor[1]} {cor[2]} rg {x:.2f} {ALTURA - topo - altura:.2f} {largura:.2f} {altura:.2f} re f")
        else:
            _, x, topo, fonte, corpo, texto, cor = elemento
            escapado = texto.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")
            # Base do texto a partir do topo desejado (descendente ~0,22 em; corpo = 1 em).
            base = ALTURA - topo - 0.78 * corpo
            partes.append(
                f"BT {cor[0]} {cor[1]} {cor[2]} rg /{fonte} {corpo} Tf 1 0 0 1 {x:.2f} {base:.2f} Tm ({escapado}) Tj ET"
            )
    return "\n".join(partes).encode("cp1252")


def _pdf(paginas: list[list[tuple]]) -> bytes:
    objetos: list[bytes] = []

    def adicionar(corpo: bytes) -> int:
        objetos.append(corpo)
        return len(objetos)

    fontes = {
        nome: adicionar(b"<< /Type /Font /Subtype /Type1 /BaseFont /%s /Encoding /WinAnsiEncoding >>" % base.encode())
        for nome, base in FONTES.items()
    }
    imagem = adicionar(
        b"<< /Type /XObject /Subtype /Image /Width 1 /Height 1 /ColorSpace /DeviceGray "
        b"/BitsPerComponent 8 /Length 1 >>\nstream\n\x80\nendstream"
    )
    recursos = b"<< /Font << %s >> /XObject << /Im1 %d 0 R >> >>" % (
        b" ".join(b"/%s %d 0 R" % (nome.encode(), ident) for nome, ident in fontes.items()),
        imagem,
    )
    conteudos = []
    for elementos in paginas:
        fluxo = _fluxo(elementos)
        conteudos.append(adicionar(b"<< /Length %d >>\nstream\n%s\nendstream" % (len(fluxo), fluxo)))
    id_pages = len(objetos) + len(paginas) + 1
    ids_paginas = [
        adicionar(
            b"<< /Type /Page /Parent %d 0 R /MediaBox [0 0 %.2f %.2f] /Resources %s /Contents %d 0 R >>"
            % (id_pages, LARGURA, ALTURA, recursos, conteudo)
        )
        for conteudo in conteudos
    ]
    kids = b" ".join(b"%d 0 R" % ident for ident in ids_paginas)
    assert adicionar(b"<< /Type /Pages /Kids [%s] /Count %d >>" % (kids, len(ids_paginas))) == id_pages
    catalogo = adicionar(b"<< /Type /Catalog /Pages %d 0 R >>" % id_pages)

    saida = bytearray(b"%PDF-1.4\n")
    offsets = []
    for numero, corpo in enumerate(objetos, start=1):
        offsets.append(len(saida))
        saida += b"%d 0 obj\n%s\nendobj\n" % (numero, corpo)
    xref = len(saida)
    saida += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objetos) + 1)
    for offset in offsets:
        saida += b"%010d 00000 n \n" % offset
    saida += b"trailer\n<< /Size %d /Root %d 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objetos) + 1, catalogo, xref)
    return bytes(saida)


def _moldura(numero_impresso: int) -> list[tuple]:
    """Logo do cabeçalho + rodapé do responsável técnico + número da página."""
    return [
        _imagem(448, 13, 109, 52),
        _texto(246, 787, "F1", 10, "Fulano de Tal"),
        _texto(196, 799, "F1", 10, "Eng. Civil - CREA-XX nº 1234567890/D-XX"),
        _texto(196, 811, "F1", 10, "fulano.teste@exemplo.com / (62) 98888-7777", AZUL_LINK),
        _texto(512, 824, "F1", 11, str(numero_impresso)),
    ]


def _paragrafos(topo: float, linhas: int = 6) -> tuple[list[tuple], float]:
    """Parágrafos justificados (x 85 -> 539), entrelinha 15 e 6 pt entre parágrafos."""
    elementos = []
    for indice in range(linhas):
        elementos.append(_texto(85, topo, "F1", 12, "Texto corrido do laudo de vistoria"))
        elementos.append(_texto(519.3, topo, "F1", 12, "fim."))
        topo += 21 if indice % 3 == 2 else 15
    return elementos, topo


def _titulo(numero: str, texto: str, topo: float) -> list[tuple]:
    # Afastado do número para o `extract_words` não fundir "1." e o título.
    return [_texto(71, topo, "F2", 14, numero), _texto(111, topo, "F2", 14, texto)]


def _pagina_de_texto(numero_impresso: int, titulos: list[tuple[str, str]]) -> list[tuple]:
    elementos = _moldura(numero_impresso)
    topo = 80.0
    for numero, texto in titulos:
        elementos += _titulo(numero, texto, topo)
        topo += 29
        corpo, topo = _paragrafos(topo, 6)
        elementos += corpo
        topo += 10
    return elementos


def _figura(numero: int, topo: float, descricao: str) -> list[tuple]:
    return [
        _imagem(85, topo, 454, 255),
        _texto(85, topo + 263, "F3", 9, f"Figura {numero} - {descricao}. Verificou-se falha localizada", CINZA_LEGENDA),
        _texto(85, topo + 274, "F3", 9, "no elemento registrado. Fonte: Autor.", CINZA_LEGENDA),
    ]


@pytest.fixture(scope="module")
def pdf_vistoria(tmp_path_factory: pytest.TempPathFactory) -> Path:
    capa = [
        _imagem(0, 0, LARGURA, ALTURA),
        _imagem(160, 0, 275, 150),
        _imagem(17, 676, 314, 138),
        _texto(27, 188, "F4", 34.4, "VISTORIA TÉCNICA", BRANCO),
        _texto(27, 229, "F4", 34.4, "CAUTELAR PARA", BRANCO),
        _texto(27, 269, "F4", 34.4, "RECEBIMENTO", BRANCO),
        _texto(27, 310, "F4", 34.4, "DE OBRA", BRANCO),
        _texto(27, 357, "F4", 15.4, "Retrofit do Pav. Térreo", BRANCO),
        _texto(27, 375, "F4", 15.4, "Cond. Residencial Fictício", BRANCO),
        _texto(31, 751, "F4", 15, "RESP. TÉCNICO:", AZUL_CAPA),
        _texto(31, 768, "F4", 15, "ENG. CIVIL FULANO DE TAL", AZUL_CAPA),
        _texto(31, 786, "F4", 15, "CREA: 1234567890-D/XX", AZUL_CAPA),
        _texto(450, 804, "F4", 15.4, "JUNHO DE 2026", BRANCO),
    ]
    folha_de_rosto = [
        *_moldura(1),
        _texto(129, 139, "F2", 36, "LAUDO TÉCNICO DE"),
        _texto(223, 187, "F2", 36, "VISTORIA"),
        _texto(156, 242, "F2", 36, "CAUTELAR PARA"),
        _texto(89, 290, "F2", 36, "RECEBIMENTO DE OBRA"),
        _texto(163, 401, "F2", 36, "Reforma Térrea do"),
        _texto(130, 442, "F2", 36, "Condomínio Fictício"),
        _texto(256, 658, "F2", 18, "Junho de 2026"),
    ]
    sumario = [*_moldura(2), _texto(85, 118, "F2", 16, "SUMÁRIO")]
    for indice, (numero, texto, x) in enumerate(
        [("1.", "INTRODUÇÃO", 85), ("1.1.", "Histórico", 96), ("2.", "CONSIDERAÇÕES", 85), ("5.1.1.", "Constatações", 107)]
    ):
        topo = 143 + indice * 19
        sumario += [
            _texto(x, topo, "F2", 11, numero),
            _texto(x + 30, topo, "F2", 11, texto),
            _texto(300, topo, "F2", 11, "........................"),
            _texto(510, topo, "F2", 11, "4"),
        ]

    paginas = [capa, folha_de_rosto, sumario]
    paginas.append(_pagina_de_texto(3, [("1.", "INTRODUÇÃO"), ("1.1.", "Histórico e Contexto da Diligência")]))
    paginas.append(
        _pagina_de_texto(4, [("2.", "CONSIDERAÇÕES PRELIMINARES"), ("2.1.", "Geral"), ("2.2.", "Pressupostos e ressalvas")])
    )
    paginas.append(_pagina_de_texto(5, [("3.", "OBJETIVO"), ("3.1.", "Geral")]))
    fotos_1 = _moldura(6) + _titulo("4.", "RELATÓRIO FOTOGRÁFICO", 73) + _paragrafos(109, 3)[0] + _figura(1, 216, "Vista geral")
    paginas.append(fotos_1)
    paginas.append(_moldura(7) + _figura(2, 71, "Deficiência de acabamento") + _figura(3, 386, "Sujidades no piso"))
    paginas.append(_moldura(8) + _figura(4, 71, "Fissura no forro") + _figura(5, 386, "Falha de pintura"))
    paginas.append(
        _pagina_de_texto(
            9,
            [
                ("5.", "ANÁLISE E CONSIDERAÇÕES TÉCNICAS"),
                ("5.1.", "Revestimentos de Pintura"),
                ("5.1.1.", "Constatações"),
                ("5.1.2.", "Fundamentação Técnica"),
            ],
        )
    )
    paginas.append(
        _pagina_de_texto(
            10,
            [
                ("5.2.", "Instalações Elétricas"),
                ("5.2.1.", "Constatações"),
                ("5.2.2.", "Fundamentação Técnica"),
                ("5.3.", "Correlação Técnica e Responsabilidade"),
            ],
        )
    )
    conclusao = _pagina_de_texto(
        11,
        [
            ("6.", "CONCLUSÃO E CONSIDERAÇÕES FINAIS"),
            ("6.1.", "Parecer Técnico — Recebimento Parcial com Ressalvas"),
            ("6.2.", "Plano de Correções Remanescentes"),
        ],
    )
    for x, largura, rotulo in ((63, 28, "Item"), (91, 92, "Localização"), (183, 149, "Descrição da Pendência"),
                               (332, 208, "Metodologia Corretiva Indicada")):
        conclusao += [_retangulo(x, 560, largura, 16, FUNDO_TABELA), _texto(x + 3, 562, "F2", 12, rotulo)]
    conclusao += [
        _texto(66, 590, "F1", 12, "1"),
        _texto(94, 590, "F1", 12, "Hall"),
        _texto(186, 590, "F1", 12, "Fiação exposta"),
        _texto(335, 590, "F1", 12, "Isolar e proteger"),
    ]
    paginas.append(conclusao)
    encerramento = [*_pagina_de_texto(12, [("7.", "ENCERRAMENTO")]),
        _imagem(341, 478, 138, 80),
        _texto(251, 518, "F1", 12, "_" * 48),
        _texto(440, 535, "F2", 12, "Fulano de Tal"),
        _texto(350, 552, "F1", 12, "Eng. Civil - CREA nº 1234567890 D-XX;"),
        _texto(356, 569, "F1", 12, "Membro titular do IBAPE-XX, nº 999;"),
        _texto(326, 650, "F1", 12, "Cidade Fictícia, 22 de junho de 2026."),
    ]
    paginas.append(encerramento)

    destino = tmp_path_factory.mktemp("vistoria") / "laudo_sintetico_vistoria.pdf"
    destino.write_bytes(_pdf(paginas))
    return destino


@pytest.fixture(scope="module")
def layout(pdf_vistoria: Path) -> dict:
    return extrair_layout(pdf_vistoria)


def contexto_exemplo() -> dict:
    """Contexto mínimo de renderização (nomes fictícios), igual para HTML e DOCX."""
    return {
        "responsavel": {
            "nome": "Beltrana Exemplo",
            "titulo_profissional": "Eng. Civil",
            "crea": "000/D-ZZ",
            "email": "contato@exemplo.test",
            "telefone": "(00) 0000-0000",
            "qualificacoes": ["Especialista em Perícias"],
        },
        "obra": {"descricao": "Reforma de Exemplo"},
        "edificacao": {"nome": "Edifício Exemplo"},
        "data_emissao_mes_ano": "Março de 2030",
        "data_emissao_extenso": "1 de março de 2030",
        "local_emissao": "Cidade Exemplo",
        "conteudo": {"introducao": ["Parágrafo de introdução."]},
        "complementos": {"parecer_tecnico": "Recebimento com Ressalvas"},
        "sistemas": [
            {"nome": "Pintura", "constatacoes": ["Constatação A."], "fundamentacao_tecnica": ["Fundamento A."]},
            {"nome": "Elétrica", "constatacoes": ["Constatação B."], "fundamentacao_tecnica": []},
        ],
        "figuras": [{"numero": 1, "legenda": "Vista de exemplo.", "foto_data_uri": "", "imagem": ""}],
        "tabelas": {
            "plano_de_correcoes_remanescentes": [
                {
                    "item": "1",
                    "localizacao": "Hall",
                    "descricao_da_pendencia": "Pendência X",
                    "metodologia_corretiva_indicada": "Corrigir Y",
                }
            ]
        },
        "logo_data_uri": "",
        "capa_fundo_data_uri": "",
        "assinatura_data_uri": "",
        "assinatura_imagem": "",
    }


#: Placeholders que os dois templates precisam ter (dados pessoais e do caso).
PLACEHOLDERS = (
    "{{ responsavel.nome }}",
    "{{ responsavel.crea }}",
    "{{ responsavel.email }}",
    "{{ responsavel.telefone }}",
    "{{ obra.descricao }}",
    "{{ data_emissao_mes_ano",
    "{{ local_emissao }}, {{ data_emissao_extenso }}.",
    "responsavel.qualificacoes",
    "{{ sistema.nome }}",
    "{{ figura.legenda }}",
    "{{ linha.metodologia_corretiva_indicada }}",
)


def _texto_docx(caminho_ou_bytes) -> str:
    """Todo o XML de texto do DOCX (corpo, cabeçalhos e rodapés), sem as tags de run."""
    origem = io.BytesIO(caminho_ou_bytes) if isinstance(caminho_ou_bytes, bytes) else caminho_ou_bytes
    with zipfile.ZipFile(origem) as pacote:
        partes = [
            pacote.read(nome).decode("utf-8")
            for nome in sorted(pacote.namelist())
            if re.match(r"word/(document|header\d*|footer\d*)\.xml$", nome)
        ]
    return "".join(re.sub(r"<[^>]+>", "", parte) for parte in partes)


def _titulos_docx(caminho: Path, nivel: int) -> list[str]:
    from docx import Document

    return [p.text for p in Document(caminho).paragraphs if p.style.name == f"Heading {nivel}"]


# --------------------------------------------------------------------------------------
# Extrator
# --------------------------------------------------------------------------------------


def test_mede_pagina_margens_e_tipografia(layout: dict) -> None:
    assert layout["tipo_documento"] == "VISTORIA_CAUTELAR"
    assert layout["pagina"]["tamanho"] == "A4"
    margens = layout["pagina"]["margens_cm"]
    assert margens["esquerda"] == pytest.approx(3.0, abs=0.05)
    assert margens["direita"] == pytest.approx(2.0, abs=0.1)
    assert margens["inferior"] == pytest.approx((ALTURA - 787) * 2.54 / 72, abs=0.1)
    assert layout["tipografia"]["familia"] == "Times"
    assert layout["tipografia"]["corpo_pt"] == 12.0
    assert layout["tipografia"]["titulo_pt"] == 14.0
    assert layout["paragrafo"]["entrelinha_pt"] == 15.0
    assert layout["paragrafo"]["espaco_entre_paragrafos_pt"] == 6.0
    assert layout["paragrafo"]["alinhamento"] == "justify"


def test_cabecalho_e_rodape_guardam_geometria_e_placeholders(layout: dict) -> None:
    logo = layout["cabecalho"]["logo"]
    assert logo["alinhamento"] == "right"
    assert logo["largura_pt"] == pytest.approx(109, abs=1)
    rodape = layout["rodape"]
    assert [linha["modelo"] for linha in rodape["linhas"]] == [PH_NOME, PH_REGISTRO, PH_CONTATO]
    assert rodape["linhas"][2]["cor"] == "#0563C1"
    assert rodape["numeracao_pagina"]["fonte_pt"] == 11.0
    # A capa não é contada: a página física 2 recebe o número 1.
    assert rodape["numeracao_pagina"]["deslocamento"] == -1


def test_capa_e_folha_de_rosto_separam_titulo_fixo_de_dado_do_caso(layout: dict) -> None:
    capa = layout["capa"]
    assert capa["titulo"]["linhas"] == ["VISTORIA TÉCNICA", "CAUTELAR PARA", "RECEBIMENTO", "DE OBRA"]
    assert capa["titulo"]["fonte_pt"] == 34.4
    assert capa["titulo"]["cor"] == "#FFFFFF"
    assert capa["imagem_de_fundo"] is True
    papeis = {elemento["papel"]: elemento for elemento in capa["elementos"]}
    assert set(papeis) == {"subtitulo", "responsavel", "data"}
    assert papeis["subtitulo"]["linhas"] == [PH_OBRA, "{{ edificacao.nome }}"]
    assert papeis["responsavel"]["linhas"][0] == "RESP. TÉCNICO:"
    assert papeis["responsavel"]["faixa"] is not None
    assert papeis["data"]["alinhamento"] == "right"

    folha = layout["folha_de_rosto"]
    assert folha["titulo"]["linhas"] == ["LAUDO TÉCNICO DE", "VISTORIA", "CAUTELAR PARA", "RECEBIMENTO DE OBRA"]
    assert folha["objeto"]["modelo"] == PH_OBRA
    assert folha["data"]["modelo"] == PH_DATA_MES_ANO
    assert layout["sumario"]["titulo_pt"] == 16.0
    assert layout["sumario"]["entrada_pt"] == 11.0


def test_mapeia_ordem_e_titulos_fixos_das_secoes(layout: dict) -> None:
    secoes = layout["estrutura"]["secoes"]
    assert [(secao["numero"], secao["titulo"]) for secao in secoes] == [
        ("1", "INTRODUÇÃO"),
        ("2", "CONSIDERAÇÕES PRELIMINARES"),
        ("3", "OBJETIVO"),
        ("4", "RELATÓRIO FOTOGRÁFICO"),
        ("5", "ANÁLISE E CONSIDERAÇÕES TÉCNICAS"),
        ("6", "CONCLUSÃO E CONSIDERAÇÕES FINAIS"),
        ("7", "ENCERRAMENTO"),
    ]
    tipos = {secao["numero"]: secao["tipo"] for secao in secoes}
    assert tipos["4"] == "relatorio_fotografico"
    assert tipos["5"] == "por_sistema"
    assert tipos["7"] == "encerramento"

    analise = secoes[4]
    # Os sistemas (5.1, 5.2) são do caso: só os rótulos recorrentes ficam.
    assert analise["rotulos_por_sistema"] == [
        {"titulo": "Constatações", "chave": "constatacoes"},
        {"titulo": "Fundamentação Técnica", "chave": "fundamentacao_tecnica"},
    ]
    assert [sub["numero"] for sub in analise["subsecoes"]] == ["5.3"]
    assert analise["subsecoes"][0]["posicao"] == "depois_dos_sistemas"

    conclusao = secoes[5]["subsecoes"]
    assert conclusao[0]["titulo"] == "Parecer Técnico"
    assert conclusao[0]["complemento"] == {"separador": "—", "chave": "parecer_tecnico"}
    assert conclusao[1]["tabelas"] == ["plano_de_correcoes_remanescentes"]

    # "Geral" aparece em 2.1 e 3.1: a chave de conteúdo não pode colidir.
    chaves = [sub["chave"] for secao in secoes for sub in secao["subsecoes"]]
    assert len(chaves) == len(set(chaves))


def test_mede_grade_e_legenda_do_relatorio_fotografico(layout: dict) -> None:
    relatorio = layout["relatorio_fotografico"]
    assert relatorio["fotos_por_pagina"] == 2
    assert relatorio["foto"]["largura_pt"] == 454.0
    legenda = relatorio["legenda"]
    assert legenda["italico"] is True
    assert legenda["fonte_pt"] == 9.0
    assert legenda["cor"] == "#44546A"
    assert legenda["separador"] == "-"
    assert legenda["posicao"] == "abaixo"
    assert legenda["sufixo_fonte"] == "Fonte: Autor."


def test_mede_tabela_e_bloco_de_assinatura(layout: dict) -> None:
    (tabela,) = layout["tabelas"]
    assert [coluna["rotulo"] for coluna in tabela["colunas"]] == [
        "Item",
        "Localização",
        "Descrição da Pendência",
        "Metodologia Corretiva Indicada",
    ]
    assert tabela["cabecalho_fundo"] == "#DEEAF6"
    assert tabela["secao"] == "6.2"
    assert sum(coluna["largura_pct"] for coluna in tabela["colunas"]) == pytest.approx(100, abs=0.5)

    assinatura = layout["assinatura"]
    assert assinatura["alinhamento"] == "right"
    assert assinatura["linhas"] == [PH_NOME, PH_REGISTRO]
    assert assinatura["qualificacoes"]["linhas_medidas"] == 1
    assert assinatura["imagem_assinatura"] is not None
    assert assinatura["local_data"]["modelo"] == "{{ local_emissao }}, {{ data_emissao_extenso }}."


def test_layout_nao_carrega_dado_pessoal_do_exemplar(layout: dict) -> None:
    """Regressão de privacidade (OWASP A02): o layout.json é versionado."""
    serializado = json.dumps(layout, ensure_ascii=False)
    for dado in (*DADOS_PESSOAIS, "laudo_sintetico"):
        assert dado not in serializado, dado
    assert "arquivo" not in layout["origem"]
    assert len(layout["origem"]["sha256"]) == 64


def test_verificador_de_dado_pessoal_e_fail_closed() -> None:
    _garantir_sem_dados_pessoais({"cor": "#000000", "modelo": PH_CONTATO})
    for vazado in ("contato@exemplo.com", "(62) 98888-7777", "CREA 1234567890", "123.456.789-00", "74000-000"):
        with pytest.raises(LayoutExtractionError, match="Dado pessoal"):
            _garantir_sem_dados_pessoais({"rodape": [vazado]})


def test_original_ausente_falha_explicitamente(tmp_path: Path) -> None:
    with pytest.raises(LayoutExtractionError, match="não encontrado"):
        extrair_layout(tmp_path / "inexistente.pdf")


def test_pdf_sem_relatorio_fotografico_falha(tmp_path: Path) -> None:
    destino = tmp_path / "sem_fotos.pdf"
    destino.write_bytes(_pdf([[_texto(27, 188, "F4", 30, "CAPA")]] + [_pagina_de_texto(n, [("1.", "INTRODUÇÃO")]) for n in range(4)]))
    with pytest.raises(LayoutExtractionError, match="relatório fotográfico"):
        extrair_layout(destino)


# --------------------------------------------------------------------------------------
# Templates
# --------------------------------------------------------------------------------------


def test_html_tem_medidas_e_placeholders_e_renderiza(layout: dict) -> None:
    import jinja2

    html = gerar_html(layout)
    margens = layout["pagina"]["margens_cm"]
    assert "size: A4 portrait" in html
    assert f"margin: {margens['superior']}cm {margens['direita']}cm" in html
    assert f"font-size: {layout['tipografia']['corpo_pt']}pt" in html
    assert "#DEEAF6" in html and "#44546A" in html
    for placeholder in PLACEHOLDERS:
        assert placeholder in html, placeholder
    for dado in DADOS_PESSOAIS:
        assert dado not in html, dado

    ambiente = jinja2.Environment(undefined=jinja2.StrictUndefined, autoescape=True)
    renderizado = ambiente.from_string(html).render(**contexto_exemplo())
    assert "Beltrana Exemplo" in renderizado
    assert "5.1. Pintura" in renderizado and "5.2.2. Fundamentação Técnica" in renderizado
    # A subseção fixa depois dos sistemas é renumerada pela quantidade real de sistemas.
    assert "5.3. Correlação Técnica e Responsabilidade" in renderizado
    assert "Parecer Técnico — Recebimento com Ressalvas" in renderizado
    assert "Figura 1 - Vista de exemplo. Fonte: Autor." in renderizado
    assert "<td>Corrigir Y</td>" in renderizado


def test_docx_tem_placeholders_blocos_balanceados_e_renderiza(layout: dict, tmp_path: Path) -> None:
    from docx import Document
    from docxtpl import DocxTemplate

    destino = tmp_path / "vistoria_cautelar_template.docx"
    gerar_docx(layout, destino)
    texto = _texto_docx(destino)
    for placeholder in PLACEHOLDERS:
        assert placeholder in texto, placeholder
    for dado in DADOS_PESSOAIS:
        assert dado not in texto, dado

    template = DocxTemplate(destino)
    template.init_docx()
    tags = re.findall(r"\{%[^%]*%\}", template.patch_xml(template.get_xml()))
    assert sum(1 for tag in tags if re.search(r"\bfor\b", tag)) == sum(1 for tag in tags if "endfor" in tag)
    assert sum(1 for tag in tags if re.search(r"\bif\b", tag)) == sum(1 for tag in tags if "endif" in tag)

    template.render(contexto_exemplo())
    renderizado = tmp_path / "renderizado.docx"
    template.save(renderizado)
    documento = Document(renderizado)
    paragrafos = [p.text for p in documento.paragraphs]
    assert "5.1. Pintura" in paragrafos
    assert "5.3. Correlação Técnica e Responsabilidade" in paragrafos
    assert "6.1. Parecer Técnico — Recebimento com Ressalvas" in paragrafos
    assert "Cidade Exemplo, 1 de março de 2030." in paragrafos
    assert not [p for p in paragrafos if "{{" in p or "{%" in p]
    tabela = documento.tables[-1]
    assert [celula.text for celula in tabela.rows[1].cells] == ["1", "Hall", "Pendência X", "Corrigir Y"]
    rodape = [p.text for p in documento.sections[1].footer.paragraphs]
    assert rodape[:3] == ["Beltrana Exemplo", "Eng. Civil - CREA nº 000/D-ZZ", "contato@exemplo.test / (00) 0000-0000"]


def test_pdf_e_docx_derivam_do_mesmo_layout(layout: dict, tmp_path: Path) -> None:
    """RF-06: a mesma especificação gera os dois formatos — mudar o layout muda ambos."""
    html = gerar_html(layout)
    destino = tmp_path / "a.docx"
    gerar_docx(layout, destino)
    titulos_html = re.findall(r'<h1 id="[^"]+">([^<]+)</h1>', html)
    assert titulos_html == _titulos_docx(destino, 1)
    assert len(titulos_html) == len(layout["estrutura"]["secoes"])

    alterado = json.loads(json.dumps(layout))
    alterado["estrutura"]["secoes"][0]["titulo"] = "APRESENTAÇÃO"
    alterado["tabelas"][0]["colunas"][1]["rotulo"] = "Local"
    alterado["tipografia"]["corpo_pt"] = 11.0
    html_alterado = gerar_html(alterado)
    destino_alterado = tmp_path / "b.docx"
    gerar_docx(alterado, destino_alterado)
    assert "1. APRESENTAÇÃO" in html_alterado and "<th>Local</th>" in html_alterado
    assert "font-size: 11.0pt" in html_alterado
    assert _titulos_docx(destino_alterado, 1)[0] == "1. APRESENTAÇÃO"
    assert "Local" in _texto_docx(destino_alterado) and "Localização" not in _texto_docx(destino_alterado)


def test_geracao_e_deterministica(layout: dict, tmp_path: Path) -> None:
    assert gerar_html(layout) == gerar_html(json.loads(json.dumps(layout)))
    gerar_docx(layout, tmp_path / "1.docx")
    gerar_docx(layout, tmp_path / "2.docx")
    assert (tmp_path / "1.docx").read_bytes() == (tmp_path / "2.docx").read_bytes()


def test_artefatos_versionados_estao_em_dia_com_o_layout(tmp_path: Path) -> None:
    """layout.json versionado: sem dado pessoal e com os templates regenerados a partir dele."""
    if not LAYOUT_JSON.is_file():
        pytest.skip("templates/vistoria_cautelar/layout.json ainda não gerado nesta máquina.")
    versionado = json.loads(LAYOUT_JSON.read_text(encoding="utf-8"))
    assert versionado["versao_schema"] == 1
    assert versionado["tipo_documento"] == "VISTORIA_CAUTELAR"
    assert "arquivo" not in versionado["origem"]
    _garantir_sem_dados_pessoais(versionado)
    assert HTML_TEMPLATE.read_text(encoding="utf-8") == gerar_html(versionado)
    regenerado = tmp_path / "regenerado.docx"
    gerar_docx(versionado, regenerado)
    assert _texto_docx(regenerado) == _texto_docx(DOCX_TEMPLATE)


def test_pdf_renderizado_pelo_weasyprint_respeita_o_layout(layout: dict, tmp_path: Path) -> None:
    try:
        from weasyprint import HTML
    except (ImportError, OSError) as erro:  # pragma: no cover - depende do sistema
        pytest.skip(
            "WeasyPrint indisponível neste ambiente (no Windows local faltam as bibliotecas "
            f"Pango/GTK; o teste roda no container do backend): {type(erro).__name__}"
        )
    import jinja2
    import pdfplumber

    ambiente = jinja2.Environment(undefined=jinja2.StrictUndefined, autoescape=True)
    html = ambiente.from_string(gerar_html(layout)).render(**contexto_exemplo())
    destino = tmp_path / "vistoria.pdf"
    HTML(string=html).write_pdf(destino)
    with pdfplumber.open(destino) as pdf:
        primeira = pdf.pages[0]
        assert float(primeira.width) == pytest.approx(LARGURA, abs=1)
        assert float(primeira.height) == pytest.approx(ALTURA, abs=1)
        texto = "\n".join(pagina.extract_text() or "" for pagina in pdf.pages)
    assert "VISTORIA TÉCNICA" in texto
    assert "Beltrana Exemplo" in texto
    assert "5.1. Pintura" in texto
