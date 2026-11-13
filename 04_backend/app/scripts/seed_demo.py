"""Seed de demonstração dos 5 relatórios (V1-08) — material da conferência visual HT-09.

Cria, de forma idempotente, uma Edificação com endereço completo, um fiscal (CREA, título,
qualificações), um auditor de demonstração e um Contrato + Inspeção para cada tipo
(RFO, LTIP, RFIP, VISTORIA_CAUTELAR, VISTORIA_RESIDENCIAL):

- RFO: 2 visitas com mão de obra, medições e fotos;
- demais tipos: 8 ocorrências em 4 sistemas prediais, com GUT e grau de risco, 1 foto cada;
- fotos sintéticas (Pillow, 1200 px) enviadas ao MinIO, com legenda aprovada (RN-16/RN-17);
- conteúdo do relatório salvo (parecer da Cautelar, unidade da Residencial, datas e local).

Todo registro criado leva o prefixo `DEMO` (`"DEMO - ..."`; e-mail `demo.auditor@example.com`)
e as chaves de storage ficam sob `fotos/demo/`. Rodar de novo não duplica nada; `--reset`
apaga só o que tem o prefixo e semeia outra vez. Nada fora do prefixo é lido ou alterado.

Uso (a partir de `04_backend/`):
    python -m app.scripts.seed_demo            # idempotente
    python -m app.scripts.seed_demo --reset    # remove os registros DEMO e recria
    python -m app.scripts.seed_demo --limpar   # só remove

Senha do auditor de demonstração: variável `DEMO_SENHA` (padrão só para ambiente local).
"""
from __future__ import annotations

import argparse
import asyncio
import io
import logging
import os
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta

from PIL import Image, ImageDraw
from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models import (
    Contrato,
    ContratoExecutor,
    Edificacao,
    Foto,
    Inspecao,
    Ocorrencia,
    Relatorio,
    Responsavel,
    SistemaPredial,
    Subsistema,
    TipoAnomalia,
    Usuario,
    Visita,
    VisitaMaoObra,
    VisitaMedicao,
)
from app.models.relatorio_conteudo import RelatorioConteudo
from app.models.tipo_servico import TipoServico
from app.schemas.relatorio_conteudo import ConteudoDados
from app.services import relatorio_conteudo_service
from app.services.storage.s3_client import S3StorageClient

logger = logging.getLogger(__name__)

PREFIXO_PADRAO = "DEMO"
LADO_FOTO = 1200
SENHA_PADRAO = "demo-senha-123"  # só ambiente local; sobrescreva com DEMO_SENHA
ENDERECO = "Avenida das Palmeiras, 1200, Setor Bueno, Goiânia-GO, 74215-010"
CEP = "74215-010"
N_OCORRENCIAS = 8
N_SISTEMAS = 4
GRAUS = ("CRITICO", "MEDIO", "MINIMO", "MEDIO")
PRIORIDADE_POR_GRAU = {"CRITICO": 5, "MEDIO": 3, "MINIMO": 1}
ORDEM_TIPOS = (
    TipoServico.RFO,
    TipoServico.LTIP,
    TipoServico.RFIP,
    TipoServico.VISTORIA_CAUTELAR,
    TipoServico.VISTORIA_RESIDENCIAL,
)
LOCAIS = (
    "Hall de entrada", "Garagem — 1º subsolo", "Cobertura — casa de máquinas", "Fachada leste",
    "Circulação do 3º pavimento", "Reservatório superior", "Salão de festas", "Escada de emergência",
)
DESCRICOES = (
    "Fissuras com abertura aproximada de 0,3 mm em alvenaria de vedação, com trajeto inclinado.",
    "Infiltração com manchas de umidade e desagregação do revestimento junto ao forro.",
    "Corrosão superficial em elementos metálicos expostos, sem perda significativa de seção.",
    "Destacamento de revestimento cerâmico com som cavo à percussão.",
    "Instalação elétrica aparente sem eletroduto de proteção em trecho de circulação.",
    "Vazamento em conexão hidráulica com formação de eflorescência na parede adjacente.",
    "Selante de junta de dilatação ressecado e com perda de aderência.",
    "Sinalização de segurança contra incêndio ausente ou danificada.",
)
FUNCOES = ("Pedreiro", "Servente", "Eletricista", "Encanador")


