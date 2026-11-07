"""Testes do extrator de layout do RFO e dos geradores de template (BL-12/BL-13).

Não dependem do original do cliente (`01_output-context/`, fora do Git): a
planilha de referência é construída em memória com a mesma estrutura observada
no original — cabeçalho de marca, seções sombreadas, rótulos em negrito, grade
fotográfica e bloco de assinaturas.

Também não importam `weasyprint`, que só carrega dentro do container Docker
(dependências GTK ausentes no Windows).
"""

from __future__ import annotations

import json
from pathlib import Path

import openpyxl
import pytest
from jinja2 import DictLoader, Environment, select_autoescape
from openpyxl.styles import Alignment, Font, PatternFill

from app.scripts.build_rfo_templates import gerar_docx, gerar_html
from app.scripts.rfo_layout_extractor import LayoutExtractionError, extrair_layout

CINZA_SECAO = "FFD9D9D9"


def _cabecalho_secao(ws, celula: str, titulo: str) -> None:
    ws[celula] = titulo
    ws[celula].font = Font(name="Arial", size=10, bold=True)
    ws[celula].fill = PatternFill(fill_type="solid", start_color=CINZA_SECAO, end_color=CINZA_SECAO)


def _rotulo(ws, celula_rotulo: str, texto: str, celula_valor: str | None = None, valor: str | None = None) -> None:
    ws[celula_rotulo] = texto
    ws[celula_rotulo].font = Font(name="Arial", size=10, bold=True)
    if celula_valor is not None:
        ws[celula_valor] = valor
        ws[celula_valor].font = Font(name="Arial", size=10, bold=False)


@pytest.fixture(scope="module")
def planilha_rfo(tmp_path_factory) -> Path:
    """Planilha sintética com a mesma estrutura do RFO original."""
    workbook = openpyxl.Workbook()

    capa = workbook.active
    capa.title = "Informações Gerais"
    capa["F1"] = "Relatório de Fiscalização"
    capa["F1"].font = Font(name="Arial", size=48)
    capa["K5"] = "Rua Coronel José Augusto Perilo Qd. 47 - Aparecida de Goiânia/GO. CEP: 74954-102"
    capa["K5"].font = Font(name="Arial", size=10)
    _cabecalho_secao(capa, "B9", "INFORMAÇÕES DA EDIFICAÇÃO")
    _rotulo(capa, "B10", "Local:", "C10", "Residencial Exemplo")
    _rotulo(capa, "B11", "Endereço:", "C11", "Rua Exemplo, 100")
    _cabecalho_secao(capa, "B13", "INFORMAÇÕES TÉCNICAS DA FISCALIZAÇÃO")
    _rotulo(capa, "B14", "Contrato:", "C14", "008/2021")
    capa.print_area = "'Informações Gerais'!$A$1:$W$87"

    visita = workbook.create_sheet("Dia 01")
    visita["H1"] = "Relatório de Fiscalização"
    visita["H1"].font = Font(name="Arial", size=48)
    visita["N5"] = "Rua Coronel José Augusto Perilo Qd. 47 - contato@construtoragarra.com"
    visita["N5"].font = Font(name="Arial", size=10)
    visita["H7"] = "Empresa: Construtora do Exemplar"
    visita["H7"].font = Font(name="Arial", size=22, bold=True)
    _cabecalho_secao(visita, "B9", "RELATÓRIO DIÁRIO DE FISCALIZAÇÃO")
    _rotulo(visita, "R10", "Data:", "S10", "2022-06-14")
    _rotulo(visita, "B11", "Obra:", "C11", "Impermeabilização de lajes")
    _rotulo(visita, "I10", "Status:")  # campo sem valor preenchido no exemplar
    _cabecalho_secao(visita, "B16", "ATIVIDADES CONSTATADAS NO DIA DA VISITA")
    _cabecalho_secao(visita, "B23", "EQUIPE EFETIVA EM OBRA")
    _cabecalho_secao(visita, "B34", "REGISTRO FOTOGRÁFICO")
    for indice, (linha, colunas) in enumerate(((36, ("B", "L")), (54, ("B", "L")), (94, ("B", "L")))):
        for deslocamento, coluna in enumerate(colunas):
            visita[f"{coluna}{linha}"] = f"Foto {indice * 2 + deslocamento + 1:02d}"
            visita[f"{coluna}{linha}"].font = Font(name="Arial", size=10, bold=True)
    for celula, rotulo in (("W63", "RESPONSÁVEL TÉCNICO"), ("W72", "CONTRATADA"), ("W121", "RESPONSÁVEL TÉCNICO")):
        visita[celula] = f"\n________________________\n{rotulo}"
        visita[celula].font = Font(name="Arial", size=10)
        visita[celula].alignment = Alignment(horizontal="center")
    visita.print_area = "'Dia 01'!$A$1:$AC$90"
    visita.page_margins.left = 0.59
    visita.page_margins.right = 0.24
    visita.page_margins.top = 0.75
    visita.page_margins.bottom = 0.75

    destino = tmp_path_factory.mktemp("originais") / "RFO sintetico.xlsx"
    workbook.save(destino)
    return destino


