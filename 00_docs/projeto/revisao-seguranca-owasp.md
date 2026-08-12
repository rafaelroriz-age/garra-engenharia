---
title: Revisão de Segurança OWASP Top 10 — Sistema de Automação de Relatórios Prediais
type: gestao
status: concluido
owner: Garra Engenharia
related:
  - 00_docs/arquitetura.md
  - 00_docs/projeto/backlog-tarefas.md
  - 00_docs/projeto/riscos.md
tags: [seguranca, owasp, rnf-05, bl-23]
last_updated: 2026-08-07
---

# Revisão de Segurança OWASP Top 10:2021 (BL-23, RNF-05)

Revisão de código do backend (`04_backend`) e do frontend (`03_frontend`) contra as 10 categorias do OWASP Top 10:2021, usando como referência o mapeamento já previsto em [arquitetura.md Seção 10.1](../arquitetura.md).

**Escopo auditado:** autenticação/autorização, upload de arquivos, acesso a dados, configuração de produção, tratamento de erros e cabeçalhos HTTP. Fora de escopo: pentest externo, análise dinâmica (DAST) e revisão do pipeline de geração de relatórios (BL-12/BL-13, ainda bloqueado por B-02).

---

## Resumo dos achados

| # | Categoria | Achado | Severidade | Situação |
|---|---|---|---|---|
| S-01 | A01 — Broken Access Control | `POST /auth/register` era **público**: qualquer pessoa com a URL da API criava uma conta `auditor` com acesso total de escrita | **Alta** | ✅ Corrigido |
| S-02 | A07 — Auth Failures | Nenhum limite de tentativas de login (força bruta ilimitada contra `POST /auth/login`) | **Alta** | ✅ Corrigido |
| S-03 | A05 — Security Misconfiguration | `/docs`, `/redoc` e `/openapi.json` expostos em qualquer ambiente, revelando toda a superfície da API | **Média** | ✅ Corrigido |
| S-04 | A05 — Security Misconfiguration | `JWT_SECRET_KEY` com default `"changeme"` — subir produção com o default assinaria tokens forjáveis | **Alta** | ✅ Corrigido |
| S-05 | A05 — Security Misconfiguration | Respostas da API sem cabeçalhos defensivos (`nosniff`, `X-Frame-Options`, CSP, HSTS) | **Baixa** | ✅ Corrigido |
| S-06 | A09 — Logging Failures | Sem `request_id` para correlacionar requisição ↔ log ↔ erro (previsto em ADR-08, nunca implementado) | **Média** | ✅ Corrigido |
| S-07 | A01 — Broken Access Control | Portal do Cliente poderia aceitar `edificacao_id`/`relatorio_id` de outro contratante | **Alta** | ✅ Mitigado por design (BL-32/BL-33) |
| S-08 | A02 — Cryptographic Failures | Download de relatório do Portal expõe objeto do storage | **Média** | ✅ Mitigado por design (URL pré-assinada, 15 min) |
| S-09 | A03 — Injection | Queries dinâmicas de listagem/dashboard | — | ✅ Conforme (SQLAlchemy com bind params, zero SQL concatenado) |
| S-10 | A08 — Data Integrity Failures | Upload de imagem maliciosa disfarçada de foto | — | ✅ Conforme (magic bytes + recodificação Pillow, BL-11) |
| S-11 | A10 — SSRF | Endpoint que busque URL fornecida pelo cliente | — | ✅ Conforme (nenhum endpoint aceita URL externa) |
| S-12 | A01 — Broken Access Control | Endpoints de auditor não filtram por proprietário (qualquer auditor vê todos os contratos) | **Baixa** | ⚠️ Aceito conscientemente — ver "Riscos residuais" |
| S-13 | A06 — Vulnerable Components | Bumps major de dependência pendentes (Next 16, React 19, ESLint 10, Node 25) | **Baixa** | ⚠️ Pendente (decisão consciente, DEC-22) |
| S-14 | A07 — Auth Failures | Sem refresh token nem revogação de token emitido | **Baixa** | ⚠️ Aceito para a v1.0 |

---

## Correções aplicadas

### S-01 — Registro de usuário protegido (A01)

