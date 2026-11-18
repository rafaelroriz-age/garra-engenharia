"""Peças reutilizáveis na montagem do contexto dos relatórios (V1-03).

Camada de montagem apenas (sem arquivos nem imagens): carrega inspeção + contrato +
edificação + fiscal, converte ocorrências (sistema/subsistema com `ordem`, GUT, grau de
risco, prioridade, localização) e fotos (legenda só via `legenda_para_relatorio`, DEC-37 DP-9).
Campo de texto vazio vira '—' (DEC-33); número ausente fica `None` (o pipeline imprime '—').
"""
from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ConflictError, NotFoundError
from app.models import Contrato, Foto, Inspecao, Ocorrencia, Responsavel
from app.models.tipo_servico import TipoServico
from app.services.report_generator.legenda_foto import legenda_para_relatorio

VAZIO = "—"


def vazio(valor: Any) -> bool:
    """None, texto em branco ou o próprio traço (campo já normalizado por DEC-33)."""
    return valor is None or (isinstance(valor, str) and valor.strip() in ("", VAZIO))


def texto_ou_traco(valor: str | None) -> str:
    """DEC-33: campo vazio (None, '' ou só espaços) vira '—'; demais valores seguem inalterados."""
    if valor is None or not valor.strip():
        return VAZIO
    return valor


def data_br(valor: date | None) -> str | None:
    return valor.strftime("%d/%m/%Y") if valor else None


def fotos_ordenadas(fotos: list[Foto]) -> list[Foto]:
    """Por `ordem` (nulos ao final), desempate estável por id."""
    return sorted(fotos, key=lambda f: (f.ordem is None, f.ordem or 0, str(f.id)))


def validar_obrigatorios(contexto: dict[str, Any], campos: tuple[tuple[str, str], ...]) -> list[str]:
    """Caminhos `secao.campo` ausentes (`None`, em branco ou '—'); vazia = emitível."""
    return [f"{secao}.{campo}" for secao, campo in campos if vazio((contexto.get(secao) or {}).get(campo))]


async def carregar_inspecao(db: AsyncSession, inspecao_id: uuid.UUID, tipo: TipoServico) -> Inspecao:
    """Inspeção com contrato, edificação, fiscal e ocorrências (sistema, subsistema, fotos).

    404 se não existe; 409 (`inspecao-nao-{tipo}`) se o tipo da inspeção é outro.
    """
    resultado = await db.execute(
        select(Inspecao)
        .options(
            selectinload(Inspecao.contrato).selectinload(Contrato.edificacao),
            selectinload(Inspecao.contrato).selectinload(Contrato.fiscal),
            selectinload(Inspecao.contrato).selectinload(Contrato.nbrs),
            selectinload(Inspecao.ocorrencias).selectinload(Ocorrencia.fotos),
            selectinload(Inspecao.ocorrencias).selectinload(Ocorrencia.sistema),
            selectinload(Inspecao.ocorrencias).selectinload(Ocorrencia.subsistema),
        )
        .where(Inspecao.id == inspecao_id)
    )
    inspecao = resultado.scalar_one_or_none()
    if inspecao is None:
        raise NotFoundError(f"Inspeção '{inspecao_id}' não encontrada.", type_suffix="inspecao-nao-encontrada")
    if TipoServico.normalizar(inspecao.tipo) is not tipo:
        raise ConflictError(
            f"Inspeção '{inspecao_id}' é do tipo '{inspecao.tipo}'; o relatório {tipo.value} só é gerado "
            f"para inspeções do tipo '{tipo.value}'.",
            type_suffix=f"inspecao-nao-{tipo.value.lower()}",
        )
    return inspecao


def inspecao_ctx(inspecao: Inspecao) -> dict[str, Any]:
    return {"id": str(inspecao.id), "tipo": inspecao.tipo, "status": inspecao.status}


def fiscal_ctx(fiscal: Responsavel) -> dict[str, Any]:
    """Fiscal do contrato como signatário (nome, título, CREA, contato)."""
    return {
        "nome": texto_ou_traco(fiscal.nome),
        "titulo_profissional": texto_ou_traco(fiscal.titulo_profissional),
        "crea": texto_ou_traco(fiscal.crea),
        "email": texto_ou_traco(fiscal.email),
        "telefone": texto_ou_traco(fiscal.telefone),
    }


def edificacao_ctx(edificacao: Any) -> dict[str, Any]:
    return {
        "nome": texto_ou_traco(edificacao.nome),
        "endereco": texto_ou_traco(edificacao.endereco),
        "cep": texto_ou_traco(edificacao.cep),
        "tipologia": texto_ou_traco(edificacao.tipologia),
        "sistema_construtivo": texto_ou_traco(edificacao.sistema_construtivo),
        "descricao_pavimentos": texto_ou_traco(edificacao.descricao_pavimentos),
        "area_total_m2": edificacao.area_total_m2,
    }


