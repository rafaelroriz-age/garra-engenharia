# V1-05 · Emissão da Vistoria Residencial a partir do banco (T61)

Papel: Engenheiro Backend. Data: 2026-11-11. Branch: `worktree-backlog-T61`.
Status: **implementado e testado** (PostgreSQL e WeasyPrint do 05_infra). `POST /api/v1/inspecoes/{id}/relatorios/VISTORIA_RESIDENCIAL` emite PDF e DOCX.

> **Nota de ambiente:** o worktree nasceu de `14ead2f` (2026-10-28), sem V1-01/V1-02 nem o pipeline da Residencial. A branch não tinha commits próprios e `14ead2f` é ancestral de `main`, então fiz `git merge --ff-only main` (até `16fc3bc`) antes de começar. Nada foi reescrito.

## O que mudou

| Arquivo | Mudança |
|---|---|
| `04_backend/app/services/report_generator/vistoria_residencial_contexto.py` (novo) | `TIPO_VISTORIA_RESIDENCIAL`, `montar_contexto_vistoria_residencial(db, inspecao_id)`, `validar_contexto_vistoria_residencial(ctx)`, `extrair_fotos_vistoria_residencial(ctx)`, `anexar_imagens_do_storage(ctx, storage)`; geradores puros `texto_tipologia`, `texto_caracterizacao`, `texto_localizacao`, `texto_responsavel`, `texto_datas_vistorias`, `cidade_do_endereco` e `hoje()`. As consultas estão no próprio arquivo (`contexto_comum.py` não existe na `main`, então não o criei). |
| `04_backend/app/services/relatorio_service.py` | `Emissor` ganhou o campo opcional `anexar_do_storage: Callable[[dict, StorageClient], None] \| None = None`. `emitir_relatorio` chama esse campo (em thread) depois da validação e antes de baixar as fotos. O tipo `VISTORIA_RESIDENCIAL` fica registrado no import do módulo, como o RFO. Os outros emissores continuam iguais (o padrão é `None`). |
| `04_backend/tests/test_vistoria_residencial_contexto.py` (novo) | 13 funções / 17 casos: 5 funções de unidade (9 casos com o parametrize) e 8 com banco. |

Não houve migration, variável de ambiente nem mudança de template ou pipeline. `01_output-context/` não foi tocado.

## Mapeamento (banco → contexto do `vistoria_residencial_pipeline`)

| Contexto | Origem | Padrão / observação |
|---|---|---|
| `imovel.unidade` | `relatorio_conteudos.dados.unidade` (tipo `VISTORIA_RESIDENCIAL`) | `'—'`. A validação trata `'—'` como ausente, o que dá 422. |
| `edificacao.{nome, endereco, cep, tipologia, sistema_construtivo, descricao_pavimentos, area_total_m2}` | `contrato.edificacao` | o pipeline preenche com `'—'` |
| `fiscal.{nome, crea, email, telefone, titulo_profissional, qualificacoes}` | `contrato.fiscal` (`Responsavel`, campos de V1-01) | `qualificacoes`: lista sem itens vazios |
| `data_emissao` | `dados.data_emissao` (ISO) | `hoje()` no fuso `America/Sao_Paulo` (ver Achados 1) |
| `local_emissao` | `dados.local_emissao` | `cidade_do_endereco(edificacao.endereco)` → `"Goiânia-GO"`; sem padrão `Cidade - UF`/`Cidade/UF` no fim do endereço → `'—'` |
| `textos.*` | padrões de `textos_padrao/vistoria_residencial.json` (com `{edificacao_nome}`/`{edificacao_endereco}`), depois os gerados e por fim `dados.textos` | a prioridade é: o salvo, depois o gerado, depois o padrão (`deep_merge`); o gerado só entra se não for vazio |
| `textos.s4_2_1` | `edificacao.tipologia` | `"Tipologia da edificação: X."` |
| `textos.s4_2_2` | `sistema_construtivo`, `descricao_pavimentos`, `area_total_m2` | um parágrafo por campo; área em pt-BR (`15.000 m²`, `12.345,50 m²`) |
| `textos.s4_2_3` | `endereco`, `cep` | `"Endereço: …."` e `"CEP: …."` (substitui o padrão `Endereço: {edificacao_endereco}.`) |
| `textos.s5_1` | fiscal | `"A inspeção foi realizada pelo responsável técnico Nome, Título, CREA nº X."` e `"Contato: email / telefone."` |
| `textos.s5_2` | `dados.datas_vistorias` | `"A vistoria foi realizada em dd/mm/aaaa."` ou `"As vistorias foram realizadas em a, b e c."` (ordenadas, sem repetição) |
| `fotos[]` | fotos das ocorrências (ocorrências por `seq_numero`, fotos por `ordem`, com nulos no fim) | `numero` de 1 a N; `legenda = legenda_para_relatorio(foto)` (só `legenda`, **nunca** `legenda_ia_sugerida`); `fonte = 'Autor'`; a foto sem legenda aprovada **continua** no laudo, com `'—'` na legenda |
| `sistemas[]` | ocorrências agrupadas por `sistema_id`, ordenadas por `SistemaPredial.ordem` e nome | `constatacoes`: `"Localização: descrição (Figuras n, m)."`; `fundamentacao_tecnica`: `dados.fundamentacao_tecnica[sistema_id]` |
| `assinatura_data_uri` | `fiscal.assinatura_storage_key` → bytes do storage → data URI (sem otimizar, para preservar a transparência do PNG) | `None` + aviso |
| `capa_fundo_data_uri` | último item de `edificacao.documentos_tecnicos.itens` com `tipo` `capa` ou `fachada` (sem diferenciar maiúsculas) → JPEG de até 1200 px | `None` + aviso (ver Decisões propostas 2) |
| `avisos` | falhas das imagens opcionais (storage fora do ar, chave inexistente, arquivo que não é imagem) | também vão para o log (`logger.warning`); a emissão **não** falha |

