# Emissão de relatório genérica por tipo (V1-02 / T58)

Status: **implementado e testado** (PostgreSQL de 05_infra). Único tipo registrado: **RFO**. LTIP, RFIP e vistorias entram em tarefas próprias, registrando um `Emissor` como descrito abaixo.

## O que mudou

| Arquivo | Mudança |
|---|---|
| `04_backend/app/services/relatorio_service.py` | Dataclass `Emissor`, registro `EMISSORES` + `registrar_emissor`/`obter_emissor`/`tipos_disponiveis`; RFO registrado no import do módulo; `Renderizador` genérico (recebe o módulo do pipeline); `ContextoIncompletoError(tipo, campos)`; `TipoRelatorioNaoRegistradoError` (422); `emitir_relatorio(db, inspecao_id, tipo, storage, renderizador=None)`; `listar_relatorios`; `gerar_url_download` interno (escopo da inspeção). |
| `04_backend/app/services/report_generator/imagem.py` (novo) | `otimizar_imagem` movida para cá (só Pillow, sem WeasyPrint). |
| `04_backend/app/services/report_generator/rfo_pipeline.py` | Remove a definição de `otimizar_imagem` e a reexporta de `imagem.py` (`rfo_pipeline.otimizar_imagem` continua valendo para o benchmark BL-22). |
| `04_backend/app/services/report_generator/__init__.py` | `report_generator.otimizar_imagem` resolve para `imagem.py` (não carrega mais o WeasyPrint). |
| `04_backend/app/services/portal_service.py` | Extraídos `campo_do_formato(formato)` e `url_assinada_do_relatorio(relatorio, campo_key, formato, storage)`; `gerar_url_download` do portal usa os dois (comportamento igual, filtro por contratante mantido). |
| `04_backend/app/schemas/relatorio.py` | `RelatorioVersaoRead` (listagem) e `RelatorioDownloadRead` (subclasse de `PortalDownloadRead`, mesmo formato). |
| `04_backend/app/api/v1/relatorios.py` | Rotas novas (abaixo) + dependency `get_renderizador_por_tipo`. `POST .../relatorios/rfo` e `get_renderizador_rfo` mantidos. |
| `04_backend/tests/test_relatorios_emissao_generica.py` (novo) 18 funções / 20 casos: registro e contrato do RFO, tipo divergente no registro, chave por tipo, erro genérico + alias, `Renderizador` com módulo e otimização, re-export de `otimizar_imagem`; tipo inexistente 422; tipo ≠ inspeção 409; normalização `Rfo`; auxiliar 403 na emissão; emissor fake `TESTE` emite V01/V02 com chaves `teste-v0N`; contexto incompleto genérico 422; listagem (ordem, campos, 404, cliente 403); download por papel (auditor 200, auxiliar 200, cliente 403), docx e formato inválido; relatório de outra inspeção 404; serviço sem renderizador injetado usa o do emissor. |
| `04_backend/tests/test_relatorios_rfo_api.py` | Correção de fixture: RFO e LTIP agora em contratos distintos (ver Achados, item 1). |

### Compatibilidade preservada
- `RenderizadorRFO` (alias do protocolo `RenderizadorProtocol`), `RenderizadorRFOPadrao` (= `Renderizador("rfo_pipeline")`), `get_renderizador_rfo`, `emitir_rfo(db, inspecao_id, storage, renderizador)`, `storage_keys_das_fotos`.
- `RfoContextoIncompletoError(campos)` é subclasse de `ContextoIncompletoError` com `tipo="RFO"`; `type_suffix` continua `rfo-contexto-incompleto`.
- Chave no storage: `relatorios/{inspecao_id}/{tipo.lower()}-{versao.lower()}.{ext}` → para o RFO continua `relatorios/{id}/rfo-v01.pdf`.
- 409 por tipo divergente: `type_suffix` = `inspecao-nao-{tipo.lower()}` → para o RFO continua `inspecao-nao-rfo`.

