"""Prontidão de produção para o go-live no Render (T110, DEC-59).

Cobre: validação fail-closed de produção, STORAGE_LOCAL_DIR vindo do ambiente,
seeds no boot (SEED_ON_STARTUP), `seed_admin` sem senha padrão fora de dev e o
campo `storage` do `/health`. Nenhum teste aqui toca o banco.
"""
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

import app.core.bootstrap as bootstrap
import app.main as main_mod
from app.core.config import SENHA_ADMIN_PADRAO_DEV, Settings
from app.scripts import seed_admin

JWT_FORTE = "x" * 48


def _prod(**extra) -> Settings:
    base = {
        "environment": "production",
        "jwt_secret_key": JWT_FORTE,
        "backend_cors_origins": "https://garra.github.io",
    }
    return Settings(_env_file=None, **{**base, **extra})


def test_producao_valida_jwt_e_cors():
    with pytest.raises(ValidationError, match="JWT_SECRET_KEY"):
        _prod(jwt_secret_key="changeme")
    with pytest.raises(ValidationError, match="BACKEND_CORS_ORIGINS"):
        _prod(backend_cors_origins="*")
    assert _prod().cors_origins_list == ["https://garra.github.io"]


def test_storage_local_dir_vem_do_ambiente(monkeypatch, tmp_path):
    monkeypatch.setenv("STORAGE_PROVEDOR", "local")
    monkeypatch.setenv("STORAGE_LOCAL_DIR", str(tmp_path / "disco"))
    s = Settings(_env_file=None)
    assert s.storage_provedor == "local"
    assert s.storage_local_dir == str(tmp_path / "disco")


def test_padrao_do_storage_local_dir_preservado(monkeypatch):
    monkeypatch.delenv("STORAGE_LOCAL_DIR", raising=False)
    assert Settings(_env_file=None).storage_local_dir == "../05_infra/local/storage"


@pytest.mark.parametrize("senha", [None, "curta", SENHA_ADMIN_PADRAO_DEV])
def test_seed_no_boot_em_producao_exige_admin_senha_forte(senha):
    with pytest.raises(ValidationError, match="SEED_ON_STARTUP"):
        _prod(seed_on_startup=True, admin_senha=senha)


def test_seed_no_boot_em_producao_com_senha_forte_ok():
    s = _prod(seed_on_startup=True, admin_senha="uma-senha-bem-longa")
    assert s.admin_senha.get_secret_value() == "uma-senha-bem-longa"


def test_admin_senha_fraca_sem_seed_no_boot_nao_bloqueia_producao():
    """Não quebra quem já roda produção com ADMIN_SENHA curta e seed manual."""
    assert _prod(admin_senha="abc12345").seed_on_startup is False


def test_seed_admin_recusa_senha_padrao_fora_de_dev(monkeypatch, capsys):
    monkeypatch.delenv("ADMIN_SENHA", raising=False)
    monkeypatch.setattr(seed_admin, "get_settings", lambda: _prod())

    async def _nao_deve_rodar(*_a):  # pragma: no cover - falha se chamado
        raise AssertionError("criar_admin não deveria ser chamado")

    monkeypatch.setattr(seed_admin, "criar_admin", _nao_deve_rodar)
    assert seed_admin.main() == 1
    assert "ADMIN_SENHA" in capsys.readouterr().err


def test_seed_admin_usa_senha_padrao_em_dev(monkeypatch):
    monkeypatch.delenv("ADMIN_SENHA", raising=False)
    monkeypatch.setattr(seed_admin, "get_settings", lambda: Settings(_env_file=None))
    recebido = {}

    async def _fake(email, senha, nome):
        recebido.update(email=email, senha=senha)
        return "ok"

    monkeypatch.setattr(seed_admin, "criar_admin", _fake)
    assert seed_admin.main() == 0
    assert recebido["senha"] == SENHA_ADMIN_PADRAO_DEV


def test_lifespan_roda_migrations_e_seeds_quando_habilitado(monkeypatch, tmp_path):
    chamadas = []
    monkeypatch.setattr(main_mod, "aplicar_migrations", lambda: chamadas.append("migrations"))

    async def _seed(_settings):
        chamadas.append("seed")

    monkeypatch.setattr(main_mod, "semear_no_boot", _seed)
    monkeypatch.setattr(main_mod.settings, "run_migrations_on_startup", True)
    monkeypatch.setattr(main_mod.settings, "seed_on_startup", True)
    monkeypatch.setattr(main_mod.settings, "storage_provedor", "local")
    monkeypatch.setattr(main_mod.settings, "storage_local_dir", str(tmp_path / "st"))

    with TestClient(main_mod.app) as client:
        corpo = client.get("/health").json()

    assert chamadas == ["migrations", "seed"]
    assert corpo["storage"] == "ok"
    assert (tmp_path / "st").is_dir()


def test_lifespan_sem_flags_nao_roda_nada(monkeypatch):
    chamadas = []
    monkeypatch.setattr(main_mod, "aplicar_migrations", lambda: chamadas.append("migrations"))
    monkeypatch.setattr(main_mod.settings, "run_migrations_on_startup", False)
    monkeypatch.setattr(main_mod.settings, "seed_on_startup", False)
    with TestClient(main_mod.app):
        pass
    assert chamadas == []


def test_health_sem_auth_reporta_storage_indisponivel(monkeypatch, tmp_path):
    arquivo = tmp_path / "nao-e-diretorio"
    arquivo.write_text("x")
    monkeypatch.setattr(main_mod.settings, "storage_provedor", "local")
    monkeypatch.setattr(main_mod.settings, "storage_local_dir", str(arquivo))

    resposta = TestClient(main_mod.app).get("/health")

    assert resposta.status_code == 200
    assert resposta.json()["storage"] == "unavailable"
    assert resposta.json()["status"] == "degraded"


def test_verificar_storage_s3_nao_faz_rede():
    assert bootstrap.verificar_storage_local(Settings(_env_file=None, storage_provedor="s3")) == (
        "nao_verificado"
    )


async def test_semear_no_boot_sem_senha_so_roda_gabarito(monkeypatch):
    import app.scripts.seed_gabarito as seed_gabarito_mod

    chamadas = []

    async def _gabarito(_session):
        chamadas.append("gabarito")
        return {}

    async def _admin(*_a):  # pragma: no cover - falha se chamado
        chamadas.append("admin")

    monkeypatch.setattr(seed_gabarito_mod, "seed_gabarito", _gabarito)
    monkeypatch.setattr(seed_admin, "criar_admin", _admin)

    await bootstrap.semear_no_boot(Settings(_env_file=None))
    assert chamadas == ["gabarito"]

    await bootstrap.semear_no_boot(Settings(_env_file=None, admin_senha="uma-senha-bem-longa"))
    assert chamadas == ["gabarito", "gabarito", "admin"]
