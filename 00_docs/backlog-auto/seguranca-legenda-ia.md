# Revisão de segurança — legenda por IA, fotos e visitas (BL-23, 2ª passada)

Data: 2026-11-05 · Escopo: só revisão, nenhum código de produção alterado. Base: relatório anterior
`00_docs/projeto/revisao-seguranca-owasp.md` (2026-08-07), RN-16, RN-17, RN-18, DEC-27, DEC-37.
Testes: `04_backend/tests/test_seguranca_legenda_ia.py`.

## Resultado da execução dos testes

- **Rodaram e passaram (8):** `test_cliente_nao_acessa_visitas_nem_itens` e as 7 variantes de
  `test_descartar_upload_recusa_chave_fora_do_padrao` (usam PostgreSQL em `localhost:5433` e storage falso).
- **Não rodaram (9):** os demais (3 de regressão e 6 `xfail`, que precisam de foto com objeto no storage).
  A porta `localhost:9000` respondeu `403 Forbidden` no `HeadBucket`, ou seja, o MinIO de `05_infra`
  não estava no ar com as credenciais do projeto (`docker` não existe nesta máquina). Os resultados
  esperados abaixo vêm da leitura do código e **não foram confirmados por execução**.
- `ruff check tests/test_seguranca_legenda_ia.py`: sem erros. `pytest` completo e `ruff` do projeto inteiro não foram rodados.
- Antes disso o worktree estava 137 commits atrás de `main` e sem o código de legenda IA; foi atualizado por fast-forward.

## O que está correto (sem achado)

| Item | Evidência |
|---|---|
| Perfil `cliente` sem acesso | Todos os endpoints de foto, legenda IA e visitas usam `require_equipe` (`fotos.py`, `visitas.py`); teste de 12 rotas devolve 403. |
| 401 antes de 503 | `usuario` é resolvido antes de `get_legenda_ia_client` (`fotos.py:127-135`); `get_legenda_ia_client` sem adapter responde 503 RFC 7807 sem detalhe interno. |
| Aprovador vem do token | `foto_service.atualizar` grava `aprovado_por_id = usuario.id` e `aprovado_em` no servidor; `FotoUpdatePayload` não tem esses campos (cobertos por `test_legenda_ia_endpoints.py`). |
| `storage_key` | `_STORAGE_KEY_PATTERN` com `fullmatch` e UUID minúsculo bloqueia `../`, caminho absoluto, outro prefixo, `.svg`, maiúsculas. `DELETE /fotos/upload` recusa chave já vinculada. |
| Limite de entrada | `legenda_bruta` ≤ 5000, `legenda` ≤ 500 no payload. |
| Erros | Exceção do provedor cai em `_handle_unexpected_error`: corpo genérico, stack só no log. Não há `logger` em `foto_service.py`, então nem chave de storage nem legenda são logadas por esse caminho. |
| Prompt | `prompt_ia_service` não tem rota HTTP; versões imutáveis; o hash vai para a foto. |

## Achados

