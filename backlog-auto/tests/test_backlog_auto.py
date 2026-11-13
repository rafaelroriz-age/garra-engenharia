import json
import subprocess
from pathlib import Path

import pytest

from backlog_auto import guard, hooks, runner
from backlog_auto.backlog import gravar_status, ler, lote, prontas, validar
from backlog_auto.config import ConfigErro, carregar
from backlog_auto.scaffold import init

BACKLOG = """# B

## Bloco A

### T01 · Primeira
- **Status:** todo
- **Papel:** x
- **Depende:** —
- **Ambiente:** offline
- **Dificuldade:** baixa
- **Toca:** src/a.py, docs/a.md
- **Prompt:**
```text
faça A
```

### T02 · Segunda
- **Status:** todo
- **Depende:** T01
- **Ambiente:** offline
- **Toca:** src/b.py
- **Prompt:**
```text
faça B
```

### T03 · Terceira
- **Status:** todo
- **Depende:** —
- **Ambiente:** offline
- **Dificuldade:** alta
- **Toca:** docs/x.md
- **Prompt:**
```text
faça C
```
"""


def sh(cwd, *a):
    return subprocess.run(["git", *a], cwd=cwd, capture_output=True, text=True, check=True).stdout


@pytest.fixture
def projeto(tmp_path, monkeypatch):
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    init(tmp_path, "Teste", False, True, True)
    (tmp_path / "BACKLOG.md").write_text(BACKLOG, encoding="utf-8")
    sh(tmp_path, "init", "-b", "main")
    sh(tmp_path, "config", "user.email", "t@t")
    sh(tmp_path, "config", "user.name", "t")
    sh(tmp_path, "add", "-A")
    sh(tmp_path, "commit", "-m", "base")
    monkeypatch.chdir(tmp_path)
    return carregar(tmp_path)


def test_init_cria_arquivos_e_hooks(projeto):
    r = projeto.raiz
    assert (r / "backlog.toml").exists() and (r / "docs" / "BACKLOG-MANUAL.md").exists()
    s = json.loads((r / ".claude" / "settings.json").read_text(encoding="utf-8"))
    assert "backlog_auto.hooks guard" in json.dumps(s["hooks"]["PreToolUse"])
    assert "backlog_auto.hooks lembrete" in json.dumps(s["hooks"]["PostToolUse"])
    assert ".claude/worktrees/" in (r / ".gitignore").read_text(encoding="utf-8")


def test_init_e_idempotente(projeto):
    init(projeto.raiz, "Teste", False, True, True)
    s = json.loads((projeto.raiz / ".claude" / "settings.json").read_text(encoding="utf-8"))
    assert len(s["hooks"]["PreToolUse"]) == 1 and len(s["hooks"]["PostToolUse"]) == 1


def test_template_ambientes_fica_no_topo(projeto):
    # Antes de qualquer [tabela]: senão o TOML o lê como projeto.ambientes e o valor editado é ignorado.
    toml = projeto.raiz / "backlog.toml"
    toml.write_text(toml.read_text(encoding="utf-8").replace('["offline", "humano"]', '["offline", "banco"]'),
                    encoding="utf-8")
    assert carregar(projeto.raiz).ambientes == ["offline", "banco"]


def test_sem_config_erro(tmp_path, monkeypatch):
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    with pytest.raises(ConfigErro):
        carregar(tmp_path)


def test_parser_e_dependencias(projeto):
    _, t = ler(projeto)
    assert list(t) == ["T01", "T02", "T03"]
    assert t["T01"]["bloco"] == "Bloco A" and t["T02"]["dificuldade"] == "media"
    assert [x["id"] for x in prontas(t)] == ["T01", "T03"]


def test_lote_evita_conflito_de_toca(projeto):
    _, t = ler(projeto)
    assert {x["id"] for x in lote(prontas(t))} == {"T01", "T03"}
    t["T03"]["toca"] = "docs"
    assert {x["id"] for x in lote(prontas(t))} == {"T01"}


