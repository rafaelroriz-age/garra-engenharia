"""Download de arquivos do storage local por token assinado (DEC-57, P6).

Sem JWT: o token HMAC-SHA256 (chave derivada de `JWT_SECRET_KEY`, com expiração)
é a autorização, como uma URL pré-assinada do S3. Só funciona com
`STORAGE_PROVEDOR=local`.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from app.services.storage import StorageClient, get_storage_client
from app.services.storage.local_client import (
    LocalStorageClient,
    content_type_da_chave,
    validar_token,
)

router = APIRouter(prefix="/api/v1/arquivos", tags=["arquivos"])


@router.get("/{token}", include_in_schema=False)
async def baixar_arquivo(
    token: str, storage: StorageClient = Depends(get_storage_client)
) -> FileResponse:
    if not isinstance(storage, LocalStorageClient):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Arquivo não encontrado.")
    chave = validar_token(token)
    if chave is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Link inválido ou expirado.")
    try:
        caminho = storage.caminho_para_download(chave)
    except ValueError:  # chave fora da raiz (token assinado com chave maliciosa)
        caminho = None
    if caminho is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Arquivo não encontrado.")
    # S3 não definia Content-Disposition (o navegador exibe inline); mantém o mesmo comportamento.
    return FileResponse(
        caminho,
        filename=caminho.name,
        media_type=content_type_da_chave(chave),
        content_disposition_type="inline",
        headers={
            "Cache-Control": "private, no-store",
            "Content-Security-Policy": "frame-ancestors 'none'",
        },
    )
