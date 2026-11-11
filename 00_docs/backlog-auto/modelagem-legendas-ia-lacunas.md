# Lacunas de modelagem para legendas assistidas por IA (BL-04 — revisão de integração)

- **Tarefa:** revisão de integração do BL-04 para o fluxo de legendas por IA (RF-15, RN-16, RN-17, DEC-21, ADR-12), preparando BL-34 a BL-39.
- **Tipo:** análise e documentação. **Nenhum código, migration ou teste foi alterado.**
- **Testes:** não há código alterado, portanto **não houve testes a rodar** (`pytest`, `ruff`, `npm` não foram executados). O checklist de `.github/pull_request_template.md` não se aplica a esta entrega.
- **Ambiente:** worktree `worktree-backlog-T14`, sem push.
- **Documentos de gestão não editados:** `backlog-tarefas.md`, `backlog-kanban.md`, `status.md`, `decisoes.md`, `riscos.md`. Propostas de decisão estão na seção 5, para o integrador.

---

## 0. Resumo

1. **O código está atrás da documentação.** `arquitetura.md` §3 (ER) e ADR-12 já descrevem os campos de legenda IA e a tabela `prompts_ia`, mas nenhum existe em `04_backend/app/models/foto.py`, nem em migrations (a head atual é `d3b7c9e4f1a2`, BL-15).
2. **A maior parte da modelagem independe do provedor de LLM** (ver seção 2). Só a rastreabilidade do provedor/modelo, a política de retenção e o campo de geração dependem do provedor (B-04, lacuna #13).
3. **Há três lacunas de integridade no código atual** que afetam RN-16/RN-17 e devem entrar em BL-36/BL-38:
   - `PUT /fotos/{id}` grava `legenda` sem registrar autoria nem aprovação; o `_usuario` do endpoint é descartado.
   - `foto_repository.update` só grava `legenda` se não for `None` (`04_backend/app/repositories/foto_repository.py:44`), então não há como limpar uma legenda.
   - Não há filtro de status: os consumidores de `foto.legenda` leem o texto direto (ver 1.6).

---

## 1. Inventário do que existe hoje

### 1.1 Modelo `Foto` (`04_backend/app/models/foto.py`)

| Campo | Tipo SQLAlchemy | Linha | Observação |
|---|---|---|---|
| `id` | `UUID` PK | 20 | |
| `ocorrencia_id` | `UUID` FK `ocorrencias.id`, nullable | 21-23 | |
| `visita_id` | `UUID` FK `visitas.id`, nullable | 24-26 | |
| `storage_key` | `String`, not null | 27 | chave no `StorageClient` |
| `url_publica` | `String`, nullable | 28 | |
| `legenda` | `Text`, nullable | 29 | único campo de texto de legenda |
| `origem` | `String`, not null | 30 | sem enum; livre |
| `ordem` | `Integer`, nullable | 31 | |
| `created_at` | `DateTime(tz)`, server default | 32 | |
| `criado_por_id` | `UUID` FK `usuarios.id`, nullable | 34-36 | autoria de campo (RN-18/DEC-27) |

Relacionamentos: `ocorrencia` (linha 38), `visita` (linha 39).

**Ausente no modelo:** `legenda_bruta`, `legenda_ia_sugerida`, `nivel_certeza_ia`, `status_validacao_ia`, `alertas_ia`, `pendencias_ia`, `prompt_ia_id`, `aprovado_por_id`, `aprovado_em`.

**Ausente no código:** modelo `PromptIA` / tabela `prompts_ia` (grep em `04_backend/app` e `04_backend/alembic` sem resultado).

### 1.2 Schemas (`04_backend/app/schemas/foto.py`)

| Schema | Linha | Campos relevantes |
|---|---|---|
| `FotoBase` | 8 | `ocorrencia_id`, `visita_id`, `storage_key`, `url_publica`, `legenda`, `origem`, `ordem` |
| `FotoRead` | 22 | herda `FotoBase`; `id`, `created_at`, `criado_por_id` (somente leitura) |
| `FotoUploadResponse` | 31 | `storage_key`, `url` |
| `FotoVincularPayload` | 49 | `storage_key`, `legenda`, `ordem`, `origem` |
| `FotoUpdatePayload` | 62 | apenas `legenda` e `ordem` |

Não há campo de status, de sugestão, nem de aprovação em nenhum schema.

### 1.3 Endpoints (`04_backend/app/api/v1/fotos.py`)

| Endpoint | Linha | Papel | Autoria/aprovação |
|---|---|---|---|
| `POST /fotos/upload` | 37-48 | upload multipart | — |
| `POST /fotos/upload-clipboard` | 51-63 | upload base64 | — |
| `POST /ocorrencias/{id}/fotos` | 66-85 | vincula foto + legenda | grava `criado_por_id=usuario.id` |
| `POST /visitas/{id}/fotos` | 88-102 | vincula foto + legenda | grava `criado_por_id=usuario.id` |
| `PUT /fotos/{id}` | 104-111 | atualiza legenda/ordem | **`_usuario` ignorado** (linha 108); sem autoria |
| `DELETE /fotos/{id}` | 114-123 | remove | — |

`atualizar_foto` (linha 104) chama `foto_service.atualizar(db, foto_id, legenda=..., ordem=...)` sem passar o usuário.

### 1.4 Serviço (`04_backend/app/services/foto_service.py`)

- `atualizar(db, foto_id, *, legenda, ordem)` (linha 101): sem parâmetro de usuário; delega a `foto_repository.update`.
- `vincular_a_ocorrencia` (linha 63) e `vincular_a_visita` (linha 83) aceitam `criado_por_id`.

### 1.5 Repositório (`04_backend/app/repositories/foto_repository.py`)

- `create` (linha 19): aceita `legenda`, `criado_por_id`.
- `update(db, foto, *, legenda, ordem)` (linha 43): `if legenda is not None: foto.legenda = legenda` (linha 44). **Não é possível apagar a legenda.**

### 1.6 Consumidores de `legenda` (sem filtro de status)

| Arquivo:linha | Uso |
|---|---|
| `04_backend/app/scripts/benchmark_relatorio_geracao.py:71` | monta contexto `{"legenda": foto.legenda}` |
| `04_backend/app/scripts/build_rfo_templates.py:238` | template Jinja `{% if foto.legenda %}` |

Nenhum dos dois verifica status de aprovação. Não foi inspecionado `app/services/report_generator/` além da busca por `.legenda`; a verificação de RN-16 no pipeline de relatório precisa ser feita quando BL-38 for implementado.

### 1.7 Storage (`04_backend/app/services/storage/base.py`)

- `StorageClient(ABC)`: linha 11. Métodos `upload` (15), `download` (29), `delete` (37), `generate_presigned_url` (45). É o Adapter de referência (ADR-02 / Seção 9.9).
- Legendas são **texto**: ficam em PostgreSQL, não no storage (RNF-07 reserva o storage para binários). O storage só entra se a transcrição de áudio for guardada como arquivo (não previsto em RF-15).

### 1.8 Migrations (`04_backend/alembic/versions/`)

- Head atual: `d3b7c9e4f1a2` (`prioridade_sugerida_sobrescrita_bl_15.py`, revisa `7c1a4e0b93d5`).
- `c22d4029c062` cria `fotos` (linha 154) com `legenda` Text (linha 160).
- `7c1a4e0b93d5` adiciona `criado_por_id` em `visitas`, `ocorrencias` e `fotos`.
- Nenhuma migration toca `legenda_*`, `prompts_ia`, `aprovado_*`.

### 1.9 Especificação já escrita (não implementada)

- `00_docs/arquitetura.md` §3, entidade `FOTO` (linhas 231-250): inclui `legenda_bruta`, `legenda_ia_sugerida`, `nivel_certeza_ia`, `status_validacao_ia`, `alertas_ia` (jsonb), `pendencias_ia` (jsonb), `prompt_ia_id` FK, `aprovado_por_id` FK, `aprovado_em`.
- `arquitetura.md` §3, entidade `PROMPT_IA` (linhas 252-259): `id`, `nome`, `versao`, `conteudo`, `ativo`, `created_at`.
- `arquitetura.md` linha 288: `PROMPT_IA ||--o{ FOTO : "gerou sugestão (opcional)"`. **Inconsistência menor:** ADR-12 diz que `prompt_ia_id` referencia a versão *ativa* usada, não que "gerou" a sugestão. Ajustar o rótulo do ER em BL-36.
- `estudo-do-contexto.md` RF-15 (linha 174), RN-16 (150), RN-17 (151).
- `decisoes.md` DEC-21 (linha 315), DEC-19 (285).

---

## 2. Lacunas para RF-15 / RN-16 / RN-17

Legenda da marcação: **[I]** independe do provedor; **[P]** depende do provedor (B-04, lacuna #13).

| # | Requisito | Lacuna | Estado hoje | Marca | Tarefa sugerida |
|---|---|---|---|---|---|
| L1 | RF-15 | Campo para a anotação/transcrição bruta do auditor | não existe (`legenda_bruta`) | **[I]** | BL-36 |
| L2 | RF-15 | Campo para a sugestão da IA, separado de `legenda` | não existe (`legenda_ia_sugerida`) | **[I]** | BL-36 |
| L3 | RF-15 | Nível de certeza (4 níveis do prompt do cliente: constatação direta, indício técnico, hipótese técnica, causa comprovada) | não existe (`nivel_certeza_ia`) | **[I]** (enum vem do prompt do cliente, não do provedor) | BL-36 |
| L4 | RN-16 | Status `rascunho` / `aprovada` para a legenda gerada | não existe (`status_validacao_ia`) | **[I]** | BL-36 |
| L5 | RF-15 | Pendências e alertas estruturados retornados pelo prompt | não existem (`pendencias_ia`, `alertas_ia`, jsonb) | **[I]** (estrutura definida pelo JSON de saída do prompt do cliente) | BL-36 |
| L6 | RN-17 | Tabela `prompts_ia` com versão do prompt-sistema | não existe | **[I]** | BL-36 |
| L7 | RN-17 | FK `Foto.prompt_ia_id` para a versão usada | não existe | **[I]** | BL-36 |
| L8 | RN-17 | `aprovado_por_id` e `aprovado_em` | não existem | **[I]** | BL-36 |
| L9 | RN-17 | Quem **editou** a sugestão (além de quem aprovou) | não existe; RN-17 pede "aprovou/editou" | **[I]** (decisão, ver DP-3) | BL-36 / BL-38 |
| L10 | RN-17 | Snapshot do conteúdo do prompt usado, para não depender do registro vivo de `prompts_ia` | não previsto | **[I]** (ver DP-2) | BL-36 |
| L11 | RN-17 | Data/hora da geração da sugestão (além da aprovação) | não existe | **[I]** | BL-36 |
| L12 | RN-17 | Provedor e modelo que geraram a sugestão | não existem | **[P]** (valores vêm do adapter concreto) | BL-34 (colunas em BL-36) |
| L13 | RN-17 / OWASP A02 | Política de retenção/privacidade dos dados enviados ao provedor (campos, logs, retenção) | sem definição; lacuna #13 | **[P]** | decisão antes de BL-34 |
| L14 | RN-16 | Bloqueio de inclusão no relatório sem aprovação | sem enforcement; consumidores em 1.6 leem `legenda` direto | **[I]** (regra no pipeline de relatório) | BL-38 |
| L15 | RN-16 / RN-17 | `PUT /fotos/{id}` não registra autoria/aprovação; `_usuario` é descartado (`fotos.py:108`) | defeito atual | **[I]** | BL-34 / BL-38 |
| L16 | RN-16 | Não é possível limpar `legenda` (`foto_repository.py:44`) | defeito atual; afeta rejeitar sugestão | **[I]** | BL-38 |
| L17 | RF-15 | A sugestão nunca sobrescreve `legenda` automaticamente | regra, ainda sem campo que a separe | **[I]** (resolvida por L2) | BL-36 |
| L18 | RF-15 | Campos `origem` livres (sem enum) — distinguir foto com/sem legenda IA não é preciso | ok para o escopo | **[I]** | — (apenas registrar) |
| L19 | DEC-21 | Índice de unicidade "uma versão ativa por nome" em `prompts_ia` | não previsto | **[I]** | BL-36 |
| L20 | ER | Rótulo de `PROMPT_IA → FOTO` em `arquitetura.md:288` | inconsistente com ADR-12 | **[I]** (documental) | BL-36 |
| L21 | RF-15 | Schemas de `FotoRead` / `FotoUpdatePayload` não expõem status, sugestão nem aprovação | não existe | **[I]** | BL-34 |
| L22 | RN-16 | Endpoint `POST /fotos/{id}/legenda-ia/gerar` não existe | não existe | **[P]** (depende do adapter) | BL-34 |

**Resumo:** 20 lacunas independem do provedor (L1-L11, L14-L21), 3 dependem (L12, L13, L22). Quase toda a modelagem pode ser feita antes da escolha de B-04.

---

## 3. Esboço do Adapter `LegendaIAClient` e cliente fake

Pseudo-código Python (não é código de produção). Segue o padrão de `StorageClient` (ABC) com um `Protocol`, para que o fake não herde de nada. Os nomes de campo seguem o ER de `arquitetura.md` §3.

```python
# 04_backend/app/services/ia_legenda/base.py  (ESBOÇO)
from dataclasses import dataclass, field
from typing import Literal, Protocol

# Níveis de certeza do prompt-sistema do cliente (RF-15). Valores ASCII em código.
NivelCerteza = Literal[
    "constatacao_direta",
    "indicio_tecnico",
    "hipotese_tecnica",
    "causa_comprovada",
]


@dataclass(frozen=True)
class EntradaLegenda:
    """O que o sistema envia ao provedor. Nunca inclui dados que o prompt não exige."""
    texto_bruto: str                 # anotação de campo ou transcrição (-> legenda_bruta)
    contexto: dict[str, str]         # dados da ocorrência/visita necessários ao prompt
    prompt_nome: str                 # prompts_ia.nome
    prompt_versao: str               # prompts_ia.versao
    prompt_conteudo: str             # prompts_ia.conteudo (snapshot enviado)


@dataclass(frozen=True)
class SugestaoLegenda:
    """Retorno normalizado. Nunca é gravado em Foto.legenda: vai para legenda_ia_sugerida."""
    legenda: str                     # -> legenda_ia_sugerida
    nivel_certeza: NivelCerteza      # -> nivel_certeza_ia
    alertas: list[str] = field(default_factory=list)      # -> alertas_ia (jsonb)
    pendencias: list[str] = field(default_factory=list)   # -> pendencias_ia (jsonb)
    # Preenchidos pela implementação concreta (L12) — dependem de B-04:
    provedor: str = ""
    modelo: str = ""


class ErroLegendaIA(Exception):
    """Falha do provedor (timeout, cota, resposta fora do JSON esperado)."""


class LegendaIAClient(Protocol):
    async def gerar(self, entrada: EntradaLegenda) -> SugestaoLegenda:
        """Envia a entrada ao LLM com o prompt-sistema e devolve a sugestão estruturada.

        Lança ErroLegendaIA se a resposta não puder ser normalizada.
        Não persiste nada: quem persiste é o serviço (BL-34).
        """
        ...
```

```python
# 04_backend/tests/fakes/legenda_ia_fake.py  (ESBOÇO — para testes; não usa rede)
class FakeLegendaIAClient:
    """Implementa LegendaIAClient sem provedor real. Permite testar BL-34 a BL-39 antes de B-04."""

    def __init__(
        self,
        resposta: SugestaoLegenda | None = None,
        erro: Exception | None = None,
    ) -> None:
        self._resposta = resposta
        self._erro = erro
        self.chamadas: list[EntradaLegenda] = []   # para asserts: o que foi enviado

    async def gerar(self, entrada: EntradaLegenda) -> SugestaoLegenda:
        self.chamadas.append(entrada)
        if self._erro is not None:
            raise self._erro
        if self._resposta is not None:
            return self._resposta
        # Padrão determinístico: sugestão derivada do texto, sem inventar dados.
        return SugestaoLegenda(
            legenda=f"[fake] {entrada.texto_bruto[:200]}",
            nivel_certeza="indicio_tecnico",
            alertas=[],
            pendencias=["fake: revisão humana obrigatória"],
            provedor="fake",
            modelo="fake-1",
        )
```

Pontos de atenção do desenho:
- `SugestaoLegenda` e `EntradaLegenda` são imutáveis: a sugestão não pode ser alterada por engano antes de ser persistida como rascunho.
- O cliente **não** tem acesso à sessão do banco. Quem grava é o serviço, que impõe RN-16 (nunca grava em `legenda` a partir do adapter).
- Para BL-34, `get_legenda_ia_client()` (fábrica por configuração) só será implementado depois de B-04; até lá, a fábrica retorna o fake em testes e levanta erro explícito fora deles.

---

## 4. Ordem sugerida de implementação

| Ordem | Tarefa | Depende de | Independe de B-04? | Motivo |
|---|---|---|---|---|
| 1 | **BL-36** — extensão da modelagem (`prompts_ia`, colunas em `fotos`, migration com `downgrade()`) | BL-04 | **sim** (exceto colunas `provedor_ia`/`modelo_ia`, que podem ficar nulas até BL-34) | Base de tudo; sem dependência de provedor. |
| 2 | **BL-37** — rastreio do artefato gerado e metadados de prompt/status | BL-36 | sim | Consolida L8-L11 e L19 na camada de repositório/serviço. |
| 3 | **BL-34** — backend: Adapter, serviço, endpoints `gerar` e `PUT` com aprovação | BL-36, BL-37; **B-04 para a implementação concreta** | parcial: contrato, serviço e testes com fake sim; provedor real não | Pode ser implementado e testado com `FakeLegendaIAClient` antes da escolha. Só o adapter concreto espera B-04. |
| 4 | **BL-38** — integração upload/edição com geração | BL-36, BL-37 (e BL-34 para o fluxo completo) | não totalmente | Trata L14 (bloqueio no relatório) e L16 (limpar legenda). |
| 5 | **BL-39** — integração do editor de anotação com o fluxo de aprovação | BL-38 | depende de BL-38 | Fluxo de aprovação após anotação (ADR-10 não muda). |
| 6 | **BL-35** — frontend: botão, campo editável, alertas, confirmação | BL-34 | depende de BL-34 (pode usar o fake via mock de API) | Último por depender do contrato de API de BL-34. |

Nota de divergência: `backlog-tarefas.md` marca BL-35 como dependente de BL-34 e BL-36 a BL-39 como 🔴 "depende da definição do provedor". Esta ordem é compatível com isso, mas **BL-36 e BL-37 não precisam esperar B-04** (o próprio status de BL-36 cita a definição do provedor como dependência, e isso é mais restritivo do que o necessário). Propõe-se rever essa marcação (DP-6).

---

## 5. Decisões propostas (texto, não editadas em `decisoes.md`)

**DP-1 — Estados de `status_validacao_ia` (RN-16).** Valores fechados: `rascunho` (sugestão gerada, não aprovada) e `aprovada` (confirmada ou editada por um usuário da equipe). `NULL` significa "sem sugestão". Nenhum outro estado é usado na v1.0. Um relatório só pode incluir a legenda com `status_validacao_ia = 'aprovada'`.

**DP-2 — Snapshot do prompt usado (RN-17).** Além de `prompt_ia_id`, gravar `prompt_conteudo_hash` (SHA-256 do `conteudo` enviado) na geração. Assim a rastreabilidade sobrevive a uma eventual edição do registro de `prompts_ia`. Regra: versões de `prompts_ia` são imutáveis (uma nova versão é uma nova linha; `ativo` alterna por nome).

**DP-3 — Autoria da aprovação e da edição (RN-17).** `aprovado_por_id` e `aprovado_em` são preenchidos **somente** no `PUT` que confirma a legenda como `aprovada`, com o usuário autenticado (nunca do payload, mesmo padrão de `criado_por_id`, RN-18). Quem edita a sugestão antes de aprovar é o mesmo usuário da aprovação na v1.0; a sugestão original permanece em `legenda_ia_sugerida`, então a diferença entre sugerido e final é reconstruível. Se o cliente exigir trilha de edições separada, abrir nova decisão.

**DP-4 — Escrita da sugestão nunca toca em `legenda` (RF-15).** O endpoint `gerar` grava somente em `legenda_ia_sugerida`, `nivel_certeza_ia`, `alertas_ia`, `pendencias_ia`, `status_validacao_ia='rascunho'`, `prompt_ia_id`, `legenda_bruta` e a data da geração. `legenda` só muda no `PUT` de aprovação.

**DP-5 — Correção de defeitos do `PUT /fotos/{id}`.** Passar o usuário autenticado ao serviço (`fotos.py:108` hoje descarta `_usuario`) e permitir limpar a legenda, com `legenda: null` explícito distinto de "campo ausente" (`PATCH` semântico, ou campo `limpar_legenda: bool`). Escolha da forma fica para BL-38; a proposta é `model_fields_set` do Pydantic.

**DP-6 — Revisar dependência de BL-36 e BL-37 em B-04.** Propor que `backlog-tarefas.md` deixe de marcar BL-36 e BL-37 como bloqueadas por B-04: a modelagem e o rastreio independem do provedor (ver seção 2). Só BL-34 (adapter concreto, colunas `provedor_ia`/`modelo_ia` com valores reais), a retenção (L13) e BL-38/39 com fluxo real permanecem dependentes.

**DP-7 — Sem armazenamento de áudio.** RF-15 usa transcrição ou anotação em texto. Não guardar arquivo de áudio no storage na v1.0; a transcrição fica em `legenda_bruta`. Se o cliente pedir o áudio original, abrir nova decisão (impacto em RNF-07 e armazenamento).

**DP-8 — Ajuste de rótulo no ER.** Trocar em `arquitetura.md:288` o rótulo "gerou sugestão (opcional)" por "versão ativa usada na geração (opcional)", alinhado a ADR-12.

---

## 6. Próximos passos para o integrador

1. Revisar DP-1 a DP-8 e registrar as aceitas em `decisoes.md` (não feito aqui).
2. Confirmar com o cliente a política de retenção e o provedor (L12, L13), que continuam bloqueando BL-34 em produção.
3. Atualizar o status de BL-04 e a marcação de BL-36/BL-37 em `backlog-tarefas.md` e `backlog-kanban.md` no fechamento do lote.
4. Iniciar BL-36 quando autorizado. A migration deve ter `downgrade()`, e a tabela `prompts_ia` deve ter unicidade parcial de `ativo` por `nome`.

---

## 7. Registro de fatos verificados (comandos)

- Leitura dos requisitos: `00_docs/estudo-do-contexto.md` (RF-15 linha 174, RN-16 linha 150, RN-17 linha 151).
- Leitura das decisões: `00_docs/projeto/decisoes.md` (DEC-19 linha 285, DEC-21 linha 315).
- Leitura da arquitetura: `00_docs/arquitetura.md` §3 (ER FOTO linhas 231-250, PROMPT_IA linhas 252-259, relação linha 288), ADR-12 (linha 704), tabela de API (linhas 345-355).
- Código lido: `04_backend/app/models/foto.py`, `04_backend/app/schemas/foto.py`, `04_backend/app/api/v1/fotos.py`, `04_backend/app/services/foto_service.py`, `04_backend/app/repositories/foto_repository.py`, `04_backend/app/services/storage/base.py`.
- Busca por consumidores: `grep -rn "\.legenda" 04_backend/app --include=*.py`.
- Busca por `prompts_ia|legenda_ia|aprovado_por` em `04_backend` (`*.py`): nenhum resultado.
- Migrations lidas: `04_backend/alembic/versions/` (head `d3b7c9e4f1a2`).
- Nenhum comando de build, lint ou teste foi executado (não há código alterado).