def test_gravar_status_so_muda_a_linha(projeto):
    linhas, t = ler(projeto)
    gravar_status(projeto, linhas, t, "T01", "done")
    _, t2 = ler(projeto)
    assert t2["T01"]["status"] == "done" and t2["T02"]["status"] == "todo"
    assert [x["id"] for x in prontas(t2)] == ["T02", "T03"]
    with pytest.raises(ValueError):
        gravar_status(projeto, linhas, t, "T01", "feito")


def test_validar_acusa_problemas(projeto):
    _, t = ler(projeto)
    assert validar(projeto, t) == []
    t["T02"]["depende"] = "T09"
    t["T01"]["depende"] = "T02"
    t["T02"]["depende"] = "T01"
    erros = " ".join(validar(projeto, t))
    assert "ciclo" in erros


def test_validar_exige_doc_dentro_de_toca(projeto):
    _, t = ler(projeto)
    t["T03"]["doc"] = "docs/outro.md §2, docs/x.md"
    erros = validar(projeto, t)
    assert any("T03" in e and "docs/outro.md" in e for e in erros)
    assert not any("docs/x.md" in e for e in erros)
    t["T03"]["status"] = "done"
    assert validar(projeto, t) == []


def test_rota_e_comando_da_sessao(projeto):
    _, t = ler(projeto)
    cmd = runner.comando_sessao(projeto, "claude", t["T03"], None)
    assert cmd[cmd.index("--model") + 1] == "opus" and cmd[cmd.index("--max-budget-usd") + 1] == "8"
    assert cmd[cmd.index("--permission-mode") + 1] == "bypassPermissions"
    assert cmd[-1].endswith("faça C")
    forcado = runner.comando_sessao(projeto, "claude", t["T03"], "haiku")
    assert forcado[forcado.index("--model") + 1] == "haiku"


def test_guard_bloqueia_e_libera(projeto, monkeypatch):
    sql = "DROP " + "TABLE clientes"
    assert guard.violacoes(projeto, sql) == ["DML/DDL SQL"]
    assert guard.violacoes(projeto, "SELECT 1") == []
    monkeypatch.setenv("BACKLOG_ESCRITA", "1")
    assert guard.violacoes(projeto, sql) == []


def test_guard_comando_so_com_gatilho_e_codigo_sempre(projeto):
    sql = "DELETE " + "FROM t"
    assert guard.avaliar(projeto, {"command": f'echo "{sql}"'}) == []
    assert guard.avaliar(projeto, {"command": f'psql -c "{sql}"'}) != []
    assert guard.avaliar(projeto, {"file_path": "x/a.py", "content": sql}) != []
    assert guard.avaliar(projeto, {"file_path": "x/.claude/hooks/a.py", "content": sql}) == []
    destino = "/Tab" + "les/"
    assert guard.avaliar(projeto, {"file_path": "a.py", "content": f'df.write.save("abfss://x{destino}t")'}) != []


def test_hook_guard_e_fail_open(projeto, monkeypatch, capsys):
    import io
    sql = "DROP " + "TABLE t"
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps({"tool_input": {"file_path": "a.sql", "content": sql}})))
    assert hooks.main(["guard"]) == 2
    monkeypatch.setattr("sys.stdin", io.StringIO("não é json"))
    assert hooks.main(["guard"]) == 0


def test_hook_lembrete(projeto, monkeypatch, capsys):
    import io
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps({"tool_input": {"file_path": "src/a.py"}})))
    assert hooks.main(["lembrete"]) == 0
    assert "additionalContext" in capsys.readouterr().out


def _simular_sessao(projeto, tid, arquivo, texto):
    nome = projeto.sessao_prefixo + tid
    wt = projeto.worktrees / nome
    sh(projeto.raiz, "worktree", "add", str(wt), "-b", f"worktree-{nome}")
    (wt / arquivo).parent.mkdir(parents=True, exist_ok=True)
    (wt / arquivo).write_text(texto, encoding="utf-8")
    return wt


