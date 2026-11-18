"""Monta o contexto da Vistoria Residencial (consumido por `vistoria_residencial_pipeline`)
a partir do banco (V1-05).

Camada de montagem: não gera arquivos. As fotos saem com `storage_key` (o
binário é baixado pela emissão genérica, `relatorio_service.emitir_relatorio`).
A assinatura do fiscal e a arte de fundo da capa, que o template recebe como
data URI, são anexadas por `anexar_imagens_do_storage` (best-effort: erro do
storage vira aviso, não derruba a emissão).

Origem dos campos (contrato em 00_docs/backlog-auto/v1-vistoria-residencial-contexto.md):

- `imovel.unidade` ← `relatorio_conteudos.dados.unidade` ('—' se ausente).
- `edificacao` ← `contrato.edificacao`; `fiscal` ← `contrato.fiscal`.
- `data_emissao`/`local_emissao` ← conteúdo (padrão: hoje / cidade do endereço).
- `textos.*` ← padrões do tipo, sobrescritos pelos textos gerados do banco
  (`s4_2_1`, `s4_2_2`, `s4_2_3`, `s5_1`, `s5_2`), sobrescritos pelo conteúdo salvo.
- `fotos[]` ← fotos das ocorrências (só `legenda`, nunca a sugestão de IA), numeradas.
- `sistemas[]` ← ocorrências por sistema + `dados.fundamentacao_tecnica[sistema_id]`.
"""
from __future__ import annotations

import base64
import logging
import re
import uuid
from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import NotFoundError
from app.models import Contrato, Inspecao, Ocorrencia, RelatorioConteudo
from app.models.tipo_servico import TipoServico
from app.services.relatorio_conteudo_service import (
    deep_merge,
    preencher_placeholders,
    textos_padrao,
)
from app.services.report_generator.contexto_comum import cidade_emissao
from app.services.report_generator.imagem import otimizar_imagem
from app.services.report_generator.legenda_foto import legenda_para_relatorio
from app.services.storage import StorageClient

logger = logging.getLogger(__name__)

TIPO_VISTORIA_RESIDENCIAL = TipoServico.VISTORIA_RESIDENCIAL.value
VAZIO = "—"
FONTE_PADRAO = "Autor"
FUSO_EMISSAO = "America/Sao_Paulo"  # padrão de `data_emissao` (Goiânia = UTC-3)
# Tipos de `edificacao.documentos_tecnicos.itens[].tipo` aceitos como arte de fundo da capa.
TIPOS_DOCUMENTO_CAPA = frozenset({"capa", "fachada"})

# Campos sem os quais o laudo não é emitido (422 por campo). `fiscal.nome` é NOT NULL
# no banco, mas a checagem é barata e protege contextos montados à mão.
CAMPOS_OBRIGATORIOS: tuple[tuple[str, str], ...] = (
    ("fiscal", "nome"),
    ("fiscal", "crea"),
    ("imovel", "unidade"),
)

# Separadores entre cidade e UF: hífen, travessão curto (U+2013) ou barra.
_SEP = "\\-\u2013"
_CIDADE_UF_RE = re.compile(
    rf"(?:^|[,{_SEP}])\s*(?P<cidade>[^\d,{_SEP}/]+?)\s*[{_SEP}/]\s*(?P<uf>[A-Z]{{2}})\b"
    rf"(?:\s*[,{_SEP}]?\s*(?:CEP:?\s*)?\d{{5}}-?\d{{3}})?\s*\.?\s*$"
)


# --- validação ------------------------------------------------------------------------


def _ausente(valor: Any) -> bool:
    return valor is None or (isinstance(valor, str) and valor.strip() in ("", VAZIO))


def validar_contexto_vistoria_residencial(contexto: dict[str, Any]) -> list[str]:
    """Caminhos obrigatórios ausentes (`fiscal.crea`, `imovel.unidade`); vazia = emitível.

    Ausente = `None`, texto em branco ou '—' (o traço do DEC-33 é preenchimento, não valor).
    """
    return [
        f"{secao}.{campo}"
        for secao, campo in CAMPOS_OBRIGATORIOS
        if _ausente((contexto.get(secao) or {}).get(campo))
    ]


# --- auxiliares puros -----------------------------------------------------------------


def _texto(valor: Any) -> str | None:
    if valor is None:
        return None
    texto = str(valor).strip()
    return texto or None


