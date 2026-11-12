"""Harness de avaliação da legenda por IA contra o golden set (BL-34; plano-deepseek item 7).

Modos:
- `live`: chama o `DeepSeekLegendaIAClient` (via settings, atrás do `ClienteLegendaIAProtegido`, como
  na rota) para cada caso do golden set e grava a resposta bruta da API (corpo JSON + usage) em
  `<respostas>/<rotulo>.jsonl`. Sem `DEEPSEEK_API_KEY` aborta antes de qualquer chamada.
- `replay`: relê `<respostas>/<rotulo>.jsonl` e recalcula as métricas, sem rede (roda no CI).

Nos dois modos a resposta passa pelo mesmo caminho da produção (`DeepSeekLegendaIAClient._converter`
→ `sanear_resultado`), então as métricas valem para o que o usuário veria. Saída: tabela no terminal
e `<saida>/<rotulo>.resumo.json` com as métricas por caso e agregadas, comparável entre rótulos
(ex.: baseline, compacto, rag). Definições das métricas: 00_docs/backlog-auto/ia-avaliacao-harness.md.

Exemplos (a partir de 04_backend):
    python -m app.scripts.avaliar_legenda_ia --modo replay --rotulo sintetico
    python -m app.scripts.avaliar_legenda_ia --modo live --rotulo baseline --prompt ativo --limite 20
    python -m app.scripts.avaliar_legenda_ia --modo live --rotulo rag --prompt ativo --rag 3
"""
import argparse
import asyncio
import hashlib
import json
import os
import re
import statistics
import sys
import time
import unicodedata
from dataclasses import asdict, dataclass, field
from pathlib import Path

import httpx

from app.services.legenda_ia.contexto import ContextoLegenda, NbrContexto

BACKEND_DIR = Path(__file__).resolve().parents[2]
GOLDEN_PADRAO = BACKEND_DIR / "tests" / "fixtures" / "ia" / "golden_legenda.jsonl"
RESPOSTAS_PADRAO = BACKEND_DIR / "tests" / "fixtures" / "ia" / "respostas"
SAIDA_PADRAO = BACKEND_DIR / "tests" / "fixtures" / "ia" / "resumos"

LIMITE_CARACTERES = 481  # prompt do cliente: legenda com no máximo 481 caracteres (com ponto final)
NOME_PROMPT = "legenda_foto"  # mesmo nome usado por foto_service (PROMPT_LEGENDA_IA_NOME)
ENV_PRECOS = {
    "hit": "DEEPSEEK_PRECO_ENTRADA_CACHE_HIT",
    "miss": "DEEPSEEK_PRECO_ENTRADA_CACHE_MISS",
    "saida": "DEEPSEEK_PRECO_SAIDA",
}


class ErroAvaliacao(Exception):
    """Erro de uso do harness (mensagem clara, sem traceback no terminal)."""


# --------------------------------------------------------------------------------------------------
# Normalização e casamento de termos (também usados pelo extrator do golden set)
# --------------------------------------------------------------------------------------------------
def normalizar(texto: str | None) -> str:
    """Minúsculas, sem acentos, hífen como espaço e espaços colapsados."""
    if not texto:
        return ""
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFKD", texto) if unicodedata.category(c) != "Mn"
    )
    return " ".join(sem_acento.casefold().replace("-", " ").split())


def _radical(palavra: str) -> str:
    """Radical simples para casar singular/plural e gênero: «infiltrações» ~ «infiltração»."""
    if len(palavra) <= 4:
        return palavra
    if palavra.endswith("oes") or palavra.endswith("aes"):
        return palavra[:-3]
    if palavra.endswith("ao"):
        return palavra[:-2]
    if palavra.endswith("s"):
        palavra = palavra[:-1]
    if palavra[-1] in "aoe":
        palavra = palavra[:-1]
    return palavra


def padrao_termo(termo: str) -> re.Pattern[str]:
    palavras = normalizar(termo).split()
    corpo = r"\s+".join(re.escape(_radical(p)) + r"\w*" for p in palavras)
    return re.compile(rf"\b{corpo}")