def test_colher_integra_e_marca_done(projeto, monkeypatch):
    monkeypatch.setattr(runner, "sessoes_ativas", lambda exe: [])
    monkeypatch.setattr(runner, "achar_claude", lambda cfg: None)
    linhas, t = ler(projeto)
    gravar_status(projeto, linhas, t, "T01", "doing")
    sh(projeto.raiz, "commit", "-am", "doing")
    _simular_sessao(projeto, "T01", "src/a.py", "x = 1\n")  # sem commit: o integrador deve commitar
    assert runner.colher(projeto)["feitas"] == 1
    _, t2 = ler(projeto)
    assert t2["T01"]["status"] == "done"
    assert (projeto.raiz / "src" / "a.py").exists()
    assert "worktree-backlog-T01" not in sh(projeto.raiz, "branch")
    assert sh(projeto.raiz, "status", "--porcelain", "--untracked-files=no").strip() == ""


def test_colher_sessao_vazia_vira_blocked(projeto, monkeypatch):
    monkeypatch.setattr(runner, "sessoes_ativas", lambda exe: [])
    monkeypatch.setattr(runner, "achar_claude", lambda cfg: None)
    linhas, t = ler(projeto)
    gravar_status(projeto, linhas, t, "T03", "doing")
    sh(projeto.raiz, "commit", "-am", "doing")
    nome = projeto.sessao_prefixo + "T03"
    sh(projeto.raiz, "worktree", "add", str(projeto.worktrees / nome), "-b", f"worktree-{nome}")
    assert runner.colher(projeto)["problemas"] == 1
    assert ler(projeto)[1]["T03"]["status"] == "blocked"


def test_colher_respeita_sessao_ocupada_e_main_suja(projeto, monkeypatch):
    monkeypatch.setattr(runner, "achar_claude", lambda cfg: "claude")
    monkeypatch.setattr(runner, "sessoes_ativas", lambda exe: [{"name": "backlog-T01", "status": "busy", "id": "a"}])
    linhas, t = ler(projeto)
    gravar_status(projeto, linhas, t, "T01", "doing")
    sh(projeto.raiz, "commit", "-am", "doing")
    assert runner.colher(projeto)["ocupadas"] == 1
    (projeto.raiz / "docs" / "BACKLOG-MANUAL.md").write_text("mudou", encoding="utf-8")
    projeto.d["projeto"]["autocommit"] = False
    with pytest.raises(runner.ColherErro):
        runner.colher(projeto)


def test_colher_commita_pendencias_sem_chave_de_assinatura(projeto, monkeypatch):
    monkeypatch.setattr(runner, "achar_claude", lambda cfg: None)
    monkeypatch.setattr(runner, "sessoes_ativas", lambda exe: [])
    sh(projeto.raiz, "config", "commit.gpgsign", "true")
    sh(projeto.raiz, "config", "gpg.program", "programa-que-nao-existe")
    linhas, t = ler(projeto)
    gravar_status(projeto, linhas, t, "T01", "doing")
    sh(projeto.raiz, "-c", "commit.gpgsign=false", "commit", "-am", "doing")
    _simular_sessao(projeto, "T01", "src/a.py", "x = 1\n")
    (projeto.raiz / "docs" / "BACKLOG-MANUAL.md").write_text("mudou", encoding="utf-8")
    assert runner.colher(projeto)["feitas"] == 1
    assert sh(projeto.raiz, "status", "--porcelain", "--untracked-files=no").strip() == ""
    assert "pendentes antes de integrar" in sh(projeto.raiz, "log", "--format=%s")


