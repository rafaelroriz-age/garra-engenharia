"""Coleta em processo das respostas de leitura da equipe para o snapshot (DEC-57, T81).

Chama o próprio app FastAPI via `httpx.AsyncClient(transport=ASGITransport(app))`,
autenticado como um auditor de serviço, e guarda cada corpo JSON sob a chave
`/api/v1<path>?<query>` — exatamente o `path` que o front passa para `apiFetch`
(relativo a `NEXT_PUBLIC_API_URL`, que termina em `/api/v1`), com a query na
mesma ordem do `URLSearchParams` das telas. A lista de rotas e de onde vem cada
uma está em `00_docs/backlog-auto/snapshot-cifrado.md`.

Fora do snapshot, por desenho: `/portal/*`, `/auth/login`, downloads de
relatório (`/download/`), bytes de fotos e documentos.
"""
import asyncio
import logging
import secrets
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import quote, urlencode

import httpx
from fastapi import FastAPI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.database import get_db
from app.core.security import create_access_token, hash_password
from app.models import Usuario

logger = logging.getLogger(__name__)

PREFIXO_API = "/api/v1"
EMAIL_SERVICO_PADRAO = "snapshot.servico@garra-engenharia.com.br"
NOME_SERVICO = "Snapshot de leitura (serviço)"
ROLE_SERVICO = "auditor"

# Tamanhos de página usados pelas telas (03_frontend/app/*/page.tsx).
PAGE_SIZE_TELAS = 10  # edificacoes/page.tsx e contratos/page.tsx
PAGE_SIZE_SELECT_EDIFICACOES = 100  # contratos/page.tsx (select de edificação)

# Rotas nunca capturadas, mesmo que alguma regra futura as gere.
_PROIBIDOS = ("/portal", "/auth/login", "/download/", "/documentos", "/fotos/")

CONCORRENCIA_PADRAO = 8

# Caracteres que `encodeURIComponent` não codifica (além de letras, dígitos e -_.~).
_SEGURO_URI_COMPONENT = "!'()*"


class SnapshotUsuarioInvalido(RuntimeError):
    """O e-mail do usuário de serviço já pertence a uma conta que não é auditor ativo."""


@dataclass
class ResultadoColeta:
    rotas: dict[str, Any] = field(default_factory=dict)
    falhas: dict[str, int] = field(default_factory=dict)  # chave -> status HTTP


async def garantir_usuario_servico(db: AsyncSession, email: str = EMAIL_SERVICO_PADRAO) -> Usuario:
    """Devolve o auditor de serviço, criando-o com senha aleatória (descartada) se não existir.

    Nunca altera uma conta existente: se o e-mail já for de um usuário que não é
    auditor ativo, falha em vez de promovê-lo.
    """
    usuario = await db.scalar(select(Usuario).where(Usuario.email == email))
    if usuario is not None:
        if usuario.role != ROLE_SERVICO or not usuario.ativo:
            raise SnapshotUsuarioInvalido(
                f"O e-mail {email!r} já pertence a um usuário com role={usuario.role!r}, "
                f"ativo={usuario.ativo}; escolha outro SNAPSHOT_USUARIO_EMAIL."
            )
        return usuario
    usuario = Usuario(
        nome=NOME_SERVICO,
        email=email,
        senha_hash=hash_password(secrets.token_urlsafe(32)),
        ativo=True,
        role=ROLE_SERVICO,
    )
    db.add(usuario)
    await db.commit()
    await db.refresh(usuario)
    logger.info("Usuário de serviço do snapshot criado: %s", email)
    return usuario


def _qs(params: dict[str, Any]) -> str:
    """Query igual à do `URLSearchParams` do front (ordem de inserção, espaço como '+')."""
    return urlencode({k: str(v) for k, v in params.items() if v is not None})


def _itens(corpo: Any) -> list[dict[str, Any]]:
    if isinstance(corpo, dict):
        return list(corpo.get("items") or [])
    if isinstance(corpo, list):
        return corpo
    return []


class _Coletor:
    def __init__(self, client: httpx.AsyncClient, concorrencia: int) -> None:
        self._client = client
        self._sem = asyncio.Semaphore(concorrencia)
        self.resultado = ResultadoColeta()

    async def get(self, path: str) -> Any | None:
        """GET `path` (relativo a /api/v1, como no front) e grava sob a chave completa."""
        chave = PREFIXO_API + path
        if any(p in chave for p in _PROIBIDOS):
            raise ValueError(f"Rota proibida no snapshot: {chave}")
        if chave in self.resultado.rotas:
            return self.resultado.rotas[chave]
        async with self._sem:
            resposta = await self._client.get(chave)
        if resposta.status_code != 200 or "json" not in resposta.headers.get("content-type", ""):
            self.resultado.falhas[chave] = resposta.status_code
            logger.warning("Snapshot: %s -> HTTP %s", chave, resposta.status_code)
            return None
        corpo = resposta.json()
        self.resultado.rotas[chave] = corpo
        return corpo

    async def varios(self, paths: list[str]) -> list[Any | None]:
        return list(await asyncio.gather(*(self.get(p) for p in paths)))

    async def paginar(self, base: str, page_size: int, filtros: dict[str, Any] | None = None) -> list[dict]:
        """Percorre todas as páginas (`page`, `page_size` e depois os filtros, como no front)."""
        itens: list[dict] = []
        page = 1
        while True:
            corpo = await self.get(f"{base}?{_qs({'page': page, 'page_size': page_size, **(filtros or {})})}")
            if not isinstance(corpo, dict):
                break
            novos = _itens(corpo)
            itens.extend(novos)
            if not novos or page * page_size >= int(corpo.get("total") or 0):
                break
            page += 1
        return itens


