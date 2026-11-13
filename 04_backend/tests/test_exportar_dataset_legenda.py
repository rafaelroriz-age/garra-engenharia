"""Export do dataset de feedback da legenda IA (BL-34, IA-06).

Usa o PostgreSQL de `05_infra`. Cada teste cria os próprios dados e os remove no fim; o export só lê.
"""
import json
import uuid
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.models import (
    ChamadaIA,
    Contrato,
    Edificacao,
    Foto,
    Inspecao,
    Ocorrencia,
    PromptIA,
    Responsavel,
    SistemaPredial,
    Usuario,
)
from app.scripts import exportar_dataset_legenda as exp

_engine = create_async_engine(get_settings().database_url, poolclass=NullPool, future=True)
_Session = async_sessionmaker(bind=_engine, expire_on_commit=False)
_HASH = "$2b$12$" + "a" * 53  # só precisa existir (bug passlib x bcrypt do ambiente)

CPF, EMAIL = "123.456.789-09", "maria.souza@cliente.com.br"


def test_distancia_de_edicao():
    d = exp.distancia_edicao_normalizada
    assert d("abc", "abc") == 0.0
    assert d("  abc  def ", "abc def") == 0.0  # espaço não é edição
    assert d("abc", "") == 1.0
    assert d("abc", "xyz") == 1.0
    assert d("kitten", "sitting") == pytest.approx(3 / 7)
    assert d("abcd", "abce") == pytest.approx(0.25)


def test_recusa_saida_dentro_do_repositorio():
    repo = Path(__file__).resolve().parents[2]
    assert (repo / ".git").exists()
    for destino in (repo / "dados", repo / "04_backend" / "x" / "y", Path(__file__).parent):
        with pytest.raises(exp.SaidaNoRepositorio):
            exp.validar_saida(destino)
    assert exp.main(["--saida", str(repo / "saida-proibida")]) == 2
    assert not (repo / "saida-proibida").exists()


def test_aceita_saida_fora_do_repositorio(tmp_path):
    assert exp.validar_saida(tmp_path / "ok") == (tmp_path / "ok").resolve()


