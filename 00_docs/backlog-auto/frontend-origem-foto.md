# BL-31 — Origem da foto no vínculo (frontend)

Tarefa: corrigir o valor de `origem` enviado ao vincular foto no `FotoUpload` (`03_frontend/components/foto-upload.tsx`), achado na T26 (BL-35).

## 1. Valores aceitos pelo backend (verificado no código)

| Verificação | Resultado |
|---|---|
| `04_backend/app/schemas/foto.py` (`FotoVincularPayload.origem`) | `origem: str`, **sem enum, sem validador**. Qualquer string é aceita. |
| `04_backend/app/models/foto.py:30` | `origem: Mapped[str] = mapped_column(String, nullable=False)`. Sem `CheckConstraint`. |
| Migration inicial (`04_backend/alembic/versions/c22d4029c062_*`) | `sa.Column('origem', sa.String(), nullable=False)`. Sem restrição. |
| `04_backend/app/api/v1/fotos.py` | Só define `POST /fotos/upload-clipboard` (base64, "integração Lightshot"). Não traduz nem valida `origem`. |
| Lista `upload_manual\|lightshot\|clipboard` | **Não existe no código.** Grep em todo o backend não encontrou. |
| Seed `04_backend/app/scripts/seed_benchmark_rfo.py:209` | Usa `origem="upload_manual"`. É o único valor "manual" usado no backend. |
| DEC-39 em `00_docs/projeto/decisoes.md` | **Não encontrado.** O último registro é DEC-30. |

**Conclusão:** a hipótese de 422 no vínculo por `origem: "upload"` **não é confirmada pelo código**. O backend aceita `"upload"`, porque não valida o valor. O problema real é de contrato: o frontend enviava um rótulo interno que não corresponde ao valor usado no backend (`upload_manual`). O enum que o backend deveria impor ainda não existe no código.

## 2. Clipboard → `lightshot`

Mantido. O código do frontend (`foto-upload.tsx`, cabeçalho e `handleClipboardPaste`) e o docstring de `fotos.py:58` tratam o clipboard como captura Lightshot. Portanto `clipboard → lightshot` é coerente com a intenção do código. O backend não impõe isso: ele grava a string que o cliente envia.

## 3. Alterações

- `03_frontend/lib/types.ts`: `OrigemFoto = "upload_manual" | "lightshot" | "clipboard"`, único tipo de origem do frontend. Removidos `"upload"` e `"camera"`. Não existe nenhum envio com `"camera"` no código.
- `03_frontend/components/foto-upload.tsx`:
  - `linkFoto(upload, origem: OrigemFoto)`, em vez de `string`.
  - A origem interna do editor (`"upload" | "clipboard"`) é convertida só na chamada ao backend: `clipboard → lightshot`, `upload → upload_manual`.
- `03_frontend/e2e/foto-origem.spec.ts` (novo): mocka toda a API com `page.route`, intercepta `POST /visitas/{id}/fotos` e verifica que `origem` é `"upload_manual"`, e não `"upload"`.
  - Obs.: `e2e/legenda-ia.spec.ts` citado na tarefa **não existe** no repositório. O estilo seguido foi o de `e2e/rfo.spec.ts` e `e2e/helpers.ts`.
  - Ao contrário dos fluxos RFO/LTIP, este spec não precisa do backend real nem do `docker compose`.
- Backend: **não alterado**.

## 4. Resultados

Executados em `03_frontend` (Windows, Node via `npm ci`):

| Comando | Resultado |
|---|---|
| `npm run lint` | OK, "No ESLint warnings or errors" |
| `npm run build` | OK (exit 0) |
| `npx tsc --noEmit -p .` | OK (exit 0), também após o spec novo |
| `npx playwright test e2e/foto-origem.spec.ts` | **1 passed** (chromium, 2.0s). Frontend em `npm run start -p 3000` com build atual. |

## 5. Não executado / limites

- **Não rodei o spec contra o código antigo** para demonstrar que ele falha antes da correção. A asserção é a que falharia com `"upload"`, mas isso é inferência, não execução.
- Fluxo de clipboard (`navigator.clipboard.read`) não coberto pelo spec.
- Backend: `pytest` e `ruff` não rodados, porque o backend não foi alterado. PostgreSQL de `localhost:5433` não foi verificado.
- Os demais specs (`rfo.spec.ts`, `ltip.spec.ts`) não rodados: exigem a stack completa.

## 6. Decisão proposta (não registrada em `decisoes.md`)

**Proposta DEC-XX (para o integrador):** definir no backend um enum fechado para `origem` de `Foto` (por exemplo `Literal["upload_manual", "lightshot", "clipboard"]` em `FotoVincularPayload`), e alinhar o seed com ele. Hoje o contrato existe só no frontend e a validação é ausente. A decisão ficaria a cargo do integrador. O backend está fora do escopo do BL-31.

## 7. Arquivos alterados

- `03_frontend/lib/types.ts`
- `03_frontend/components/foto-upload.tsx`
- `03_frontend/e2e/foto-origem.spec.ts` (novo)
- `00_docs/backlog-auto/frontend-origem-foto.md` (este doc)
