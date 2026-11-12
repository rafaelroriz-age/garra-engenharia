"""Service Layer de `Foto` (BL-11, RF-05, RNF-02 parcial, mitigações A08/A10 OWASP).

Todo upload (arquivo ou clipboard base64) passa por `app.services.image_processing`
antes de chegar ao `StorageClient` — nunca persiste o arquivo original sem
reprocessamento. Uploads nunca aceitam URL fornecida pelo cliente (A10).
"""
import base64
import binascii
import re
import time
import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import ConflictError, DomainError, NotFoundError
from app.models import Foto, Ocorrencia, Usuario, Visita
from app.repositories import foto_repository
from app.services import image_processing, prompt_ia_service
from app.services.legenda_ia import LegendaIAClient, montar_contexto, telemetria
from app.services.storage.base import StorageClient
from app.services.storage.s3_client import MAX_UPLOAD_SIZE_BYTES, ObjectNotFoundError

_PRESIGNED_URL_EXPIRES_IN_SECONDS = 15 * 60

# Nome do prompt-sistema de legenda em `prompts_ia` (BL-34); a versão ativa é a usada (DP-2).
PROMPT_LEGENDA_IA_NOME = "legenda_foto"
STATUS_RASCUNHO = "rascunho"
STATUS_APROVADA = "aprovada"

# Chave emitida pelo servidor em `_processar_e_enviar` (DEC-39 A). `fullmatch` + UUID canônico
# impede `../`, caminho absoluto, outro prefixo e chaves de outros objetos do bucket.
_STORAGE_KEY_PATTERN = re.compile(
    r"fotos/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.(?:jpg|png|webp)"
)


def _validar_storage_key(storage_key: str) -> None:
    """Aceita apenas chaves no formato emitido pelo upload do servidor (A01)."""
    if not _STORAGE_KEY_PATTERN.fullmatch(storage_key):
        raise DomainError(
            "storage_key inválida: use a chave devolvida por /fotos/upload ou /fotos/upload-clipboard.",
            type_suffix="storage-key-invalida",
            title="Foto inválida",
        )


async def _validar_chave_para_vinculo(db: AsyncSession, storage_key: str, storage: StorageClient) -> None:
    """Chave no padrão do servidor, existente no bucket e ainda não vinculada (DEC-39 A)."""
    _validar_storage_key(storage_key)
    if not storage.exists(storage_key):
        raise DomainError(
            "O arquivo informado não existe no storage; envie-o antes de vincular.",
            type_suffix="storage-key-inexistente",
            title="Foto inválida",
        )
    if await foto_repository.get_by_storage_key(db, storage_key) is not None:
        raise ConflictError(
            "Esta foto já está vinculada a outro registro.", type_suffix="storage-key-ja-vinculada"
        )


def _validar_tamanho(conteudo: bytes) -> None:
    if not conteudo:
        raise DomainError(
            "O arquivo enviado está vazio.", type_suffix="arquivo-vazio", title="Foto inválida"
        )
    if len(conteudo) > MAX_UPLOAD_SIZE_BYTES:
        raise DomainError(
            f"Arquivo de {len(conteudo)} bytes excede o limite máximo de {MAX_UPLOAD_SIZE_BYTES} bytes.",
            type_suffix="arquivo-excede-tamanho-maximo",
            title="Foto inválida",
        )


async def _processar_e_enviar(conteudo: bytes, storage: StorageClient) -> tuple[str, str]:
    """Reprocessa (Pillow, A08) e envia ao storage. Retorna `(storage_key, url_presignada)`."""
    _validar_tamanho(conteudo)
    conteudo_recodificado, extensao, content_type = image_processing.reprocessar_imagem(conteudo)

    storage_key = f"fotos/{uuid.uuid4()}.{extensao}"
    storage.upload(storage_key, conteudo_recodificado, content_type=content_type)
    url = storage.generate_presigned_url(storage_key, expires_in=_PRESIGNED_URL_EXPIRES_IN_SECONDS)
    return storage_key, url


async def upload_arquivo(conteudo: bytes, storage: StorageClient) -> tuple[str, str]:
    """Upload manual (multipart) — Opção B da Seção 6 de `00_docs/arquitetura.md`."""
    return await _processar_e_enviar(conteudo, storage)


