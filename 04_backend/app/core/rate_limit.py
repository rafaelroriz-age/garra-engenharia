"""Limitador de tentativas de login em memória (OWASP A07, BL-23).

Conta apenas tentativas MALSUCEDIDAS por (IP, e-mail) dentro de uma janela
deslizante; um login bem-sucedido zera o contador. Isso freia força bruta sem
penalizar uso legítimo.

Escopo consciente desta implementação: o estado vive no processo. Para o porte
atual (uso individual/pequena equipe, um único worker) é suficiente. Se a API
passar a rodar com múltiplos workers/réplicas, migrar o contador para o Redis
já previsto em ADR-06/DEC-10 — a interface pública (`registrar_falha`,
`verificar_bloqueio`, `registrar_sucesso`) não muda.
"""
import time
from collections import defaultdict
from threading import Lock

MAX_TENTATIVAS = 5
JANELA_SEGUNDOS = 15 * 60

_tentativas: dict[tuple[str, str], list[float]] = defaultdict(list)
_lock = Lock()


def _limpar_expiradas(chave: tuple[str, str], agora: float) -> list[float]:
    recentes = [t for t in _tentativas[chave] if agora - t < JANELA_SEGUNDOS]
    _tentativas[chave] = recentes
    return recentes


def segundos_ate_liberar(ip: str, email: str) -> int:
    """Retorna quantos segundos faltam para liberar; 0 se não estiver bloqueado."""
    agora = time.monotonic()
    chave = (ip, email.lower())
    with _lock:
        recentes = _limpar_expiradas(chave, agora)
        if len(recentes) < MAX_TENTATIVAS:
            return 0
        return max(1, int(JANELA_SEGUNDOS - (agora - recentes[0])))


def registrar_falha(ip: str, email: str) -> None:
    agora = time.monotonic()
    chave = (ip, email.lower())
    with _lock:
        _limpar_expiradas(chave, agora)
        _tentativas[chave].append(agora)


def registrar_sucesso(ip: str, email: str) -> None:
    with _lock:
        _tentativas.pop((ip, email.lower()), None)


def resetar() -> None:
    """Limpa todo o estado — usado apenas por testes."""
    with _lock:
        _tentativas.clear()
