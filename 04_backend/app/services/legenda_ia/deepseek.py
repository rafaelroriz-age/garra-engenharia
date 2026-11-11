"""Adapter DeepSeek Platform API (B-04, V1-07): POST {base_url}/chat/completions.

A chave e a imagem nunca vão para log nem para mensagens de erro. A legenda bruta chega já
delimitada (DEC-42 D) e segue em mensagem de usuário própria, separada do prompt (SEG-IA-08).
Sem modelo com visão confirmado, o modo padrão é `texto`: a imagem não é enviada.
"""
import base64
import io
import json
import logging

import httpx
from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.config import Settings
from app.core.errors import DomainError
from app.services.legenda_ia.contrato import LegendaIAResultado
from app.services.legenda_ia.saneamento import SaidaLegendaIAInvalida

logger = logging.getLogger(__name__)

LADO_MAX_PX = 1024
_INSTRUCAO_JSON = (
    'Responda somente com um objeto JSON: {"legenda_sugerida": string, '
    '"alertas": [string], "pendencias": [string]}.'
)


class ProvedorIAIndisponivel(DomainError):
    def __init__(self, motivo: str) -> None:
        super().__init__(
            f"O provedor de IA não respondeu adequadamente ({motivo}).",
            type_suffix="legenda-ia-indisponivel",
            title="Legenda por IA indisponível",
            status_code=502,
        )


def reduzir_imagem_para_data_uri(imagem: bytes, lado_max: int = LADO_MAX_PX) -> str:
    """JPEG com no máximo `lado_max` px no maior lado, como data URI base64."""
    try:
        with Image.open(io.BytesIO(imagem)) as origem:
            img = ImageOps.exif_transpose(origem).convert("RGB")
    except (UnidentifiedImageError, OSError) as exc:
        raise ProvedorIAIndisponivel("imagem ilegível") from exc
    img.thumbnail((lado_max, lado_max))
    saida = io.BytesIO()
    img.save(saida, format="JPEG", quality=85)
    return "data:image/jpeg;base64," + base64.b64encode(saida.getvalue()).decode("ascii")


def _lista_textos(valor: object) -> list[str]:
    if valor is None:
        return []
    if not isinstance(valor, list) or not all(isinstance(i, str) for i in valor):
        raise SaidaLegendaIAInvalida
    return valor


class DeepSeekLegendaIAClient:
    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = "https://api.deepseek.com",
        modelo: str = "deepseek-flash",
        timeout_s: float = 30.0,
        enviar_imagem: bool = False,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._api_key = api_key
        self._url = base_url.rstrip("/") + "/chat/completions"
        self._modelo = modelo
        self._timeout = timeout_s
        self._enviar_imagem = enviar_imagem
        self._transport = transport

    @classmethod
    def de_settings(
        cls, settings: Settings, transport: httpx.AsyncBaseTransport | None = None
    ) -> "DeepSeekLegendaIAClient":
        chave = settings.deepseek_api_key.get_secret_value() if settings.deepseek_api_key else ""
        return cls(
            chave,
            base_url=settings.deepseek_base_url,
            modelo=settings.deepseek_modelo,
            timeout_s=settings.deepseek_timeout_s,
            enviar_imagem=settings.deepseek_enviar_imagem,
            transport=transport,
        )

    def _mensagens(self, imagem: bytes, prompt: str, legenda_bruta: str | None) -> list[dict]:
        sistema = f"{prompt}\n\n{_INSTRUCAO_JSON}"
        texto = legenda_bruta or "(sem legenda bruta informada)"
        if self._enviar_imagem:
            usuario: object = [
                {"type": "image_url", "image_url": {"url": reduzir_imagem_para_data_uri(imagem)}},
                {"type": "text", "text": texto},
            ]
        else:
            usuario = texto
        return [{"role": "system", "content": sistema}, {"role": "user", "content": usuario}]

    async def gerar_legenda(
        self, imagem: bytes, prompt: str, legenda_bruta: str | None = None
    ) -> LegendaIAResultado:
        modo = "imagem" if self._enviar_imagem else "texto"
        corpo = {
            "model": self._modelo,
            "messages": self._mensagens(imagem, prompt, legenda_bruta),
            "response_format": {"type": "json_object"},
            "stream": False,
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout, transport=self._transport) as http:
                resp = await http.post(
                    self._url, json=corpo, headers={"Authorization": f"Bearer {self._api_key}"}
                )
        except httpx.TimeoutException as exc:
            logger.warning("DeepSeek: timeout (modo=%s)", modo)
            raise ProvedorIAIndisponivel("tempo esgotado") from exc
        except httpx.HTTPError as exc:
            logger.warning("DeepSeek: falha de rede %s (modo=%s)", type(exc).__name__, modo)
            raise ProvedorIAIndisponivel("falha de rede") from exc
        if resp.status_code != 200:
            logger.warning("DeepSeek: HTTP %s (modo=%s)", resp.status_code, modo)
            raise ProvedorIAIndisponivel(f"HTTP {resp.status_code}")
        resultado = self._converter(resp, modo)
        logger.info("DeepSeek: legenda gerada (modelo=%s, modo=%s)", self._modelo, modo)
        return resultado

    @staticmethod
    def _converter(resp: httpx.Response, modo: str) -> LegendaIAResultado:
        try:
            conteudo = resp.json()["choices"][0]["message"]["content"]
            dados = json.loads(conteudo)
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise SaidaLegendaIAInvalida from exc
        legenda = dados.get("legenda_sugerida") if isinstance(dados, dict) else None
        if not isinstance(legenda, str) or not legenda.strip():
            raise SaidaLegendaIAInvalida
        return LegendaIAResultado(
            legenda_sugerida=legenda,
            alertas=_lista_textos(dados.get("alertas")),
            pendencias=_lista_textos(dados.get("pendencias")),
            modo=modo,
        )
