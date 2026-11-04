"""Testes do pipeline de templates do RFIP (BL-12, ADR-13/DEC-25, DEC-35, RF-06, RNF-03).

Não dependem de `01_output-context/`: cada teste monta, em `tmp_path`, uma planilha
SINTÉTICA com a mesma estrutura do original (aba fotográfica com fichas de 24 linhas,
coluna auxiliar oculta `<CAMPO> Foto nº NN`, fotos ancoradas, rodapé com a
identificação do responsável e aba de resumo). Os valores preenchidos trazem dados
pessoais falsos de propósito, para provar que nenhum deles chega ao layout.json.
"""

from __future__ import annotations

import io
import json
import re
import zipfile
from html.parser import HTMLParser
from pathlib import Path

import jinja2
import openpyxl
import pytest
from openpyxl.drawing.image import Image as ImagemXlsx
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.page import PageMargins
from openpyxl.worksheet.pagebreak import Break
from openpyxl.worksheet.properties import PageSetupProperties
from PIL import Image

from app.scripts import rfip_layout_extractor
from app.scripts.build_rfip_templates import (
    DOCX_TEMPLATE,
    HTML_TEMPLATE,
    LAYOUT_JSON,
    especificacao_ficha,
    gerar_docx,
    gerar_html,
    gerar_templates,
    gravar_layout,
    tamanho_logo_cm,
)
from app.scripts.rfip_layout_extractor import (
    LayoutExtractionError,
    extrair_layout,
    garantir_sem_dados_pessoais,
)

CINZA = PatternFill("solid", fgColor="FFD8D8D8")
FINA = Side(style="thin")
CAIXA = Border(left=FINA, right=FINA, top=FINA, bottom=FINA)

# Dados pessoais e valores de exemplar plantados na planilha sintética.
NOME = "Fulano Sintético de Tal"
CPF = "123.456.789-09"
EMAIL = "fulano.sintetico@example.com"
TELEFONE = "(62) 9 9876-5432"
CREA = "1234567890/D-GO"
TITULO_SISTEMA = "Sistema Sintético Alfa"
LOCAL = "Apartamento 1404 do Sr. Beltrano"
OBSERVACAO = f"Morador {NOME}, CPF {CPF}, contato {EMAIL}."
PLANTADOS = (NOME, CPF, EMAIL, TELEFONE, CREA, "1234567890", TITULO_SISTEMA, LOCAL, "Beltrano", "Endógena", "Operação")

ROTULOS_FIXOS = {
    "SITUAÇÃO",
    "PRIORIDADE",
    "GRAVIDADE",
    "URGÊNCIA",
    "TENDÊNCIA",
    "PONTUAÇÃO",
    "CLASSIFICAÇÃO",
    "GRAU DE RISCO",
    "SISTEMA",
    "OBSERVAÇÕES TÉCNICAS",
    "SUBSISTEMA",
    "LOCALIZAÇÃO",
}


def _celula(ws, ref: str, valor=None, *, negrito=False, rotulo=False, corpo=11, borda=True, h="center", v="center"):
    celula = ws[ref]
    celula.value = valor
    celula.font = Font(name="Calibri", size=corpo, bold=negrito or rotulo)
    if rotulo:
        celula.fill = CINZA
    if borda:
        celula.border = CAIXA
    celula.alignment = Alignment(horizontal=h, vertical=v, wrap_text=True)


