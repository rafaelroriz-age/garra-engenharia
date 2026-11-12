# 04_backend

Aplicação **FastAPI (Python 3.12)** responsável pela API, regras de negócio, persistência, armazenamento de arquivos, geração de relatórios e integração com o frontend.

> O backend já está em uma fase funcional para o fluxo principal do sistema: autenticação JWT, dados mestre, CRUD de edificações/contratos/inspeções/visitas/ocorrências, upload e reprocessamento de fotos, dashboard de saúde, portal do cliente e storage compatível com MinIO/S3. A geração final de PDF/DOCX fiel ao template do cliente ainda depende da entrega dos modelos originais do cliente e da finalização do pipeline de relatórios.

## Status atual real

- **Autenticação e autorização**: login JWT, proteção de rotas, RBAC básico para auditor/cliente e fluxo de portal escopado por responsável/contrato.
- **Domínio principal**: endpoints para edificações, contratos, inspeções, visitas, ocorrências, fotos e documentos técnicos.
- **Dados mestre**: gabarito de sistemas prediais, subsistemas, tipos de anomalia/falha e localizações carregado via seed idempotente.
- **Storage**: upload/download/delete e URLs pré-assinadas para MinIO/S3.
- **Segurança e operação**: tratamento global de erros, rate limit, middleware de segurança e preparação para deploy/produção.
- **Pendências**: geração final do relatório usando os templates Word originais e a integração completa da feature de legendas assistidas por IA.

## Estrutura atual

```
04_backend/
├── app/
│   ├── api/
│   │   ├── deps.py              # dependências de autenticação/autorização
│   │   └── v1/                  # rotas de auth, dados mestre, edificações, contratos, inspeções, visitas, ocorrências, fotos, portal e documentos
│   ├── models/                # modelos SQLAlchemy 2 (async) para o domínio principal e os dados mestre
│   ├── schemas/                # schemas Pydantic v2 request/response para os principais recursos
│   ├── scripts/                # parsers e seeds dos gabaritos e utilidades operacionais
│   ├── services/
│   │   └── storage/             # StorageClient (interface) + S3StorageClient (boto3/MinIO)
│   ├── core/
│   │   ├── config.py            # settings de banco, MinIO, JWT e ambiente
│   │   ├── database.py          # engine/sessão assíncrona SQLAlchemy 2
│   │   └── security.py          # hash/verify de senha (bcrypt) + create/decode de JWT
│   └── main.py                  # instância FastAPI, CORS, GET /health e inclusão dos routers
├── templates/assets/            # marca vetorizada do JPEG oficial (DEC-30): logo-garra.svg (PDF), logo-garra.png transparente (DOCX), negativa, símbolo e marca.json
├── alembic.ini                  # config do Alembic (URL sobrescrita em runtime por env.py)
├── alembic/
│   ├── env.py                    # migrations async (asyncio.run + run_sync), target_metadata = app.models.Base.metadata
│   └── versions/                 # c22d4029c062_initial... (BL-04) + 8e2467ad6a92_gabarito_tipos... (BL-05) + ab22bfcbdd0a_usuario... (BL-06)
├── tests/
│   ├── conftest.py               # fixture db_session (engine de teste com NullPool)
│   ├── test_health.py
│   ├── test_models.py            # testes de integração das 14 entidades e seus relacionamentos
│   ├── test_gabarito.py          # parser + seed + endpoints de dados mestre (BL-05)
│   ├── test_auth.py              # registro, login (sucesso/falha) e proteção de rota (BL-06)
│   ├── test_storage.py           # upload/download/delete/URL pré-assinada contra o MinIO real (BL-07)
│   ├── test_storage_legenda_ia.py # exists/list_keys/órfãos/presigned com S3 falso, sem MinIO (T30)
│   ├── test_relatorio_orfaos.py  # relatório de órfãos em dry-run com S3 falso e vínculos injetados (T32)
│   └── test_foto_origem_enum.py  # enum fechado de `origem` no vínculo de foto (T31)
├── requirements.txt
├── Dockerfile
├── pytest.ini
├── conftest.py
└── .env.example
```

## Como rodar localmente (sem Docker)

```powershell
cd 04_backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env   # ajuste se necessário; padrão assume Postgres/MinIO publicados pelo docker-compose em 05_infra/
uvicorn app.main:app --reload
```

A API sobe em `http://localhost:8000`. Documentação OpenAPI automática em `http://localhost:8000/docs`.
Requer o PostgreSQL de [05_infra/docker-compose.yml](../05_infra/docker-compose.yml) rodando (`cd 05_infra && docker compose up -d postgres`) para que `GET /health` reporte `database: "ok"`.

## Como rodar via Docker Compose

```powershell
cd 05_infra
docker compose up -d --build backend
```

## Modelos de dados e migrations (BL-04)

