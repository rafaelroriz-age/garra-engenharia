"""Adapter DeepSeek Platform API (B-04, V1-07): POST {base_url}/chat/completions.

A chave e a imagem nunca vão para log nem para mensagens de erro. A legenda bruta chega já
delimitada (DEC-42 D) dentro do `ContextoLegenda` e segue na mensagem de usuário, nunca no `system`
(SEG-IA-08). Sem modelo com visão confirmado, o modo padrão é `texto`: a imagem não é enviada.

Cache de prefixo da DeepSeek: a API reaproveita (a preço menor) o prefixo idêntico das mensagens.
Por isso o `system` é `prompt + instrução JSON` e **nada variável** entra nele: contexto, legenda
bruta, ids e datas ficam só na mensagem `user`. `_mensagens` mantém essa ordem fixa.

Retry: até `MAX_REENVIOS` novas tentativas com backoff exponencial curto, só para 429, 5xx e
timeout; os demais 4xx e falhas de rede falham na hora.
"""
import asyncio
import base64
import io
import json
import logging

import httpx
from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.config import Settings
from app.core.errors import DomainError
from app.services.legenda_ia.contexto import ContextoLegenda
from app.services.legenda_ia.contrato import LegendaIAResultado
from app.services.legenda_ia.saneamento import SaidaLegendaIAInvalida

logger = logging.getLogger(__name__)

LADO_MAX_PX = 1024
MAX_REENVIOS = 2
BACKOFF_BASE_S = 0.5
# Contrato do cliente (prompt-lado-cliente.md §25) → enums de `foto.py` (NIVEIS_CERTEZA_IA).
# `nao_aplicavel` é válido no prompt mas não existe no banco: vira None sem alerta.
_NIVEL_CERTEZA = {
    "constatacao_direta": "constatacao_direta",
    "indicio_tecnico": "indicio_tecnico",
    "hipotese_tecnica": "hipotese_tecnica",
    "causa_documentalmente_comprovada": "causa_comprovada",
    "nao_aplicavel": None,
}
_STATUS_CONHECIDOS = {"aprovada", "aprovada_com_ressalva", "revisar", "informacao_insuficiente"}
_STATUS_COM_ALERTA = {
    "aprovada_com_ressalva": "O modelo aprovou a legenda com ressalvas: revise antes de aprovar.",
    "revisar": "O modelo pediu revisão da legenda.",
    "informacao_insuficiente": "O modelo indicou informação insuficiente para a legenda.",
}
# Instrução fixa (parte do prefixo cacheável do `system`); aceita as chaves do prompt do cliente.
_INSTRUCAO_JSON = (
    'Responda somente com um objeto JSON: {"legenda_sugerida": string, '
    '"alertas": [string], "pendencias": [string], "nivel_certeza": string, '
    '"status_validacao": string}.'
)
_CHAVES_USO = ("prompt_tokens", "prompt_cache_hit_tokens", "prompt_cache_miss_tokens", "completion_tokens")


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


def _extrair_uso(usage: object) -> dict[str, int] | None:
    if not isinstance(usage, dict):
        return None
    uso = {c: usage[c] for c in _CHAVES_USO if isinstance(usage.get(c), int)}
    return uso or None


