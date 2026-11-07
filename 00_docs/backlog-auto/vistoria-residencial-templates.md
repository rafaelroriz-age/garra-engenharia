# Templates da Vistoria Residencial derivados do PDF original

> Tarefa D — fatia "Vistoria Residencial" do modelo incremental de DEC-25 / ADR-13, pelo mesmo método do LTIP (BL-17).
> Data: 2026-11-04 · Branch: `worktree-backlog-T10` · Papel: backend (`.github/agents/backend.agent.md`).

## Resultado

| Artefato | Caminho | Observação |
|---|---|---|
| Extrator (pdfplumber) | `04_backend/app/scripts/vistoria_residencial_layout_extractor.py` | Reaproveita, **por import e sem editar**, funções de `ltip_layout_extractor.py`: `_extrair_capa`, `_extrair_hierarquia_de_titulos`, `_familia`, `_familia_legivel`, `_e_negrito`, `_sha256`, `LayoutExtractionError` e as constantes A4/`PONTO_EM_CM`/regex de título e de legenda. Nada importado da Vistoria Cautelar. |
| Gerador | `04_backend/app/scripts/build_vistoria_residencial_templates.py` | Gera os dois templates **só** a partir do `layout.json` e dos assets de marca (`templates/assets/logo-garra.png` no DOCX, `marca.json` para a cor de fundo da capa). Determinístico: o HTML sai igual byte a byte e o XML do DOCX também (as propriedades do DOCX usam data fixa). |
| Layout medido | `04_backend/templates/vistoria_residencial/layout.json` | 7,9 kB. Só geometria e rótulos fixos. Não tem `gerado_em`, ao contrário do LTIP, para que a regeneração não mude o arquivo. |
| Template PDF | `04_backend/templates/vistoria_residencial/vistoria_residencial_template.html.j2` | WeasyPrint (ADR-01), 10,9 kB. |
| Template DOCX | `04_backend/templates/vistoria_residencial/vistoria_residencial_template.docx` | docxtpl (ADR-04), 90,7 kB. |
| Testes | `04_backend/tests/test_vistoria_residencial_templates.py` | 21 testes sobre um PDF sintético gerado no próprio teste (texto, imagens e cores). Nenhum lê `01_output-context/`. |

Nada foi alterado em `01_output-context/`. O original só foi **lido**, a partir do checkout principal, para gerar o `layout.json`. As pastas `templates/ltip/`, `templates/rfo/` e a da Vistoria Cautelar não foram tocadas.

## Medidas obtidas do original

Original: `Laudo Técnico de Vistoria de Imóvel Residencial - Ap. 1404.pdf`, sha256 `c1ffc311b9cc0546…` (completo no `layout.json`), 91 páginas. O nome do arquivo identifica a unidade e por isso **não** é versionado.

| Item | Medida |
|---|---|
| Página | A4 retrato (595,5 × 842,25 pt). 4 páginas fora do A4 (A3 paisagem: enxertos de projeto do §6.3), excluídas das medidas |
| Margens | esquerda 3,00 cm · direita 1,99 cm · superior 2,58 cm · inferior 1,94 cm. Moda das bordas das linhas de corpo: os títulos de capítulo às vezes recuam ~1 cm, e a margem mínima da página daria um valor irreal |
| Corpo | Times New Roman (`TimesNewRomanPSMT`) 12 pt, cor `#000000` |
| Títulos | nível 1 e nível 2 em negrito 14 pt · níveis 3 e 4 em negrito 12 pt |
| Legenda de figura | Calibri itálico 9 pt, cor `#44546A`, abaixo da foto, formato `Figura N - <descrição>. Fonte: Autor.` |
| Grade de fotos | 2 fotos por página, 1 coluna, 16,00 × 9,00 cm |
| Cabeçalho | logo à direita em 83 páginas internas: x 448,5 pt, topo 12,8 pt, 109,4 × 52,3 pt |
| Rodapé | 3 linhas centralizadas em Times New Roman 10 pt (nome / registro CREA / contato), contato em `#0563C1` (link), topo em 787 pt; numeração à direita em Calibri 11 pt |
| Capa | foto de fundo sangrada; logo à direita (222,8 × 126,8 pt); título em Montserrat Bold 34,4 pt, branco (`#FFFFFF`), em 3 linhas; identificação em 15,4 pt; bloco do responsável em 15,0 pt com o rótulo fixo `RESP. TÉCNICO:` |
| Folha de rosto | título em bloco de 5 linhas em Times New Roman Bold 36 pt; identificação do imóvel com 3 linhas no exemplar, no mesmo corpo; data em 18 pt |
| Análise por sistema | subtítulos fixos repetidos em cada sistema, com o marcador `➢`: **Constatações** (seguido de lista com `•`) e **Fundamentação Técnica** (seguido de parágrafos) |
| Assinatura | no capítulo 11, alinhada à direita, Calibri 12 pt: rubrica (137,7 × 79,7 pt) sobre a linha, nome em negrito, 7 linhas de qualificação no exemplar, local e data |

