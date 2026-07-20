# 15 — Plano de Implementação

## Regras

Aplicação local Python 3.12+, SQLAlchemy 2.x, Alembic, Pydantic, Typer e pytest. Não implementar coletores externos antes da prova vertical local. Cada fase inclui testes e documentação.

## Fases vinculantes

1. **Decisões canônicas:** congelar enums, regions, PartialDate, Money, UUIDv7, discriminadores e identidade.
2. **Schema e migrations:** implementar 0001–0009, triggers, partial indexes e testes up/down/integridade.
3. **Identidade e persistência:** models/repositories/IdentityService para Game→Edition→Release→Product, aliases, relações, external IDs e proveniência por registro.
4. **Serviços essenciais:** catálogo, franquias/propriedade, fontes, scores, disponibilidade, UnitOfWork e change log mínimo.
5. **Importação idempotente local:** fixtures JSON/CSV, dedupe por external ID/discriminator, conflitos, dry-run; sem HTTP.
6. **Coleção pessoal:** múltiplos itens, compra/venda/empréstimo e proteção de merge/import.
7. **Hardware e jogabilidade:** modelos/unidades, capacidades, compatibilidade por Release, grupos all_of/any_of e derived state.
8. **Backup e restauração:** Online Backup API, sidecar específico, hash, integridade, retenção e teste de restore.
9. **Atualização incremental:** execution_runs, queue, política de idempotência, lock_token, recuperação, retry/dead-letter, dirty/stale/versionamento.
10. **Exportações:** allowlists, snapshot, histórico/corrente e redaction.
11. **CLI completa:** comandos do documento 14 e contratos de saída.
12. **Validação final:** propriedades, triggers, concorrência, migrations, privacidade e prova vertical.
13. **Coletores externos básicos:** somente depois dos gates anteriores e revisão atual dos termos.

## Gate de backup

Backup mínimo funcional deve existir antes de qualquer fase que execute atualização em massa, migration destrutiva, merge automático ou mudança de alto volume. Durante desenvolvimento das migrations iniciais em banco descartável, o teste pode usar cópia temporária; em banco com dados, o gate é obrigatório.

## Definition of Done

- migration e downgrade seguro/documentado;
- owner arquitetural e testes;
- nenhuma escrita direta de importador em pessoal;
- logs redigidos;
- invariantes críticos cobertos por FK/check/trigger/service/auditoria no mecanismo adequado;
- documentação/matrizes atualizadas.
