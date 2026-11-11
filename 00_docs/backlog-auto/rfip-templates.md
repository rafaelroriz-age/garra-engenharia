# Templates do RFIP: Relatório Fotográfico de Inspeção Predial (BL-12)

O RFIP era o último dos 5 modelos sem template. Ele foi feito pelo método de ADR-13/DEC-25, com origem em planilha, como o RFO: o `.xlsx` original gera o `layout.json`, e dele saem o `.html.j2` (WeasyPrint) e o `.docx` (docxtpl). O `layout.json` segue DEC-35: guarda só geometria e rótulos fixos.

- **Data:** 2026-11-04
- **Branch:** `worktree-backlog-T13` (commit local, sem push)
- **Original medido (só leitura):** `01_output-context/Relatório Fotográfico de Inspeção Predial - CORTINA D'AMPAREZZO - Versão Final.xlsx`. Tem 490,8 MB (`stat`) e sha256 `0465a67899996748…`. O arquivo fica fora do Git e não existe na worktree, por isso foi lido do checkout principal. Nada em `01_output-context/` foi alterado.

## Arquivos criados

| Caminho | Papel |
|---|---|
| `04_backend/app/scripts/rfip_layout_extractor.py` | Extrator em streaming: openpyxl `read_only=True` + `iterparse` do XML da aba. Nenhuma imagem é extraída. |
| `04_backend/app/scripts/build_rfip_templates.py` | CLI que grava o `layout.json` (com `--original`) e gera os dois templates a partir dele, em um único comando. |
| `04_backend/templates/rfip/layout.json` | Especificação versionada (31,8 kB). Não tem carimbo de data, então é determinística. |
| `04_backend/templates/rfip/rfip_template.html.j2` | Template HTML/Jinja2 para o WeasyPrint (ADR-01), 23,3 kB. |
| `04_backend/templates/rfip/rfip_template.docx` | Template DOCX para o docxtpl (ADR-04), 91,0 kB. Embute `templates/assets/logo-garra.png`. |
| `04_backend/tests/test_rfip_templates.py` | 15 testes sobre uma planilha **sintética** criada em `tmp_path`. Não leem `01_output-context/`. |

Não foram tocados: os templates de RFO, LTIP e vistorias, os outros scripts e os documentos de gestão (`00_docs/projeto/*`, `BACKLOG.md`).

Comandos (a partir de `04_backend/`):

```text
python -m app.scripts.build_rfip_templates --original "../01_output-context/Relatório Fotográfico de Inspeção Predial - CORTINA D'AMPAREZZO - Versão Final.xlsx"
python -m app.scripts.build_rfip_templates     # sem o original: regera .j2 e .docx do layout.json versionado
```

## Como o original de 479 MB é lido

O pacote tem 251 membros: 226 imagens em `xl/media/` (490,2 MB) e 3 abas (`GABARITO`, `Rel. Fotográfico`, `Relatório`). O XML das abas soma 3,8 MB. O extrator:

1. Abre o workbook duas vezes, sempre com `openpyxl.load_workbook(read_only=True, keep_links=False)`. A primeira leitura usa `data_only=True`, para pegar os valores em cache da aba fotográfica. A segunda usa `data_only=False`, só para as linhas 1 e 2 de cada aba, e serve para reconhecer o quadro-resumo pelos `PROCV`.
2. Na aba fotográfica, percorre só as **primeiras 120 linhas** (`MAX_LINHAS_PADRAO`). Isso cobre 4 fichas inteiras, 1 título de sistema e 2 quebras de página. A aba tem 11.552 linhas.
3. O modo read_only do openpyxl não expõe larguras e colunas ocultas, alturas de linha, mesclagens, margens, cabeçalho/rodapé nem quebras de página. Esses dados vêm de um `ET.iterparse` do `xl/worksheets/sheet2.xml` em streaming: cada `<row>` é limpo ao terminar, e só as mesclagens que começam nas 120 primeiras linhas são guardadas (de 4.718).
4. Das fotos, lê só as âncoras em `xl/drawings/drawing2.xml` (posição e `cx/cy`). Da logo do cabeçalho, lê só o tamanho declarado em `xl/drawings/vmlDrawing1.vml`. **Nenhum membro `xl/media/*` é aberto**, e o teste `test_extrator_le_em_read_only_sem_tocar_nas_imagens` verifica isso espionando `ZipFile.open`.
5. Antes de abrir qualquer XML, confere o tamanho descompactado contra um teto de 64 MB (proteção contra zip bomb).

