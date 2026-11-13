"""Ingestão da base de referência do RAG da legenda IA (BL-34, IA-05; plano-deepseek item 6).

Lê **somente** `00_docs/convertidos/*.md` (nunca `01_output-context/`, que guarda os originais do
cliente), quebra o texto em trechos de 300-800 caracteres, anonimiza e grava em
`trechos_conhecimento_ia` de forma idempotente (`hash` único → `ON CONFLICT DO NOTHING`).

Quebra:
- Tabela de fotos (cabeçalho com «Sistema» e «Observações técnicas»/«Manifestações patológicas»):
  uma linha por foto vira «Sistema…; tipo…; grau de risco…; Observação…». Linhas seguidas do mesmo
  sistema/subsistema são agrupadas até 300-800 caracteres; `sistema`, `tipo_anomalia` e `grau_risco`
  só são marcados quando todas as fotos do grupo concordam.
- Prosa (laudos em PDF): linhas longas viram parágrafos, empacotados em trechos de 300-800
  caracteres por seção (`## Página N`/aba). O sistema é inferido por palavras-chave quando um
  sistema domina; grau de risco/tipo de anomalia só quando o texto os cita explicitamente.

Anonimização (antes do hash, `app/services/legenda_ia/anonimizacao.py`): condomínio/edifício,
empresa, endereço, CEP, unidade, pessoas (com pronome de tratamento ou assinatura de engenheiro),
CREA, CPF/CNPJ, e-mail e telefone viram marcadores genéricos. Linhas curtas de cabeçalho/rodapé com
CREA, e-mail ou CEP são descartadas. É heurística por regex: revise o `--dry-run --amostras N`
antes de ingerir documentos novos.

Uso (a partir de 04_backend):
    python -m app.scripts.ingerir_conhecimento_ia --dry-run
    python -m app.scripts.ingerir_conhecimento_ia --dry-run --amostras 5
    python -m app.scripts.ingerir_conhecimento_ia
"""
import argparse
import asyncio
import hashlib
import re
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import TrechoConhecimentoIA
from app.services.legenda_ia.anonimizacao import (
    LINHA_CABECALHO_PESSOAL,
    anonimizar,
    nomes_de_assinatura,
)

PASTA_PADRAO = Path(__file__).resolve().parents[3] / "00_docs" / "convertidos"
PASTA_PROIBIDA = "01_output-context"
# Fora da base: índice da conversão e contrato de software (não é laudo técnico).
IGNORADOS = {"README.md", "Contrato_Prestacao_Servicos_Software.md"}

MIN_CARACTERES = 300
MAX_CARACTERES = 800
# Fim de grupo/seção: sobra menor que 300 entra no trecho anterior se couber; senão fica se ≥ este piso.
PISO_SOBRA = 150
MIN_LINHA_PROSA = 50


# --------------------------------------------------------------------------------------------------
# Metadados
# --------------------------------------------------------------------------------------------------
# Nomes do gabarito (`seed_gabarito`/RFO_INSPECAO.md), iguais a `sistemas_prediais.nome`.
_SISTEMAS_CHAVE: dict[str, tuple[str, ...]] = {
    "Elementos_Estruturais_Aparentes": ("estrutur", "viga", "pilar", "laje", "armadura", "concreto"),
    "Cobertura_e_Telhamento": ("telhado", "telha", "cobertura", "rufo", "calha", "cumeeira"),
    "Impermeabilização": ("impermeabiliza", "infiltra", "umidade", "manta asfáltica"),
    "Sistemas_Elétricos_de_baixa_tensão": ("elétric", "disjuntor", "quadro de distribuição", "fiação"),
    "Sistemas_Hidrossanitários": ("hidráulic", "hidrossanit", "esgot", "tubula", "reservatório"),
    "Revestimentos_Externos_e_Internos": ("revestimento", "reboco", "pintura", "cerâmic", "fachada"),
    "Sistema_de_Prevenção_e_Combate_a_Incêndios": ("incêndio", "extintor", "hidrante", "bombeiro"),
    "Acessibilidade": ("acessibilidade", "nbr 9050", "rampa", "pcd"),
    "Sistema_de_Esquadrias": ("esquadria", "janela", "caixilho"),
    "Vedações_verticais": ("alvenaria", "vedaç"),
    "Sistema_de_Proteção_Contra_Descargas_Atmosféricas_SPDA": ("spda", "para-raio", "descargas atmosféricas"),
    "Instalações_de_Gás_Combustível": ("gás combustível", "glp", "abrigo do gás"),
}
_GRAU_PROSA = re.compile(r"(?:grau\s+de\s+)?risco\s+(cr[íi]tico|m[ée]dio|m[íi]nimo)\b", re.IGNORECASE)
_TIPO_PROSA = re.compile(
    r"anomalias?\s+(?:de\s+origem\s+)?(end[óo]gena|ex[óo]gena|funcional)\b", re.IGNORECASE
)


