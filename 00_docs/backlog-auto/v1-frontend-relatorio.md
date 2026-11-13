# V1-06 · Tela de emissão e download de relatórios (T62)

Papel: Engenheiro Frontend. Data: 2026-11-11/12. Branch: `worktree-backlog-T62`. Backend não alterado.

> **Nota de ambiente:** o worktree nasceu numa base antiga (`14ead2f`), sem as T57/T58. A branch não tinha commits próprios e `14ead2f` é ancestral de `main`, então fiz `git merge --ff-only main` (até `b8e953a`) antes de começar. Nada foi reescrito.

## O que mudou

| Arquivo | Mudança |
|---|---|
| `03_frontend/lib/types.ts` | `Responsavel` ganha `titulo_profissional`, `qualificacoes`, `assinatura_storage_key`; novo `ResponsavelInput`. Novos `ConteudoDados` (espelho de `app/schemas/relatorio_conteudo.py`), `RelatorioConteudo`, `RelatorioVersao`, `RelatorioEmitido`, `FormatoRelatorio`, `RelatorioDownload` (= `PortalDownload`). |
| `03_frontend/lib/api-client.ts` | Helpers tipados: `relatorios.listar/emitir/download`, `conteudo.obter/salvar`, `responsaveis.listar/criar`, `uploadImagem(file)` (`POST /fotos/upload`, multipart). `emitir` e `conteudo.*` mandam o tipo em minúsculas (a API normaliza; `rfo` minúsculo cai no handler BL-13, com o mesmo resultado). |
| `03_frontend/app/inspecoes/[id]/relatorio/page.tsx` | Placeholder `UnderConstruction` substituído pela tela. O tipo vem de `GET /inspecoes/{id}` (`tipo.trim().toUpperCase()`); depois `GET /inspecoes/{id}/conteudo/{tipo}`. Link "Voltar ao contrato" usa `contrato_id`. |
| `03_frontend/components/relatorio/rotulos.ts` (novo) | Nome legível dos 5 tipos e rótulos/agrupamento das chaves de `dados.textos` para LTIP (7 chaves), Vistoria Cautelar (31, em 12 seções) e Vistoria Residencial (31, `s1`…`s12`, em 12 seções). Títulos copiados de `04_backend/templates/vistoria_*/layout.json`, `vistoria_residencial_template.html.j2` e `ltip_pipeline.SECOES_TEXTO`. As **chaves** vêm sempre da API; chave desconhecida cai no grupo "Outros textos" com rótulo derivado do nome. |
| `03_frontend/components/relatorio/conteudo-form.tsx` (novo) | "Dados da emissão" (data e local de emissão; unidade para residencial; datas das vistorias, lista com adicionar/remover, para cautelar e residencial; parecer para cautelar; "Incluir resumo" para RFIP) e "Textos do relatório" (um `<textarea>` por chave, agrupados em `<details>` colapsáveis, fechados por padrão). Salvar com estado "Salvando...", confirmação "Textos salvos em …" (`aria-live`), aviso de alterações não salvas e erro da API (`ApiErrorAlert`). Auxiliar vê tudo em modo leitura, sem botão de salvar. |
| `03_frontend/components/relatorio/emissao-versoes.tsx` (novo) | "Emitir nova versão" só para auditor, com spinner, botão desabilitado e texto "pode levar algumas dezenas de segundos"; ao concluir mostra "Versão Vxx emitida." e recarrega a lista. 422 → alerta com a lista "Campos faltantes" (`errors[].field`: `message`); outros erros → `ApiErrorAlert`. Tabela de versões (versão, emitida em, status, botões PDF/DOCX com `aria-label` "Baixar PDF da versão V01"); download pelo padrão do portal (URL pré-assinada aberta em nova aba). Em tela < 640 px, data e status vão sob a versão e as colunas próprias somem, para a tabela caber sem rolagem. |
| `03_frontend/app/responsaveis/page.tsx`, `responsavel-form.tsx` (novos) | Não havia tela de responsáveis no frontend. Lista (`GET /responsaveis`) em cartões e cadastro em diálogo (só auditor): nome, tipo, CREA, CPF/CNPJ, telefone, e-mail e o bloco "Assinatura nos laudos" (título profissional ≤ 120, qualificações em lista de até 20 itens ≤ 300, upload da imagem de assinatura com pré-visualização). |
| `03_frontend/components/layout/nav-items.ts` | Item de menu "Responsáveis" (fora da lista "Toca" da tarefa; uma linha, para a tela ser alcançável). |
| `03_frontend/e2e/relatorio.spec.ts` (novo) | 9 testes Playwright com a API mockada por `page.route` (ver abaixo). |