```powershell
cd 05_infra
docker compose up -d postgres   # sobe o PostgreSQL publicado em localhost:5433

cd ..\04_backend
cp .env.example .env             # ajuste POSTGRES_PORT=5433 (porta publicada pelo docker-compose)
.venv\Scripts\Activate.ps1
alembic upgrade head             # aplica a migration inicial (14 tabelas)
alembic revision --autogenerate -m "descrição"   # gera novas migrations a partir dos modelos
```

A URL de conexão do Alembic vem de `Settings.database_url` (via `alembic/env.py`), não do `alembic.ini` — mesma fonte de verdade usada pela aplicação.

## Gabarito de sistemas prediais/subsistemas/tipos de anomalia/falha/localizações (BL-05)

Dados mestre (RF-10) extraídos de `00_docs/convertidos/RFO_INSPECAO.md` (parser em `app/scripts/rfo_gabarito_parser.py`, sem cópia manual dos valores — evita erro de transcrição) e persistidos via seed idempotente:

```powershell
cd 04_backend
alembic upgrade head              # cria as tabelas tipos_anomalia, tipos_falha, localizacoes (além das 14 do BL-04)
python -m app.scripts.seed_gabarito   # idempotente: pode ser rodado quantas vezes for preciso
```

Endpoints (somente leitura, dados mestre editados no futuro via CRUD de BL-14+):

| Endpoint | Descrição |
|---|---|
| `GET /api/v1/sistemas-prediais` | 15 sistemas prediais com seus subsistemas aninhados |
| `GET /api/v1/gabarito/tipos-anomalia` | 6 tipos de anomalia |
| `GET /api/v1/gabarito/tipos-falha` | 9 tipos de falha |
| `GET /api/v1/gabarito/localizacoes` | 47 localizações padrão |

Ver DEC-13 em [decisoes.md](../00_docs/projeto/decisoes.md) para a justificativa de `TipoAnomalia`/`TipoFalha`/`Localizacao` serem tabelas novas fora do diagrama ER original (o campo correspondente em `Ocorrencia` permanece texto livre até a BL-14+).

## Templates de relatório derivados do original do cliente (BL-12/BL-13)

Os templates do RFO **não são escritos à mão**: o layout é medido do original do
cliente (`01_output-context/Relatório de Fiscalização 1.xlsm`) e materializado em
`templates/rfo/layout.json`, do qual derivam o `.html.j2` (WeasyPrint, DEC-01) e o
`.docx` (docxtpl, DEC-04) — garantindo que PDF e DOCX não divirjam (ADR-13/DEC-25).

```powershell
cd 04_backend
# Re-extrai o layout do original e regera os dois templates
python -m app.scripts.build_rfo_templates --original "..\01_output-context\Relatório de Fiscalização 1.xlsm"

# Apenas regera os templates a partir do layout.json já versionado
# (para máquinas/CI sem acesso aos originais do cliente)
python -m app.scripts.build_rfo_templates
```

| Arquivo | Papel |
|---|---|
| `app/scripts/rfo_layout_extractor.py` | Lê a planilha com `openpyxl` (`keep_vba=False` — as macros do `.xlsm` nunca são carregadas nem executadas, OWASP A08) e devolve margens, tipografia, cores de seção, rótulos, grade fotográfica e assinaturas |
| `app/scripts/build_rfo_templates.py` | CLI que persiste o `layout.json` e gera os dois templates |
| `templates/rfo/layout.json` | Especificação intermediária **versionada** — contém apenas geometria; os valores preenchidos no exemplar do cliente (CPF, e-mails, nomes) são descartados antes do commit |
| `templates/rfo/rfo_template.html.j2` / `rfo_template.docx` | Artefatos gerados — não editar à mão, alterar o gerador e regerar |

> O WeasyPrint não roda no venv local do Windows (faltam as libs GTK): a renderização
> real do PDF só funciona dentro do container `garra-backend`.

## Templates das Vistorias Cautelar e Residencial (T09/T10, ADR-13)

Mesmo método do LTIP, a partir dos PDFs finais do cliente (lidos de `01_output-context/`, que não é alterado):
PDF → `layout.json` (só geometria e rótulos fixos, sem dado do exemplar) → `.html.j2` (WeasyPrint) + `.docx` (docxtpl).

| Vistoria | Extrator / gerador (`app/scripts/`) | Templates | Testes |
|---|---|---|---|
| Cautelar de Recebimento | `vistoria_cautelar_layout_extractor.py`, `build_vistoria_cautelar_templates.py` | `templates/vistoria_cautelar/` | `tests/test_vistoria_cautelar_templates.py` (PDF sintético) |
| Imóvel Residencial | `vistoria_residencial_layout_extractor.py`, `build_vistoria_residencial_templates.py` | `templates/vistoria_residencial/` | `tests/test_vistoria_residencial_templates.py` (PDF sintético) |