def sem_acento(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))


def normalizar_grau(valor: str | None) -> str | None:
    """«Mínimo»/«médio»/«CRÍTICO» → MINIMO/MEDIO/CRITICO (como `ocorrencias.grau_risco`)."""
    if not valor:
        return None
    grau = sem_acento(valor).strip().upper()
    return grau if grau in {"MINIMO", "MEDIO", "CRITICO"} else None


def inferir_sistema(texto: str) -> str | None:
    baixo = texto.lower()
    contagem = Counter({s: sum(baixo.count(c) for c in chaves) for s, chaves in _SISTEMAS_CHAVE.items()})
    (primeiro, n1), (_, n2) = contagem.most_common(2)
    return primeiro if n1 >= 2 and n1 > n2 else None


def _unico(regex: re.Pattern[str], texto: str) -> str | None:
    achados = {sem_acento(m.group(1)).lower() for m in regex.finditer(texto)}
    return achados.pop() if len(achados) == 1 else None


# --------------------------------------------------------------------------------------------------
# Quebra em trechos
# --------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Trecho:
    fonte: str
    texto: str
    tipo: str = "relatorio_historico"
    sistema: str | None = None
    tipo_anomalia: str | None = None
    grau_risco: str | None = None

    @property
    def hash(self) -> str:
        return hashlib.sha256(self.texto.encode("utf-8")).hexdigest()


def _espacos(texto: str) -> str:
    return " ".join(texto.split())


def _partir_longo(texto: str, maximo: int = MAX_CARACTERES) -> list[str]:
    """Divide em frases sem passar de `maximo`; frase sozinha maior que isso é cortada em palavra."""
    partes: list[str] = []
    atual = ""
    for frase in re.split(r"(?<=[.;!?])\s+", texto):
        while len(frase) > maximo:
            corte = frase.rfind(" ", 0, maximo)
            corte = corte if corte > maximo // 2 else maximo
            partes.append(frase[:corte].strip())
            frase = frase[corte:].strip()
        if atual and len(atual) + 1 + len(frase) > maximo:
            partes.append(atual)
            atual = frase
        else:
            atual = f"{atual} {frase}".strip()
    if atual:
        partes.append(atual)
    return partes


def empacotar(blocos: list[str]) -> list[str]:
    """Junta blocos em trechos de 300-800 caracteres (sobra final curta: ver `PISO_SOBRA`)."""
    pedacos = [p for b in blocos for p in _partir_longo(_espacos(b)) if p]
    trechos: list[str] = []
    atual = ""
    for pedaco in pedacos:
        if atual and len(atual) + 1 + len(pedaco) > MAX_CARACTERES:
            if len(atual) >= PISO_SOBRA:
                trechos.append(atual)
            atual = pedaco
        else:
            atual = f"{atual} {pedaco}".strip()
        if len(atual) >= MIN_CARACTERES:
            trechos.append(atual)
            atual = ""
    if atual:
        if trechos and len(trechos[-1]) + 1 + len(atual) <= MAX_CARACTERES:
            trechos[-1] = f"{trechos[-1]} {atual}"
        elif len(atual) >= PISO_SOBRA:
            trechos.append(atual)
    return trechos


