"""Repository de `Foto` (BL-11, RF-05, RN-03, RN-11)."""
import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError
from app.models import Foto


async def get_by_id(db: AsyncSession, foto_id: uuid.UUID) -> Foto | None:
    result = await db.execute(select(Foto).where(Foto.id == foto_id))
    return result.scalar_one_or_none()


async def create(
    db: AsyncSession,
    *,
    storage_key: str,
    legenda: str | None,
    ordem: int | None,
    origem: str,
    ocorrencia_id: uuid.UUID | None = None,
    visita_id: uuid.UUID | None = None,
    url_publica: str | None = None,
    criado_por_id: uuid.UUID | None = None,
) -> Foto:
    foto = Foto(
        storage_key=storage_key,
        legenda=legenda,
        ordem=ordem,
        origem=origem,
        ocorrencia_id=ocorrencia_id,
        visita_id=visita_id,
        url_publica=url_publica,
        criado_por_id=criado_por_id,
    )
    db.add(foto)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        if "uq_fotos_storage_key" in str(exc.orig):
            raise ConflictError(
                f"A chave de armazenamento '{storage_key}' já está vinculada a outra foto.",
                type_suffix="storage-key-ja-vinculada",
            ) from exc
        raise
    await db.refresh(foto)
    return foto


async def update(db: AsyncSession, foto: Foto, *, legenda: str | None, ordem: int | None) -> Foto:
    if legenda is not None:
        foto.legenda = legenda
    if ordem is not None:
        foto.ordem = ordem
    await db.commit()
    await db.refresh(foto)
    return foto


async def delete(db: AsyncSession, foto: Foto) -> None:
    await db.delete(foto)
    await db.commit()
