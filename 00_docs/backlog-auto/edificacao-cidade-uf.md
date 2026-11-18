# `cidade` e `uf` em Edificação, usadas na emissão (DEC-50 P5)

Status: **implementado e testado** no backend (PostgreSQL de 05_infra, banco `garra_engenharia_test`). O frontend **não** foi alterado (ver Pendências).

Origem: DEC-50 P5, «A cidade da emissão sai do endereço (`Cidade-UF`) até existir `cidade`/`uf` em `Edificacao`».

## O que mudou

| Arquivo | Mudança |
|---|---|
| `04_backend/app/models/edificacao.py` | Colunas `cidade` (`String(120)`, nullable) e `uf` (`String(2)`, nullable). |
| `04_backend/app/schemas/edificacao.py` | `cidade` (até 120) e `uf` (`^[A-Z]{2}$`) opcionais em `EdificacaoBase`, herdados por `EdificacaoCreate`, `EdificacaoUpdate`, `EdificacaoRead` e `EdificacaoComContratos`. Um validador `before` apara espaços, converte vazio/só espaços em `None` e põe `uf` em maiúsculas (`go` → `GO`). `uf` com tamanho ≠ 2 ou caractere fora de A-Z (`G1`, `--`, `Ç1`) → **422** `application/problem+json`. |
| `04_backend/alembic/versions/d3e7a1c5f9b2_edificacao_cidade_uf_dec_50.py` (novo) | `add_column` das duas colunas; `downgrade()` remove as duas. Sem backfill nem reescrita de dados. |
| `04_backend/app/services/report_generator/contexto_comum.py` | Nova `cidade_emissao(edificacao, extrair_do_endereco=None)`, com as regras abaixo. |
| `04_backend/app/services/report_generator/vistoria_cautelar_contexto.py` | `local_emissao` = conteúdo salvo → `cidade_emissao(edificacao, cidade_do_endereco)`. |
| `04_backend/app/services/report_generator/vistoria_residencial_contexto.py` | Mesma troca (`… or VAZIO` mantido no fim). |
| `04_backend/tests/test_edificacao_cidade_uf.py` (novo) | 34 casos (ver Testes). |

Templates, `layout.json` e pipelines não foram tocados. O formato de saída é o mesmo de antes, `Cidade-UF` sem espaços, que é o que os dois parsers produzem e os testes existentes (`test_cidade_do_endereco` nos dois módulos de vistoria) esperam.

### Onde a cidade é derivada (diferente do que a tarefa supunha)

A derivação **não** ficava em `contexto_comum.py`. Ela fica em `cidade_do_endereco`, presente em **dois** montadores e com parsers diferentes:
- `vistoria_cautelar_contexto.py`: procura um segmento entre vírgulas no formato `Cidade-UF`/`Cidade/UF`;
- `vistoria_residencial_contexto.py`: usa uma regex no fim do endereço que aceita hífen, travessão curto ou barra e um CEP opcional.

RFO, LTIP e RFIP **não** derivam a cidade do endereço. O LTIP só usa `local_emissao` quando ele está no conteúdo salvo, e RFO e RFIP não usam o campo. Por isso a mudança alcança os dois montadores de vistoria, e o comportamento de RFO, LTIP e RFIP fica igual. Os dois parsers continuam onde estavam e são passados como fallback, para que dados antigos produzam exatamente o mesmo texto de antes.

## Regra de `cidade_emissao` (fallback)

Ordem completa em cada montador: `local_emissao` do conteúdo salvo (`relatorio_conteudos`) → `cidade_emissao(...)` → (residencial) `—`.

| `cidade` | `uf` | Resultado |
|---|---|---|
| preenchida | preenchida | `f"{cidade}-{uf}"` (ex.: `Anápolis-GO`), mesmo que o endereço aponte outra cidade |
| preenchida | vazia | o resultado do endereço, se for a **mesma** cidade (comparação sem distinguir maiúsculas), para completar a UF; senão, a **cidade sozinha** (o campo explícito prevalece sobre o texto livre) |
| vazia | preenchida | fallback pelo endereço (a UF sozinha não identifica o local) |
| vazia | vazia | fallback pelo endereço, como era antes; `None` se o endereço não tiver `Cidade-UF` |

Objetos sem os atributos `cidade`/`uf` (`getattr` com padrão) também caem no fallback. Sem parser (`extrair_do_endereco=None`), só os campos explícitos contam.

**Decisão proposta (para o fechamento de lote, complementa DEC-50 P5):** com `cidade` e `uf` preenchidas, elas prevalecem sobre o endereço. Só com `cidade`, ela prevalece e é impressa sem UF quando o endereço for de outra cidade. Só com `uf`, ela é ignorada. Os dois parsers de endereço continuam como fallback permanente para os dados antigos.

## Migration

- `alembic heads` **antes** da tarefa: um único head, `c6f2a8d4e1b9` (BL-34). Não havia vários heads (R-17), então não foi preciso fazer merge.
- Nova revisão: **`d3e7a1c5f9b2`** (`down_revision = "c6f2a8d4e1b9"`). `alembic heads` depois: `d3e7a1c5f9b2 (head)`.
- Validação no `garra_engenharia_test` (`POSTGRES_DB=garra_engenharia_test`):
  ```
  Running upgrade c6f2a8d4e1b9 -> d3e7a1c5f9b2, edificacao_cidade_uf_dec_50
  Running downgrade d3e7a1c5f9b2 -> c6f2a8d4e1b9, edificacao_cidade_uf_dec_50
  current: c6f2a8d4e1b9
  Running upgrade c6f2a8d4e1b9 -> d3e7a1c5f9b2, edificacao_cidade_uf_dec_50
  current: d3e7a1c5f9b2 (head)
  ```