def _parece_texto(texto: str) -> bool:
    """Descarta sequências de números/códigos (ex.: notas de planilha): pede ≥ 60% de letras."""
    sem_espaco = [c for c in texto if not c.isspace()]
    if not sem_espaco or sum(c.isalpha() for c in sem_espaco) / len(sem_espaco) < 0.6:
        return False
    # Texto girado/quebrado na conversão do PDF vira letras soltas («at bx a r be»): média de palavra curta.
    palavras = texto.split()
    return sum(len(p) for p in palavras) / len(palavras) >= 3.5


def _celulas(linha: str) -> list[str]:
    return [c.strip() for c in linha.strip().strip("|").split("|")]


def _chave(c: str) -> str:
    return sem_acento(c).lower().strip()


_COLUNAS_FOTO = {
    "sistema": ("sistema",),
    "subsistema": ("subsistema",),
    "local": ("localizacao",),
    "classificacao": ("classificacao",),
    "tipo": ("tipo", "tipo de anomalia"),
    "grau": ("grau de risco",),
    "obs": ("observacoes tecnicas", "manifestacoes patologicas"),
}


def _cabecalho_fotos(celulas: list[str]) -> dict[str, int] | None:
    chaves = [_chave(c) for c in celulas]
    mapa = {}
    for campo, nomes in _COLUNAS_FOTO.items():
        for i, c in enumerate(chaves):
            if c in nomes:
                mapa[campo] = i
                break
    # Pelo menos 5 colunas reconhecidas: o formulário «Rel. Fotográfico» também tem os rótulos
    # SISTEMA e OBSERVAÇÕES TÉCNICAS numa linha, mas os valores ficam em outras colunas.
    return mapa if {"sistema", "obs"} <= set(mapa) and len(mapa) >= 5 else None


def _valor(celulas: list[str], mapa: dict[str, int], campo: str) -> str | None:
    i = mapa.get(campo)
    if i is None or i >= len(celulas):
        return None
    v = _espacos(celulas[i])
    return None if v in {"", "0", "-"} else v


def _texto_foto(celulas: list[str], mapa: dict[str, int]) -> str | None:
    obs = _valor(celulas, mapa, "obs")
    if not obs:
        return None
    sistema = (_valor(celulas, mapa, "sistema") or "").replace("_", " ")
    partes = [
        f"Sistema: {sistema}" if sistema else None,
        f"subsistema: {_valor(celulas, mapa, 'subsistema')}" if _valor(celulas, mapa, "subsistema") else None,
        f"local: {_valor(celulas, mapa, 'local')}" if _valor(celulas, mapa, "local") else None,
        f"classificação: {_valor(celulas, mapa, 'classificacao')}" if _valor(celulas, mapa, "classificacao") else None,
        f"tipo: {_valor(celulas, mapa, 'tipo')}" if _valor(celulas, mapa, "tipo") else None,
        f"grau de risco: {_valor(celulas, mapa, 'grau')}" if _valor(celulas, mapa, "grau") else None,
    ]
    return "; ".join(p for p in partes if p) + f". Observação técnica: {obs}"


def _comum(valores: list[str | None]) -> str | None:
    distintos = set(valores)
    return distintos.pop() if len(distintos) == 1 else None


