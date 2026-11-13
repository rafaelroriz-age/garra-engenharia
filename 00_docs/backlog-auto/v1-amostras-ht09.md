# Seed de demonstração e amostras dos 5 relatórios (V1-08 / T64)

Material para a conferência visual humana HT-09 e primeira execução completa da suíte com banco e WeasyPrint dentro do container (riscos R-14/R-15). Papel: Engenheiro Backend. Data: 2026-11-11/12. Branch: `worktree-backlog-T64`.

> **Nota de ambiente:** o worktree nasceu de uma base antiga (`14ead2f`), sem nenhum dos V1. Como a branch não tinha commits próprios e `14ead2f` é ancestral de `main`, fiz `git merge --ff-only main` (até `58eaa81`) antes de começar. Nada foi reescrito.

## O que mudou

| Arquivo | Mudança |
|---|---|
| `04_backend/app/scripts/seed_demo.py` (novo) | Seed idempotente. `python -m app.scripts.seed_demo` (`--reset` recria; `--limpar` só remove). Tudo que cria leva o prefixo `DEMO - ` (e-mail `demo.auditor@example.com`, chaves `fotos/demo/...`); nada fora do prefixo é lido ou alterado. |
| `04_backend/tests/test_seed_demo.py` (novo) | 5 testes (banco real + storage em memória, prefixo isolado `DEMOTESTE`): rodar 2× não duplica, volume esperado, fiscal/ocorrências/conteúdo, `--reset`, limpeza só do prefixo. |

O que o seed cria: 1 edificação (endereço completo e CEP), 1 fiscal (CREA, título profissional, 3 qualificações), 1 auditor `demo.auditor@example.com` (senha de `DEMO_SENHA`, padrão local `demo-senha-123`), 5 contratos+inspeções (um por tipo, `DEMO-<TIPO>-001/2026`). RFO: 2 visitas (mão de obra, 2 medições cada) e 3 fotos por visita, mais executora com ART. Demais 4 tipos: 8 ocorrências em 4 sistemas prediais (primeiros 4 por `ordem`, 1º subsistema), GUT, grau de risco (CRITICO/MEDIO/MINIMO), prioridade, 1 foto por ocorrência. Fotos: JPEG sintético de 1200 px (Pillow), enviado ao MinIO, legenda **aprovada** (`status_validacao_ia='aprovada'`, aprovador e data). Conteúdo salvo via `relatorio_conteudo_service.salvar`: `data_emissao`, `local_emissao`; Cautelar com `parecer` e `datas_vistorias`; Residencial com `unidade` ("Apartamento 1404") e `datas_vistorias`. Total no banco: 1 edificação, 5 contratos, 2 visitas, 32 ocorrências, 38 fotos.

Se o gabarito de sistemas prediais estiver vazio, o seed chama `seed_gabarito` (ver Achados, item 2).

## Resultado das emissões (API no container, banco `garra_demo_v1`)

Emitido por `POST /api/v1/inspecoes/{id}/relatorios/{TIPO}` com o auditor do seed; download por `GET .../relatorios/{id}/download/{pdf|docx}` (URL pré-assinada). Todos 201, versão V01. O tempo é o do POST (render PDF + DOCX + upload).