## Rotas (prefixo `/api/v1/inspecoes`)

| Método e caminho | Papéis | Respostas |
|---|---|---|
| `POST /{inspecao_id}/relatorios/rfo` | auditor | igual ao BL-13 |
| `POST /{inspecao_id}/relatorios/{tipo}` | auditor (auxiliar/cliente → 403) | 201 `RelatorioEmitidoRead`; tipo normalizado (`strip().upper()`); não registrado → **422** `tipo-relatorio-nao-registrado` com `errors[0].disponiveis` (decidido antes de tocar no banco); inspeção inexistente → 404; `inspecao.tipo ≠ tipo` → **409** `inspecao-nao-{tipo}`; contexto incompleto → 422 `{tipo}-contexto-incompleto`; foto ausente no storage → 409; sem WeasyPrint → 503 |
| `GET /{inspecao_id}/relatorios` | auditor, auxiliar (cliente → 403) | 200 lista `{id, tipo, versao, status, emitido_em, tem_pdf, tem_docx}`, mais recente primeiro (`emitido_em desc nulls last, tipo, versao desc`); inspeção inexistente → 404 |
| `GET /{inspecao_id}/relatorios/{relatorio_id}/download/{formato}` | auditor, auxiliar (cliente → 403, ele usa `/portal`) | 200 `{relatorio_id, formato, url, expira_em_segundos}` (URL pré-assinada, mesma lógica do portal sem o filtro de contratante); `formato` aceita maiúsculas (`PDF`); formato ≠ pdf/docx → 404 `formato-nao-suportado`; relatório de outra inspeção → 404 `relatorio-nao-encontrado`; sem arquivo → 404 `arquivo-nao-disponivel` |

A rota fixa `.../relatorios/rfo` é declarada antes de `.../relatorios/{tipo}`, então `rfo` minúsculo continua caindo no handler do BL-13 (dependency `get_renderizador_rfo`); `RFO`/`Rfo` caem na genérica (dependency `get_renderizador_por_tipo`). As duas produzem o mesmo resultado.

## Contrato do `Emissor`

```python
@dataclass(frozen=True)
class Emissor:
    tipo: str                                                   # = Inspecao.tipo = Relatorio.tipo, maiúsculas ("LTIP")
    montar_contexto: Callable[[AsyncSession, UUID], Awaitable[dict]]  # contexto do pipeline
    validar_contexto: Callable[[dict], list[str]]               # caminhos obrigatórios ausentes ([] = ok)
    extrair_fotos: Callable[[dict], set[str]]                   # storage_keys que o template embute
    pipeline: str                                               # módulo em app.services.report_generator

    def criar_renderizador(self) -> RenderizadorProtocol: ...   # Renderizador(self.pipeline)
```

Garantias que `emitir_relatorio` dá a cada emissor, nesta ordem:
1. `obter_emissor(tipo)`: 422 se não registrado.
2. A inspeção existe (404) e `inspecao.tipo == emissor.tipo` (409). `montar_contexto` **não precisa** repetir essas checagens (o do RFO repete, sem problema).
3. `montar_contexto(db, inspecao_id)`: monta o dict que o pipeline consome. Pode lançar `DomainError`s próprios.
4. `validar_contexto(contexto)`: lista não vazia → `ContextoIncompletoError(tipo, campos)` (422, `{tipo}-contexto-incompleto`, um item em `errors` por campo).
5. `extrair_fotos(contexto)`: chaves baixadas do storage (ordem irrelevante, vão num `dict` `storage_key → bytes`); chave ausente → 409 `foto-ausente-no-storage`.
6. Renderização PDF e DOCX, lock `FOR NO KEY UPDATE` na inspeção, próxima versão **contada por (inspecao_id, tipo)** (`V01`, `V02`…; casa com `uq_relatorios_inspecao_tipo_versao`, DEC-48), upload em `relatorios/{inspecao_id}/{tipo}-{versao}.{pdf|docx}`, `Relatorio(status="emitido")`; erro → rollback + remoção dos arquivos gravados.

