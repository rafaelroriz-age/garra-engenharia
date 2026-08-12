"""Seed de dados de pior caso para o benchmark de geração de Relatório (BL-22).

Cria 1 Edificação + 1 Responsável (fiscal) + 1 Contrato (`tipo_servico="RFO"`)
+ 1 Inspeção + N Visitas (mão de obra, medições, fotos reais no MinIO) —
volume equivalente ao pior caso da RNF-06 (até 200 páginas, 150+ fotos).

Fotos são sintéticas (geradas via Pillow, não fotos reais de campo) para não
depender de nenhum arquivo do cliente; o tamanho/resolução default (2400x1800,
qualidade 85) simula uma foto de câmera de celular já comprimida pelo próprio
telefone e ainda SEM nenhum redimensionamento — reflete o que
`app.services.image_processing` (BL-11) de fato armazena hoje (recodifica mas
não redimensiona).

Idempotente por reset explícito: rode com `--reset` para apagar uma execução
anterior deste benchmark antes de semear de novo (identifica os próprios
registros pelo nome fixo da Edificação, não mexe em nenhum outro dado).

Uso:
    cd 04_backend
    python -m app.scripts.seed_benchmark_rfo --visitas 55 --fotos-por-visita 3 --reset
"""
from __future__ import annotations

import argparse
import asyncio
import io
import logging
import uuid
from datetime import date, timedelta

from PIL import Image, ImageDraw
from sqlalchemy import delete, select

from app.core.database import AsyncSessionLocal
from app.models import (
    Contrato,
    Edificacao,
    Foto,
    Inspecao,
    Relatorio,
    Responsavel,
    Visita,
    VisitaMaoObra,
    VisitaMedicao,
)
from app.services.storage.s3_client import S3StorageClient

logger = logging.getLogger(__name__)

EDIFICACAO_NOME = "Obra Benchmark RNF-06 (BL-22)"
FUNCOES = ["Pedreiro", "Servente", "Eletricista", "Encanador", "Mestre de Obra"]

SERVICOS_EXECUTADOS = (
    "Execução de impermeabilização da laje de cobertura, aplicação de manta "
    "asfáltica em duas camadas cruzadas, tratamento de juntas de dilatação e "
    "reforço de rodapés. Equipe organizada em duas frentes de trabalho, uma "
    "por torre, com acompanhamento técnico integral do fiscal responsável."
)
OBSERVACOES = (
    "Sem intercorrências relevantes na visita. Clima favorável à aplicação de "
    "manta asfáltica (sem chuva registrada nas últimas 24 horas). Recomenda-se "
    "manter o ritmo atual de execução para cumprir o prazo contratual firmado."
)