def cidade_emissao(
    edificacao: Any, extrair_do_endereco: Callable[[str | None], str | None] | None = None
) -> str | None:
    """Local de emissão `Cidade-UF` da edificação (DEC-50 P5); None se não houver como saber.

    - `cidade` e `uf` preenchidas: `f"{cidade}-{uf}"` (mesmo formato que o endereço produz).
    - Só a `cidade`: usa o resultado do endereço se ele for dessa cidade (completa a UF);
      senão, a cidade sozinha (o campo explícito prevalece sobre o endereço livre).
    - Só a `uf` ou nenhuma: fallback pelo endereço (`extrair_do_endereco`), como antes; a UF
      sozinha não identifica o local.

    `extrair_do_endereco` é o parser do montador (cautelar e residencial têm o seu); sem ele, só
    os campos explícitos contam.
    """
    cidade = (getattr(edificacao, "cidade", None) or "").strip()
    uf = (getattr(edificacao, "uf", None) or "").strip().upper()
    if cidade and uf:
        return f"{cidade}-{uf}"
    do_endereco = extrair_do_endereco(getattr(edificacao, "endereco", None)) if extrair_do_endereco else None
    if cidade:
        if do_endereco and do_endereco.rsplit("-", 1)[0].strip().casefold() == cidade.casefold():
            return do_endereco
        return cidade
    return do_endereco


def contrato_ctx(contrato: Contrato) -> dict[str, Any]:
    return {
        "numero": texto_ou_traco(contrato.numero),
        "tipo_servico": contrato.tipo_servico,
        "objeto": texto_ou_traco(contrato.objeto),
        "art_fiscalizacao": texto_ou_traco(contrato.art_fiscalizacao),
    }


def foto_ctx(foto: Foto) -> dict[str, Any]:
    # DEC-37 DP-9: só `legenda` entra (aprovada ou manual); a sugestão de IA nunca, qualquer status.
    return {
        "id": str(foto.id),
        "storage_key": foto.storage_key,
        "legenda": legenda_para_relatorio(foto) or VAZIO,
        "ordem": foto.ordem,
    }


def ocorrencia_ctx(oc: Ocorrencia) -> dict[str, Any]:
    """Ocorrência no formato de `ltip_pipeline`/`rfip_pipeline` (planas; o pipeline agrupa por sistema, RN-11).

    `sistema_ordem`/`subsistema_ordem` carregam a `ordem` do gabarito; GUT e prioridade ausentes
    ficam `None` (o pipeline imprime '—' e só calcula a pontuação com as três notas).
    """
    return {
        "id": str(oc.id),
        "seq_numero": oc.seq_numero,
        "sistema": oc.sistema.nome if oc.sistema else None,
        "sistema_ordem": oc.sistema.ordem if oc.sistema else None,
        "subsistema": oc.subsistema.nome if oc.subsistema else VAZIO,
        "subsistema_ordem": oc.subsistema.ordem if oc.subsistema else None,
        "localizacao": texto_ou_traco(oc.localizacao),
        "situacao": texto_ou_traco(oc.situacao),
        "classificacao": texto_ou_traco(oc.classificacao),
        "tipo_anomalia": oc.tipo_anomalia,
        "tipo_falha": oc.tipo_falha,
        "grau_risco": texto_ou_traco(oc.grau_risco),
        "prioridade": oc.prioridade,
        "gut_gravidade": oc.gut_gravidade,
        "gut_urgencia": oc.gut_urgencia,
        "gut_tendencia": oc.gut_tendencia,
        "descricao": texto_ou_traco(oc.descricao),
        "fotos": [foto_ctx(f) for f in fotos_ordenadas(oc.fotos)],
    }


def ocorrencias_ctx(inspecao: Inspecao) -> list[dict[str, Any]]:
    return [ocorrencia_ctx(o) for o in sorted(inspecao.ocorrencias, key=lambda o: o.seq_numero)]


def primeiras_fotos(contexto: dict[str, Any]) -> set[str]:
    """`storage_key` da 1ª foto de cada ocorrência: a ficha do LTIP/RFIP mostra uma foto só."""
    chaves: set[str] = set()
    for oc in contexto.get("ocorrencias") or []:
        fotos = oc.get("fotos") or []
        if fotos and fotos[0].get("storage_key"):
            chaves.add(fotos[0]["storage_key"])
    return chaves
