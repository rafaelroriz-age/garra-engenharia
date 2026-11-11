"""Repository de `Foto` (BL-11, RF-05, RN-03, RN-11)."""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Foto


async def get_by_id(db: AsyncSession, foto_id: uuid.UUID) -> Foto | None:
    result = await db.execute(select(Foto).where(Foto.id == foto_id))
    return result.scalar_one_or_none()


async def get_by_storage_key(db: AsyncSession, storage_key: str) -> Foto | None:
    result = await db.execute(select(Foto).where(Foto.storage_key == storage_key).limit(1))
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
    await db.commit()
    await db.refresh(foto)
    return foto


async def update(db: AsyncSession, foto: Foto, campos: dict) -> Foto:
    """Aplica apenas as chaves presentes em `campos` (`legenda`, `ordem`); `None` explícito limpa o campo."""
    for nome in ("legenda", "ordem"):
        if nome in campos:
            setattr(foto, nome, campos[nome])
    await db.commit()
    await db.refresh(foto)
    return foto


async def delete(db: AsyncSession, foto: Foto) -> None:
    await db.delete(foto)
    await db.commit()