async def upload_clipboard(imagem_base64: str, storage: StorageClient) -> tuple[str, str]:
    """Upload via clipboard paste (base64) — Opção A da Seção 6 de `00_docs/arquitetura.md`."""
    try:
        conteudo = base64.b64decode(imagem_base64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise DomainError(
            "Conteúdo base64 inválido.", type_suffix="base64-invalido", title="Foto inválida"
        ) from exc
    return await _processar_e_enviar(conteudo, storage)


async def vincular_a_ocorrencia(
    db: AsyncSession, ocorrencia_id: uuid.UUID, storage: StorageClient, *, storage_key: str,
    legenda: str | None, ordem: int | None, origem: str, criado_por_id: uuid.UUID | None = None,
) -> Foto:
    ocorrencia = await db.get(Ocorrencia, ocorrencia_id)
    if ocorrencia is None:
        raise NotFoundError(
            f"Ocorrência '{ocorrencia_id}' não encontrada.", type_suffix="ocorrencia-nao-encontrada"
        )
    await _validar_chave_para_vinculo(db, storage_key, storage)
    return await foto_repository.create(
        db,
        storage_key=storage_key,
        legenda=legenda,
        ordem=ordem,
        origem=origem,
        ocorrencia_id=ocorrencia_id,
        criado_por_id=criado_por_id,
    )


async def vincular_a_visita(
    db: AsyncSession, visita_id: uuid.UUID, storage: StorageClient, *, storage_key: str,
    legenda: str | None, ordem: int | None, origem: str, criado_por_id: uuid.UUID | None = None,
) -> Foto:
    visita = await db.get(Visita, visita_id)
    if visita is None:
        raise NotFoundError(f"Visita '{visita_id}' não encontrada.", type_suffix="visita-nao-encontrada")
    await _validar_chave_para_vinculo(db, storage_key, storage)
    return await foto_repository.create(
        db,
        storage_key=storage_key,
        legenda=legenda,
        ordem=ordem,
        origem=origem,
        visita_id=visita_id,
        criado_por_id=criado_por_id,
    )


def _invalidar_aprovacao(foto: Foto) -> None:
    foto.status_validacao_ia = STATUS_RASCUNHO
    foto.aprovado_por_id = None
    foto.aprovado_em = None


async def atualizar(
    db: AsyncSession, foto_id: uuid.UUID, campos: dict, *, usuario: Usuario | None = None
) -> Foto:
    """Atualiza só os campos presentes em `campos` (`legenda`/`ordem`); `legenda: None` limpa (DP-5).

    Com `aprovar_legenda_ia=True`, aprova a sugestão de IA (DEC-37 DP-3): `legenda` recebe o
    texto enviado ou, se ausente, a própria sugestão; `aprovado_por_id`/`aprovado_em` vêm de
    `usuario` (token), nunca do payload. Sem aprovação, os campos de IA não mudam.
    """
    foto = await foto_repository.get_by_id(db, foto_id)
    if foto is None:
        raise NotFoundError(f"Foto '{foto_id}' não encontrada.", type_suffix="foto-nao-encontrada")
    campos = dict(campos)
    if campos.pop("aprovar_legenda_ia", False):
        if usuario is None:
            raise ValueError("A aprovação exige o usuário autenticado.")
        if foto.status_validacao_ia is None:
            raise DomainError(
                "A foto não tem sugestão de legenda por IA para aprovar.",
                type_suffix="legenda-ia-sem-sugestao", title="Aprovação inválida",
            )
        legenda = campos["legenda"] if "legenda" in campos else foto.legenda_ia_sugerida
        if not (legenda or "").strip():
            raise DomainError(
                "A legenda aprovada não pode ser vazia.",
                type_suffix="legenda-aprovada-vazia", title="Aprovação inválida",
            )
        campos["legenda"] = legenda
        foto.status_validacao_ia = STATUS_APROVADA
        foto.aprovado_por_id = usuario.id
        foto.aprovado_em = datetime.now(UTC)
    elif (
        "legenda" in campos
        and foto.status_validacao_ia == STATUS_APROVADA
        and campos["legenda"] != foto.legenda
    ):
        # DEC-42 B: mudar a legenda aprovada invalida a aprovação (fecha DP-10 de DEC-37).
        _invalidar_aprovacao(foto)
    return await foto_repository.update(db, foto, campos)


async def gerar_legenda_ia(
    db: AsyncSession, foto_id: uuid.UUID, storage: StorageClient, cliente: LegendaIAClient,
    campos: dict, usuario_id: uuid.UUID | None = None,
) -> Foto:
    """Gera a sugestão de legenda por IA (BL-34; DEC-37 DP-2, DP-4; RN-16, RN-17).

    Escreve apenas os campos de sugestão (`legenda_ia_sugerida`, `legenda_bruta` se enviada em
    `campos`, alertas/pendências, prompt e hash, instante) e põe `status_validacao_ia` em
    `rascunho`. Nunca altera `legenda` nem os campos de aprovação.

    Telemetria e cache local (R-10): a mesma entrada (prompt, modelo, contexto) dentro do TTL
    reaproveita o último resultado de sucesso sem chamar a API; cada geração vira uma linha em
    `chamadas_ia` (origem `api` ou `cache_local`; erro do provedor também é registrado e relançado).
    """
    foto = await foto_repository.get_by_id(db, foto_id)
    if foto is None:
        raise NotFoundError(f"Foto '{foto_id}' não encontrada.", type_suffix="foto-nao-encontrada")
    prompt = await prompt_ia_service.obter_ativo(db, PROMPT_LEGENDA_IA_NOME)
    enviar_imagem = bool(getattr(cliente, "enviar_imagem", False))  # DEEPSEEK_ENVIAR_IMAGEM=true; senão só texto
    legenda_bruta = campos["legenda_bruta"] if "legenda_bruta" in campos else foto.legenda_bruta
    contexto = await montar_contexto(db, foto, legenda_bruta)

    settings = get_settings()
    provedor = settings.legenda_ia_provedor
    modelo = settings.deepseek_modelo if provedor == "deepseek" else "fake"
    prompt_hash = prompt_ia_service.calcular_hash(prompt.conteudo)
    # Em modo imagem o resultado também depende da foto (storage_key é único e imutável).
    chave = telemetria.chave_cache(
        prompt_hash, modelo, contexto, extra=f"imagem:{foto.storage_key}" if enviar_imagem else "texto"
    )
    comum = dict(
        chave=chave, provedor=provedor, usuario_id=usuario_id, foto_id=foto.id,
        prompt_ia_id=prompt.id, prompt_conteudo_hash=prompt_hash,
    )

    resultado = await telemetria.buscar_em_cache(db, chave, settings.legenda_ia_cache_ttl_h)
    if resultado is not None:
        await telemetria.registrar(
            db, origem="cache_local", sucesso=True, modelo=resultado.modelo or modelo,
            modo=resultado.modo, latencia_ms=0, commit=False, **comum,
        )
    else:
        imagem: bytes | None = None
        if enviar_imagem:
            try:
                imagem = storage.download(foto.storage_key)
            except ObjectNotFoundError as exc:
                raise DomainError(
                    "O arquivo da foto não existe no storage.", type_suffix="storage-key-inexistente",
                    title="Foto inválida",
                ) from exc
        inicio = time.perf_counter()
        try:
            resultado = await cliente.gerar_legenda(contexto, prompt.conteudo, imagem)
        except Exception as exc:
            # Só o tipo do erro: sem mensagem (pode ecoar conteúdo) e sem chave.
            await telemetria.registrar(
                db, origem="api", sucesso=False, modelo=modelo, modo="imagem" if enviar_imagem else "texto",
                latencia_ms=round((time.perf_counter() - inicio) * 1000),
                erro_tipo=(getattr(exc, "type_suffix", None) or type(exc).__name__)[:100], **comum,
            )
            raise
        await telemetria.registrar(
            db, origem="api", sucesso=True, modelo=resultado.modelo or modelo, modo=resultado.modo,
            latencia_ms=round((time.perf_counter() - inicio) * 1000), uso=resultado.uso,
            precos=telemetria.Precos.de_settings(settings), resultado=resultado, commit=False, **comum,
        )

    if "legenda_bruta" in campos:
        foto.legenda_bruta = legenda_bruta
    foto.legenda_ia_sugerida = resultado.legenda_sugerida
    foto.alertas_ia = list(resultado.alertas)
    foto.pendencias_ia = list(resultado.pendencias)
    foto.nivel_certeza_ia = resultado.nivel_certeza
    foto.prompt_ia_id = prompt.id
    foto.prompt_conteudo_hash = prompt_hash
    foto.legenda_ia_gerada_em = datetime.now(UTC)
    _invalidar_aprovacao(foto)  # DEC-42 B: regerar volta a rascunho e zera a aprovação
    await db.commit()
    await db.refresh(foto)
    return foto


async def remover(db: AsyncSession, foto_id: uuid.UUID, storage: StorageClient) -> None:
    foto = await foto_repository.get_by_id(db, foto_id)
    if foto is None:
        raise NotFoundError(f"Foto '{foto_id}' não encontrada.", type_suffix="foto-nao-encontrada")
    storage.delete(foto.storage_key)
    await foto_repository.delete(db, foto)


async def descartar_upload(db: AsyncSession, storage_key: str, storage: StorageClient) -> None:
    """Descarta um upload que nunca foi vinculado (DEC-39 D); recusa chave já vinculada a uma `Foto`."""
    _validar_storage_key(storage_key)
    if await foto_repository.get_by_storage_key(db, storage_key) is not None:
        raise ConflictError(
            "A foto já está vinculada; remova-a por DELETE /fotos/{id}.",
            type_suffix="storage-key-ja-vinculada",
        )
    storage.delete(storage_key)