Os pipelines de renderização (T11, T12) ficam em `app/services/report_generator/vistoria_cautelar_pipeline.py` e `vistoria_residencial_pipeline.py`, com a mesma API do LTIP (`normalizar_contexto`, `renderizar_html`, `gerar_pdf`, `gerar_docx`) e testes em `tests/test_vistoria_*_pipeline.py`. O teste de PDF é pulado onde o WeasyPrint não roda (Windows). Pendente: conferência visual no container (HT-09), a arte de capa do cliente (não versionada) e a montagem do contexto das vistorias a partir do banco. **RFO (T45, 2026-11-10):** `report_generator/rfo_contexto.py` → `montar_contexto_rfo(db, inspecao_id)` monta o contexto do `rfo_pipeline` com uma query (`selectinload`); inspeção inexistente → 404, tipo ≠ RFO → 409; sem endpoint (T46). Testes em `tests/test_rfo_contexto.py`, ainda não executados (PostgreSQL/WeasyPrint indisponíveis); ver DEC-47 e [rfo-contexto-banco.md](../00_docs/backlog-auto/rfo-contexto-banco.md). Detalhes em `00_docs/backlog-auto/vistoria-*-templates.md` e `vistoria-*-pipeline.md`.

### RFIP (BL-12, T13)

Planilha → `layout.json` → `.html.j2` + `.docx`, como no RFO, mas lendo o original de ~490 MB em streaming (`openpyxl` `read_only` e `iterparse`, sem abrir as imagens; pico de ~58 MB de memória). Extrator: `app/scripts/rfip_layout_extractor.py`; gerador: `app/scripts/build_rfip_templates.py`; saída em `templates/rfip/`; testes: `tests/test_rfip_templates.py` (planilha sintética).

```text
python -m app.scripts.build_rfip_templates --original "..\01_output-context\Relatório Fotográfico de Inspeção Predial - CORTINA D'AMPAREZZO - Versão Final.xlsx"
python -m app.scripts.build_rfip_templates
```

Sem `--original`, o comando regera os dois templates a partir do `layout.json` versionado. Pipeline: `app/services/report_generator/rfip_pipeline.py` (T18). Pendente: conferência visual do PDF (HT-09) e o mapeamento banco → contexto. Detalhes em `00_docs/backlog-auto/rfip-templates.md`.

## Validação de Ocorrências (BL-14, T08)

`app/services/ocorrencia_service.py` valida situação e classificação contra os enums (422), verifica a existência de sistema, subsistema e inspeção (404) e a coerência subsistema/sistema (422); o `PUT` não altera `inspecao_id` nem `seq_numero` e o filtro `sistema_id` é UUID. **Os testes `test_ocorrencias_regras.py` ainda não foram executados** (exigem PostgreSQL de `05_infra`). Ver `00_docs/backlog-auto/ocorrencias-correcoes.md`, DEC-34 e R-13.

## Endpoint de emissão do RFO (BL-13, T46)

`POST /api/v1/inspecoes/{inspecao_id}/relatorios/rfo` (só `auditor`, RN-18) monta o contexto (`montar_contexto_rfo`), gera PDF e DOCX, grava em `relatorios/{inspecao_id}/rfo-vNN.{pdf,docx}` e cria um novo `Relatorio` a cada emissão (`V01`, `V02`…). Resposta 201 sem chaves do storage; 403 (auxiliar/cliente), 404, 409 (não RFO ou foto ausente no storage), 422 (corpo com campo extra), 503 (WeasyPrint indisponível). Código em `app/api/v1/relatorios.py` e `app/services/relatorio_service.py` (renderizador e storage injetáveis). Os testes de integração (`tests/test_relatorios_rfo_api.py`) exigem o PostgreSQL de `05_infra/` e **não foram executados** na sessão de origem. Detalhes e pendências em [rfo-endpoint-emissao.md](../00_docs/backlog-auto/rfo-endpoint-emissao.md); decisões propostas em DEC-48. **T47–T51 (2026-11-11):** o contexto usa `legenda_para_relatorio` (só `legenda`, nunca a sugestão de IA); `emitir_rfo` valida `CAMPOS_OBRIGATORIOS_RFO` (`fiscal.crea`, `contrato.art_fiscalizacao`, `contrato.objeto`, `contrato.data_inicio`, `contrato.prazo_dias`) e responde 422 `rfo-contexto-incompleto` antes de gerar; migration `e5a1f0c2b7d4` cria `UNIQUE (inspecao_id, tipo, versao)` (aborta se houver duplicatas) — **o Alembic está com 2 heads (R-17); é preciso um merge antes do `upgrade head`**; `tests/test_portal_versoes_relatorio.py` cobre V01/V02 no Portal (1 xfail: falta campo `vigente`). Testes de banco/endpoint ainda não executados. Docs: [rfo-contexto-legenda.md](../00_docs/backlog-auto/rfo-contexto-legenda.md), [rfo-validacao-completude.md](../00_docs/backlog-auto/rfo-validacao-completude.md), [relatorio-unicidade.md](../00_docs/backlog-auto/relatorio-unicidade.md), [portal-versoes-relatorio.md](../00_docs/backlog-auto/portal-versoes-relatorio.md).

