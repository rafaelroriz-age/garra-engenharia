"""Seleção da legenda de foto impressa nos relatórios (BL-38, DEC-37 DP-9).

Funções puras, sem acesso a banco. Aceitam objeto (ORM/namespace) ou dict.
Regra: a legenda impressa é sempre `legenda`; `legenda_ia_sugerida` nunca
entra no relatório, qualquer que seja o status (NULL, `rascunho`, `aprovada`).
"""
from __future__ import annotations

from typing import Any

STATUS_RASCUNHO = "rascunho"


def _campo(foto: Any, nome: str) -> Any:
    if isinstance(foto, dict):
        return foto.get(nome)
    return getattr(foto, nome, None)


def legenda_para_relatorio(foto: Any) -> str:
    """Legenda a imprimir; string vazia se não houver."""
    return (_campo(foto, "legenda") or "").strip()


def foto_ia_em_rascunho(foto: Any) -> bool:
    """True se a foto tem sugestão de IA ainda não aprovada (`rascunho`)."""
    return _campo(foto, "status_validacao_ia") == STATUS_RASCUNHO


def sinalizar_fotos_ia_em_rascunho(fotos: list[Any]) -> list[int]:
    """Índices das fotos com legenda de origem IA ainda em rascunho."""
    return [i for i, f in enumerate(fotos) if foto_ia_em_rascunho(f)]
