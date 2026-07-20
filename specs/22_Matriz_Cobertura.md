# 22 — Matriz de Cobertura

| Tabela ou agregado | Model | Repository | Service | CLI | Exportação | Teste |
|---|---|---|---|---|---|---|
| `schema_metadata` | `SchemaMetadata` | `MigrationRepository` | `MigrationService` | db status/migrate | technical | `test_schema_metadata_integration` |
| `execution_runs` | `ExecutionRun` | `ExecutionRunRepository` | `ExecutionService` | run show/list | technical | `test_execution_runs_integration` |
| `backups` | `Backup` | `BackupRepository` | `BackupService` | backup * | technical redigido | `test_backups_integration` |
| `regions` | `Region` | `RegionRepository` | `CatalogService` | region list/show/search | public/shareable/personal | `test_regions_integration` |
| `manufacturers` | `Manufacturer` | `ManufacturerRepository` | `CatalogService` | manufacturer list/show/search | public/shareable/personal | `test_manufacturers_integration` |
| `ecosystems` | `Ecosystem` | `EcosystemRepository` | `CatalogService` | ecosystem list/show/search | public/shareable/personal | `test_ecosystems_integration` |
| `companies` | `Company` | `CompanyRepository` | `CatalogService` | company list/show/search | public/shareable/personal | `test_companies_integration` |
| `franchises` | `Franchise` | `FranchiseRepository` | `FranchiseService` | franchise list/show/search | public/shareable/personal | `test_franchises_integration` |
| `franchise_ecosystems` | `FranchiseEcosystem` | `FranchiseRepository` | `FranchiseService` | franchise show | public/shareable/personal | `test_franchise_ecosystems_integration` |
| `platforms` | `Platform` | `PlatformRepository` | `PlatformService` | platform list/show/search | public/shareable/personal | `test_platforms_integration` |
| `games` | `Game` | `GameRepository` | `IdentityService` | game * | public/shareable/personal | `test_games_integration` |
| `game_editions` | `GameEdition` | `EditionRepository` | `IdentityService` | edition * | public/shareable/personal | `test_game_editions_integration` |
| `releases` | `Release` | `ReleaseRepository` | `IdentityService` | release * | public/shareable/personal | `test_releases_integration` |
| `products` | `Product` | `ProductRepository` | `IdentityService` | product * | public/shareable/personal | `test_products_integration` |
| `game_aliases` | `GameAlias` | `GameRepository` | `IdentityService` | game show/search | public/shareable/personal | `test_game_aliases_integration` |
| `game_relations` | `GameRelation` | `GameRelationRepository` | `IdentityService` | game show/edit | public/shareable/personal | `test_game_relations_integration` |
| `game_contents` | `GameContent` | `GameContentRepository` | `CatalogService` | game show/edit | public/shareable/personal | `test_game_contents_integration` |
| `sources` | `Source` | `SourceRepository` | `SourceResolutionService` | import/source internal | public citations/technical | `test_sources_integration` |
| `source_references` | `SourceReference` | `SourceReferenceRepository` | `SourceResolutionService` | import/review internal | citations/technical | `test_source_references_integration` |
| `record_source_links` | `RecordSourceLink` | `SourceReferenceRepository` | `SourceResolutionService` | import/review internal | citations/technical | `test_record_source_links_integration` |
| `catalog_assertions` | `CatalogAssertion` | `AssertionRepository` | `SourceResolutionService` | review * | technical redigido | `test_catalog_assertions_integration` |
| `game_external_ids` | `GameExternalId` | `ExternalIdentifierRepository` | `IdentityService` | external-id lookup | personal/technical conforme termos | `test_game_external_ids_integration` |
| `edition_external_ids` | `EditionExternalId` | `ExternalIdentifierRepository` | `IdentityService` | external-id lookup | personal/technical conforme termos | `test_edition_external_ids_integration` |
| `release_external_ids` | `ReleaseExternalId` | `ExternalIdentifierRepository` | `IdentityService` | external-id lookup | personal/technical conforme termos | `test_release_external_ids_integration` |
| `platform_external_ids` | `PlatformExternalId` | `ExternalIdentifierRepository` | `IdentityService` | external-id lookup | personal/technical conforme termos | `test_platform_external_ids_integration` |
| `company_external_ids` | `CompanyExternalId` | `ExternalIdentifierRepository` | `IdentityService` | external-id lookup | personal/technical conforme termos | `test_company_external_ids_integration` |
| `franchise_external_ids` | `FranchiseExternalId` | `ExternalIdentifierRepository` | `IdentityService` | external-id lookup | personal/technical conforme termos | `test_franchise_external_ids_integration` |
| `product_external_ids` | `ProductExternalId` | `ExternalIdentifierRepository` | `IdentityService` | external-id lookup | personal/technical conforme termos | `test_product_external_ids_integration` |
| `franchise_ownerships` | `FranchiseOwnership` | `FranchiseRepository` | `FranchiseService` | franchise show/edit | public/shareable/personal | `test_franchise_ownerships_integration` |
| `game_companies` | `GameCompany` | `CreditRepository` | `CatalogService` | game show/edit | public/shareable/personal | `test_game_companies_integration` |
| `game_scores` | `GameScore` | `ScoreRepository` | `ScoreService` | game show/import | public conforme licença/technical | `test_game_scores_integration` |
| `game_primary_scores` | `GamePrimaryScore` | `ScoreRepository` | `ScoreService` | game show/edit | public/shareable/personal | `test_game_primary_scores_integration` |
| `game_lengths` | `GameLength` | `LengthRepository` | `LengthService` | game show/import | public conforme licença/technical | `test_game_lengths_integration` |
| `availability_offers` | `AvailabilityOffer` | `AvailabilityRepository` | `AvailabilityService` | availability * | public current/personal | `test_availability_offers_integration` |
| `platform_lock_reasons` | `PlatformLockReason` | `PlatformLockRepository` | `PlatformLockService` | lock * | public/shareable/personal | `test_platform_lock_reasons_integration` |
| `platform_lock_assessments` | `PlatformLockAssessment` | `PlatformLockRepository` | `PlatformLockService` | lock * | public current/shareable/personal | `test_platform_lock_assessments_integration` |
| `game_platform_lock_reasons` | `GamePlatformLockReason` | `PlatformLockRepository` | `PlatformLockService` | lock show | public somente pai current | `test_game_platform_lock_reasons_integration` |
| `personal_collection_items` | `PersonalCollectionItem` | `CollectionRepository` | `CollectionService` | collection * | personal/shareable agregado | `test_personal_collection_items_integration` |
| `hardware_models` | `HardwareModel` | `HardwareModelRepository` | `HardwareCatalogService` | hardware * | public/shareable/personal | `test_hardware_models_integration` |
| `hardware_model_external_ids` | `HardwareModelExternalId` | `ExternalIdentifierRepository` | `HardwareCatalogService` | external-id lookup | personal/technical conforme termos | `test_hardware_model_external_ids_integration` |
| `personal_hardware_units` | `PersonalHardwareUnit` | `HardwareCollectionRepository` | `HardwareCollectionService` | hardware * | personal | `test_personal_hardware_units_integration` |
| `accessory_models` | `AccessoryModel` | `AccessoryModelRepository` | `HardwareCatalogService` | accessory * | public/shareable/personal | `test_accessory_models_integration` |
| `accessory_platforms` | `AccessoryPlatform` | `AccessoryModelRepository` | `HardwareCatalogService` | accessory show | public/shareable/personal | `test_accessory_platforms_integration` |
| `personal_accessory_units` | `PersonalAccessoryUnit` | `AccessoryCollectionRepository` | `AccessoryCollectionService` | accessory * | personal | `test_personal_accessory_units_integration` |
| `personal_capabilities` | `PersonalCapability` | `CapabilityRepository` | `PlayabilityService` | capability * | personal | `test_personal_capabilities_integration` |
| `hardware_compatibility_rules` | `HardwareCompatibilityRule` | `CompatibilityRepository` | `HardwareCompatibilityService` | playability/admin | public/shareable/personal | `test_hardware_compatibility_rules_integration` |
| `compatibility_rule_releases` | `CompatibilityRuleRelease` | `CompatibilityRepository` | `HardwareCompatibilityService` | playability/admin | public/shareable/personal | `test_compatibility_rule_releases_integration` |
| `game_requirement_groups` | `GameRequirementGroup` | `RequirementRepository` | `RequirementService` | playability/admin | public/shareable/personal | `test_game_requirement_groups_integration` |
| `game_hardware_requirements` | `GameHardwareRequirement` | `RequirementRepository` | `RequirementService` | playability/admin | public/shareable/personal | `test_game_hardware_requirements_integration` |
| `personal_playability` | `PersonalPlayability` | `PlayabilityRepository` | `PlayabilityService` | playability * | personal/shareable agregado | `test_personal_playability_integration` |
| `run_tasks` | `RunTask` | `RunTaskRepository` | `QueueService` | queue * | technical | `test_run_tasks_integration` |
| `review_queue` | `ReviewItem` | `ReviewRepository` | `ReviewService` | review * | technical redigido | `test_review_queue_integration` |
| `change_log` | `ChangeLogEntry` | `ChangeLogRepository` | `ChangeLogService` | run show audit | technical redigido | `test_change_log_integration` |

Tabelas associativas usam o repository/service do agregado; isso é deliberado e evita componentes artificiais.
