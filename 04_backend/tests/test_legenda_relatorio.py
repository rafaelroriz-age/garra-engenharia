"""Seleção da legenda impressa no relatório (BL-38, DEC-37 DP-9; proposta ainda não aprovada pelo dono)."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

# Carregado por caminho: o __init__ do pacote importa o WeasyPrint (indisponível
# no Windows local), e o helper é puro e não depende dele.
_caminho = Path(__file__).resolve().parents[1] / "app" / "services" / "report_generator" / "legenda_foto.py"
_spec = importlib.util.spec_from_file_location("legenda_foto", _caminho)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
foto_ia_em_rascunho = _mod.foto_ia_em_rascunho
legenda_para_relatorio = _mod.legenda_para_relatorio
sinalizar_fotos_ia_em_rascunho = _mod.sinalizar_fotos_ia_em_rascunho


def _foto(legenda=None, ia=None, status=None):
    return SimpleNamespace(legenda=legenda, legenda_ia_sugerida=ia, status_validacao_ia=status)


def test_status_null_usa_legenda():
    assert legenda_para_relatorio(_foto("Trinca na parede", status=None)) == "Trinca na parede"


def test_status_null_ignora_sugestao_ia():
    assert legenda_para_relatorio(_foto("Manual", ia="Sugestão IA")) == "Manual"


def test_aprovada_usa_legenda():
    assert legenda_para_relatorio(_foto("Aprovada", ia="Sugestão IA", status="aprovada")) == "Aprovada"


def test_rascunho_com_legenda_usa_legenda_anterior_nunca_ia():
    assert legenda_para_relatorio(_foto("Anterior", ia="Sugestão IA", status="rascunho")) == "Anterior"


def test_rascunho_sem_legenda_fica_vazio_nunca_ia():
    assert legenda_para_relatorio(_foto(None, ia="Sugestão IA", status="rascunho")) == ""
    assert legenda_para_relatorio(_foto("", ia="Sugestão IA", status="rascunho")) == ""


def test_legenda_vazia_ou_so_espacos():
    assert legenda_para_relatorio(_foto("   ")) == ""
    assert legenda_para_relatorio(_foto(None)) == ""


def test_aceita_dict_do_contexto():
    foto = {"legenda": "X", "legenda_ia_sugerida": "IA", "status_validacao_ia": "rascunho"}
    assert legenda_para_relatorio(foto) == "X"
    assert legenda_para_relatorio({"storage_key": "k"}) == ""


def test_sinalizacao_de_rascunho():
    assert foto_ia_em_rascunho(_foto(status="rascunho")) is True
    assert foto_ia_em_rascunho(_foto(status="aprovada")) is False
    assert foto_ia_em_rascunho(_foto(status=None)) is False
    fotos = [_foto(status="rascunho"), _foto(status="aprovada"), {"status_validacao_ia": "rascunho"}]
    assert sinalizar_fotos_ia_em_rascunho(fotos) == [0, 2]
