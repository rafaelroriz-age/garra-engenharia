# RFO: validação de completude do contexto antes de emitir (DEC-47 item 2)

## O que mudou

- `04_backend/app/services/report_generator/rfo_contexto.py`: `CAMPOS_OBRIGATORIOS_RFO` e
  `validar_contexto_rfo(contexto) -> list[str]` (caminhos como `contrato.objeto`; ausente = `None` ou texto em branco; `prazo_dias == 0` conta como preenchido).
- `04_backend/app/services/relatorio_service.py`: `RfoContextoIncompletoError` (`DomainError`, HTTP 422,
  `type` `.../erros/rfo-contexto-incompleto`, `errors=[{"field": "contrato.objeto", "message": ...}]`).
  `emitir_rfo` valida logo após `montar_contexto_rfo` e antes de baixar fotos, renderizar, subir ao storage ou criar `Relatorio`.
- `tests/test_rfo_validacao_contexto.py` (novo) e `tests/test_relatorios_rfo_api.py` (cenário passou a ter `objeto`, `prazo_dias`, `art_fiscalizacao`, senão a emissão válida passaria a dar 422).
- Pré-requisito (tarefa B, `legenda_para_relatorio`): commit `900bb75` está na `main`. A branch do worktree estava atrás da `main` e foi avançada por fast-forward local.

## Campos obrigatórios e critério

Critério: campo que `templates/rfo/rfo_template.html.j2` imprime **sem fallback** (`or "—"` / `{% if %}`) **e** cuja coluna aceita NULL.

| Caminho | Uso no template |
|---|---|
| `fiscal.crea` | "Nº CREA" (capa) e "CREA nº" (cada visita) |
| `contrato.art_fiscalizacao` | "ART de Fiscalização" |
| `contrato.objeto` | "Objeto", e "Obra" em cada visita |
| `contrato.data_inicio` | "Início" |
| `contrato.prazo_dias` | "Prazo" e "Prazo contratual" |

Fora da lista, de propósito: `contrato.numero`, `edificacao.nome/endereco`, `fiscal.nome`, `executor.razao_social/cnpj` (colunas NOT NULL, o banco garante);
`fiscal.email`, `edificacao.tipologia` (têm fallback `—`).

## Lacunas para decisão do dono (não alteradas aqui)

- `executores[].art_execucao` é nullable e o template imprime sem fallback ("ART de Execução: None"). Fora da lista por não constar no pedido da DEC-47; incluir é uma linha em `CAMPOS_OBRIGATORIOS_RFO` (exigiria tratar a lista de executores).
- `visita.data`/`servicos_executados` e a regra de ocorrências no RFO (DEC-47 item 3) não foram tocadas.

## Comandos e saída

Ambiente: PostgreSQL (localhost:5433) **fora do ar** e sem `docker` na máquina; dependências do projeto não instaláveis por completo (build do pillow falhou), então usei um venv com `--system-site-packages` + `python-jose passlib bcrypt email-validator python-multipart boto3`.

- `python -m pytest tests/test_rfo_validacao_contexto.py -q -k "not endpoint"` (04_backend): **17 passed, 3 deselected**.
- **Não rodaram** (precisam de PostgreSQL): `test_endpoint_422_sem_relatorio_nem_upload` (2 casos), `test_endpoint_contrato_completo_emite_201` e a suíte completa `python -m pytest`. Os testes de endpoint foram escritos mas não executados; rodar com o compose de 05_infra no ar antes de integrar.
- `ruff check app tests/test_rfo_validacao_contexto.py tests/test_relatorios_rfo_api.py`: sem erros. `ruff check .` completo acusa erros pré-existentes em `alembic/versions/e5a1f0c2b7d4_...` e `tests/test_relatorio_unicidade.py` (não tocados).
- `npm` não se aplica (só backend alterado).
