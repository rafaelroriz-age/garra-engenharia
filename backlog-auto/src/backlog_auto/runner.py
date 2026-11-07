"""Dispara tarefas como sessões `claude --bg`, integra as concluídas na branch principal e gera o painel."""
from __future__ import annotations

import glob
import json
import os
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path

from . import novas, preparo
from .backlog import fechamento_do_backlog, gravar_status, ler, lote, prontas
from .config import Config, ConfigErro

ICONE = {"todo": "⬜", "doing": "🔄", "done": "✅", "blocked": "⛔"}


class ColherErro(Exception):
    pass


def _identidade(cfg: Config) -> list[str]:
    ok = all(subprocess.run(["git", "config", "--get", k], capture_output=True, text=True, cwd=cfg.raiz).stdout.strip()
             for k in ("user.name", "user.email"))
    return [] if ok else ["-c", "user.name=backlog-auto", "-c", "user.email=backlog-auto@localhost"]


def git(cfg: Config, *a, cwd: Path | None = None):
    """Commits automáticos não dependem de chave de assinatura, agente GPG/SSH nem credenciais (nunca há push)."""
    sem_chave = ["-c", "commit.gpgsign=false", "-c", "tag.gpgsign=false", *_identidade(cfg)]
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    return subprocess.run(["git", *sem_chave, *a], capture_output=True, text=True, encoding="utf-8",
                          cwd=cwd or cfg.raiz, env=env)


def salvar_pendentes(cfg: Config) -> bool:
    """Commita as mudanças em arquivos já rastreados da principal (não toca em arquivos novos)."""
    if not git(cfg, "status", "--porcelain", "--untracked-files=no").stdout.strip():
        return False
    git(cfg, "add", "-u")
    git(cfg, "commit", "-m", "backlog: salva mudanças pendentes antes de integrar")
    return True


def achar_claude(cfg: Config) -> str | None:
    for c in (os.environ.get("CLAUDE_EXE"), cfg.d["projeto"]["claude_exe"], shutil.which("claude")):
        if c:
            return c
    achados = sorted(glob.glob(str(Path.home() / ".vscode/extensions/anthropic.claude-code-*/resources/native-binary/claude*")))
    return achados[-1] if achados else None


def sessoes_ativas(exe: str) -> list[dict]:
    try:
        r = subprocess.run([exe, "agents", "--json"], capture_output=True, text=True, timeout=30, encoding="utf-8")
        return json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else []
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return []


def commitar_controle(cfg: Config, msg: str) -> None:
    arq = cfg.d["projeto"]["backlog"]
    if git(cfg, "ls-files", "--error-unmatch", arq).returncode == 0 and git(cfg, "diff", "--quiet", "--", arq).returncode:
        git(cfg, "commit", "-m", msg, "--", arq)


def montar_prompt(cfg: Config, t: dict) -> str:
    a = cfg.d["agente"]
    partes = [a["preambulo"].strip(), *[r.strip() for r in a["regras_extras"]]]
    return " ".join(partes) + "\n\n" + t["prompt"].strip()


def comando_sessao(cfg: Config, exe: str, t: dict, modelo: str | None) -> list[str]:
    r = cfg.rota(t["dificuldade"])
    nome = cfg.sessao_prefixo + t["id"]
    return [exe, "--bg", "-w", nome, "-n", nome, "--model", modelo or r["model"], "--effort", r["effort"],
            "--max-budget-usd", str(r["budget"]), "--permission-mode", cfg.d["agente"]["permissao"],
            "--", montar_prompt(cfg, t)]