@pytest.fixture(scope="module")
def layout(planilha_rfo: Path) -> dict:
    return extrair_layout(planilha_rfo)


def test_extrator_falha_explicitamente_sem_o_original(tmp_path: Path) -> None:
    with pytest.raises(LayoutExtractionError, match="não encontrado"):
        extrair_layout(tmp_path / "inexistente.xlsx")


def test_extrai_pagina_tipografia_e_cores(layout: dict) -> None:
    assert layout["tipo_documento"] == "RFO"
    assert layout["pagina"]["tamanho"] == "A4"
    assert layout["pagina"]["margens_cm"]["esquerda"] == pytest.approx(1.5, abs=0.05)
    assert layout["tipografia"] == {"familia": "Arial", "corpo_pt": 10.0, "titulo_pt": 48.0}
    assert layout["cores"]["cabecalho_secao_fundo"] == "#D9D9D9"


def test_extrai_secoes_e_rotulos_da_capa_e_da_visita(layout: dict) -> None:
    titulos_capa = [secao["titulo"] for secao in layout["capa"]["secoes"]]
    assert titulos_capa == ["INFORMAÇÕES DA EDIFICAÇÃO", "INFORMAÇÕES TÉCNICAS DA FISCALIZAÇÃO"]

    campos = {campo["rotulo"]: campo["celula_valor"] for campo in layout["capa"]["secoes"][0]["campos"]}
    assert campos == {"Local:": "C10", "Endereço:": "C11"}

    titulos_visita = [secao["titulo"] for secao in layout["visita"]["secoes"]]
    assert titulos_visita == [
        "RELATÓRIO DIÁRIO DE FISCALIZAÇÃO",
        "ATIVIDADES CONSTATADAS NO DIA DA VISITA",
        "EQUIPE EFETIVA EM OBRA",
        "REGISTRO FOTOGRÁFICO",
    ]


def test_rotulo_sem_valor_preenchido_nao_toma_a_celula_do_campo_seguinte(layout: dict) -> None:
    campos = {campo["rotulo"]: campo["celula_valor"] for campo in layout["visita"]["secoes"][0]["campos"]}
    assert campos["Status:"] is None
    assert campos["Data:"] == "S10"


def test_extrai_grade_fotografica_e_assinaturas(layout: dict) -> None:
    grade = layout["visita"]["registro_fotografico"]
    assert grade["encontrado"] is True
    assert grade["fotos_por_linha"] == 2
    assert grade["colunas_inicio"] == ["B", "L"]
    assert grade["linhas_por_foto"] == 18
    # O bloco de assinaturas se repete a cada página do modelo — não pode duplicar.
    assert layout["visita"]["assinaturas"] == ["RESPONSÁVEL TÉCNICO", "CONTRATADA"]


def test_layout_nao_persiste_dados_preenchidos_pelo_cliente(layout: dict) -> None:
    serializado = json.dumps(layout, ensure_ascii=False)
    assert "Residencial Exemplo" not in serializado
    assert "008/2021" not in serializado
    assert "Construtora do Exemplar" not in serializado
    # Endereço/contato do emitente é dado fixo da marca e permanece no cabeçalho.
    assert any("construtoragarra.com" in linha for linha in layout["cabecalho"]["linhas_texto"])