def _gerar_foto_sintetica(indice: int, largura: int, altura: int, qualidade: int) -> bytes:
    """Gera uma imagem JPEG sintética (não é uma foto real de campo).

    Usa formas/gradiente (não ruído aleatório puro) para que a taxa de
    compressão JPEG resultante seja realista — ruído aleatório comprime mal e
    infla artificialmente o tamanho do arquivo.
    """
    cor_base = (40 + (indice * 17) % 180, 60 + (indice * 11) % 150, 90 + (indice * 7) % 120)
    imagem = Image.new("RGB", (largura, altura), color=cor_base)
    desenho = ImageDraw.Draw(imagem)
    passo = max(30, largura // 40)
    for x in range(0, largura, passo):
        desenho.line([(x, 0), (max(0, x - altura), altura)], fill=(220, 220, 220), width=2)
    desenho.rectangle(
        [largura * 0.08, altura * 0.08, largura * 0.92, altura * 0.92],
        outline=(255, 210, 0),
        width=8,
    )
    desenho.text((30, 30), f"Foto benchmark #{indice}", fill=(255, 255, 255))
    buffer = io.BytesIO()
    imagem.save(buffer, format="JPEG", quality=qualidade)
    return buffer.getvalue()


async def _limpar_execucao_anterior(db) -> None:
    """Remove os registros de uma execução anterior deste benchmark, se houver."""
    edificacao = (
        await db.execute(select(Edificacao).where(Edificacao.nome == EDIFICACAO_NOME))
    ).scalar_one_or_none()
    if edificacao is None:
        return

    contrato = (
        await db.execute(select(Contrato).where(Contrato.edificacao_id == edificacao.id))
    ).scalar_one_or_none()
    if contrato is not None:
        inspecao = (
            await db.execute(select(Inspecao).where(Inspecao.contrato_id == contrato.id))
        ).scalar_one_or_none()
        if inspecao is not None:
            await db.execute(delete(Relatorio).where(Relatorio.inspecao_id == inspecao.id))
            visita_ids = list(
                (
                    await db.execute(select(Visita.id).where(Visita.inspecao_id == inspecao.id))
                ).scalars()
            )
            if visita_ids:
                await db.execute(delete(Foto).where(Foto.visita_id.in_(visita_ids)))
                await db.execute(delete(VisitaMaoObra).where(VisitaMaoObra.visita_id.in_(visita_ids)))
                await db.execute(delete(VisitaMedicao).where(VisitaMedicao.visita_id.in_(visita_ids)))
                await db.execute(delete(Visita).where(Visita.id.in_(visita_ids)))
            await db.execute(delete(Inspecao).where(Inspecao.id == inspecao.id))
        await db.execute(delete(Contrato).where(Contrato.id == contrato.id))
    await db.execute(delete(Edificacao).where(Edificacao.id == edificacao.id))
    await db.commit()
    logger.info("Execução anterior do benchmark removida.")


async def seed(
    n_visitas: int,
    fotos_por_visita: int,
    largura: int,
    altura: int,
    qualidade: int,
    reset: bool,
) -> uuid.UUID:
    storage = S3StorageClient()

    async with AsyncSessionLocal() as db:
        if reset:
            await _limpar_execucao_anterior(db)

        edificacao = Edificacao(
            nome=EDIFICACAO_NOME,
            endereco="Rua Benchmark, s/n - Aparecida de Goiânia/GO",
            tipologia="comercial",
            sistema_construtivo="concreto armado",
            area_total_m2=1200.0,
        )
        db.add(edificacao)
        await db.flush()

        fiscal = Responsavel(
            nome="Eng. Civil Esp. Roniel Ribeiro Costa", tipo="fiscal", crea="1020613386D-GO"
        )
        db.add(fiscal)
        await db.flush()

        contrato = Contrato(
            edificacao_id=edificacao.id,
            fiscal_id=fiscal.id,
            numero="BENCH-001/2026",
            tipo_servico="RFO",
            objeto="Fiscalização de obra — dados sintéticos gerados para o benchmark de RNF-06 (BL-22).",
            data_inicio=date(2026, 1, 5),
            prazo_dias=n_visitas * 3,
            art_fiscalizacao="0000000000000000",
            observacoes_gerais="Contrato gerado exclusivamente para o benchmark de RNF-06 (BL-22).",
            status="em_andamento",
        )
        db.add(contrato)
        await db.flush()

        inspecao = Inspecao(contrato_id=contrato.id, tipo="RFO", status="em_andamento")
        db.add(inspecao)
        await db.flush()

        foto_indice = 0
        for seq in range(1, n_visitas + 1):
            visita = Visita(
                inspecao_id=inspecao.id,
                data=contrato.data_inicio + timedelta(days=seq * 3),
                servicos_executados=SERVICOS_EXECUTADOS,
                observacoes=OBSERVACOES,
                seq_numero=seq,
            )
            db.add(visita)
            await db.flush()

            for funcao in FUNCOES[: 3 + (seq % 2)]:
                db.add(VisitaMaoObra(visita_id=visita.id, funcao=funcao, quantidade=1 + seq % 3))

            db.add(
                VisitaMedicao(
                    visita_id=visita.id, descricao="Manta asfáltica aplicada", quantidade=45.5, unidade="m²"
                )
            )
            db.add(
                VisitaMedicao(
                    visita_id=visita.id, descricao="Rodapés tratados", quantidade=12.0, unidade="m"
                )
            )

            for _ in range(fotos_por_visita):
                foto_indice += 1
                conteudo = _gerar_foto_sintetica(foto_indice, largura, altura, qualidade)
                storage_key = f"fotos/benchmark/{uuid.uuid4()}.jpg"
                storage.upload(storage_key, conteudo, content_type="image/jpeg")
                db.add(
                    Foto(
                        visita_id=visita.id,
                        storage_key=storage_key,
                        legenda=f"Vista geral da impermeabilização — Visita {seq}, foto {foto_indice}.",
                        origem="upload_manual",
                        ordem=foto_indice,
                    )
                )

        await db.commit()
        logger.info(
            "Seed de benchmark concluído: %s visitas, %s fotos (%sx%s, qualidade %s).",
            n_visitas,
            foto_indice,
            largura,
            altura,
            qualidade,
        )
        return inspecao.id


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--visitas", type=int, default=55, help="Número de visitas a gerar")
    parser.add_argument("--fotos-por-visita", type=int, default=3, help="Fotos por visita")
    parser.add_argument("--largura", type=int, default=2400, help="Largura (px) da foto sintética")
    parser.add_argument("--altura", type=int, default=1800, help="Altura (px) da foto sintética")
    parser.add_argument("--qualidade", type=int, default=85, help="Qualidade JPEG (1-95) da foto sintética")
    parser.add_argument("--reset", action="store_true", help="Apaga uma execução anterior antes de semear")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    inspecao_id = asyncio.run(
        seed(args.visitas, args.fotos_por_visita, args.largura, args.altura, args.qualidade, args.reset)
    )
    print(f"INSPECAO_ID={inspecao_id}")


if __name__ == "__main__":
    main()
