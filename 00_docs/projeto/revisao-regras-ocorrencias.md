# Revisão das regras de negócio e enums de Ocorrência (BL-14)

Escopo: backend de Ocorrência (RF-04, RN-03, RN-05, RN-10, DEC-27, DEC-29). BL-15 (prioridade derivada) e BL-16 (intervalo 0–5) não foram refeitas. Frontend, models e migrations não foram tocados.

## 1. Regras aplicáveis e se o backend as impõe

Referências: `S` = `04_backend/app/services/ocorrencia_service.py`, `A` = `04_backend/app/api/v1/ocorrencias.py`, `R` = `04_backend/app/repositories/ocorrencia_repository.py`.

| # | Regra | Imposta? | Onde / observação |
|---|---|---|---|
| 1 | Sistema obrigatório (RF-04) | Sim (schema) | `schemas/ocorrencia.py:15` (campo não opcional). O `if not dados.sistema_id` em `S:89` é código morto. |
| 2 | Situação ∈ {CONFORME, NAO_CONFORME} (RN-05) | **Não** | `S:91` só testa vazio; qualquer string é aceita. **Lacuna L1** |
| 3 | Classificação ∈ {ANOMALIA, FALHA, ANOMALIA_FALHA, NAO_SE_APLICA} (RN-05) | **Não** | `S:93` só testa vazio. **L2** |
| 4 | Tipo de anomalia obrigatório se ANOMALIA/ANOMALIA_FALHA | Sim | `S:95-96` |
| 5 | Tipo de falha obrigatório se FALHA/ANOMALIA_FALHA | Sim | `S:97-98` |
| 6 | Grau de risco ∈ {MINIMO, MEDIO, CRITICO} | Sim | `S:99-100` (também rejeita nulo) |
| 7 | Prioridade 0–5 (RN-05, BL-16) | Sim | `S:101-103` |
| 8 | Prioridade sugerida pelo grau (CRITICO=5, MEDIO=3, MINIMO=1) e sobrescrita rastreada (RN-04, BL-15) | Sim | `S:13`, `S:106-133` |
| 9 | "Não se Aplica" / Conforme ⇒ prioridade 0 (RN-05/RN-10, DEC-29) | Sim, como sugestão | `S:113-114`. Sobrescrita explícita é permitida (RN-04). |
| 10 | Sistema existe | **Não** | Sem consulta; FK violada vira erro 500. **L3** |
| 11 | Subsistema existe e pertence ao sistema informado (RF-04) | **Não** | Nenhuma checagem (`R:68-71`). Aceita subsistema de outro sistema. **L4** |
| 12 | Inspeção da URL existe | **Não** | `A:53` repassa o id direto; inexistente vira 500 (FK). **L5** |
| 13 | `PUT` não altera a Inspeção nem o `seq_numero` | **Não** | `R:105-106` aplica `model_dump()` inteiro: sobrescreve `inspecao_id` (move a ocorrência para outra inspeção) e `seq_numero` (com `None` viola NOT NULL). **L6** — o corpo deveria ser ignorado nesses campos. |
| 14 | Filtro `sistema_id` da listagem é UUID válido | **Não** | `A:30` é `str`; `R:34` faz `uuid.UUID(...)` ⇒ `ValueError`/500. **L7** |
| 15 | Autoria `criado_por_id` do usuário autenticado (RN-18, DEC-27) | Sim | `A:53-55`; `OcorrenciaRead` não aceita do payload (`schemas/ocorrencia.py:40`) |
| 16 | Permissões: auditor e auxiliar escrevem; cliente não (DEC-27) | Sim | `require_equipe` em todos os endpoints (`A:33,50,62,73,83`) |
| 17 | Auxiliar não pode **excluir** ocorrência | Não definido | DEC-27 lista criar/editar; `DELETE` (`A:79-86`) usa `require_equipe`. Ver proposta P2. |
| 18 | Ocorrência só em Inspeção LTIP/Vistoria (RF-04/RN-03) | **Não** | Os testes e o dashboard usam ocorrências em Inspeção `RFO`; ver proposta P1. |
| 19 | Pelo menos uma Foto por Ocorrência (RN-03) | Não, no CRUD | A foto é anexada depois (`POST /ocorrencias/{id}/fotos`); só pode ser exigida na emissão do relatório, fora deste escopo. A UI sinaliza (`page.tsx:254`). |
| 20 | Faixa de `gut_*` | Não definido | Sem limite nas seções lidas (CMM/GUT, RN-04/05 não fixam escala); registrado, não corrigido. |
| 21 | Todo sistema avaliado individualmente / ausência = "Não se Aplica" (RN-10) | Parcial | Registro de "Não se Aplica" funciona (regra 9); a cobertura de sistemas não avaliados é só visual no frontend (`page.tsx:153`). |