def hoje() -> date:
    """Data de hoje no fuso de Goiânia (o container roda em UTC: depois das 21h já seria amanhã)."""
    try:
        return datetime.now(ZoneInfo(FUSO_EMISSAO)).date()
    except ZoneInfoNotFoundError:  # Windows sem o pacote tzdata
        return date.today()


def _data_br(valor: date) -> str:
    return valor.strftime("%d/%m/%Y")


def _data_iso(valor: Any) -> date | None:
    if isinstance(valor, date):
        return valor
    try:
        return date.fromisoformat(str(valor))
    except (TypeError, ValueError):
        return None


def _numero_br(valor: float) -> str:
    texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return texto[:-3] if texto.endswith(",00") else texto


def cidade_do_endereco(endereco: str | None) -> str | None:
    """'Rua X, 10 - Centro, Goiânia - GO, 74000-000' -> 'Goiânia-GO'; sem 'Cidade - UF' -> None."""
    if not endereco:
        return None
    achado = _CIDADE_UF_RE.search(endereco.strip())
    if achado is None:
        return None
    return f"{achado['cidade'].strip()}-{achado['uf']}"


def texto_tipologia(edificacao: dict[str, Any]) -> list[str]:
    tipologia = _texto(edificacao.get("tipologia"))
    return [f"Tipologia da edificação: {tipologia}."] if tipologia else []


def texto_caracterizacao(edificacao: dict[str, Any]) -> list[str]:
    paragrafos = []
    if sistema := _texto(edificacao.get("sistema_construtivo")):
        paragrafos.append(f"Sistema construtivo: {sistema}.")
    if pavimentos := _texto(edificacao.get("descricao_pavimentos")):
        paragrafos.append(f"Pavimentos: {pavimentos.rstrip('.')}.")
    if (area := edificacao.get("area_total_m2")) is not None:
        paragrafos.append(f"Área total construída: {_numero_br(float(area))} m².")
    return paragrafos


def texto_localizacao(edificacao: dict[str, Any]) -> list[str]:
    paragrafos = []
    if endereco := _texto(edificacao.get("endereco")):
        paragrafos.append(f"Endereço: {endereco.rstrip('.')}.")
    if cep := _texto(edificacao.get("cep")):
        paragrafos.append(f"CEP: {cep}.")
    return paragrafos


def texto_responsavel(fiscal: dict[str, Any]) -> list[str]:
    nome = _texto(fiscal.get("nome"))
    if not nome:
        return []
    identificacao = nome
    if titulo := _texto(fiscal.get("titulo_profissional")):
        identificacao += f", {titulo}"
    if crea := _texto(fiscal.get("crea")):
        identificacao += f", CREA nº {crea}"
    paragrafos = [f"A inspeção foi realizada pelo responsável técnico {identificacao}."]
    contatos = [c for c in (_texto(fiscal.get("email")), _texto(fiscal.get("telefone"))) if c]
    if contatos:
        paragrafos.append(f"Contato: {' / '.join(contatos)}.")
    return paragrafos


def texto_datas_vistorias(datas: list[Any] | None) -> list[str]:
    validas = sorted({d for d in (_data_iso(v) for v in datas or []) if d})
    if not validas:
        return []
    if len(validas) == 1:
        return [f"A vistoria foi realizada em {_data_br(validas[0])}."]
    lista = ", ".join(_data_br(d) for d in validas[:-1]) + f" e {_data_br(validas[-1])}"
    return [f"As vistorias foram realizadas em {lista}."]


def _constatacao(ocorrencia: Ocorrencia, numeros: list[int]) -> str | None:
    descricao = _texto(ocorrencia.descricao) or _texto(ocorrencia.tipo_anomalia)
    if not descricao:
        return None
    texto = descricao.rstrip(".")
    if local := _texto(ocorrencia.localizacao):
        texto = f"{local}: {texto}"
    if numeros:
        rotulo = "Figura" if len(numeros) == 1 else "Figuras"
        texto += f" ({rotulo} {', '.join(str(n) for n in numeros)})"
    return texto + "."