## Emissão genérica por tipo, conteúdo narrativo e legenda IA (T57–T68, 2026-11-11)

- **Emissão (T58, T60):** `relatorio_service.EMISSORES` registra um `Emissor` por tipo (RFO e VISTORIA_CAUTELAR). Rotas em `/api/v1/inspecoes/{id}`: `POST /relatorios/{tipo}` (auditor; 422 tipo não registrado, 409 tipo ≠ inspeção, 422 `{tipo}-contexto-incompleto`), `GET /relatorios` (versões, auditor e auxiliar) e `GET /relatorios/{relatorio_id}/download/{formato}` (URL pré-assinada). A rota `/relatorios/rfo` continua. Para registrar LTIP, RFIP ou Residencial, siga a seção «Como registrar um tipo novo» de [v1-emissao-generica.md](../00_docs/backlog-auto/v1-emissao-generica.md). A Cautelar usa `vistoria_cautelar_contexto.py` ([v1-vistoria-cautelar-contexto.md](../00_docs/backlog-auto/v1-vistoria-cautelar-contexto.md)).
- **Dados (T57):** enum `TipoServico` (`app/models/tipo_servico.py`); tabela `relatorio_conteudos` com `GET`/`PUT /inspecoes/{id}/conteudo/{tipo}` (PUT só auditor) e textos padrão em `report_generator/textos_padrao/`; colunas `titulo_profissional`, `qualificacoes` e `assinatura_storage_key` em `responsaveis` (sem rota de escrita ainda). Migration `a9c3e5f7b1d2`, head única; o banco de dev de `05_infra` precisa de `alembic upgrade head`. Detalhes em [v1-fundacao-dados.md](../00_docs/backlog-auto/v1-fundacao-dados.md).
- **Legenda IA (T63, T65):** `app/services/legenda_ia/deepseek.py` (cliente DeepSeek, modo texto por padrão) e `legenda_ia/contexto.py` (contexto minimizado). `LEGENDA_IA_PROVEDOR=fake|deepseek` (padrão `fake`, só em desenvolvimento e teste), `DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`, `DEEPSEEK_MODELO`, `DEEPSEEK_TIMEOUT_S`, `DEEPSEEK_ENVIAR_IMAGEM`. Nenhuma chamada real foi feita. Docs: [v1-legenda-ia-deepseek.md](../00_docs/backlog-auto/v1-legenda-ia-deepseek.md), [ia-contexto-legenda.md](../00_docs/backlog-auto/ia-contexto-legenda.md).
- **Parciais (T66, T67; R-18):** `app/scripts/seed_prompt_legenda.py` (prompt em [prompt-legenda-compacto.md](../00_docs/ia/prompt-legenda-compacto.md)) e `app/scripts/avaliar_legenda_ia.py` (harness `replay`/`live`) existem sem testes, sem golden set e sem Doc; não os use em produção.
- **Emissão de LTIP e RFIP (T59):** `report_generator/contexto_comum.py` (funções compartilhadas), `ltip_contexto.py` e `rfip_contexto.py`; os dois tipos estão em `EMISSORES`, sem rota nova (`POST /inspecoes/{id}/relatorios/{LTIP|RFIP}`). Só a 1ª foto de cada ocorrência entra. Doc: [v1-ltip-rfip-contexto.md](../00_docs/backlog-auto/v1-ltip-rfip-contexto.md).
- **Telemetria e cache da legenda IA (T68):** tabela `chamadas_ia` (migration `b8d4f2a6c1e7`; rode `alembic upgrade head`), `legenda_ia/telemetria.py`, `GET /api/v1/ia/uso?de=&ate=` (auditor) e as variáveis `LEGENDA_IA_CACHE_TTL_H` (720; `0` desliga), `DEEPSEEK_PRECO_ENTRADA_CACHE_HIT_USD`, `DEEPSEEK_PRECO_ENTRADA_CACHE_MISS_USD` e `DEEPSEEK_PRECO_SAIDA_USD` (USD por 1M de tokens; vazio = custo `null`). Doc: [ia-telemetria-cache.md](../00_docs/backlog-auto/ia-telemetria-cache.md).
- **RAG da legenda IA (T69; DEC-53 proposta):** migration `c6f2a8d4e1b9` (`pg_trgm`, tabela `trechos_conhecimento_ia` com `tsv` gerada, índice FTS parcial das legendas aprovadas; o downgrade só remove a extensão se a migration a criou), `legenda_ia/recuperacao.py` (`buscar`) e `legenda_ia/anonimizacao.py`. Rode `alembic upgrade head` e depois `python -m app.scripts.ingerir_conhecimento_ia` (`--dry-run`, `--amostras N`; lê só `00_docs/convertidos/*.md`, idempotente por hash). `LEGENDA_IA_RAG_ATIVO` (`true`) e `LEGENDA_IA_RAG_K` (`3`, 0–10); o harness aceita `--rag K` no modo live. Sem a ingestão, só as legendas aprovadas servem de exemplo. Doc: [ia-rag-fts.md](../00_docs/backlog-auto/ia-rag-fts.md).
- **Seed de demonstração (T64):** `python -m app.scripts.seed_demo` (`--reset`, `--limpar`) cria dados `DEMO` dos 5 tipos, usando `DEMO_SENHA` para o auditor `demo.auditor@example.com`. Precisa do gabarito de sistemas prediais (`00_docs/convertidos/RFO_INSPECAO.md` não está na imagem do container). Use um banco separado. Doc: [v1-amostras-ht09.md](../00_docs/backlog-auto/v1-amostras-ht09.md).
- **Testes:** no Windows, `passlib`×`bcrypt` e WeasyPrint impedem parte da suíte (R-19); rode em container descartável da imagem `05_infra-backend`.

