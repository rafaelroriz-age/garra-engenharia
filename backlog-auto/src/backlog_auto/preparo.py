"""Fase de preparo: antes de qualquer tarefa do backlog, documenta (ou valida a documentação de) o sistema.

São tarefas comuns do backlog (`- **Fase:** preparo`), então rodam como sessões em background pelo mesmo
`run`/`auto`, e o backlog normal só é liberado quando todas estiverem `done`.

Cadeia: D01 mapeia o sistema e D02 inventaria a documentação (em paralelo) → D03 classifica cada documento
(efetiva / parcial / refazer / ausente) → D04 cria o que falta e refaz o que não presta → D05 confere tudo contra o código.
"""
from __future__ import annotations

from .backlog import gravar_status, ler
from .config import Config, ConfigErro

FASE = "preparo"
TITULO_BLOCO = "## Bloco 0 — Preparo da documentação (automático)"


def _regras(cfg: Config) -> str:
    p = cfg.d["preparo"]
    return (
        f"Escreva em {p['idioma']}. Só altere arquivos de documentação (nunca código-fonte, testes ou dados). "
        "O projeto pode já ter documentação ou regras de documentação sob qualquer nome (AGENTS.md, CLAUDE.md, LEIA-ME, "
        "CONTRIBUTING, índice, plano, guia, manual, pastas docs_* ou wiki): procure por conteúdo, não só pelo nome, e siga as "
        "convenções de pasta, formato e índice que encontrar. "
        "Não invente: cada afirmação precisa de um caminho de arquivo ou comando que você verificou. "
        "Onde não der para saber, escreva 'não determinado' em vez de supor."
    )


def definicao(cfg: Config) -> list[dict]:
    p = cfg.d["preparo"]
    docs, trab = p["pasta_docs"].rstrip("/"), p["pasta_trabalho"].rstrip("/")
    px = p["prefixo_id"]
    i = [f"{px}{n:02d}" for n in range(1, 6)]
    objetivo = (f" O dono declara o objetivo do sistema como: «{p['objetivo'].strip()}». Use-o como referência e aponte "
                "qualquer divergência com o que o código realmente faz.") if p["objetivo"].strip() else (
        " Ninguém declarou o objetivo: infira-o do README, do código, dos commits e da configuração, e marque-o como "
        "'inferido' com o nível de confiança (alta/média/baixa) e as evidências.")
    regras = _regras(cfg)
    return [
        {"id": i[0], "titulo": "Mapear o sistema e seu objetivo", "papel": "analista", "depende": "—", "dificuldade": "alta",
         "toca": f"{trab}/01_sistema.md", "doc": f"{trab}/01_sistema.md",
         "pronto": f"`{trab}/01_sistema.md` descreve objetivo, componentes, fluxo e como instalar, rodar e testar, com evidências.",
         "prompt": (f"Tarefa {i[0]}. Leia o sistema deste repositório (estrutura, código-fonte, configuração, testes, dependências, "
                    f"histórico do git) e escreva {trab}/01_sistema.md com: (1) objetivo do sistema e quem o usa;{objetivo} "
                    "(2) entradas e saídas; (3) tabela de componentes (caminho → responsabilidade); (4) fluxo principal de dados ou "
                    "de execução; (5) como instalar, rodar e testar (rode os testes se existirem e registre o resultado); "
                    "(6) dependências e serviços externos; (7) riscos e lacunas visíveis no código. "
                    f"{regras} Siga a \"Regra de pronto\" do BACKLOG.md.")},
        {"id": i[1], "titulo": "Inventariar a documentação existente", "papel": "analista", "depende": "—", "dificuldade": "media",
         "toca": f"{trab}/02_inventario.md", "doc": f"{trab}/02_inventario.md",
         "pronto": f"`{trab}/02_inventario.md` lista todo documento existente ou declara explicitamente que não há nenhum.",
         "prompt": (f"Tarefa {i[1]}. Encontre toda a documentação que já existe no repositório: arquivos .md/.rst/.txt/.docx, READMEs "
                    "em qualquer pasta, wiki, docstrings de módulo, cabeçalhos de scripts, notebooks com texto explicativo, "
                    "AGENTS.md/CLAUDE.md. Escreva "
                    f"{trab}/02_inventario.md com uma tabela (caminho, tema, tamanho, data do último commit que o tocou via "
                    "`git log -1 --format=%cs -- <arquivo>`, uma linha de resumo do que ele diz). Se não houver nenhuma "
                    "documentação além do código, escreva exatamente 'Nenhuma documentação existente.' no topo. "
                    f"Não avalie a qualidade aqui (isso é a próxima etapa). {regras} Siga a \"Regra de pronto\" do BACKLOG.md.")},
        {"id": i[2], "titulo": "Classificar a documentação: efetiva ou refazer", "papel": "analista", "depende": f"{i[0]}, {i[1]}",
         "dificuldade": "alta", "toca": f"{trab}/03_classificacao.md", "doc": f"{trab}/03_classificacao.md",
         "pronto": f"`{trab}/03_classificacao.md` dá um veredito com evidência para cada documento e lista o que criar e refazer.",
         "prompt": (f"Tarefa {i[2]}. Leia {trab}/01_sistema.md e {trab}/02_inventario.md e confronte cada documento com o código real. "
                    "Dê a cada um um veredito: **efetiva** (correta, atual e cobre o seu tema: não será tocada), **parcial** "
                    "(correta em parte; aponte as seções obsoletas ou faltantes) ou **refazer** (obsoleta, contradiz o código ou é "
                    "vaga demais para ser útil). Critérios verificáveis: os caminhos e comandos citados existem e funcionam; os nomes "
                    "batem com o código; o objetivo do sistema está dito; a data é compatível com as mudanças recentes no código. "
                    "Cada veredito leva a evidência (arquivo e trecho). Depois liste as lacunas, isto é, documentos que deveriam existir "
                    "e não existem (veredito **ausente**): no mínimo visão geral e objetivo, arquitetura, como instalar/rodar/testar, "
                    "e, quando o projeto tiver, dicionário de dados, decisões e guia de contribuição. Se o inventário disser que não há "
                    f"documentação, todos os itens são **ausente**. Escreva {trab}/03_classificacao.md com a tabela de vereditos e, no fim, "
                    "o 'Plano de ação': a lista exata de arquivos a criar e a refazer, cada um com o que deve conter. "
                    f"{regras} Siga a \"Regra de pronto\" do BACKLOG.md.")},
        {"id": i[3], "titulo": "Criar e refazer a documentação", "papel": "analista", "depende": i[2], "dificuldade": "alta",
         "toca": f"{docs}, README.md", "doc": f"{docs}/README.md",
         "pronto": "Todo item do plano de ação de 03_classificacao.md foi criado ou refeito; documentos efetivos ficaram intactos.",
         "prompt": (f"Tarefa {i[3]}. Execute o 'Plano de ação' de {trab}/03_classificacao.md. Crie os documentos **ausente** e refaça os "
                    "**refazer** e **parcial** (nas parciais, preserve o que está correto). Não altere os **efetiva**, só acrescente "
                    "link para eles no índice. Baseie-se em "
                    f"{trab}/01_sistema.md e no código. Ao substituir um documento, não deixe a versão antiga ao lado (o git guarda o histórico). "
                    f"Crie ou atualize um índice em {docs}/README.md que liste todos os documentos com uma linha cada, e garanta que o "
                    "README.md da raiz diga o objetivo do sistema e aponte para o índice. "
                    f"{regras} Siga a \"Regra de pronto\" do BACKLOG.md.")},
        {"id": i[4], "titulo": "Verificar a documentação contra o código", "papel": "analista", "depende": i[3], "dificuldade": "media",
         "toca": f"{docs}, {trab}/04_relatorio.md, README.md", "doc": f"{trab}/04_relatorio.md",
         "pronto": f"`{trab}/04_relatorio.md` confirma que a documentação final bate com o código e lista o que sobrou.",
         "prompt": (f"Tarefa {i[4]}. Confira a documentação final contra o código: abra cada caminho citado, siga cada link relativo, "
                    "rode os comandos documentados que forem seguros (instalar, testar, ajuda do CLI) e compare nomes de funções, "
                    "parâmetros e configurações. Corrija direto o que estiver errado. Escreva "
                    f"{trab}/04_relatorio.md com: o veredito final de cada documento (todos devem ficar **efetiva**), o que foi corrigido "
                    "nesta verificação e as pendências que exigem decisão humana (por exemplo objetivo inferido com confiança baixa). "
                    f"{regras} Siga a \"Regra de pronto\" do BACKLOG.md.")},
    ]


