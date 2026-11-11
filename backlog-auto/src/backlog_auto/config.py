"""Configuração por projeto: um `backlog.toml` na raiz, mesclado sobre os padrões abaixo."""
from __future__ import annotations

import copy
import os
import tomllib
from pathlib import Path

NOME_ARQUIVO = "backlog.toml"

PREAMBULO_PADRAO = (
    "Você roda em background num worktree isolado, sem ninguém para aprovar prompts. "
    "Faça só a tarefa abaixo, rode os testes do projeto, registre o resultado no doc indicado e, ao terminar, "
    "faça `git add` e `git commit` na branch do worktree (sem push). Não edite o arquivo do backlog nem o de "
    "progresso: o status é atualizado pelo integrador. Seja econômico: leia só os arquivos citados e os que precisar."
)

PADRAO = {
    "projeto": {
        "nome": "Projeto",
        "branch_principal": "main",
        "backlog": "BACKLOG.md",
        "progresso": "PROGRESSO.md",
        "prefixo_id": "T",
        "sessao_prefixo": "backlog-",
        "claude_exe": "",
        "autocommit": True,
    },
    "ambientes": ["offline", "humano"],
    "agente": {
        "permissao": "bypassPermissions",
        "preambulo": PREAMBULO_PADRAO,
        "regras_extras": [],
    },
    "rota": {
        "baixa": {"model": "haiku", "effort": "low", "budget": 1},
        "media": {"model": "sonnet", "effort": "medium", "budget": 3},
        "alta": {"model": "opus", "effort": "high", "budget": 8},
    },
    "guard": {
        "ativo": True,
        "variavel_liberacao": "BACKLOG_ESCRITA",
        "presets": ["sql", "delta"],
        "comando_gatilho": "",
        "isentos": ["/.claude/"],
        "padroes": {},
        "mensagem": "Bloqueado pela barreira de dados: este projeto não altera nem apaga dados existentes.",
    },
    "preparo": {
        "ativo": False,
        "prefixo_id": "D",
        "pasta_docs": "docs",
        "pasta_trabalho": "docs/_preparo",
        "idioma": "português do Brasil",
        "objetivo": "",
    },
    "fechamento": {
        "ativo": True,
        "model": "sonnet",
        "effort": "medium",
        "budget": 3,
        "timeout": 1800,
        "prompt": "",
        "proibidas_extensoes": ["py", "ipynb", "sql", "ts", "tsx", "js", "jsx", "j2", "sh", "ps1", "toml", "yml", "yaml"],
    },
    "planejamento": {
        "ativo": False,
        "model": "sonnet",
        "effort": "medium",
        "budget": 3,
        "timeout": 900,
        "fontes": [],
        "max_tarefas": 5,
        "prompt": "",
    },
    "lembrete": {
        "ativo": True,
        "extensoes": ["py", "ipynb", "sql"],
        "execucao": ["python", "pytest"],
        "texto": "Lembrete: antes de encerrar, registre o que mudou na documentação e no backlog.",
    },
}


class ConfigErro(Exception):
    pass


def _mesclar(base: dict, extra: dict) -> dict:
    for k, v in extra.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _mesclar(base[k], v)
        else:
            base[k] = v
    return base


class Config:
    def __init__(self, raiz: Path, dados: dict):
        self.raiz = Path(raiz)
        self.d = dados

    @property
    def backlog(self) -> Path:
        return self.raiz / self.d["projeto"]["backlog"]

    @property
    def progresso(self) -> Path:
        return self.raiz / self.d["projeto"]["progresso"]

    @property
    def principal(self) -> str:
        return self.d["projeto"]["branch_principal"]

    @property
    def prefixo_id(self) -> str:
        return self.d["projeto"]["prefixo_id"]

    @property
    def sessao_prefixo(self) -> str:
        return self.d["projeto"]["sessao_prefixo"]

    @property
    def worktrees(self) -> Path:
        return self.raiz / ".claude" / "worktrees"

    @property
    def logs(self) -> Path:
        return self.raiz / ".claude" / "logs"

    @property
    def pendente_fechamento(self) -> Path:
        return self.logs / "fechamento_pendente.json"

    @property
    def ambientes(self) -> list[str]:
        return list(self.d["ambientes"])

    @property
    def arquivos_controle(self) -> set[str]:
        p = self.d["projeto"]
        return {p["backlog"], p["progresso"]}

    def rota(self, dificuldade: str) -> dict:
        r = self.d["rota"]
        return r.get(dificuldade) or r.get("media") or next(iter(r.values()))


def achar_raiz(inicio: Path | None = None) -> Path | None:
    candidatos = []
    if os.environ.get("CLAUDE_PROJECT_DIR"):
        candidatos.append(Path(os.environ["CLAUDE_PROJECT_DIR"]))
    candidatos.append(Path(inicio or Path.cwd()))
    for c in candidatos:
        for p in [c.resolve(), *c.resolve().parents]:
            if (p / NOME_ARQUIVO).is_file():
                return p
    return None


def carregar(inicio: Path | None = None) -> Config:
    raiz = achar_raiz(inicio)
    if raiz is None:
        raise ConfigErro(f"{NOME_ARQUIVO} não encontrado. Rode `backlog-auto init` na raiz do projeto.")
    try:
        extra = tomllib.loads((raiz / NOME_ARQUIVO).read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as e:
        raise ConfigErro(f"{NOME_ARQUIVO} inválido: {e}") from e
    return Config(raiz, _mesclar(copy.deepcopy(PADRAO), extra))