`POST /api/v1/auth/register` agora exige um **auditor autenticado**. A única exceção é o *bootstrap*: quando a tabela `usuarios` está vazia, o primeiro cadastro é liberado para permitir a instalação inicial. Um script idempotente (`app/scripts/seed_admin.py`) formaliza esse bootstrap em produção e no CI.

O schema `UsuarioCreate` passou a aceitar `role` (`auditor`|`cliente`), habilitando o onboarding manual do usuário Cliente previsto em DEC-18 — operação que, por construção, só um auditor autenticado consegue executar.

### S-02 — Limite de tentativas de login (A07)

`app/core/rate_limit.py`: janela deslizante de 15 minutos, máximo de **5 tentativas malsucedidas** por (IP, e-mail); um login bem-sucedido zera o contador (não penaliza uso legítimo). Excedido o limite, a API responde `429` com `Retry-After`.

O estado é in-process — suficiente para o porte atual (um worker). Com múltiplas réplicas, migrar o contador para o Redis já previsto em ADR-06/DEC-10; a interface pública do módulo não muda. Em VPS próprio, o Nginx (`05_infra/nginx/nginx.conf`, BL-27) aplica um segundo limite na borda (`5r/m` em `/api/v1/auth/login`).

### S-03 e S-04 — Configuração fail-closed (A05)

- Documentação interativa (`/docs`, `/redoc`, `/openapi.json`) só é montada quando `ENVIRONMENT` é de desenvolvimento.
- `Settings` recusa iniciar fora de desenvolvimento se `JWT_SECRET_KEY` for vazia, `"changeme"` ou tiver menos de 32 caracteres, ou se `BACKEND_CORS_ORIGINS` contiver `*`. A aplicação falha no boot em vez de rodar insegura.

### S-05 e S-06 — Cabeçalhos e correlação (A05/A09)

`app/core/middleware.py`: `SecurityHeadersMiddleware` (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, CSP restritiva e HSTS fora de desenvolvimento) e `RequestIdMiddleware` (`X-Request-ID` gerado ou propagado do cliente, ecoado na resposta). Isso vale também no Render, onde não é possível customizar cabeçalhos no proxy gerenciado.

### S-07 e S-08 — Escopo do Portal do Cliente (A01/A02)

Implementado junto com BL-32/BL-33: todo endpoint `/portal/*` resolve o escopo a partir de `Responsavel.usuario_id = current_user.id` e valida o vínculo antes de qualquer leitura. Acesso a recurso de outro contratante responde **404** (não 403), para não revelar a existência de dados de terceiros. O download nunca expõe a chave do storage — devolve URL pré-assinada de 15 minutos.

---

## Riscos residuais aceitos

- **S-12 — Isolamento entre auditores:** hoje qualquer usuário `auditor` autenticado enxerga todos os contratos/edificações. É compatível com o uso previsto (um engenheiro ou uma pequena equipe da mesma empresa, RNF-05) e depende da lacuna #2 de [estudo-do-contexto.md](../estudo-do-contexto.md) (o engenheiro trabalha sozinho ou com auxiliares?). Se a resposta for "equipe com segregação", será necessário filtrar por proprietário na camada de repositório.
- **S-13 — Dependências major:** bumps não testados (Next 16, React 19, ESLint 10, Node 25) permanecem fechados por decisão consciente (DEC-22). O scan Trivy + `pip-audit`/`npm audit` do `ci.yml` continua bloqueando severidade HIGH/CRITICAL.
- **S-14 — Ciclo de vida do token:** o access token JWT expira em 60 minutos e não há refresh token nem lista de revogação. Um token vazado é válido até expirar. Aceito para a v1.0; revisitar se o Portal do Cliente passar a ter uso amplo.
- **Provedor de LLM (RF-15, R-10):** o envio de fotos/descrições a um provedor externo (A02) continua bloqueado por B-04 até a definição de provedor e política de retenção.

---

## Como reproduzir a validação

```bash
cd 04_backend
.venv/Scripts/python -m pytest tests/test_seguranca.py tests/test_auth.py tests/test_portal_cliente.py tests/test_rbac_portal.py -q
```

Cobertura automatizada dos controles: bloqueio após 5 falhas de login, reset por login bem-sucedido, presença dos cabeçalhos de segurança, propagação do `X-Request-ID`, `403` no registro sem autenticação, e recusa de configuração de produção insegura (`JWT_SECRET_KEY` default e CORS `*`).