@dataclass
class Prefixos:
    """Tudo o que identifica um registro como demonstração (parametrizado para os testes)."""

    base: str = PREFIXO_PADRAO

    @property
    def nome(self) -> str:
        return f"{self.base} - "

    @property
    def like(self) -> str:
        return f"{self.base} - %"

    @property
    def email(self) -> str:
        return f"{self.base.lower()}.auditor@example.com"

    @property
    def storage(self) -> str:
        return f"fotos/{self.base.lower()}/"

    @property
    def numero(self) -> str:
        return f"{self.base}-"


@dataclass
class Resumo:
    criados: dict[str, int] = field(default_factory=dict)
    inspecoes: dict[str, str] = field(default_factory=dict)  # tipo -> inspecao_id
    auditor_email: str = ""

    def somar(self, chave: str, n: int = 1) -> None:
        self.criados[chave] = self.criados.get(chave, 0) + n


def gerar_foto_sintetica(indice: int, rotulo: str, lado: int = LADO_FOTO) -> bytes:
    """JPEG sintético (não é foto real de campo): gradiente, linhas e moldura, `lado` px de largura."""
    largura, altura = lado, int(lado * 0.75)
    base = (50 + (indice * 23) % 150, 70 + (indice * 13) % 130, 100 + (indice * 7) % 100)
    imagem = Image.new("RGB", (largura, altura), color=base)
    desenho = ImageDraw.Draw(imagem)
    for x in range(0, largura, 40):
        desenho.line([(x, 0), (max(0, x - altura), altura)], fill=(225, 225, 225), width=2)
    desenho.rectangle([largura * 0.06, altura * 0.06, largura * 0.94, altura * 0.94], outline=(255, 210, 0), width=8)
    desenho.text((40, 40), f"Foto sintetica #{indice} - {rotulo}", fill=(255, 255, 255))
    buf = io.BytesIO()
    imagem.save(buf, format="JPEG", quality=80)
    return buf.getvalue()


# --- limpeza (só o que tem o prefixo) --------------------------------------------------


async def limpar(db: AsyncSession, pref: Prefixos, storage=None) -> None:
    """Remove edificações/contratos/inspeções/fotos/fiscal/auditor com o prefixo (e as fotos no storage)."""
    edif_ids = list((await db.execute(select(Edificacao.id).where(Edificacao.nome.like(pref.like)))).scalars())
    contrato_ids = (
        list((await db.execute(select(Contrato.id).where(Contrato.edificacao_id.in_(edif_ids)))).scalars())
        if edif_ids
        else []
    )
    insp_ids = (
        list((await db.execute(select(Inspecao.id).where(Inspecao.contrato_id.in_(contrato_ids)))).scalars())
        if contrato_ids
        else []
    )
    if insp_ids:
        visita_ids = list((await db.execute(select(Visita.id).where(Visita.inspecao_id.in_(insp_ids)))).scalars())
        ocor_ids = list(
            (await db.execute(select(Ocorrencia.id).where(Ocorrencia.inspecao_id.in_(insp_ids)))).scalars()
        )
        filtros = []
        if visita_ids:
            filtros.append(Foto.visita_id.in_(visita_ids))
        if ocor_ids:
            filtros.append(Foto.ocorrencia_id.in_(ocor_ids))
        if filtros:
            chaves = list((await db.execute(select(Foto.storage_key).where(or_(*filtros)))).scalars())
            await db.execute(delete(Foto).where(or_(*filtros)))
            if storage is not None:
                for chave in chaves:
                    storage.delete(chave)
        if visita_ids:
            await db.execute(delete(VisitaMaoObra).where(VisitaMaoObra.visita_id.in_(visita_ids)))
            await db.execute(delete(VisitaMedicao).where(VisitaMedicao.visita_id.in_(visita_ids)))
            await db.execute(delete(Visita).where(Visita.id.in_(visita_ids)))
        if ocor_ids:
            await db.execute(delete(Ocorrencia).where(Ocorrencia.id.in_(ocor_ids)))
        await db.execute(delete(Relatorio).where(Relatorio.inspecao_id.in_(insp_ids)))
        await db.execute(delete(RelatorioConteudo).where(RelatorioConteudo.inspecao_id.in_(insp_ids)))
        await db.execute(delete(Inspecao).where(Inspecao.id.in_(insp_ids)))
    if contrato_ids:
        await db.execute(delete(ContratoExecutor).where(ContratoExecutor.contrato_id.in_(contrato_ids)))
        await db.execute(delete(Contrato).where(Contrato.id.in_(contrato_ids)))
    if edif_ids:
        await db.execute(delete(Edificacao).where(Edificacao.id.in_(edif_ids)))
    await db.execute(delete(Responsavel).where(Responsavel.nome.like(pref.like)))
    await db.execute(delete(Usuario).where(Usuario.email == pref.email))
    await db.commit()


