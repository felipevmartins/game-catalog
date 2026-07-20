# 26 — Sequência de Migrations

## Regras gerais

- banco novo aplica 0001→0009; toda conexão usa foreign_keys ON;
- UUIDs de seed são constantes v7 geradas uma vez;
- banco com dados cria backup válido antes de migration destrutiva/rebuild;
- downgrade não é promessa de recuperação de dados; restore é mecanismo distinto.

| Migration | Tabelas | Dependências | Upgrade | Downgrade | Backup | Teste |
|---|---|---|---|---|---|---|
| `0001_foundation` | `schema_metadata`, `execution_runs`, `backups` | nenhuma | Cria metadados, runs e backups. As duas FKs circulares são nullable e não diferíveis: inserir run, inserir backup relacionado e então atualizar run.backup_id. | Drop inverso somente em banco de desenvolvimento vazio. | não, banco novo | `test_migration_0001_foundation` |
| `0002_reference_catalog` | `regions`, `manufacturers`, `ecosystems`, `companies`, `franchises`, `franchise_ecosystems`, `platforms` | 0001 | Cria vocabulários, hierarquias e índices anti-duplicação. | Drop inverso; destrutivo. | sim em banco existente | `test_migration_0002_reference_catalog` |
| `0003_game_identity` | `games`, `game_editions`, `releases`, `products`, `game_aliases`, `game_relations`, `game_contents` | 0002 | Cria cadeia, discriminadores estáveis para Edition/Release/Product/Content, partial unique de Edition original e relações. | Drop inverso; bloqueado se houver pessoal. | sim em banco existente | `test_migration_0003_game_identity` |
| `0004_sources_and_external_ids` | `sources`, `source_references`, `record_source_links`, `catalog_assertions`, tabelas external ID de Game/Edition/Release/Platform/Company/Franchise/Product | 0003 | Cria proveniência seletiva, unique accepted e IDs externos. Adiciona FK de alias por rebuild se necessário. | Rebuild reverso; destrutivo. | sim | `test_migration_0004_sources_external` |
| `0005_catalog_facts_and_availability` | `franchise_ownerships`, `game_companies`, `game_scores`, `game_primary_scores`, `game_lengths`, `availability_offers`, tabelas de platform lock | 0004 | Cria histórico de propriedade, scores, disponibilidade temporal/current e derivados. Inclui triggers de crédito/score. | Drop de derivados/fatos; destrutivo. | sim | `test_migration_0005_catalog_facts` |
| `0006_personal_collection` | `personal_collection_items` | 0005 | Cria coleção multi-item e triggers de cadeia. | Proibido sem export/backup explícito. | sim | `test_migration_0006_personal_collection` |
| `0007_hardware_and_playability` | `hardware_models`, `hardware_model_external_ids`, `personal_hardware_units`, `accessory_models`, `accessory_platforms`, `personal_accessory_units`, `personal_capabilities`, `hardware_compatibility_rules`, `compatibility_rule_releases`, `game_requirement_groups`, `game_hardware_requirements`, `personal_playability` | 0006 | Cria hardware, capacidades, compatibilidade por Release, requisitos e cache. | Destrutivo; requer backup/export pessoal. | sim | `test_migration_0007_hardware` |
| `0008_incremental_operations` | `run_tasks`, `review_queue`, `change_log` | 0007 | Cria fila, idempotency policy, dedupe de revisão e auditoria. | Drop somente em desenvolvimento. | sim | `test_migration_0008_operations` |
| `0009_seed_reference_data` | nenhuma; seeds | 0008 | Insere regions, ecossistemas, plataformas mínimas, motivos de lock e fonte manual com UUIDv7 fixos. UPSERT por UUID/código fixo. | Remove apenas seeds não referenciados. | não no banco novo; sim antes de reaplicar em banco existente | `test_migration_0009_seeds` |

## Ordem de FKs e triggers

Cada migration cria pais antes de filhos e remove filhos antes de pais. Triggers são criados após todas as tabelas que consultam existirem e removidos antes de rebuild/drop. A migration 0004 pode reconstruir `game_aliases` para adicionar FK de fonte; exige backup em banco existente e teste de preservação.
