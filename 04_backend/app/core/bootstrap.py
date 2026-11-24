"""Seeds no boot e verificação do storage local (go-live no Render, T110 / DEC-59).

O Render não oferece Pre-Deploy Command no plano usado, então, além das migrations
(`RUN_MIGRATIONS_ON_STARTUP`), os seeds idempotentes podem rodar no boot com
`SEED_ON_STARTUP=true`:

- gabarito de dados mestre (`seed_gabarito`, usa o JSON embutido em `app/data/`);
- usuário auditor administrativo (`seed_admin.criar_admin`), só se `ADMIN_SENHA`
  estiver definida. Criar o admin antes de servir tráfego fecha a janela em que o
  primeiro `POST /api/v1/auth/register` (aberto com o banco sem usuários) viraria auditor.
"""
import logging
import os
import tempfile
from pathlib import Path

from app.core.config import Settings

logger = logging.getLogger(__name__)


async def semear_no_boot(settings: Settings) -> None:
    """Roda os seeds idempotentes. Erros sobem: o boot falha em vez de servir sem dados mestre."""
    from app.core.database import AsyncSessionLocal
    from app.scripts.seed_admin import criar_admin
    from app.scripts.seed_gabarito import seed_gabarito

    async with AsyncSessionLocal() as session:
        resumo = await seed_gabarito(session)
    logger.info("Seed do gabarito no boot: %s", resumo)

    if settings.admin_senha is None or not settings.admin_senha.get_secret_value():
        logger.warning("SEED_ON_STARTUP: ADMIN_SENHA não definida, admin não semeado.")
        return
    mensagem = await criar_admin(
        settings.admin_email, settings.admin_senha.get_secret_value(), settings.admin_nome
    )
    logger.info("Seed do admin no boot: %s", mensagem)


def verificar_storage_local(settings: Settings) -> str:
    """`ok` se `STORAGE_LOCAL_DIR` existe (ou pode ser criado) e aceita escrita.

    Retorna `nao_verificado` para o provedor s3 (evita chamada de rede no healthcheck)
    e `unavailable` quando o diretório não pode ser criado ou gravado (ex.: disco do
    Render montado sem permissão para o usuário `appuser` do Dockerfile.render).
    """
    if settings.storage_provedor != "local":
        return "nao_verificado"
    raiz = Path(settings.storage_local_dir).resolve()
    try:
        raiz.mkdir(parents=True, exist_ok=True)
        fd, caminho = tempfile.mkstemp(dir=raiz, prefix=".health-")
        os.close(fd)
        os.unlink(caminho)
    except OSError:
        logger.exception("Storage local indisponível para escrita em %s", raiz)
        return "unavailable"
    return "ok"