## Pipeline de renderização do LTIP (BL-17, T05)

`app/services/report_generator/ltip_pipeline.py` preenche os templates de `templates/ltip/` e gera o PDF (WeasyPrint) e o DOCX (docxtpl), no mesmo desenho do `rfo_pipeline.py`. Funções: `normalizar_contexto`, `agrupar_por_sistema` (RN-11), `renderizar_html`, `gerar_pdf` e `gerar_docx`. O módulo não acessa o MinIO: quem chama entrega as fotos em bytes, indexadas por `storage_key`. O WeasyPrint é importado só dentro de `gerar_pdf`, então contexto, HTML e DOCX funcionam fora do container. Testes: `pytest tests/test_ltip_pipeline.py` (o teste de PDF é pulado onde o WeasyPrint não carrega). Pendências e campos do contexto em [ltip-pipeline.md](../00_docs/backlog-auto/ltip-pipeline.md). A revisão das regras de Ocorrências (T06, lacunas ainda não corrigidas) está em [revisao-regras-ocorrencias.md](../00_docs/projeto/revisao-regras-ocorrencias.md).

## Marca vetorizada no cabeçalho dos relatórios (DEC-30/ADR-16)

A marca da Garra só existe em JPEG, com o fundo chapado embutido no arquivo. Em vez de
imprimir esse retângulo creme no cabeçalho do relatório, os assets de `templates/assets/`
são **derivados por script** do JPEG oficial — mesmo princípio do `layout.json` acima.

```powershell
cd 04_backend
python -m app.scripts.build_brand_assets
```

| Arquivo | Papel |
|---|---|
| `app/scripts/bitmap_tracer.py` | Vetorizador: contornos da máscara → Douglas-Peucker → caminho SVG (reta nos cantos vivos, Bézier quadrática nas curvas da tipografia). Só depende do Pillow |
| `app/scripts/build_brand_assets.py` | CLI: detecta e remove o fundo, mede a paleta, separa símbolo e nome, grava os SVGs, o PNG transparente e `marca.json` |
| `templates/assets/logo-garra.svg` | Marca em 2 tons, fundo transparente — embutida no HTML/PDF por `rfo_pipeline` |
| `templates/assets/logo-garra.png` | Mesma marca em raster transparente — o formato Office não aceita SVG, então é o que vai embutido nos templates DOCX |
| `templates/assets/logo-garra-negativa.svg` / `logo-garra-simbolo.svg` | Variante branca (fundo escuro) e só o skyline |
| `templates/assets/marca.json` | Procedência: sha256 do JPEG de origem, recorte, paleta medida e tolerância |

> Os arquivos gerados trazem o cabeçalho "ARQUIVO GERADO" e não devem ser editados à
> mão. Se o cliente enviar uma marca nova, substituir o JPEG de origem e reexecutar o
> comando acima; depois regerar os templates DOCX (`build_rfo_templates`/`build_ltip_templates`),
> que embutem o PNG.

## Autenticação JWT + bcrypt (BL-06)

Entidade `Usuario` própria (`email`, `senha_hash`, `nome`, `ativo`) — não reaproveita `Responsavel` (ver DEC-15). Senha nunca é armazenada em texto plano (`passlib[bcrypt]`) nem retornada pela API. Token JWT (`python-jose`) assinado com `JWT_SECRET_KEY`, expiração configurável via `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` (padrão 60 min).

| Endpoint | Descrição |
|---|---|
| `POST /api/v1/auth/register` | Cria um novo usuário (uso interno da equipe, sem cadastro público). `201` ou `409` se o email já existir. |
| `POST /api/v1/auth/login` | Recebe `email`/`senha`, retorna `access_token` (JWT) + `token_type: bearer`. `401` se credenciais inválidas ou usuário inativo. |
| `GET /api/v1/auth/me` | Retorna os dados do usuário autenticado. Requer header `Authorization: Bearer <token>`. `401` se token ausente/inválido/expirado. |

Como testar (via `curl` ou `http://localhost:8000/docs`):