| ID | Sev. | Achado | Evidência | Correção sugerida | Teste |
|---|---|---|---|---|---|
| SEG-IA-01 | Alta | Sem limite de taxa nem de custo em `POST /fotos/{id}/legenda-ia/gerar`. Qualquer `auxiliar`/`auditor` (ou token roubado) dispara chamadas pagas ao LLM sem teto; cada chamada baixa a imagem inteira do storage. O único limitador (`app/core/rate_limit.py`) cobre só login. | `fotos.py:127-141`; `rate_limit.py` | Limite por usuário (ex.: N/min e N/dia) e por foto, 429 com `Retry-After`; orçamento diário no adapter; mover o contador para Redis se houver mais de um worker (ADR-06). Fazer antes do adapter real (BL-34). | `test_gerar_tem_limite_de_taxa_por_usuario` (xfail, não rodou) |
| SEG-IA-02 | Média | Regerar sugestão em foto já `aprovada` volta o status para `rascunho`, mas mantém `aprovado_por_id` e `aprovado_em` antigos. A trilha de RN-17 passa a dizer que alguém aprovou um texto que não aprovou. | `foto_service.gerar_legenda_ia` não zera os campos | Zerar `aprovado_por_id`/`aprovado_em` ao regerar, ou recusar regerar foto aprovada sem pedido explícito. | `test_regerar_apos_aprovar_limpa_aprovacao_anterior` (xfail, não rodou) |
| SEG-IA-03 | Média | DP-10 (já proposta em DEC-37): `PUT` que muda `legenda` de foto aprovada, sem a flag, mantém `aprovada` e o aprovador anterior; o texto do relatório deixa de ser o que o responsável aprovou (RN-16). | `foto_service.atualizar` só mexe no status dentro do `if aprovar_legenda_ia` | Adotar DP-10: editar legenda aprovada volta a `rascunho` (ou vira nova aprovação do editor). | `test_editar_legenda_aprovada_nao_atribui_edicao_ao_aprovador_anterior` (xfail, não rodou) |
| SEG-IA-04 | Média | Saída do LLM gravada sem limite nem saneamento. `legenda_ia_sugerida` é `Text` e `alertas_ia`/`pendencias_ia` são JSONB sem tamanho; na aprovação a sugestão vira `legenda` sem passar pelo limite de 500 do payload. Resposta longa ou maliciosa (injeção de prompt) estoura o layout do relatório e infla o banco. | `foto_service.py:176-211`, `models/foto.py:77-80`; `atualizar` usa `foto.legenda_ia_sugerida` direto | Validar a saída no serviço: legenda ≤ 500, no máx. N alertas/pendências com tamanho limitado, remover controle/HTML; recusar com 502 se exceder. Escapar no gerador de relatório. | `test_sugestao_longa_do_llm_nao_burla_limite_da_legenda` (xfail, não rodou) |
| SEG-IA-05 | Média | Auxiliar aprova legenda. RN-16/RF-15 exigem aprovação do «profissional responsável/habilitado»; RN-18 diz que o auxiliar «não assume responsabilidade técnica». Hoje `require_equipe` deixa o auxiliar aprovar e o `test_auxiliar_gera_e_aprova` consagra isso. | `fotos.py:114-124` | **Decisão do dono** (ver abaixo). Se for só auditor: 403 quando `aprovar_legenda_ia` vier de auxiliar. | `test_auxiliar_nao_aprova_legenda_ia` (xfail, não rodou) |
| SEG-IA-06 | Baixa | Auxiliar remove foto de legenda aprovada (`DELETE /fotos/{id}`) sem bloqueio nem registro de quem removeu. | `fotos.py:158-168` | Bloquear (409) ou exigir auditor quando `status_validacao_ia = 'aprovada'`; registrar remoção em log de auditoria. | `test_auxiliar_nao_remove_foto_com_legenda_aprovada` (xfail, não rodou) |
| SEG-IA-07 | Média (risco aberto) | IDOR entre contratos: nenhuma rota de foto/visita confere vínculo usuário↔contrato. Qualquer usuário da equipe lê, edita, aprova, gera e remove fotos e itens de visita de qualquer contrato. É L15 de DEC-27, ainda sem decisão. Com IA, soma custo (SEG-IA-01) a acesso cruzado. | `foto_service.*` e `visita_service.*` buscam só por id | Decidir L15; se adotado, filtrar por contrato no repositório e responder 404. | Sem teste: não há modelo de vínculo para afirmar o comportamento. Registrar em `riscos.md` no fechamento de lote. |
| SEG-IA-08 | Baixa (a confirmar no adapter) | Injeção de prompt: `legenda_bruta` (texto livre, até 5000) chega ao cliente de IA como argumento separado do prompt. O contrato `LegendaIAClient` não obriga o adapter a delimitar a entrada do usuário. | `legenda_ia/__init__.py`; `gerar_legenda(imagem, prompt, legenda_bruta)` | No adapter (BL-34): mensagem de sistema só com o prompt versionado, texto do usuário em mensagem separada e delimitada, saída em formato estruturado validado (ver SEG-IA-04), sem ferramentas nem URLs. Revisar o adapter antes de ligar. | — |
| SEG-IA-09 | Baixa | URL pré-assinada: `FotoRead.url` expira em 15 min (`_PRESIGNED_URL_EXPIRES_IN_SECONDS`), adequado; mas o link vai para qualquer usuário da equipe (ver SEG-IA-07) e a imagem é enviada a provedor externo (R-10, retenção). | `foto_service.py:23` | Sem ação além de SEG-IA-07 e da política de retenção antes de produção. | — |

Não há achado em visitas/mão de obra/medições além de SEG-IA-07: RBAC por `require_equipe` em todas as rotas (testado).

## Decisões propostas (para o fechamento de lote; não editei `decisoes.md`)

1. **DEC-37 DP-11 (proposta):** quem pode aprovar legenda IA. Recomendação: só `auditor` (RN-16, RN-18); auxiliar gera e edita rascunho. Depende do dono, pois muda um teste e a UI (T26 mostra o painel ao auxiliar).
2. **DEC-37 DP-12 (proposta):** regerar/editar legenda aprovada invalida a aprovação (zera `aprovado_*`, volta a `rascunho`); resolve SEG-IA-02 e SEG-IA-03 e fecha DP-10.
3. **Proposta:** limite de taxa e custo em `gerar` e validação da saída do LLM antes de BL-34 ligar o adapter real (bloqueio de produção, ao lado de R-10).
4. **Risco a registrar:** L15/DEC-27 (SEG-IA-07) sem imposição.

## Próximos passos

- Subir MinIO e PostgreSQL de `05_infra` e rodar `pytest tests/test_seguranca_legenda_ia.py` (esperado: 11 passam, 6 xfail). Se algum `xfail` passar sem correção, `strict` falha e o diagnóstico acima estava errado.
- Ao corrigir cada achado, remover a marca `xfail` do teste correspondente.

## Andamento (fechamento do lote T33–T35, 2026-11-06)

- **Corrigidos no código:** SEG-IA-02, SEG-IA-03 e SEG-IA-05 (T33, backend; T34, painel); SEG-IA-01 e SEG-IA-04 (T35, por usuário e por foto; sem orçamento global, e o contador é por processo).
- **Mitigado:** SEG-IA-08 só no contrato (delimitação de `legenda_bruta`); a revisão do adapter real continua necessária.
- **Abertos:** SEG-IA-06, SEG-IA-07 (L15/DEC-27) e SEG-IA-09.
- As marcas `xfail` de `test_seguranca_legenda_ia.py` estão desatualizadas e precisam sair (ver `legenda-ia-limites.md` §6, pendência 5).