Contrato do módulo `pipeline` (o mesmo de `rfo_pipeline`, `ltip_pipeline`, `rfip_pipeline`, `vistoria_*_pipeline`):

```python
def gerar_pdf(contexto: dict, fotos_bytes: dict[str, bytes], destino: Path) -> Any: ...
def gerar_docx(contexto: dict, fotos_bytes: dict[str, bytes], destino: Path) -> Any: ...
```

O `Renderizador` importa o módulo sob demanda (`__import__("app.services.report_generator", fromlist=[pipeline])`), passa as fotos por `imagem.otimizar_imagem` (lado máx. 1200 px, JPEG q72) e devolve os bytes do arquivo gravado em diretório temporário. `ImportError`/`OSError` no import → 503 `gerador-relatorio-indisponivel`. Também aceita um módulo já importado (`Renderizador(modulo)`), útil em testes.

## Como registrar um tipo novo (LTIP, RFIP, vistorias)

1. Criar `app/services/report_generator/{tipo}_contexto.py` com `TIPO_X = "X"`, `async def montar_contexto_x(db, inspecao_id) -> dict` e `def validar_contexto_x(contexto) -> list[str]` (padrão de `rfo_contexto.py`, DEC-47: só campos que o template imprime sem fallback e cujas colunas aceitam NULL).
2. Garantir que o pipeline (`x_pipeline.py`) expõe `gerar_pdf`/`gerar_docx(contexto, fotos_bytes, destino)` e que o import do WeasyPrint é tardio ou que o módulo só é importado pelo `Renderizador`.
3. Registrar no fim de `relatorio_service.py` (ou num módulo importado por ele, para o registro acontecer no startup da API):
   ```python
   from app.services.report_generator.ltip_contexto import TIPO_LTIP, montar_contexto_ltip, validar_contexto_ltip

   registrar_emissor(TIPO_LTIP, Emissor(
       tipo=TIPO_LTIP,
       montar_contexto=montar_contexto_ltip,
       validar_contexto=validar_contexto_ltip,
       extrair_fotos=lambda ctx: {f["storage_key"] for o in ctx["ocorrencias"] for f in o["fotos"]},
       pipeline="ltip_pipeline",
   ))
   ```
   `registrar_emissor` normaliza a chave para maiúsculas e recusa (`ValueError`) chave diferente de `emissor.tipo`; registrar de novo o mesmo tipo substitui.
4. Nenhuma rota nova: `POST /inspecoes/{id}/relatorios/x` passa a funcionar, e listagem/download já cobrem o tipo. Se o pipeline não precisar de `otimizar_imagem` (ex.: já redimensiona), criar uma subclasse de `Emissor` que sobrescreva `criar_renderizador` devolvendo `Renderizador(self.pipeline, otimizar_fotos=False)`.
5. Testes: seguir `tests/test_relatorios_emissao_generica.py` (fixture `emissor_teste` registra/desregistra o tipo; `app.dependency_overrides[get_renderizador_por_tipo] = lambda: (lambda tipo: fake)` evita WeasyPrint).

## Comandos e saída

O Python local (anaconda, Windows) não roda a suíte: `passlib` falha com o `bcrypt` instalado (`password cannot be longer than 72 bytes`; o requirements fixa `bcrypt<4.1`) e o WeasyPrint não carrega `libpango` (impede coletar `test_rfo_contexto.py`, que importa `rfo_pipeline`). Por isso rodei num container descartável da imagem `05_infra-backend`, com `04_backend` do worktree montado em `/app`, na rede `garra-net` (Postgres `garra-postgres`), com `pip install -r requirements.txt` antes (a imagem não tinha `pytest-asyncio`):