### Tempo e memória observados

Medição local (Windows, venv do checkout principal, Python 3.13, openpyxl 3.1.5, arquivo em pasta do OneDrive). O script de medição ficou fora do repositório, em `$CLAUDE_JOB_DIR/tmp/medir.py`, e usa `tracemalloc` + `GetProcessMemoryInfo`.

| Execução | Tempo total de `extrair_layout` | dos quais sha256 do arquivo | Pico `tracemalloc` (Python) | Working set do processo, antes → pico |
|---|---|---|---|---|
| 1 | 2,45 s | ~1,26 s | 9,0 MB | 35,7 → 57,9 MB |
| 2 | 6,68 s | ~1,55 s | 9,0 MB | 35,9 → 58,1 MB |
| CLI (`build_rfip_templates --original`) | 4,06 s / 6,95 s / 7,38 s | — | 9,0 MB | — |

Resumo: o processo tem pico de cerca de 58 MB para um arquivo de 491 MB. Cerca de 22 MB são da extração; o resto é o interpretador com openpyxl carregado. O tempo varia com o cache de disco do OneDrive e é dominado pelo sha256 (leitura integral do arquivo, em blocos de 1 MB) e pelo `iterparse` da aba inteira, que é necessário porque `<pageMargins>`, `<headerFooter>` e `<rowBreaks>` vêm depois de `<sheetData>`.

## Medidas obtidas no original (`templates/rfip/layout.json`)

| Item | Valor medido | De onde vem |
|---|---|---|
| Página | A4 retrato. Margens: esq./dir. 0,6 cm, superior 2,5 cm, inferior 2,0 cm, cabeçalho/rodapé 0 | `<pageMargins>` / `<pageSetup paperSize="9">` |
| Ajuste | "ajustar à largura da página" ativo (`fitToPage`, `fitToHeight=0`) → escala 0,9744 | `<sheetPr><pageSetUpPr>` + soma das colunas |
| Colunas impressas | A 2,0 · D 33,66 · E 3,66 · F 45,0 · H 16,66 · I 5,44 · J 3,11 (caracteres) → 0,36 / 6,08 / 0,67 / 8,12 / 3,02 / 0,98 / 0,57 cm | `<cols>`. B, C e G estão **ocultas**. |
| Tipografia da ficha | Calibri 11 pt (moda). Legenda 12 pt negrito; notas GUT 12 pt; observações 10 pt; "TIPO DE …" 9 pt | estilos das células |
| Fonte padrão (rodapé) | Times New Roman 10 pt | 1ª `<font>` de `styles.xml` |
| Cores | texto `#000000`, fundo de rótulo `#D8D8D8`, e-mail do rodapé `#4F81BD` (tema accent1) | `fill`, `&K04+000`, `theme1.xml` |
| Título de sistema | `7.N. <Sistema>`: Cambria 11 negrito, à esquerda, mesclado C:J (impresso D:J), 14,25 pt + 6 pt de espaço | linha 1 e linha 2 |
| Ficha | **24 linhas por ficha, 2 fichas por página**, legenda `Foto nº` + 2 dígitos | distância entre legendas e `<rowBreaks>` (49, 99, …) |
| Alturas | 14,25 pt em todas as linhas, exceto a do rótulo "TIPO DE …" (24 pt) | `<row ht>` |
| Foto | área mesclada D:G × 15 linhas. Imagem mediana 14,14 × 7,48 cm (5 âncoras) | `drawing2.xml` |
| Campos | SITUAÇÃO, GRAVIDADE, URGÊNCIA, TENDÊNCIA, PONTUAÇÃO, CLASSIFICAÇÃO, TIPO DE ANOMALIA, GRAU DE RISCO, SISTEMA, OBSERVAÇÕES TÉCNICAS, SUBSISTEMA, LOCALIZAÇÃO, com a linha do valor de cada um | coluna auxiliar oculta B |
| Grade da ficha | 29 células: 13 rótulos, 12 valores, título da foto, área da foto, 1 vazia. Inclui mesclagens, bordas, fundo e alinhamento | — |
| Cabeçalho | `&R&G`: logo à direita, 5,63 × 2,82 cm | `oddHeader` + VML |
| Rodapé | centro com 3 linhas (nome em negrito; registro; e-mail em negrito azul + telefone); direita com o nº da página | `oddFooter` |
| Quadro-resumo | aba `Relatório`, 12 colunas (Imagem … OBSERVAÇÕES TÉCNICAS). Cabeçalho Times New Roman 14 negrito, branco sobre `#17365D`. Corpo TNR 10 com bordas `hair`. Margens 1,3/2,0 cm | linha 1 e linha 2 da aba |