| Tipo | Páginas (PDF) | Tempo | PDF | DOCX | Original de referência (`01_output-context/`) | Páginas do original |
|---|---|---|---|---|---|---|
| RFO | 9 | 3,26 s | 904 512 B (883 KiB) | 485 629 B (474 KiB) | `Relatório de Fiscalização.pdf` (e `Relatório de Fiscalização 1.xlsm`) | 98 |
| LTIP | 13 | 2,43 s | 1 114 110 B (1,06 MiB) | 446 739 B (436 KiB) | `Laudo Técnico de Inspeção Predial 2026 - Cond. Cortina D'Ampezzo.pdf` | 199 |
| RFIP | 9 | 4,02 s | 1 406 492 B (1,34 MiB) | 631 527 B (617 KiB) | `Relatório Fotográfico de Inspeção Predial - CORTINA D'AMPAREZZO - Versão Final.xlsx` | (planilha) |
| VISTORIA_CAUTELAR | 25 | 7,07 s | 1 978 244 B (1,89 MiB) | 638 093 B (623 KiB) | `Laudo Técnico de Vistoria Cautelar de Recebimento - Reforma New York - V01.pdf` | 148 |
| VISTORIA_RESIDENCIAL | 22 | 5,75 s | 1 853 627 B (1,77 MiB) | 635 951 B (621 KiB) | `Laudo Técnico de Vistoria de Imóvel Residencial - Ap. 1404.pdf` | 91 |

Arquivos em `01_output-context/_amostras_ht09/v1/<tipo>-v1.pdf|docx` (nomes: `rfo`, `ltip`, `rfip`, `vistoria_cautelar`, `vistoria_residencial`; mais `resultado.json` com os números acima). A pasta está no `.gitignore` (`01_output-context/_amostras_ht09/`), **não foi commitada**. Nenhum outro arquivo de `01_output-context/` foi tocado (só li os originais para contar páginas).

As amostras têm 9 a 25 páginas porque o volume de dados é pequeno (8 ocorrências, 6 fotos); a comparação com o original é de **layout e estilo**, não de extensão. **Não inspecionei as páginas visualmente**: a conferência abaixo é a tarefa humana HT-09.

## Folha de conferência (HT-09)

Para cada tipo, abrir `<tipo>-v1.pdf` ao lado do original indicado e marcar. O DOCX deriva do mesmo `layout.json` (DEC-25/ADR-13): conferir os mesmos itens abrindo `<tipo>-v1.docx` no Word.

Itens comuns a todos os tipos:

| Item | O que comparar | OK? |
|---|---|---|
| Cabeçalho/logo | Logo, posição, tamanho, texto e linha do cabeçalho em todas as páginas (e a capa sem cabeçalho, se o original assim for) | ☐ |
| Rodapé e paginação | Texto do rodapé, formato "Página X de Y", numeração começando onde o original começa | ☐ |
| Tabelas | Larguras de coluna, bordas, cor e fonte do cabeçalho de tabela, alinhamento, texto sem corte | ☐ |
| Fotos e legendas | Quantidade por página, proporção, moldura, legenda abaixo/ao lado como no original, numeração "Foto N" | ☐ |
| Quebras de página | Título sem ficar órfão no fim da página; tabela/foto sem cortar no meio; quebras entre seções | ☐ |
| Tipografia | Família, corpo, entrelinha, negrito/itálico, cor dos títulos e hierarquia 1/1.1/1.1.1 | ☐ |

Pontos específicos por tipo:

| Tipo | Arquivo | Original | Específico a conferir |
|---|---|---|---|
| RFO | `rfo-v1.*` | `Relatório de Fiscalização.pdf` | Quadro de identificação (fiscal, ART, objeto, prazo), bloco da executora (ART de execução), tabela de mão de obra e de medições por visita, fotos da visita |
| LTIP | `ltip-v1.*` | `Laudo Técnico de Inspeção Predial 2026 - Cond. Cortina D'Ampezzo.pdf` | Seções textuais (introdução a conclusão), ficha de cada ocorrência (sistema, GUT, grau de risco, prioridade), foto da ocorrência, assinatura do fiscal |
| RFIP | `rfip-v1.*` | `Relatório Fotográfico ... Versão Final.xlsx` | Grade de fotos com legenda, resumo (`incluir_resumo` = verdadeiro), um bloco por ocorrência; o original é planilha: comparar a organização, não a paginação |
| VISTORIA_CAUTELAR | `vistoria_cautelar-v1.*` | `Laudo Técnico de Vistoria Cautelar de Recebimento - Reforma New York - V01.pdf` | Capa, sumário, datas das vistorias, parecer técnico (10.1), plano de correções (10.2), fundamentação por sistema, referências |
| VISTORIA_RESIDENCIAL | `vistoria_residencial-v1.*` | `Laudo Técnico de Vistoria de Imóvel Residencial - Ap. 1404.pdf` | Identificação da unidade ("Apartamento 1404"), seções s1 a s12, análise por sistema, datas das vistorias |

