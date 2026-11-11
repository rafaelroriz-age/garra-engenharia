"""Seed idempotente do prompt ativo `legenda_foto` (BL-34, IA-02; DEC-37 DP-2).

Lê o bloco entre `MARCADOR_INICIO` e `MARCADOR_FIM` de `00_docs/ia/prompt-legenda-compacto.md`
(dentro de uma cerca ```text), compara o SHA-256 com a versão ativa e só então cria uma
nova versão imutável e a ativa. Rodar de novo com o mesmo texto não faz nada.

Uso (a partir de `04_backend/`):
    python -m app.scripts.seed_prompt_legenda --dry-run
    python -m app.scripts.seed_prompt_legenda
    python -m app.scripts.seed_prompt_legenda --arquivo /caminho/prompt-legenda-compacto.md

`--dry-run` lê o banco para comparar o hash, mas não grava nada.
"""
import argparse
import asyncio
import sys
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.core.errors import DomainError
from app.services import prompt_ia_service
from app.services.foto_service import PROMPT_LEGENDA_IA_NOME

MARCADOR_INICIO = "<!-- PROMPT-LEGENDA-FOTO:INICIO -->"
MARCADOR_FIM = "<!-- PROMPT-LEGENDA-FOTO:FIM -->"
# 04_backend/app/scripts/ → raiz do monorepo.
ARQUIVO_PADRAO = Path(__file__).resolve().parents[3] / "00_docs" / "ia" / "prompt-legenda-compacto.md"
_SEM_VERSAO_ATIVA = "prompt-ia-sem-versao-ativa"


class BlocoPromptInvalido(ValueError):
    """O arquivo não tem exatamente um bloco de prompt bem formado."""


@dataclass(frozen=True)
class ResultadoSeed:
    acao: str  # "inalterado" | "criado" | "seria_criado"
    hash: str
    versao: str | None


def extrair_prompt(texto: str) -> str:
    """Devolve o conteúdo da cerca de código entre os marcadores, normalizado.

    Normaliza `\\r\\n`→`\\n` e remove espaços à direita de cada linha, para que o hash
    não dependa do sistema operacional nem do editor.
    """
    todas = [linha.rstrip() for linha in texto.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    # Marcadores só contam como linha inteira (citá-los no meio de um parágrafo não conta).
    inicios = [i for i, linha in enumerate(todas) if linha.strip() == MARCADOR_INICIO]
    fins = [i for i, linha in enumerate(todas) if linha.strip() == MARCADOR_FIM]
    if len(inicios) != 1 or len(fins) != 1:
        raise BlocoPromptInvalido("Esperado exatamente um par de marcadores do prompt, cada um em linha própria.")
    if fins[0] < inicios[0]:
        raise BlocoPromptInvalido("Marcador de fim antes do marcador de início.")
    linhas = todas[inicios[0] + 1 : fins[0]]
    while linhas and not linhas[0]:
        linhas.pop(0)
    while linhas and not linhas[-1]:
        linhas.pop()
    if len(linhas) < 2 or not linhas[0].startswith("```") or linhas[-1] != "```":
        raise BlocoPromptInvalido("O bloco entre os marcadores deve ser uma cerca ```text ... ```.")
    conteudo = "\n".join(linhas[1:-1]).strip()
    if not conteudo:
        raise BlocoPromptInvalido("O bloco do prompt está vazio.")
    return conteudo


async def _hash_ativo(db: AsyncSession, nome: str) -> str | None:
    try:
        ativo = await prompt_ia_service.obter_ativo(db, nome)
    except DomainError as exc:
        if exc.type_suffix == _SEM_VERSAO_ATIVA:
            return None
        raise
    return prompt_ia_service.calcular_hash(ativo.conteudo)


async def sincronizar(
    db: AsyncSession, conteudo: str, *, nome: str = PROMPT_LEGENDA_IA_NOME, dry_run: bool = False
) -> ResultadoSeed:
    """Cria e ativa nova versão de `nome` só se o hash diferir da versão ativa."""
    novo_hash = prompt_ia_service.calcular_hash(conteudo)
    if await _hash_ativo(db, nome) == novo_hash:
        return ResultadoSeed("inalterado", novo_hash, None)
    if dry_run:
        return ResultadoSeed("seria_criado", novo_hash, None)
    versao = await prompt_ia_service.criar_versao(db, nome=nome, conteudo=conteudo)
    await prompt_ia_service.ativar(db, versao.id)
    return ResultadoSeed("criado", novo_hash, versao.versao)


async def _executar(conteudo: str, dry_run: bool) -> ResultadoSeed:
    engine = create_async_engine(get_settings().database_url, future=True)
    try:
        async with async_sessionmaker(bind=engine, expire_on_commit=False)() as session:
            return await sincronizar(session, conteudo, dry_run=dry_run)
    finally:
        await engine.dispose()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Seed idempotente do prompt 'legenda_foto'.")
    parser.add_argument("--arquivo", type=Path, default=ARQUIVO_PADRAO, help="Markdown com o bloco do prompt.")
    parser.add_argument("--dry-run", action="store_true", help="Só compara o hash; não grava.")
    args = parser.parse_args(argv)

    try:
        conteudo = extrair_prompt(args.arquivo.read_text(encoding="utf-8"))
    except (OSError, BlocoPromptInvalido) as exc:
        print(f"Erro ao ler o prompt em '{args.arquivo}': {exc}", file=sys.stderr)
        return 1

    resultado = asyncio.run(_executar(conteudo, args.dry_run))
    mensagens = {
        "inalterado": "Versão ativa já tem este conteúdo — nada a fazer.",
        "seria_criado": "[dry-run] Conteúdo difere da versão ativa: uma nova versão seria criada e ativada.",
        "criado": f"Versão {resultado.versao} de '{PROMPT_LEGENDA_IA_NOME}' criada e ativada.",
    }
    print(f"{mensagens[resultado.acao]} ({len(conteudo)} caracteres, sha256={resultado.hash})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