# --- criação (get-or-create) -----------------------------------------------------------


async def _auditor(db: AsyncSession, pref: Prefixos, resumo: Resumo) -> Usuario:
    usuario = await db.scalar(select(Usuario).where(Usuario.email == pref.email))
    if usuario is None:
        usuario = Usuario(
            nome=f"{pref.nome}Auditor",
            email=pref.email,
            senha_hash=hash_password(os.environ.get("DEMO_SENHA", SENHA_PADRAO)),
            ativo=True,
            role="auditor",
        )
        db.add(usuario)
        await db.flush()
        resumo.somar("usuarios")
    resumo.auditor_email = usuario.email
    return usuario


async def _fiscal(db: AsyncSession, pref: Prefixos, resumo: Resumo) -> Responsavel:
    nome = f"{pref.nome}Eng. Civil Maria Exemplo da Silva"
    fiscal = await db.scalar(select(Responsavel).where(Responsavel.nome == nome))
    if fiscal is None:
        fiscal = Responsavel(
            nome=nome,
            tipo="fiscal",
            cpf_cnpj="000.000.000-00",
            crea="0000000000D-GO",
            email="fiscal.demo@example.com",
            telefone="(62) 90000-0000",
            titulo_profissional="Engenheira Civil, Especialista em Patologia das Construções",
            qualificacoes=[
                "Engenheira Civil (CREA-GO 0000000000D)",
                "Especialização em Patologia das Construções",
                "Perícias e inspeções prediais conforme NBR 16747",
            ],
        )
        db.add(fiscal)
        await db.flush()
        resumo.somar("responsaveis")
    return fiscal


async def _edificacao(db: AsyncSession, pref: Prefixos, resumo: Resumo) -> Edificacao:
    nome = f"{pref.nome}Edifício Residencial Aurora"
    edif = await db.scalar(select(Edificacao).where(Edificacao.nome == nome))
    if edif is None:
        edif = Edificacao(
            nome=nome,
            endereco=ENDERECO,
            cep=CEP,
            tipologia="residencial multifamiliar",
            sistema_construtivo="concreto armado com vedação em alvenaria",
            descricao_pavimentos="Térreo, 2 subsolos de garagem, 14 pavimentos-tipo e cobertura.",
            area_total_m2=8450.0,
        )
        db.add(edif)
        await db.flush()
        resumo.somar("edificacoes")
    return edif


async def _contrato_e_inspecao(
    db: AsyncSession, pref: Prefixos, tipo: TipoServico, edif: Edificacao, fiscal: Responsavel, resumo: Resumo
) -> tuple[Inspecao, bool]:
    """Devolve a inspeção e se ela acabou de ser criada (filhos só são semeados nesse caso)."""
    numero = f"{pref.numero}{tipo.value}-001/2026"
    contrato = await db.scalar(select(Contrato).where(Contrato.numero == numero))
    if contrato is None:
        contrato = Contrato(
            edificacao_id=edif.id,
            fiscal_id=fiscal.id,
            numero=numero,
            tipo_servico=tipo.value,
            objeto=f"Serviço de demonstração ({tipo.value}) para conferência visual dos modelos de relatório.",
            data_inicio=date(2026, 9, 1),
            prazo_dias=90,
            art_fiscalizacao="0000000000000",
            observacoes_gerais="Dados fictícios de demonstração (V1-08).",
            status="em_andamento",
        )
        db.add(contrato)
        await db.flush()
        resumo.somar("contratos")
    inspecao = await db.scalar(select(Inspecao).where(Inspecao.contrato_id == contrato.id))
    novo = inspecao is None
    if novo:
        inspecao = Inspecao(contrato_id=contrato.id, tipo=tipo.value, status="em_andamento")
        db.add(inspecao)
        await db.flush()
        resumo.somar("inspecoes")
    return inspecao, novo


def _legenda_aprovada(foto: Foto, legenda: str, auditor: Usuario) -> None:
    """Legenda final aprovada pelo auditor, com a trilha da IA preenchida (RN-16/RN-17, DEC-37)."""
    foto.legenda = legenda
    foto.legenda_bruta = legenda.lower()
    foto.legenda_ia_sugerida = legenda
    foto.nivel_certeza_ia = "constatacao_direta"
    foto.status_validacao_ia = "aprovada"
    foto.aprovado_por_id = auditor.id
    foto.aprovado_em = datetime.now(UTC)


