## O que este PR faz
<!-- Descrição curta do que muda e por quê. -->

## Referências

- Backlog: BL-XX (`00_docs/projeto/backlog-tarefas.md`)
- Requisitos/Regras: RF-XX / RN-XX / RNF-XX (`00_docs/estudo-do-contexto.md`)
- Decisão relacionada (se houver): DEC-XX (`00_docs/projeto/decisoes.md`)

## Checklist

- [ ] Testes novos/atualizados e `pytest` (`04_backend`) / `npm run lint` + `npm run build` (`03_frontend`) passando localmente
- [ ] Sem segredo/credencial commitado (`.env`, chaves, tokens)
- [ ] Migration Alembic inclui `downgrade()` testado (se aplicável)
- [ ] Variáveis de ambiente novas documentadas em `.env.example`
- [ ] Documentação (`00_docs/`) atualizada, se o comportamento ou uma decisão mudou