def test_restart_descarta_worktree_e_volta_para_todo(projeto, monkeypatch):
    monkeypatch.setattr(runner, "sessoes_ativas", lambda exe: [])
    monkeypatch.setattr(runner, "achar_claude", lambda cfg: None)
    linhas, t = ler(projeto)
    gravar_status(projeto, linhas, t, "T01", "doing")
    gravar_status(projeto, linhas, t, "T03", "done")
    sh(projeto.raiz, "commit", "-am", "doing")
    _simular_sessao(projeto, "T01", "src/a.py", "x = 1\n")
    with pytest.raises(ValueError):
        runner.reiniciar(projeto, ["T03"])
    assert runner.reiniciar(projeto, dry=True) == ["T01"]
    assert ler(projeto)[1]["T01"]["status"] == "doing"
    assert runner.reiniciar(projeto) == ["T01"]
    assert ler(projeto)[1]["T01"]["status"] == "todo"
    assert not (projeto.worktrees / "backlog-T01").exists()
    assert "worktree-backlog-T01" not in sh(projeto.raiz, "branch")


def test_restart_poupa_sessao_trabalhando(projeto, monkeypatch):
    monkeypatch.setattr(runner, "achar_claude", lambda cfg: "claude")
    monkeypatch.setattr(runner, "sessoes_ativas", lambda exe: [{"name": "backlog-T01", "status": "busy", "id": "a"}])
    linhas, t = ler(projeto)
    gravar_status(projeto, linhas, t, "T01", "doing")
    assert runner.reiniciar(projeto, dry=True) == []
    assert runner.reiniciar(projeto, forcar=True, dry=True) == ["T01"]


def test_status_gera_painel(projeto, monkeypatch):
    monkeypatch.setattr(runner, "achar_claude", lambda cfg: None)
    txt = runner.status(projeto)
    assert "0/3 concluídas" in txt and "T01" in txt and projeto.progresso.exists()


def test_preparo_insere_uma_vez_e_trava_o_resto(projeto):
    from backlog_auto import preparo
    assert preparo.garantir(projeto) is True and preparo.garantir(projeto) is False
    _, t = ler(projeto)
    assert [i for i in t if t[i]["fase"] == "preparo"] == ["D01", "D02", "D03", "D04", "D05"]
    assert validar(projeto, t) == []
    assert [x["id"] for x in prontas(t)] == ["D01", "D02"]          # D01 e D02 em paralelo; T01..T03 travadas
    assert {x["id"] for x in lote(prontas(t))} == {"D01", "D02"}
    assert "01_sistema.md" in t["D01"]["prompt"] and "efetiva" in t["D03"]["prompt"]


def test_preparo_libera_o_backlog_so_no_fim(projeto):
    from backlog_auto import preparo
    preparo.garantir(projeto)
    for i in ("D01", "D02", "D03", "D04"):
        linhas, t = ler(projeto)
        gravar_status(projeto, linhas, t, i, "done")
    assert [x["id"] for x in prontas(ler(projeto)[1])] == ["D05"]
    linhas, t = ler(projeto)
    gravar_status(projeto, linhas, t, "D05", "done")
    assert [x["id"] for x in prontas(ler(projeto)[1])] == ["T01", "T03"]
    assert preparo.refazer(projeto) == 5
    assert [x["id"] for x in prontas(ler(projeto)[1])] == ["D01", "D02"]


def test_preparo_usa_objetivo_declarado_e_detecta_colisao(projeto):
    from backlog_auto import preparo
    projeto.d["preparo"]["objetivo"] = "prever consumo de amostras"
    assert "prever consumo de amostras" in preparo.definicao(projeto)[0]["prompt"]
    assert "inferido" in (lambda c: (c.d["preparo"].update(objetivo=""), preparo.definicao(c)[0]["prompt"])[1])(projeto)
    projeto.d["preparo"]["prefixo_id"] = "T"
    with pytest.raises(ConfigErro):
        preparo.garantir(projeto)


def test_disparar_adiciona_preparo_quando_ativo(projeto, capsys):
    runner.disparar(projeto, dry=True)
    out = capsys.readouterr().out
    assert "D01" in out and "D02" in out and "T01" not in out


def test_init_cria_guia_do_celular(projeto):
    txt = (projeto.raiz / "docs" / "CELULAR.md").read_text(encoding="utf-8")
    assert "Teste" in txt and "{{" not in txt and "backlog-auto auto" in txt