def disparar(cfg: Config, ambiente: str | None = None, modelo: str | None = None, dry: bool = False) -> int:
    exe = achar_claude(cfg)
    if not exe and not dry:
        raise SystemExit("CLI `claude` não encontrado (PATH, extensão do VS Code, CLAUDE_EXE ou projeto.claude_exe).")
    if cfg.d["preparo"]["ativo"] and preparo.garantir(cfg):
        print("Fase de preparo da documentação adicionada ao backlog (D01..D05); ela roda antes das demais tarefas.")
        commitar_controle(cfg, "backlog: adiciona fase de preparo da documentação")
    linhas, tarefas = ler(cfg)
    paralelo = lote(prontas(tarefas, ambiente))
    if not paralelo:
        print("Nenhuma tarefa liberada.")
        return 0
    print(f"{'(simulação) ' if dry else ''}Lote de {len(paralelo)} tarefas:")
    ok = []
    for t in paralelo:
        r = cfg.rota(t["dificuldade"])
        rotulo = f"{t['id']}  [{t['dificuldade']} → {modelo or r['model']}/{r['effort']}/US${r['budget']}]"
        if dry:
            print(f"  {rotulo} {t['titulo']}")
            continue
        p = subprocess.run(comando_sessao(cfg, exe, t, modelo), capture_output=True, text=True, encoding="utf-8", cwd=cfg.raiz)
        saida = (p.stdout + p.stderr).strip()
        if p.returncode == 0:
            gravar_status(cfg, linhas, tarefas, t["id"], "doing")
            ok.append({"tarefa": t["id"], "modelo": modelo or r["model"], "effort": r["effort"], "retorno": saida})
            print(f"  {rotulo} disparada")
        else:
            print(f"  {rotulo} FALHOU (código {p.returncode}): {saida[:300]}")
    if ok:
        commitar_controle(cfg, "backlog: disparo de " + ", ".join(d["tarefa"] for d in ok))
        cfg.logs.mkdir(parents=True, exist_ok=True)
        (cfg.logs / f"lote_{datetime.now():%Y%m%d_%H%M%S}.json").write_text(
            json.dumps(ok, indent=2, ensure_ascii=False), encoding="utf-8")
        print("\nQuando terminarem: `backlog-auto colher` (ou deixe `backlog-auto auto` rodando).")
    return len(ok)


def integrar(cfg: Config, tid: str, dry: bool, proibidas: set[str] | None = None) -> tuple[str, str]:
    """Retorna (estado, mensagem); estado: ok | vazio | ausente | conflito | recusado.

    `proibidas`: extensões que a branch não pode ter alterado (usado no fechamento de lote, que só mexe em documentação).
    """
    nome = cfg.sessao_prefixo + tid
    wt, branch = cfg.worktrees / nome, f"worktree-{nome}"
    if not wt.exists():
        return "ausente", "worktree não encontrado"
    if git(cfg, "status", "--porcelain", cwd=wt).stdout.strip():
        if dry:
            return "ok", "(simulação) commit automático das mudanças pendentes + merge"
        git(cfg, "add", "-A", cwd=wt)
        git(cfg, "commit", "-m", f"{tid}: commit automático do integrador", cwd=wt)
    if not git(cfg, "log", "--oneline", f"{cfg.principal}..{branch}").stdout.strip():
        return "vazio", "terminou sem nenhuma mudança (veja `claude logs`)"
    if proibidas:
        mexidos = git(cfg, "diff", "--name-only", f"{cfg.principal}...{branch}").stdout.split()
        codigo = [f for f in mexidos if f.rsplit(".", 1)[-1].lower() in proibidas]
        if codigo:
            return "recusado", f"alterou arquivos de código ({', '.join(codigo[:5])}); nada foi integrado"
    if dry:
        return "ok", "(simulação) merge"
    r = git(cfg, "merge", "--no-ff", "-m", f"Integra {tid} (backlog)", branch)
    if r.returncode:
        conflitos = set(git(cfg, "diff", "--name-only", "--diff-filter=U").stdout.split())
        if conflitos and conflitos <= cfg.arquivos_controle:
            git(cfg, "checkout", "--ours", "--", *conflitos)
            git(cfg, "add", "--", *conflitos)
            git(cfg, "commit", "--no-edit")
        else:
            git(cfg, "merge", "--abort")
            return "conflito", f"conflito em {', '.join(sorted(conflitos)) or (r.stdout + r.stderr).strip()[:200]}; resolva à mão"
    return "ok", "integrada"