def _ficha(ws, r: int, numero: int, classificacao: str, tipo: str) -> None:
    """Uma ficha de 24 linhas com a mesma grade do original."""
    legenda = f"Foto nº {numero:02d}"
    ws.merge_cells(f"D{r}:I{r}")
    _celula(ws, f"D{r}", legenda, negrito=True, corpo=12)
    ws.merge_cells(f"D{r + 1}:G{r + 15}")
    _celula(ws, f"D{r + 1}")
    campos = [  # (rótulo, linha do rótulo, linha do valor, coluna do rótulo, coluna do valor, valor)
        ("SITUAÇÃO", 1, 2, "H", "H", "Não Conforme" if numero % 2 else "Conforme"),
        ("GRAVIDADE", 4, 4, "H", "I", numero + 1),
        ("URGÊNCIA", 5, 5, "H", "I", 2),
        ("TENDÊNCIA", 6, 6, "H", "I", 3),
        ("PONTUAÇÃO", 7, 8, "H", "H", 6 * (numero + 1)),
        ("CLASSIFICAÇÃO", 9, 10, "H", "H", classificacao),
        (f"TIPO DE {classificacao.upper()}", 11, 12, "H", "H", tipo),
        ("GRAU DE RISCO", 14, 15, "H", "H", "Mínimo" if numero % 2 else "Crítico"),
        ("SISTEMA", 16, 17, "D", "D", f"Chave_{numero}"),
        ("OBSERVAÇÕES TÉCNICAS", 16, 18, "F", "F", OBSERVACAO),
        ("SUBSISTEMA", 19, 20, "D", "D", f"Subsistema {numero}"),
        ("LOCALIZAÇÃO", 21, 22, "D", "D", LOCAL),
    ]
    _celula(ws, f"H{r + 3}", "PRIORIDADE", rotulo=True)
    ws.merge_cells(f"H{r + 3}:I{r + 3}")
    for rotulo, linha_rotulo, linha_valor, coluna_rotulo, coluna_valor, valor in campos:
        mesma_linha = linha_rotulo == linha_valor
        _celula(ws, f"{coluna_rotulo}{r + linha_rotulo}", rotulo, rotulo=not mesma_linha, corpo=10 if mesma_linha else 11)
        _celula(ws, f"{coluna_valor}{r + linha_valor}", valor, corpo=10 if coluna_valor == "F" else 11)
        # Coluna auxiliar oculta usada pelo PROCV da aba de resumo.
        ws[f"B{r + linha_valor}"] = f"{rotulo} {legenda}"
    for intervalo in (
        f"H{r + 1}:I{r + 1}", f"H{r + 2}:I{r + 2}", f"H{r + 7}:I{r + 7}", f"H{r + 8}:I{r + 8}",
        f"H{r + 9}:I{r + 9}", f"H{r + 10}:I{r + 10}", f"H{r + 11}:I{r + 11}", f"H{r + 12}:I{r + 13}",
        f"H{r + 14}:I{r + 14}", f"H{r + 15}:I{r + 15}", f"D{r + 16}:E{r + 16}", f"F{r + 16}:I{r + 16}",
        f"D{r + 17}:E{r + 18}", f"F{r + 18}:I{r + 22}", f"D{r + 19}:E{r + 19}", f"D{r + 20}:E{r + 20}",
        f"D{r + 21}:E{r + 21}", f"D{r + 22}:E{r + 22}",
    ):
        ws.merge_cells(intervalo)
    ws.row_dimensions[r + 11].height = 24
    for deslocamento in range(24):
        if deslocamento != 11:
            ws.row_dimensions[r + deslocamento].height = 14.25
    imagem = io.BytesIO()
    Image.new("RGB", (40, 20), "gray").save(imagem, "PNG")
    imagem.seek(0)
    foto = ImagemXlsx(imagem)
    foto.width, foto.height = 535, 283  # px a 96 dpi ≈ 14,16 x 7,49 cm
    ws.add_image(foto, f"D{r + 1}")