def _nova_foto(db, storage, pref, tipo, indice, auditor, legenda, *, visita_id=None, ocorrencia_id=None) -> None:
    chave = f"{pref.storage}{tipo.value.lower()}/foto-{indice:02d}.jpg"
    storage.upload(chave, gerar_foto_sintetica(indice, tipo.value), content_type="image/jpeg")
    foto = Foto(
        visita_id=visita_id,
        ocorrencia_id=ocorrencia_id,
        storage_key=chave,
        origem="upload_manual",
        ordem=indice,
        criado_por_id=auditor.id,
    )
    _legenda_aprovada(foto, legenda, auditor)
    db.add(foto)


async def _semear_rfo(db, storage, pref, inspecao, auditor, resumo) -> None:
    indice = 0
    for seq in (1, 2):
        visita = Visita(
            inspecao_id=inspecao.id,
            data=date(2026, 9, 1) + timedelta(days=seq * 7),
            servicos_executados=(
                "Recuperação estrutural de vigas do subsolo, com remoção do concreto desagregado, "
                "tratamento da armadura e reconstituição com argamassa estrutural."
            ),
            observacoes="Sem intercorrências. Equipamentos de proteção individual em uso por toda a equipe.",
            seq_numero=seq,
            criado_por_id=auditor.id,
        )
        db.add(visita)
        await db.flush()
        resumo.somar("visitas")
        for funcao in FUNCOES[: 2 + seq]:
            db.add(VisitaMaoObra(visita_id=visita.id, funcao=funcao, quantidade=seq + 1))
        db.add(VisitaMedicao(visita_id=visita.id, descricao="Concreto removido", quantidade=3.2 * seq, unidade="m²"))
        db.add(
            VisitaMedicao(
                visita_id=visita.id, descricao="Argamassa estrutural aplicada", quantidade=2.8 * seq, unidade="m²"
            )
        )
        for _ in range(3):
            indice += 1
            _nova_foto(
                db, storage, pref, TipoServico.RFO, indice, auditor,
                f"Visita {seq}: recuperação da viga V{indice}, vista geral do serviço executado.",
                visita_id=visita.id,
            )
            resumo.somar("fotos")
    # Executora (ART de execução), para o bloco de execução do RFO.
    legal = Responsavel(
        nome=f"{pref.nome}Responsável Legal Executora", tipo="responsavel_legal",
        cpf_cnpj="111.111.111-11", crea="1111111111D-GO",
    )
    rte = Responsavel(nome=f"{pref.nome}RTE Executora", tipo="rte", crea="2222222222D-GO")
    db.add_all([legal, rte])
    await db.flush()
    db.add(
        ContratoExecutor(
            contrato_id=inspecao.contrato_id, responsavel_legal_id=legal.id, rte_id=rte.id,
            razao_social=f"{pref.nome}Construtora Exemplo Ltda", cnpj="00.000.000/0001-00",
            endereco="Rua das Obras, 100, Goiânia-GO", art_execucao="1111111111111",
        )
    )


async def _sistemas(db: AsyncSession) -> list[tuple[SistemaPredial, Subsistema | None]]:
    """Os N primeiros sistemas prediais (por `ordem`) com um subsistema cada; gabarito se a tabela estiver vazia."""
    if not await db.scalar(select(func.count()).select_from(SistemaPredial)):
        from app.scripts.seed_gabarito import seed_gabarito

        await seed_gabarito(db)
    sistemas = list(
        (await db.execute(select(SistemaPredial).order_by(SistemaPredial.ordem).limit(N_SISTEMAS))).scalars()
    )
    pares = []
    for s in sistemas:
        sub = await db.scalar(
            select(Subsistema).where(Subsistema.sistema_id == s.id).order_by(Subsistema.ordem).limit(1)
        )
        pares.append((s, sub))
    return pares