@pytest_asyncio.fixture
async def cenario():
    tag = uuid.uuid4().hex[:10]
    async with _Session() as s:
        usuario = Usuario(nome="Auditor exp", email=f"exp-{tag}@garra.test", senha_hash=_HASH, ativo=True, role="auditor")
        edificacao = Edificacao(nome=f"Ed. exp {tag}", endereco="Rua E, 1")
        fiscal = Responsavel(nome="Fiscal exp", tipo="fiscal", crea="111111-GO")
        sistema = SistemaPredial(nome=f"Sistema exp {tag}", ordem=999)
        s.add_all([usuario, edificacao, fiscal, sistema])
        await s.flush()
        contrato = Contrato(
            edificacao_id=edificacao.id, fiscal_id=fiscal.id, numero=f"CT-EXP-{tag}",
            tipo_servico="Inspeção predial", status="em_andamento", art_fiscalizacao="ART-1",
        )
        s.add(contrato)
        await s.flush()
        inspecao = Inspecao(contrato_id=contrato.id, tipo="LTIP", status="em_andamento")
        s.add(inspecao)
        await s.flush()
        ocorrencia = Ocorrencia(
            inspecao_id=inspecao.id, sistema_id=sistema.id, situacao="Não conforme", classificacao="Anomalia",
            tipo_anomalia="Fissura", localizacao=f"Hall, contato {EMAIL}", descricao=f"Fissura vista; CPF {CPF}",
            seq_numero=1,
        )
        prompt = PromptIA(nome=f"teste-exp-{tag}", versao="v1", conteudo="Prompt de teste do export.")
        s.add_all([ocorrencia, prompt])
        await s.flush()

        def foto(legenda, sugerida, status, aprovado_em=None, **extra):
            return Foto(
                storage_key=f"fotos/{uuid.uuid4()}.png", origem="upload_manual", ocorrencia_id=ocorrencia.id,
                legenda=legenda, legenda_bruta=f"bruta {tag} {EMAIL}", legenda_ia_sugerida=sugerida,
                status_validacao_ia=status, prompt_ia_id=prompt.id, nivel_certeza_ia="indicio_tecnico",
                aprovado_por_id=usuario.id if status == "aprovada" else None, aprovado_em=aprovado_em, **extra,
            )

        sem_edicao = foto("Fissura no piso do hall.", "Fissura no piso do hall.", "aprovada",
                          datetime(2026, 3, 10, tzinfo=UTC))
        editada = foto(f"Fissura de 0,5 mm; CPF {CPF} do morador.", "Fissura abcd", "aprovada",
                       datetime(2026, 6, 20, tzinfo=UTC))
        rascunho = foto("Rascunho não aprovado.", "Sugestão em rascunho", "rascunho")
        sem_ia = Foto(storage_key=f"fotos/{uuid.uuid4()}.png", origem="upload_manual",
                      ocorrencia_id=ocorrencia.id, legenda="Foto sem IA.")
        fotos = [sem_edicao, editada, rascunho, sem_ia]
        s.add_all(fotos)
        await s.flush()
        s.add(ChamadaIA(foto_id=sem_edicao.id, provedor="deepseek", modelo="deepseek-chat", modo="texto",
                        prompt_ia_id=prompt.id, chave_cache="k" * 64, origem="api", sucesso=True))
        await s.commit()
        ids = {"usuario": usuario.id, "fotos": [f.id for f in fotos], "prompt": prompt.id, "tag": tag,
               "sistema_nome": sistema.nome}
        objetos = [ocorrencia, inspecao, contrato, fiscal, edificacao, sistema]
    yield ids
    async with _Session() as s:
        await s.execute(delete(ChamadaIA).where(ChamadaIA.foto_id.in_(ids["fotos"])))
        await s.execute(delete(Foto).where(Foto.id.in_(ids["fotos"])))
        await s.execute(delete(PromptIA).where(PromptIA.id == ids["prompt"]))
        await s.commit()
        for obj in objetos:
            await s.delete(await s.get(type(obj), obj.id))
            await s.commit()
        await s.execute(delete(Usuario).where(Usuario.id == ids["usuario"]))
        await s.commit()


def _meus(registros, cenario):
    ids = {str(i) for i in cenario["fotos"]}
    return [r for r in registros if r.foto_id in ids]


@pytest.mark.asyncio
async def test_so_aprovadas_formato_jsonl_metricas_e_sem_dados_pessoais(cenario, tmp_path):
    async with _Session() as s:
        registros, gravou = await exp.exportar(s, tmp_path)
    assert gravou
    meus = _meus(registros, cenario)
    # só as duas aprovadas com sugestão: rascunho e foto sem IA ficam de fora
    assert sorted(r.final[:8] for r in meus) == ["Fissura ", "Fissura "]
    assert {r.foto_id for r in meus} == {str(cenario["fotos"][0]), str(cenario["fotos"][1])}

    linhas = [json.loads(linha) for linha in (tmp_path / exp.ARQUIVO_JSONL).read_text("utf-8").splitlines()]
    assert len(linhas) == len(registros)
    minhas = [m for m in linhas if "Prompt de teste do export." in m["messages"][0]["content"]]
    assert len(minhas) == 2
    for m in minhas:
        sistema, usuario, assistente = m["messages"]
        assert [x["role"] for x in m["messages"]] == ["system", "user", "assistant"]
        assert sistema["content"].startswith("Prompt de teste do export.\n\nResponda somente com um objeto JSON")
        assert usuario["content"].startswith("DADOS DA OCORRÊNCIA")
        assert f"Sistema: {cenario['sistema_nome']}" in usuario["content"]
        saida = json.loads(assistente["content"])
        assert saida["status_validacao"] == "aprovada" and saida["nivel_certeza"] == "indicio_tecnico"
    finais = {json.loads(m["messages"][2]["content"])["legenda_sugerida"] for m in minhas}
    assert "Fissura no piso do hall." in finais
    assert "Fissura de 0,5 mm; CPF [CPF] do morador." in finais  # a final é a do auditor, já limpa

    # nenhum CPF/e-mail sobrevive em nenhum arquivo
    for arquivo in (exp.ARQUIVO_JSONL, exp.ARQUIVO_CSV):
        texto = (tmp_path / arquivo).read_text("utf-8")
        for sensivel in (CPF, "12345678909", EMAIL, "maria.souza"):
            assert sensivel not in texto
    assert "[CPF]" in (tmp_path / exp.ARQUIVO_JSONL).read_text("utf-8")
    assert "[EMAIL]" in (tmp_path / exp.ARQUIVO_JSONL).read_text("utf-8")


