"""Exporta o dataset de feedback da legenda por IA (BL-34, IA-06; plano-deepseek §«fine-tuning»).

Cada foto com legenda IA **aprovada** pelo auditor vira uma tripla
`contexto -> sugestão da IA -> legenda final`. Saídas:

- `dataset_legenda.jsonl`: formato chat (`{"messages": [system, user, assistant]}`), em que
  `system` é o prompt da versão usada (+ a instrução JSON do adapter), `user` é idêntico ao enviado
  pelo adapter DeepSeek e `assistant` é o JSON de saída com a legenda FINAL do auditor.
- `metricas_legenda.csv`: uma linha por foto, com a distância de edição normalizada
  sugestão→final (0 = aceita sem edição, 1 = reescrita total), nível de certeza, modelo/prompt etc.

Somente leitura no banco. Dados de cliente não vão para o git: `--saida` dentro de um repositório
git é recusada. Todo texto livre passa de novo por `limpar_dados_pessoais` (CPF/CNPJ/e-mail/telefone).
Isso é rede de segurança por regex, não anonimização garantida.

Uso (a partir de `04_backend/`):
    python -m app.scripts.exportar_dataset_legenda --saida D:/dados/legenda \
        [--desde 2026-01-01] [--ate 2026-12-31] [--min-registros 500]
"""
import argparse
import asyncio
import csv
import json
import sys
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.models import ChamadaIA, Foto, PromptIA
from app.services.legenda_ia.contexto import limpar_dados_pessoais, montar_contexto
from app.services.legenda_ia.deepseek import _INSTRUCAO_JSON, _texto_usuario

ARQUIVO_JSONL = "dataset_legenda.jsonl"
ARQUIVO_CSV = "metricas_legenda.csv"
COLUNAS_CSV = (
    "foto_id", "aprovado_em", "distancia_edicao", "aceita_sem_edicao", "nivel_certeza_ia",
    "modelo", "modo", "prompt_ia_id", "prompt_versao", "sistema", "tipo_anomalia",
)
SEM_SISTEMA = "(sem sistema)"


class SaidaNoRepositorio(ValueError):
    """`--saida` aponta para dentro de um repositório git."""


@dataclass(frozen=True)
class Registro:
    foto_id: str
    aprovado_em: str
    sugerida: str
    final: str
    distancia: float
    nivel_certeza: str | None
    modelo: str | None
    modo: str | None
    prompt_ia_id: str | None
    prompt_versao: str | None
    sistema: str | None
    tipo_anomalia: str | None
    mensagens: list[dict] | None  # None quando a foto não tem prompt registrado

    @property
    def aceita_sem_edicao(self) -> bool:
        return self.distancia == 0.0


def distancia_edicao_normalizada(sugerida: str, final: str) -> float:
    """Levenshtein(sugerida, final) / max(len): 0.0 = idênticas, 1.0 = totalmente diferentes.

    Espaços nas pontas e entre palavras não contam como edição (a UI do auditor os normaliza).
    """
    a, b = " ".join(sugerida.split()), " ".join(final.split())
    if a == b:
        return 0.0
    if not a or not b:
        return 1.0
    anterior = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        atual = [i]
        for j, cb in enumerate(b, start=1):
            atual.append(min(anterior[j] + 1, atual[j - 1] + 1, anterior[j - 1] + (ca != cb)))
        anterior = atual
    return anterior[-1] / max(len(a), len(b))


def _repositorio_git_de(caminho: Path) -> Path | None:
    """Raiz do repositório git que contém `caminho` (mesmo inexistente), ou None."""
    atual = caminho.resolve()
    for pasta in (atual, *atual.parents):
        if (pasta / ".git").exists():
            return pasta
    return None


def validar_saida(saida: Path) -> Path:
    raiz = _repositorio_git_de(saida)
    if raiz is not None:
        raise SaidaNoRepositorio(
            f"--saida '{saida}' está dentro do repositório git '{raiz}'. Dados de cliente não "
            "podem ir para o git: use uma pasta fora do repositório."
        )
    return saida.resolve()


def _limpo(texto: str | None) -> str:
    return limpar_dados_pessoais(texto) or ""


def _mensagens(prompt: str, user: str, final: str, nivel: str | None) -> list[dict]:
    """system/user como o adapter (`DeepSeekLegendaIAClient._mensagens`); assistant com a legenda final."""
    saida: dict[str, object] = {"legenda_sugerida": final, "alertas": [], "pendencias": []}
    if nivel:
        saida["nivel_certeza"] = nivel
    saida["status_validacao"] = "aprovada"
    return [
        {"role": "system", "content": f"{prompt}\n\n{_INSTRUCAO_JSON}"},
        {"role": "user", "content": user},
        {"role": "assistant", "content": json.dumps(saida, ensure_ascii=False)},
    ]


