"""CORS no Render: o front publicado entra mesmo com BACKEND_CORS_ORIGINS errado no painel."""
from app.core.config import ORIGEM_FRONT_PRODUCAO, Settings


def _origens(valor: str) -> list[str]:
    return Settings(_env_file=None, backend_cors_origins=valor).cors_origins_list


def test_render_sempre_libera_o_front_publicado(monkeypatch):
    monkeypatch.setenv("RENDER", "true")
    assert _origens("https://outro.exemplo/") == ["https://outro.exemplo", ORIGEM_FRONT_PRODUCAO]
    assert _origens(f"{ORIGEM_FRONT_PRODUCAO}/") == [ORIGEM_FRONT_PRODUCAO]


def test_fora_do_render_vale_so_o_ambiente(monkeypatch):
    monkeypatch.delenv("RENDER", raising=False)
    assert _origens("http://localhost:3000") == ["http://localhost:3000"]