### Como rótulo e valor são separados

O original traz o próprio dicionário de dados. A coluna B, oculta, tem em cada linha de valor o texto `<CAMPO> Foto nº NN` (por exemplo, `GRAVIDADE Foto nº 01`). É a chave que a aba `Relatório` usa nos `PROCV`. O extrator usa esse marcador para saber em que linha fica o valor e localiza o rótulo pelo texto. O valor fica na coluna do rótulo ou, quando os dois dividem a linha (notas GUT), na próxima coluna visível. Uma célula só é gravada como **rótulo fixo** quando tem o mesmo texto, na mesma posição, nas 4 fichas amostradas. Qualquer outro texto vira `papel: "descartado"`: a geometria fica e o texto vai embora. No original não houve nenhum descartado.

O rótulo "TIPO DE ANOMALIA" muda conforme a classificação da ficha (a aba de resumo monta a chave com `"TIPO DE "&Classificação`). Ele é gravado como `texto: "TIPO DE"` + `sufixo_campo: "classificacao"`, e o template imprime `TIPO DE {{ classificação|upper }}`.

## Dado pessoal (OWASP A02, DEC-35)

- O rodapé do exemplar traz nome, título profissional, número do CREA, e-mail e telefone do responsável. Cada trecho vira papel + placeholder (`{{ responsavel.nome }}`, `{{ responsavel.titulo_profissional }} - CREA nº {{ responsavel.crea }}`, `{{ responsavel.email }}`, ` / {{ responsavel.telefone }}`). Do exemplar ficam só o negrito e a cor de cada trecho. Texto livre não reconhecido é descartado.
- Valores das fichas (situação, notas, observações, localização como "Piso do Ap. …"), títulos de sistema e o nome do arquivo (que identifica o condomínio) **não entram** no JSON. A procedência fica no sha256.
- Antes de gravar, `garantir_sem_dados_pessoais` (fail-closed) recusa o layout se qualquer string casar com e-mail, telefone, CPF, CNPJ, CEP ou sequência de 6 dígitos ou mais. A mensagem de erro não ecoa o valor.
- Conferência manual: `grep -i` por nome, e-mail, telefone, nº do CREA e nome do condomínio no `layout.json` e no `.html.j2` não achou nada (exit 1). A mesma busca em todos os XML do `.docx` voltou vazia.
- Sem `extraido_em`/`gerado_em` (DEC-35 B). Rodar a extração 3 vezes no original deu JSON idêntico, sha256 do `layout.json` `6e2289cd1ae70b14…` em todas.

## Templates gerados

Os dois geradores consomem a mesma lista, `especificacao_ficha(layout)`: posição, extensão, papel, conteúdo (rótulo ou tag Jinja) e estilo de cada célula. Margens, larguras de coluna (cm, já com a escala), alturas de linha (pt × escala), tamanho da foto e da logo também vêm de funções compartilhadas. O teste de paridade compara a saída dos dois com essa lista. Em seguida altera um rótulo e uma margem no layout e confere que os dois formatos mudam juntos.