def _planilha_sintetica(destino: Path) -> Path:
    wb = openpyxl.Workbook()
    wb.active.title = "GABARITO"
    wb["GABARITO"]["B4"] = "Lista auxiliar"
    ws = wb.create_sheet("Rel. Fotográfico")
    for coluna, largura in {"A": 2, "B": 14.66, "C": 8.1, "D": 33.66, "E": 3.66, "F": 45, "G": 8, "H": 16.66, "I": 5.44, "J": 3.11}.items():
        ws.column_dimensions[coluna].width = largura
    for coluna in ("B", "C", "G"):
        ws.column_dimensions[coluna].hidden = True
    ws.merge_cells("C1:J1")
    ws["C1"] = f"7.1. {TITULO_SISTEMA}"
    ws["C1"].font = Font(name="Cambria", size=11, bold=True)
    ws["C1"].alignment = Alignment(horizontal="left", wrap_text=True)
    ws.row_dimensions[1].height = 14.25
    ws.row_dimensions[2].height = 6
    _ficha(ws, 3, 1, "Anomalia", "Endógena")
    _ficha(ws, 27, 2, "Falha", "Operação")
    _ficha(ws, 51, 3, "Anomalia", "Endógena")
    _ficha(ws, 75, 4, "Falha", "Operação")
    ws.row_breaks.append(Break(id=49))
    ws.row_breaks.append(Break(id=97))
    ws.page_margins = PageMargins(left=0.2362, right=0.2362, top=0.9843, bottom=0.7874, header=0, footer=0)
    ws.page_setup.paperSize = 9
    ws.page_setup.orientation = "portrait"
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
    ws.oddFooter.center.text = (
        f'&"-,Negrito"{NOME}&"-,Normal"\nEng. Civil - CREA-GO nº {CREA}\n'
        f'&"-,Negrito"&K04+000{EMAIL}&"-,Normal"&K000000 / {TELEFONE}'
    )
    ws.oddFooter.right.text = "&P"

    resumo = wb.create_sheet("Relatório")
    for indice, rotulo in enumerate(("Imagem", "Gravidade", "Urgência", "Tendência", "Pontuação", "Classificação", "Tipo", "Sistema"), start=1):
        celula = resumo.cell(row=1, column=indice, value=rotulo)
        celula.font = Font(name="Times New Roman", size=14, bold=True, color="FFFFFFFF")
        celula.fill = PatternFill("solid", fgColor="FF17365D")
        resumo.cell(row=2, column=indice, value="Foto nº 01" if indice == 1 else f"=VLOOKUP(\"x\",'Rel. Fotográfico'!$B:$J,{indice},0)")
    resumo.page_margins = PageMargins(left=0.5118, right=0.5118, top=0.7874, bottom=0.7874)
    wb.save(destino)
    return destino


@pytest.fixture
def planilha(tmp_path: Path) -> Path:
    return _planilha_sintetica(tmp_path / "rfip_sintetico.xlsx")


@pytest.fixture
def layout(planilha: Path) -> dict:
    return extrair_layout(planilha)


# ------------------------------------------------------------------- extração


