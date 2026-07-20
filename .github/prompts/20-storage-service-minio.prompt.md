---
description: "Ativa o agente Engenheiro Backend para implementar o serviço de armazenamento de arquivos (MinIO/S3) do Sistema de Automação de Relatórios Prediais."
---
## Contexto
Tarefa BL-07 do backlog em `00_docs/projeto/backlog-tarefas.md`, Etapa 0 (Fundação Técnica) de `00_docs/projeto/ciclo-de-vida.md`.
Requisito RNF-07 de `00_docs/estudo-do-contexto.md`: fotos devem ser armazenadas em serviço de objeto (S3/MinIO), fora do banco relacional.
Decisão DEC-02 de `00_docs/projeto/decisoes.md`: MinIO self-hosted via Docker, SDK `boto3` (S3-compatível) para portabilidade.
Padrão de projeto Adapter (`00_docs/arquitetura.md` Seção 9.9): `StorageClient` (interface) + `S3StorageClient` (implementação boto3/MinIO), para permitir troca de provedor sem alterar os serviços consumidores.
O serviço MinIO já está disponível via `05_infra/docker-compose.yml` (BL-01, concluída). Depende do scaffold do backend (`15-scaffold-backend-fastapi.prompt.md`). Não depende de B-01 nem B-02.

## Tarefa
Assuma o papel de **Engenheiro Backend** e implemente o serviço de armazenamento:

1. Defina a interface `StorageClient` (ex.: `04_backend/app/services/storage/base.py`) com os métodos mínimos: `upload(key, file_bytes, content_type) -> str`, `download(key) -> bytes`, `delete(key) -> None`, `generate_presigned_url(key, expires_in) -> str`.
2. Implemente `S3StorageClient` (`04_backend/app/services/storage/s3_client.py`) usando `boto3`, configurado via variáveis de ambiente (endpoint, access key, secret key, bucket, região) já previstas em `05_infra/.env.example`.
3. Garanta que o bucket seja criado automaticamente se não existir (idempotente, seguro para rodar múltiplas vezes).
4. Configure URLs pré-assinadas com expiração curta (ex.: 15 minutos) para downloads, conforme RNF-07 e Seção 10.1 (A02) de `00_docs/arquitetura.md`.
5. Exponha o `StorageClient` via dependency injection do FastAPI (`Depends`), para permitir substituição por um fake/stub nos testes.
6. Escreva testes de integração contra o MinIO real do `05_infra/docker-compose.yml` (upload, download, delete, geração de URL pré-assinada).
7. Rode os testes e valide o fluxo completo localmente.

## Saída Esperada
- Interface `StorageClient` e implementação `S3StorageClient` em `04_backend/app/services/storage/`
- Criação automática de bucket
- URLs pré-assinadas com expiração configurável
- Dependency injectável para uso nos endpoints de foto (preparação para BL-11)
- Testes de integração passando
- Resumo: variáveis de ambiente necessárias, como rodar os testes, como o serviço será consumido pelos endpoints de foto

## Restrições
- NÃO exponha credenciais do MinIO/S3 em código — sempre via variável de ambiente.
- NÃO gere URLs públicas permanentes — sempre pré-assinadas com expiração.
- NÃO acople os serviços consumidores diretamente ao `boto3` — sempre através da interface `StorageClient` (Adapter Pattern).
- SEMPRE valide entradas (tamanho de arquivo, chave não vazia) nos limites do sistema.
- Leia os arquivos antes de modificá-los.