## Suíte completa no container

Ambiente: imagem `05_infra-backend` (Python 3.12, WeasyPrint 70.0, bcrypt do pin `<4.1`), contra o PostgreSQL de `05_infra` (container `garra-postgres`), no banco novo `garra_demo_v1` (`alembic upgrade head` limpo, ver Achados, item 1). Comando: `docker exec -e POSTGRES_DB=garra_demo_v1 garra-backend python -m pytest -p no:cacheprovider -q -rfEs`.

| Execução | passed | failed | error | skipped | xfailed | Duração |
|---|---|---|---|---|---|---|
| Suíte inteira, uma execução | **697** | **15** | **14** | **3** | 5 | 326,22 s (5 min 26 s) |

Reexecução dos 7 arquivos com falha, um por vez (R-15):

| Arquivo | Na suíte inteira | Sozinho | Causa provável |
|---|---|---|---|
| `test_fotos_lacunas.py` (1 failed) | `test_lacuna_3_imagem_truncada_retorna_422_nao_500[JPEG]`: 201 em vez de 422 | **27 passed** | Interferência entre testes na mesma execução (R-15: loop de eventos/estado compartilhado). Não reproduz isolado. |
| `test_ocorrencias_dashboard.py` (2 failed) | `test_criar_e_listar_ocorrencias`, `test_dashboard_edificacao_retorna_agregados` | **3 passed** | Idem (R-15). |
| `test_portal_cliente.py` (3 failed) | 404 do portal e download docx inexistente | **7 passed** | Idem (R-15). |
| `test_ocorrencias_prioridade.py` (5 failed) | os 5 testes que usam `headers=auth["Authorization"]` | **5 failed** | Bug do teste: `auth["Authorization"]` é um texto, mas o `httpx` 0.28 exige um dict de cabeçalhos (`ValueError: not enough values to unpack (expected 2, got 1)`, `tests/test_ocorrencias_prioridade.py:123,138,152,173,187,195`). Correção: `headers=auth` (ou `{"Authorization": ...}`). |
| `test_ocorrencias_regras.py` (13 errors) | erro no fixture `ctx` | **13 errors** | Bug do fixture: cria 2 `Inspecao` para o mesmo contrato (`tests/test_ocorrencias_regras.py:~84`, `outra_inspecao`), mas `inspecoes.contrato_id` é UNIQUE (relação 1:1, `models/inspecao.py`): `UniqueViolationError inspecoes_contrato_id_key`. Correção: dar um contrato próprio à `outra_inspecao`. |
| `test_seguranca_legenda_ia.py` (4 failed) | `test_erro_de_arquivo_ausente_nao_expoe_storage_key`, `test_regerar_apos_aprovar_limpa_aprovacao_anterior`, `test_editar_legenda_aprovada_nao_atribui_edicao_ao_aprovador_anterior`, `test_auxiliar_nao_aprova_legenda_ia` | **4 failed, 10 passed, 3 xfailed** | Persistem isolados. Só aprofundei o primeiro: `tests/test_seguranca_legenda_ia.py:148` espera 400/404/422 e a API devolve 200. Os outros 3 não foram analisados (causa não determinada). Comportamento ou teste desatualizado em relação à emissão/legenda: precisa de análise do dono. |
| `test_relatorio_unicidade.py` (1 error) | erro de teardown de `test_duplicata_levanta_integrity_error` | **2 passed, 1 skipped, 1 error** | `sqlalchemy.exc.MissingGreenlet` no teardown (uso de objeto ORM fora do contexto async após o `IntegrityError`); o teste em si passa. |