def _fotos_e_sistemas(
    ocorrencias: list[Ocorrencia], fundamentacao: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    fotos: list[dict[str, Any]] = []
    sistemas: dict[uuid.UUID, dict[str, Any]] = {}
    ordem_sistema: dict[uuid.UUID, tuple] = {}
    for oc in sorted(ocorrencias, key=lambda o: o.seq_numero):
        numeros: list[int] = []
        for foto in sorted(oc.fotos, key=lambda f: (f.ordem is None, f.ordem or 0, str(f.id))):
            numero = len(fotos) + 1
            numeros.append(numero)
            # DEC-37 DP-9: só `legenda` entra; a sugestão de IA nunca, qualquer status.
            fotos.append({
                "id": str(foto.id),
                "numero": numero,
                "storage_key": foto.storage_key,
                "legenda": legenda_para_relatorio(foto) or None,
                "fonte": FONTE_PADRAO,
                "ocorrencia_id": str(oc.id),
            })
        sistema = oc.sistema
        bloco = sistemas.setdefault(oc.sistema_id, {
            "id": str(oc.sistema_id),
            "nome": sistema.nome if sistema else None,
            "constatacoes": [],
            "fundamentacao_tecnica": list(fundamentacao.get(str(oc.sistema_id)) or []),
        })
        ordem_sistema.setdefault(oc.sistema_id, (sistema.ordem if sistema else 0, bloco["nome"] or ""))
        if constatacao := _constatacao(oc, numeros):
            bloco["constatacoes"].append(constatacao)
    ordenados = sorted(sistemas, key=lambda sid: (*ordem_sistema[sid], str(sid)))
    return fotos, [sistemas[sid] for sid in ordenados]


def _documento_capa(documentos_tecnicos: dict[str, Any] | None) -> str | None:
    """Último documento técnico da edificação do tipo 'capa'/'fachada' (storage_key)."""
    itens = (documentos_tecnicos or {}).get("itens") or []
    for item in reversed(itens):
        if isinstance(item, dict) and str(item.get("tipo") or "").strip().lower() in TIPOS_DOCUMENTO_CAPA:
            if chave := _texto(item.get("storage_key")):
                return chave
    return None


# --- montagem -------------------------------------------------------------------------


async def montar_contexto_vistoria_residencial(db: AsyncSession, inspecao_id: uuid.UUID) -> dict[str, Any]:
    """Dicionário aceito por `vistoria_residencial_pipeline.normalizar_contexto`.

    404 se a inspeção não existe. A checagem de tipo (409) fica com a emissão genérica.
    """
    resultado = await db.execute(
        select(Inspecao)
        .options(
            selectinload(Inspecao.contrato).selectinload(Contrato.edificacao),
            selectinload(Inspecao.contrato).selectinload(Contrato.fiscal),
            selectinload(Inspecao.ocorrencias).selectinload(Ocorrencia.fotos),
            selectinload(Inspecao.ocorrencias).selectinload(Ocorrencia.sistema),
        )
        .where(Inspecao.id == inspecao_id)
    )
    inspecao = resultado.scalar_one_or_none()
    if inspecao is None:
        raise NotFoundError(f"Inspeção '{inspecao_id}' não encontrada.", type_suffix="inspecao-nao-encontrada")
    dados: dict[str, Any] = (
        await db.execute(
            select(RelatorioConteudo.dados).where(
                RelatorioConteudo.inspecao_id == inspecao_id,
                RelatorioConteudo.tipo == TIPO_VISTORIA_RESIDENCIAL,
            )
        )
    ).scalar_one_or_none() or {}

    contrato = inspecao.contrato
    edificacao = contrato.edificacao
    responsavel = contrato.fiscal
    edificacao_ctx = {
        "nome": edificacao.nome,
        "endereco": edificacao.endereco,
        "cep": edificacao.cep,
        "tipologia": edificacao.tipologia,
        "sistema_construtivo": edificacao.sistema_construtivo,
        "descricao_pavimentos": edificacao.descricao_pavimentos,
        "area_total_m2": edificacao.area_total_m2,
    }
    fiscal_ctx = {
        "nome": responsavel.nome,
        "crea": responsavel.crea,
        "email": responsavel.email,
        "telefone": responsavel.telefone,
        "titulo_profissional": responsavel.titulo_profissional,
        "qualificacoes": [str(q) for q in (responsavel.qualificacoes or []) if _texto(q)],
    }

    padroes = preencher_placeholders(
        textos_padrao(TipoServico.VISTORIA_RESIDENCIAL),
        {"edificacao_nome": edificacao.nome, "edificacao_endereco": edificacao.endereco},
    )
    gerados = {
        "s4_2_1": texto_tipologia(edificacao_ctx),
        "s4_2_2": texto_caracterizacao(edificacao_ctx),
        "s4_2_3": texto_localizacao(edificacao_ctx),
        "s5_1": texto_responsavel(fiscal_ctx),
        "s5_2": texto_datas_vistorias(dados.get("datas_vistorias")),
    }
    textos = deep_merge(padroes, {chave: valor for chave, valor in gerados.items() if valor})
    textos = deep_merge(textos, dados.get("textos") or {})

    fotos, sistemas = _fotos_e_sistemas(inspecao.ocorrencias, dados.get("fundamentacao_tecnica") or {})

    return {
        "inspecao": {"id": str(inspecao.id), "tipo": inspecao.tipo, "status": inspecao.status},
        "imovel": {"unidade": _texto(dados.get("unidade")) or VAZIO},
        "edificacao": edificacao_ctx,
        "fiscal": fiscal_ctx,
        "data_emissao": _data_iso(dados.get("data_emissao")) or hoje(),
        "local_emissao": _texto(dados.get("local_emissao"))
        or cidade_emissao(edificacao, cidade_do_endereco)
        or VAZIO,
        "textos": textos,
        "fotos": fotos,
        "sistemas": sistemas,
        "assinatura_storage_key": _texto(responsavel.assinatura_storage_key),
        "capa_fundo_storage_key": _documento_capa(edificacao.documentos_tecnicos),
        "assinatura_data_uri": None,
        "capa_fundo_data_uri": None,
        "avisos": [],
    }


def extrair_fotos_vistoria_residencial(contexto: dict[str, Any]) -> set[str]:
    """`storage_key` das fotos do cap. 8 (assinatura e capa vêm de `anexar_imagens_do_storage`)."""
    return {f["storage_key"] for f in contexto.get("fotos", []) if f.get("storage_key")}


# --- imagens opcionais do storage ----------------------------------------------------


def _mime(conteudo: bytes) -> str | None:
    if conteudo.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if conteudo.startswith(b"\xff\xd8"):
        return "image/jpeg"
    if conteudo[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if conteudo[:4] == b"RIFF" and conteudo[8:12] == b"WEBP":
        return "image/webp"
    inicio = conteudo[:256].lstrip().lower()
    if inicio.startswith(b"<svg") or (inicio.startswith(b"<?xml") and b"<svg" in conteudo[:2048].lower()):
        return "image/svg+xml"
    return None


def _data_uri(conteudo: bytes, *, otimizar: bool) -> str | None:
    mime = _mime(conteudo)
    if mime is None:
        return None
    if otimizar and mime in ("image/jpeg", "image/png", "image/webp"):
        try:
            conteudo, mime = otimizar_imagem(conteudo), "image/jpeg"
        except Exception:  # imagem que o Pillow não abre: segue o original
            logger.warning("Capa da Vistoria Residencial não otimizada; usando o arquivo original.")
    return f"data:{mime};base64,{base64.b64encode(conteudo).decode('ascii')}"


def anexar_imagens_do_storage(contexto: dict[str, Any], storage: StorageClient) -> None:
    """Preenche `assinatura_data_uri` e `capa_fundo_data_uri` a partir do storage.

    Opcionais: chave ausente, arquivo inexistente, erro do storage ou formato que
    não é imagem só registram aviso (`contexto["avisos"]` e log) e o campo fica `None`.
    A assinatura não é otimizada (PNG com transparência); a capa vira JPEG ≤ 1200 px.
    """
    avisos = contexto.setdefault("avisos", [])
    for chave_storage, chave_uri, otimizar in (
        ("assinatura_storage_key", "assinatura_data_uri", False),
        ("capa_fundo_storage_key", "capa_fundo_data_uri", True),
    ):
        chave = contexto.get(chave_storage)
        if not chave:
            continue
        try:
            conteudo = storage.download(chave)
        except Exception as exc:  # opcional: nunca derruba a emissão
            mensagem = f"{chave_uri}: não foi possível ler '{chave}' do storage ({type(exc).__name__})."
            logger.warning("Vistoria Residencial %s: %s", contexto.get("inspecao", {}).get("id"), mensagem)
            avisos.append(mensagem)
            continue
        uri = _data_uri(conteudo, otimizar=otimizar)
        if uri is None:
            mensagem = f"{chave_uri}: '{chave}' não é uma imagem reconhecida (PNG, JPEG, GIF, WebP ou SVG)."
            logger.warning("Vistoria Residencial %s: %s", contexto.get("inspecao", {}).get("id"), mensagem)
            avisos.append(mensagem)
            continue
        contexto[chave_uri] = uri