def conferir_principal(cfg: Config) -> None:
    """A principal precisa estar na branch certa e sem mudanças soltas antes de qualquer merge."""
    atual = git(cfg, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    if atual != cfg.principal:
        raise ColherErro(f"a branch atual é '{atual}', não '{cfg.principal}'.")
    if cfg.d["projeto"]["autocommit"] and salvar_pendentes(cfg):
        print("  principal: mudanças pendentes commitadas automaticamente.")
    sujas = [l for l in git(cfg, "status", "--porcelain", "--untracked-files=no").stdout.splitlines()
             if l[3:].strip().strip('"') not in cfg.arquivos_controle]
    if sujas:
        raise ColherErro("a branch principal tem mudanças não commitadas"
                         + ("" if cfg.d["projeto"]["autocommit"] else " (autocommit desligado)")
                         + "; commite ou guarde (git stash).")


def colher(cfg: Config, dry: bool = False) -> dict:
    """Integra o que terminou. Retorna contagens: feitas, ocupadas, esperando, problemas."""
    res = {"feitas": 0, "ocupadas": 0, "esperando": 0, "problemas": 0}
    exe = achar_claude(cfg)
    sessoes = {s.get("name"): s for s in (sessoes_ativas(exe) if exe else [])}
    linhas, tarefas = ler(cfg)
    doing = [t for t in tarefas.values() if t["status"] == "doing"]
    if not doing:
        print("Nada em andamento.")
        return res
    if not dry:
        conferir_principal(cfg)
    for t in doing:
        s = sessoes.get(cfg.sessao_prefixo + t["id"])
        estado = s.get("status") if s else "encerrada"
        if estado == "busy":
            res["ocupadas"] += 1
            print(f"  {t['id']}  trabalhando")
            continue
        if estado == "waiting":
            res["esperando"] += 1
            print(f"  {t['id']}  esperando {s.get('waitingFor', '?')}: `claude attach {s.get('id')}`")
            continue
        est, msg = integrar(cfg, t["id"], dry)
        print(f"  {t['id']}  {msg}")
        if dry:
            continue
        if est == "conflito":
            res["problemas"] += 1
            continue
        gravar_status(cfg, linhas, tarefas, t["id"], "done" if est == "ok" else "blocked")
        commitar_controle(cfg, f"backlog: {t['id']} {'done' if est == 'ok' else 'blocked (' + est + ')'}")
        if est != "ok":
            res["problemas"] += 1
        else:
            res["feitas"] += 1
            if t["fase"] != "preparo":  # o preparo (D04/D05) já documenta; fechamento extra seria redundante
                registrar_pendente(cfg, t["id"])
        if s and exe:
            subprocess.run([exe, "stop", s["id"]], capture_output=True)
            subprocess.run([exe, "rm", s["id"]], capture_output=True)
        if est == "ok":
            wt = cfg.worktrees / (cfg.sessao_prefixo + t["id"])
            if wt.exists():
                git(cfg, "worktree", "remove", "-f", "-f", str(wt))
            git(cfg, "worktree", "prune")
            git(cfg, "branch", "-d", f"worktree-{cfg.sessao_prefixo}{t['id']}")
    return res


def _pendentes(cfg: Config) -> list[str]:
    try:
        return json.loads(cfg.pendente_fechamento.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []


def registrar_pendente(cfg: Config, tid: str) -> None:
    """Lembra, em disco, que `tid` entrou na principal e ainda não passou pelo fechamento de lote."""
    ids = _pendentes(cfg)
    if tid not in ids:
        cfg.logs.mkdir(parents=True, exist_ok=True)
        cfg.pendente_fechamento.write_text(json.dumps(ids + [tid]), encoding="utf-8")


def prompt_fechamento(cfg: Config, ids: list[str], tarefas: dict) -> str:
    """Texto do 'Fechamento de lote' do backlog (ou do toml), mais o contexto do lote e as regras desta sessão."""
    a, f = cfg.d["agente"], cfg.d["fechamento"]
    base = f["prompt"].strip() or fechamento_do_backlog(cfg)
    lote_txt = "; ".join(f"{i} ({tarefas[i]['titulo']}; Doc: {tarefas[i]['doc'] or '—'})" for i in ids if i in tarefas)
    ext = ", ".join(f"*.{e}" for e in f["proibidas_extensoes"])
    return " ".join([
        a["preambulo"].strip(), *[r.strip() for r in a["regras_extras"]],
        "ESTA É A SESSÃO DE FECHAMENTO DE LOTE: a regra que reserva os documentos de gestão ao fechamento vale para as outras "
        "sessões, não para você; é você quem os atualiza. Não edite o arquivo do backlog nem o de progresso (o integrador cuida). "
        f"Altere somente documentação; o integrador recusa o merge se houver mudança em {ext}.",
    ]) + f"\n\nTarefas integradas neste lote: {lote_txt or ', '.join(ids)}.\n\n" + base


def fechar(cfg: Config, dry: bool = False) -> str:
    """Roda a sessão de fechamento de lote e integra o resultado. Retorna: nada | adiado | ok | falha."""
    ids = _pendentes(cfg)
    linhas, tarefas = ler(cfg)
    if not ids:
        print("Nenhum lote a fechar.")
        return "nada"
    if any(t["status"] == "doing" for t in tarefas.values()):
        print("Fechamento adiado: ainda há tarefas em andamento.")
        return "adiado"
    nome = cfg.sessao_prefixo + "fechamento"
    wt, branch = cfg.worktrees / nome, f"worktree-{nome}"
    f = cfg.d["fechamento"]
    print(f"{'(simulação) ' if dry else ''}Fechamento de lote ({', '.join(ids)}) → {f['model']}/{f['effort']}/US${f['budget']}")
    if dry:
        return "ok"
    exe = achar_claude(cfg)
    if not exe:
        print("  CLI `claude` não encontrado; fechamento não executado.")
        return "falha"
    try:
        conferir_principal(cfg)
    except ColherErro as e:
        print(f"  Fechamento adiado: {e}")
        return "adiado"
    if wt.exists() or git(cfg, "rev-parse", "--verify", "-q", branch).returncode == 0:
        print("  Descartando resíduo de um fechamento anterior.")
        git(cfg, "worktree", "remove", "-f", "-f", str(wt))
        git(cfg, "worktree", "prune")
        git(cfg, "branch", "-D", branch)
    cmd = [exe, "-p", "-w", nome, "--model", f["model"], "--effort", f["effort"], "--max-budget-usd", str(f["budget"]),
           "--permission-mode", cfg.d["agente"]["permissao"], "--", prompt_fechamento(cfg, ids, tarefas)]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", cwd=cfg.raiz, timeout=f["timeout"])
    except subprocess.TimeoutExpired:
        print(f"  Fechamento excedeu {f['timeout']}s; veja {wt}.")
        return "falha"
    if p.returncode:
        print(f"  Fechamento FALHOU (código {p.returncode}): {(p.stdout + p.stderr).strip()[:300]}")
        return "falha"
    est, msg = integrar(cfg, "fechamento", False, set(f["proibidas_extensoes"]))
    print(f"  fechamento  {msg}")
    if est not in ("ok", "vazio"):
        return "falha"
    cfg.pendente_fechamento.unlink(missing_ok=True)
    git(cfg, "worktree", "remove", "-f", "-f", str(wt))
    git(cfg, "worktree", "prune")
    git(cfg, "branch", "-D", branch)
    return "ok"


def passo(cfg: Config, ambiente: str | None = None, fechamento: bool = True) -> dict:
    """Uma volta completa: colher, fechar o lote se ele acabou, disparar o próximo.

    Retorna as contagens do `colher` mais `novas` (disparadas) e `fechamento` (nada | adiado | ok | falha).
    """
    try:
        r = colher(cfg)
    except ColherErro as e:
        print(f"Colheita adiada: {e}")
        r = {"feitas": 0, "ocupadas": 1, "esperando": 0, "problemas": 0}
    r["fechamento"] = "nada"
    if fechamento and cfg.d["fechamento"]["ativo"] and not r["ocupadas"] and not r["esperando"] and not r["problemas"]:
        r["fechamento"] = fechar(cfg)
        if r["fechamento"] == "falha":
            r["novas"] = 0
            return r
    r["novas"] = disparar(cfg, ambiente)
    return r


def auto(cfg: Config, ambiente: str | None, intervalo: int, max_rodadas: int, fechamento: bool = True) -> None:
    rodada = 0
    while True:
        rodada += 1
        r = passo(cfg, ambiente, fechamento)
        if r["fechamento"] == "falha":
            print("Parado: o fechamento de lote falhou. Corrija e rode `backlog-auto fechar` (o lote seguinte só começa depois dele).")
            return
        if r["novas"] == 0 and r["ocupadas"] == 0 and r["feitas"] == 0:
            try:
                criadas = novas.planejar_se_preciso(cfg)
            except (novas.PlanejarErro, ConfigErro) as e:
                print(f"Parado: planejamento não concluído: {e}")
                return
            if criadas:
                print(f"Planejamento criou {criadas} tarefa(s) novas; seguindo.")
                continue
            if criadas == 0:
                print("Backlog esgotado e o planejamento não encontrou nada novo. Fim.")
                return
            if r["esperando"] or r["problemas"]:
                print("Parado: há tarefas esperando aprovação, bloqueadas ou com conflito. Veja `backlog-auto status`.")
            elif any(t["status"] == "blocked" for t in ler(cfg)[1].values()):
                print("Parado: há tarefas bloqueadas (uma tarefa de preparo bloqueada trava o resto). Veja `backlog-auto status`.")
            else:
                print("Nada em andamento nem liberado. Fim.")
            return
        if max_rodadas and rodada >= max_rodadas:
            print(f"Limite de {max_rodadas} rodadas atingido.")
            return
        time.sleep(intervalo)


def reiniciar(cfg: Config, ids: list[str] | None = None, forcar: bool = False, dry: bool = False) -> list[str]:
    """Descarta sessão, worktree e branch de tarefas travadas e as devolve para `todo`.

    Sem ids: as `doing`/`blocked`, poupando as que estão trabalhando (a menos que `forcar`).
    """
    linhas, tarefas = ler(cfg)
    exe = achar_claude(cfg)
    sessoes = {s.get("name"): s for s in (sessoes_ativas(exe) if exe else [])}
    nome_de = lambda tid: cfg.sessao_prefixo + tid  # noqa: E731
    if ids:
        desconhecidas = [i for i in ids if i not in tarefas]
        if desconhecidas:
            raise ValueError(f"tarefas inexistentes: {', '.join(desconhecidas)}")
        feitas = [i for i in ids if tarefas[i]["status"] == "done"]
        if feitas:
            raise ValueError(f"{', '.join(feitas)} já está done (integrada); não há o que reiniciar.")
        alvo = list(ids)
    else:
        alvo = [i for i, t in tarefas.items() if t["status"] in ("doing", "blocked")
                and (forcar or sessoes.get(nome_de(i), {}).get("status") != "busy")]
        poupadas = [i for i, t in tarefas.items() if t["status"] == "doing" and i not in alvo]
        if poupadas:
            print(f"  Poupadas por estarem trabalhando (use --forcar ou cite o id): {', '.join(poupadas)}")
    if not alvo:
        print("Nenhuma tarefa doing/blocked para reiniciar.")
        return []
    for tid in alvo:
        nome, branch = nome_de(tid), f"worktree-{nome_de(tid)}"
        wt = cfg.worktrees / nome
        perdidos = len(git(cfg, "log", "--oneline", f"{cfg.principal}..{branch}").stdout.split()) if wt.exists() else 0
        print(f"  {tid}  {'(simulação) ' if dry else ''}reinicia"
              + (f" (descarta {perdidos} commit(s) não integrados)" if perdidos else ""))
        if dry:
            continue
        s = sessoes.get(nome)
        if s and exe:
            subprocess.run([exe, "stop", s["id"]], capture_output=True)
            subprocess.run([exe, "rm", s["id"]], capture_output=True)
        if wt.exists():
            git(cfg, "worktree", "remove", "-f", "-f", str(wt))
        git(cfg, "worktree", "prune")
        git(cfg, "branch", "-D", branch)
        gravar_status(cfg, linhas, tarefas, tid, "todo")
    if not dry:
        commitar_controle(cfg, "backlog: reinicia " + ", ".join(alvo))
    return alvo


def gerar_progresso(cfg: Config, tarefas: dict, sessoes: list[dict]) -> str:
    cont = {s: sum(t["status"] == s for t in tarefas.values()) for s in ICONE}
    prox = lote(prontas(tarefas))
    nome = cfg.d["projeto"]["nome"]
    L = [f"# Progresso — {nome}", "",
         f"> Gerado por `backlog-auto status` a partir do [{cfg.backlog.name}]({cfg.backlog.name}). Não edite à mão.", "",
         f"Atualizado em {datetime.now():%d/%m/%Y %H:%M} · **{cont['done']}/{len(tarefas)} concluídas** · "
         f"{cont['doing']} em andamento · {cont['todo']} a fazer · {cont['blocked']} bloqueadas", "",
         "## Próximo lote (pode rodar em paralelo)", ""]
    feitas, total = preparo.estado(tarefas)
    if total and feitas < total:
        L.insert(-2, f"> ⚠️ Preparo da documentação em andamento ({feitas}/{total}): as demais tarefas só são liberadas depois dele.")
        L.insert(-2, "")
    L += [f"- **{t['id']}** [{t['ambiente']}, {t['dificuldade']} → {cfg.rota(t['dificuldade'])['model']}] {t['titulo']}"
          for t in prox] or ["- nenhum liberado"]
    bg = [s for s in sessoes if str(s.get("name", "")).startswith(cfg.sessao_prefixo)]
    L += ["", "## Sessões em background agora", ""]
    L += [f"- {s['name']}: {s.get('status', '?')}" + (f" ({s['waitingFor']})" if s.get("waitingFor") else "")
          for s in bg] or ["- nenhuma"]
    blocos: dict[str, list[dict]] = {}
    for t in tarefas.values():
        blocos.setdefault(t["bloco"] or "Tarefas", []).append(t)
    for bloco, ts in blocos.items():
        feitas = sum(t["status"] == "done" for t in ts)
        L += ["", f"## {bloco} ({feitas}/{len(ts)})", "",
              "| | Tarefa | Papel | Ambiente | Dificuldade | Depende |", "|---|---|---|---|---|---|"]
        L += [f"| {ICONE.get(t['status'], '?')} | **{t['id']}** {t['titulo']} | {t['papel']} | {t['ambiente']} | "
              f"{t['dificuldade']} | {t['depende']} |" for t in ts]
    return "\n".join(L) + "\n"


def status(cfg: Config) -> str:
    _, tarefas = ler(cfg)
    exe = achar_claude(cfg)
    texto = gerar_progresso(cfg, tarefas, sessoes_ativas(exe) if exe else [])
    cfg.progresso.write_text(texto, encoding="utf-8")
    return texto
