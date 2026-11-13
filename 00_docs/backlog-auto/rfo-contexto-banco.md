# Contexto do RFO a partir do banco (BL-13)

Código: `04_backend/app/services/report_generator/rfo_contexto.py` → `montar_contexto_rfo(db: AsyncSession, inspecao_id)`.
Testes: `04_backend/tests/test_rfo_contexto.py`. Sem endpoint (tarefa seguinte).

## Comportamento
- Uma query com `selectinload` (contrato→edificação/fiscal/executores→responsável legal+RTE/NBRs; visitas→mão de obra/medições/fotos; ocorrências→fotos/sistema/subsistema): sem N+1.
- Visitas e ocorrências por `seq_numero`; fotos por `ordem` (nulos ao final); mão de obra por função; medições por descrição; executores por razão social; NBRs por código.
- Fotos saem só com `id`, `storage_key`, `url_publica`, `legenda`, `ordem`. O `data_uri`/binário continua a cargo do fetcher (`gerar_pdf` exige `fotos_bytes[storage_key]`).
- Inspeção inexistente → `NotFoundError` (404, `inspecao-nao-encontrada`); `tipo != 'RFO'` → `ConflictError` (409, `inspecao-nao-rfo`).
- Datas saem como `dd/mm/aaaa` (o template imprime `{{ visita.data }}` direto).

## Mapeamento banco → contexto
| Contexto | Origem |
|---|---|
| `contrato.numero/tipo_servico/objeto/prazo_dias/art_fiscalizacao/observacoes_gerais` | `Contrato.*` |
| `contrato.data_inicio` | `Contrato.data_inicio` (dd/mm/aaaa) |
| `edificacao.nome/endereco/cep/tipologia/sistema_construtivo/descricao_pavimentos/area_total_m2` | `Edificacao.*` |
| `fiscal.nome/crea/email/telefone` | `Contrato.fiscal` (`Responsavel`) |
| `executores[].razao_social/cnpj/endereco/art_execucao` | `ContratoExecutor.*` |
| `executores[].responsavel_legal`, `.rte` | `ContratoExecutor.responsavel_legal/rte` (`Responsavel`: nome, cpf_cnpj, crea) |
| `nbrs[].codigo_nbr/descricao` | `ContratoNbr.*` |
| `visitas[].seq_numero/data/servicos_executados/observacoes` | `Visita.*` (as `*_lista` são derivadas por `normalizar_contexto`) |
| `visitas[].mao_obra[].funcao/quantidade` | `VisitaMaoObra` |
| `visitas[].medicoes[].descricao/quantidade/unidade` | `VisitaMedicao` |
| `visitas[].fotos[]` / `ocorrencias[].fotos[]` | `Foto` (`storage_key`, `url_publica`, `legenda`, `ordem`) |
| `ocorrencias[]` (sistema, subsistema, localizacao, situacao, classificacao, tipo_anomalia, tipo_falha, grau_risco, prioridade, descricao) | `Ocorrencia` + `SistemaPredial.nome`/`Subsistema.nome` |
| `inspecao.id/tipo/status` | `Inspecao` |
| `logo_data_uri` | `normalizar_contexto` (arquivo SVG) |

## Correção do fechamento de lote (2026-11-10)
A lacuna 1 e a proposta P1 abaixo **estão obsoletas**: a sessão rodou num worktree defasado. Na `main` existem `report_generator/legenda_foto.py` (`legenda_para_relatorio`, que imprime sempre `legenda` e nunca `legenda_ia_sugerida`) e DEC-37; o estado da IA é `status_validacao_ia`, e `Foto` não tem `legenda_status`. Portanto `legenda_aprovada` é permissiva e deve ser trocada por `legenda_para_relatorio` (DEC-47, item 1); a coluna `legenda_status` não é necessária. Não alterado aqui (só documentação).

## Lacunas
1. **`legenda_foto.py` / `legenda_para_relatorio` não existem** neste repositório (busca em todo o worktree sem resultado), nem DEC-37/DP-9 em `00_docs/`. `Foto` não tem campo de status da legenda. Implementei `legenda_aprovada(foto)`: usa `foto.legenda_status` se existir (só `"aprovada"` passa); sem o campo, a legenda é tratada como aprovada. O teste de "pendente" usa objeto simulado, não banco.
2. O template HTML do RFO não renderiza `ocorrencias` nem `observacoes_gerais`; o contexto as traz, mas hoje são ignoradas.
3. `Foto.data_uri` não vem do banco (esperado; vem do fetcher).
4. `fiscal.crea` e `contrato.art_fiscalizacao/objeto/data_inicio/prazo_dias` são nulos no banco; o template imprime vazio/`None`. Falta validação de completude antes de gerar.
5. Sem assinaturas/ART de RTE no template, embora o banco tenha `rte`.
6. `renderizar_html` citada no enunciado não existe em `rfo_pipeline`; o teste renderiza com Jinja2 do mesmo modo que `gerar_pdf`.

## Propostas de decisão
- **P1:** adicionar `Foto.legenda_status` (`pendente`/`aprovada`, default `pendente`) com migration, e então tornar `legenda_aprovada` estrito (hoje é permissivo por falta do campo).
- **P2:** `montar_contexto_rfo` validar campos obrigatórios do template e falhar com 422 antes de renderizar.
- **P3:** decidir se o RFO imprime ocorrências (RF-04..06) ou se ficam só no LTIP.

## Resultado dos testes (ambiente da sessão)
- `ruff check` nos dois arquivos novos: OK. `ruff check .` no backend inteiro: 215 erros **preexistentes** (não tocados).
- `pytest tests/test_rfo_contexto.py`: **não rodou**. (a) PostgreSQL em localhost:5433 fora do ar; (b) o ambiente Windows não tem as bibliotecas nativas do WeasyPrint (Pango: `OSError: cannot load library 'libpango-1.0'`), e `app.services.report_generator.__init__` importa o weasyprint. Instalei o pacote `weasyprint` via pip (só no ambiente).
- Verificação parcial com weasyprint simulado: `legenda_aprovada` e a ordenação de fotos por `ordem` funcionam.
- Para rodar: subir `docker compose up -d` em `05_infra/`, depois `python -m pytest tests/test_rfo_contexto.py` em `04_backend/` (com Pango/GTK instalado ou em container).