## Comportamentos e decisões de implementação

- **Salvar = PUT completo.** O `PUT /conteudo/{tipo}` substitui o conteúdo salvo, então o payload parte de todo o `dados` que a API devolveu (inclusive `metodologia_corretiva` e `fundamentacao_tecnica`, que a tela não edita) e sobrescreve só textos e campos simples do tipo. Consequência: ao salvar a primeira vez, todos os textos padrão passam a ficar gravados como texto do auditor (mudança futura de padrão no backend não os atualiza). Testes (2) e (8) cobrem isso.
- **Parágrafos.** Na tela, os parágrafos de uma chave aparecem separados por linha em branco; ao salvar, cada linha não vazia vira um parágrafo (mesma regra de `em_paragrafos` do backend). Texto vazio envia `[]`, que remove a seção (contrato da T57).
- Campos vazios de texto curto (local, unidade, parecer) vão como `null`, não `""`.
- O botão de emissão avisa quando há textos não salvos (a emissão usa o conteúdo salvo); não salva automaticamente.
- Ocultar botões por papel é só usabilidade (`useUsuarioAtual`, `GET /auth/me`, mesmo mecanismo da T54); a autorização continua no backend (`require_auditor`).

## Lacunas encontradas (backend, para o fechamento de lote)

1. **Não há rota de edição de responsável.** `app/api/v1/responsaveis.py` tem só `GET ""`, `POST ""` e `GET /{id}`; o schema `ResponsavelUpdate` existe sem rota (já apontado na T57, proposta 5). Por isso a tela só **cadastra** e lista; não dá para acrescentar título/qualificações/assinatura a um responsável já existente. Precisa de `PUT/PATCH /responsaveis/{id}` (auditor) para a edição.
2. **Upload da assinatura reaproveita `POST /fotos/upload`.** Funciona (devolve `storage_key` + URL pré-assinada; PNG e JPEG são revalidados com Pillow, PNG mantém transparência), mas a chave fica sob o prefixo `fotos/` e não é uma `Foto`: o relatório de órfãos (`app/scripts/relatorio_orfaos.py`, DEC-44) vai listá-la como órfã. O backend também não valida `assinatura_storage_key` contra o storage. Proposta: rota própria (`POST /responsaveis/{id}/assinatura`, prefixo `assinaturas/`) ou incluir `responsaveis.assinatura_storage_key` no conjunto de chaves vinculadas do script de órfãos.
3. **Só o RFO é emitível hoje** (T58). Para LTIP/RFIP/vistorias a API responde 422 `tipo-relatorio-nao-registrado`; a tela mostra esse 422 como lista de "campos faltantes" (`tipo: Use um dos tipos disponíveis.`). Fica correto quando os emissores dos outros tipos forem registrados.
4. **Download em iOS/Safari.** Como no portal, a URL é aberta com `window.open` depois de um `await`; navegadores móveis podem bloquear como pop-up. Se ocorrer no teste com o celular, trocar por `window.location.assign(url)` (com `Content-Disposition: attachment` no storage) nas duas telas.

## Testes e comandos (a partir de `03_frontend`)

