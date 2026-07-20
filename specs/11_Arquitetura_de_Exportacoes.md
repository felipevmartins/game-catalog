# 11 — Arquitetura de Exportações

## Regra deny-by-default

Cada perfil mantém allowlist literal de tabela/coluna. Coluna nova não entra automaticamente: o teste de schema diff falha até classificação explícita. FKs/UUIDs podem ser exportados; `created_at`, `updated_at` e `deleted_at` só entram no perfil técnico quando listados.

## Allowlist `public`

| Tabela/visão | Colunas permitidas |
|---|---|
| regions | id, code, name, region_type, parent_region_id |
| manufacturers | id, name, country_code |
| ecosystems | id, name, manufacturer_id, parent_ecosystem_id, ecosystem_type |
| companies | id, name, company_type, parent_company_id, country_code, website |
| franchises | id, name, parent_franchise_id, status, status_reason |
| franchise_ecosystems | franchise_id, ecosystem_id, association_type, valid_from_year, valid_to_year, notes |
| franchise_ownerships | franchise_id, owner_company_id, ownership_type, is_current, PartialDate de início/fim, notes |
| platforms | id, name, manufacturer_id, ecosystem_id, platform_type, release_year, discontinuation_year |
| games | id, canonical_title, franchise_id, game_type, campaign_focus, online_only, regional_only, historically_relevant, collector_relevant, notes |
| game_editions | id, game_id, name, edition_type, is_definitive, notes |
| releases | id, edition_id, platform_id, region_id, release_type, PartialDate de release, official, notes |
| products | id, release_id, product_type, media_format, store_company_id, region_id, display_name |
| game_aliases | game_id, alias, alias_type, language_code, region_id |
| game_relations | source_game_id, target_game_id, relation_type, confidence, notes |
| game_contents | parent_game_id, title, content_type, requires_base_game, sequence_number, notes |
| game_companies | game_id, edition_id, release_id, company_id, role, notes |
| game_scores | id, release_id, source_id, score_value, review_count, retrieved_at |
| game_primary_scores | game_id, score_id, selection_reason, selected_at |
| game_lengths | game_id, source_id, main_story_minutes, main_extra_minutes, completionist_minutes, not_applicable, retrieved_at |
| availability_offers | release_id, access_platform_id, provider_company_id, availability_type, region_id, status, PartialDate de validade, observed_at, last_verified_at, valid_until; somente linha corrente |
| platform_lock_reasons | code, name, description |
| platform_lock_assessments | game_id, locked, severity_level, justification, minimum_official_hardware, content_lost, state, rule_version, calculated_at; valores omitidos quando state != current |
| game_platform_lock_reasons | game_id, reason_id, is_primary, notes; somente quando assessment pai está current |
| hardware_models | id, platform_id, manufacturer_id, name, model_code, hardware_type, introduced_year, discontinued_year, notes |
| accessory_models | id, manufacturer_id, name, accessory_type, model_code, notes |
| accessory_platforms | accessory_model_id, platform_id, support_level, required_adapter_model_id, notes |
| hardware_compatibility_rules | id, source_hardware_model_id, target_platform_id, compatibility_type, scope, notes |
| compatibility_rule_releases | compatibility_rule_id, release_id, support_level, notes |
| game_requirement_groups | id, release_id, group_operator, mandatory, description |
| game_hardware_requirements | id, group_id, hardware_model_id, accessory_model_id, capability_code, capability_provider_company_id, capability_platform_id, minimum_quantity, minimum_value, notes |
| sources | id, code, name, source_type, license_name, attribution_text, redistribution_policy |
| projeção `citations` (não persistente) | source_code, source_name, source_type, source_url, retrieved_at, verified_at, license_name, attribution_text |

Não entram em `public`/`shareable`: `schema_metadata`, `execution_runs`, `backups`, `source_references` brutas, `record_source_links`, `catalog_assertions`, todas as tabelas `*_external_ids`, tabelas pessoais, `run_tasks`, `review_queue` e `change_log`. A projeção `citations` é montada pelo ExportService a partir de FKs diretas e `record_source_links`, somente com URLs/atribuições aprovadas pela política de redistribuição.

Ofertas expiradas ou não correntes não são apresentadas como disponibilidade atual; podem ser incluídas em export histórico explícito pós-MVP.

## Allowlist `shareable`

Inclui todo `public` e apenas as visões agregadas:

- `collection_summary(game_id, owned_count, wishlist_count, played_any, completed_any)`;
- `playability_summary(release_id, playable_now, compatibility_level, state, calculated_at)`.

Não exporta linhas de itens/unidades nem datas, preços, origem, empréstimo, serial, localização, capacidades ou notas privadas.

## Allowlist `personal`

Inclui `public` e as colunas de:

- `personal_collection_items`: todas, inclusive preços, origem, empréstimo e private_notes;
- `products.sku`;
- tabelas `*_external_ids`: id, FK da entidade, source_id, external_id, context, is_primary, created_at, updated_at, quando os termos permitirem export pessoal;
- `personal_hardware_units` e `personal_accessory_units`: todas, inclusive serial_number, location, preços e private_notes;
- `personal_capabilities`: todas;
- `personal_playability`: release_id, playable_now, compatibility_level, missing_requirements_json, state, versões e calculated_at.

Requer `--profile personal --confirm-sensitive-export`. O arquivo usa permissão restrita quando o SO suportar.

## Allowlist `technical`

- `schema_metadata`: todos os campos;
- `execution_runs`: id, execution_type, status, requested_by, dry_run, application_version, schema_version, started_at, heartbeat_at, finished_at, backup_id, summary_json, error_summary_redacted, created_at; exclui parameters_json por padrão;
- `backups`: id, backup_type, file_name, size_bytes, sha256, schema_version, application_version, integrity_status, related_run_id, created_at, verified_at, retained, retention_reason, deleted_at, restored_at; exclui file_path;
- `run_tasks`: id, execution_run_id, task_type, entity_type, entity_id, source_id, priority, status, idempotency_policy, scheduled_for, attempt_count, max_attempts, deduplication_key, lock_owner, lock_token, locked_at, lock_expires_at, last_error_redacted, created_at, updated_at, finished_at;
- `review_queue`: id, entity_type, entity_id, field_name, reason, source_reference_id, priority, status, deduplication_key, created_at, reviewed_at, reviewed_by; payloads e review_notes apenas com `--include-review-payload` explícito;
- `change_log`: todos os campos após redaction.

Nunca inclui credenciais, caminhos absolutos, erro bruto, serial, localização, capacidades ou notas pessoais fora do perfil personal.

## Snapshot e atomicidade

O ExportService abre uma transação de leitura, fixa o snapshot WAL, executa todas as consultas no mesmo snapshot, escreve em temporário, valida e renomeia atomicamente. Falha preserva a exportação anterior.

## Execução não interativa

Default seguro: `public`. Perfil sensível sem confirmação falha; arquivo existente exige `--force`; logs exibem destino relativo/redigido.

## Testes

Schema diff deny-by-default, varredura de vazamento, licença/atribuição, snapshot sob writer concorrente, disponibilidade expirada, derivado stale/dirty, motivos de lock não current, falha atômica e permissões do perfil pessoal.