Validação (`422 vistoria_residencial-contexto-incompleto`, um item em `errors[]` por campo): `fiscal.nome`, `fiscal.crea` e `imovel.unidade`. A checagem de inspeção inexistente (404) e de tipo divergente (409) fica com `emitir_relatorio`; o `montar_contexto` só repete o 404.

## Testes e comandos

Ambiente: `garra-postgres`/`garra-minio` no ar (rede `garra-net`). Docker em `C:\Program Files\Docker\Docker\resources\bin`. O Python local do Windows não roda a suíte (WeasyPrint sem GTK; `bcrypt`/`passlib`, ver `v1-fundacao-dados.md`), então tudo rodou no container.

Imagem: a partir de `05_infra`, `docker compose --env-file <checkout principal>/05_infra/.env build backend` (o worktree não tem `.env`, e sem ele o compose recusa a interpolação de `MINIO_ROOT_USER`) → `05_infra-backend` reconstruída com `pytest 9.2.0`.

Banco descartável (o banco de dev não foi tocado): `CREATE DATABASE garra_tmp_v105` no `garra-postgres` e depois `alembic upgrade head` no container → `a9c3e5f7b1d2 (head)`.

Comando base (o `04_backend` do worktree montado em `/app`):

```
docker compose --env-file <.env> run --rm --no-deps -e POSTGRES_DB=garra_tmp_v105 -v <worktree>/04_backend:/app backend sh -c '...'
```

### pytest

```
python -m pytest tests/test_vistoria_residencial_contexto.py tests/test_vistoria_residencial_pipeline.py tests/test_relatorios_rfo_api.py -q
→ 39 passed in 22.95s
   tests/test_vistoria_residencial_contexto.py : 17 passed
   tests/test_vistoria_residencial_pipeline.py :  9 passed   (inclui test_pdf_gerado_com_weasyprint, com WeasyPrint real)
   tests/test_relatorios_rfo_api.py            : 13 passed
```

Vizinhos afetados pela mudança em `relatorio_service.py`:

```
python -m pytest tests/test_relatorios_emissao_generica.py tests/test_relatorio_conteudo.py tests/test_rfo_contexto.py tests/test_vistoria_residencial_templates.py -q
→ 71 passed in 40.01s
```