def contem_termo(texto: str | None, termo: str) -> bool:
    return bool(padrao_termo(termo).search(normalizar(texto)))


# --------------------------------------------------------------------------------------------------
# Métricas
# --------------------------------------------------------------------------------------------------
def distancia_edicao(a: str, b: str) -> int:
    """Levenshtein (inserção, remoção, substituição com custo 1)."""
    if len(a) < len(b):
        a, b = b, a
    anterior = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        atual = [i]
        for j, cb in enumerate(b, 1):
            atual.append(min(anterior[j] + 1, atual[j - 1] + 1, anterior[j - 1] + (ca != cb)))
        anterior = atual
    return anterior[-1]


def distancia_edicao_normalizada(a: str | None, b: str | None) -> float:
    """Levenshtein sobre o texto normalizado ÷ tamanho do maior: 0 = igual, 1 = nada em comum."""
    na, nb = normalizar(a), normalizar(b)
    maior = max(len(na), len(nb))
    return 0.0 if maior == 0 else round(distancia_edicao(na, nb) / maior, 4)


_GRAUS = ("critico", "medio", "minimo")
_GRAU_NO_TEXTO = re.compile(
    r"\b(?:grau de risco|risco)\s*(?::\s*|e\s+|classificad\w*\s+como\s+|considerad\w*\s+)?"
    r"(critico|medio|minimo)\b"
)
_ORIGEM_ENDO_EXO = re.compile(r"\b(endogen|exogen)\w*")
_ORIGEM_NAT_FUNC = re.compile(r"\b(?:anomalia|origem|natureza)\s+(?:\w+\s+)?(natural|funcional)\b")
_ORIGENS = {"endogen": "endogena", "exogen": "exogena", "natural": "natural", "funcional": "funcional"}


def graus_mencionados(texto: str | None) -> set[str]:
    return set(_GRAU_NO_TEXTO.findall(normalizar(texto)))


def origens_mencionadas(texto: str | None) -> set[str]:
    norm = normalizar(texto)
    achadas = {_ORIGENS[m] for m in _ORIGEM_ENDO_EXO.findall(norm)}
    return achadas | {_ORIGENS[m] for m in _ORIGEM_NAT_FUNC.findall(norm)}


def origens_esperadas(tipo_anomalia: str | None) -> set[str]:
    norm = normalizar(tipo_anomalia)
    return {o for o in ("endogena", "exogena", "natural", "funcional") if o in norm}


def grau_risco_coerente(
    legenda: str, grau_esperado: str | None, grau_declarado: str | None = None
) -> bool | None:
    """False se a legenda (ou um campo `grau_risco` na resposta) afirma outro grau; None sem gabarito."""
    esperado = normalizar(grau_esperado)
    if esperado not in _GRAUS:
        return None
    citados = graus_mencionados(legenda)
    if grau_declarado:
        citados.add(normalizar(grau_declarado))
    return citados <= {esperado}


def tipo_anomalia_coerente(
    legenda: str, tipo_esperado: str | None, tipo_declarado: str | None = None
) -> bool:
    """False se a legenda (ou `tipo_anomalia` na resposta) atribui origem fora da esperada."""
    citadas = origens_mencionadas(legenda)
    if tipo_declarado:
        citadas |= origens_esperadas(tipo_declarado)
    return citadas <= origens_esperadas(tipo_esperado)


@dataclass(frozen=True)
class Precos:
    """US$ por 1M de tokens. Qualquer preço ausente desliga o custo (só tokens no relatório)."""

    hit: float | None = None
    miss: float | None = None
    saida: float | None = None

    @property
    def completos(self) -> bool:
        return None not in (self.hit, self.miss, self.saida)


def tokens_do_uso(uso: dict | None) -> dict[str, int | None]:
    uso = uso or {}
    hit = uso.get("prompt_cache_hit_tokens")
    miss = uso.get("prompt_cache_miss_tokens")
    entrada = uso.get("prompt_tokens")
    if miss is None and entrada is not None:
        miss = entrada - (hit or 0)
    return {"entrada": entrada, "hit": hit, "miss": miss, "saida": uso.get("completion_tokens")}


