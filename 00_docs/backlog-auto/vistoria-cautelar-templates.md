# Templates da Vistoria Cautelar de Recebimento (Tarefa C)

Fatia "Vistoria Cautelar" do modelo incremental de DEC-25 / ADR-13, feita pelo mesmo método do LTIP (BL-17): PDF final do cliente → `layout.json` → `.html.j2` (WeasyPrint) + `.docx` (docxtpl).

- **Data:** 2026-11-04
- **Branch:** `worktree-backlog-T09` (commit local, sem push)
- **Original medido (só leitura):** `01_output-context/Laudo Técnico de Vistoria Cautelar de Recebimento - Reforma New York - V01.pdf`. São 148 páginas, sha256 `918804e1f2e5b0b8…`. O arquivo não foi alterado. Não existe na worktree (fica fora do Git), então foi lido a partir do checkout principal.

## Arquivos criados

| Caminho | Papel |
|---|---|
| `04_backend/app/scripts/vistoria_cautelar_layout_extractor.py` | Extrator (pdfplumber). Reaproveita por import do `ltip_layout_extractor`: `LayoutExtractionError`, `RE_TITULO_NUMERADO`, `RE_LEGENDA_FIGURA`, constantes A4, `_familia`, `_familia_legivel`, `_e_negrito`, `_sha256`. O extrator do LTIP não foi editado. |
| `04_backend/app/scripts/build_vistoria_cautelar_templates.py` | CLI que gera os dois templates só a partir do `layout.json`. Com `--original`, mede o PDF e grava o `layout.json` antes. |
| `04_backend/templates/vistoria_cautelar/layout.json` | Especificação versionada: só geometria e rótulos fixos, 14,7 kB. |
| `04_backend/templates/vistoria_cautelar/vistoria_cautelar_template.html.j2` | Template HTML/Jinja2 para o WeasyPrint (ADR-01). |
| `04_backend/templates/vistoria_cautelar/vistoria_cautelar_template.docx` | Template DOCX para o docxtpl (ADR-04). Embute `templates/assets/logo-garra.png`, a mesma marca usada pelo LTIP. |
| `04_backend/tests/test_vistoria_cautelar_templates.py` | 16 testes sobre um PDF sintético gerado no próprio teste. Não leem `01_output-context/`. |

Não foram tocados: a pasta `templates/ltip/`, a pasta `templates/rfo/`, os outros templates e os documentos de gestão.

## Medidas obtidas no original

| Item | Valor medido |
|---|---|
| Página | A4 retrato (595,5 × 842,25 pt) |
| Margens do texto corrido (moda) | esquerda 3,00 cm · direita 2,03 cm · superior 2,58 cm · inferior 1,95 cm (inferior = até a 1ª linha do rodapé) |
| Corpo | Times New Roman (`TimesNewRomanPSMT`) 12 pt, justificado, entrelinha 15 pt (1,25), 6 pt entre parágrafos |
| Títulos numerados | Times New Roman Bold 14 pt nos níveis 1 a 3. Recuo do nível 1: −0,5 cm em relação ao corpo (moda; nas páginas do relatório fotográfico em diante o recuo é 0) |
| Capa | Arte de fundo sangrada e logo no topo (x 160, 275 × 157 pt). Título "VISTORIA TÉCNICA / CAUTELAR PARA / RECEBIMENTO / DE OBRA" em Montserrat Bold 34,4 pt branco, x 27 pt, topo 188 pt, entrelinha 41 pt. Subtítulo Montserrat Bold 15,4 pt branco. Bloco "RESP. TÉCNICO:" em Montserrat Bold 15 pt `#49567F`, sobre uma faixa de 314 × 138 pt. Data em Open Sans Bold 15,4 pt branco, alinhada à direita |
| Folha de rosto | Título "LAUDO TÉCNICO DE / VISTORIA / CAUTELAR PARA / RECEBIMENTO DE OBRA" em Times Bold 36 pt centralizado. Objeto do laudo em 36 pt e data em 18 pt (ambos placeholders) |
| Sumário | "SUMÁRIO" Times Bold 16 pt. Entradas Times Bold 11 pt com pontilhado em Calibri. Recuo de 0,39 cm por nível (3 níveis) |
| Cabeçalho | Logo à direita em todas as páginas do corpo (144 páginas): x 448,5 pt, topo 12,8 pt, 109,4 × 52,3 pt |
| Rodapé | 3 linhas centralizadas em Times 10 pt (nome; título profissional + CREA; e-mail / telefone em `#0563C1`). Número da página em Calibri 11 pt alinhado à direita (borda em 518 pt). Deslocamento −1: a capa não entra na contagem e a folha de rosto é a página 1 |
| Relatório fotográfico | 2 fotos por página (moda em 121 páginas), 454 × 255 pt, na largura total do texto. Legenda abaixo da foto (afastamento de 8 pt) em Calibri Itálico 9 pt `#44546A`, no formato "Figura N - … Fonte: Autor." |
| Tabelas (só o cabeçalho) | Em 4.2: "ASPECTO TÉCNICO / DESCRIÇÃO DETALHADA" (24,6 % / 75,3 %), cabeçalho `#002060` com texto branco Times Bold 11 pt. Em 10.2: "Item / Localização / Descrição da Pendência / Metodologia Corretiva Indicada" (5,8 / 19,2 / 31,2 / 43,5 %), cabeçalho `#DEEAF6` Times Bold 12 pt |
| Assinatura | Bloco alinhado à direita em Calibri 12 pt: imagem da rubrica (138 × 80 pt) sobre um traço de 286,7 pt, nome em negrito, linha do CREA, 6 linhas de qualificação e "local, data" 85 pt abaixo |
| Cores | texto `#000000` · legenda `#44546A` · contato no rodapé `#0563C1` · título da capa `#FFFFFF` · destaque da capa `#49567F` · cabeçalhos de tabela `#002060` e `#DEEAF6` |

