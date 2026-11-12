"""Anonimização heurística de texto livre para a IA (BL-34, IA-05; R-10).

Troca por marcadores genéricos: condomínio/edifício/empreendimento/torre, empresa, endereço, bairro,
CEP, matrícula, unidade, pessoas (com pronome de tratamento ou assinatura de engenheiro), CREA,
CPF/CNPJ, e-mail e telefone. É usada na ingestão dos relatórios históricos
(`app/scripts/ingerir_conhecimento_ia.py`) e nas legendas aprovadas usadas como few-shot
(`recuperacao.py`), que podem ser de outro cliente. É regex, **não** garantia: nome de pessoa sem
pronome de tratamento no meio do texto não é detectado.
"""
import re

from app.services.legenda_ia.contexto import limpar_dados_pessoais

_MAI = "A-ZÁÉÍÓÚÂÊÔÃÕÇ"
_MIN = "a-záéíóúâêôãõçü"
_PALAVRA_PROPRIA = rf"[{_MAI}][{_MIN}]+"
_CONECTOR = r"(?:d[aeo]s?|e)"
_NOME_PESSOA = rf"{_PALAVRA_PROPRIA}(?:\s+(?:{_CONECTOR}\s+)?{_PALAVRA_PROPRIA})+"
# Após pronome de tratamento basta um nome («Sr. Wesley»).
_TRATAMENTO = re.compile(
    rf"\b(?:Sr\.?ª|Srª|Sra|Sr|Dra|Dr|Engª|Eng\.ª|Arq)\.?\s+"
    rf"({_PALAVRA_PROPRIA}(?:\s+(?:{_CONECTOR}\s+)?{_PALAVRA_PROPRIA})*)"
)
_LINHA_SO_NOME = re.compile(rf"^\s*({_NOME_PESSOA})\s*$")
_EDIFICACAO = re.compile(
    rf"\b(?:Condom[íi]nio(?:\s+do)?(?:\s+Edif[íi]cio)?|Cond\.|Edif[íi]cio|Ed\.|Residencial)"
    rf"\s+(?:[{_MAI}][\w\u2019'\u00b4]*|D[\u2019'\u00b4]\s?\w+)(?:\s+(?:[{_MAI}][\w\u2019'\u00b4]*|D[\u2019'\u00b4]\s?\w+))*"
)
# Nomes próprios dos relatórios de exemplo que aparecem sem «Condomínio»/«LTDA» antes ou depois.
_NOMES_CONHECIDOS = re.compile(
    r"cortina\s*d?\s*[\u2019'\u00b4]?\s*amp[a-z]*|new\s+york|(?:opus\s+)?gyro(?:\s+ricardo\s+paranhos|\s+market)?", re.IGNORECASE
)
_EMPREENDIMENTO = re.compile(rf"\b([Ee]mpreendimento)\s+[{_MAI}][\w\u2019'\u00b4]*(?:\s+[{_MAI}][\w\u2019'\u00b4]*)*")
# Firma pelo ramo: «Fulano Arquitetura e Interiores», «Monte Sinai Impermeabilizações e Reformas Prediais».
_FIRMA = re.compile(
    rf"(?:\b[{_MAI}][{_MIN}]+\s+){{1,4}}(?:Arquitetura|Impermeabiliza[çc][õo]es|Engenharia|Construtora|Incorporadora)"
    rf"(?:\s+e\s+[{_MAI}][{_MIN}]+(?:\s+[{_MAI}][{_MIN}]+)*)?"
)
_EMPRESAS_CONHECIDAS = re.compile(r"urb[âa]nica(?:\s+(?:engenharia|construtora|e))*", re.IGNORECASE)
_ENDERECO = re.compile(
    r"\b(?:Rua|R\.|Avenida|Av\.|Alameda|Al\.|Rodovia|Travessa|Pra[çc]a|Estrada)\s+[^,;\n]{2,60}"
)
_QUADRA_LOTE = re.compile(r"\b(?:Qd|Quadra|Lt|Lote)\.?\s*\d+[A-Za-z]?\b")
_BAIRRO = re.compile(rf"\b(?:Setor|Bairro|Jardim|Parque)\s+[{_MAI}][{_MIN}]+(?:\s+[{_MAI}][{_MIN}]+)*")
_CEP = re.compile(r"\bCEP[:.]?\s*\d{2}\.?\d{3}-?\d{3}\b", re.IGNORECASE)
_MATRICULA = re.compile(r"\bMatr[íi]cula:?\s*(?:n[º°o]\.?\s*)?[\d.]+", re.IGNORECASE)
_UNIDADE = re.compile(r"\b(?:Apartamento|Apto\.?|Ap\.)\s*(?:n[º°o]\.?\s*)?\d+\b", re.IGNORECASE)
_CREA = re.compile(r"\bCREA(?:-[A-Z]{2})?\s*(?:n[º°o]\.?\s*)?[\d./-]+(?:/?[A-Z]-?[A-Z]{0,2})?")
_TELEFONE_LIVRE = re.compile(r"\(\d{2}\)\s*9?\s?\d{4}[-\s]?\d{4}")
LINHA_CABECALHO_PESSOAL = re.compile(
    r"CREA|@|Eng\.\s*Civil|Engenheir[oa]\s+Civil|\bCEP\b|^\s*(?:Rua|Av\.|Avenida)\s", re.IGNORECASE
)
_TORRE = re.compile(rf"\b(Torres?|Bloco)\s+[{_MAI}][{_MIN}]+")
_EMPRESA = re.compile(
    rf"(?:\b[{_MAI}][\w&]*\s+(?:(?:e|de|da|do)\s+)?){{1,6}}(?:LTDA|Ltda|S/A|S\.A\.|EIRELI)\b\.?"
)


