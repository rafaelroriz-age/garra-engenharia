# Unicidade de versão em `relatorios` (DEC-48 P3)

Status: **implementado, NÃO verificado contra banco migrado** (ver Pendências).

## O que mudou
- `04_backend/alembic/versions/e5a1f0c2b7d4_relatorios_unicidade_versao_dec_48.py` (down_revision `d3b7c9e4f1a2`, head único confirmado por `alembic heads`).
  - `upgrade()`: consulta duplicatas de (`inspecao_id`, `tipo`, `versao`); se houver, levanta `RuntimeError` listando-as e orientando limpeza manual (não apaga nem renumera nada); depois cria `uq_relatorios_inspecao_tipo_versao`.
  - `downgrade()`: remove a constraint.
- `app/models/relatorio.py`: mesma `UniqueConstraint` (mesmo nome) em `__table_args__`. A coluna de versão chama-se `versao` (String).
- `tests/test_relatorio_unicidade.py`: duplicata → `IntegrityError`; versões e tipos diferentes coexistem; teste de emissão sequencial dupla do RFO está **skip**.

## Decisões
- Nome explícito `uq_relatorios_inspecao_tipo_versao` (convenção `uq_<tabela>_<colunas>`).
- Migration aborta em vez de limpar: renumerar versões é decisão de negócio.

## Comandos e saída
- `alembic heads` → `e5a1f0c2b7d4 (head)`.
- `alembic upgrade head` / `downgrade -1` / `upgrade head`: **não rodou**. O banco apontado pelo `.env` está carimbado na revisão `f7c2a9d4e6b1`, que não existe nesta branch (vem de outra tarefa do lote; banco compartilhado): `Can't locate revision identified by 'f7c2a9d4e6b1'`. Não forcei `stamp` para não corromper o banco compartilhado.
- `pytest tests/test_relatorio_unicidade.py`: 1 passed, 1 failed, 1 skipped. A falha (`test_duplicata_levanta_integrity_error`) é esperada: a constraint ainda não existe no banco, pois a migration não foi aplicada. O teste de coexistência passou.
- `pytest` completo: **não rodou** — 16 erros de coleta (`ModuleNotFoundError: No module named 'jose'`, dependência ausente no ambiente).
- `ruff check .`: 221 erros já existentes no repositório (UP007/UP035/I001 etc., inclusive nas migrations existentes); a migration nova segue o mesmo estilo. Arquivo de teste novo corrigido (import).

## Pendências / riscos
1. **`emitir_rfo` e `00_docs/backlog-auto/rfo-endpoint-emissao.md` não existem nesta branch** (`app/services/relatorio_service.py` ausente): o teste de emissão sequencial (V01 → V02) ficou `skip`; habilitar após integrar o endpoint de emissão, usando storage/gerador fake dos testes de emissão.
2. Aplicar a migration e rodar a sequência upgrade/downgrade/upgrade num banco limpo (ou no do integrador, na revisão correta) e rodar o pytest completo após `pip install -r requirements`.
3. Dados existentes em produção: se já houver duplicatas, o upgrade aborta (sem alterar dados); rodar antes `SELECT inspecao_id, tipo, versao, count(*) FROM relatorios GROUP BY 1,2,3 HAVING count(*)>1;`. Esperado zero (RFO ainda não emite em produção).
4. Para o integrador: ordenar com a migration `f7c2a9d4e6b1` (outra tarefa) — `down_revision` desta deve apontar para o head vigente no momento do merge (hoje `d3b7c9e4f1a2`; ajustar ou criar merge para evitar múltiplos heads).
