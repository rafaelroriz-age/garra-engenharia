"""Benchmark de geração de PDF/DOCX do RFO — BL-22 (RNF-06, R-03).

Mede, com dados reais no Postgres/MinIO (ver `app.scripts.seed_benchmark_rfo`),
o tempo de geração de PDF (WeasyPrint) e DOCX (docxtpl) SEPARADAMENTE, do
carregamento dos dados/fotos até a escrita do arquivo final — incluindo o
tempo de leitura das fotos no MinIO — em dois cenários:

  * "sem_otimizacao": fotos embutidas na resolução/tamanho originais (o que o
    pipeline de upload de fotos, BL-11, de fato armazena hoje).
  * "otimizado": fotos redimensionadas/recomprimidas antes de compor o
    documento (`app.services.report_generator.rfo_pipeline.otimizar_imagem`).

Ao final, cria/atualiza um registro `Relatorio` real (status `concluido`,
`pdf_key`/`docx_key` apontando para os arquivos gerados no cenário
"otimizado", já enviados de volta ao MinIO) — reproduzindo o critério de
aceite descrito no prompt de benchmark (RELATORIO.status = concluido).

Uso:
    cd 04_backend
    python -m app.scripts.benchmark_relatorio_geracao --inspecao-id <uuid>
"""
from __future__ import annotations

import argparse
import asyncio
import json
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import AsyncSessionLocal
from app.models import Contrato, Inspecao, Relatorio, Visita
from app.services.report_generator import rfo_pipeline
from app.services.storage.s3_client import S3StorageClient

REPO_ROOT = Path(__file__).resolve().parents[3]
SAIDA_DIR = REPO_ROOT / "tmp_benchmark"

# Relatórios finais (PDF/DOCX) são legitimamente maiores que uma única foto —
# o limite de `S3StorageClient` (25 MB, pensado para fotos individuais, BL-07)
# não se aplica aqui. 150 MB é uma folga generosa para o pior caso de RNF-06.
RELATORIO_MAX_UPLOAD_SIZE_BYTES = 150 * 1024 * 1024


async def _carregar_contexto(inspecao_id: uuid.UUID) -> tuple[dict, list[str]]:
    async with AsyncSessionLocal() as db:
        inspecao = (
            await db.execute(
                select(Inspecao)
                .where(Inspecao.id == inspecao_id)
                .options(
                    selectinload(Inspecao.contrato).selectinload(Contrato.edificacao),
                    selectinload(Inspecao.contrato).selectinload(Contrato.fiscal),
                    selectinload(Inspecao.visitas).selectinload(Visita.mao_obra),
                    selectinload(Inspecao.visitas).selectinload(Visita.medicoes),
                    selectinload(Inspecao.visitas).selectinload(Visita.fotos),
                )
            )
        ).scalar_one()

        contrato = inspecao.contrato
        visitas_ctx = []
        storage_keys: list[str] = []
        for visita in sorted(inspecao.visitas, key=lambda v: v.seq_numero):
            fotos_ctx = []
            for foto in sorted(visita.fotos, key=lambda f: f.ordem or 0):
                fotos_ctx.append({"storage_key": foto.storage_key, "legenda": foto.legenda})
                storage_keys.append(foto.storage_key)
            visitas_ctx.append(
                {
                    "seq_numero": visita.seq_numero,
                    "data": visita.data.isoformat(),
                    "servicos_executados": visita.servicos_executados,
                    "observacoes": visita.observacoes,
                    "mao_obra": [{"funcao": m.funcao, "quantidade": m.quantidade} for m in visita.mao_obra],
                    "medicoes": [
                        {"descricao": m.descricao, "quantidade": m.quantidade, "unidade": m.unidade}
                        for m in visita.medicoes
                    ],
                    "fotos": fotos_ctx,
                }
            )

        contexto = {
            "contrato": {
                "numero": contrato.numero,
                "tipo_servico": contrato.tipo_servico,
                "objeto": contrato.objeto,
                "art_fiscalizacao": contrato.art_fiscalizacao,
            },
            "edificacao": {"nome": contrato.edificacao.nome, "endereco": contrato.edificacao.endereco},
            "fiscal": {"nome": contrato.fiscal.nome, "crea": contrato.fiscal.crea},
            "visitas": visitas_ctx,
            "gerado_em": datetime.now(UTC).isoformat(),
        }
        return contexto, storage_keys