- `npm ci` → ok.
- `npm run lint` → `✔ No ESLint warnings or errors`.
- `npm run build` → `✓ Compiled successfully`, 11/11 páginas; `/inspecoes/[id]/relatorio` 8.88 kB, `/responsaveis` 7.29 kB.
- Playwright 1.62.1 (chromium), contra `next start -p 3100` deste worktree, sem backend:
  `E2E_BASE_URL=http://localhost:3100 npx playwright test e2e/relatorio.spec.ts e2e/portal-perfil.spec.ts e2e/portal.spec.ts`
  → **20 passed, 1 failed** (29 s).
  - `relatorio.spec.ts`: **9/9**.
    1. carrega os textos padrão do tipo da inspeção (LTIP), agrupados, colapsados e com rótulos legíveis;
    2. salva: o `PUT` leva a chave editada em parágrafos, as demais chaves inalteradas, data e local; não leva campos de outros tipos; mostra "Textos salvos em";
    3. auditor emite: botão "Emitindo..." desabilitado e aviso de demora enquanto o `POST .../relatorios/ltip` não responde; depois "Versão V02 emitida." e a V02 no topo da tabela;
    4. auxiliar não vê "Emitir nova versão" nem "Salvar textos"; vê versões e textos (readonly);
    5. 422 `ltip-contexto-incompleto` → lista "Campos faltantes" com os 2 campos; botão volta a ficar habilitado;
    6. download chama `/api/v1/inspecoes/{id}/relatorios/{relatorio_id}/download/docx` e `/pdf` e abre as URLs pré-assinadas devolvidas;
    7. vistoria cautelar em 360×640 (5,5"): parecer, datas das vistorias, sem campo de unidade, rótulo longo 9.8; `scrollWidth ≤ clientWidth` na página **e** no contêiner da tabela de versões;
    8. vistoria residencial: unidade e datas vão no `PUT` e `fundamentacao_tecnica` (não editada) é preservada;
    9. responsáveis (360×640): cadastro com título, 2 qualificações e upload multipart da assinatura; o `POST /responsaveis` leva `assinatura_storage_key` devolvida pelo upload.
  - `portal-perfil.spec.ts`: 4/4.
  - `portal.spec.ts`: 7/8. A falha é `(e) perfil auditor ... a UI não bloqueia /portal (lacuna)`, **anterior a esta tarefa e já registrada na T54** (`portal-perfil-ui.md`): o teste ainda espera o comportamento antigo (auditor fica em `/portal` e vê o 403), mas desde a T54 o auditor é redirecionado a `/dashboard`. Não editei `portal.spec.ts`.
- Primeira rodada: 3 falhas de seletor no próprio spec novo (`getByLabel("Data da vistoria 1")` casava também com o botão "Remover data da vistoria 1"), corrigidas com `exact: true`; e a tabela de versões rolava por dentro a 360 px, corrigido no componente (colunas data/status escondidas abaixo de `sm`, padding do card `px-4` no celular).
- Backend não foi tocado, então `pytest`/`ruff` não se aplicam a esta tarefa.

## Para o fechamento de lote (00_docs)

- `03_frontend/README.md`: telas `/inspecoes/[id]/relatorio` e `/responsaveis`, helpers novos de `lib/api-client.ts`, e o spec `e2e/relatorio.spec.ts` (mockado, roda sem backend).
- `00_docs/projeto/riscos.md` / backlog: lacunas 1 (rota de edição de responsável) e 2 (upload de assinatura via `/fotos/upload` aparece como órfão).
- Reescrever o teste `(e)` de `portal.spec.ts` para o comportamento da T54 (pendência herdada).
- Proposta de decisão: o conteúdo do relatório é sempre enviado completo pelo frontend (PUT substitui), o que congela os textos padrão no primeiro salvamento; se o produto quiser que padrões novos cheguem a inspeções já salvas, o frontend teria que enviar só as chaves alteradas (precisaria de um indicador de "padrão vs. salvo" por chave na API).