@pytest.mark.asyncio
async def test_metrica_de_edicao_e_csv(cenario, tmp_path):
    async with _Session() as s:
        registros, _ = await exp.exportar(s, tmp_path)
    por_id = {r.foto_id: r for r in _meus(registros, cenario)}
    aceita = por_id[str(cenario["fotos"][0])]
    editada = por_id[str(cenario["fotos"][1])]
    assert aceita.aceita_sem_edicao and aceita.distancia == 0.0
    assert not editada.aceita_sem_edicao and 0.0 < editada.distancia <= 1.0
    assert aceita.modelo == "deepseek-chat" and aceita.modo == "texto"
    assert editada.modelo is None  # sem chamada em `chamadas_ia`
    assert aceita.sistema == cenario["sistema_nome"] and aceita.tipo_anomalia == "Fissura"
    assert aceita.prompt_versao == "v1"

    import csv

    with (tmp_path / exp.ARQUIVO_CSV).open(encoding="utf-8", newline="") as f:
        linhas = {r["foto_id"]: r for r in csv.DictReader(f)}
    assert tuple(next(iter(linhas.values())).keys()) == exp.COLUNAS_CSV
    assert linhas[aceita.foto_id]["aceita_sem_edicao"] == "1"
    assert linhas[aceita.foto_id]["distancia_edicao"] == "0.0000"
    assert linhas[editada.foto_id]["aceita_sem_edicao"] == "0"
    assert linhas[aceita.foto_id]["nivel_certeza_ia"] == "indicio_tecnico"
    texto = exp.resumo(_meus(registros, cenario))
    assert "Registros: 2" in texto and "50.0%" in texto and cenario["sistema_nome"] in texto


@pytest.mark.asyncio
async def test_filtros_desde_ate_e_min_registros(cenario, tmp_path):
    async with _Session() as s:
        so_marco, _ = await exp.exportar(s, tmp_path / "a", date(2026, 3, 1), date(2026, 3, 10))
        so_junho, _ = await exp.exportar(s, tmp_path / "b", desde=date(2026, 4, 1))
        nenhum, gravou = await exp.exportar(s, tmp_path / "c", min_registros=10**6)
    assert [r.foto_id for r in _meus(so_marco, cenario)] == [str(cenario["fotos"][0])]  # `--ate` inclusivo
    assert str(cenario["fotos"][1]) in [r.foto_id for r in so_junho]
    assert str(cenario["fotos"][0]) not in [r.foto_id for r in so_junho]
    assert not gravou and not (tmp_path / "c").exists() and nenhum is not None


@pytest.mark.asyncio
async def test_nao_altera_o_banco(cenario, tmp_path):
    async with _Session() as s:
        antes = [(f.legenda, f.legenda_ia_sugerida, f.status_validacao_ia) for f in
                 [await s.get(Foto, i) for i in cenario["fotos"]]]
    async with _Session() as s:
        await exp.exportar(s, tmp_path)
    async with _Session() as s:
        depois = [(f.legenda, f.legenda_ia_sugerida, f.status_validacao_ia) for f in
                  [await s.get(Foto, i) for i in cenario["fotos"]]]
    assert antes == depois and CPF in antes[1][0]  # o banco segue intacto; só a saída é limpa
