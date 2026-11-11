"""Contexto técnico só texto da legenda por IA (BL-34; plano-deepseek item 1; risco R-10).

`ContextoLegenda` reúne o que o modelo precisa para acertar a legenda (anomalia, sistema, GUT, grau
de risco, NBRs do contrato) e **nada que identifique pessoas ou o cliente**: sem nome de cliente,
endereço, CPF/CNPJ, nomes de pessoas, ids ou datas. O texto livre (legenda bruta, descrição,
localização) passa por `limpar_dados_pessoais`, uma limpeza por regex de CPF/CNPJ/e-mail/telefone.
Ela é uma rede de segurança simples, não uma garantia de anonimização.
"""
import json
import re
import uuid
from dataclasses import asdict, dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ContratoNbr, Foto, Inspecao, Ocorrencia, SistemaPredial, Subsistema, Visita

_CNPJ = re.compile(r"(?<!\d)\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}(?!\d)")
_CPF = re.compile(r"(?<!\d)\d{3}\.?\d{3}\.?\d{3}-?\d{2}(?!\d)")
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
# Telefone só com DDD/código do país ou hífen, para não apagar medidas como «1234 5678 mm».
_TELEFONE = re.compile(
    r"(?<![\d.,])(?:(?:\+?55[\s-]?)?(?:\(\d{2}\)\s?|\d{2}[\s-])9?\d{4}[-\s]?\d{4}|9?\d{4}-\d{4})(?![\d.,])"
)

_SEM_INFORMACAO = object()


def limpar_dados_pessoais(texto: str | None) -> str | None:
    """Troca CPF, CNPJ, e-mail e telefone por marcadores; `None`/vazio vira `None`."""
    if texto is None:
        return None
    limpo = _CNPJ.sub("[CNPJ]", texto)
    limpo = _CPF.sub("[CPF]", limpo)
    limpo = _EMAIL.sub("[EMAIL]", limpo)
    limpo = _TELEFONE.sub("[TELEFONE]", limpo)
    return limpo.strip() or None


@dataclass(frozen=True)
class NbrContexto:
    codigo: str
    descricao: str | None = None


@dataclass(frozen=True)
class ContextoLegenda:
    legenda_bruta: str | None = None
    tipo_anomalia: str | None = None
    sistema: str | None = None
    subsistema: str | None = None
    ambiente: str | None = None
    descricao: str | None = None
    gut_gravidade: float | None = None
    gut_urgencia: float | None = None
    gut_tendencia: float | None = None
    grau_risco: str | None = None
    nbrs: tuple[NbrContexto, ...] = field(default_factory=tuple)
    tipo_relatorio: str | None = None

    def canonico(self) -> str:
        """JSON ordenado e estável (chaves ordenadas, NBRs ordenadas), próprio para chave de cache."""
        dados = asdict(self)
        dados["nbrs"] = sorted(
            ({"codigo": n.codigo, "descricao": n.descricao} for n in self.nbrs),
            key=lambda n: (n["codigo"], n["descricao"] or ""),
        )
        return json.dumps(dados, sort_keys=True, ensure_ascii=False, separators=(",", ":"))

    def bloco_dados(self) -> str:
        """Bloco «DADOS DA OCORRÊNCIA» (sem a legenda bruta, que segue delimitada à parte)."""
        gut = [
            f"{rotulo}={valor:g}"
            for rotulo, valor in (
                ("G", self.gut_gravidade), ("U", self.gut_urgencia), ("T", self.gut_tendencia)
            )
            if valor is not None
        ]
        linhas = [
            ("Tipo de relatório", self.tipo_relatorio),
            ("Sistema", self.sistema),
            ("Subsistema", self.subsistema),
            ("Ambiente/localização", self.ambiente),
            ("Tipo de anomalia", self.tipo_anomalia),
            ("Descrição da ocorrência", self.descricao),
            ("Notas GUT", " ".join(gut) if gut else None),
            ("Grau de risco", self.grau_risco),
            (
                "NBRs do contrato",
                "; ".join(f"{n.codigo} ({n.descricao})" if n.descricao else n.codigo for n in self.nbrs)
                or None,
            ),
        ]
        corpo = [f"- {rotulo}: {valor}" for rotulo, valor in linhas if valor]
        return "DADOS DA OCORRÊNCIA\n" + ("\n".join(corpo) if corpo else "(sem dados da ocorrência)")


async def montar_contexto(
    db: AsyncSession, foto: Foto, legenda_bruta: object = _SEM_INFORMACAO
) -> ContextoLegenda:
    """Monta o contexto da foto a partir da ocorrência, inspeção e contrato (consultas explícitas).

    `legenda_bruta` substitui a gravada na foto (a que chegou na requisição de geração).
    Foto sem ocorrência (só visita) ainda recebe tipo de relatório e NBRs pela inspeção da visita.
    """
    bruta = foto.legenda_bruta if legenda_bruta is _SEM_INFORMACAO else legenda_bruta
    ocorrencia = (
        await db.get(Ocorrencia, foto.ocorrencia_id) if foto.ocorrencia_id is not None else None
    )
    inspecao_id: uuid.UUID | None = ocorrencia.inspecao_id if ocorrencia else None
    if inspecao_id is None and foto.visita_id is not None:
        visita = await db.get(Visita, foto.visita_id)
        inspecao_id = visita.inspecao_id if visita else None
    inspecao = await db.get(Inspecao, inspecao_id) if inspecao_id is not None else None

    sistema = subsistema = None
    if ocorrencia is not None:
        item = await db.get(SistemaPredial, ocorrencia.sistema_id)
        sistema = item.nome if item else None
        if ocorrencia.subsistema_id is not None:
            sub = await db.get(Subsistema, ocorrencia.subsistema_id)
            subsistema = sub.nome if sub else None

    nbrs: tuple[NbrContexto, ...] = ()
    if inspecao is not None:
        linhas = await db.execute(
            select(ContratoNbr)
            .where(ContratoNbr.contrato_id == inspecao.contrato_id)
            .order_by(ContratoNbr.codigo_nbr)
        )
        nbrs = tuple(
            NbrContexto(n.codigo_nbr, limpar_dados_pessoais(n.descricao))
            for n in linhas.scalars().all()
        )

    return ContextoLegenda(
        legenda_bruta=limpar_dados_pessoais(bruta),
        tipo_anomalia=ocorrencia.tipo_anomalia if ocorrencia else None,
        sistema=sistema,
        subsistema=subsistema,
        ambiente=limpar_dados_pessoais(ocorrencia.localizacao) if ocorrencia else None,
        descricao=limpar_dados_pessoais(ocorrencia.descricao) if ocorrencia else None,
        gut_gravidade=ocorrencia.gut_gravidade if ocorrencia else None,
        gut_urgencia=ocorrencia.gut_urgencia if ocorrencia else None,
        gut_tendencia=ocorrencia.gut_tendencia if ocorrencia else None,
        grau_risco=ocorrencia.grau_risco if ocorrencia else None,
        nbrs=nbrs,
        tipo_relatorio=inspecao.tipo if inspecao else None,
    )
