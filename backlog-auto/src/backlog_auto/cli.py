"""Linha de comando: `backlog-auto <comando>` ou `python -m backlog_auto <comando>`."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import preparo, runner
from .backlog import gravar_status, ler, lote, prontas, validar
from .config import ConfigErro, carregar
from .scaffold import doctor, init


def _lista(cfg, a):
    _, tarefas = ler(cfg)
    for t in tarefas.values():
        if a.ambiente and t["ambiente"] != a.ambiente:
            continue
        print(f'{t["id"]}  {t["status"]:<7} {t["ambiente"]:<8} {t["dificuldade"]:<6} {t["papel"]:<22} {t["titulo"]}  [dep: {t["depende"]}]')


def _proximo(cfg, a):
    _, tarefas = ler(cfg)
    prox = prontas(tarefas, a.ambiente)
    if not prox:
        print("Nenhuma tarefa liberada.")
        return
    paralelo = lote(prox)
    print("Lote paralelo seguro (sem arquivos em comum):")
    for t in paralelo:
        print(f'  {t["id"]}  [{t["ambiente"]}, {t["dificuldade"]}] {t["titulo"]}')
    espera = [t for t in prox if t not in paralelo]
    if espera:
        print("Liberadas, mas conflitam com o lote (próxima rodada):")
        for t in espera:
            print(f'  {t["id"]}  [{t["ambiente"]}, {t["dificuldade"]}] {t["titulo"]}')
    if a.prompts:
        for t in paralelo:
            print(f'\n===== {t["id"]} =====\n{t["prompt"]}')


def _mostrar(cfg, a):
    _, tarefas = ler(cfg)
    if a.id not in tarefas:
        sys.exit(f"Tarefa {a.id} não existe.")
    print(tarefas[a.id]["prompt"].rstrip())


def _definir(cfg, a):
    linhas, tarefas = ler(cfg)
    try:
        gravar_status(cfg, linhas, tarefas, a.id, a.status)
    except (KeyError, ValueError) as e:
        sys.exit(str(e.args[0]))
    print(f"{a.id} -> {a.status}")


def _validar(cfg, a):
    _, tarefas = ler(cfg)
    erros = validar(cfg, tarefas)
    for e in erros:
        print(f"- {e}")
    print("Backlog válido." if not erros else f"{len(erros)} problema(s).")
    return 1 if erros else 0


def _preparo(cfg, a):
    if preparo.garantir(cfg):
        print("Fase de preparo inserida no backlog.")
    if a.refazer:
        print(f"{preparo.refazer(cfg)} tarefas de preparo voltaram para todo.")
    feitas, total = preparo.estado(ler(cfg)[1])
    print(f"Preparo: {feitas}/{total} concluídas. Rode `backlog-auto auto` para executar.")


def _colher(cfg, a):
    try:
        res = runner.colher(cfg, a.dry)
    except runner.ColherErro as e:
        sys.exit(f"Colheita recusada: {e}")
    if res["feitas"]:
        print("\nLote concluído? Rode o 'Fechamento de lote' do backlog antes do próximo.")


def _fechar(cfg, a):
    return 1 if runner.fechar(cfg, a.dry) == "falha" else 0


def _avancar(cfg, a):
    r = runner.passo(cfg, a.ambiente, not a.sem_fechamento)
    print(f"Colhidas {r['feitas']} · fechamento: {r['fechamento']} · disparadas {r['novas']} · em andamento {r['ocupadas']}"
          f" · esperando {r['esperando']} · com problema {r['problemas']}")
    return 1 if r["fechamento"] == "falha" else 0


def _restart(cfg, a):
    try:
        runner.reiniciar(cfg, a.ids, a.forcar, a.dry)
    except ValueError as e:
        sys.exit(str(e))
    if a.auto and not a.dry:
        runner.auto(cfg, a.ambiente, a.intervalo, a.max_rodadas, not a.sem_fechamento)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="backlog-auto", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init", help="instala o sistema no projeto (backlog.toml, BACKLOG.md, manual, hooks)")
    p.add_argument("pasta", nargs="?", default=".")
    p.add_argument("--nome")
    p.add_argument("--force", action="store_true", help="sobrescreve arquivos existentes")
    p.add_argument("--sem-guard", action="store_true")
    p.add_argument("--sem-lembrete", action="store_true")

    sub.add_parser("doctor", help="diagnostica a instalação")
    sub.add_parser("validar", help="confere o backlog (campos, dependências, ciclos)")
    p = sub.add_parser("preparo", help="insere a fase de preparo da documentação no backlog (D01..D05)")
    p.add_argument("--refazer", action="store_true", help="volta as tarefas de preparo para todo (reclassifica e refaz a documentação)")
    for nome in ("list", "next"):
        p = sub.add_parser(nome)
        p.add_argument("--ambiente")
        if nome == "next":
            p.add_argument("--prompts", action="store_true")
    sub.add_parser("show").add_argument("id")
    p = sub.add_parser("set")
    p.add_argument("id")
    p.add_argument("status")
    p = sub.add_parser("run", help="dispara o próximo lote em sessões background")
    p.add_argument("--ambiente")
    p.add_argument("--model", help="força um modelo para o lote (ignora a dificuldade)")
    p.add_argument("--dry", action="store_true")
    sub.add_parser("colher", help="integra na principal o que terminou e marca done").add_argument("--dry", action="store_true")
    p = sub.add_parser("fechar", help="roda a sessão de fechamento de lote (documentação) e integra o resultado")
    p.add_argument("--dry", action="store_true")
    p = sub.add_parser("avancar", help="um passo: colher, fechar o lote se acabou e disparar o próximo")
    p.add_argument("--ambiente")
    p.add_argument("--sem-fechamento", action="store_true")
    p = sub.add_parser("auto", help="colher + fechar lote + run em loop até acabar")
    p.add_argument("--ambiente")
    p.add_argument("--sem-fechamento", action="store_true", help="não roda o fechamento de lote entre os lotes")
    p.add_argument("--intervalo", type=int, default=120)
    p.add_argument("--max-rodadas", type=int, default=0, help="0 = sem limite")
    p = sub.add_parser("restart", help="recomeça tarefas travadas (doing/blocked): descarta sessão, worktree e branch")
    p.add_argument("ids", nargs="*", help="tarefas a reiniciar; sem ids, as doing/blocked que não estão trabalhando")
    p.add_argument("--dry", action="store_true")
    p.add_argument("--forcar", action="store_true", help="inclui também as sessões que estão trabalhando")
    p.add_argument("--auto", action="store_true", help="depois de reiniciar, retoma o fluxo automático")
    p.add_argument("--sem-fechamento", action="store_true")
    p.add_argument("--ambiente")
    p.add_argument("--intervalo", type=int, default=120)
    p.add_argument("--max-rodadas", type=int, default=0)
    sub.add_parser("status", help="regenera e imprime o painel de progresso")
    a = ap.parse_args(argv)

    if sys.platform.startswith("win"):
        sys.stdout.reconfigure(encoding="utf-8")
    if a.cmd == "init":
        for linha in init(Path(a.pasta), a.nome, a.force, not a.sem_guard, not a.sem_lembrete):
            print(linha)
        print("\nPróximo passo: edite backlog.toml e BACKLOG.md, `git add` e commit, depois `backlog-auto doctor`.")
        return 0
    if a.cmd == "doctor":
        return doctor()
    try:
        cfg = carregar()
    except ConfigErro as e:
        sys.exit(str(e))
    acoes = {
        "list": lambda: _lista(cfg, a), "next": lambda: _proximo(cfg, a), "show": lambda: _mostrar(cfg, a),
        "set": lambda: _definir(cfg, a), "validar": lambda: _validar(cfg, a), "preparo": lambda: _preparo(cfg, a),
        "run": lambda: runner.disparar(cfg, a.ambiente, a.model, a.dry), "colher": lambda: _colher(cfg, a),
        "auto": lambda: runner.auto(cfg, a.ambiente, a.intervalo, a.max_rodadas, not a.sem_fechamento),
        "fechar": lambda: _fechar(cfg, a), "avancar": lambda: _avancar(cfg, a),
        "restart": lambda: _restart(cfg, a), "status": lambda: print(runner.status(cfg)),
    }
    r = acoes[a.cmd]()
    return r if isinstance(r, int) and a.cmd in ("validar", "fechar", "avancar") else 0


if __name__ == "__main__":
    raise SystemExit(main())