def _ler_fotos(storage: S3StorageClient, storage_keys: list[str]) -> tuple[dict[str, bytes], float]:
    inicio = time.perf_counter()
    fotos = {key: storage.download(key) for key in storage_keys}
    duracao = time.perf_counter() - inicio
    return fotos, duracao


def _otimizar_fotos(fotos_originais: dict[str, bytes]) -> tuple[dict[str, bytes], float]:
    inicio = time.perf_counter()
    otimizadas = {key: rfo_pipeline.otimizar_imagem(conteudo) for key, conteudo in fotos_originais.items()}
    duracao = time.perf_counter() - inicio
    return otimizadas, duracao


async def _registrar_relatorio_concluido(
    inspecao_id: uuid.UUID, storage: S3StorageClient, pdf_path: Path, docx_path: Path
) -> tuple[uuid.UUID, float]:
    """Cria/atualiza um `Relatorio` real: upload dos artefatos + status=concluido.

    Retorna `(relatorio_id, tempo_total_registro_s)` — o tempo aqui cobre
    exatamente o passo final do pipeline real (ADR-06): salvar PDF/DOCX no
    storage e persistir `Relatorio.status = "concluido"`.
    """
    inicio = time.perf_counter()
    pdf_key = f"relatorios/benchmark/{uuid.uuid4()}.pdf"
    docx_key = f"relatorios/benchmark/{uuid.uuid4()}.docx"
    storage.upload(
        pdf_key,
        pdf_path.read_bytes(),
        content_type="application/pdf",
        max_size_bytes=RELATORIO_MAX_UPLOAD_SIZE_BYTES,
    )
    storage.upload(
        docx_key,
        docx_path.read_bytes(),
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        max_size_bytes=RELATORIO_MAX_UPLOAD_SIZE_BYTES,
    )

    async with AsyncSessionLocal() as db:
        relatorio = Relatorio(
            inspecao_id=inspecao_id,
            versao="BENCH-01",
            tipo="RFO",
            status="concluido",
            pdf_key=pdf_key,
            docx_key=docx_key,
            emitido_em=datetime.now(UTC),
        )
        db.add(relatorio)
        await db.commit()
        await db.refresh(relatorio)
        relatorio_id = relatorio.id

    return relatorio_id, time.perf_counter() - inicio