async def coletar(
    db: AsyncSession, desde: date | None = None, ate: date | None = None
) -> list[Registro]:
    """Consulta SOMENTE LEITURA: fotos aprovadas com sugestão e legenda final."""
    consulta = (
        select(Foto)
        .where(
            Foto.status_validacao_ia == "aprovada",
            Foto.legenda_ia_sugerida.is_not(None),
            Foto.legenda.is_not(None),
        )
        .order_by(Foto.aprovado_em, Foto.id)
    )
    if desde is not None:
        consulta = consulta.where(Foto.aprovado_em >= datetime.combine(desde, time.min, tzinfo=UTC))
    if ate is not None:  # `--ate` é inclusivo
        consulta = consulta.where(
            Foto.aprovado_em < datetime.combine(ate + timedelta(days=1), time.min, tzinfo=UTC)
        )
    registros: list[Registro] = []
    for foto in (await db.execute(consulta)).scalars().all():
        sugerida = _limpo(foto.legenda_ia_sugerida)
        final = _limpo(foto.legenda)
        if not final:
            continue
        contexto = await montar_contexto(db, foto)
        prompt = await db.get(PromptIA, foto.prompt_ia_id) if foto.prompt_ia_id else None
        chamada = (
            await db.execute(
                select(ChamadaIA)
                .where(ChamadaIA.foto_id == foto.id, ChamadaIA.origem == "api", ChamadaIA.sucesso.is_(True))
                .order_by(ChamadaIA.criado_em.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        mensagens = (
            _mensagens(prompt.conteudo, _limpo(_texto_usuario(contexto)), final, foto.nivel_certeza_ia)
            if prompt is not None
            else None
        )
        registros.append(
            Registro(
                foto_id=str(foto.id),
                aprovado_em=foto.aprovado_em.isoformat() if foto.aprovado_em else "",
                sugerida=sugerida,
                final=final,
                distancia=round(distancia_edicao_normalizada(sugerida, final), 4),
                nivel_certeza=foto.nivel_certeza_ia,
                modelo=chamada.modelo if chamada else None,
                modo=chamada.modo if chamada else None,
                prompt_ia_id=str(foto.prompt_ia_id) if foto.prompt_ia_id else None,
                prompt_versao=prompt.versao if prompt else None,
                sistema=contexto.sistema,
                tipo_anomalia=contexto.tipo_anomalia,
                mensagens=mensagens,
            )
        )
    return registros


def gravar(registros: list[Registro], saida: Path) -> tuple[Path, Path]:
    saida.mkdir(parents=True, exist_ok=True)
    jsonl, csv_path = saida / ARQUIVO_JSONL, saida / ARQUIVO_CSV
    with jsonl.open("w", encoding="utf-8", newline="\n") as f:
        for r in registros:
            if r.mensagens is not None:
                f.write(json.dumps({"messages": r.mensagens}, ensure_ascii=False) + "\n")
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        escritor = csv.writer(f)
        escritor.writerow(COLUNAS_CSV)
        for r in registros:
            escritor.writerow([
                r.foto_id, r.aprovado_em, f"{r.distancia:.4f}", int(r.aceita_sem_edicao),
                r.nivel_certeza or "", r.modelo or "", r.modo or "", r.prompt_ia_id or "",
                r.prompt_versao or "", r.sistema or "", r.tipo_anomalia or "",
            ])
    return jsonl, csv_path


def resumo(registros: list[Registro]) -> str:
    n = len(registros)
    if n == 0:
        return "Nenhuma legenda aprovada no período."
    aceitas = sum(r.aceita_sem_edicao for r in registros)
    sem_prompt = sum(r.mensagens is None for r in registros)
    linhas = [
        f"Registros: {n}",
        f"Aceitas sem edição: {aceitas} ({100 * aceitas / n:.1f}%)",
        f"Distância média de edição: {sum(r.distancia for r in registros) / n:.3f}",
        f"Sem prompt registrado (fora do JSONL): {sem_prompt}",
        "Distância média por sistema:",
    ]
    por_sistema: dict[str, list[float]] = {}
    for r in registros:
        por_sistema.setdefault(r.sistema or SEM_SISTEMA, []).append(r.distancia)
    for sistema, valores in sorted(por_sistema.items()):
        linhas.append(f"  {sistema}: {sum(valores) / len(valores):.3f} (n={len(valores)})")
    return "\n".join(linhas)


async def exportar(
    db: AsyncSession,
    saida: Path,
    desde: date | None = None,
    ate: date | None = None,
    min_registros: int = 0,
) -> tuple[list[Registro], bool]:
    """Valida a saída, coleta e grava. Retorna (registros, gravou); não grava abaixo de `min_registros`."""
    destino = validar_saida(saida)
    registros = await coletar(db, desde, ate)
    if len(registros) < min_registros:
        return registros, False
    gravar(registros, destino)
    return registros, True


def _data(texto: str) -> date:
    return date.fromisoformat(texto)


async def _executar(args: argparse.Namespace) -> int:
    try:
        validar_saida(args.saida)
    except SaidaNoRepositorio as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 2
    engine = create_async_engine(get_settings().database_url, poolclass=NullPool, future=True)
    try:
        async with async_sessionmaker(bind=engine, expire_on_commit=False)() as db:
            registros, gravou = await exportar(db, args.saida, args.desde, args.ate, args.min_registros)
    finally:
        await engine.dispose()
    print(resumo(registros))
    if not gravou:
        print(
            f"Nada gravado: {len(registros)} registros < --min-registros {args.min_registros}.",
            file=sys.stderr,
        )
        return 1
    print(f"Gravado em {args.saida.resolve()} ({ARQUIVO_JSONL}, {ARQUIVO_CSV}).")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Exporta o dataset de feedback da legenda IA (somente leitura).")
    p.add_argument("--saida", type=Path, required=True, help="pasta de saída, FORA do repositório git")
    p.add_argument("--desde", type=_data, help="aprovadas a partir de AAAA-MM-DD (inclusivo)")
    p.add_argument("--ate", type=_data, help="aprovadas até AAAA-MM-DD (inclusivo)")
    p.add_argument("--min-registros", type=int, default=0, help="não grava se houver menos registros")
    return asyncio.run(_executar(p.parse_args(argv)))


if __name__ == "__main__":
    sys.exit(main())
