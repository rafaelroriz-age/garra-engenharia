---
description: "Ativa o agente de Prototipagem/Backend para derivar os templates HTML/CSS e DOCX do LTIP e do relatório fotográfico por sistema a partir do PDF original do cliente."
---
## Contexto
Tarefa BL-17 do backlog em `00_docs/projeto/backlog-tarefas.md`, Etapa 5. Continuação direta de BL-12/BL-13, que fizeram o mesmo para o RFO a partir da planilha original.
Requisitos/decisões: RF-06, RN-11, RNF-03 (`00_docs/estudo-do-contexto.md`), DEC-25 / ADR-13 (`00_docs/arquitetura.md`).
Origem: `01_output-context/Laudo Técnico de Inspeção Predial ... .pdf` — PDF final de alta fidelidade, fora do Git (`.gitignore`). O cliente não produz este documento em Word; o PDF é a referência de layout.
Base já existente: `app/scripts/rfo_layout_extractor.py` + `app/scripts/build_rfo_templates.py` + `templates/rfo/layout.json` estabelecem o padrão a seguir — extração determinística → artefato intermediário versionado → HTML/Jinja2 (WeasyPrint) e DOCX (docxtpl) derivados da mesma especificação.

## Tarefa
Assuma o papel de **Engenheiro Backend** com foco em prototipagem de documento.

1. Escreva `app/scripts/ltip_layout_extractor.py`, que lê o PDF com `pdfplumber` e **mede** (nunca transcreve à mão): tamanho e orientação da página, margens, família e corpo da fonte de texto, corpo dos títulos e das legendas de figura, hierarquia de títulos numerados (`1.`, `1.1.`, `4.2.1.`), linhas fixas do rodapé, presença de numeração de página, título/logo da capa e a grade do relatório fotográfico.
2. Meça as margens pela **moda** da borda do bloco de texto, não pelo mínimo — uma figura ou nota desalinhada puxaria o extremo e produziria margem irreal. Ignore as páginas com imagem ao medir o corpo do texto, e use somente elas ao medir a legenda de figura.
3. Reconheça a ficha de ocorrência do relatório fotográfico por sistema (RN-11): rótulo `Foto nº NN` e os campos `SITUAÇÃO`, `PRIORIDADE`, `GRAVIDADE`, `URGÊNCIA`, `TENDÊNCIA`, `PONTUAÇÃO`, `CLASSIFICAÇÃO`, `GRAU DE RISCO`, `SISTEMA`, `SUBSISTEMA`, `LOCALIZAÇÃO`, `OBSERVAÇÕES TÉCNICAS`. Conte quantas fichas cabem por página em vez de assumir.
4. Escreva `app/scripts/build_ltip_templates.py` (CLI com `--original`), que grava `templates/ltip/layout.json` e gera dele o `ltip_template.html.j2` e o `ltip_template.docx`. Sem `--original`, regera os templates do `layout.json` já versionado — é assim que o CI funciona sem o arquivo do cliente.
5. No HTML, agrupe as ocorrências por Sistema Predial e, dentro de cada um, itere as fichas (RN-11). Use `@page` com as margens medidas e o rodapé do emitente.
6. Escreva testes que construam um **PDF sintético em memória** com a mesma geometria do original — o CI não tem `01_output-context/`. Cubra: geometria, tipografia, hierarquia de títulos, rodapé, grade fotográfica, arquivo ausente, PDF sem ficha fotográfica, e o balanceamento dos blocos `{% for %}`/`{% endfor %}` no DOCX.

## Saída Esperada
- `templates/ltip/layout.json` versionado + `ltip_template.html.j2` + `ltip_template.docx`
- Extrator e gerador determinísticos, reexecutáveis
- Testes independentes do arquivo do cliente
- Resumo: medidas extraídas do original, comando para regerar e resultado dos testes

## Restrições
- NUNCA versione dado do exemplar do cliente no `layout.json` (OWASP A02): nem observações técnicas, nem nome do condomínio — **inclusive o nome do arquivo original**, que identifica o imóvel inspecionado. Guarde apenas geometria, a marca do emitente e o `sha256` do original.
- NÃO transcreva medidas manualmente: tudo que entrar no `layout.json` precisa ter sido medido por código.
- NÃO faça o extrator assumir a presença do original no repositório — receba o caminho por parâmetro e falhe explicitamente se não existir.
- PDF recebido é apenas lido, nunca executado ou reescrito.
- Leia os arquivos antes de modificá-los.