A extração do PDF de 148 páginas leva cerca de 20 s.

## Seções mapeadas (ordem e títulos fixos)

| Nº | Título | Tipo no layout | Subseções fixas |
|---|---|---|---|
| 1 | INTRODUÇÃO | texto | 1.1 Histórico e Contexto da Diligência |
| 2 | CONSIDERAÇÕES PRELIMINARES | texto | 2.1 Geral · 2.2 Pressupostos, ressalvas e fatores limitantes |
| 3 | OBJETIVO | texto | 3.1 Geral · 3.2 Específico |
| 4 | OBJETO | texto | 4.1 Geral · 4.2 Identificação (contém a tabela `identificacao`) |
| 5 | DA REALIZAÇÃO DA INSPEÇÃO | texto | 5.1 Apresentação do Responsável Técnico · 5.2 Datas das Vistorias |
| 6 | METODOLOGIA | texto | 6.1 Classificação da Inspeção quanto ao Nível · 6.2 Critério de classificação técnica dos achados · 6.3 Levantamento de Dados e Documentação · 6.4 Ensaios Técnicos Instrumentais Realizados |
| 7 | DESENVOLVIMENTO DAS ATIVIDADES DA INSPEÇÃO | texto | 7.1 Sistemas Construtivos Inspecionados · 7.2 Dinâmica de Campo e Correções em Tempo Real |
| 8 | RELATÓRIO FOTOGRÁFICO | relatorio_fotografico | laço de figuras |
| 9 | ANÁLISE E CONSIDERAÇÕES TÉCNICAS | por_sistema | laço `sistemas`, cada um com "Constatações" e "Fundamentação Técnica" (7 sistemas no exemplar); depois 9.8 Correlação Técnica entre Origem Provável, Repercussão Funcional e Responsabilidade, renumerada como `9.{{ sistemas\|length + 1 }}` |
| 10 | CONCLUSÃO E CONSIDERAÇÕES FINAIS | texto | 10.1 Parecer Técnico (+ complemento) · 10.2 Plano de Correções Remanescentes (tabela) · 10.3 Prazos e Condicionantes para o Recebimento Definitivo |
| 11 | ENCERRAMENTO | encerramento | texto + bloco de assinatura |
| 12 | REFERÊNCIAS BIBLIOGRÁFICAS | texto | — |

Regras deterministas usadas para separar a estrutura fixa do conteúdo do caso:

- Os títulos são numerados, em negrito e com corpo maior que o do texto. São lidos do corpo do laudo, não do sumário.
- Uma subseção de nível 2 vira laço por sistema quando os mesmos rótulos de nível 3 se repetem sob pais diferentes. Assim, "9.1 Revestimentos de Pintura…" até "9.7 Pendências Executivas…" não são gravados; ficam só os rótulos recorrentes.
- Os demais títulos de nível 3 (4.2.1 Tipologia, 6.4.1 Ensaio Percussivo, 6.4.2 "Projetos Executivo – Proposta da Reforma Térrea" etc.) são conteúdo do caso e não entram no layout.
- Num título como "Parecer Técnico — Recebimento Parcial com Ressalvas", o trecho depois do travessão é o resultado do caso e vira `complementos.parecer_tecnico`.
- Quando uma chave repete ("Geral" em 2.1, 3.1 e 4.1), ela recebe o prefixo do capítulo: `consideracoes_preliminares_geral`, `objetivo_geral`, `objeto_geral`.
- Uma tabela é um cabeçalho preenchido com largura de pelo menos 30 % da página; isso descarta o realce amarelo encontrado numa legenda. A tabela se liga ao título de nível 2 que a precede. Só os rótulos do cabeçalho são lidos; as células do corpo, não.

## Dados pessoais (OWASP A02)

Descartados do exemplar e trocados por placeholders: nome do responsável técnico, CREA e nº IBAPE, e-mail, telefone, nome do condomínio e da construtora, descrição da obra, cidade e datas. Também não entram no layout os parágrafos, as legendas e as células de tabela. O nome do arquivo também não é gravado; guarda-se apenas o sha256.

A função `_garantir_sem_dados_pessoais` varre todo o `layout.json` antes de devolver e falha sem mostrar o valor se encontrar e-mail, telefone, CPF, CEP ou sequência de 6 ou mais dígitos. Cores hexadecimais e o hash ficam fora dessa varredura.

Conferência no `layout.json` real: nenhum destes termos aparece (busca sem diferenciar maiúsculas): roniel, ribeiro, costa, new york, urbânica, gmail, 98250, 1020613386, aparecida, goiânia, luécia, retrofit, ibape, tjgo, natália, junho.

## Placeholders (contrato do contexto de renderização)

Os dois templates usam os mesmos nomes. A única diferença está nas imagens: o HTML recebe data URIs e o DOCX recebe `InlineImage`.

| Placeholder | Onde |
|---|---|
| `{{ responsavel.nome }}` | rodapé, assinatura |
| `{{ responsavel.titulo_profissional }} - CREA nº {{ responsavel.crea }}` | rodapé, assinatura |
| `{{ responsavel.email }} / {{ responsavel.telefone }}` | rodapé |
| `{{ (responsavel.titulo_profissional ~ ' ' ~ responsavel.nome)\|upper }}`, `CREA: {{ responsavel.crea }}` | capa (bloco "RESP. TÉCNICO:") |
| `{% for linha in responsavel.qualificacoes %}` | assinatura |
| `{{ obra.descricao }}` | capa (subtítulo, linha 1), folha de rosto |
| `{{ edificacao.nome }}` | capa (subtítulo, linha 2), `<title>` |
| `{{ data_emissao_mes_ano }}` / `{{ data_emissao_mes_ano\|upper }}` | folha de rosto / capa |
| `{{ local_emissao }}, {{ data_emissao_extenso }}.` | assinatura |
| `conteudo.get('<chave>', [])` | parágrafos de cada capítulo e subseção (chaves de `estrutura.secoes[*].chave` e `subsecoes[*].chave`) |
| `complementos.get('parecer_tecnico')` | complemento do título 10.1 |
| `{% for sistema in sistemas %}` · `{{ sistema.nome }}` · `sistema.get('constatacoes')` · `sistema.get('fundamentacao_tecnica')` | capítulo 9 |
| `{% for figura in figuras %}` · `{{ figura.numero }}` · `{{ figura.legenda }}` · `figura.foto_data_uri` (HTML) / `{{ figura.imagem }}` (DOCX) | capítulo 8 |
| `tabelas.get('identificacao')` → `linha.aspecto_tecnico`, `linha.descricao_detalhada` | 4.2 |
| `tabelas.get('plano_de_correcoes_remanescentes')` → `linha.item`, `linha.localizacao`, `linha.descricao_da_pendencia`, `linha.metodologia_corretiva_indicada` | 10.2 |
| `logo_data_uri`, `capa_fundo_data_uri`, `assinatura_data_uri` (HTML) · `assinatura_imagem` (DOCX) | marca, arte da capa, rubrica (opcionais) |