```powershell
# 1. Criar usuário
curl -X POST http://localhost:8000/api/v1/auth/register `
  -H "Content-Type: application/json" `
  -d '{"nome": "Seu Nome", "email": "voce@garra-engenharia.com.br", "senha": "senha-com-8-ou-mais-caracteres"}'

# 2. Login (retorna access_token)
curl -X POST http://localhost:8000/api/v1/auth/login `
  -H "Content-Type: application/json" `
  -d '{"email": "voce@garra-engenharia.com.br", "senha": "senha-com-8-ou-mais-caracteres"}'

# 3. Usar o token em rotas protegidas
curl http://localhost:8000/api/v1/auth/me -H "Authorization: Bearer <access_token>"
```

Para proteger um novo endpoint, use a dependency `get_current_user` (`app/api/deps.py`):

```python
from app.api.deps import get_current_user
from app.models import Usuario

@router.get("/rota-protegida")
async def rota(usuario_atual: Usuario = Depends(get_current_user)):
    ...
```

> **Nota de compatibilidade**: `bcrypt` está fixado em `<4.1` no `requirements.txt` — versões mais novas removeram o atributo `__about__` usado pelo `passlib` 1.7.4 para detectar o backend, quebrando o hashing com `ValueError` espúrio.
Storage service MinIO/S3 (BL-07)

Adapter Pattern (`00_docs/arquitetura.md` Seção 9.9): `StorageClient` (interface, `app/services/storage/base.py`) + `S3StorageClient` (implementação `boto3`, `app/services/storage/s3_client.py`), compatível com MinIO (dev) e AWS S3 (produção) sem alterar os serviços consumidores.

| Método | Descrição |
|---|---|
| `upload(key, file_bytes, content_type) -> str` | Envia o conteúdo para o bucket. Valida `key` não vazia, conteúdo não vazio e tamanho máximo de 25 MB por arquivo. |
| `download(key) -> bytes` | Retorna o conteúdo binário. Lança `ObjectNotFoundError` se a chave não existir. |
| `delete(key) -> None` | Remove o objeto (idempotente — não lança erro se a chave já não existir). |
| `generate_presigned_url(key, expires_in) -> str` | Gera URL de download temporária (padrão 15 minutos — RNF-07/ADR-02/Seção 10.1 A02). Nunca gera URLs públicas permanentes. |
| `exists(key) -> bool` | Checa existência por HEAD (404/NoSuchKey → `False`). Adicionado na T30. |
| `list_keys(prefix) -> list[str]` | Lista chaves por prefixo, com paginação. Adicionado na T30. |
| `list_objects(prefix) -> list[tuple[str, datetime]]` | Lista `(chave, LastModified)` com paginação; método não abstrato em `StorageClient` (levanta `NotImplementedError` em fakes que não o implementam). Adicionado na T32. |
| `listar_orfaos(chaves_registradas, prefix)` | Devolve as chaves do storage sem vínculo no banco; só leitura, nada é apagado (política em DEC-44, proposta). |

**Relatório de órfãos (T32, DEC-44 proposta)** — somente leitura, não apaga nada:

```bash
python -m app.scripts.relatorio_orfaos [--idade-minima-horas 24] [--prefixo fotos/]
```

Compara as `storage_key` vinculadas em `fotos` com os objetos do bucket e lista os sem vínculo com idade acima do limite (tabela com chave, `LastModified` UTC e idade em horas, mais a contagem). Exige PostgreSQL e MinIO no ar; nenhuma variável de ambiente nova. Detalhes: [storage-orfaos-relatorio.md](../00_docs/backlog-auto/storage-orfaos-relatorio.md).

**`origem` da foto (T31, DEC-43 proposta):** o payload de vínculo (`FotoVincularPayload`) aceita só `upload_manual`, `lightshot` ou `clipboard`; outro valor retorna 422. A leitura (`FotoRead`) não valida, então dados antigos continuam legíveis; sem CHECK no banco. Detalhes: [dec-43-origem-foto.md](../00_docs/backlog-auto/dec-43-origem-foto.md).

O bucket (`MINIO_BUCKET_NAME`) é criado automaticamente pelo próprio `S3StorageClient` na primeira instanciação, se ainda não existir (`head_bucket` + `create_bucket`, idempotente) — funciona mesmo sem o job `createbuckets` do `05_infra/docker-compose.yml`.

Variáveis de ambiente necessárias (já previstas em `.env.example`/`Settings`): `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`, `MINIO_BUCKET_NAME`, `MINIO_HOST`, `MINIO_API_PORT`, `MINIO_USE_SSL`.

Uso em um endpoint (dependency injetável, para permitir substituição por stub/fake nos testes):

```python
from fastapi import Depends
from app.services.storage import StorageClient, get_storage_client

@router.post("/fotos")
async def upload_foto(storage: StorageClient = Depends(get_storage_client)):
    key = storage.upload("visitas/123/foto1.jpg", conteudo, "image/jpeg")
    url = storage.generate_presigned_url(key, expires_in=900)
    ...
```

Como rodar os testes de integração (contra o MinIO real):

