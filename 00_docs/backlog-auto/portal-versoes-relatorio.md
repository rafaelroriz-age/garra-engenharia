# Portal do Cliente — versões de relatório (DEC-48 P1)

Tarefa de **teste e diagnóstico**: nenhum código de produção foi alterado.
Arquivo de teste: `04_backend/tests/test_portal_versoes_relatorio.py`.

## Fatos observados (código atual)

- Cada emissão cria um `Relatorio` novo (`versao` = "V01", "V02"…), todos ligados à mesma `Inspecao`.
- `GET /api/v1/portal/relatorios` (`portal_service.listar_relatorios`) devolve **todas** as versões de todos os contratos do contratante: não há filtro de "mais recente" nem agrupamento por inspeção.
- Ordenação: `emitido_em DESC NULLS LAST`, depois `versao` ascendente. Com V01 (fev) e V02 (mar), a V02 vem primeiro.
- Campo de versão exposto: `versao` (string). O schema `PortalRelatorioRead` **não** tem campo que indique a versão vigente (`vigente`/`mais_recente`); o cliente só infere pela ordem/data.
- Relatório sem `emitido_em` (rascunho) também aparece na listagem, no fim; `tem_pdf`/`tem_docx` ficam `false`.
- `GET /portal/relatorios/{id}/download/{formato}` aceita o id de **qualquer** versão do contratante, inclusive as antigas (V01 continua baixável depois da V02).
- Escopo: validado por `Contrato.contratante_id == responsavel.id`; relatório de outro contratante responde 404 `relatorio-nao-encontrado` (não revela existência).
- Download devolve `{relatorio_id, formato, url, expira_em_segundos=900}`; a chave de storage (`pdf_key`/`docx_key`) não aparece em nenhuma resposta.
- Sem `pdf_key`/`docx_key` → 404 `arquivo-nao-disponivel`. Formato fora de `pdf|docx` → 404 `formato-nao-suportado`.

## Tabela de casos

| # | Caso | Esperado | Resultado |
|---|------|----------|-----------|
| a1 | Inspeção com V01+V02: contagem da listagem | 2 itens, mesma `inspecao_id` | passa |
| a2 | Ordem | V02, V01 | passa |
| a3 | Campo `versao` e flags `tem_pdf`/`tem_docx` | presentes | passa |
| a4 | Listagem sinaliza a versão vigente | `vigente`/`mais_recente` = [true, false] | **xfail(strict)** — campo não existe |
| b1 | Cliente B lista relatórios | `[]` | passa |
| b2 | Cliente B baixa V01/V02 em pdf/docx (4 casos) | 404 `relatorio-nao-encontrado` | passa |
| c1 | Download V01/V02 em pdf/docx (4 casos) | 200, URL `https://…`, 900 s, sem chave | passa |
| c2 | Listagem não vaza chaves | sem `relatorios/`, `pdf_key`, `docx_key` | passa |
| d1 | Relatório sem pdf_key/docx_key | listado com flags false; download 404 `arquivo-nao-disponivel` (pdf e docx) | passa |
| d2 | Formato inválido | 404 `formato-nao-suportado` | passa |

O storage é substituído por um fake via `dependency_overrides[get_storage_client]` (sem rede/MinIO).

## Comandos e saída

Ambiente: o Python global não tinha as dependências; criei um venv temporário fora do repositório (`--system-site-packages`) e instalei `requirements.txt` sem `pillow` (falha de build no Windows; já presente no Python global), mais `pytest`, `pytest-asyncio>=1.0` (o 0.23 quebra com o pytest 9 e com o `pytest.ini`) e `ruff`.

```
cd 04_backend
python -m pytest tests/test_portal_versoes_relatorio.py
  -> 15 passed, 1 xfailed, 1 warning
python -m pytest tests/test_portal_cliente.py tests/test_portal_versoes_relatorio.py
  -> 3 failed, 19 passed, 1 xfailed   (antes do ajuste de um assert meu; ver abaixo)
python -m ruff check tests/test_portal_versoes_relatorio.py
  -> sem erros (após --fix de imports/UTC no arquivo novo)
python -m ruff check .
  -> ainda com erros pré-existentes em outros arquivos (~200, sem config ruff no repo); não tocados
```

PostgreSQL em `localhost:5433` estava no ar (os testes de banco rodaram).

**Falhas pré-existentes, não causadas por esta tarefa**: `tests/test_portal_cliente.py::test_download_docx_inexistente_retorna_404` e `::test_download_de_relatorio_de_outro_contratante_retorna_404` falham com `ConnectionRefusedError` — usam o storage real (MinIO/S3) e ele não está no ar neste ambiente. Sugestão: esse arquivo deveria também sobrescrever `get_storage_client` com um fake, como faz o arquivo novo. O terceiro "failed" da execução combinada foi um assert errado meu (procurava o sufixo do cenário, que aparece no nome da edificação); corrigido.

## Proposta de decisão para DEC-48 P1 (PROPOSTA — não é decisão vigente)

**Manter todas as versões visíveis e baixáveis, mas destacar a vigente.**

1. Não filtrar a listagem para só a última emissão: o cliente tem motivo legítimo para consultar/baixar versões anteriores (rastreabilidade do que foi emitido), e esconder V01 quebraria links/downloads já usados.
2. Adicionar a `PortalRelatorioRead` um booleano `vigente` (verdadeiro para o `Relatorio` mais recente por `inspecao_id` + `tipo`, critério `emitido_em` desc), e o portal exibir a vigente em destaque e as demais como "versões anteriores".
3. Excluir rascunhos (`status != emitido` / sem `emitido_em`) da listagem do cliente — hoje eles aparecem. Requer confirmar com o produto.
4. Ao implementar, remover o `xfail` de `test_listagem_sinaliza_qual_versao_e_a_vigente` (é `strict`, então passará a falhar o suite até a marca ser retirada, o que serve de lembrete).

Pontos abertos para o integrador: confirmar (2) e (3) com o cliente; decidir se a vigência é por `tipo` ou só por inspeção.