## Seções mapeadas (títulos fixos, na ordem do laudo)

| Nº | Título | Tipo no template |
|---|---|---|
| 1. | INTRODUÇÃO · 1.1. Histórico | texto |
| 2. | CONSIDERAÇÕES PRELIMINARES · 2.1. Geral · 2.2. Pressupostos, ressalvas e fatores limitantes | texto |
| 3. | OBJETIVO · 3.1. Geral · 3.2. Específico | texto |
| 4. | OBJETO · 4.1. Geral · 4.2. Identificação · 4.2.1. Tipologia · 4.2.2. Caracterização · 4.2.3. Localização · 4.2.4. Descrição Qualitativa · 4.2.4.1. Região · 4.2.4.2. Valorização Imobiliária | texto |
| 5. | DA REALIZAÇÃO DA INSPEÇÃO · 5.1. Responsável Técnico · 5.2. Datas das Vistorias | texto |
| 6. | METODOLOGIA · 6.1. Classificação da Inspeção quanto ao Nível · 6.2. Critério de classificação técnica dos achados · 6.3. Levantamento de Dados e Documentação | texto |
| 7. | DESENVOLVIMENTO DAS ATIVIDADES DA INSPEÇÃO · 7.1. Sistemas Construtivos Inspecionados | texto |
| 8. | RELATÓRIO FOTOGRÁFICO | `fotografico`: laço `{% for foto in fotos %}` |
| 9. | ANÁLISE E CONSIDERAÇÕES TÉCNICAS | `por_sistema`: laço `{% for sistema in sistemas %}`, numerado `9.{{ loop.index }}.` |
| 10. | CONCLUSÃO E CONSIDERAÇÕES FINAIS | texto |
| 11. | ENCERRAMENTO | texto + bloco de assinatura |
| 12. | REFERÊNCIAS BIBLIOGRÁFICAS | texto |

As subseções do capítulo 9 do exemplar (9.1 Estrutura e Laje … 9.8) são conteúdo do caso (os sistemas inspecionados) e foram descartadas: viram o laço por sistema. O subtítulo 6.3.1 do exemplar ("Projetos do <unidade>", negrito 14 pt) está na página 15, que é A3 paisagem, como as páginas 15 a 18 com os enxertos de projeto. Essas páginas ficam fora das medidas, então ele não entrou, e de todo modo é título do caso. Se entrasse, `anonimizar()` o reduziria a `Projetos do {{ imovel.unidade }}`, comportamento coberto por teste.

## Privacidade (OWASP A02)

