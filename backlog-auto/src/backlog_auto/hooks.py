"""Hooks do Claude Code. Uso em settings.json: `python -m backlog_auto.hooks guard|lembrete`.

Falham aberto: qualquer erro interno (sem backlog.toml, JSON inválido) deixa a ferramenta seguir.
"""
from __future__ import annotations

import json
import re
import sys

from .config import achar_raiz, carregar
from .guard import avaliar


def _evento():
    try:
        return json.load(sys.stdin)
    except ValueError:
        return None


def guard() -> int:
    evento = _evento()
    if not evento or achar_raiz() is None:
        return 0
    cfg = carregar()
    g = cfg.d["guard"]
    if not g["ativo"]:
        return 0
    achados = avaliar(cfg, evento.get("tool_input") or {})
    if not achados:
        return 0
    print(f"{g['mensagem']} Padrões: {', '.join(achados)}. Para uma escrita legítima, peça a uma pessoa que defina "
          f"{g['variavel_liberacao']}=1 na sessão.", file=sys.stderr)
    return 2


def lembrete() -> int:
    evento = _evento()
    if not evento or achar_raiz() is None:
        return 0
    cfg = carregar()
    r = cfg.d["lembrete"]
    if not r["ativo"]:
        return 0
    entrada = evento.get("tool_input") or {}
    caminho = (entrada.get("file_path") or "").replace("\\", "/")
    comando = entrada.get("command") or ""
    if "/.claude/" in caminho:
        return 0
    codigo = re.compile(r"\.(" + "|".join(map(re.escape, r["extensoes"])) + r")$", re.I)
    execucao = re.compile(r"\b(" + "|".join(map(re.escape, r["execucao"])) + r")\b", re.I)
    if not (codigo.search(caminho) or execucao.search(comando)):
        return 0
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": r["texto"]}}))
    return 0


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    alvo = {"guard": guard, "lembrete": lembrete}.get(argv[0] if argv else "")
    if alvo is None:
        print("uso: python -m backlog_auto.hooks guard|lembrete", file=sys.stderr)
        return 1
    try:
        return alvo()
    except Exception:  # noqa: BLE001 — hook nunca pode travar o agente por erro interno
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
