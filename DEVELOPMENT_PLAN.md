# Plano de desenvolvimento

Este plano transforma as fases vinculantes da especificação v1.3 em gates incrementais. Uma etapa só começa depois que os critérios da anterior forem verificados.

## Regras de execução

- SQLite é a fonte da verdade; exportações são snapshots derivados.
- Nenhuma integração HTTP será implementada antes da prova vertical local.
- Cada etapa entrega código, testes e documentação compatíveis com seu risco.
- Mudanças de schema respeitam a ordem `0001` a `0009`.
- Banco com dados exige backup válido antes de migration destrutiva, merge automático ou alteração em massa.
- Importadores nunca escrevem em tabelas pessoais.
- Decisões não cobertas pelas specs ficam registradas como pendências; não serão inventadas.

## Entregáveis transversais

Cada etapa deve atualizar, quando aplicável:

- código de produção e migrations;
- testes unitários, de integração e de propriedade;
- documentação de decisões e operação;
- matrizes de cobertura/persistência afetadas;
- fixture ou evidência reproduzível do gate.

O pipeline mínimo deve executar formatação, lint, type-check, testes e validação de migrations em SQLite real. Métricas de cobertura ajudam a localizar lacunas, mas não substituem os gates de invariantes.

## Etapas e gates

1. **Baseline canônico** — registrar precedência, stack, contratos de dados, identidade, seeds mínimos e decisões humanas pendentes. Gate: baseline revisado e sem contradição conhecida.
2. **Fundação Python** — criar pacote e camadas, `pyproject.toml`, configuração, logging redigido e testes básicos. Gate: instalação local, lint/type-check/testes aprovados.
3. **Schema e migrations** — implementar Alembic `0001`–`0009`, FKs, checks, triggers e índices parciais. Gate: upgrade/downgrade documentado e testes em SQLite real.
4. **Identidade e persistência** — models, repositories e `IdentityService` para Game → Edition → Release → Product, aliases, relações, IDs externos e proveniência. Gate: casos de identidade e reimportação idempotente aprovados.
5. **Serviços essenciais** — catálogo, franquias/propriedade, fontes, scores, disponibilidade, Unit of Work e change log mínimo. Gate: invariantes de serviço e transação aprovados.
6. **Importação local** — fixtures JSON/CSV, normalização, deduplicação, conflitos e dry-run, sem HTTP. Gate: reimportação não altera contagens e dry-run não muda estado funcional.
7. **Coleção pessoal** — múltiplos itens, compra, venda, empréstimo e proteção em merge/import. Gate: triggers de cadeia e isolamento de dados pessoais aprovados.
8. **Hardware e jogabilidade** — modelos, unidades, capacidades, compatibilidade por Release, grupos `all_of`/`any_of` e estado derivado. Gate: cenários de requisitos e compatibilidade aprovados.
9. **Backup e restauração** — Online Backup API, sidecar, SHA-256, integridade, retenção e restore. Gate: falha de backup impede writes protegidos e restore recupera um snapshot íntegro.
10. **Atualização incremental** — runs, fila, idempotência, fencing por `lock_token`, retry/dead-letter e estados dirty/stale. Gate: testes determinísticos de concorrência e recuperação aprovados.
11. **Exportações** — allowlists, snapshot consistente, perfis corrente/histórico e redaction. Gate: varredura pública sem dados pessoais ou campos não classificados.
12. **CLI** — comandos e contratos de saída definidos na especificação. Gate: testes end-to-end dos principais fluxos e códigos de saída.
13. **Validação final** — propriedades, triggers, concorrência, migrations, privacidade e os 15 cenários da prova vertical. Gate: relatório reproduzível com contagens, IDs, hashes e estados.
14. **Coletores externos (condicional)** — somente após os gates anteriores e revisão humana atual dos termos/licenças. Gate: fontes explicitamente autorizadas e limites operacionais definidos.

## Marcos de entrega

| Marco | Etapas | Resultado demonstrável |
|---|---:|---|
| M0 — contrato congelado | 1 | baseline, riscos e decisões abertas registrados |
| M1 — banco executável | 2–3 | ambiente instalável e migrations completas em SQLite real |
| M2 — catálogo mínimo | 4–6 | cadeia de identidade persistida e reimportação local idempotente |
| M3 — acervo pessoal | 7–8 | coleção, hardware e jogabilidade sem escrita externa em dados pessoais |
| M4 — operação segura | 9–10 | backup/restore e fila incremental recuperável com fencing |
| M5 — produto local | 11–12 | exportações seguras e CLI utilizável de ponta a ponta |
| M6 — aceite técnico | 13 | 15 cenários da prova vertical e auditorias aprovados |
| M7 — integrações | 14 | somente fontes autorizadas, observáveis e limitadas |

## Dependências críticas

```text
baseline → fundação → migrations → identidade → importação local
                                      ├→ coleção → hardware/jogabilidade
                                      └→ serviços essenciais
backup/restore → atualização incremental
catálogo + pessoal + operação segura → exportações → CLI → prova vertical
prova vertical + revisão de termos → coletores externos
```

## Ordem prática da próxima etapa

1. Criar o pacote Python, `pyproject.toml` e as camadas definidas na arquitetura.
2. Registrar versões suportadas e escolher a biblioteca UUIDv7 por teste de formato, variante e ordenação.
3. Configurar conexão SQLite com `foreign_keys=ON`, WAL, timeout e logging redigido.
4. Preparar Alembic e um teste que aplique `upgrade head` em banco temporário real.
5. Configurar os checks locais/CI de formatação, lint, tipos e pytest.
6. Só então iniciar `0001_foundation`, preservando a sequência canônica das migrations.

## Rastreabilidade principal

| Área do plano | Fontes primárias |
|---|---|
| Baseline, identidade, datas, dinheiro e IDs | `06`, `08`, `17`, `identity_test_cases.md` |
| Python, persistência e services | `07`, `08`, `09`, `23`, `24` |
| Coleção, hardware e jogabilidade | `10`, `22`, `23`, `27` |
| Fontes, conflitos e incremental | `12`, `13`, `25`, `27` |
| Exportações, CLI e privacidade | `11`, `14`, `22`, `27` |
| Migrations e validação final | `16`, `24`, `25`, `26`, `27`, `29` |

## Estado

- Etapa 1 — Baseline canônico: **concluída**.
- Etapa 2 — Fundação Python: **concluída** com ambiente reproduzível, CI e gates locais.
- Etapa atual: **3 — Schema e migrations**.
- Migration `0001_foundation`: **implementada e testada** em SQLite real.
- Migration `0002_reference_catalog`: **implementada e testada** em SQLite real.
- Migration `0003_game_identity`: **implementada e testada** em SQLite real.
- Migration `0004_sources_and_external_ids`: **implementada e testada** em SQLite real.
- Migration `0005_catalog_facts_and_availability`: **implementada e testada** em SQLite real.
- Migration `0006_personal_collection`: **implementada e testada** em SQLite real.
- Migration `0007_hardware_and_playability`: **implementada e testada** em SQLite real.
- Migration `0008_incremental_operations`: **implementada e testada** em SQLite real.
- Migration `0009_seed_reference_data`: **implementada e testada** em SQLite real.
- Repositórios iniciais, Unit of Work e criação transacional de Game/Edition: **implementados e testados**.
- CLI `db init`, `game add` e `game list`: **implementada e testada de ponta a ponta**.
- Próxima ação: ampliar a prova vertical com Release por plataforma/região e coleção pessoal.
