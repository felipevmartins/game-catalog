# 21 — Matriz de Resolução da Auditoria

| Achado | Status | Decisão | Arquivos alterados | Evidência | Teste |
|---|---|---|---|---|---|
| `AUD-A01` | resolvido | Identidade Game→Edition→Release→Product integrada; Product limitado a uma Release no MVP. | 01, 06, 08, 17 | 08 games–products; 17 matriz | `identity_counts_idempotent` |
| `AUD-A02` | resolvido | UUIDv7 interno com formato/variante; exceções técnicas explícitas. | 00, 03, 07, 08, 17 | 07 IDs; 08 contrato | `uuid_canonical_constraints` |
| `AUD-A03` | resolvido | PartialDate único; unknown exige qualifier nulo. | 03, 08, 17, 24 | 17 PartialDate | `partial_date_property_suite` |
| `AUD-A04` | resolvido | Money inteiro + ISO 4217 em compra/venda. | 03, 08, 10, 17 | personal tables | `money_roundtrip_and_pair_checks` |
| `AUD-A05` | resolvido | Coleção 1:N e triggers de cadeia. | 06, 08, 10, 23, 27 | 08 personal_collection_items | `multiple_copies_chain_triggers` |
| `AUD-A06` | resolvido | IDs externos por entidade/contexto e discriminadores estáveis. | 08, 12, 17, 25 | releases/products | `external_id_discriminator_reimport` |
| `AUD-A07` | resolvido | Enums separados para Game, Edition e Release. | 03, 06, 08, 17 | vocabulário | `enum_consistency_identity_cases` |
| `AUD-A08` | resolvido | Tabelas do MVP definidas, migradas e com owner. | 08, 22, 26, schema_manifest | manifest | `schema_manifest_cross_check` |
| `AUD-A09` | resolvido | Migrations, backup e downgrade diferenciados. | 07, 13, 15, 26 | 26 sequência | `migration_up_down_backup_tests` |
| `AUD-B01` | resolvido | execution_runs única, incluindo manual_edit. | 06, 08, 09, 13, 14 | 13 máquina | `execution_state_machine_tests` |
| `AUD-B02` | resolvido | Fila com dedupe, retry, idempotency policy e fencing. | 07, 08, 13, 24, 27 | run_tasks | `lock_reclaim_old_worker_test` |
| `AUD-B03` | resolvido | Dirty/stale/versionamento implementável; versões obrigatórias apenas em current. | 05, 08, 10, 13 | derived tables | `dirty_same_transaction_and_stale_read` |
| `AUD-B04` | resolvido | Backup/restore com WAL, sidecar específico e retenção explícita. | 07, 08, 13, 26, 27 | backup sections | `backup_restore_fault_injection` |
| `AUD-B05` | resolvido | Proveniência por registro/fato/assertion seletiva. | 08, 12, 23 | record_source_links | `source_provenance_conflict_suite` |
| `AUD-B06` | resolvido | Exportações allowlist, snapshot, histórico/corrente e redaction. | 11, 14, 23, 27 | 11 perfis | `public_export_no_leak` |
| `AUD-B07` | resolvido | Hardware, capacidades, all_of/any_of e selected_titles por Release. | 08, 10, 23, 27 | hardware sections | `playability_requirement_groups` |
| `AUD-B08` | resolvido | Arquitetura cobre agregados sem componentes artificiais. | 09, 22 | serviços/matriz | `architecture_owner_completeness` |
| `AUD-B09` | resolvido | Invariantes, propriedades e prova vertical têm resultados esperados. | 24, 25, 27, identity_test_cases | anexos | `vertical_proof_suite` |
| `AUD-V12-01` | resolvido | Correções de atributos não alteram identidade de Edition/Release/Product/Content. | 03, 06, 08, 12, 17 | identity_discriminator | `child_identity_correction_no_duplicate` |
| `AUD-V12-02` | resolvido | Disponibilidade preserva histórico e linha corrente única. | 06, 08, 11, 12, 27 | availability_offers | `availability_delist_relist_history` |
| `AUD-V12-03` | resolvido | Histórico de proprietária passou a ter persistência. | 04, 08, 11, 23 | franchise_ownerships | `franchise_ownership_timeline` |
| `AUD-V12-04` | resolvido | Run abandonada não deixa tasks sob run terminal. | 09, 13, 24, 27 | recuperação | `abandoned_run_recovery` |
| `AUD-C01` | não aplicável ao escopo | Event sourcing/rollback universal rejeitados. | 06, 13, 18, 28 | 13 Rollback | `restore_and_compensation_tests` |
| `AUD-C02` | não aplicável ao escopo | DAG/orquestrador distribuído rejeitado. | 07, 13, 18, 28 | fila SQLite | `queue_integration` |