- Rodapé, capa, folha de rosto e assinatura **nunca** copiam texto do exemplar. O extrator classifica cada linha por papel (nome / registro / contato) e grava só o placeholder.
- Os únicos textos copiados são os títulos de seção, o título da capa e o da folha de rosto, e o rótulo `RESP. TÉCNICO:`. Todos passam por `anonimizar()`, que troca e-mail, CPF/CNPJ, CREA, telefone, CEP e número de unidade por placeholder.
- Guarda final: `verificar_sem_dados_pessoais()` recusa gravar o layout se algum desses padrões sobrou (teste `test_guarda_final_recusa_layout_com_dado_pessoal`).
- Conferido no artefato gerado a partir do original: nome do engenheiro, número do CREA, e-mail, telefone, número do apartamento e nome do empreendimento não aparecem no `layout.json`, no `.html.j2` nem no `word/document.xml` do DOCX. Fiz a busca pelos valores reais do exemplar fora do repositório e eles **não** foram escritos em nenhum teste. Os testes usam dados fictícios (`Fulano de Tal`, `Ap. 101`…).

## Placeholders (contexto esperado pelos dois templates)

| Variável | Uso |
|---|---|
| `fiscal.nome`, `fiscal.crea` | capa, rodapé e assinatura |
| `fiscal.email`, `fiscal.telefone` | linha de contato do rodapé |
| `fiscal.qualificacoes` | lista de linhas de qualificação no bloco de assinatura |
| `imovel.unidade` | capa, folha de rosto e `<title>` (não existe no modelo: o pipeline deve fornecer) |
| `edificacao.nome` | capa e folha de rosto |
| `data_emissao`, `local_emissao` | capa, folha de rosto e local/data do encerramento |
| `textos.<chave>` | parágrafos de cada seção fixa; chave = `chave_secao("4.2.1.")` → `s4_2_1` |
| `fotos` | `{numero, legenda, fonte, data_uri}` no HTML / `{…, imagem: InlineImage}` no DOCX; `fonte` vazio vira `Autor` |
| `sistemas` | `{nome, constatacoes: [...], fundamentacao_tecnica: [...]}`; as chaves vêm de `analise_por_sistema.subtitulos[].chave` |
| `logo_data_uri`, `capa_fundo_data_uri`, `assinatura_data_uri` | imagens opcionais do HTML |

Placeholders gerados por `anonimizar()` caso apareçam em títulos: `{{ contratante.cpf_cnpj }}` e `{{ edificacao.cep }}`. Hoje nenhum título do exemplar os contém.

## Comandos e saídas

Todos rodados a partir de `04_backend/`, com o venv do checkout principal (o worktree não tem `.venv`).

```text
$ python -m app.scripts.build_vistoria_residencial_templates --original "<01_output-context>/Laudo Técnico de Vistoria de Imóvel Residencial - Ap. 1404.pdf"
layout.json atualizado a partir do original informado (sha256 c1ffc311b9cc0546…)
gerados: vistoria_residencial_template.html.j2, vistoria_residencial_template.docx

$ pytest tests/test_vistoria_residencial_templates.py tests/test_ltip_templates.py -v -rs
31 passed, 1 skipped in 23.54s
SKIPPED [1] tests\test_vistoria_residencial_templates.py:551: WeasyPrint indisponível neste ambiente
  (não roda no Windows local, só no container): [Errno 22] Invalid argument
```

Os 21 testes novos cobrem: geometria e margens; tipografia e cores; logo do cabeçalho; rodapé em placeholder e numeração; ordem e tipo das seções; grade e legenda das fotos; subtítulos da análise por sistema; bloco de assinatura; capa e folha de rosto; ausência de dado pessoal; `anonimizar()`; guarda final; original ausente; PDF sem fotos; placeholders no HTML; placeholders e blocos `for`/`endfor` balanceados no DOCX; **PDF e DOCX derivados do mesmo layout** (todo título, subtítulo e linha de rodapé aparece nos dois, as margens do DOCX batem com o layout, e mudar o layout muda os dois formatos); determinismo; renderização com contexto de exemplo (Jinja2 e docxtpl); PDF via WeasyPrint (skip local); artefatos versionados em dia com o `layout.json`. Os 11 testes do LTIP continuam passando com o import.