```powershell
cd 05_infra
docker compose up -d minio createbuckets

cd ..\04_backend
.venv\Scripts\Activate.ps1
pytest tests/test_storage.py -v
```

## 
## Como rodar os testes

```powershell
cd 04_backend
pip install -r requirements.txt
pytest
```

Os testes de `tests/test_models.py` exigem o PostgreSQL do `05_infra/docker-compose.yml` rodando (usam `JSONB`, específico do dialeto PostgreSQL) e a migration aplicada. Cada teste remove os registros que cria.

> **Ambiente (T01, T02 e T04, 2026-11-04):** use Python 3.12 (o 3.14 não instala o Pillow fixado). `requirements.txt` fixa `pytest>=9.1.1,<10.0` com `pytest-asyncio>=1.4.1,<1.5`; o 0.23.x não coleta com pytest 9, então valide qualquer troca com `python -m pytest --collect-only -q` (139 testes). Lint: `ruff check .` (configuração em [ruff.toml](ruff.toml)) retorna 0 erros; o ruff não está no `requirements.txt` (`pip install ruff` ou `uvx ruff`). A suíte de integração exige PostgreSQL com `alembic upgrade head`. Ver [pytest-compat.md](../00_docs/backlog-auto/pytest-compat.md), [ruff.md](../00_docs/backlog-auto/ruff.md), R-11 e DEC-31.

## Referências

- Stack, modelo ER, contratos de API, padrões de projeto e system design: [00_docs/arquitetura.md](../00_docs/arquitetura.md) (Seções 9-11)
- Regras de negócio: [00_docs/estudo-do-contexto.md](../00_docs/estudo-do-contexto.md)
- Documentos/templates de origem: [01_output-context/](../01_output-context/)
- Prompt de scaffold: [.github/prompts/15-scaffold-backend-fastapi.prompt.md](../.github/prompts/15-scaffold-backend-fastapi.prompt.md)

## Convenção de execução (DEC-09)

Comandos Python/uvicorn/alembic deste app são executados a partir desta pasta (`04_backend/`). O `Dockerfile` de build/runtime também vive aqui; o `docker-compose.yml` que o referencia está em [05_infra/](../05_infra/) (build context `../04_backend`).

## Revisões do lote T14–T17 (2026-11-04)

Sem código de produção alterado. Resultados e propostas de decisão (DEC-37 a DEC-40) nos Docs de `00_docs/backlog-auto/`:

| Tema | Doc | Testes novos | Situação |
|---|---|---|---|
| Lacunas do modelo para legendas por IA (BL-04 → BL-36..BL-39) | `modelagem-legendas-ia-lacunas.md` | — | só análise; resolvida em parte pela T22 (linha abaixo) |
| Regras de Visitas (BL-10, RN-01/RN-02) | `revisao-regras-visitas.md` | `tests/test_visitas_lacunas.py` | coletados, **não executados** (banco sem schema); devem falhar até a correção |
| Upload de fotos (BL-11, RF-05) | `revisao-regras-fotos.md` | `tests/test_fotos_lacunas.py` | coletados, **não executados** (sem PostgreSQL/MinIO); a lacuna mais grave é a `storage_key` vinda do cliente |
| Benchmark dos pipelines finais (BL-22) | `benchmark-pipelines-finais.md` | — | RFO e Cautelar atendem RNF-06; Residencial no limite; **LTIP viola** |

Para rodar os testes de lacuna: `docker compose up -d` em `05_infra/`, `alembic upgrade head` e `pytest tests/test_visitas_lacunas.py tests/test_fotos_lacunas.py` em `04_backend/`.

## Correções do lote T18–T21 (2026-11-04)