def bloco(cfg: Config) -> list[str]:
    L = [TITULO_BLOCO, "",
         "Gerado por `backlog-auto preparo`. Enquanto estas tarefas não estiverem `done`, nenhuma outra é liberada.", ""]
    for t in definicao(cfg):
        L += [f"### {t['id']} · {t['titulo']}", "- **Status:** todo", f"- **Fase:** {FASE}", f"- **Papel:** {t['papel']}",
              f"- **Depende:** {t['depende']}", f"- **Ambiente:** {cfg.ambientes[0]}", f"- **Dificuldade:** {t['dificuldade']}",
              f"- **Toca:** {t['toca']}", f"- **Doc:** {t['doc']}", f"- **Pronto:** {t['pronto']}", "- **Prompt:**",
              "```text", t["prompt"], "```", ""]
    return L


def garantir(cfg: Config) -> bool:
    """Insere o bloco de preparo no backlog se ainda não houver. Retorna True se inseriu."""
    linhas, tarefas = ler(cfg)
    if any(t["fase"] == FASE for t in tarefas.values()):
        return False
    novos = {t["id"] for t in definicao(cfg)} & set(tarefas)
    if novos:
        raise ConfigErro(f"o backlog já usa os ids {sorted(novos)}; mude [preparo] prefixo_id em backlog.toml.")
    pos = next((n for n, l in enumerate(linhas) if l.startswith("## Bloco")), None)
    if pos is None:
        linhas += ["", "---", ""] + bloco(cfg)
    else:
        linhas[pos:pos] = bloco(cfg) + ["---", ""]
    cfg.backlog.write_text("\n".join(linhas).rstrip("\n") + "\n", encoding="utf-8")
    return True


def refazer(cfg: Config) -> int:
    """Volta todas as tarefas de preparo para `todo` (para reclassificar e refazer a documentação)."""
    linhas, tarefas = ler(cfg)
    ids = [t["id"] for t in tarefas.values() if t["fase"] == FASE]
    for tid in ids:
        gravar_status(cfg, linhas, tarefas, tid, "todo")
    return len(ids)


def estado(tarefas: dict) -> tuple[int, int]:
    """(feitas, total) das tarefas de preparo."""
    ts = [t for t in tarefas.values() if t["fase"] == FASE]
    return sum(t["status"] == "done" for t in ts), len(ts)