A renderização foi conferida com um contexto fictício: Jinja2 com `StrictUndefined` no HTML e docxtpl no DOCX. Os dois numeram os sistemas (9.1, 9.2…), renumeram a subseção fixa seguinte (9.3 com 2 sistemas), preenchem a tabela e não deixam tag sem resolver.

## Como PDF e DOCX derivam do mesmo layout

As duas saídas percorrem a mesma lista de blocos, montada por `_plano_de_secoes(layout)`: título, parágrafos, tabela, figuras, sistemas e assinatura. O teste `test_pdf_e_docx_derivam_do_mesmo_layout` confere duas coisas. Primeiro, que os títulos de nível 1 do HTML e os parágrafos "Heading 1" do DOCX são idênticos. Segundo, que uma alteração no layout (título de seção, rótulo de coluna, corpo) aparece nos dois formatos.

No DOCX, a capa fica numa seção própria, sem cabeçalho nem rodapé. O corpo começa com `pgNumType start=1`, reproduzindo o deslocamento −1. O sumário é um campo `TOC \o "1-3"` sobre os estilos de título e é preenchido quando o Word atualiza os campos (F9). No HTML, o sumário usa `target-counter()` e `leader('.')`.

A geração é determinística. O mesmo `layout.json` produz o mesmo `.html.j2` e o mesmo `.docx` byte a byte: o ZIP é regravado com data fixa e as propriedades `dc:`/`dcterms:` são fixadas.

Encontrado no caminho: com o docxtpl carregado no mesmo processo, o prefixo `cp:` é remapeado e as propriedades `cp:lastModifiedBy`/`cp:revision` saem duplicadas no `core.xml`. Por isso o gerador não mexe nelas. O `build_ltip_templates` não usa essas propriedades e não é afetado.

## Comandos e saídas

Todos rodados a partir de `04_backend/`, com o Python do venv do backend (`04_backend/.venv`, Python 3.14.6, pdfplumber 0.11.10):

```text
$ python -m app.scripts.build_vistoria_cautelar_templates --original "<checkout>/01_output-context/Laudo Técnico de Vistoria Cautelar de Recebimento - Reforma New York - V01.pdf"
layout.json atualizado a partir do original informado (sha256 918804e1f2e5b0b8…)
gerados: vistoria_cautelar_template.html.j2, vistoria_cautelar_template.docx

$ python -m app.scripts.build_vistoria_cautelar_templates        # sem --original: regenera a partir do layout.json
gerados: vistoria_cautelar_template.html.j2, vistoria_cautelar_template.docx

$ python -m pytest tests/test_vistoria_cautelar_templates.py -v -rs
... 15 passed, 1 skipped in 7.26s
SKIPPED tests\test_vistoria_cautelar_templates.py: WeasyPrint indisponível neste ambiente
  (no Windows local faltam as bibliotecas Pango/GTK; o teste roda no container do backend): OSError

$ python -m pytest tests/test_ltip_templates.py tests/test_rfo_templates.py tests/test_brand_assets.py -q
41 passed in 9.09s      # não regrediu nada dos templates vizinhos

$ ruff check --isolated app/scripts/vistoria_cautelar_layout_extractor.py app/scripts/build_vistoria_cautelar_templates.py tests/test_vistoria_cautelar_templates.py
All checks passed!

$ ruff check --isolated .
Found 46 errors.        # todos pré-existentes, em arquivos não tocados (F821/F401 em app/models, app/api, app/repositories, alembic; F541 em tests/test_ltip_templates.py)
```

Observação sobre o `ruff`: rodado sem `--isolated` nesta máquina, ele herda um `pyproject.toml` de fora do repositório (`C:\Users\dynatest\OneDrive - Dynatest Engenharia\pyproject.toml`, com regras I/UP/RUF/B) e acusa 226 erros. O CI (`.github/workflows/ci.yml`, `pip install ruff` + `ruff check .`) não tem config no repositório e usa os padrões, que equivalem a `--isolated`. Nos arquivos novos, a config externa só aponta RUF001, pelo travessão "–" usado de propósito nas regex de legenda e título, e RUF005.

