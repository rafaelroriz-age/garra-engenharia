# Pipeline de renderização da Vistoria Residencial

> Tarefa T12 — DEC-35 / ADR-13. Modelo estrutural: `ltip_pipeline.py` (T05) e `ltip-pipeline.md`.
> Data: 2026-11-04 · Branch: `worktree-backlog-T12` · Papel: backend (`.github/agents/backend.agent.md`).

## Resultado

| Artefato | Caminho |
|---|---|
| Pipeline | `04_backend/app/services/report_generator/vistoria_residencial_pipeline.py` |
| Testes | `04_backend/tests/test_vistoria_residencial_pipeline.py` (9 testes: 8 passam, 1 pulado — PDF) |

API (mesma do LTIP):

- `renderizar_html(contexto, fotos_bytes) -> str`
- `gerar_pdf(contexto, fotos_bytes, destino) -> dict` — chaves `render_html`, `conversao_pdf`, `total`, `n_paginas`, `tamanho_bytes`
- `gerar_docx(contexto, fotos_bytes, destino, *, template_path=None) -> dict` — chaves `montagem_fotos`, `render_e_salvar`, `total`, `tamanho_bytes`
- `normalizar_contexto(contexto) -> dict` (auxiliar pública, como no LTIP; não muta a entrada)

Convenções seguidas: Jinja2 e docxtpl com `autoescape`; fotos como data URI no HTML e `InlineImage` no DOCX; WeasyPrint importado dentro de `gerar_pdf`; o módulo não acessa o MinIO (o chamador entrega `fotos_bytes` por `storage_key`); `KeyError` para foto referenciada e ausente (HTML e DOCX); campo vazio vira `—` (DEC-33). Nada é importado de `rfo_pipeline` nem de `ltip_pipeline`.

## Tabela de campos do contexto

Descobertos lendo `vistoria_residencial_template.html.j2`, o `layout.json` e os placeholders do `word/document.xml` do DOCX.

| Campo | Tipo | Usado em | Se vazio |
|---|---|---|---|
| `imovel.unidade` | str | `<title>`, capa, folha de rosto | `—` |
| `edificacao.nome` | str | capa, folha de rosto | `—` |
| `fiscal.nome` | str | capa (`\|upper`), rodapé, assinatura | `—` |
| `fiscal.crea` | str | capa, rodapé, assinatura | `—` |
| `fiscal.email`, `fiscal.telefone` | str | linha de contato do rodapé | `—` |
| `fiscal.qualificacoes` | lista ou texto (um item por linha) | linhas de qualificação sob a assinatura | lista vazia (sem linhas) |
| `data_emissao` | `date`/`datetime`/str | capa (`\|upper`), folha de rosto, encerramento | hoje, `dd/mm/aaaa` (str é usada como veio) |
| `local_emissao` | str | encerramento (`<local>, <data>.`) | `—` |
| `textos.<chave>` | lista ou texto (um parágrafo por linha) | parágrafos de cada seção fixa | lista vazia (seção só com o título) |
| `fotos[].storage_key` | str | chave em `fotos_bytes` | foto sem imagem; legenda sai |
| `fotos[].numero` | int | `Figura N` | sequencial a partir de 1 |
| `fotos[].legenda` | str | legenda | `—` |
| `fotos[].fonte` | str | `Fonte: …` | `Autor` (fallback do template) |
| `sistemas[].nome` | str | `9.<n>. <nome>` | `—` |
| `sistemas[].constatacoes` | lista ou texto | lista `•` | `['—']` |
| `sistemas[].fundamentacao_tecnica` | lista ou texto | parágrafos | `['—']` |
| `logo_data_uri` | str | cabeçalho e capa (HTML) | padrão: `templates/assets/logo-garra.svg` |
| `capa_fundo_data_uri`, `assinatura_data_uri` | str (HTML) | foto de fundo da capa; rubrica | omitidos (a capa usa a cor `#0c5276`) |

Chaves de `textos` (`chave_secao("4.2.1.")` → `s4_2_1`), todas sempre presentes após a normalização:
`s1 s1_1 · s2 s2_1 s2_2 · s3 s3_1 s3_2 · s4 s4_1 s4_2 s4_2_1 s4_2_2 s4_2_3 s4_2_4 s4_2_4_1 s4_2_4_2 · s5 s5_1 s5_2 · s6 s6_1 s6_2 s6_3 · s7 s7_1 · s8 · s9 · s10 · s11 · s12`.
A constante `TEXTOS_CHAVES` do módulo as lista; um teste a confronta com as chaves `textos.*` do `.html.j2` (se o template mudar, o teste acusa).

Diferenças relevantes em relação ao LTIP:

- O relatório fotográfico (cap. 8) é uma lista plana `fotos`, não uma foto por ocorrência. No DOCX a foto entra em `foto.imagem` (160 mm = largura útil A4); no HTML em `foto.data_uri`.
- O cap. 9 é por `sistemas` com listas livres — não há agrupamento por `Ocorrencia`/GUT. Quem chama monta `sistemas`, `fotos` e `textos` (ver proposta 1).
- `data_emissao` só é formatada quando vem como `date`/`datetime`; uma string ISO passa como está (idêntico ao LTIP). O chamador deve entregar `date`.

## Comandos e saídas

Rodados a partir de `04_backend/`, com o venv do checkout principal (o worktree não tem `.venv`) e o `ruff` global do anaconda (o venv não o instala).

```text
$ python -m pytest tests/test_vistoria_residencial_pipeline.py tests/test_ltip_pipeline.py tests/test_vistoria_residencial_templates.py -q -rs
39 passed, 3 skipped, 1 warning in 21.82s
SKIPPED  test_vistoria_residencial_pipeline.py:169  WeasyPrint indisponível (OSError): só carrega no container
SKIPPED  test_ltip_pipeline.py:265                  idem
SKIPPED  test_vistoria_residencial_templates.py:552 idem

$ python -m ruff check app/services/report_generator/vistoria_residencial_pipeline.py tests/test_vistoria_residencial_pipeline.py
All checks passed!

$ python -m ruff check .
Found 12 errors.   # nenhum nos dois arquivos novos; os demais já existiam

$ python -m pytest        # suíte completa, sem PostgreSQL
6 failed, 102 passed, 4 skipped, 104 errors in 96.52s
```

O que **não** rodou, e por quê:

- **PDF (WeasyPrint):** o teste `test_pdf_gerado_com_weasyprint` foi pulado, e o PDF desta tarefa **nunca foi renderizado**. Este Windows não tem GTK/Pango, e o Docker não está instalado nesta máquina (`docker: command not found`), então não foi possível rodar no container de `05_infra/`. Só o HTML (Jinja2) e o DOCX foram exercitados.
- **PostgreSQL (localhost:5433):** não estava no ar. Na suíte completa, os 104 erros (`OSError`/greenlet, em `test_storage.py`, `test_visitas.py` etc.) e as 6 falhas (`test_auth.py`, `test_edificacoes.py`, `test_responsaveis.py`, `test_seguranca.py`) estão em arquivos que dependem do banco/da aplicação. Não diagnostiquei cada falha individualmente; nenhum desses arquivos foi tocado por esta tarefa. Os testes do pipeline não usam banco.
- `npm run lint`/`build`: não aplicável (só backend).

Nota de ambiente: o worktree do job nasceu de um commit sem T05/T10 (`templates/vistoria_residencial/` e `ltip_pipeline.py` não existiam). Foi feito `git merge main` na branch do worktree (commit de merge local) antes de trabalhar.

## Propostas (não aplicadas)

1. **Montagem do contexto.** Falta quem converta o modelo (`Inspecao`, `Ocorrencia`, `Foto`, `Responsavel`) no contexto acima: `textos` por seção, `sistemas` com `constatacoes`/`fundamentacao_tecnica` e `fotos` com `storage_key`. Não existem no modelo `imovel.unidade`, `fiscal.qualificacoes` e `local_emissao`. Sugiro uma tarefa à parte, como foi o BL-17 para o LTIP.
2. **Módulo comum.** `_em_paragrafos`, `_logo_data_uri`, `_formatar_data` e `_mime` já estão duplicados em `ltip_pipeline.py` e aqui (a extração está sugerida em `ltip-pipeline.md`). Com a Vistoria Residencial são três pipelines com o mesmo trecho.
3. **`data_emissao` como string.** Aceitar string ISO (`aaaa-mm-dd`) e formatá-la, em todos os pipelines, evitaria o passo de conversão no chamador.
4. **Defeito possível no template DOCX** (não alterado): `fiscal.email` e `fiscal.telefone` não aparecem em `word/document.xml`; podem estar só no rodapé do DOCX. Conferir visualmente (HT-09) se o rodapé do DOCX traz os dois.
5. **Conferência visual do PDF** no container, com os pontos já listados em `vistoria-residencial-templates.md` (numeração de páginas, capa, fontes, 2 fotos por página).

## Para o fechamento de lote (00_docs/projeto/)

- `backlog-tarefas.md`/`status.md`: T12 entregue (pipeline + 9 testes), PDF pendente de conferência no container.
- `riscos.md`: o PDF da Vistoria Residencial segue sem renderização real fora do container (mesmo risco do LTIP).
- `decisoes.md`: nenhuma decisão nova; o pipeline segue DEC-33 (traço), DEC-35 e ADR-13.
