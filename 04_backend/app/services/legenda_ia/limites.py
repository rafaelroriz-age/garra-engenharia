"""Limite de taxa da geração de legenda por IA (DEC-42 C, SEG-IA-01).

Janela deslizante por usuário e por foto, com relógio injetável. A verificação e o registro são
atômicos: pedidos simultâneos não passam juntos, e uma recusa não gasta cota de nenhuma regra.

Mesmo mecanismo de `app/core/rate_limit.py` (DEC-24), que não pôde ser reaproveitado direto: ele
conta falhas de login, com constantes fixas e `time.monotonic` embutido.

Limitação: o estado vive no processo. Com N workers/réplicas o limite efetivo vira N vezes o
configurado e reiniciar zera os contadores; para isso, migrar para Redis (ADR-06/DEC-10) ou banco,
mantendo `consumir`.
"""
import math
import time
import uuid
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache
from threading import Lock
from typing import Literal

from app.core.config import Settings, get_settings
from app.core.errors import DomainError

_SEGUNDOS_POR_DIA = 86400
_INTERVALO_EXPURGO_SEGUNDOS = 60


class LimiteLegendaIAExcedido(DomainError):
    """429 RFC 7807. `retry_after` também vai no corpo: o handler global não repassa headers."""

    def __init__(self, retry_after: int) -> None:
        super().__init__(
            f"Limite de geração de legenda por IA excedido. Tente novamente em {retry_after} segundos.",
            type_suffix="legenda-ia-limite-excedido",
            title="Limite de legenda por IA excedido",
            status_code=429,
            errors=[{"field": "retry_after_segundos", "message": str(retry_after)}],
        )
        self.retry_after = retry_after


@dataclass(frozen=True)
class RegraLimite:
    alvo: Literal["usuario", "foto"]
    maximo: int
    janela_segundos: int


def construir_regras(settings: Settings) -> tuple[RegraLimite, ...]:
    return (
        RegraLimite("usuario", settings.legenda_ia_limite_por_usuario, settings.legenda_ia_janela_usuario_segundos),
        RegraLimite("usuario", settings.legenda_ia_limite_diario_por_usuario, _SEGUNDOS_POR_DIA),
        RegraLimite("foto", settings.legenda_ia_limite_por_foto, settings.legenda_ia_janela_foto_segundos),
    )


class LimitadorLegendaIA:
    def __init__(
        self, regras: tuple[RegraLimite, ...], relogio: Callable[[], float] = time.monotonic
    ) -> None:
        self._regras = regras
        self._relogio = relogio
        self._eventos: dict[tuple[RegraLimite, uuid.UUID], deque[float]] = defaultdict(deque)
        self._lock = Lock()
        self._ultimo_expurgo = relogio()

    def consumir(self, usuario_id: uuid.UUID, foto_id: uuid.UUID) -> None:
        """Registra uma geração ou lança `LimiteLegendaIAExcedido` sem registrar nada."""
        ids = {"usuario": usuario_id, "foto": foto_id}
        agora = self._relogio()
        with self._lock:
            self._expurgar(agora)
            eventos = [(regra, self._eventos[(regra, ids[regra.alvo])]) for regra in self._regras]
            espera = 0.0
            for regra, fila in eventos:
                while fila and agora - fila[0] >= regra.janela_segundos:
                    fila.popleft()
                if len(fila) >= regra.maximo:
                    espera = max(espera, regra.janela_segundos - (agora - fila[0]))
            if espera:
                raise LimiteLegendaIAExcedido(max(1, math.ceil(espera)))
            for _, fila in eventos:
                fila.append(agora)

    def chaves_ativas(self) -> int:
        with self._lock:
            return len(self._eventos)

    def _expurgar(self, agora: float) -> None:
        """Descarta chaves sem evento na janela, para a memória não crescer com fotos antigas."""
        if agora - self._ultimo_expurgo < _INTERVALO_EXPURGO_SEGUNDOS:
            return
        self._ultimo_expurgo = agora
        for (regra, alvo_id), fila in list(self._eventos.items()):
            if not fila or agora - fila[-1] >= regra.janela_segundos:
                del self._eventos[(regra, alvo_id)]


@lru_cache
def get_limitador_padrao() -> LimitadorLegendaIA:
    """Instância única por processo, com as regras das variáveis de ambiente."""
    return LimitadorLegendaIA(construir_regras(get_settings()))