O teste do WeasyPrint não rodou: a biblioteca não carrega no Windows (OSError) e não há Docker nesta máquina. A suíte de integração com banco não foi rodada, como pede a tarefa: este arquivo não usa banco.

## Testes (`tests/test_vistoria_cautelar_templates.py`)

O PDF sintético é escrito à mão no teste. Tem capa com arte de fundo, logo e faixa; folha de rosto; sumário com pontilhado; 7 capítulos; 3 páginas de fotos com 5 figuras; 2 sistemas com "Constatações" e "Fundamentação Técnica"; tabela com cabeçalho `#DEEAF6`; e assinatura com rubrica. Nome, CREA, e-mail, telefone, condomínio e cidade fictícios aparecem em capa, rodapé e assinatura.

Os 16 testes cobrem:

1. página, margens, tipografia e parágrafo;
2. cabeçalho e rodapé (geometria e placeholders);
3. capa e folha de rosto (título fixo separado de dado do caso);
4. ordem e títulos das seções, tipos, rótulos por sistema, complemento e chaves únicas;
5. grade e legenda do relatório fotográfico;
6. tabela e assinatura;
7. JSON sem dado pessoal;
8. verificador fail-closed;
9. original ausente;
10. PDF sem fotos;
11. HTML com medidas e placeholders, renderizado com `StrictUndefined`;
12. DOCX com placeholders e blocos `for`/`if` balanceados, renderizado pelo docxtpl;
13. PDF e DOCX derivam do mesmo layout;
14. determinismo byte a byte;
15. artefatos versionados em dia com o `layout.json`;
16. PDF real pelo WeasyPrint (pulado no Windows, com motivo explícito).

## Pendências

- **Conferência visual (HT-09).** Comparar o PDF gerado com o original lado a lado. Pontos a verificar:
  - `@page capa { counter-increment: none }`, que deveria fazer a folha de rosto sair como página 1;
  - posição dos elementos `running()` do cabeçalho e do rodapé;
  - sumário com `target-counter`;
  - recuo de −0,5 cm dos títulos de nível 1.

  Sem WeasyPrint local, nada disso foi visto renderizado.
- **Capa sem a arte do cliente.** A arte de fundo sangrada é do exemplar e não é versionada. O HTML aceita `capa_fundo_data_uri` e, sem ela, usa fundo sólido `#49567F` com a faixa do responsável em branco. No DOCX, o título branco é trocado pela cor de destaque, para não sumir no papel. A arte definitiva da Garra precisa de decisão de design.
- **Fontes.** Montserrat e Open Sans (capa) e Calibri (legenda, rodapé, assinatura) precisam estar instaladas no container do WeasyPrint. Sem elas, o CSS cai para sans-serif genérica.
- **Pipeline de renderização.** É tarefa à parte, como o `ltip_pipeline.py`: montar o contexto acima a partir do banco (responsável, edificação, ocorrências por sistema, fotos, pendências), gerar o PDF com o WeasyPrint e o DOCX com o docxtpl e `InlineImage`.

## Para o fechamento de lote (não editado aqui)

- `00_docs/projeto/backlog-tarefas.md`, `backlog-kanban.md` e `status.md`: a fatia Vistoria Cautelar de ADR-13 tem extrator, `layout.json` e templates entregues, com o pipeline pendente.
- `04_backend/README.md`: citar o comando `python -m app.scripts.build_vistoria_cautelar_templates` e a pasta `templates/vistoria_cautelar/`.
- **Decisão proposta (DEC-XX):** os templates de laudo em PDF guardam no `layout.json` só geometria e rótulos fixos. A identificação do responsável técnico, inclusive no rodapé, vira placeholder, e o `layout.json` passa por um verificador fail-closed de dado pessoal.

  Hoje o `templates/ltip/layout.json` versionado ainda guarda o rodapé literal do emitente (CREA, e-mail e telefone). Recomenda-se uma tarefa para aplicar ao LTIP a mesma regra; esta tarefa não tocou o LTIP.
- **Risco proposto.** O `ruff` local herda um `pyproject.toml` de fora do repositório, o que pode divergir do CI. Sugestão: fixar `[tool.ruff]` em `04_backend/pyproject.toml` ou rodar com `--isolated`. Há também 46 erros de lint pré-existentes nos padrões do CI.
