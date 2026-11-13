"""Contexto técnico só texto da legenda IA (BL-34): minimização de dados e chave canônica."""
import uuid
from types import SimpleNamespace

import pytest

from app.services.legenda_ia.contexto import (
    ContextoLegenda,
    NbrContexto,
    limpar_dados_pessoais,
    montar_contexto,
)


@pytest.mark.parametrize(
    ("entrada", "marcador"),
    [
        ("CPF 123.456.789-09 do morador", "[CPF]"),
        ("cpf 12345678909", "[CPF]"),
        ("CNPJ 12.345.678/0001-95 da empresa", "[CNPJ]"),
        ("12345678000195", "[CNPJ]"),
        ("contato joao.silva+obra@empresa.com.br urgente", "[EMAIL]"),
        ("fone (61) 99876-5432", "[TELEFONE]"),
        ("fone +55 61 3322-1100", "[TELEFONE]"),
    ],
)
def test_limpeza_remove_cpf_cnpj_email_telefone(entrada, marcador):
    saida = limpar_dados_pessoais(entrada)
    assert marcador in saida
    for sensivel in ("123.456.789-09", "12345678909", "12.345.678/0001-95", "12345678000195",
                     "joao.silva", "99876-5432", "3322-1100"):
        assert sensivel not in saida


def test_limpeza_preserva_medidas_tecnicas():
    texto = "Fissura de 0,5 mm a 1250 mm do piso, 2 de 4 pilares, ABNT NBR 16747"
    assert limpar_dados_pessoais(texto) == texto


def test_limpeza_none_e_vazio():
    assert limpar_dados_pessoais(None) is None
    assert limpar_dados_pessoais("   ") is None


def test_canonico_e_estavel_e_independe_da_ordem_das_nbrs():
    a = ContextoLegenda(
        legenda_bruta="x", tipo_anomalia="Trinca", grau_risco="Alto",
        nbrs=(NbrContexto("NBR 16747", "Inspeção predial"), NbrContexto("NBR 5674")),
    )
    b = ContextoLegenda(
        grau_risco="Alto", tipo_anomalia="Trinca", legenda_bruta="x",
        nbrs=(NbrContexto("NBR 5674"), NbrContexto("NBR 16747", "Inspeção predial")),
    )
    assert a.canonico() == b.canonico() == a.canonico()
    assert a.canonico() != ContextoLegenda(legenda_bruta="y").canonico()
    assert a.canonico().startswith('{"ambiente":null')  # chaves ordenadas


class _Resultado:
    def __init__(self, itens):
        self._itens = itens

    def scalars(self):
        return self

    def all(self):
        return self._itens


class _Banco:
    """Banco falso: `get` por classe e `execute` devolvendo as NBRs."""

    def __init__(self, objetos, nbrs):
        self.objetos = objetos
        self.nbrs = nbrs

    async def get(self, modelo, chave):
        return self.objetos.get((modelo.__name__, chave))

    async def execute(self, _consulta):
        return _Resultado(self.nbrs)


async def test_montar_contexto_sem_dados_pessoais():
    ids = {n: uuid.uuid4() for n in ("oc", "insp", "sis", "sub", "contrato")}
    ocorrencia = SimpleNamespace(
        inspecao_id=ids["insp"], sistema_id=ids["sis"], subsistema_id=ids["sub"],
        tipo_anomalia="Fissura", grau_risco="Médio", localizacao="Bloco B, e-mail fulano@x.com",
        descricao="Morador CPF 123.456.789-09 relatou infiltração", gut_gravidade=3,
        gut_urgencia=4, gut_tendencia=5, nome_cliente="NAO DEVE APARECER",
    )
    objetos = {
        ("Ocorrencia", ids["oc"]): ocorrencia,
        ("Inspecao", ids["insp"]): SimpleNamespace(contrato_id=ids["contrato"], tipo="LTIP"),
        ("SistemaPredial", ids["sis"]): SimpleNamespace(nome="Cobertura"),
        ("Subsistema", ids["sub"]): SimpleNamespace(nome="Telhado"),
    }
    nbrs = [SimpleNamespace(codigo_nbr="NBR 16747", descricao="Inspeção predial")]
    foto = SimpleNamespace(
        ocorrencia_id=ids["oc"], visita_id=None, legenda_bruta="trinca, tel (61) 98888-7777"
    )

    ctx = await montar_contexto(_Banco(objetos, nbrs), foto)

    assert (ctx.tipo_anomalia, ctx.sistema, ctx.subsistema, ctx.grau_risco) == (
        "Fissura", "Cobertura", "Telhado", "Médio",
    )
    assert ctx.tipo_relatorio == "LTIP"
    assert ctx.nbrs == (NbrContexto("NBR 16747", "Inspeção predial"),)
    assert (ctx.gut_gravidade, ctx.gut_urgencia, ctx.gut_tendencia) == (3, 4, 5)
    texto = ctx.canonico() + ctx.bloco_dados()
    for proibido in ("123.456.789-09", "fulano@x.com", "98888-7777", "NAO DEVE"):
        assert proibido not in texto
    assert "[CPF]" in texto and "[EMAIL]" in texto and "[TELEFONE]" in texto
    for uid in ids.values():
        assert str(uid) not in texto


async def test_montar_contexto_substitui_legenda_bruta_e_aceita_foto_sem_ocorrencia():
    foto = SimpleNamespace(ocorrencia_id=None, visita_id=None, legenda_bruta="antiga")
    ctx = await montar_contexto(_Banco({}, []), foto, "nova")
    assert ctx == ContextoLegenda(legenda_bruta="nova")
    assert (await montar_contexto(_Banco({}, []), foto, None)).legenda_bruta is None
