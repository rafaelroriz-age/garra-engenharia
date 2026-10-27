"""Barreira configurável contra alteração/remoção de dados existentes (SQL, Delta, arquivos).

Inspeciona o TEXTO de arquivos de código escritos e de comandos executados pelo agente.
Limite: não pega escrita montada dinamicamente em tempo de execução.
Liberação: só uma pessoa, definindo a variável de ambiente `guard.variavel_liberacao` = 1.
"""
from __future__ import annotations

import os
import re

from .config import Config

CODIGO = re.compile(r"\.(py|ipynb|sql)$", re.I)

# O destino é montado em duas partes para o próprio código-fonte não casar com o padrão que ele define.
_PASTA_TABELAS = "/Tab" + "les/"

PRESETS: dict[str, dict[str, str]] = {
    "sql": {
        "DML/DDL SQL": r"\b(INSERT\s+INTO|UPDATE\s+[\w.\[\]`\"]+\s+SET|DELETE\s+FROM|DROP\s+(TABLE|VIEW|SCHEMA|DATABASE)"
                       r"|TRUNCATE\s+TABLE|ALTER\s+(TABLE|VIEW|SCHEMA)|MERGE\s+INTO|CREATE\s+OR\s+REPLACE)\b",
    },
    "delta": {
        "saveAsTable/insertInto": r"\.(saveAsTable|insertInto)\s*\(",
        "operação Delta de escrita": r"DeltaTable[\s\S]{0,200}\.(delete|update|merge|vacuum|optimize)\s*\(",
        "gravação em pasta de tabelas": r"(\.write\b|\.save\(|to_parquet\(|to_delta\(|put\(|upload)[^\n]{0,200}"
                                         + re.escape(_PASTA_TABELAS),
    },
    "destrutivo": {
        "rm -rf": r"\brm\s+-[a-z]*r[a-z]*\s+(/|~|\*|\.\.?)(\s|$)",
        "git push --force": r"git\s+push\s+[^\n]*(--force\b|\s-f\b)",
        "Remove-Item recursivo": r"Remove-Item[^\n]*-Recurse",
    },
}


def padroes(cfg: Config) -> dict[str, re.Pattern]:
    g = cfg.d["guard"]
    brutos: dict[str, str] = {}
    for p in g["presets"]:
        if p not in PRESETS:
            raise ValueError(f"preset de guard desconhecido: {p} (disponíveis: {', '.join(PRESETS)})")
        brutos.update(PRESETS[p])
    brutos.update(g["padroes"])
    return {nome: re.compile(rx, re.I) for nome, rx in brutos.items()}


def liberado(cfg: Config) -> bool:
    return os.environ.get(cfg.d["guard"]["variavel_liberacao"]) == "1"


def violacoes(cfg: Config, texto: str) -> list[str]:
    if liberado(cfg) or not texto:
        return []
    return [nome for nome, rx in padroes(cfg).items() if rx.search(texto)]


def avaliar(cfg: Config, entrada: dict) -> list[str]:
    """Aplica as regras ao `tool_input` de um evento PreToolUse."""
    g = cfg.d["guard"]
    caminho = (entrada.get("file_path") or "").replace("\\", "/")
    if any(i in caminho for i in g["isentos"]):
        return []
    if CODIGO.search(caminho):
        texto = entrada.get("content") or entrada.get("new_string") or ""
    else:
        comando = entrada.get("command") or ""
        gatilho = g["comando_gatilho"]
        texto = comando if (not gatilho or re.search(gatilho, comando, re.I)) else ""
    return violacoes(cfg, texto)