def custo_usd(tokens: dict[str, int | None], precos: Precos) -> float | None:
    if not precos.completos or tokens["miss"] is None or tokens["saida"] is None:
        return None
    total = (tokens["hit"] or 0) * precos.hit + tokens["miss"] * precos.miss
    return round((total + tokens["saida"] * precos.saida) / 1_000_000, 8)


# --------------------------------------------------------------------------------------------------
# Golden set e respostas
# --------------------------------------------------------------------------------------------------
def contexto_de_dict(dados: dict) -> ContextoLegenda:
    campos = dict(dados)
    campos["nbrs"] = tuple(NbrContexto(**n) for n in campos.get("nbrs") or ())
    return ContextoLegenda(**campos)


def carregar_jsonl(caminho: Path) -> list[dict]:
    if not caminho.is_file():
        raise ErroAvaliacao(f"Arquivo não encontrado: {caminho}")
    with caminho.open(encoding="utf-8") as arq:
        return [json.loads(linha) for linha in arq if linha.strip()]


def sha256_arquivo(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


@dataclass
class ResultadoCaso:
    id: str
    sistema: str | None
    grau_risco_esperado: str | None
    json_valido: bool = False
    erro: str | None = None
    legenda: str | None = None
    tamanho: int | None = None
    tamanho_ok: bool | None = None
    termos_presentes: list[str] = field(default_factory=list)
    termos_faltando: list[str] = field(default_factory=list)
    cobertura_termos: float | None = None
    grau_risco_coerente: bool | None = None
    tipo_anomalia_coerente: bool | None = None
    distancia_edicao: float | None = None
    nivel_certeza: str | None = None
    status_validacao: str | None = None
    n_alertas: int = 0
    n_pendencias: int = 0
    tokens: dict[str, int | None] = field(default_factory=dict)
    custo_usd: float | None = None
    latencia_ms: float | None = None


def _conteudo_json(corpo: dict) -> dict | None:
    try:
        dados = json.loads(corpo["choices"][0]["message"]["content"])
    except (KeyError, IndexError, TypeError, ValueError):
        return None
    return dados if isinstance(dados, dict) else None


def avaliar_caso(caso: dict, resposta: dict, precos: Precos, limites=None) -> ResultadoCaso:
    """Métricas de um caso a partir do registro gravado (`corpo` da API ou `erro`)."""
    from app.services.legenda_ia.deepseek import DeepSeekLegendaIAClient
    from app.services.legenda_ia.saneamento import (
        LimitesSaida,
        SaidaLegendaIAInvalida,
        sanear_resultado,
        sanear_texto,
    )

    esperado = caso["esperado"]
    res = ResultadoCaso(
        id=caso["id"],
        sistema=caso["entrada"].get("sistema"),
        grau_risco_esperado=esperado.get("grau_risco"),
        latencia_ms=resposta.get("latencia_ms"),
    )
    corpo = resposta.get("corpo")
    if isinstance(corpo, dict):
        res.tokens = tokens_do_uso(corpo.get("usage"))
        res.custo_usd = custo_usd(res.tokens, precos)
    if not isinstance(corpo, dict) or "choices" not in corpo:
        # Sem resposta de chat (falha de rede, HTTP de erro): nada para avaliar além do erro.
        res.erro = resposta.get("erro") or "resposta sem conteúdo"
        return res

    limites = limites or LimitesSaida(max_caracteres=500, max_itens=20, max_caracteres_item=300)
    try:
        resultado = DeepSeekLegendaIAClient._converter(
            httpx.Response(200, json=corpo), "texto", str(corpo.get("model") or "")
        )
        final = sanear_resultado(resultado, limites)
    except SaidaLegendaIAInvalida:
        res.erro = "JSON inválido ou sem legenda"
        return res

    dados = _conteudo_json(corpo) or {}
    res.json_valido = True
    res.legenda = final.legenda_sugerida
    res.tamanho = len(sanear_texto(resultado.legenda_sugerida))  # antes do corte do sistema
    res.tamanho_ok = res.tamanho <= LIMITE_CARACTERES
    termos = esperado.get("termos_esperados") or []
    res.termos_presentes = [t for t in termos if contem_termo(res.legenda, t)]
    res.termos_faltando = [t for t in termos if t not in res.termos_presentes]
    res.cobertura_termos = round(len(res.termos_presentes) / len(termos), 4) if termos else None
    declarado_grau = dados.get("grau_risco") if isinstance(dados.get("grau_risco"), str) else None
    declarado_tipo = dados.get("tipo_anomalia") if isinstance(dados.get("tipo_anomalia"), str) else None
    res.grau_risco_coerente = grau_risco_coerente(res.legenda, esperado.get("grau_risco"), declarado_grau)
    res.tipo_anomalia_coerente = tipo_anomalia_coerente(
        res.legenda, esperado.get("tipo_anomalia"), declarado_tipo
    )
    res.distancia_edicao = distancia_edicao_normalizada(res.legenda, esperado.get("legenda_referencia"))
    res.nivel_certeza = final.nivel_certeza
    status = dados.get("status_validacao")
    res.status_validacao = status if isinstance(status, str) else None
    res.n_alertas = len(final.alertas)
    res.n_pendencias = len(final.pendencias)
    return res


def _taxa(valores: list[bool | None]) -> float | None:
    validos = [v for v in valores if v is not None]
    return round(sum(validos) / len(validos), 4) if validos else None


def _media(valores: list[float | int | None]) -> float | None:
    validos = [v for v in valores if v is not None]
    return round(statistics.fmean(validos), 4) if validos else None


def _soma(valores: list[int | None]) -> int | None:
    validos = [v for v in valores if v is not None]
    return sum(validos) if validos else None


def agregar(resultados: list[ResultadoCaso], precos: Precos) -> dict:
    validos = [r for r in resultados if r.json_valido]
    tok = {k: _soma([r.tokens.get(k) for r in resultados]) for k in ("entrada", "hit", "miss", "saida")}
    distancias = [r.distancia_edicao for r in validos if r.distancia_edicao is not None]
    custos = [r.custo_usd for r in resultados if r.custo_usd is not None]
    niveis: dict[str, int] = {}
    for r in validos:
        chave = r.nivel_certeza or "ausente"
        niveis[chave] = niveis.get(chave, 0) + 1
    entrada_cache = (tok["hit"] or 0) + (tok["miss"] or 0)
    return {
        "n_casos": len(resultados),
        "n_erros": sum(1 for r in resultados if r.erro),
        "taxa_json_valido": _taxa([r.json_valido for r in resultados]),
        "taxa_tamanho_ok": _taxa([r.tamanho_ok for r in validos]),
        "tamanho_medio": _media([r.tamanho for r in validos]),
        "cobertura_termos_media": _media([r.cobertura_termos for r in validos]),
        "taxa_grau_risco_coerente": _taxa([r.grau_risco_coerente for r in validos]),
        "taxa_tipo_anomalia_coerente": _taxa([r.tipo_anomalia_coerente for r in validos]),
        "distancia_edicao_media": _media(distancias),
        "distancia_edicao_mediana": round(statistics.median(distancias), 4) if distancias else None,
        "nivel_certeza": dict(sorted(niveis.items())),
        "tokens_total": tok,
        "tokens_medios_por_caso": {
            k: (round(v / len(resultados), 1) if v is not None and resultados else None)
            for k, v in tok.items()
        },
        "taxa_cache_hit": round((tok["hit"] or 0) / entrada_cache, 4) if entrada_cache else None,
        "custo_total_usd": round(sum(custos), 8) if precos.completos and custos else None,
        "custo_medio_por_legenda_usd": round(statistics.fmean(custos), 8)
        if precos.completos and custos
        else None,
        "latencia_media_ms": _media([r.latencia_ms for r in resultados]),
    }


# --------------------------------------------------------------------------------------------------
# Execução
# --------------------------------------------------------------------------------------------------
def resolver_precos(args: argparse.Namespace) -> Precos:
    def valor(arg: float | None, chave: str) -> float | None:
        if arg is not None:
            return arg
        bruto = os.environ.get(ENV_PRECOS[chave], "").strip().replace(",", ".")
        if not bruto:
            return None
        try:
            return float(bruto)
        except ValueError as exc:
            raise ErroAvaliacao(f"{ENV_PRECOS[chave]} não é número: {bruto!r}") from exc

    return Precos(valor(args.preco_hit, "hit"), valor(args.preco_miss, "miss"), valor(args.preco_saida, "saida"))


async def _prompt_ativo() -> str:
    from app.core.database import AsyncSessionLocal
    from app.services.prompt_ia_service import obter_ativo

    async with AsyncSessionLocal() as db:
        return (await obter_ativo(db, NOME_PROMPT)).conteudo


def carregar_prompt(origem: str | None) -> str:
    if not origem:
        raise ErroAvaliacao("O modo live exige --prompt <arquivo|ativo>.")
    if origem == "ativo":
        try:
            return asyncio.run(_prompt_ativo())
        except Exception as exc:
            raise ErroAvaliacao(
                f"Não foi possível ler o prompt ativo '{NOME_PROMPT}' do banco: {exc}"
            ) from exc
    caminho = Path(origem)
    if not caminho.is_file():
        raise ErroAvaliacao(f"Arquivo de prompt não encontrado: {caminho}")
    return caminho.read_text(encoding="utf-8")


class _TransporteGravador(httpx.AsyncBaseTransport):
    """Repassa ao transporte real e guarda o último corpo JSON recebido (resposta bruta)."""

    def __init__(self, interno: httpx.AsyncBaseTransport) -> None:
        self._interno = interno
        self.ultimo_corpo: dict | None = None

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        resposta = await self._interno.handle_async_request(request)
        conteudo = await resposta.aread()
        try:
            self.ultimo_corpo = json.loads(conteudo)
        except ValueError:
            self.ultimo_corpo = None
        # `aread` já decodificou o corpo: sem estes cabeçalhos o httpx não tenta decodificar de novo.
        cabecalhos = [
            (k, v)
            for k, v in resposta.headers.items()
            if k.lower() not in ("content-encoding", "content-length", "transfer-encoding")
        ]
        return httpx.Response(resposta.status_code, headers=cabecalhos, content=conteudo, request=request)

    async def aclose(self) -> None:
        await self._interno.aclose()


def verificar_chave(settings) -> None:
    chave = settings.deepseek_api_key.get_secret_value().strip() if settings.deepseek_api_key else ""
    if not chave:
        raise ErroAvaliacao(
            "Modo live sem DEEPSEEK_API_KEY: defina a chave no ambiente (ou no .env do backend) "
            "para chamar a API DeepSeek. Para avaliar sem rede use --modo replay."
        )


# Fonte do golden set: com --rag fica fora das referências, senão o trecho traria a própria resposta.
FONTES_GOLDEN = ("Relatorio_Fotografico_de_Inspecao_Predial_-_CORTINA_DAMPAREZZO_-_Versao_Final.md",)


async def contextos_com_rag(casos: list[dict], k: int) -> list[ContextoLegenda]:
    """Enriquece cada caso com o RAG (IA-05) a partir do banco configurado (aprovadas + trechos)."""
    from app.core.database import AsyncSessionLocal
    from app.services.legenda_ia import recuperacao

    saida = []
    async with AsyncSessionLocal() as db:
        for caso in casos:
            ctx = contexto_de_dict(caso["entrada"])
            achado = await recuperacao.buscar(db, ctx, k, excluir_fontes=FONTES_GOLDEN)
            saida.append(achado.aplicar(ctx))
    return saida


async def coletar_live(
    casos: list[dict], prompt: str, settings, rotulo: str, transporte: httpx.AsyncBaseTransport | None = None,
    rag_k: int | None = None,
) -> list[dict]:
    """Chama a API para cada caso; devolve os registros brutos (sem chave, sem a imagem).

    `rag_k` (não None) liga o RAG da IA-05: few-shots e referências entram como na produção.
    """
    from app.services.legenda_ia import ClienteLegendaIAProtegido, DeepSeekLegendaIAClient
    from app.services.legenda_ia.saneamento import construir_limites_saida

    gravador = _TransporteGravador(transporte or httpx.AsyncHTTPTransport())
    cliente = ClienteLegendaIAProtegido(
        DeepSeekLegendaIAClient.de_settings(settings, transport=gravador),
        construir_limites_saida(settings),
    )
    prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    registros = []
    contextos = (
        await contextos_com_rag(casos, rag_k) if rag_k is not None else [contexto_de_dict(c["entrada"]) for c in casos]
    )
    for caso, contexto in zip(casos, contextos, strict=True):
        gravador.ultimo_corpo = None
        inicio = time.perf_counter()
        erro = None
        try:
            await cliente.gerar_legenda(contexto, prompt)
        except Exception as exc:  # registra e segue: um caso ruim não derruba a rodada paga
            erro = f"{type(exc).__name__}: {getattr(exc, 'detail', None) or exc}"
        registros.append(
            {
                "id": caso["id"],
                "rotulo": rotulo,
                "modelo": settings.deepseek_modelo,
                "prompt_hash": prompt_hash,
                "latencia_ms": round((time.perf_counter() - inicio) * 1000, 1),
                "erro": erro,
                "corpo": gravador.ultimo_corpo,
            }
        )
        print(f"  {caso['id']}: {'erro' if erro else 'ok'}", file=sys.stderr)
    return registros


def _fmt(valor, casas: int = 2) -> str:
    if valor is None:
        return "-"
    if isinstance(valor, bool):
        return "sim" if valor else "não"
    if isinstance(valor, float):
        return f"{valor:.{casas}f}"
    return str(valor)


def imprimir_tabela(rotulo: str, resultados: list[ResultadoCaso], agregado: dict) -> None:
    cab = f"{'caso':<14}{'json':>5}{'tam':>5}{'≤481':>5}{'termos':>8}{'grau':>6}{'tipo':>6}{'dist':>6}  certeza"
    print(f"\nAvaliação da legenda IA — rótulo «{rotulo}»\n{cab}\n{'-' * len(cab)}")
    for r in resultados:
        termos = f"{len(r.termos_presentes)}/{len(r.termos_presentes) + len(r.termos_faltando)}"
        print(
            f"{r.id:<14}{_fmt(r.json_valido):>5}{_fmt(r.tamanho):>5}{_fmt(r.tamanho_ok):>5}"
            f"{termos if r.json_valido else '-':>8}{_fmt(r.grau_risco_coerente):>6}"
            f"{_fmt(r.tipo_anomalia_coerente):>6}{_fmt(r.distancia_edicao):>6}  "
            f"{r.nivel_certeza or r.erro or '-'}"
        )
    print("\nAgregado")
    for chave, valor in agregado.items():
        print(f"  {chave:<30} {json.dumps(valor, ensure_ascii=False) if isinstance(valor, dict) else _fmt(valor, 4)}")


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--modo", choices=("replay", "live"), default="replay")
    p.add_argument("--rotulo", default="baseline", help="nome da rodada (arquivo de respostas e resumo)")
    p.add_argument("--prompt", help="arquivo de texto com o prompt ou 'ativo' (prompt ativo no banco)")
    p.add_argument("--limite", type=int, help="avalia só os N primeiros casos")
    p.add_argument("--saida", type=Path, default=SAIDA_PADRAO, help="diretório do JSON de resumo")
    p.add_argument("--golden", type=Path, default=GOLDEN_PADRAO)
    p.add_argument("--respostas", type=Path, default=RESPOSTAS_PADRAO, help="diretório das respostas brutas")
    p.add_argument("--sobrescrever", action="store_true", help="live: substitui respostas existentes do rótulo")
    p.add_argument(
        "--rag", type=int, metavar="K",
        help="live: liga o RAG (IA-05) com K exemplos aprovados; exige banco com a migration c6f2a8d4e1b9",
    )
    p.add_argument("--preco-hit", type=float, help=f"US$/1M tokens de entrada em cache (ou {ENV_PRECOS['hit']})")
    p.add_argument("--preco-miss", type=float, help=f"US$/1M tokens de entrada fora do cache (ou {ENV_PRECOS['miss']})")
    p.add_argument("--preco-saida", type=float, help=f"US$/1M tokens de saída (ou {ENV_PRECOS['saida']})")
    return p


def get_settings():
    from app.core.config import get_settings as _get

    return _get()


def executar(argv: list[str] | None = None) -> dict:
    args = _parser().parse_args(argv)
    if args.limite is not None and args.limite < 1:
        raise ErroAvaliacao("--limite deve ser ≥ 1.")
    if not re.fullmatch(r"[\w.-]+", args.rotulo):
        raise ErroAvaliacao("--rotulo aceita só letras, números, '.', '_' e '-'.")
    precos = resolver_precos(args)
    arquivo_respostas = args.respostas / f"{args.rotulo}.jsonl"
    casos = carregar_jsonl(args.golden)
    prompt_hash = None

    if args.modo == "live":
        settings = get_settings()
        verificar_chave(settings)
        if arquivo_respostas.exists() and not args.sobrescrever:
            raise ErroAvaliacao(f"{arquivo_respostas} já existe; use outro --rotulo ou --sobrescrever.")
        prompt = carregar_prompt(args.prompt)
        prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        selecionados = casos[: args.limite] if args.limite else casos
        print(f"Chamando a API para {len(selecionados)} caso(s)...", file=sys.stderr)
        registros = asyncio.run(coletar_live(selecionados, prompt, settings, args.rotulo, rag_k=args.rag))
        arquivo_respostas.parent.mkdir(parents=True, exist_ok=True)
        with arquivo_respostas.open("w", encoding="utf-8") as arq:
            for reg in registros:
                arq.write(json.dumps(reg, ensure_ascii=False) + "\n")
        from app.services.legenda_ia.saneamento import construir_limites_saida

        limites = construir_limites_saida(settings)
    else:
        limites = None

    respostas = {r["id"]: r for r in carregar_jsonl(arquivo_respostas)}
    por_id = {c["id"]: c for c in casos}
    desconhecidos = sorted(set(respostas) - set(por_id))
    if desconhecidos:
        raise ErroAvaliacao(f"Respostas com id fora do golden set: {', '.join(desconhecidos)}")
    avaliados = [c for c in casos if c["id"] in respostas]
    if args.limite:
        avaliados = avaliados[: args.limite]
    if not avaliados:
        raise ErroAvaliacao(f"Nenhuma resposta de {arquivo_respostas} corresponde ao golden set.")

    resultados = [avaliar_caso(c, respostas[c["id"]], precos, limites) for c in avaliados]
    agregado = agregar(resultados, precos)
    hashes = {r.get("prompt_hash") for r in respostas.values()} - {None}
    modelos = {r.get("modelo") for r in respostas.values()} - {None}
    resumo = {
        "rotulo": args.rotulo,
        "modo": args.modo,
        "golden": {"arquivo": args.golden.name, "sha256": sha256_arquivo(args.golden), "n_casos": len(casos)},
        "respostas": arquivo_respostas.name,
        "prompt_hash": prompt_hash or (sorted(hashes)[0] if len(hashes) == 1 else sorted(hashes)),
        "modelo": sorted(modelos)[0] if len(modelos) == 1 else sorted(modelos),
        "precos_usd_por_1m": asdict(precos) if precos.completos else None,
        "limite_caracteres": LIMITE_CARACTERES,
        "n_golden_sem_resposta": len(casos) - len(set(respostas) & set(por_id)),
        "agregado": agregado,
        "casos": [asdict(r) for r in resultados],
    }
    args.saida.mkdir(parents=True, exist_ok=True)
    destino = args.saida / f"{args.rotulo}.resumo.json"
    destino.write_text(json.dumps(resumo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    imprimir_tabela(args.rotulo, resultados, agregado)
    if not precos.completos:
        print("\nCusto não calculado: informe os 3 preços (--preco-* ou DEEPSEEK_PRECO_*).")
    print(f"\nResumo: {destino}")
    return resumo


def main(argv: list[str] | None = None) -> int:
    try:
        executar(argv)
    except ErroAvaliacao as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
