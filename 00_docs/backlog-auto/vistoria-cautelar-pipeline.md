# Pipeline de renderização da Vistoria Cautelar (T11, DEC-35)

Pipeline irmão de `ltip_pipeline` (T05) para os templates de T09 (`templates/vistoria_cautelar/`).

- **Data:** 2026-11-04
- **Branch:** `worktree-backlog-T11` (commit local, sem push)
- **Base:** a branch estava 60 commits atrás de `main` e sem os artefatos de T05/T09. Foi feito `git merge --ff-only main` (sem divergência) antes de implementar.

## Arquivos

| Caminho | Papel |
|---|---|
| `04_backend/app/services/report_generator/vistoria_cautelar_pipeline.py` | `normalizar_contexto`, `renderizar_html`, `gerar_pdf`, `gerar_docx` |
| `04_backend/tests/test_vistoria_cautelar_pipeline.py` | 9 testes, contexto sintético; não leem `01_output-context/` nem o banco |

Templates, `layout.json` e `01_output-context/` não foram alterados.

## API

- `renderizar_html(contexto, fotos_bytes) -> str`: Jinja2 com autoescape; imagens como data URI.
- `gerar_pdf(contexto, fotos_bytes, destino) -> dict`: WeasyPrint importado dentro da função. Métricas: `render_html`, `conversao_pdf`, `total`, `n_paginas`, `tamanho_bytes` (iguais às do LTIP).
- `gerar_docx(contexto, fotos_bytes, destino, *, template_path=None) -> dict`: docxtpl com `autoescape=True` e `InlineImage`. Métricas: `montagem_fotos`, `render_e_salvar`, `total`, `tamanho_bytes`.
- O módulo não acessa o MinIO. O chamador entrega `fotos_bytes` indexado por `storage_key`. Foto referenciada e ausente levanta `KeyError`.
- `normalizar_contexto` não muta a entrada. Campos escalares vazios saem como `—` (DEC-33).

## Contrato do contexto

Lido do `.html.j2`, do `.docx` (document, header e footer) e do `layout.json`.

| Campo | Tipo | Obrigatório | Uso / tratamento |
|---|---|---|---|
| `responsavel.nome`, `.titulo_profissional`, `.crea`, `.email`, `.telefone` | str | não | capa, rodapé, assinatura; vazio → `—` |
| `responsavel.qualificacoes` | lista de str (ou texto) | não | linhas sob a assinatura |
| `obra.descricao` | str | não | capa, folha de rosto; vazio → `—` |
| `edificacao.nome` | str | não | capa, `<title>`; vazio → `—` |
| `data_emissao` | date / datetime / `AAAA-MM-DD` | não | base das duas datas abaixo; padrão = hoje |
| `data_emissao_mes_ano` | str | não | derivada (`Novembro de 2026`); o chamador pode sobrescrever |
| `data_emissao_extenso` | str | não | derivada (`4 de novembro de 2026`) |
| `local_emissao` | str | não | assinatura; vazio → `—` |
| `conteudo` | dict chave → lista de str ou texto livre | não | parágrafos por seção; chaves de `estrutura.secoes[*].chave`/`subsecoes[*].chave` do `layout.json` (ex.: `introducao`, `metodologia`, `encerramento`). Chave ausente = seção sem parágrafos |
| `complementos.parecer_tecnico` | str | não | complemento do título 10.1 (omitido se vazio) |
| `tabelas.identificacao[]` | `aspecto_tecnico`, `descricao_detalhada` | não | tabela 4.2; célula vazia → `—` |
| `tabelas.plano_de_correcoes_remanescentes[]` | `item`, `localizacao`, `descricao_da_pendencia`, `metodologia_corretiva_indicada` | não | tabela 10.2; célula vazia → `—` |
| `sistemas[]` | `nome`, `constatacoes`, `fundamentacao_tecnica` | não | capítulo 9 (9.1, 9.2…); os dois últimos aceitam lista ou texto |
| `figuras[]` | `numero` (padrão: sequência), `legenda`, `storage_key` | não | capítulo 8; sem `storage_key` a figura sai sem imagem; `storage_key` fora de `fotos_bytes` → `KeyError` |
| `assinatura_storage_key` | str | não | rubrica (HTML `assinatura_data_uri`, DOCX `assinatura_imagem`) |
| `capa_fundo_storage_key` | str | não | arte de fundo da capa; só HTML (`capa_fundo_data_uri`) |
| `logo_data_uri` | str | não | padrão: `templates/assets/logo-garra.svg` |

## Comandos e saídas

Rodados em `04_backend/` com o venv do checkout principal (`04_backend/.venv`; o worktree não tem venv próprio):

```text
$ python -m pytest tests/test_vistoria_cautelar_pipeline.py -q -rs
8 passed, 1 skipped
SKIPPED: WeasyPrint indisponível neste ambiente: OSError   (Pango/GTK ausentes no Windows)

$ python -m pytest -q tests/test_ltip_pipeline.py tests/test_vistoria_cautelar_templates.py tests/test_ltip_templates.py tests/test_rfo_templates.py
47 passed, 2 skipped

$ ruff check --isolated <arquivos novos>
All checks passed!
$ ruff check --isolated .
Found 5 errors.        # fora dos arquivos novos
```

**Não rodou:**

- **`pytest` completo.** O PostgreSQL de `05_infra` não está no ar (`localhost:5433`: conexão recusada) e o Docker não existe nesta máquina. A suíte completa travou por falta de banco e foi interrompida. Não há resultado dela.
- **PDF real.** O teste de PDF foi pulado pelo mesmo motivo (WeasyPrint indisponível no Windows). Falta rodá-lo no container, junto com a conferência visual HT-09 de T09.

## Observações e propostas (templates não alterados)

- O `.html.j2` usa `conteudo.get(...)`, `tabelas.get(...)` e `complementos.get(...)`. Sem esses dicts o Jinja falha, então `normalizar_contexto` sempre os cria.
- Sem sistemas, a subseção fixa "Correlação Técnica" assume o número 9.1 (comportamento do template, coberto em teste).
- Proposta: o chamador (futura rota/serviço) deve montar `sistemas`, `figuras` e `fotos_bytes` a partir do banco/MinIO, redimensionando antes. Esse mapeamento do banco para o contexto não faz parte desta tarefa.
- Proposta: extrair para módulo comum os auxiliares duplicados entre `ltip_pipeline` e este (`_mime`, `_em_paragrafos`, `_logo_data_uri`), como já sugerido em `ltip-pipeline.md`.

## Para o fechamento de lote (não editado aqui)

`backlog-tarefas.md`, `backlog-kanban.md` e `status.md`: pipeline da Vistoria Cautelar entregue; falta o teste de PDF no container e o mapeamento banco → contexto.