| Tema | Doc | O que mudou | Situação |
|---|---|---|---|
| Pipeline do RFIP (BL-12) | `rfip-pipeline.md` | `app/services/report_generator/rfip_pipeline.py` (`normalizar_contexto`, `renderizar_html`, `gerar_pdf`, `gerar_docx`), `tests/test_rfip_pipeline.py` | 12 testes; PDF pulado sem WeasyPrint; falta mapeamento banco → contexto |
| Upload de fotos (BL-11) | `fotos-correcoes.md` | `storage_key` validada e conferida no bucket, 409 de chave duplicada, `exif_transpose`, validação de `origem`/`ordem`/`legenda`, `PUT` parcial, `DELETE /fotos/upload`, teto de 50 Mpx | 44 testes passaram; faltam `UNIQUE(storage_key)` e URL pré-assinada |
| PDF do LTIP (RNF-06) | `ltip-desempenho.md` | Template com linhas de fichas no lugar do flex único e fotos por `url_fetcher` | 72,1 → 11,6 s (239 fotos); 154,5 → 19,3 s (~200 páginas) |
| Visitas (BL-10) | `visitas-correcoes.md` | Migration `e5a1c3f7b9d2` (UNIQUE `(inspecao_id, seq_numero)` e `(inspecao_id, data)`; aborta se houver data duplicada), data ≤ hoje, só RFO, `PUT` parcial, `GET /visitas/{id}` e CRUD de mão de obra e medições | L15 em `xfail` (DEC-27); `alembic upgrade head` pendente em produção |
| Legendas por IA, modelo de dados (BL-36) | `legenda-ia-modelo.md` | Migration `f7c2a9d4e6b1` (`prompts_ia` + 11 colunas em `fotos`, 5 CHECKs, `downgrade()`), `PromptIA`, `LegendaIARead`; sem adapter nem endpoint | 24 testes em `test_legenda_ia_modelo.py`; `alembic upgrade head` pendente nos ambientes; L12, L13, L22 aguardam o provedor (B-04) |
| Legendas por IA, serviço de prompts e contrato do cliente (BL-37) | `legenda-ia-servico.md` | `app/services/prompt_ia_service.py` (versões imutáveis, hash, ativação única) e `app/services/legenda_ia/` (`LegendaIAClient`, `FakeLegendaIAClient`) | 8 testes em `test_prompt_ia_service.py`; sem cliente de provedor real (B-04) |
| Legenda aprovada no relatório (BL-38, DP-9) | `legenda-relatorio.md` | `report_generator/legenda_foto.py`, aplicado só ao `rfo_pipeline.py` (PDF e DOCX) | 8 testes em `test_legenda_relatorio.py`; LTIP e RFIP na T36 e as duas vistorias na T37 (linhas abaixo) |
| Legendas por IA, endpoints (BL-34) | `legenda-ia-endpoints.md` | `POST /api/v1/fotos/{id}/legenda-ia/gerar` e `PUT /api/v1/fotos/{id}` com `aprovar_legenda_ia`; dependência `get_legenda_ia_client` (503 até haver adapter, B-04) | 14 testes em `test_legenda_ia_endpoints.py`; adapter concreto pendente |
| `url_fetcher` de fotos em RFO, Cautelar e Residencial (DEC-41 B) | `pipelines-url-fetcher.md` | `report_generator/foto_fetcher.py` (só `garra-foto:<n>` registrado e `data:`); `renderizar_html` segue com data URI | 18 passed, 2 pulados (sem GTK); PDF real e medição não executados |
| Revisão de segurança de legenda IA, fotos e visitas (BL-23, T29) | `seguranca-legenda-ia.md` | só revisão e `tests/test_seguranca_legenda_ia.py`; 9 achados SEG-IA abertos (sem limite de taxa/custo em `gerar`, aprovação mantida ao regerar/editar, IDOR entre contratos) | 8 passaram, 9 não rodaram (MinIO indisponível) |
| Legendas por IA, aprovação e limites (DEC-42, T33/T35) | `legenda-ia-aprovacao-auditor.md`, `legenda-ia-limites.md` | `PUT /fotos/{id}` com `aprovar_legenda_ia` só para `auditor` (403 ao `auxiliar`); editar/regerar foto aprovada volta a `rascunho`. `app/services/legenda_ia/` (`limites.py`, `saneamento.py`, `contrato.py`): 429 em `gerar` por usuário e por foto, saída truncada em 500 caracteres e saneada, `legenda_bruta` delimitada. 8 variáveis `LEGENDA_IA_*` (já em `.env.example`; ainda não repassadas pelo compose/`render.yaml`) | 53 testes de limites passaram; os testes com PostgreSQL não rodaram. Sem `Retry-After` no header; janela em memória por processo |
| Legenda aprovada nas Vistorias Cautelar e Residencial (BL-38, T37) | `legenda-relatorio-vistorias.md` | `normalizar_contexto` dos dois pipelines usa `legenda_para_relatorio`: só `legenda` é impressa, nunca `legenda_ia_sugerida` (PDF e DOCX). Testes de PDF puladas sem WeasyPrint/GTK |
| Legenda aprovada no LTIP e no RFIP (BL-38, T36) | `legenda-relatorio-ltip-rfip.md` | `_normalizar_ocorrencia` do `ltip_pipeline.py` passa cada foto por `legenda_para_relatorio`; o `rfip_pipeline.py` herda, sem edição. Hoje nenhum template imprime legenda de foto | `test_legenda_relatorio_ltip_rfip.py`: 42 passed, 5 skipped (sem WeasyPrint/GTK) com os testes de pipeline; PDF não executado |

A suíte completa do backend não foi validada numa única execução: o venv do checkout principal estava sem `greenlet` funcional, houve interrupção por falta de memória e testes assíncronos falham com `RuntimeError: There is no current event loop` quando um teste usa `asyncio.run`. `ruff check .` ainda acusa erros preexistentes fora das áreas tocadas.

> **Lint (T39, 2026-11-07; T43, 2026-11-10):** `ruff check .` (ruff 0.15.1, com `ruff.toml`) sai com 0 achados e o CI fixa `ruff==0.15.1`; o passo segue não bloqueante até a aprovação da DEC-46. Plano em DEC-46 e em [ci-lint-bloqueante.md](../00_docs/backlog-auto/ci-lint-bloqueante.md).