O que `test_vistoria_residencial_contexto.py` cobre:
- emissor registrado (pipeline, funções e `extrair_fotos` sem chaves nulas);
- `cidade_do_endereco` (hífen, barra, travessão curto e endereço sem UF);
- textos gerados (tipologia, caracterização com área em pt-BR, localização, responsável, datas);
- validação por campo;
- imagens opcionais: PNG vira data URI; chave inexistente, arquivo que não é imagem e storage que lança `RuntimeError` só geram aviso;
- com banco: o contexto real passa no `normalizar_contexto` e o HTML renderizado não tem `None`, `{{` nem `{%` e escapa `&`/`<`;
- `s4_2_x` gerados da edificação, e o texto salvo prevalece sobre o gerado;
- a legenda não aprovada (`legenda=None`, `legenda_ia_sugerida` em `rascunho`) não entra no contexto bruto nem no normalizado;
- sem conteúdo salvo, valem os padrões e a validação devolve `["imovel.unidade"]`;
- `POST .../relatorios/VISTORIA_RESIDENCIAL`:
  - com renderizador e storage fakes cria `V01` em `relatorios/{id}/vistoria_residencial-v01.{pdf,docx}`, com a assinatura como data URI e a capa ausente como aviso (201);
  - sem unidade dá 422 `errors[].field == ["imovel.unidade"]`, e o renderizador não é chamado;
  - sem CREA dá 422 `["fiscal.crea"]`.

A suíte completa (`pytest` sem argumentos) **não** foi rodada.

### ruff (0.17.4, `ruff.toml` do backend)

- `ruff check app/services/relatorio_service.py app/services/report_generator/vistoria_residencial_contexto.py tests/test_vistoria_residencial_contexto.py` → `All checks passed!`
- `ruff check .` → `Found 10 errors.`, todos em arquivos não tocados e os mesmos já registrados em `v1-fundacao-dados.md`/`v1-emissao-generica.md`: `alembic/versions/e5a1f0c2b7d4_…dec_48.py` (UP035, I001, UP007 ×3), `tests/test_fotos_storage_key_unico.py` (F811 ×3), `tests/test_portal_versoes_relatorio.py` (I001), `tests/test_relatorio_unicidade.py` (I001).

### PDF e DOCX reais (uma emissão, dentro do container)

Script descartável em `$CLAUDE_JOB_DIR/tmp/v105/gerar_real.py`, fora do repositório. Ele cria no `garra_tmp_v105`:
- edificação, fiscal com assinatura e qualificação, 2 sistemas, 2 ocorrências;
- 3 fotos, uma delas só com sugestão de IA em rascunho;
- o conteúdo salvo (unidade, 2 datas e fundamentação).

Depois chama `relatorio_service.emitir_relatorio` com o **renderizador real** (`Renderizador("vistoria_residencial_pipeline")`, WeasyPrint + docxtpl) e storage em memória, extrai o texto (`pypdf` para o PDF, XML de `word/*.xml` para o DOCX) e apaga os dados.

```
versao: V01 relatorios/<id>/vistoria_residencial-v01.pdf relatorios/<id>/vistoria_residencial-v01.docx
PDF: 18547 caracteres; {'None': 0, '{{': 0, '{%': 0, 'SUGESTAO IA': 0, 'Apartamento 101': 2, 'Goiânia-GO': 1}
DOCX: 109566 caracteres; {'None': 0, '{{': 0, '{%': 0, 'SUGESTAO IA': 0, 'Apartamento 101': 2, 'Goiânia-GO': 1}
PDF páginas: 18 bytes: 698966 | DOCX bytes: 97352
imagens no PDF (pág. 1): 5 | imagens no DOCX: 4
  'Tipologia da edificação' / 'Sistema construtivo' / 'CEP: 74000-000' /
  'As vistorias foram realizadas em 04/11/2026 e 06/11/2026' / 'Figuras 1, 2' /
  'ABNT NBR 15575-2' / 'Especialista em Patologia'   → PDF=True DOCX=True (todos)
```

Conferência visual (páginas 1 e 17 renderizadas com `pypdfium2`):
- a capa sai com a arte de fundo vinda do storage, "Apartamento 101", o nome da edificação e o responsável e CREA;
- a página do encerramento traz o bloco de assinatura (nome, `Eng. Civil - CREA nº`, qualificação) e `Goiânia-GO, dd/mm/aaaa.`;
- o rodapé traz nome, CREA, e-mail e telefone.