Resumo depois de separar: dos 29 itens com falha/erro na execução única, **6 passam isolados** (efeito R-15) e **23 persistem** (5 + 13 + 4 + 1), todos em **código de teste ou comportamento já existente** em `main`; nenhum deles toca `seed_demo`. Os 3 skips: 2 em `test_foto_origem_enum.py:62` ("PostgreSQL de 05_infra indisponível em localhost:5433": dentro do container o banco é `postgres:5432`, então o teste não decide) e 1 em `test_relatorio_unicidade.py:59` ("`emitir_rfo` ... não existe nesta branch": o skip está desatualizado, `emitir_rfo` existe hoje).

Não corrigi nenhum teste nem código fora do Toca; as correções acima são propostas.

## Testes novos e lint

- `tests/test_seed_demo.py`: **5 passed** no container (`docker exec -e POSTGRES_DB=garra_demo_v1 garra-backend python -m pytest tests/test_seed_demo.py -q`). No host (Python do anaconda, bcrypt 5.0, fora do pin `<4.1`) o hash da senha quebra com o `passlib` (`ValueError: password cannot be longer than 72 bytes`); o mesmo ocorre em `tests/test_auth.py` no host. Por isso a validação é no container.
- `ruff check .` em `04_backend`: **All checks passed!** (após `--fix` de `datetime.UTC` no seed).
- Frontend não foi tocado (`npm run lint`/`build` não se aplicam).

## Achados e propostas

1. **Migration `e5a1f0c2b7d4` falha no banco de desenvolvimento** (`garra_engenharia`): `RuntimeError: Existem 1 grupo(s) duplicado(s) em relatorios (inspecao_id, tipo, versao)` (inspeção `22db6dc2-f9d0-4d38-87ec-218e68c8c8cd`, tipo RFO, versão `BENCH-01`, 2 registros: `fddefc2c-...`, `fee39a87-...`; resíduo do benchmark BL-22). Esse banco está na revisão `f7c2a9d4e6b1`, abaixo do head. A migration manda limpar manualmente e **não alterei nem apaguei nada** lá. Para a tarefa criei o banco separado `garra_demo_v1` (`CREATE DATABASE`, mesmo servidor), migrado até `a9c3e5f7b1d2 (head)`, e usei-o para seed, API e suíte. Decisão do dono: renumerar/remover as 2 linhas `BENCH-01` e rodar `alembic upgrade head` no banco de desenvolvimento. Os bancos `garra_tmp_v105`, `garra_engenharia_test` e `garra_bl34_tmp2` já existiam e não foram tocados.
2. **`seed_gabarito` não roda dentro da imagem do backend**: `rfo_gabarito_parser.py` lê `/00_docs/convertidos/RFO_INSPECAO.md`, que não existe no container (contexto de build é `../04_backend`). Contornei copiando o arquivo para o container (`docker cp` para `/00_docs/convertidos/`, fora do repositório) e rodando `python -m app.scripts.seed_gabarito` com `POSTGRES_DB=garra_demo_v1`. O `seed_demo` chama o gabarito sozinho se a tabela estiver vazia, então em ambiente novo precisa do mesmo arquivo disponível. Proposta: embutir o gabarito já parseado (JSON) na imagem ou montar `00_docs/convertidos` como volume.
3. **Idempotência sob falha**: a primeira execução do seed (sem gabarito) criou só o RFO e abortou nas ocorrências do LTIP (transação por tipo, com `commit` ao fim de cada um); a execução seguinte completou os outros 4 (`CRIADOS={'contratos': 4, 'inspecoes': 4, 'ocorrencias': 32, 'fotos': 32, 'conteudos': 4}`). Fotos de um tipo que falhou ficam no MinIO como órfãs até a reexecução (chaves determinísticas: são sobrescritas, não duplicadas).
4. **Segunda API só para as amostras**: como o container `garra-backend` serve o banco de desenvolvimento, subi uma segunda instância do uvicorn dentro dele (`docker exec -d -e POSTGRES_DB=garra_demo_v1 garra-backend uvicorn app.main:app --host 127.0.0.1 --port 8001`), não publicada no host. Ela existe só enquanto o container não for recriado.
5. **Dados de demonstração só no banco `garra_demo_v1`**; nada de `DEMO` no banco de desenvolvimento. O MinIO é o mesmo (bucket `relatorios-prediais`): objetos `fotos/demo/...` (38) e `relatorios/<inspecao>/<tipo>-v01.pdf|docx` (10). Para remover: `docker exec -e POSTGRES_DB=garra_demo_v1 garra-backend python -m app.scripts.seed_demo --limpar` (apaga fotos do storage e o banco-fonte); os relatórios emitidos no MinIO precisam de limpeza à parte.
6. **Decisão proposta (para `decisoes.md`, no fechamento)**: convenção `DEMO` (nome `DEMO - ...`, e-mail `demo.auditor@example.com`, `fotos/demo/`) para dados de demonstração, com `--limpar`/`--reset` restritos ao prefixo; senha do auditor só por `DEMO_SENHA`.