def _claude_falso(monkeypatch, projeto, arquivo, texto):
    """Troca a chamada ao `claude -p -w` por uma sessão simulada que escreve `arquivo` no worktree de fechamento."""
    real = subprocess.run
    chamadas = []

    def falso(cmd, *a, **k):
        if cmd[0] != "claude-falso":
            return real(cmd, *a, **k)
        chamadas.append(cmd)
        nome = cmd[cmd.index("-w") + 1]
        wt = projeto.worktrees / nome
        sh(projeto.raiz, "worktree", "add", str(wt), "-b", f"worktree-{nome}")
        (wt / arquivo).parent.mkdir(parents=True, exist_ok=True)
        (wt / arquivo).write_text(texto, encoding="utf-8")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(runner.subprocess, "run", falso)
    monkeypatch.setattr(runner, "achar_claude", lambda cfg: "claude-falso")
    monkeypatch.setattr(runner, "sessoes_ativas", lambda exe: [])
    return chamadas


def _lote_colhido(projeto):
    linhas, t = ler(projeto)
    gravar_status(projeto, linhas, t, "T01", "doing")
    sh(projeto.raiz, "commit", "-am", "doing")
    _simular_sessao(projeto, "T01", "src/a.py", "x = 1\n")
    assert runner.colher(projeto)["feitas"] == 1


def test_fechamento_do_backlog_le_o_bloco_da_secao(projeto):
    from backlog_auto.backlog import PROMPT_FECHAMENTO_PADRAO, fechamento_do_backlog
    assert fechamento_do_backlog(projeto).strip() != ""
    projeto.backlog.write_text("# B\n\n## Fechamento de lote\n\n```text\natualize X\ne Y\n```\n\n## Outro\n```text\nnão\n```\n", encoding="utf-8")
    assert fechamento_do_backlog(projeto) == "atualize X\ne Y"
    projeto.backlog.write_text("# B\n", encoding="utf-8")
    assert fechamento_do_backlog(projeto) == PROMPT_FECHAMENTO_PADRAO


def test_colher_registra_lote_pendente_e_fechar_sem_pendencia_nao_faz_nada(projeto, monkeypatch):
    monkeypatch.setattr(runner, "sessoes_ativas", lambda exe: [])
    monkeypatch.setattr(runner, "achar_claude", lambda cfg: None)
    assert runner.fechar(projeto) == "nada"
    _lote_colhido(projeto)
    assert runner._pendentes(projeto) == ["T01"]


def test_fechar_integra_documentacao_e_limpa_pendencia(projeto, monkeypatch):
    _lote_colhido(projeto)
    chamadas = _claude_falso(monkeypatch, projeto, "docs/status.md", "T01 feita\n")
    assert runner.fechar(projeto) == "ok"
    assert (projeto.raiz / "docs" / "status.md").read_text(encoding="utf-8") == "T01 feita\n"
    assert runner._pendentes(projeto) == []
    assert "worktree-backlog-fechamento" not in sh(projeto.raiz, "branch")
    assert "-p" in chamadas[0] and "T01" in chamadas[0][-1] and "SESSÃO DE FECHAMENTO" in chamadas[0][-1]


def test_fechar_recusa_mudanca_em_codigo_e_mantem_pendencia(projeto, monkeypatch):
    _lote_colhido(projeto)
    _claude_falso(monkeypatch, projeto, "src/novo.py", "x = 2\n")
    assert runner.fechar(projeto) == "falha"
    assert not (projeto.raiz / "src" / "novo.py").exists()
    assert runner._pendentes(projeto) == ["T01"]


def test_fechar_adia_com_tarefa_em_andamento(projeto, monkeypatch):
    _lote_colhido(projeto)
    linhas, t = ler(projeto)
    gravar_status(projeto, linhas, t, "T03", "doing")
    assert runner.fechar(projeto) == "adiado"


