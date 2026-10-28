"""`init` (instala o sistema num projeto) e `doctor` (diagnostica a instalação)."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from importlib import resources
from pathlib import Path

from . import preparo
from .backlog import ler, validar
from .config import NOME_ARQUIVO, ConfigErro, carregar
from .runner import achar_claude, git

HOOK_GUARD = "python -m backlog_auto.hooks guard"
HOOK_LEMBRETE = "python -m backlog_auto.hooks lembrete"
MATCHER = "Edit|Write|NotebookEdit|Bash|PowerShell"
GITIGNORE = [".claude/worktrees/"]


def _template(nome: str) -> str:
    return (resources.files("backlog_auto") / "templates" / nome).read_text(encoding="utf-8")


def _escrever(destino: Path, texto: str, force: bool, acoes: list[str]) -> None:
    if destino.exists() and not force:
        acoes.append(f"mantido (já existe): {destino.name}")
        return
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(texto, encoding="utf-8")
    acoes.append(f"criado: {destino.name}")


def _registrar_hook(settings: dict, evento: str, comando: str) -> bool:
    lista = settings.setdefault("hooks", {}).setdefault(evento, [])
    for entrada in lista:
        if any(comando in h.get("command", "") for h in entrada.get("hooks", [])):
            return False
    lista.append({"matcher": MATCHER, "hooks": [{"type": "command", "command": comando}]})
    return True


def init(destino: Path, nome: str | None, force: bool, guard: bool, lembrete: bool) -> list[str]:
    destino = destino.resolve()
    acoes: list[str] = []
    nome = nome or destino.name
    cfg_txt = (_template("backlog.toml").replace("{{nome}}", nome)
               .replace("{{guard_ativo}}", str(guard).lower()).replace("{{lembrete_ativo}}", str(lembrete).lower()))
    _escrever(destino / NOME_ARQUIVO, cfg_txt, force, acoes)
    _escrever(destino / "BACKLOG.md", _template("BACKLOG.md").replace("{{nome}}", nome), force, acoes)
    _escrever(destino / "docs" / "BACKLOG-MANUAL.md", _template("MANUAL.md"), force, acoes)
    _escrever(destino / "docs" / "CELULAR.md",
              _template("CELULAR.md").replace("{{nome}}", nome).replace("{{principal}}", "main"), force, acoes)

    settings_path = destino / ".claude" / "settings.json"
    settings = json.loads(settings_path.read_text(encoding="utf-8")) if settings_path.exists() else {}
    mudou = False
    if guard:
        mudou |= _registrar_hook(settings, "PreToolUse", HOOK_GUARD)
    if lembrete:
        mudou |= _registrar_hook(settings, "PostToolUse", HOOK_LEMBRETE)
    if mudou:
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        acoes.append("atualizado: .claude/settings.json (hooks)")

    gi = destino / ".gitignore"
    atual = gi.read_text(encoding="utf-8") if gi.exists() else ""
    falta = [l for l in GITIGNORE if l not in atual.splitlines()]
    if falta:
        gi.write_text(atual + ("" if atual.endswith("\n") or not atual else "\n") + "\n".join(falta) + "\n", encoding="utf-8")
        acoes.append("atualizado: .gitignore")
    return acoes


def doctor(inicio: Path | None = None) -> int:
    problemas = 0

    def linha(ok: bool | None, texto: str):
        nonlocal problemas
        marca = {True: "OK  ", False: "FALHA", None: "AVISO"}[ok]
        problemas += ok is False
        print(f"[{marca}] {texto}")

    linha(sys.version_info >= (3, 11), f"Python {sys.version.split()[0]} (precisa de 3.11+)")
    try:
        cfg = carregar(inicio)
    except ConfigErro as e:
        linha(False, str(e))
        return 1
    linha(True, f"{NOME_ARQUIVO} em {cfg.raiz}")
    exe = achar_claude(cfg)
    linha(bool(exe), f"CLI claude: {exe or 'não encontrado (PATH, extensão do VS Code, CLAUDE_EXE ou projeto.claude_exe)'}")
    repo = git(cfg, "rev-parse", "--is-inside-work-tree").stdout.strip() == "true"
    linha(repo, "repositório git")
    if repo:
        atual = git(cfg, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
        linha(atual == cfg.principal, f"branch atual '{atual}' (principal configurada: '{cfg.principal}')")
        rastreado = git(cfg, "ls-files", "--error-unmatch", cfg.d["projeto"]["backlog"]).returncode == 0
        linha(rastreado or None, f"{cfg.backlog.name} versionado (o integrador precisa dele no git)")
        sujo = git(cfg, "status", "--porcelain", "--untracked-files=no").stdout.strip()
        linha(None if sujo else True, "branch principal limpa" if not sujo else "há mudanças não commitadas (o `colher` recusa até commitar)")
    if cfg.backlog.exists():
        _, tarefas = ler(cfg)
        erros = validar(cfg, tarefas)
        linha(not erros, f"{len(tarefas)} tarefas no backlog" + ("" if not erros else f", {len(erros)} erro(s)"))
        for e in erros:
            print(f"        - {e}")
        if cfg.d["preparo"]["ativo"]:
            feitas, total = preparo.estado(tarefas)
            linha(None if feitas < total else True,
                  f"preparo da documentação: {feitas}/{total}" if total else "preparo da documentação ainda não inserido (entra no primeiro `run`/`auto`)")
    else:
        linha(False, f"{cfg.backlog.name} não existe")
    settings = cfg.raiz / ".claude" / "settings.json"
    texto = settings.read_text(encoding="utf-8") if settings.exists() else ""
    if cfg.d["guard"]["ativo"]:
        linha(HOOK_GUARD in texto, "hook do guard registrado em .claude/settings.json")
    if cfg.d["lembrete"]["ativo"]:
        linha(HOOK_LEMBRETE in texto or None, "hook de lembrete registrado em .claude/settings.json")
    if shutil.which("python") is None:
        linha(None, "`python` fora do PATH: os hooks usam `python -m backlog_auto.hooks`")
    else:
        r = subprocess.run(["python", "-c", "import backlog_auto"], capture_output=True)
        linha(r.returncode == 0, "`python` do PATH importa backlog_auto (necessário para os hooks)")
    print("\nAvisos manuais (não dá para checar daqui): aceitar a confiança da pasta e o aviso do modo sem aprovação, "
          "rodando `claude --dangerously-skip-permissions` uma vez na raiz do projeto.")
    return 1 if problemas else 0
