# 23 — Matriz Requisito → Persistência

| Requisito | Entidade/tabela | Constraint ou mecanismo | Serviço responsável | Teste |
|---|---|---|---|---|
| Identidade Game→Edition→Release→Product | games, game_editions, releases, products | FKs, discriminator, identity_key estável | IdentityService | identity_test_cases |
| Port/remaster/remake | game_editions, releases, game_relations | enums separados + relação | IdentityService | identity_counts_idempotent |
| Reimportação sem duplicata | *_external_ids, edition/release/product discriminator | uniques + resolver | IdentityService | reimport_same_counts |
| Região válida | regions + FKs region_id | FK/seed | Catalog/Identity/Availability | region_fk_suite |
| PartialDate | releases, availability_offers, franchise_ownerships | checks estruturais + value object | serviços correspondentes | partial_date_property_suite |
| Compra e venda | personal_collection_items e unidades pessoais | pares amount/currency | Collection/Hardware services | money_pair_and_exponent |
| Múltiplas cópias | personal_collection_items | PK por item; sem unique game_id | CollectionService | multiple_copies |
| Cadeia pessoal coerente | personal_collection_items | triggers + service | CollectionService | personal_chain_trigger_suite |
| Preservar pessoal em merge | FK RESTRICT + transação de redirect | merge aborta em inconsistência | IdentityService | merge_preserves_personal |
| Histórico de propriedade | franchise_ownerships | FKs + PartialDate + fonte | FranchiseService | franchise_ownership_timeline |
| Score primário único | game_primary_scores | PK game_id + UNIQUE score_id + trigger | ScoreService | primary_score_same_game |
| Disponibilidade histórica/corrente | availability_offers | offer_identity_key + unique current | AvailabilityService | delist_relist_history |
| Jogabilidade | requirements, compatibility releases, personal units/capabilities, personal_playability | groups + state/version | PlayabilityService | playability_all_any |
| Fontes/conflitos | sources, source_references, record_source_links, assertions, review_queue | priority/status/TTL/unique accepted | SourceResolutionService | source_conflict_suite |
| Execução incremental | execution_runs, run_tasks | state machine, dedupe, policy, lock_token | Execution/Queue services | queue_concurrency |
| Recuperação abandonada | execution_runs, run_tasks | running→queued controlado ou fail+cancel | ExecutionService | abandoned_run_recovery |
| Dirty/stale | platform_lock_assessments, personal_playability | state/rule/input versions | PlatformLock/Playability | dirty_stale_suite |
| Backup/restore | backups, execution_runs | hash/integrity/sidecar específico | BackupService | backup_restore_faults |
| Exportação segura | schema classifications + allowlists | deny-by-default + current-only | ExportService | public_export_no_leak |
| Auditoria sem event sourcing | change_log | registro redigido, sem replay universal | ChangeLogService | change_log_redaction |
