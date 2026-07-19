---
description: "Ativa o agente Engenheiro Backend para implementar autenticação JWT + bcrypt do Sistema de Automação de Relatórios Prediais."
---
## Contexto
Tarefa BL-06 do backlog em `00_docs/projeto/backlog-tarefas.md`, Etapa 0 (Fundação Técnica) de `00_docs/projeto/ciclo-de-vida.md`.
Requisito RNF-05 de `00_docs/estudo-do-contexto.md`: autenticação com login e senha, uso individual ou pequena equipe. Decisão DEC-05 de `00_docs/projeto/decisoes.md`: FastAPI + JWT (python-jose) + bcrypt.
Depende do scaffold do backend e do modelo de dados (prompts `15-scaffold-backend-fastapi.prompt.md` e `17-modelagem-dados-migrations.prompt.md`). Não depende de B-01 nem B-02.

## Tarefa
Assuma o papel de **Engenheiro Backend** e implemente a autenticação:

1. Crie o modelo `Usuario` (email, hash de senha, nome, ativo) em `04_backend/app/models/` com migration Alembic correspondente. Caso já exista entidade `Responsavel` no modelo ER que sirva a esse propósito, avalie reaproveitá-la e registre a decisão em `00_docs/projeto/decisoes.md`.
2. Implemente hashing de senha com `passlib[bcrypt]`.
3. Implemente geração e validação de token JWT com `python-jose`, incluindo expiração configurável via variável de ambiente.
4. Crie os endpoints:
   - `POST /api/v1/auth/login` — recebe email/senha, retorna access token (e refresh token, se aplicável)
   - `POST /api/v1/auth/register` — cria novo usuário (uso interno da equipe, sem cadastro público)
   - `GET /api/v1/auth/me` — retorna dados do usuário autenticado
5. Crie uma dependency FastAPI (`get_current_user`) para proteger rotas que exigem autenticação, retornando 401 quando o token for inválido/expirado.
6. Escreva testes cobrindo: login com sucesso, login com senha incorreta (401), acesso a rota protegida sem token (401), acesso a rota protegida com token válido (200).
7. Rode os testes e valide o fluxo completo localmente.

## Saída Esperada
- Modelo de usuário/autenticação com migration aplicada
- Endpoints `/auth/login`, `/auth/register`, `/auth/me` funcionando
- Dependency de proteção de rotas (`get_current_user`)
- Testes passando cobrindo casos de sucesso e falha de autenticação
- Resumo: como criar um usuário, como obter e usar o token JWT, tempo de expiração configurado

## Restrições
- NÃO armazene senha em texto plano — sempre hash com bcrypt.
- NÃO exponha o hash da senha em nenhuma resposta da API.
- NÃO hardcode o secret do JWT — use variável de ambiente (`JWT_SECRET`) documentada em `.env.example`.
- SEMPRE valide entradas (formato de email, tamanho mínimo de senha).
- Siga as boas práticas OWASP Top 10 para autenticação (proteção contra brute force pode ser tratada em tarefa futura de hardening — Etapa 6).
- Leia os arquivos antes de modificá-los.
