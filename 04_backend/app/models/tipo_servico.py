"""Enum `TipoServico` — os 5 relatórios emitidos pelo sistema (plano de entrega v1.0, V1-01).

`Contrato.tipo_servico` e `Inspecao.tipo` continuam `String` no banco (a migration
`a9c3e5f7b1d2` só normaliza para maiúsculas); a validação acontece nos schemas de
entrada. O enum aceita minúsculas e espaços nas bordas (`"ltip"` -> `LTIP`), porque
havia dados gravados assim antes da normalização.
"""
from enum import StrEnum


class TipoServico(StrEnum):
    RFO = "RFO"
    LTIP = "LTIP"
    RFIP = "RFIP"
    VISTORIA_CAUTELAR = "VISTORIA_CAUTELAR"
    VISTORIA_RESIDENCIAL = "VISTORIA_RESIDENCIAL"

    @classmethod
    def _missing_(cls, value: object) -> "TipoServico | None":
        if isinstance(value, str):
            normalizado = value.strip().upper()
            for membro in cls:
                if membro.value == normalizado:
                    return membro
        return None

    @classmethod
    def normalizar(cls, valor: str | None) -> "TipoServico | None":
        """Converte texto livre do banco no enum; `None` se não for um tipo conhecido."""
        if valor is None:
            return None
        try:
            return cls(valor)
        except ValueError:
            return None