def _trechos_de_fotos(linhas: list[str], fonte: str, nomes: set[str]) -> list[Trecho]:
    """Linhas da(s) tabela(s) de fotos, agrupadas por sistema/subsistema consecutivos."""
    grupos: list[tuple[tuple, list[tuple[str, str | None, str | None]]]] = []
    mapa: dict[str, int] | None = None
    vistos: set[str] = set()
    for linha in linhas:
        if not linha.startswith("|"):
            mapa = None
            continue
        celulas = _celulas(linha)
        novo = _cabecalho_fotos(celulas)
        if novo:
            mapa = novo
            continue
        if mapa is None:
            continue
        texto = _texto_foto(celulas, mapa)
        if not texto or texto in vistos:
            continue
        vistos.add(texto)
        chave = (_valor(celulas, mapa, "sistema"), _valor(celulas, mapa, "subsistema"))
        item = (anonimizar(texto, nomes), _valor(celulas, mapa, "tipo"), normalizar_grau(_valor(celulas, mapa, "grau")))
        if grupos and grupos[-1][0] == chave:
            grupos[-1][1].append(item)
        else:
            grupos.append((chave, [item]))

    trechos: list[Trecho] = []
    for (sistema, _sub), itens in grupos:
        lote: list[tuple[str, str | None, str | None]] = []

        def fechar(lote_atual: list, sistema: str | None = sistema) -> None:
            if not lote_atual:
                return
            texto = " | ".join(i[0] for i in lote_atual)
            trechos.append(
                Trecho(
                    fonte=fonte, texto=texto, sistema=sistema,
                    tipo_anomalia=_comum([i[1] for i in lote_atual]), grau_risco=_comum([i[2] for i in lote_atual]),
                )
            )

        for item in itens:
            texto_item = _partir_longo(item[0])[0] if len(item[0]) > MAX_CARACTERES else item[0]
            item = (texto_item, item[1], item[2])
            tamanho = sum(len(i[0]) + 3 for i in lote)
            if lote and tamanho + len(item[0]) > MAX_CARACTERES:
                if tamanho >= PISO_SOBRA:
                    fechar(lote)
                lote = []
            lote.append(item)
            if sum(len(i[0]) + 3 for i in lote) >= MIN_CARACTERES:
                fechar(lote)
                lote = []
        if lote:
            sobra = " | ".join(i[0] for i in lote)
            anterior = trechos[-1] if trechos and trechos[-1].sistema == sistema else None
            if anterior and len(anterior.texto) + 3 + len(sobra) <= MAX_CARACTERES:
                todos = [anterior.tipo_anomalia, *[i[1] for i in lote]]
                graus = [anterior.grau_risco, *[i[2] for i in lote]]
                trechos[-1] = Trecho(
                    fonte=fonte, texto=f"{anterior.texto} | {sobra}", sistema=sistema,
                    tipo_anomalia=_comum(todos), grau_risco=_comum(graus),
                )
            elif len(sobra) >= PISO_SOBRA:
                fechar(lote)
    return trechos


def _trechos_de_prosa(linhas: list[str], fonte: str, nomes: set[str], com_tabelas: bool) -> list[Trecho]:
    secoes: list[list[str]] = [[]]
    paragrafo: list[str] = []
    celulas_vistas: set[str] = set()

    def fechar_paragrafo() -> None:
        if paragrafo:
            texto = ""
            for parte in paragrafo:
                texto = texto[:-1] + parte if texto.endswith("-") else f"{texto} {parte}".strip()
            secoes[-1].append(texto)
            paragrafo.clear()

    for bruta in linhas:
        linha = bruta.strip()
        if linha.startswith("#"):
            fechar_paragrafo()
            if linha.startswith("## "):
                secoes.append([])
            continue
        if linha.startswith("|"):
            fechar_paragrafo()
            if com_tabelas:
                for c in _celulas(linha):
                    c = _espacos(c)
                    if (
                        len(c) >= MIN_LINHA_PROSA and c not in celulas_vistas and _parece_texto(c)
                        and not LINHA_CABECALHO_PESSOAL.search(c)
                    ):
                        celulas_vistas.add(c)
                        secoes[-1].append(c)
            continue
        if not linha or linha.startswith("!["):
            fechar_paragrafo()
            continue
        if LINHA_CABECALHO_PESSOAL.search(linha) and len(linha) < 90:
            fechar_paragrafo()
            continue
        if len(linha) >= MIN_LINHA_PROSA and _parece_texto(linha):
            paragrafo.append(linha)
        elif paragrafo and linha[-1:] in ".;:":
            paragrafo.append(linha)
            fechar_paragrafo()
        else:
            fechar_paragrafo()
    fechar_paragrafo()

    trechos: list[Trecho] = []
    for blocos in secoes:
        for texto in empacotar([anonimizar(b, nomes) for b in blocos]):
            trechos.append(
                Trecho(
                    fonte=fonte, texto=texto, sistema=inferir_sistema(texto),
                    tipo_anomalia=(_unico(_TIPO_PROSA, texto) or "").capitalize() or None,
                    grau_risco=normalizar_grau(_unico(_GRAU_PROSA, texto)),
                )
            )
    return trechos


