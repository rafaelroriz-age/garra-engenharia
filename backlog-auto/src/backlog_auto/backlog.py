"""Parser e consultas do arquivo de backlog (Markdown)."""
from __future__ import annotations

import re

from .config import Config

STATUS = ("todo", "doing", "done", "blocked")
CAMPO = re.compile(r"^- \*\*(\w+):\*\* ?(.*)$")
PADRAO_TAREFA = {"status": "todo", "papel": "", "depende": "—", "ambiente": "", "dificuldade": "media",
                 "toca": "", "doc": "", "pronto": "", "prompt": "", "fase": ""}


def ler(cfg: Config):
    titulo = re.compile(r"^### ([A-Za-z]+\d+)\s*[·:—-]\s*(.+)$")
    linhas = cfg.backlog.read_text(encoding="utf-8").splitlines()
    tarefas, atual, em_prompt, bloco = {}, None, False, ""
    for i, linha in enumerate(linhas):
        if linha.startswith("## Bloco"):
            bloco = linha[3:].strip()
        m = titulo.match(linha)
        if m:
            atual = {**PADRAO_TAREFA, "ambiente": cfg.ambientes[0], "id": m.group(1), "titulo": m.group(2).strip(),
                     "linha_status": None, "bloco": bloco}
            tarefas[atual["id"]] = atual
            em_prompt = False
            continue
        if atual is None:
            continue
        if em_prompt:
            if linha.startswith("```"):
                if atual["prompt"]:
                    em_prompt = False
                continue
            atual["prompt"] += linha + "\n"
            continue
        c = CAMPO.match(linha)
        if c:
            chave, valor = c.group(1).lower(), c.group(2).strip()
            atual[chave] = valor
            if chave == "status":
                atual["linha_status"] = i
            if chave == "prompt":
                em_prompt, atual["prompt"] = True, ""
    return linhas, tarefas


PROMPT_FECHAMENTO_PADRAO = (
    "Rode `git status` e `git log` para ver o que o último lote mudou. Para cada tarefa concluída, atualize a documentação "
    "do projeto com os fatos novos, seguindo as regras de documentação do projeto, e confira se o backlog reflete os status "
    "reais (`backlog-auto list`). Não altere código."
)


def fechamento_do_backlog(cfg: Config) -> str:
    """Primeiro bloco ```text sob '## Fechamento de lote' do backlog; sem ele, o texto padrão."""
    dentro = fence = False
    achado: list[str] = []
    for linha in cfg.backlog.read_text(encoding="utf-8").splitlines():
        if linha.startswith("## "):
            if dentro:
                break
            dentro = linha[3:].strip().lower().startswith("fechamento de lote")
        elif dentro and linha.startswith("```"):
            if fence:
                break
            fence = True
        elif dentro and fence:
            achado.append(linha)
    return "\n".join(achado).strip() or PROMPT_FECHAMENTO_PADRAO


def lista(valor: str) -> list[str]:
    return [v.strip() for v in valor.split(",") if v.strip() and v.strip() != "—"]


def prontas(tarefas: dict, ambiente: str | None = None) -> list[dict]:
    """Tarefas liberadas. Enquanto houver tarefa de preparo não concluída, só as de preparo são liberadas."""
    preparo_aberto = any(t["fase"] == "preparo" and t["status"] != "done" for t in tarefas.values())
    return [
        t for t in tarefas.values()
        if t["status"] == "todo"
        and (not preparo_aberto or t["fase"] == "preparo")
        and all(d in tarefas and tarefas[d]["status"] == "done" for d in lista(t["depende"]))
        and (ambiente is None or t["ambiente"] == ambiente)
    ]


def conflita(a: dict, b: dict) -> bool:
    for x in lista(a["toca"]):
        for y in lista(b["toca"]):
            x, y = x.split(" ")[0].rstrip("/"), y.split(" ")[0].rstrip("/")
            if x == y or x.startswith(y + "/") or y.startswith(x + "/"):
                return True
    return False


def lote(candidatas: list[dict]) -> list[dict]:
    escolhidas: list[dict] = []
    for t in candidatas:
        if not any(conflita(t, e) for e in escolhidas):
            escolhidas.append(t)
    return escolhidas


def gravar_status(cfg: Config, linhas: list[str], tarefas: dict, tid: str, status: str) -> None:
    t = tarefas.get(tid)
    if not t:
        raise KeyError(f"Tarefa {tid} não existe.")
    if status not in STATUS:
        raise ValueError(f"Status deve ser um de {STATUS}.")
    if t["linha_status"] is None:
        raise ValueError(f"{tid} não tem a linha '- **Status:**'.")
    linhas[t["linha_status"]] = f"- **Status:** {status}"
    t["status"] = status
    cfg.backlog.write_text("\n".join(linhas) + "\n", encoding="utf-8")


def validar(cfg: Config, tarefas: dict) -> list[str]:
    erros = []
    if not tarefas:
        return [f"nenhuma tarefa encontrada em {cfg.backlog.name} (título esperado: '### {cfg.prefixo_id}01 · Título')"]
    for t in tarefas.values():
        i = t["id"]
        if t["linha_status"] is None:
            erros.append(f"{i}: falta '- **Status:**'")
        elif t["status"] not in STATUS:
            erros.append(f"{i}: status inválido '{t['status']}'")
        if t["ambiente"] not in cfg.ambientes:
            erros.append(f"{i}: ambiente '{t['ambiente']}' fora de {cfg.ambientes}")
        if t["dificuldade"] not in cfg.d["rota"]:
            erros.append(f"{i}: dificuldade '{t['dificuldade']}' fora de {list(cfg.d['rota'])}")
        if not t["prompt"].strip():
            erros.append(f"{i}: sem Prompt")
        if not t["toca"].strip():
            erros.append(f"{i}: sem Toca (a tarefa nunca conflitaria com outra no mesmo lote)")
        for d in lista(t["depende"]):
            if d not in tarefas:
                erros.append(f"{i}: depende de {d}, que não existe")
        if t["status"] != "done":
            for doc in lista(t["doc"]):
                caminho = doc.split(" ")[0].rstrip("/")
                if "." in caminho.rsplit("/", 1)[-1] and not conflita({"toca": caminho}, t):
                    erros.append(f"{i}: o doc '{caminho}' é editado pela tarefa mas não está em Toca "
                                 "(tarefas paralelas podem conflitar nele)")
    visitando, ok = set(), set()

    def ciclo(i, caminho):
        if i in ok:
            return
        if i in visitando:
            erros.append("ciclo de dependências: " + " → ".join([*caminho, i]))
            return
        visitando.add(i)
        for d in lista(tarefas[i]["depende"]):
            if d in tarefas:
                ciclo(d, [*caminho, i])
        visitando.discard(i)
        ok.add(i)

    for i in tarefas:
        ciclo(i, [])
    return erros