- `alembic check` → **FAILED**, mas só por drift **anterior** do BL-34 (`c6f2a8d4e1b9`), sem relação com `edificacoes`: `remove_index ix_fotos_legenda_aprovada_fts`, `ix_trechos_conhecimento_ia_texto_trgm`, `ix_trechos_conhecimento_ia_tsv` e `remove_table_comment trechos_conhecimento_ia`. São índices e comentários criados por SQL na migration e ausentes dos modelos. Não apareceu nenhuma operação sobre `edificacoes.cidade`/`uf`, então modelo e migration desta tarefa estão em sincronia. Não corrigi o drift do BL-34, que está fora do escopo (sugestão: declarar esses índices nos modelos ou filtrá-los em `include_object` no `alembic/env.py`).
- O banco de dev `garra_engenharia` **não** foi migrado por esta tarefa.

## API

`POST /api/v1/edificacoes` e `PUT /api/v1/edificacoes/{id}` aceitam `cidade` e `uf` opcionais, e as leituras os devolvem (`null` quando ausentes). O `PUT` substitui todos os campos (BL-08): se o corpo vier sem `cidade`/`uf`, os dois voltam a `null`. O cliente que só quer manter os valores precisa reenviá-los.

## Testes

Ambiente: venv `04_backend/.venv` do checkout principal (o worktree não tem venv), `.env` copiado do checkout principal (ignorado pelo git, não commitado), `POSTGRES_DB=garra_engenharia_test`, Postgres `garra-postgres` em `localhost:5433`.

| Comando | Onde | Resultado |
|---|---|---|
| `pytest tests/test_edificacao_cidade_uf.py -q` | host (Windows) | **34 passed** em 223,5 s |
| `pytest tests/test_edificacoes.py -q` | host | **7 passed** em 91,3 s |
| `pytest tests -k "contexto or emissao or relatorio" -q` | host | **não rodou**: erro de coleta em `tests/test_rfo_contexto.py`, `OSError: cannot load library 'libpango-1.0-0'` (WeasyPrint sem as bibliotecas nativas no Windows) |
| o mesmo, na imagem `05_infra-backend` (WeasyPrint 70.0) com o worktree montado em `/app`, rede `garra-net`, `POSTGRES_DB=garra_engenharia_test` | container | **217 passed, 1 failed, 1 skipped, 1 xfailed, 1 error**, 631 deselected, 127,9 s |
| `ruff check .` | host | `All checks passed!` |

As duas falhas do recorte **já existem na `main`**. Rodei `tests/test_portal_cliente.py` e `tests/test_relatorio_unicidade.py` isolados, no mesmo container, numa cópia limpa da `main` (`git archive main`) e neste worktree, e o resultado foi idêntico nos dois: `2 failed, 7 passed, 1 skipped, 1 error`.
- `test_portal_cliente.py::test_download_de_relatorio_de_outro_contratante_retorna_404` (e, isolado, `test_download_docx_inexistente_retorna_404`): `RuntimeError: ... attached to a different loop` (event loop da fixture vs. `TestClient`).
- `test_relatorio_unicidade.py::test_duplicata_levanta_integrity_error`: erro de fixture já registrado em `v1-emissao-generica.md`.

Os testes de `cidade_do_endereco` dos dois montadores de vistoria (`test_vistoria_cautelar_contexto.py`, `test_vistoria_residencial_contexto.py`) estão no recorte e passaram: o fallback continua igual.

Cobertura de `test_edificacao_cidade_uf.py`:
- API: criar sem os campos (`null`), criar com `"  Anápolis "`/`" go "` → `Anápolis`/`GO` e releitura por `GET`, vazio → `null`, `uf` inválida → 422 (6 casos), `cidade` com 121 caracteres → 422, `PUT` define e depois remove (`null`), `PUT` com `uf` inválida → 422.
- `cidade_emissao`, com os dois parsers: cidade+uf prevalecem, ausentes → endereço, só `uf` → endereço, só `cidade` igual à do endereço → completa a UF, só `cidade` diferente → cidade sozinha, endereço sem cidade → `None`, sem parser e objeto antigo sem atributos.
- Montadores no banco (cautelar e residencial) × (cidade+uf, ausentes, só uf, só cidade): `local_emissao` = `Anápolis-GO`, `Goiânia-GO`, `Goiânia-GO`, `Anápolis`.

## Pendências

1. **Frontend**: o formulário de edificação (`03_frontend/app/edificacoes/`) ainda não expõe `cidade` e `uf`. Fica para uma próxima tarefa: dois campos opcionais (UF como seleção das 27 siglas, para evitar o 422) e o reenvio dos dois no `PUT`, para não apagá-los ao editar outro campo.
2. Não existe backfill: edificações antigas continuam com `cidade`/`uf` nulos e usam o endereço. Preencher a partir do parser exigiria uma migration de dados aprovada pelo dono (regra «nunca alterar dados existentes»).
3. Drift do `alembic check` vindo do BL-34 (acima).
4. Se o produto quiser, LTIP e RFIP podem passar a usar `cidade_emissao` como padrão de `local_emissao`. Hoje não usam nenhum, e mudar isso altera a saída deles, por isso ficou fora desta tarefa.