def _contexto_minimo() -> dict:
    return {
        "contrato": {
            "numero": "001/2026",
            "objeto": "Impermeabilização",
            "art_fiscalizacao": "ART-123",
            "data_inicio": "2026-01-05",
            "prazo_dias": 50,
        },
        "edificacao": {"nome": "Ed. Teste", "endereco": "Rua A, 1", "tipologia": "residencial"},
        "fiscal": {"nome": "Eng. Fulano", "crea": "123D-GO", "email": "eng@example.com"},
        "executores": [{"razao_social": "Executora X", "cnpj": "00.000.000/0001-00", "art_execucao": "ART-999"}],
        "nbrs": [{"codigo_nbr": "NBR 9575", "descricao": "Impermeabilização"}],
        "visitas": [
            {
                "seq_numero": 1,
                "data": "2026-01-06",
                "servicos_executados_lista": ["Escarificação da platibanda"],
                "observacoes": "Sem placa de obra.",
                "observacoes_lista": ["Sem placa de obra."],
                "mao_obra": [{"funcao": "Pedreiro", "quantidade": 1}],
                "medicoes": [{"descricao": "Área", "quantidade": 120, "unidade": "m²"}],
                "fotos": [{"data_uri": "data:image/jpeg;base64,AAAA", "legenda": "Platibanda"}],
            }
        ],
        "logo_data_uri": None,
    }


def test_html_gerado_renderiza_e_reflete_o_layout_medido(layout: dict) -> None:
    fonte = gerar_html(layout)
    margens = layout["pagina"]["margens_cm"]
    esperado = (
        f"margin: {margens['superior']}cm {margens['direita']}cm "
        f"{margens['inferior']}cm {margens['esquerda']}cm"
    )
    assert esperado in fonte
    assert "background: #D9D9D9" in fonte
    assert "font-size: 10.0pt" in fonte

    env = Environment(loader=DictLoader({"rfo": fonte}), autoescape=select_autoescape(["html"]))
    html = env.get_template("rfo").render(**_contexto_minimo())
    assert "Ed. Teste" in html
    assert "Escarificação da platibanda" in html
    assert "NBR 9575" in html
    assert "Foto 01" in html
    assert "CONTRATADA" in html


def test_docx_gerado_e_um_template_docxtpl_valido(layout: dict, tmp_path: Path) -> None:
    from docxtpl import DocxTemplate

    destino = tmp_path / "rfo_template.docx"
    gerar_docx(layout, destino)
    assert destino.is_file()

    tpl = DocxTemplate(str(destino))
    variaveis = tpl.get_undeclared_template_variables()
    assert {"contrato", "edificacao", "fiscal", "visitas"} <= variaveis


def test_docx_gerado_renderiza_com_o_mesmo_contexto_do_html(layout: dict, tmp_path: Path) -> None:
    from docx import Document
    from docxtpl import DocxTemplate

    template = tmp_path / "rfo_template.docx"
    gerar_docx(layout, template)

    contexto = _contexto_minimo()
    contexto["visitas"][0]["servicos_executados"] = "Escarificação da platibanda"
    contexto["visitas"][0]["fotos_doc"] = ""

    tpl = DocxTemplate(str(template))
    tpl.render(contexto)
    renderizado = tmp_path / "rfo_render.docx"
    tpl.save(str(renderizado))

    texto = "\n".join(p.text for p in Document(str(renderizado)).paragraphs)
    assert "Ed. Teste" in texto
    assert "NBR 9575" in texto
    assert "Escarificação da platibanda" in texto


def test_templates_versionados_do_original_renderizam() -> None:
    """Os templates de `templates/rfo/` (derivados do original do cliente) devem
    renderizar mesmo em máquinas sem acesso a `01_output-context/`."""
    from docxtpl import DocxTemplate

    from app.scripts.build_rfo_templates import DOCX_TEMPLATE, HTML_TEMPLATE, LAYOUT_JSON

    assert LAYOUT_JSON.is_file(), "Rode `python -m app.scripts.build_rfo_templates --original <planilha>`."
    layout_versionado = json.loads(LAYOUT_JSON.read_text(encoding="utf-8"))
    assert layout_versionado["origem"]["arquivo"].lower().endswith((".xlsx", ".xlsm"))

    env = Environment(
        loader=DictLoader({"rfo": HTML_TEMPLATE.read_text(encoding="utf-8")}),
        autoescape=select_autoescape(["html"]),
    )
    html = env.get_template("rfo").render(**_contexto_minimo())
    assert "Relatório de Fiscalização" in html
    assert "Ed. Teste" in html

    assert {"contrato", "visitas"} <= DocxTemplate(str(DOCX_TEMPLATE)).get_undeclared_template_variables()