def extrair_trechos(conteudo: str, fonte: str) -> list[Trecho]:
    """Trechos anonimizados de um `.md` convertido, sem repetição de texto."""
    linhas = conteudo.splitlines()
    nomes = nomes_de_assinatura(linhas)
    fotos = _trechos_de_fotos(linhas, fonte, nomes)
    # Planilha com tabela de fotos: as demais células repetem as mesmas observações (formulário).
    prosa = _trechos_de_prosa(linhas, fonte, nomes, com_tabelas=not fotos)
    unicos: dict[str, Trecho] = {}
    for t in [*fotos, *prosa]:
        unicos.setdefault(t.hash, t)
    return list(unicos.values())


def arquivos_fonte(pasta: Path) -> list[Path]:
    pasta = pasta.resolve()
    if PASTA_PROIBIDA in pasta.parts:
        raise SystemExit(f"Recusado: {PASTA_PROIBIDA}/ guarda os originais do cliente; use 00_docs/convertidos.")
    if not pasta.is_dir():
        raise SystemExit(f"Pasta não encontrada: {pasta}")
    return sorted(p for p in pasta.glob("*.md") if p.name not in IGNORADOS)


def coletar(pasta: Path) -> list[Trecho]:
    unicos: dict[str, Trecho] = {}
    for arquivo in arquivos_fonte(pasta):
        for t in extrair_trechos(arquivo.read_text(encoding="utf-8"), arquivo.name):
            unicos.setdefault(t.hash, t)
    return list(unicos.values())


async def ingerir(db: AsyncSession, trechos: list[Trecho]) -> tuple[int, int]:
    """Insere os trechos novos (por `hash`); devolve (inseridos, já existentes)."""
    inseridos = 0
    for i in range(0, len(trechos), 200):
        lote = trechos[i : i + 200]
        valores = [
            {
                "fonte": t.fonte[:300], "tipo": t.tipo, "sistema": t.sistema, "tipo_anomalia": t.tipo_anomalia,
                "grau_risco": t.grau_risco, "texto": t.texto, "hash": t.hash,
            }
            for t in lote
        ]
        resultado = await db.execute(
            insert(TrechoConhecimentoIA).values(valores).on_conflict_do_nothing(index_elements=["hash"])
            .returning(TrechoConhecimentoIA.id)
        )
        inseridos += len(resultado.all())
    await db.commit()
    return inseridos, len(trechos) - inseridos


def _resumo(trechos: list[Trecho]) -> str:
    por_fonte = Counter(t.fonte for t in trechos)
    tamanhos = sorted(len(t.texto) for t in trechos) or [0]
    linhas = [f"{n:5d}  {fonte}" for fonte, n in sorted(por_fonte.items())]
    linhas.append(
        f"Total: {len(trechos)} trechos; tamanho min/mediana/max = "
        f"{tamanhos[0]}/{tamanhos[len(tamanhos) // 2]}/{tamanhos[-1]} caracteres"
    )
    linhas.append(
        f"Com sistema: {sum(1 for t in trechos if t.sistema)}; com tipo_anomalia: "
        f"{sum(1 for t in trechos if t.tipo_anomalia)}; com grau_risco: {sum(1 for t in trechos if t.grau_risco)}"
    )
    return "\n".join(linhas)


async def _gravar(trechos: list[Trecho]) -> tuple[int, int]:
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        return await ingerir(db, trechos)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--pasta", type=Path, default=PASTA_PADRAO, help="pasta dos .md convertidos")
    p.add_argument("--dry-run", action="store_true", help="só mostra contagens, sem gravar")
    p.add_argument("--amostras", type=int, default=0, help="com --dry-run, imprime N trechos de exemplo")
    args = p.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # console Windows (cp1252) não imprime todos os caracteres
    trechos = coletar(args.pasta)
    print(_resumo(trechos))
    if args.dry_run:
        passo = max(len(trechos) // max(args.amostras, 1), 1)
        for t in trechos[::passo][: args.amostras]:
            print(f"\n--- {t.fonte} | {t.sistema} | {t.tipo_anomalia} | {t.grau_risco}\n{t.texto}")
        return 0
    inseridos, existentes = asyncio.run(_gravar(trechos))
    print(f"Inseridos: {inseridos}; já existentes: {existentes}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
