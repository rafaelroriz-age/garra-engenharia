"""Criação de tarefas no BACKLOG.md: a partir de um JSON (`nova`) ou de um planejamento automático (`planejar`).

Duas portas de entrada, um só caminho de gravação:
- `inserir`: recebe itens (dicts), atribui ids novos (T02, T03...), monta os blocos no formato do backlog, grava e
  confere o arquivo inteiro com `validar`. Se algo não bater, restaura o texto original e não grava nada.
- `planejar`: uma sessão `claude -p` (só leitura) lê o backlog de produto e o BACKLOG.md, devolve um JSON com as
  próximas tarefas e o `inserir` as grava. Roda na branch principal, como o `colher`, e só commita o backlog.

Formato do item (JSON), campos obrigatórios: `bloco` (começa com "Bloco"), `titulo`, `papel`, `ambiente`, `dificuldade`,
`toca`, `pronto`, `prompt`. Opcionais: `origem` (ex.: "BL-10"; itens com origem já existente são ignorados),
`doc`, `depende` (lista de ids existentes ou de `chave` de outro item do mesmo lote) e `chave` (apelido local).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from .backlog import gravar_status, ler, validar
from .config import Config, ConfigErro

OBRIGATORIOS = ("bloco", "titulo", "papel", "ambiente", "dificuldade", "toca", "pronto", "prompt")


class PlanejarErro(Exception):
    pass


def _ids_existentes(tarefas: dict, prefixo: str) -> list[int]:
    return [int(m.group(1)) for t in tarefas if (m := re.fullmatch(rf"{re.escape(prefixo)}(\d+)", t))]


def proximo_id(tarefas: dict, prefixo: str, reservados: int = 0) -> str:
    numeros = _ids_existentes(tarefas, prefixo)
    prox = (max(numeros) if numeros else 0) + 1 + reservados
    return f"{prefixo}{prox:02d}"


def _lista(valor) -> list[str]:
    if valor is None or valor == "" or valor == "—":
        return []
    if isinstance(valor, str):
        return [v.strip() for v in valor.split(",") if v.strip() and v.strip() != "—"]
    return [str(v).strip() for v in valor if str(v).strip()]


def checar_itens(cfg: Config, itens: list[dict], tarefas: dict) -> list[str]:
    """Erros de formato que dá para apontar antes de montar o backlog."""
    erros: list[str] = []
    chaves = [str(i.get("chave") or "") for i in itens]
    for n, it in enumerate(itens, 1):
        rot = f"item {n} ({it.get('titulo', '?')})"
        for campo in OBRIGATORIOS:
            if not str(it.get(campo) or "").strip():
                erros.append(f"{rot}: falta '{campo}'")
        if str(it.get("bloco", "")).strip() and not str(it["bloco"]).strip().startswith("Bloco"):
            erros.append(f"{rot}: 'bloco' deve começar com 'Bloco' (ex.: 'Bloco B — Fundação do RFO')")
        if it.get("ambiente") and it["ambiente"] not in cfg.ambientes:
            erros.append(f"{rot}: ambiente '{it['ambiente']}' fora de {cfg.ambientes}")
        if it.get("dificuldade") and it["dificuldade"] not in cfg.d["rota"]:
            erros.append(f"{rot}: dificuldade '{it['dificuldade']}' fora de {list(cfg.d['rota'])}")
        for d in _lista(it.get("depende")):
            if d not in tarefas and d not in chaves:
                erros.append(f"{rot}: depende de '{d}', que não é tarefa existente nem chave do lote")
    dup = {c for c in chaves if c and chaves.count(c) > 1}
    if dup:
        erros.append(f"chaves repetidas no lote: {sorted(dup)}")
    return erros


def _bloco_linhas(tid: str, it: dict, depende: list[str]) -> list[str]:
    L = [f"### {tid} · {it['titulo'].strip()}", "- **Status:** todo"]
    if it.get("origem"):
        L.append(f"- **Origem:** {it['origem']}")
    L += [f"- **Papel:** {it['papel']}",
          f"- **Depende:** {', '.join(depende) if depende else '—'}",
          f"- **Ambiente:** {it['ambiente']}",
          f"- **Dificuldade:** {it['dificuldade']}",
          f"- **Toca:** {it['toca']}"]
    if it.get("doc"):
        L.append(f"- **Doc:** {it['doc']}")
    L += [f"- **Pronto:** {it['pronto']}", "- **Prompt:**", "```text", it["prompt"].strip(), "```", ""]
    return L


def _inserir_no_bloco(linhas: list[str], bloco: str, novas: list[str]) -> list[str]:
    """Põe `novas` no fim do bloco homônimo; se não existir, cria o bloco no fim do arquivo."""
    cabeca = f"## {bloco.strip()}"
    i = next((n for n, l in enumerate(linhas) if l.strip() == cabeca), None)
    if i is None:
        base = list(linhas)
        while base and not base[-1].strip():
            base.pop()
        return base + ["", "---", "", cabeca, "", *novas]
    fim = next((n for n in range(i + 1, len(linhas)) if linhas[n].startswith("## ") or linhas[n].strip() == "---"),
               len(linhas))
    corte = fim
    while corte > i + 1 and not linhas[corte - 1].strip():
        corte -= 1
    return linhas[:corte] + [""] + novas + linhas[corte:]


def inserir(cfg: Config, itens: list[dict]) -> list[str]:
    """Grava os itens no backlog e devolve os ids criados. Tudo ou nada: se o backlog resultante não validar, nada muda."""
    original = cfg.backlog.read_text(encoding="utf-8")
    linhas, tarefas = ler(cfg)
    origens_existentes = {t["origem"] for t in tarefas.values() if t.get("origem")}
    a_criar = [i for i in itens if not (i.get("origem") and i["origem"] in origens_existentes)]
    if not a_criar:
        return []
    erros = checar_itens(cfg, a_criar, tarefas)
    if erros:
        raise ConfigErro("; ".join(erros))

    prefixo = cfg.prefixo_id
    ids = [proximo_id(tarefas, prefixo, reservados=n) for n in range(len(a_criar))]
    mapa = {str(it["chave"]): tid for it, tid in zip(a_criar, ids) if it.get("chave")}
    por_bloco: dict[str, list[str]] = {}
    for it, tid in zip(a_criar, ids):
        depende = [mapa.get(d, d) for d in _lista(it.get("depende"))]
        por_bloco.setdefault(it["bloco"].strip(), []).extend(_bloco_linhas(tid, it, depende))
    novo = list(linhas)
    for bloco, bl in por_bloco.items():
        novo = _inserir_no_bloco(novo, bloco, bl[:-1])  # o último "" de cada bloco é só separador
    texto = "\n".join(novo).rstrip("\n") + "\n"
    cfg.backlog.write_text(texto, encoding="utf-8")
    _, tarefas_novas = ler(cfg)
    problemas = validar(cfg, tarefas_novas)
    if problemas:
        cfg.backlog.write_text(original, encoding="utf-8")
        raise ConfigErro("o backlog resultante não valida (nada foi gravado): " + "; ".join(problemas))
    return ids


def ler_itens(texto: str) -> list[dict]:
    """Aceita um objeto ou uma lista de objetos em JSON."""
    try:
        dados = json.loads(texto)
    except ValueError as e:
        raise ConfigErro(f"JSON inválido: {e}") from e
    if isinstance(dados, dict):
        dados = [dados]
    if not isinstance(dados, list) or not all(isinstance(i, dict) for i in dados):
        raise ConfigErro("o JSON precisa ser um objeto ou uma lista de objetos de tarefa.")
    return dados


def _extrair_json(saida: str) -> list[dict]:
    m = re.search(r"```(?:json)?\s*(\[.*\])\s*```", saida, re.S)
    trecho = m.group(1) if m else saida[saida.find("["): saida.rfind("]") + 1]
    if not trecho.strip():
        raise PlanejarErro("a sessão não devolveu a lista de tarefas em JSON.")
    try:
        return ler_itens(trecho)
    except ConfigErro as e:
        raise PlanejarErro(str(e)) from e


def prompt_planejamento(cfg: Config, tarefas: dict, max_tarefas: int) -> str:
    p = cfg.d["planejamento"]
    a = cfg.d["agente"]
    fontes = ", ".join(p["fontes"]) or "(nenhuma fonte configurada: use o BACKLOG.md e a documentação em 00_docs/)"
    existentes = sorted({t["origem"] for t in tarefas.values() if t.get("origem")})
    ids = ", ".join(sorted(tarefas)) or "nenhum"
    blocos = ", ".join(sorted({t["bloco"] for t in tarefas.values() if t.get("bloco")})) or "nenhum"
    regras = " ".join(r.strip() for r in a["regras_extras"])
    base = p["prompt"].strip() or (
        "Você é o planejador do backlog. Leia as fontes de produto indicadas e o arquivo do backlog "
        f"({cfg.d['projeto']['backlog']}). Escolha até {max_tarefas} itens que ainda não foram feitos (não marcados como "
        "concluídos na fonte), que estejam desbloqueados ou cujas dependências já estejam no backlog, e que não estejam "
        "já listados no backlog. Ordene do mais simples e desbloqueado para o mais complexo. Para cada item, escreva uma "
        "tarefa executável por uma sessão sem contexto da conversa: prompt autocontido, com caminhos, critério de pronto "
        "verificável e a instrução de seguir a \"Regra de pronto\" do BACKLOG.md. Tarefas que podem rodar no mesmo lote "
        "precisam ter `toca` disjunto; se duas mexem nos mesmos arquivos, encadeie-as com `depende`. Itens que exigem "
        "decisão de negócio, cliente, credencial ou ato jurídico ficam fora (ou com ambiente 'humano')."
    )
    formato = (
        "Responda SOMENTE com uma lista JSON dentro de um bloco ```json. Cada item tem as chaves: "
        '"chave" (apelido local, ex.: "A"), "bloco" (um dos blocos existentes ou um novo começando com "Bloco"), '
        '"titulo", "origem" (id da fonte, ex.: "BL-10"), "papel", "depende" (lista de ids existentes ou de chaves '
        'do lote, ou []), "ambiente" (um de '
        f'{cfg.ambientes}), "dificuldade" (um de {list(cfg.d["rota"])}), "toca" (arquivos/pastas escritos), '
        '"doc" (arquivo onde registrar o resultado, dentro de "toca"), "pronto" (critério verificável) e "prompt" '
        "(instrução completa). `depende` só pode citar ids já existentes ou chaves de itens que você mesmo devolve nesta "
        "lista (nunca blocos como 'B' nem itens fora da lista); liste cada item antes dos que dependem dele. Não edite nenhum arquivo: esta sessão só lê e responde."
    )
    contexto = (
        f"Fontes de produto: {fontes}.\n"
        f"Ids já usados no backlog: {ids}. Origens já cobertas (não repita): {', '.join(existentes) or 'nenhuma'}.\n"
        f"Blocos existentes: {blocos}.\n"
        f"Regras do projeto para todo prompt: {regras}"
    )
    return f"{base}\n\n{contexto}\n\n{formato}"


def _limitar(itens: list[dict], n: int) -> list[dict]:
    """Corta o lote em `n` itens, puxando para dentro os itens de que os mantidos dependem (por chave), se couber."""
    por_chave = {str(i["chave"]): i for i in itens if i.get("chave")}
    escolhidos: list[dict] = []

    def add(it: dict) -> None:
        if any(it is e for e in escolhidos) or len(escolhidos) >= n:
            return
        for d in _lista(it.get("depende")):
            if d in por_chave:
                add(por_chave[d])
        if len(escolhidos) < n and not any(it is e for e in escolhidos):
            escolhidos.append(it)

    for it in itens:
        add(it)
    return escolhidos


def _sanear_dependencias(itens: list[dict], tarefas: dict) -> None:
    """Descarta (com aviso) dependências que não são id existente nem chave do lote, em vez de abortar o planejamento."""
    chaves = {str(i["chave"]) for i in itens if i.get("chave")}
    for n, it in enumerate(itens, 1):
        deps = _lista(it.get("depende"))
        boas = [d for d in deps if d in tarefas or d in chaves]
        for d in deps:
            if d not in boas:
                print(f"aviso: item {n} ({it.get('titulo', '?')}): dependência '{d}' descartada "
                      "(não é tarefa existente nem chave do lote)", file=sys.stderr)
        it["depende"] = boas


def planejar(cfg: Config, dry: bool = False) -> int:
    """Gera e grava as próximas tarefas. Devolve quantas foram criadas (0 se nada novo)."""
    from . import runner  # import tardio: runner também importa este módulo

    p = cfg.d["planejamento"]
    _, tarefas = ler(cfg)
    prompt = prompt_planejamento(cfg, tarefas, p["max_tarefas"])
    if dry:
        print(f"(simulação) planejamento com {p['model']}/{p['effort']}/US${p['budget']}:\n\n{prompt}")
        return 0
    exe = runner.achar_claude(cfg)
    if not exe:
        raise PlanejarErro("CLI `claude` não encontrado; planejamento não executado.")
    try:
        runner.conferir_principal(cfg)
    except runner.ColherErro as e:
        raise PlanejarErro(str(e)) from e
    cmd = [exe, "-p", "--model", p["model"], "--effort", p["effort"], "--max-budget-usd", str(p["budget"]),
           "--allowedTools", "Read,Grep,Glob", "--", prompt]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", cwd=cfg.raiz, timeout=p["timeout"])
    except subprocess.TimeoutExpired as e:
        raise PlanejarErro(f"planejamento excedeu {p['timeout']}s") from e
    if r.returncode:
        raise PlanejarErro(f"planejamento falhou (código {r.returncode}): {(r.stdout + r.stderr).strip()[:300]}")
    itens = _limitar(_extrair_json(r.stdout), p["max_tarefas"])
    _sanear_dependencias(itens, tarefas)
    ids = inserir(cfg, itens)
    if ids:
        runner.commitar_controle(cfg, "backlog: planejamento cria " + ", ".join(ids))
    return len(ids)


def planejar_se_preciso(cfg: Config) -> int | None:
    """Para o `auto`: planeja quando não resta nenhuma tarefa no backlog (todo, doing ou blocked).

    Retorna None se o planejamento está desligado ou não era hora; senão, quantas tarefas criou.
    """
    if not cfg.d["planejamento"]["ativo"]:
        return None
    _, tarefas = ler(cfg)
    if any(t["status"] in ("todo", "doing", "blocked") for t in tarefas.values()):
        return None
    return planejar(cfg)