```
docker run --rm --network garra-net --env-file <env do garra-backend> -v <worktree>/04_backend:/app -w /app 05_infra-backend \
  sh -c 'pip install -q -r requirements.txt; python -m pytest tests/test_relatorios_emissao_generica.py tests/test_relatorios_rfo_api.py tests/test_rfo_contexto.py -q'
```

- `pytest tests/test_relatorios_emissao_generica.py tests/test_relatorios_rfo_api.py tests/test_rfo_contexto.py` → **40 passed**.
- `tests/test_rfo_pipeline.py`, citado no prompt, **não existe** no repositório (`ERROR: file or directory not found`). O `rfo_pipeline` é coberto por `test_rfo_templates.py` e `test_pipelines_url_fetcher.py`, que passaram na suíte completa.
- `pytest` completo (mesmo container): `12 failed, 562 passed, 3 skipped, 5 xfailed, 19 errors`. As mesmas falhas aparecem na `main` (`d656e34`), rodando os mesmos arquivos numa cópia limpa (`git archive`): `test_gabarito` (FileNotFound, `01_output-context` fora do container), `test_ocorrencias_regras` (erros de fixture), `test_ocorrencias_prioridade` (5), `test_seguranca_legenda_ia` (3), `test_edificacoes::test_listar_edificacoes_paginado`, `test_fotos_storage_key_unico::test_banco_rejeita_storage_key_duplicada` e `test_relatorio_unicidade::test_duplicata_levanta_integrity_error`; as duas últimas esperam migrations que o banco não tem (item 2). A única diferença, `test_fotos_lacunas::test_lacuna_3_imagem_truncada_retorna_422_nao_500[JPEG]`, é intermitente: gera a imagem com `os.urandom`. Rodando isolado na minha árvore deu 27/27 duas vezes, e o teste não usa nada alterado aqui.
- `ruff check .` → 10 erros, **todos em arquivos não tocados** e já presentes na `main`: `alembic/versions/e5a1f0c2b7d4_relatorios_unicidade_versao_dec_48.py` (UP035/I001/UP007×3), `tests/test_fotos_storage_key_unico.py` (F811×3), `tests/test_portal_versoes_relatorio.py` (I001), `tests/test_relatorio_unicidade.py` (I001). `ruff check app tests/test_relatorios_emissao_generica.py tests/test_relatorios_rfo_api.py` → `All checks passed!`. Não corrigi os de fora do escopo, para não conflitar com outras tarefas do lote.

## Achados para o fechamento de lote

1. **`inspecoes.contrato_id` é UNIQUE** (`app/models/inspecao.py:29`, constraint `inspecoes_contrato_id_key` desde a migration inicial): um contrato tem uma inspeção só. A fixture do BL-13 (`test_relatorios_rfo_api.py`) criava RFO e LTIP no mesmo contrato e **falhava em 23 testes na `main`** (`UniqueViolationError`). Corrigi só a fixture: a LTIP ganhou um contrato próprio. Se o produto precisar de várias inspeções/tipos por contrato (ex.: RFO + LTIP do mesmo contrato), isso é decisão de modelo para um DEC.
2. **Banco do 05_infra atrás das migrations**: `alembic_version = f7c2a9d4e6b1`, e a `main` tem os heads `e5a1f0c2b7d4` (unicidade de relatório, DEC-48) e `e5a1c7d9b3f4` (merge, storage_key único). Sem `alembic upgrade head`, a constraint `uq_relatorios_inspecao_tipo_versao` não existe no banco local. Esta tarefa não cria migration.
3. A imagem `05_infra-backend` está desatualizada em relação ao `requirements.txt` (sem `pytest-asyncio`): convém `docker compose build backend`.
4. `00_docs/projeto` (fechamento): registrar as rotas novas no README do backend/arquitetura e propor um DEC para o **registro de emissores** como ponto de extensão dos tipos de relatório (contrato acima).