- **HTML (`rfip_template.html.j2`):** `@page` A4 com as margens medidas. A logo entra como running element no `@top-right` e o rodapé no `@bottom-center`, com nº de página no `@bottom-right`. Cada sistema vira `h2` (`7.{{ loop.index }}. {{ sistema.nome }}`) e cada ocorrência uma `table.ficha` de 24 linhas × 5 colunas (D, E, F, H, I), com `rowspan`/`colspan`, bordas, fundo e fonte medidos, e `break-inside: avoid`. O quadro-resumo é opcional (`{% if incluir_resumo %}`), numa `@page resumo` com as margens da aba `Relatório`.
- **DOCX (`rfip_template.docx`):** seção A4 (o python-docx nasce em Carta) com as mesmas margens. Logo no cabeçalho, à direita. Rodapé em tabela de 3 colunas (esquerda/centro/direita, como `&L/&C/&R`) com campo `PAGE`. Ficha como tabela com grid fixo, `tblInd` igual à coluna A, linhas `cantSplit`, mesclagens e `tcBorders`. Laços com `{%p for … %}`. A foto é `{{ ocorrencia.foto_docx }}`, uma InlineImage do docxtpl montada pelo pipeline com `tamanho_foto_cm(layout)`. O quadro-resumo usa linhas `{%tr %}` próprias (abertura e fechamento em linhas separadas).
- **Contexto esperado** (mesmo do LTIP): `sistemas[].nome`, `sistemas[].ocorrencias[]` com `seq_numero`, `situacao`, `gut_gravidade/urgencia/tendencia`, `pontuacao_gut`, `classificacao`, `tipo_anomalia`/`tipo_falha`, `grau_risco`, `subsistema`, `localizacao`, `descricao`, `foto_data_uri` (HTML) e `foto_docx` (DOCX). Também `responsavel.*`, `logo_data_uri` e `incluir_resumo`. Campo vazio sai como "—" (DEC-33), com a mesma expressão nos dois formatos.

## Testes

`04_backend/tests/test_rfip_templates.py`, 15 testes. A planilha sintética tem 4 fichas, colunas B/C/G ocultas, coluna auxiliar, fotos ancoradas, quebras de página, rodapé com dados pessoais falsos (nome, CPF, e-mail, telefone, CREA) e aba de resumo. Os testes cobrem:

- leitura em `read_only` em todas as chamadas, com âncoras lidas de `xl/drawings/` e nenhum `xl/media/` aberto;
- página, margens, escala e colunas ocultas; ficha (24 linhas, 2 por página, foto, alturas); separação rótulo/valor e o rótulo dinâmico "TIPO DE";
- rodapé convertido em placeholders, com cor e negrito; `layout.json` sem nenhum dos 11 valores plantados nem o nome do arquivo; verificador fail-closed sem eco do dado; extração determinística;
- original ausente ou corrompido, e planilha sem fichas: os três falham explicitamente;
- paridade HTML × DOCX sobre o mesmo layout; `.j2` compila e renderiza (Jinja2, autoescape, e `HTMLParser` conferindo que nenhum `style` inline ficou truncado); DOCX abre, renderiza e reabre com docxtpl;
- logo limitada à margem superior; artefatos versionados em dia (o `.j2` é idêntico ao que o `layout.json` gera, e o `document.xml`/`footer1.xml` do `.docx` também).

Saídas (rodadas em `04_backend/` com o venv do checkout principal):

```text
$ python -m pytest -q -p no:cacheprovider tests/test_rfip_templates.py tests/test_rfo_templates.py tests/test_ltip_templates.py tests/test_brand_assets.py
56 passed, 1 warning in 24.14s            # 15 RFIP + 41 dos outros templates/marca

$ python -m pytest -q -p no:cacheprovider          # suíte completa
6 failed, 63 passed, 6 warnings, 91 errors in 112.46s
```

**A suíte completa não pôde ser validada, porque o ambiente não tem PostgreSQL.** `localhost:5433` não respondeu (o `docker compose` de `05_infra/` não estava no ar e não foi iniciado). Os 91 erros e 6 falhas estão todos fora do RFIP: `test_auth`, `test_contratos`, `test_edificacoes`, `test_fotos`, `test_gabarito`, `test_models`, `test_ocorrencias_*`, `test_portal_cliente`, `test_rbac_*`, `test_responsaveis`, `test_seguranca`, `test_storage`, `test_visitas`. As mensagens são `ValueError: the greenlet library is required … No module named 'greenlet._greenlet'` (SQLAlchemy async no venv local) e, em `test_storage`, `OSError: [Errno 22] Invalid argument`. Precisam ser reavaliados com o banco no ar.

**ruff:**

```text
$ ruff check --config ../../../../04_backend/ruff.toml app/scripts/rfip_layout_extractor.py app/scripts/build_rfip_templates.py tests/test_rfip_templates.py
All checks passed!

$ ruff check .            # dentro de 04_backend/ da worktree
Found 215 errors.
```