## Comandos e saídas literais

Docker em `C:\Program Files\Docker\Docker\resources\bin` (adicionado ao `PATH`). O `.env` está só no checkout principal (não existe no worktree, é ignorado pelo git); usei `--env-file` apontando para ele, sem copiá-lo nem commitá-lo.

```text
$ cd 05_infra; docker compose --env-file <.env do checkout principal> build backend
 ... #9 [backend 5/6] RUN pip install --no-cache-dir -r requirements.txt  CACHED
 ... #10 [backend 6/6] COPY . .  DONE 0.3s
 ... naming to docker.io/library/05_infra-backend  done

$ docker compose --env-file <.env> up -d
 Container garra-backend  Recreated
 Container garra-frontend  Recreated
 Container garra-minio / garra-postgres  Healthy
$ docker compose ps
 garra-backend   Up 21 seconds (healthy)   127.0.0.1:8000->8000/tcp
 garra-frontend  Up 20 seconds             127.0.0.1:3000->3000/tcp
 garra-minio     Up 5 hours (healthy)      127.0.0.1:9000-9001->9000-9001/tcp
 garra-postgres  Up 5 hours (healthy)      127.0.0.1:5433->5432/tcp

$ docker exec garra-backend alembic upgrade head          # banco de desenvolvimento
 RuntimeError: Existem 1 grupo(s) duplicado(s) em relatorios (inspecao_id, tipo, versao); a constraint uq_relatorios_inspecao_tipo_versao não pode ser criada.
   inspecao_id=22db6dc2-f9d0-4d38-87ec-218e68c8c8cd tipo=RFO versao=BENCH-01 (2 registros: fddefc2c-1f5f-4663-900b-88d16c436cc7, fee39a87-2b84-42bb-b7e4-85ff2829e7ca)
 Limpe manualmente (revise e remova/renumere com critério de negócio) e rode o upgrade novamente. Esta migration não altera dados.

$ docker exec garra-postgres psql -U garra -d postgres -c "CREATE DATABASE garra_demo_v1"
 CREATE DATABASE
$ docker exec -e POSTGRES_DB=garra_demo_v1 garra-backend alembic upgrade head
 ... Running upgrade e5a1c7d9b3f4 -> a9c3e5f7b1d2, conteudo_relatorio_tipo_servico_v1_01
$ docker exec -e POSTGRES_DB=garra_demo_v1 garra-backend alembic current
 a9c3e5f7b1d2 (head)

$ docker exec -e POSTGRES_DB=garra_demo_v1 garra-backend python -m app.scripts.seed_gabarito
 INFO:__main__:Seed do gabarito concluído: {'sistemas_prediais': 15, 'subsistemas': 113, 'tipos_anomalia': 6, 'tipos_falha': 9, 'localizacoes': 47}

$ docker exec -e POSTGRES_DB=garra_demo_v1 garra-backend python -m app.scripts.seed_demo     # 1ª (completando a execução abortada)
 CRIADOS={'contratos': 4, 'inspecoes': 4, 'ocorrencias': 32, 'fotos': 32, 'conteudos': 4}
 AUDITOR_EMAIL=demo.auditor@example.com
 INSPECAO_RFO=feb6e47c-f5d2-40a1-8777-5932d2161807
 INSPECAO_LTIP=2f33d3ea-4c8f-46b5-8d9d-39b123ce0642
 INSPECAO_RFIP=692c327f-499c-4921-81df-b298c2e8fec1
 INSPECAO_VISTORIA_CAUTELAR=d64193f8-e8fe-467a-91fa-645264692ca2
 INSPECAO_VISTORIA_RESIDENCIAL=5e117fe0-3b11-4b96-93a2-76e5711333a8
$ ... seed_demo                                                                               # 2ª: nada a criar
 CRIADOS={}
 (mesmos 5 INSPECAO_*)

$ docker exec garra-backend python /tmp/emitir.py RFO=<id> LTIP=<id> RFIP=<id> VISTORIA_CAUTELAR=<id> VISTORIA_RESIDENCIAL=<id>
 login 200
 RFO 201 3.26s
 LTIP 201 2.43s
 RFIP 201 4.02s
 VISTORIA_CAUTELAR 201 7.07s
 VISTORIA_RESIDENCIAL 201 5.75s
 [{"tipo":"RFO","versao":"V01","pdf_bytes":904512,"docx_bytes":485629,"paginas_pdf":9},
  {"tipo":"LTIP","versao":"V01","pdf_bytes":1114110,"docx_bytes":446739,"paginas_pdf":13},
  {"tipo":"RFIP","versao":"V01","pdf_bytes":1406492,"docx_bytes":631527,"paginas_pdf":9},
  {"tipo":"VISTORIA_CAUTELAR","versao":"V01","pdf_bytes":1978244,"docx_bytes":638093,"paginas_pdf":25},
  {"tipo":"VISTORIA_RESIDENCIAL","versao":"V01","pdf_bytes":1853627,"docx_bytes":635951,"paginas_pdf":22}]
 (resumo; o JSON completo, com ids e HTTP 200 dos downloads, está em 01_output-context/_amostras_ht09/v1/resultado.json)

$ docker exec -e POSTGRES_DB=garra_demo_v1 garra-backend python -m pytest -p no:cacheprovider -q -rfEs
 15 failed, 697 passed, 3 skipped, 5 xfailed, 33 warnings, 14 errors in 326.22s (0:05:26)

$ docker exec -e POSTGRES_DB=garra_demo_v1 garra-backend python -m pytest tests/test_seed_demo.py tests/test_relatorio_conteudo.py -q
 28 passed, 7 warnings in 21.23s
$ docker exec -e POSTGRES_DB=garra_demo_v1 garra-backend python -m pytest tests/test_seed_demo.py -q   # após o ajuste do ruff
 5 passed, 1 warning in 8.10s

$ cd 04_backend; ruff check .
 All checks passed!
```

## Para o fechamento de lote

- `backlog-tarefas.md`/`backlog-kanban.md`: V1-08 concluída (código e Doc); HT-09 passa a ter material em `01_output-context/_amostras_ht09/v1/` (pasta local, ignorada pelo git).
- `riscos.md`: R-14/R-15 com números reais (697 passed; 6 falhas só na execução única, 23 persistentes em testes antigos); registrar a falha da migration `e5a1f0c2b7d4` no banco de desenvolvimento (resíduo `BENCH-01`).
- `decisoes.md`: proposta do item 6.
- `05_infra/README.md`/`04_backend/README.md`: citar `seed_demo` e a necessidade do gabarito no container (item 2).