**Ruff:**

```text
$ ruff check --config <checkout principal>/04_backend/ruff.toml <3 arquivos novos>
All checks passed!

$ ruff check .            # sem ruff.toml nesta branch
Found 215 errors.         # todos já existiam; dos arquivos novos, só 1 I001 no teste (ver abaixo)
```

O `04_backend/ruff.toml` do BL-26/DEC-31 **não está nesta branch** (existe só no checkout principal). Sem ele, o `ruff check .` puro resolve um `pyproject.toml` de fora do repositório (R-11). Essa config trata `app` como pacote de terceiros e acusa `I001` em qualquer teste que importe `app.*` depois de `pytest`, inclusive `test_ltip_templates.py` e `test_rfo_templates.py`. Com a config do projeto, os três arquivos novos passam limpos. Não copiei o `ruff.toml` para cá porque ele pertence ao BL-26.

O banco não foi necessário: estes testes não usam PostgreSQL, e a suíte de integração não foi rodada, como pedia a tarefa.

## Pendências

1. **Conferência visual (HT-09).** O PDF renderizado só pode ser comparado com o original no container, onde o WeasyPrint roda. Pontos a conferir:
   - a numeração de páginas: no original a folha de rosto é a página 1 e a capa não conta; no CSS atual, `counter(page)` conta a capa;
   - as posições absolutas da capa (título, identificação, responsável), estimadas a partir das coordenadas medidas;
   - a disponibilidade das fontes Montserrat, Calibri e Times New Roman no container, que do contrário cai nos fallbacks `Open Sans`/`DejaVu Serif`;
   - a quebra de 2 fotos por página.
2. **Pipeline de renderização**, tarefa à parte, como o `ltip_pipeline.py` previsto (hoje só existe `app/services/report_generator/rfo_pipeline.py`). Ele precisa montar o contexto da tabela acima: `textos` indexado por `chave_secao()`, fotos com `data_uri` (HTML) e `InlineImage` (DOCX), `sistemas`, e `imovel.unidade`, `fiscal.qualificacoes` e `local_emissao`, que não existem nos modelos atuais. `Responsavel` tem `nome`, `crea`, `email` e `telefone`.
3. **Capa do DOCX** sem a foto de fundo sangrada. Por isso o texto usa a cor de corpo (preto), e não o branco medido sobre a foto, que ficaria invisível no papel. A capa do HTML usa a foto (`capa_fundo_data_uri`) ou, sem ela, a cor escura da marca (`#0c5276`, `marca.json`).
4. **Páginas A3 paisagem** (p. 15–18 do exemplar, enxertos de projeto do §6.3, com o subtítulo 6.3.1) não têm template próprio: no template atual, o §6.3 só tem o laço de parágrafos. Se o cliente quiser os enxertos, é preciso uma seção com `@page` A3 paisagem.
5. A linha de registro do rodapé fixa o título profissional `Eng. Civil` (`Eng. Civil - CREA nº {{ fiscal.crea }}`), como no exemplar. Se outro profissional emitir o laudo, o pipeline deve expor um campo de título.

## Decisões propostas (para o fechamento de lote, não aplicadas em `decisoes.md`)

- **Proposta A (privacidade dos layouts de PDF):** nos `layout.json` derivados de PDF, o rodapé guarda só papéis e placeholders, nunca o texto do exemplar. O `templates/ltip/layout.json` versionado hoje guarda as linhas do rodapé do emitente, com e-mail e telefone pessoal do engenheiro, por decisão de BL-17 ("marca do emitente"). Sugiro alinhar o LTIP a esta regra numa tarefa própria e registrar em `riscos.md` como resíduo de A02, se não for alinhado. Não toquei na pasta do LTIP.
- **Proposta B (determinismo):** o `layout.json` da vistoria não grava `gerado_em`, para que regerar a partir do mesmo original não produza diff. O sha256 do original já basta para rastrear a procedência.