## 2. Lacunas reais e correções

Testes escritos primeiro em `04_backend/tests/test_ocorrencias_regras.py` (marcados `test_lacuna_*`). **As correções no service/schema/endpoint não foram aplicadas**: o PostgreSQL não estava disponível, então não seria possível ver o teste ficar verde. Correção mínima planejada:

- L1/L2: constantes `_SITUACOES`/`_CLASSIFICACOES` em `ocorrencia_service` e `DomainError` com sufixos `ocorrencia-situacao-invalida` / `ocorrencia-classificacao-invalida` em `_validar_payload`.
- L3/L4/L5: `criar` e `atualizar` consultam inspeção, sistema e subsistema (`NotFoundError` com `inspecao-nao-encontrada`, `sistema-nao-encontrado`, `subsistema-nao-encontrado`) e comparam `subsistema.sistema_id` com `sistema_id` (`DomainError` `ocorrencia-subsistema-incoerente`, 422).
- L6: em `ocorrencia_repository.update`, usar `model_dump(exclude={"inspecao_id", "seq_numero"})`.
- L7: tipar `sistema_id: uuid.UUID | None` em `A:30` (FastAPI devolve 422).

## 3. Propostas (não implementadas; decisão do dono)

- **P1** — Restringir ocorrências a Inspeção LTIP/Vistoria (RF-04). Hoje fixtures e dashboard usam RFO; mudar quebraria testes existentes e exige decisão. Ainda não existe enum de `Inspecao.tipo` (`schemas/inspecao.py:12` é `str`).
- **P2** — Decidir se auxiliar pode excluir ocorrência (DEC-27 é omissa).
- **P3** — Se quiser enums reais no schema (Pydantic `Literal`/`Enum`), a resposta de erro passa de RFC 7807 do domínio para o 422 padrão do FastAPI; por isso L1/L2 ficam no service. Persistir como enum no banco exigiria migration (não feita).
- **P4** — `prioridade_ajustada_*` é regravado a cada `PUT` enquanto a prioridade diferir da sugestão, mesmo sem mudança do valor (perde a autoria original). Avaliar só atualizar quando o valor mudar.
- **P5** — Os testes de `PUT` existentes (`test_ocorrencias_prioridade.py`) enviam `seq_numero` nulo; se passavam, vale confirmar como o NOT NULL não disparou (L6 não verificada com banco).

## 4. Comandos e resultado

Ambiente: sem Docker (`docker: command not found`) e `localhost:5433` sem resposta (timeout); `pytest_asyncio` também não está instalado no Python atual.

| Comando (em `04_backend`) | Resultado |
|---|---|
| `pytest tests/test_ocorrencias_dashboard.py tests/test_ocorrencias_prioridade.py tests/test_ocorrencias_regras.py` | **Não rodou**: `ModuleNotFoundError: No module named 'pytest_asyncio'` ao carregar `tests/conftest.py`, e o PostgreSQL de `05_infra/docker-compose.yml` não está no ar. Nenhum resultado de teste é afirmado aqui. |
| `python -m py_compile tests/test_ocorrencias_regras.py` | OK |
| `ruff check tests/test_ocorrencias_regras.py` | OK após `--fix` de ordenação de imports |
| `ruff check .` | 214 erros **pré-existentes** em outros arquivos (nenhum no arquivo novo; antes do `--fix` eram 215) |

Para validar: subir `docker compose up -d` em `05_infra`, instalar dependências de dev e rodar o `pytest` acima; os testes `test_lacuna_*` devem falhar antes das correções e passar depois.