async def rodar(inspecao_id: uuid.UUID) -> dict:
    storage = S3StorageClient()
    SAIDA_DIR.mkdir(exist_ok=True)

    contexto, storage_keys = await _carregar_contexto(inspecao_id)
    fotos_originais, tempo_leitura = _ler_fotos(storage, storage_keys)
    tamanho_total_original_mb = sum(len(b) for b in fotos_originais.values()) / (1024 * 1024)

    fotos_otimizadas, tempo_otimizacao = _otimizar_fotos(fotos_originais)
    tamanho_total_otimizado_mb = sum(len(b) for b in fotos_otimizadas.values()) / (1024 * 1024)

    resultados: dict = {
        "inspecao_id": str(inspecao_id),
        "n_visitas": len(contexto["visitas"]),
        "n_fotos": len(storage_keys),
        "tempo_leitura_storage_s": round(tempo_leitura, 2),
        "tamanho_total_fotos_original_mb": round(tamanho_total_original_mb, 2),
        "tempo_otimizacao_fotos_s": round(tempo_otimizacao, 2),
        "tamanho_total_fotos_otimizado_mb": round(tamanho_total_otimizado_mb, 2),
        "cenarios": {},
    }

    cenarios = {
        "sem_otimizacao": fotos_originais,
        "otimizado": fotos_otimizadas,
    }

    pdf_path_otimizado: Path | None = None
    docx_path_otimizado: Path | None = None

    for nome_cenario, fotos_bytes in cenarios.items():
        pdf_path = SAIDA_DIR / f"rfo_benchmark_{nome_cenario}.pdf"
        docx_path = SAIDA_DIR / f"rfo_benchmark_{nome_cenario}.docx"

        pdf_info = rfo_pipeline.gerar_pdf(contexto, fotos_bytes, pdf_path)
        docx_info = rfo_pipeline.gerar_docx(contexto, fotos_bytes, docx_path)

        resultados["cenarios"][nome_cenario] = {
            "pdf": pdf_info,
            "docx": docx_info,
            "tempo_total_com_leitura_storage_pdf_s": round(tempo_leitura + pdf_info["total"], 2),
            "tempo_total_com_leitura_storage_docx_s": round(tempo_leitura + docx_info["total"], 2),
        }

        if nome_cenario == "otimizado":
            pdf_path_otimizado, docx_path_otimizado = pdf_path, docx_path

        # Salva um snapshot parcial a cada cenário concluído — se o registro
        # final (upload + `Relatorio.status=concluido`) falhar por qualquer
        # motivo, as medições de tempo já feitas não se perdem.
        SAIDA_DIR.mkdir(exist_ok=True)
        (SAIDA_DIR / "resultado_parcial.json").write_text(
            json.dumps(resultados, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    assert pdf_path_otimizado is not None and docx_path_otimizado is not None
    try:
        relatorio_id, tempo_registro = await _registrar_relatorio_concluido(
            inspecao_id, storage, pdf_path_otimizado, docx_path_otimizado
        )
    except Exception as exc:
        resultados["registro_final_erro"] = str(exc)
        return resultados
    resultados["relatorio_id"] = str(relatorio_id)
    resultados["tempo_registro_final_storage_e_db_s"] = round(tempo_registro, 2)

    # Dois cenários de fim-a-fim para o formato "otimizado", porque a
    # otimização de imagem (`tempo_otimizacao_fotos_s`) é um custo que só
    # precisa ser pago 1x por foto — não 1x por RELATÓRIO gerado — se for
    # movida para o momento do upload (BL-11) em vez de rodar a cada geração
    # de relatório (ver recomendação no relatório de benchmark, BL-22):
    #   * "por_geracao": otimiza as fotos a cada vez que o relatório é gerado
    #     (o que este script faz hoje, pior caso).
    #   * "pre_otimizada_no_upload": assume que a foto já foi salva otimizada
    #     no upload — a geração do relatório só lê e renderiza.
    for formato in ("pdf", "docx"):
        tempo_formato = resultados["cenarios"]["otimizado"][formato]["total"]
        resultados[f"tempo_fim_a_fim_{formato}_otimizado_por_geracao_s"] = round(
            tempo_leitura + tempo_otimizacao + tempo_formato + tempo_registro, 2
        )
        resultados[f"tempo_fim_a_fim_{formato}_pre_otimizada_no_upload_s"] = round(
            tempo_leitura + tempo_formato + tempo_registro, 2
        )

    return resultados


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inspecao-id", required=True, help="UUID da Inspeção semeada por seed_benchmark_rfo")
    parser.add_argument(
        "--saida-json", default=None, help="Caminho do arquivo JSON de saída (default: tmp_benchmark/resultado.json)"
    )
    args = parser.parse_args()

    resultados = asyncio.run(rodar(uuid.UUID(args.inspecao_id)))

    saida_json = Path(args.saida_json) if args.saida_json else SAIDA_DIR / "resultado.json"
    saida_json.parent.mkdir(exist_ok=True)
    saida_json.write_text(json.dumps(resultados, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(resultados, indent=2, ensure_ascii=False))
    print(f"\nResultado salvo em {saida_json}")


if __name__ == "__main__":
    main()