def nomes_de_assinatura(linhas: list[str]) -> set[str]:
    """Nomes de pessoas citados no arquivo: linha só com nome antes de «Eng./CREA», e após Sr./Sra./Dr."""
    nomes: set[str] = set()
    for i, linha in enumerate(linhas):
        for m in _TRATAMENTO.finditer(linha):
            nomes.add(m.group(1))
        seguinte = linhas[i + 1] if i + 1 < len(linhas) else ""
        m = _LINHA_SO_NOME.match(linha)
        if m and LINHA_CABECALHO_PESSOAL.search(seguinte):
            nomes.add(m.group(1))
    return nomes


def anonimizar(texto: str, nomes: set[str] | frozenset[str] = frozenset()) -> str:
    """Troca dados identificadores por marcadores genéricos (heurística; ver docstring do módulo)."""
    t = _TRATAMENTO.sub("[PESSOA]", texto)
    for nome in sorted(nomes, key=len, reverse=True):
        t = t.replace(nome, "[PESSOA]")
    t = _EDIFICACAO.sub("[EDIFICAÇÃO]", t)
    t = _NOMES_CONHECIDOS.sub("[EDIFICAÇÃO]", t)
    t = _TORRE.sub(lambda m: f"{m.group(1)} [NOME]", t)
    t = _EMPRESA.sub("[EMPRESA]", t)
    t = _EMPRESAS_CONHECIDAS.sub("[EMPRESA]", t)
    t = _FIRMA.sub("[EMPRESA]", t)
    t = _EMPREENDIMENTO.sub(lambda m: f"{m.group(1)} [EDIFICAÇÃO]", t)
    t = _CEP.sub("[CEP]", t)
    t = _MATRICULA.sub("Matrícula [REGISTRO]", t)
    t = _BAIRRO.sub("[BAIRRO]", t)
    t = _ENDERECO.sub("[ENDEREÇO]", t)
    t = _QUADRA_LOTE.sub("[ENDEREÇO]", t)
    t = _UNIDADE.sub("[UNIDADE]", t)
    t = _CREA.sub("CREA [REGISTRO]", t)
    t = _TELEFONE_LIVRE.sub("[TELEFONE]", t)
    return limpar_dados_pessoais(t) or ""