async def _semear_ocorrencias(db, storage, pref, tipo, inspecao, auditor, resumo) -> None:
    pares = await _sistemas(db)
    if not pares:
        raise RuntimeError("Gabarito de sistemas prediais vazio: rode `python -m app.scripts.seed_gabarito`.")
    anomalias = list(
        (await db.execute(select(TipoAnomalia.nome).order_by(TipoAnomalia.ordem).limit(N_OCORRENCIAS))).scalars()
    )
    for i in range(N_OCORRENCIAS):
        sistema, sub = pares[i % len(pares)]
        grau = GRAUS[i % len(GRAUS)]
        ocorrencia = Ocorrencia(
            inspecao_id=inspecao.id,
            sistema_id=sistema.id,
            subsistema_id=sub.id if sub else None,
            localizacao=LOCAIS[i],
            situacao="NAO_CONFORME",
            classificacao="ANOMALIA",
            tipo_anomalia=anomalias[i % len(anomalias)] if anomalias else "Fissura",
            grau_risco=grau,
            prioridade=PRIORIDADE_POR_GRAU[grau],
            prioridade_sugerida=PRIORIDADE_POR_GRAU[grau],
            descricao=DESCRICOES[i],
            gut_gravidade=float(5 - (i % 3)),
            gut_urgencia=float(4 - (i % 2)),
            gut_tendencia=float(3 + (i % 3)),
            seq_numero=i + 1,
            criado_por_id=auditor.id,
        )
        db.add(ocorrencia)
        await db.flush()
        resumo.somar("ocorrencias")
        _nova_foto(
            db, storage, pref, tipo, i + 1, auditor,
            f"Ocorrência {i + 1} — {LOCAIS[i]}: {DESCRICOES[i].split(',')[0].rstrip('.')}.",
            ocorrencia_id=ocorrencia.id,
        )
        resumo.somar("fotos")


def _dados_conteudo(tipo: TipoServico, datas: list[str]) -> ConteudoDados:
    base: dict = {"data_emissao": "2026-11-11", "local_emissao": "Goiânia-GO"}
    if tipo is TipoServico.VISTORIA_CAUTELAR:
        base |= {
            "datas_vistorias": datas,
            "parecer": (
                "Com base nas constatações registradas, o imóvel vistoriado apresenta anomalias "
                "preexistentes de baixa a média criticidade, descritas e fotografadas neste laudo."
            ),
        }
    elif tipo is TipoServico.VISTORIA_RESIDENCIAL:
        base |= {"unidade": "Apartamento 1404", "datas_vistorias": datas}
    return ConteudoDados(**base)


async def _salvar_conteudo(db, tipo, inspecao, auditor, resumo) -> None:
    ja_salvo = await db.scalar(
        select(RelatorioConteudo.id).where(
            RelatorioConteudo.inspecao_id == inspecao.id, RelatorioConteudo.tipo == tipo.value
        )
    )
    if ja_salvo is not None:
        return
    await relatorio_conteudo_service.salvar(
        db, inspecao.id, tipo, _dados_conteudo(tipo, ["2026-10-05", "2026-10-12"]), usuario_id=auditor.id
    )
    resumo.somar("conteudos")


async def seed(db: AsyncSession, storage, pref: Prefixos | None = None, *, reset: bool = False) -> Resumo:
    """Semeia (ou re-semeia com `reset`) os 5 contratos de demonstração. Idempotente."""
    pref = pref or Prefixos()
    resumo = Resumo()
    if reset:
        await limpar(db, pref, storage)
    auditor = await _auditor(db, pref, resumo)
    fiscal = await _fiscal(db, pref, resumo)
    edif = await _edificacao(db, pref, resumo)
    for tipo in ORDEM_TIPOS:
        inspecao, novo = await _contrato_e_inspecao(db, pref, tipo, edif, fiscal, resumo)
        if novo:
            if tipo is TipoServico.RFO:
                await _semear_rfo(db, storage, pref, inspecao, auditor, resumo)
            else:
                await _semear_ocorrencias(db, storage, pref, tipo, inspecao, auditor, resumo)
        await db.commit()
        await _salvar_conteudo(db, tipo, inspecao, auditor, resumo)
        resumo.inspecoes[tipo.value] = str(inspecao.id)
    await db.commit()
    return resumo


async def _main(reset: bool, so_limpar: bool) -> None:
    storage = S3StorageClient()
    async with AsyncSessionLocal() as db:
        if so_limpar:
            await limpar(db, Prefixos(), storage)
            print("Registros DEMO removidos.")
            return
        resumo = await seed(db, storage, reset=reset)
    print(f"CRIADOS={resumo.criados}")
    print(f"AUDITOR_EMAIL={resumo.auditor_email}")
    for tipo, inspecao_id in resumo.inspecoes.items():
        print(f"INSPECAO_{tipo}={inspecao_id}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--reset", action="store_true", help="Remove os registros DEMO e semeia de novo")
    parser.add_argument("--limpar", action="store_true", help="Só remove os registros DEMO")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    asyncio.run(_main(args.reset, args.limpar))


if __name__ == "__main__":
    main()