## Achados

1. **Data padrão no fuso errado se usar `date.today()`.** O container roda em UTC. Na primeira geração, às 22h55 de 11/11 em Goiânia, a data saiu `12/11/2026`. Por isso `hoje()` usa `ZoneInfo("America/Sao_Paulo")`, com volta para `date.today()` quando não há base de fusos (Windows sem `tzdata`). `vistoria_residencial_pipeline.normalizar_contexto` (e os outros pipelines) ainda usam `date.today()` como padrão, mas esse caminho não é atingido pela emissão da Residencial.
2. **Logo sobreposto ao texto** na capa e no cabeçalho do PDF (título "VISTORIA TÉCNICA…" e "11. ENCERRAMENTO" encostam no `logo-garra.svg`). É do template ou do asset, anterior a esta tarefa e fora do escopo; vale uma conferência visual (HT-09) contra o original.
3. **O DOCX não usa `assinatura_data_uri` nem `capa_fundo_data_uri`** (o `vistoria_residencial_template.docx` não tem essas variáveis). A assinatura e a capa só aparecem no PDF.
4. O banco descartável `garra_tmp_v105` **ficou** no `garra-postgres`, só com o schema (os dados de teste foram apagados pelos fixtures e pelo script). O `DROP DATABASE` foi bloqueado pela barreira de dados do backlog-auto (hook `PreToolUse`). Para remover: `docker exec garra-postgres psql -U garra -d postgres -c "DROP DATABASE garra_tmp_v105"`.
5. A imagem `05_infra-backend` foi reconstruída a partir do código do worktree (`docker compose build backend`). O container `garra-backend` em execução **não** foi reiniciado.

## Decisões propostas (para o fechamento de lote; não registradas em `00_docs/projeto/decisoes.md`)

1. **Gancho `Emissor.anexar_do_storage`.** É o ponto de extensão para arquivos **opcionais** do storage (assinatura, capa, logo do cliente), separado de `extrair_fotos`, em que a ausência dá 409. O `montar_contexto` continua sem acesso ao storage, e o storage injetado na rota (fake nos testes) é o mesmo das fotos. A Vistoria Cautelar pode reaproveitar o gancho (hoje o pipeline dela recebe `assinatura_storage_key`/`capa_fundo_storage_key` por `fotos_bytes`).
2. **Origem da capa.** Não existe coluna para a "foto de capa" da edificação. Usei `edificacao.documentos_tecnicos.itens[]` com `tipo` `capa`/`fachada` (o upload `POST /edificacoes/{id}/documentos` já aceita `tipo` livre). Proposta: formalizar esse `tipo` no front (ou criar `edificacoes.capa_storage_key`).
3. **Foto sem legenda aprovada fica no laudo** com `'—'` (a evidência fotográfica é mantida e a sugestão de IA nunca é impressa). A alternativa, omitir a foto, mudaria a numeração das figuras citadas nas constatações.
4. **Campos obrigatórios da Residencial**: `fiscal.nome`, `fiscal.crea` e `imovel.unidade` (DEC-47 aplicado ao tipo).
5. **`local_emissao` padrão** tirado do endereço só quando ele termina em `Cidade - UF`/`Cidade/UF` (com CEP opcional depois). Proposta de modelo: colunas `cidade`/`uf` em `edificacoes`.

## Para o fechamento de lote (00_docs)

- `00_docs/arquitetura.md`: o tipo `VISTORIA_RESIDENCIAL` passa a ser emitível por `POST /inspecoes/{id}/relatorios/{tipo}`; incluir o campo `anexar_do_storage` no contrato do `Emissor` (em `v1-emissao-generica.md` também).
- `00_docs/projeto/decisoes.md`: avaliar as propostas 1 a 5.
- `00_docs/projeto/riscos.md`: data padrão em UTC nos outros pipelines (Achados 1) e sobreposição do logo (Achados 2).
- `00_docs/backlog-auto/vistoria-residencial-pipeline.md`: o "item aberto 1" (montagem do contexto) está resolvido por esta tarefa.