def test_extrator_le_em_read_only_sem_tocar_nas_imagens(planilha: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    chamadas: list[dict] = []
    original_load = openpyxl.load_workbook

    def espiao_load(*args, **kwargs):
        chamadas.append(kwargs)
        return original_load(*args, **kwargs)

    membros_lidos: list[str] = []
    original_open = zipfile.ZipFile.open

    def espiao_open(self, nome, *args, **kwargs):
        membros_lidos.append(nome if isinstance(nome, str) else nome.filename)
        return original_open(self, nome, *args, **kwargs)

    monkeypatch.setattr(rfip_layout_extractor.openpyxl, "load_workbook", espiao_load)
    monkeypatch.setattr(zipfile.ZipFile, "open", espiao_open)
    extrair_layout(planilha)

    assert chamadas, "o extrator deveria abrir a planilha com openpyxl"
    assert all(kwargs.get("read_only") is True for kwargs in chamadas)
    assert any(nome.startswith("xl/drawings/") for nome in membros_lidos), "âncoras das fotos vêm do XML do desenho"
    assert not [nome for nome in membros_lidos if nome.startswith("xl/media/")], "nenhuma imagem pode ser extraída"


def test_mede_pagina_margens_e_grade(layout: dict) -> None:
    assert layout["tipo_documento"] == "RFIP"
    pagina = layout["pagina"]
    assert (pagina["tamanho"], pagina["orientacao"]) == ("A4", "portrait")
    assert pagina["margens_cm"]["esquerda"] == pytest.approx(0.6, abs=0.01)
    assert pagina["margens_cm"]["superior"] == pytest.approx(2.5, abs=0.01)
    assert pagina["margens_cm"]["inferior"] == pytest.approx(2.0, abs=0.01)
    assert pagina["ajustar_largura_a_pagina"] is True
    grade = layout["grade"]
    assert grade["colunas_ocultas"] == ["B", "C", "G"]
    assert [c["coluna"] for c in grade["colunas"]] == ["A", "D", "E", "F", "H", "I", "J"]
    assert 0 < grade["escala_impressao"] <= 1
    largura_impressa = sum(c["largura_cm"] for c in grade["colunas"])
    assert largura_impressa == pytest.approx(grade["largura_util_cm"], abs=0.05)


def test_mede_a_ficha_fotografica(layout: dict) -> None:
    ficha = layout["ficha"]
    assert ficha["linhas_por_ficha"] == 24
    assert ficha["fichas_por_pagina"] == 2
    assert ficha["legenda"] == {"prefixo": "Foto nº", "digitos": 2}
    assert ficha["alturas_pt"][11] == 24.0
    assert ficha["foto"]["largura_cm"] == pytest.approx(14.16, abs=0.05)
    assert ficha["foto"]["altura_cm"] == pytest.approx(7.49, abs=0.05)
    papeis = {c["papel"] for c in ficha["celulas"]}
    assert {"titulo_foto", "foto", "rotulo", "valor"} <= papeis
    foto = next(c for c in ficha["celulas"] if c["papel"] == "foto")
    assert (foto["linha"], foto["coluna"], foto["linhas"], foto["colunas"]) == (1, "D", 15, 3)
    assert layout["titulo_sistema"]["numeracao"]["capitulo"] == 7
    assert layout["titulo_sistema"]["estilo"]["fonte"] == "Cambria"


def test_separa_rotulos_fixos_de_valores_preenchidos(layout: dict) -> None:
    celulas = layout["ficha"]["celulas"]
    rotulos = {c["texto"] for c in celulas if c["papel"] == "rotulo"}
    assert ROTULOS_FIXOS <= rotulos
    tipo = next(c for c in celulas if c.get("sufixo_campo"))
    assert (tipo["texto"], tipo["sufixo_campo"]) == ("TIPO DE", "classificacao")
    valores = {c["campo"]: (c["linha"], c["coluna"]) for c in celulas if c["papel"] == "valor"}
    assert valores["situacao"] == (2, "H")
    assert valores["gravidade"] == (4, "I")
    assert valores["observacoes_tecnicas"] == (18, "F")
    assert valores["localizacao"] == (22, "D")
    assert all("texto" not in c for c in celulas if c["papel"] in ("valor", "descartado", "foto"))


def test_rodape_vira_placeholders(layout: dict) -> None:
    centro = layout["rodape"]["secoes"]["centro"]
    assert [linha["papel"] for linha in centro] == ["nome", "registro", "contato"]
    contato = centro[2]["trechos"]
    assert contato[0]["placeholder"] == "{{ responsavel.email }}"
    assert contato[0]["negrito"] is True and contato[0]["cor"] == "#4F81BD"
    assert contato[1]["placeholder"] == " / {{ responsavel.telefone }}"
    assert layout["rodape"]["secoes"]["direita"][0]["papel"] == "numero_pagina"


def test_layout_json_nao_contem_dado_pessoal(layout: dict, tmp_path: Path) -> None:
    destino = tmp_path / "layout.json"
    gravar_layout(layout, destino)
    serializado = destino.read_text(encoding="utf-8")
    for valor in PLANTADOS:
        assert valor not in serializado, "valor do exemplar vazou para o layout.json"
    assert "rfip_sintetico" not in serializado, "o nome do arquivo original identifica a obra (DEC-35)"
    assert not re.search(r"[\w.+-]+@[\w-]+\.\w+", serializado)
    assert "extraido_em" not in serializado and "gerado_em" not in serializado
    assert len(layout["origem"]["sha256"]) == 64


def test_verificador_falha_fechado_se_sobrar_dado_pessoal(layout: dict) -> None:
    layout["ficha"]["celulas"][0]["texto"] = f"contato {EMAIL}"
    with pytest.raises(LayoutExtractionError, match="Dado pessoal") as erro:
        garantir_sem_dados_pessoais(layout)
    assert EMAIL not in str(erro.value), "a mensagem de erro não pode ecoar o dado"


def test_extracao_e_deterministica(planilha: Path) -> None:
    assert json.dumps(extrair_layout(planilha), sort_keys=True) == json.dumps(extrair_layout(planilha), sort_keys=True)


def test_original_ausente_ou_invalido_falha_explicitamente(tmp_path: Path) -> None:
    with pytest.raises(LayoutExtractionError, match="não encontrado"):
        extrair_layout(tmp_path / "inexistente.xlsx")
    corrompido = tmp_path / "corrompido.xlsx"
    corrompido.write_bytes(b"isto nao e um zip")
    with pytest.raises(LayoutExtractionError, match="não é um pacote"):
        extrair_layout(corrompido)


def test_planilha_sem_fichas_falha(tmp_path: Path) -> None:
    wb = openpyxl.Workbook()
    wb.active["A1"] = "sem fichas"
    wb.save(tmp_path / "vazia.xlsx")
    with pytest.raises(LayoutExtractionError, match="Foto"):
        extrair_layout(tmp_path / "vazia.xlsx")


# -------------------------------------------------------------------- templates


def _contexto() -> dict:
    return {
        "sistemas": [
            {
                "nome": "Revestimentos",
                "ocorrencias": [
                    {
                        "seq_numero": 7, "situacao": "Não Conforme", "gut_gravidade": 3, "gut_urgencia": 2,
                        "gut_tendencia": 1, "pontuacao_gut": 6, "classificacao": "Anomalia", "tipo_anomalia": "Endógena",
                        "tipo_falha": None, "grau_risco": "Médio", "subsistema": "Fachada", "localizacao": "Bloco A",
                        "descricao": "Fissura", "foto_data_uri": "", "foto_docx": "",
                    },
                    {
                        "seq_numero": 8, "situacao": "Conforme", "gut_gravidade": None, "gut_urgencia": None,
                        "gut_tendencia": None, "pontuacao_gut": None, "classificacao": "Falha", "tipo_anomalia": None,
                        "tipo_falha": "Operação", "grau_risco": None, "subsistema": None, "localizacao": None,
                        "descricao": "", "foto_data_uri": "", "foto_docx": "",
                    },
                ],
            }
        ],
        "responsavel": {"nome": "Responsável Teste", "titulo_profissional": "Eng. Civil", "crea": "X", "email": "r@t.dev", "telefone": "0"},
        "logo_data_uri": "",
        "incluir_resumo": True,
    }


def _textos_da_primeira_ficha_docx(caminho: Path) -> list[str]:
    from docx import Document

    tabela = Document(str(caminho)).tables[0]
    textos: list[str] = []
    elementos: list = []  # mantém os proxies vivos para a comparação por identidade
    for linha in tabela.rows:
        for celula in linha.cells:
            if any(celula._tc is visto for visto in elementos):
                continue  # célula mesclada aparece repetida em `row.cells`
            elementos.append(celula._tc)
            if celula.text and celula.text != "{{ ocorrencia.foto_docx }}":
                textos.append(celula.text)
    return textos


def test_html_e_docx_derivam_do_mesmo_layout(layout: dict, tmp_path: Path) -> None:
    html, docx = gerar_templates(layout, tmp_path)
    conteudo_html = html.read_text(encoding="utf-8")
    conteudos = [c["conteudo"] for c in especificacao_ficha(layout) if c["conteudo"]]
    textos_docx = _textos_da_primeira_ficha_docx(docx)
    assert textos_docx == conteudos, "DOCX e especificação da ficha divergem"
    for conteudo in conteudos:
        assert conteudo in conteudo_html, "HTML e especificação da ficha divergem"

    from docx import Document

    secao = Document(str(docx)).sections[0]
    margens = layout["pagina"]["margens_cm"]
    assert secao.left_margin.cm == pytest.approx(margens["esquerda"], abs=0.01)
    assert secao.top_margin.cm == pytest.approx(margens["superior"], abs=0.01)
    assert secao.page_width.cm == pytest.approx(21.0, abs=0.01)
    assert f"margin: {margens['superior']}cm {margens['direita']}cm {margens['inferior']}cm {margens['esquerda']}cm" in conteudo_html

    # Mudar o layout.json muda os dois formatos — nenhum deles tem medida própria.
    rotulo = next(c for c in layout["ficha"]["celulas"] if c.get("texto") == "SITUAÇÃO")
    rotulo["texto"] = "SITUAÇÃO ALTERADA"
    layout["pagina"]["margens_cm"]["esquerda"] = 1.23
    html2, docx2 = gerar_templates(layout, tmp_path / "alterado")
    assert "SITUAÇÃO ALTERADA" in html2.read_text(encoding="utf-8")
    assert "SITUAÇÃO ALTERADA" in _textos_da_primeira_ficha_docx(docx2)
    assert "1.23cm;" in html2.read_text(encoding="utf-8")
    assert Document(str(docx2)).sections[0].left_margin.cm == pytest.approx(1.23, abs=0.01)


class _CelulasDaFicha(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.estilos: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        atributos = dict(attrs)
        if tag == "td" and "data-papel" in atributos:
            self.estilos.append(atributos.get("style") or "")


def test_template_j2_compila_e_renderiza(layout: dict) -> None:
    ambiente = jinja2.Environment(autoescape=True)
    template = ambiente.from_string(gerar_html(layout))
    saida = template.render(**_contexto())
    leitor = _CelulasDaFicha()
    leitor.feed(saida)
    assert leitor.estilos, "nenhuma célula de ficha no HTML"
    assert all("font-size" in estilo and "vertical-align" in estilo for estilo in leitor.estilos), (
        "atributo style inline truncado (aspas mal escapadas)"
    )
    assert saida.count('class="ficha"') == 2
    assert "Foto nº 07" in saida and "Foto nº 08" in saida
    assert "TIPO DE ANOMALIA" in saida and "TIPO DE FALHA" in saida
    assert "7.1. Revestimentos" in saida
    assert "Responsável Teste" in saida and "r@t.dev" in saida
    assert "—" in saida, "campo vazio sai como travessão (DEC-33)"


def test_docx_abre_e_renderiza_com_docxtpl(layout: dict, tmp_path: Path) -> None:
    from docx import Document
    from docxtpl import DocxTemplate

    destino = tmp_path / "rfip_template.docx"
    gerar_docx(layout, destino)
    modelo = DocxTemplate(str(destino))
    assert modelo.get_undeclared_template_variables() <= {"sistemas", "responsavel", "incluir_resumo"}
    modelo.render(_contexto())
    renderizado = tmp_path / "renderizado.docx"
    modelo.save(str(renderizado))

    documento = Document(str(renderizado))
    texto = "\n".join(c.text for t in documento.tables for linha in t.rows for c in linha.cells)
    assert "Foto nº 07" in texto and "Foto nº 08" in texto
    assert "TIPO DE ANOMALIA" in texto and "TIPO DE FALHA" in texto
    assert "{{" not in texto and "{%" not in texto
    rodape = "\n".join(p.text for t in documento.sections[0].footer.tables for linha in t.rows for c in linha.cells for p in c.paragraphs)
    assert "Responsável Teste" in rodape and "r@t.dev / 0" in rodape


def test_logo_do_cabecalho_cabe_na_margem_superior(layout: dict) -> None:
    layout["cabecalho"]["secoes"]["direita"] = [{"papel": "imagem", "trechos": [], "imagem": {"largura_cm": 5.63, "altura_cm": 2.82}}]
    largura, altura = tamanho_logo_cm(layout)
    assert altura <= layout["pagina"]["margens_cm"]["superior"]
    assert largura / altura == pytest.approx(5.63 / 2.82, rel=0.01)


def test_artefatos_versionados_estao_em_dia_com_o_layout(tmp_path: Path) -> None:
    """O .j2 e o .docx versionados são exatamente o que o layout.json versionado gera."""
    layout = json.loads(LAYOUT_JSON.read_text(encoding="utf-8"))
    assert layout["versao_schema"] == 1 and layout["tipo_documento"] == "RFIP"
    garantir_sem_dados_pessoais(layout)
    assert "arquivo" not in layout["origem"]
    assert HTML_TEMPLATE.read_text(encoding="utf-8") == gerar_html(layout)
    destino = tmp_path / "regerado.docx"
    gerar_docx(layout, destino)
    with zipfile.ZipFile(DOCX_TEMPLATE) as versionado, zipfile.ZipFile(destino) as gerado:
        for parte in ("word/document.xml", "word/footer1.xml"):
            if parte in versionado.namelist():
                assert gerado.read(parte) == versionado.read(parte), f"{parte} desatualizado: rode o build"