class DeepSeekLegendaIAClient:
    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = "https://api.deepseek.com",
        modelo: str = "deepseek-flash",
        timeout_s: float = 30.0,
        backoff_s: float = BACKOFF_BASE_S,
        enviar_imagem: bool = False,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._api_key = api_key
        self._url = base_url.rstrip("/") + "/chat/completions"
        self._modelo = modelo
        self._timeout = timeout_s
        self._backoff = backoff_s
        self.enviar_imagem = enviar_imagem
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

    def _mensagens(self, contexto: ContextoLegenda, prompt: str, imagem: bytes | None) -> list[dict]:
        """`system` idêntico para o mesmo prompt; todo dado variável vai na mensagem `user`."""
        sistema = f"{prompt}\n\n{_INSTRUCAO_JSON}"
        bruta = contexto.legenda_bruta or "(sem legenda bruta informada)"
        texto = f"{contexto.bloco_dados()}\n\nLEGENDA BRUTA\n{bruta}"
        if self.enviar_imagem and imagem is not None:
            usuario: object = [
                {"type": "image_url", "image_url": {"url": reduzir_imagem_para_data_uri(imagem)}},
                {"type": "text", "text": texto},
            ]
        else:
            usuario = texto
        return [{"role": "system", "content": sistema}, {"role": "user", "content": usuario}]

    async def _enviar(self, corpo: dict, modo: str) -> httpx.Response:
        for tentativa in range(MAX_REENVIOS + 1):
            ultima = tentativa == MAX_REENVIOS
            try:
                async with httpx.AsyncClient(timeout=self._timeout, transport=self._transport) as http:
                    resp = await http.post(
                        self._url, json=corpo, headers={"Authorization": f"Bearer {self._api_key}"}
                    )
            except httpx.TimeoutException as exc:
                logger.warning("DeepSeek: timeout (modo=%s, tentativa=%d)", modo, tentativa + 1)
                if ultima:
                    raise ProvedorIAIndisponivel("tempo esgotado") from exc
            except httpx.HTTPError as exc:
                logger.warning("DeepSeek: falha de rede %s (modo=%s)", type(exc).__name__, modo)
                raise ProvedorIAIndisponivel("falha de rede") from exc
            else:
                if resp.status_code == 200:
                    return resp
                logger.warning(
                    "DeepSeek: HTTP %s (modo=%s, tentativa=%d)", resp.status_code, modo, tentativa + 1
                )
                if not (resp.status_code == 429 or resp.status_code >= 500) or ultima:
                    raise ProvedorIAIndisponivel(f"HTTP {resp.status_code}")
            await asyncio.sleep(self._backoff * 2**tentativa)
        raise AssertionError("inalcançável")  # pragma: no cover

    async def gerar_legenda(
        self, contexto: ContextoLegenda, prompt: str, imagem: bytes | None = None
    ) -> LegendaIAResultado:
        modo = "imagem" if self.enviar_imagem and imagem is not None else "texto"
        corpo = {
            "model": self._modelo,
            "messages": self._mensagens(contexto, prompt, imagem),
            "response_format": {"type": "json_object"},
            "stream": False,
        }
        resp = await self._enviar(corpo, modo)
        resultado = self._converter(resp, modo, self._modelo)
        logger.info("DeepSeek: legenda gerada (modelo=%s, modo=%s)", self._modelo, modo)
        return resultado

    @staticmethod
    def _converter(resp: httpx.Response, modo: str, modelo: str) -> LegendaIAResultado:
        try:
            corpo = resp.json()
            conteudo = corpo["choices"][0]["message"]["content"]
            dados = json.loads(conteudo)
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise SaidaLegendaIAInvalida from exc
        if not isinstance(dados, dict):
            raise SaidaLegendaIAInvalida
        legenda = dados.get("legenda_sugerida", dados.get("legenda_tecnica"))
        if not isinstance(legenda, str) or not legenda.strip():
            raise SaidaLegendaIAInvalida
        alertas = list(_lista_textos(dados.get("alertas")))
        nivel = dados.get("nivel_certeza")
        if nivel is not None and nivel not in _NIVEL_CERTEZA:
            alertas.append("Nível de certeza desconhecido devolvido pelo modelo; campo não preenchido.")
        status = dados.get("status_validacao")
        if status in _STATUS_COM_ALERTA:
            alertas.append(_STATUS_COM_ALERTA[status])
        elif status is not None and status not in _STATUS_CONHECIDOS:
            alertas.append("Status de validação desconhecido devolvido pelo modelo.")
        return LegendaIAResultado(
            legenda_sugerida=legenda,
            alertas=alertas,
            pendencias=_lista_textos(dados.get("pendencias")),
            modo=modo,
            nivel_certeza=_NIVEL_CERTEZA.get(nivel) if isinstance(nivel, str) else None,
            uso=_extrair_uso(corpo.get("usage")),
            modelo=modelo,
        )