def test_passo_fecha_o_lote_antes_de_disparar_o_proximo(projeto, monkeypatch):
    _lote_colhido(projeto)
    ordem = []
    monkeypatch.setattr(runner, "fechar", lambda cfg, dry=False: ordem.append("fechar") or "ok")
    monkeypatch.setattr(runner, "disparar", lambda cfg, amb=None, *a: ordem.append("disparar") or 2)
    monkeypatch.setattr(runner, "colher", lambda cfg: ordem.append("colher") or {"feitas": 0, "ocupadas": 0, "esperando": 0, "problemas": 0})
    r = runner.passo(projeto)
    assert ordem == ["colher", "fechar", "disparar"] and r["novas"] == 2
    ordem.clear()
    runner.passo(projeto, fechamento=False)
    assert ordem == ["colher", "disparar"]


def _item(**extra):
    base = {"bloco": "Bloco A", "titulo": "Nova tarefa", "papel": "backend", "ambiente": "offline",
            "dificuldade": "baixa", "toca": "src/novo.py, docs/novo.md", "doc": "docs/novo.md", "pronto": "testes verdes",
            "prompt": "Faça o novo módulo e registre em docs/novo.md."}
    return {**base, **extra}


def test_nova_cria_ids_em_sequencia_e_resolve_chaves(projeto):
    from backlog_auto import novas
    ids = novas.inserir(projeto, [
        _item(chave="X", titulo="Primeira", origem="BL-10"),
        _item(chave="Y", titulo="Segunda", depende="X, T01", toca="src/outro.py, docs/outro.md", doc="docs/outro.md"),
    ])
    assert ids == ["T04", "T05"]
    _, t = ler(projeto)
    assert t["T04"]["origem"] == "BL-10" and t["T04"]["status"] == "todo"
    assert t["T05"]["depende"] == "T04, T01"
    assert t["T04"]["bloco"] == "Bloco A" and t["T05"]["bloco"] == "Bloco A"
    assert t["T05"]["prompt"].strip() == "Faça o novo módulo e registre em docs/novo.md."
    assert not validar(projeto, t)


def test_nova_rejeita_lote_invalido_sem_gravar(projeto):
    from backlog_auto import novas
    from backlog_auto.config import ConfigErro
    antes = projeto.backlog.read_text(encoding="utf-8")
    with pytest.raises(ConfigErro):
        novas.inserir(projeto, [_item(ambiente="nuvem")])
    with pytest.raises(ConfigErro):
        novas.inserir(projeto, [_item(depende="T99")])
    with pytest.raises(ConfigErro):
        novas.inserir(projeto, [_item(prompt="")])
    assert projeto.backlog.read_text(encoding="utf-8") == antes


def test_nova_ignora_origem_ja_cadastrada(projeto):
    from backlog_auto import novas
    assert novas.inserir(projeto, [_item(origem="BL-7")]) == ["T04"]
    assert novas.inserir(projeto, [_item(origem="BL-7", titulo="repetida")]) == []


def test_nova_cria_bloco_que_nao_existe(projeto):
    from backlog_auto import novas
    novas.inserir(projeto, [_item(bloco="Bloco Z — Outro")])
    _, t = ler(projeto)
    assert t["T04"]["bloco"] == "Bloco Z — Outro"


def test_planejar_grava_o_json_da_sessao_so_leitura(projeto, monkeypatch):
    from backlog_auto import novas
    real = subprocess.run
    chamadas = []
    saida = ("Aqui está:\n```json\n" + json.dumps([
        {"chave": "A", "bloco": "Bloco A", "titulo": "Planejada", "origem": "BL-20", "papel": "backend",
         "depende": [], "ambiente": "offline", "dificuldade": "baixa", "toca": "src/p.py, docs/p.md", "doc": "docs/p.md",
         "pronto": "ok", "prompt": "faça p"}]) + "\n```")

    def falso(cmd, *a, **k):
        if cmd[0] != "claude-falso":
            return real(cmd, *a, **k)
        chamadas.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, saida, "")

    monkeypatch.setattr(novas.subprocess, "run", falso)
    monkeypatch.setattr(runner, "achar_claude", lambda cfg: "claude-falso")
    assert novas.planejar(projeto) == 1
    cmd = chamadas[0]
    assert cmd[cmd.index("--allowedTools") + 1] == "Read,Grep,Glob"
    _, t = ler(projeto)
    assert t["T04"]["origem"] == "BL-20"
    assert "planejamento cria T04" in sh(projeto.raiz, "log", "-1", "--format=%s")