async def _coletar(c: _Coletor) -> None:
    # Perfil, uso de IA e dados mestre/gabarito.
    await c.varios([
        "/auth/me",
        "/ia/uso",
        "/sistemas-prediais",
        "/gabarito/tipos-anomalia",
        "/gabarito/tipos-falha",
        "/gabarito/localizacoes",
    ])

    # Responsáveis (lista + detalhe).
    responsaveis = _itens(await c.get("/responsaveis"))
    await c.varios([f"/responsaveis/{r['id']}" for r in responsaveis])

    # Edificações: dashboard (sem query), select de contratos (page_size=100) e tela paginada.
    await c.get("/edificacoes")
    await c.get(f"/edificacoes?{_qs({'page': 1, 'page_size': PAGE_SIZE_SELECT_EDIFICACOES})}")
    edificacoes = await c.paginar("/edificacoes", PAGE_SIZE_TELAS)
    edif_ids = [e["id"] for e in edificacoes]
    await c.varios([f"/edificacoes/{i}" for i in edif_ids] + [f"/edificacoes/{i}/dashboard" for i in edif_ids])

    # Contratos: tela paginada, sem filtro e com cada filtro isolado (valores presentes).
    contratos = await c.paginar("/contratos", PAGE_SIZE_TELAS)
    tipos = sorted({ct["tipo_servico"] for ct in contratos if ct.get("tipo_servico")})
    status = sorted({ct["status"] for ct in contratos if ct.get("status")})
    await asyncio.gather(
        *(c.paginar("/contratos", PAGE_SIZE_TELAS, {"tipo_servico": t}) for t in tipos),
        *(c.paginar("/contratos", PAGE_SIZE_TELAS, {"status": s}) for s in status),
        *(c.paginar("/contratos", PAGE_SIZE_TELAS, {"edificacao_id": e}) for e in edif_ids),
    )
    detalhes = await c.varios([f"/contratos/{ct['id']}" for ct in contratos])

    # Inspeções vêm do detalhe do contrato (não há listagem própria).
    inspecoes = [d["inspecao"] for d in detalhes if isinstance(d, dict) and d.get("inspecao")]
    await asyncio.gather(*(_coletar_inspecao(c, i) for i in inspecoes))


async def _coletar_inspecao(c: _Coletor, inspecao: dict[str, Any]) -> None:
    iid = inspecao["id"]
    tipo = str(inspecao.get("tipo") or "").strip().lower()
    paths = [f"/inspecoes/{iid}", f"/inspecoes/{iid}/relatorios"]
    if tipo:
        # Mesmo `encodeURIComponent(tipo.toLowerCase())` de lib/api-client.ts.
        paths.append(f"/inspecoes/{iid}/conteudo/{quote(tipo, safe=_SEGURO_URI_COMPONENT)}")
    detalhe, *_ = await c.varios(paths)

    visitas = (detalhe or {}).get("visitas") or []
    await c.varios(
        [f"/visitas/{v['id']}{suf}" for v in visitas for suf in ("", "/mao-obra", "/medicoes")]
    )

    # Ocorrências: lista sem filtro, filtros isolados e pares presentes, e detalhe.
    base = f"/inspecoes/{iid}/ocorrencias"
    ocorrencias = _itens(await c.get(base))
    sistemas = sorted({o["sistema_id"] for o in ocorrencias if o.get("sistema_id")})
    graus = sorted({o["grau_risco"] for o in ocorrencias if o.get("grau_risco")})
    pares = sorted({(o["sistema_id"], o["grau_risco"]) for o in ocorrencias if o.get("sistema_id") and o.get("grau_risco")})
    await c.varios(
        [f"{base}?{_qs({'sistema_id': s})}" for s in sistemas]
        + [f"{base}?{_qs({'grau_risco': g})}" for g in graus]
        + [f"{base}?{_qs({'sistema_id': s, 'grau_risco': g})}" for s, g in pares]
        + [f"/ocorrencias/{o['id']}" for o in ocorrencias]
    )


async def coletar_rotas(
    app: FastAPI,
    session_factory: async_sessionmaker[AsyncSession],
    *,
    email_servico: str = EMAIL_SERVICO_PADRAO,
    concorrencia: int = CONCORRENCIA_PADRAO,
) -> ResultadoColeta:
    """Coleta todas as rotas de leitura da equipe usando `session_factory` como banco.

    Sobrescreve `get_db` só durante a coleta (restaurando o override anterior),
    para o app usar o engine do chamador no event loop corrente.
    """
    async with session_factory() as db:
        usuario = await garantir_usuario_servico(db, email_servico)
        token = create_access_token(subject=str(usuario.id))

    async def _get_db():
        async with session_factory() as session:
            yield session

    anterior = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = _get_db
    try:
        # Um 500 numa rota vira falha registrada (fora do snapshot), sem abortar a coleta.
        transporte = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(
            transport=transporte,
            base_url="http://snapshot",
            headers={"Authorization": f"Bearer {token}"},
            timeout=120,
        ) as client:
            coletor = _Coletor(client, concorrencia)
            await _coletar(coletor)
    finally:
        if anterior is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = anterior
    return coletor.resultado