`04_backend/ruff.toml` (BL-26/DEC-31) **não está versionado nesta branch**: só existe, não rastreado, no checkout principal (`git log --all -- 04_backend/ruff.toml` está vazio). Por isso `ruff check .` na worktree resolve `OneDrive - Dynatest Engenharia/pyproject.toml`, fora do repositório (o problema de R-11). Com essa configuração externa sobram 214 erros pré-existentes em arquivos não tocados, mais 1 `I001` em `tests/test_rfip_templates.py`. Esse `I001` existe porque a config externa não reconhece `app` como first-party. A ordem adotada é a do `ruff.toml` do projeto, igual à de `test_ltip_templates.py`, e com ele os 3 arquivos novos passam limpos.

## Limitações e pendências

- **HT-09 (conferência visual):** o WeasyPrint não roda neste Windows, então o PDF não foi renderizado. No container, conferir lado a lado com o original:
  - a logo no `@top-right`: ela foi reduzida para 4,59 × 2,30 cm, para caber na margem superior de 2,5 cm; no Excel ela tem 5,63 × 2,82 cm e a margem de cabeçalho é 0;
  - a quebra a cada 2 fichas: no HTML vem de `break-inside: avoid` mais as alturas medidas, sem quebra forçada;
  - a disponibilidade de Calibri/Cambria ou dos equivalentes métricos (Carlito, Caladea) na imagem.
- **Conversão de largura de coluna:** usa a convenção do Excel `px = trunc(((256·w + trunc(128/7))/256)·7)`, com largura de dígito de 7 px a 96 dpi. É convenção de conversão, não medida do arquivo. Como a planilha usa "ajustar à largura", só as proporções importam e a escala (0,9744) normaliza o total para os 19,8 cm úteis.
- **Escala de impressão:** é aplicada a larguras, alturas e foto, mas não ao corpo das fontes. Isso dá 2,6% de diferença em relação ao Excel, que reduz tudo.
- **Altura das linhas:** é "no mínimo" nos dois formatos (`AT_LEAST` no DOCX, `height` de `tr` no HTML). Assim, observações longas crescem em vez de serem cortadas, como acontece no Excel.
- **Quadro-resumo:** as larguras são proporcionais às medidas e reduzidas à largura da página. No original, a coluna L tem 149 caracteres e não cabe em A4 retrato.
- **Integração:** não existe ainda um `rfip_pipeline` que renderize esses templates (como o `rfo_pipeline`). Montar o contexto, gerar as InlineImage com `tamanho_foto_cm` e expor o endpoint fica para a tarefa de geração do RFIP.

## Decisões propostas (para o fechamento de lote)

- **DEC-XX (proposta): a coluna auxiliar oculta é a fonte do mapa rótulo → valor do RFIP.** O extrator usa os marcadores `<CAMPO> Foto nº NN` da coluna B, a mesma chave dos `PROCV` da aba de resumo, em vez de adivinhar pelo texto. Um rótulo só é "fixo" se repetir igual em todas as fichas amostradas. Se o cliente mudar a planilha e remover essa coluna, a extração falha explicitamente.
- **DEC-XX (proposta): a numeração de páginas do RFIP começa em 1 nos dois formatos.** O exemplar começa na página 30 (`firstPageNumber`) porque é anexo do laudo. Isso fica registrado como `pagina.primeira_pagina_no_original`, mas não é aplicado: numeração contínua com o LTIP é decisão de montagem do pacote, não do modelo.
- **DEC-XX (proposta): o quadro-resumo é opcional (`incluir_resumo`)** e vem depois das fichas, numa página com as margens da aba `Relatório`.

## Para o fechamento de lote (`00_docs/`)

- BL-12: marcar a fatia "templates do RFIP" como entregue em `backlog-tarefas.md`/`backlog-kanban.md`/`status.md`. Com isso, os 5 modelos têm template.
- `decisoes.md`: avaliar as 3 propostas acima.
- `riscos.md`: R-11 voltou a valer nesta branch, porque `ruff.toml` não está versionado. Versioná-lo ou registrar o resíduo. Registrar também que os testes de banco dependem do PostgreSQL e de um `greenlet` funcional no venv local.
- `04_backend/README.md`: citar `python -m app.scripts.build_rfip_templates` junto dos builds de RFO/LTIP.