def _planejar_com(projeto, monkeypatch, itens):
    from backlog_auto import novas
    real = subprocess.run
    saida = "```json\n" + json.dumps(itens) + "\n```"

    def falso(cmd, *a, **k):
        if cmd[0] != "claude-falso":
            return real(cmd, *a, **k)
        return subprocess.CompletedProcess(cmd, 0, saida, "")

    monkeypatch.setattr(novas.subprocess, "run", falso)
    monkeypatch.setattr(runner, "achar_claude", lambda cfg: "claude-falso")
    return novas.planejar(projeto)


def _plan_item(chave, depende=(), n=0):
    return {"chave": chave, "bloco": "Bloco A", "titulo": f"Plan {chave}", "origem": f"BL-9{n}", "papel": "backend",
            "depende": list(depende), "ambiente": "offline", "dificuldade": "baixa", "toca": f"src/{chave}.py",
            "pronto": "ok", "prompt": "faça"}


def test_planejar_descarta_dependencia_desconhecida(projeto, monkeypatch, capsys):
    assert _planejar_com(projeto, monkeypatch, [_plan_item("A", ["B"])]) == 1
    _, t = ler(projeto)
    assert t["T04"]["depende"] in ([], "—")
    assert "dependência 'B' descartada" in capsys.readouterr().err


def test_planejar_corte_nao_deixa_dependencia_orfa(projeto, monkeypatch):
    projeto.d["planejamento"]["max_tarefas"] = 2
    itens = [_plan_item("A", ["F"], 1), _plan_item("B", [], 2), _plan_item("C", [], 3), _plan_item("F", [], 6)]
    assert _planejar_com(projeto, monkeypatch, itens) == 2
    _, t = ler(projeto)
    assert {t["T04"]["origem"], t["T05"]["origem"]} == {"BL-91", "BL-96"}


def test_nova_manual_continua_estrita_com_dependencia_inexistente(projeto):
    from backlog_auto import novas
    from backlog_auto.config import ConfigErro
    with pytest.raises(ConfigErro):
        novas.inserir(projeto, [_item(depende=["B"])])


def test_planejar_dry_nao_chama_o_claude(projeto, monkeypatch, capsys):
    from backlog_auto import novas
    monkeypatch.setattr(runner, "achar_claude", lambda cfg: pytest.fail("não podia chamar o claude"))
    assert novas.planejar(projeto, dry=True) == 0
    assert "Responda SOMENTE com uma lista JSON" in capsys.readouterr().out


def test_planejar_se_preciso_so_quando_o_backlog_acaba(projeto, monkeypatch):
    from backlog_auto import novas
    monkeypatch.setattr(novas, "planejar", lambda cfg, dry=False: pytest.fail("não era hora"))
    assert novas.planejar_se_preciso(projeto) is None  # desligado por padrão
    projeto.d["planejamento"]["ativo"] = True
    assert novas.planejar_se_preciso(projeto) is None  # ainda há tarefas todo


def test_passo_nao_dispara_se_o_fechamento_falhou(projeto, monkeypatch):
    monkeypatch.setattr(runner, "colher", lambda cfg: {"feitas": 0, "ocupadas": 0, "esperando": 0, "problemas": 0})
    monkeypatch.setattr(runner, "fechar", lambda cfg, dry=False: "falha")
    monkeypatch.setattr(runner, "disparar", lambda *a, **k: pytest.fail("não podia disparar"))
    assert runner.passo(projeto)["fechamento"] == "falha"
