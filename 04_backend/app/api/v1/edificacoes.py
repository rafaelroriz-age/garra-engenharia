"""Endpoints de Edificação (BL-08, RF-01, `00_docs/arquitetura.md` Seção 4).

- `GET /edificacoes` — lista paginada, filtro por nome/endereço.
- `POST /edificacoes` — cria edificação.
- `GET /edificacoes/{id}` — detalhe com histórico de contratos vinculados.
- `PUT /edificacoes/{id}` — atualiza edificação.
- `POST /edificacoes/{id}/documentos` — upload de documento técnico (DEC-16, RF-01).

Leitura liberada à equipe (`auditor`/`auxiliar`); escrita restrita ao `auditor`
(RN-18, DEC-27) — nenhuma rota aceita apenas "estar autenticado", para que um
usuário do Portal do Cliente não alcance dados internos (OWASP A01).
"""
import uuid

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_auditor, require_equipe
from app.core.database import get_db
from app.core.errors import DomainError
from app.models import Edificacao, Usuario
from app.schemas.common import PaginatedResponse
from app.schemas.edificacao import (
    EdificacaoComContratos,
    EdificacaoCreate,
    EdificacaoRead,
    EdificacaoUpdate,
)
from app.services import edificacao_service
from app.services.storage import get_storage_client
from app.services.storage.base import StorageClient

router = APIRouter(prefix="/api/v1/edificacoes", tags=["edificacoes"])

_MAX_DOCUMENTO_SIZE_BYTES = 25 * 1024 * 1024


@router.get("", response_model=PaginatedResponse[EdificacaoRead])
async def listar_edificacoes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    nome: str | None = Query(None),
    endereco: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(require_equipe),
) -> PaginatedResponse:
    """Lista edificações paginadas, com filtro opcional por nome e/ou endereço."""
    items, total = await edificacao_service.listar(
        db, page=page, page_size=page_size, nome=nome, endereco=endereco
    )
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=EdificacaoRead, status_code=status.HTTP_201_CREATED)
async def criar_edificacao(
    dados: EdificacaoCreate,
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(require_auditor),
) -> Edificacao:
    """Cria uma nova edificação (RF-01)."""
    return await edificacao_service.criar(db, dados)


@router.get("/{edificacao_id}", response_model=EdificacaoComContratos)
async def obter_edificacao(
    edificacao_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(require_equipe),
) -> Edificacao:
    """Detalhe da edificação com o histórico de contratos vinculados."""
    return await edificacao_service.obter_por_id(db, edificacao_id)


@router.put("/{edificacao_id}", response_model=EdificacaoRead)
async def atualizar_edificacao(
    edificacao_id: uuid.UUID,
    dados: EdificacaoUpdate,
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(require_auditor),
) -> Edificacao:
    """Atualiza os dados de uma edificação existente."""
    return await edificacao_service.atualizar(db, edificacao_id, dados)


@router.post("/{edificacao_id}/documentos", response_model=EdificacaoRead, status_code=status.HTTP_201_CREATED)
async def enviar_documento_tecnico(
    edificacao_id: uuid.UUID,
    arquivo: UploadFile = File(...),
    tipo: str = Form(...),
    db: AsyncSession = Depends(get_db),
    storage: StorageClient = Depends(get_storage_client),
    _usuario: Usuario = Depends(require_auditor),
) -> Edificacao:
    """Envia um documento técnico (projeto, ART) e o anexa a `documentos_tecnicos` (DEC-16)."""
    edificacao = await edificacao_service.obter_por_id(db, edificacao_id)

    conteudo = await arquivo.read()
    if not conteudo:
        raise DomainError(
            "O arquivo enviado está vazio.",
            type_suffix="documento-vazio",
            title="Documento técnico inválido",
        )
    if len(conteudo) > _MAX_DOCUMENTO_SIZE_BYTES:
        raise DomainError(
            f"O arquivo excede o limite máximo de {_MAX_DOCUMENTO_SIZE_BYTES} bytes.",
            type_suffix="documento-excede-tamanho-maximo",
            title="Documento técnico inválido",
        )

    storage_key = f"edificacoes/{edificacao_id}/documentos/{uuid.uuid4()}-{arquivo.filename}"
    storage.upload(storage_key, conteudo, content_type=arquivo.content_type or "application/octet-stream")

    documentos_atuais = edificacao.documentos_tecnicos or {}
    lista_documentos = list(documentos_atuais.get("itens", []))
    lista_documentos.append({"nome": arquivo.filename, "tipo": tipo, "storage_key": storage_key})

    edificacao.documentos_tecnicos = {"itens": lista_documentos}
    await db.commit()
    await db.refresh(edificacao)
    return edificacao
