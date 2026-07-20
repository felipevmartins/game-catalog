# 08 — Modelo Relacional Detalhado v1.3

## 1. Regras comuns

- Toda PK textual de entidade é UUIDv7 canônica; `schema_metadata.id=1` e PKs compostas de associações são exceções técnicas declaradas.
- O CHECK UUID valida comprimento, hífens, hexadecimal, versão 7 e variante RFC 4122.
- `created_at`/`updated_at` são UTC.
- `deleted_at` indica soft delete; registros pessoais não são soft-deletados automaticamente.
- Checks de calendário gregoriano completo ficam no domínio; SQLite garante estrutura/ranges de PartialDate.
- `NULL` significa desconhecido/não aplicável conforme o campo; strings vazias são normalizadas para NULL.
- Índices condicionais usam partial indexes do SQLite quando indicado.
- FKs polimórficas existem apenas em proveniência/revisão/auditoria e são limitadas por allowlist, service e auditoria de integridade.

## 2. Diagrama lógico

```text
schema_metadata
execution_runs -> backups
execution_runs -> run_tasks
execution_runs -> change_log
regions -> releases/products/game_aliases/availability_offers
manufacturers -> ecosystems/platforms/hardware_models/accessory_models
companies -> franchises/franchise_ownerships/products/availability_offers/game_companies
franchises -> franchise_ecosystems -> ecosystems
franchises -> franchise_ownerships
franchises -> games -> game_editions -> releases -> products
games -> game_aliases/game_relations/game_contents/game_companies/game_lengths
game_scores -> game_primary_scores -> games
releases -> game_scores/availability_offers/personal_collection_items
releases -> game_requirement_groups -> game_hardware_requirements
releases -> personal_playability
sources -> source_references -> record_source_links/catalog_assertions
source_references -> review_queue
sources -> *_external_ids
games -> game_external_ids
game_editions -> edition_external_ids
releases -> release_external_ids
platforms -> platform_external_ids
companies -> company_external_ids
franchises -> franchise_external_ids
products -> product_external_ids
hardware_models -> hardware_model_external_ids
games -> platform_lock_assessments -> game_platform_lock_reasons -> platform_lock_reasons
hardware_models -> personal_hardware_units
personal_capabilities
hardware_models -> hardware_compatibility_rules -> compatibility_rule_releases -> releases
accessory_models -> accessory_platforms -> platforms
accessory_models -> personal_accessory_units
run_tasks -> sources (optional)
```

## 3. Contratos reutilizados

### UUIDv7

PKs UUID usam CHECK equivalente a: formato `8-4-4-4-12`, caracteres hexadecimais, `substr(id,15,1)='7'` e `lower(substr(id,20,1)) IN ('8','9','a','b')`. Seeds são constantes UUIDv7 pré-geradas, não IDs determinísticos por nome.

### PartialDate

Para cada prefixo existem `*_year`, `*_month`, `*_day`, `*_precision`, `*_qualifier`. `precision=unknown` exige componentes e qualifier nulos; `year` exige só ano; `month` exige ano/mês; `day` exige os três. Qualifier é `circa|before|after` ou NULL (exato).

### Dinheiro

Cada par `*_amount_minor`/`*_currency_code` é ambos NULL ou ambos preenchidos; amount não negativo. A aplicação usa o expoente ISO 4217 da moeda, sem assumir duas casas.

### Identidade estável

`identity_discriminator` é uma chave opaca, persistida e imutável dentro do pai lógico. `identity_key` é derivada somente de UUIDs de escopo e discriminator; datas, títulos, tipos classificatórios, mídia, SKU, loja e nomes não participam da identidade.

## 4. Tabelas

### 4.1 `schema_metadata`

Registra a versão lógica do schema e versões mínimas compatíveis.

- **Classificação:** operacional
- **Owner arquitetural:** `MigrationRepository`
- **Migration:** `0001_foundation`
- **Exclusão:** não é excluída
- **Atualização:** somente migrations

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `id` | INTEGER | não | PK fixa = 1 |
| `schema_version` | TEXT | não | versão Alembic aplicada |
| `minimum_app_version` | TEXT | não | versão mínima da aplicação |
| `updated_at` | TEXT UTC timestamp | não | UTC |

**Checks/invariantes locais:** id = 1.

### 4.2 `execution_runs`

Máquina de estados única para qualquer operação relevante, incluindo edições manuais.

- **Classificação:** operacional
- **Owner arquitetural:** `ExecutionRunRepository`
- **Migration:** `0001_foundation`
- **Exclusão:** RESTRICT; runs são retidos
- **Atualização:** ExecutionService por transições válidas

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `id` | TEXT UUIDv7 | não | PK |
| `execution_type` | TEXT | não | import\|update\|recalculate\|export\|backup\|restore\|migration\|merge\|maintenance\|manual_edit |
| `status` | TEXT | não | queued\|running\|succeeded\|succeeded_with_warnings\|failed\|cancelled |
| `requested_by` | TEXT | não | cli\|scheduler\|migration\|system |
| `dry_run` | INTEGER boolean | não | default 0 |
| `parameters_json` | TEXT JSON | sim | filtros sem segredos |
| `application_version` | TEXT | não |  |
| `schema_version` | TEXT | não |  |
| `started_at` | TEXT UTC timestamp | sim | primeiro início; pode permanecer após recuperação para queued |
| `heartbeat_at` | TEXT UTC timestamp | sim |  |
| `finished_at` | TEXT UTC timestamp | sim |  |
| `backup_id` | TEXT UUIDv7 | sim | FK backups ON DELETE RESTRICT; preenchida após backup válido |
| `summary_json` | TEXT JSON | sim | contagens |
| `error_summary_redacted` | TEXT | sim | sem caminhos/credenciais/dados pessoais |
| `created_at` | TEXT UTC timestamp | não |  |

**Checks/invariantes locais:** running exige started_at e heartbeat_at; estado terminal exige finished_at; queued/running não possuem finished_at.

**Índices:** `(status, created_at)`; `(execution_type, created_at)`.
### 4.3 `backups`

Manifesto dos backups íntegros e restaurações.

- **Classificação:** operacional privado
- **Owner arquitetural:** `BackupRepository`
- **Migration:** `0001_foundation`
- **Exclusão:** arquivo removido só pela política de retenção; linha recebe deleted_at
- **Atualização:** BackupService

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `id` | TEXT UUIDv7 | não | PK |
| `backup_type` | TEXT | não | operational\|daily\|weekly\|monthly\|release\|audit_snapshot |
| `file_name` | TEXT | não | nome sem diretório |
| `file_path` | TEXT | não | caminho local privado |
| `size_bytes` | INTEGER | não | >= 0 |
| `sha256` | TEXT | não | 64 hex |
| `schema_version` | TEXT | não |  |
| `application_version` | TEXT | não |  |
| `integrity_status` | TEXT | não | pending\|valid\|invalid |
| `related_run_id` | TEXT UUIDv7 | sim | FK execution_runs ON DELETE RESTRICT |
| `created_at` | TEXT UTC timestamp | não |  |
| `verified_at` | TEXT UTC timestamp | sim |  |
| `retained` | INTEGER boolean | não | default 0 |
| `retention_reason` | TEXT | sim | motivo explícito de preservação |
| `deleted_at` | TEXT UTC timestamp | sim | remoção física já realizada |
| `restored_at` | TEXT UTC timestamp | sim | última restauração |

**Checks/invariantes locais:** size_bytes >= 0; integrity_status = valid para uso em restore; retained=1 exige retention_reason.

**Índices:** `sha256`; `(backup_type, created_at)`; `(integrity_status, created_at)`; `related_run_id`.
### 4.4 `regions`

Vocabulário controlado de países, mercados editoriais e região global.

- **Classificação:** catálogo público
- **Owner arquitetural:** `RegionRepository`
- **Migration:** `0002_reference_catalog`
- **Exclusão:** RESTRICT; desativar em vez de excluir quando referenciada
- **Atualização:** seed/migration e CatalogService

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `id` | TEXT UUIDv7 | não | PK |
| `code` | TEXT | não | ISO 3166-1 alpha-2 ou WORLD/EU/NA/OTHER |
| `name` | TEXT | não | nome público |
| `region_type` | TEXT | não | country\|market\|global\|other |
| `parent_region_id` | TEXT UUIDv7 | sim | FK regions ON DELETE RESTRICT |
| `active` | INTEGER boolean | não | default 1 |
| `created_at` | TEXT UTC timestamp | não |  |
| `updated_at` | TEXT UTC timestamp | não |  |

**Unicidades:** `code`.

**Checks/invariantes locais:** parent_region_id <> id.

**Índices:** `region_type`; `parent_region_id`; `active`.

### 4.5 `manufacturers`

Fabricantes de hardware/plataformas.

- **Classificação:** catálogo público
- **Owner arquitetural:** `ManufacturerRepository`
- **Migration:** `0002_reference_catalog`
- **Exclusão:** soft delete; FK RESTRICT
- **Atualização:** CatalogService; importadores via política de fontes

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `id` | TEXT UUIDv7 | não | PK |
| `name` | TEXT | não | nome canônico |
| `normalized_name` | TEXT | não | busca/deduplicação |
| `country_code` | TEXT | sim | ISO 3166-1 alpha-2 |
| `notes` | TEXT | sim | público editorial |
| `created_at` | TEXT UTC timestamp | não |  |
| `updated_at` | TEXT UTC timestamp | não |  |
| `deleted_at` | TEXT UTC timestamp | sim | soft delete |

**Unicidades:** `normalized_name WHERE deleted_at IS NULL`.

**Índices:** `normalized_name`.

### 4.6 `ecosystems`

Famílias de plataformas, não grupos empresariais adquiridos.

- **Classificação:** catálogo público
- **Owner arquitetural:** `EcosystemRepository`
- **Migration:** `0002_reference_catalog`
- **Exclusão:** soft delete; RESTRICT
- **Atualização:** CatalogService

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `id` | TEXT UUIDv7 | não | PK |
| `name` | TEXT | não | PlayStation, Xbox, Nintendo etc. |
| `normalized_name` | TEXT | não |  |
| `manufacturer_id` | TEXT UUIDv7 | sim | FK manufacturers ON DELETE RESTRICT |
| `ecosystem_type` | TEXT | não | console_family\|pc\|arcade\|mobile\|cloud\|other |
| `parent_ecosystem_id` | TEXT UUIDv7 | sim | FK ecosystems ON DELETE RESTRICT |
| `created_at` | TEXT UTC timestamp | não |  |
| `updated_at` | TEXT UTC timestamp | não |  |
| `deleted_at` | TEXT UTC timestamp | sim |  |

**Unicidades:** `normalized_name WHERE deleted_at IS NULL`.

**Checks/invariantes locais:** parent_ecosystem_id <> id.

**Índices:** `manufacturer_id`; `parent_ecosystem_id`.

### 4.7 `companies`

Desenvolvedoras, publicadoras, distribuidoras, lojas e proprietárias de IP. `company_type` é classificação principal não exclusiva; papéis concretos são registrados nas relações.

- **Classificação:** catálogo público
- **Owner arquitetural:** `CompanyRepository`
- **Migration:** `0002_reference_catalog`
- **Exclusão:** soft delete; RESTRICT
- **Atualização:** CatalogService/SourceResolutionService

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `id` | TEXT UUIDv7 | não | PK |
| `name` | TEXT | não |  |
| `normalized_name` | TEXT | não |  |
| `company_type` | TEXT | não | developer\|publisher\|platform_holder\|distributor\|store\|holding\|other; classificação principal |
| `parent_company_id` | TEXT UUIDv7 | sim | FK companies ON DELETE RESTRICT |
| `country_code` | TEXT | sim | ISO 3166-1 alpha-2 |
| `website` | TEXT | sim |  |
| `created_at` | TEXT UTC timestamp | não |  |
| `updated_at` | TEXT UTC timestamp | não |  |
| `deleted_at` | TEXT UTC timestamp | sim |  |

**Unicidades:** `(normalized_name, COALESCE(country_code, '')) WHERE deleted_at IS NULL`.

**Checks/invariantes locais:** parent_company_id <> id.

**Índices:** `normalized_name`; `parent_company_id`; `company_type`.
### 4.8 `franchises`

Franquias e sub-séries por relação pai. A proprietária atual é derivada de `franchise_ownerships`, não duplicada nesta tabela.

- **Classificação:** catálogo público
- **Owner arquitetural:** `FranchiseRepository`
- **Migration:** `0002_reference_catalog`
- **Exclusão:** soft delete; RESTRICT
- **Atualização:** FranchiseService; status derivado/manual conforme fonte

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `id` | TEXT UUIDv7 | não | PK |
| `name` | TEXT | não |  |
| `normalized_name` | TEXT | não |  |
| `parent_franchise_id` | TEXT UUIDv7 | sim | FK franchises ON DELETE RESTRICT |
| `status` | TEXT | não | active\|hiatus\|officially_ended\|unknown |
| `status_reason` | TEXT | sim | evidência/razão editorial |
| `official_end_confirmed` | INTEGER boolean | não | default 0 |
| `created_at` | TEXT UTC timestamp | não |  |
| `updated_at` | TEXT UTC timestamp | não |  |
| `deleted_at` | TEXT UTC timestamp | sim |  |

**Unicidades:** `(normalized_name, COALESCE(parent_franchise_id, '')) WHERE deleted_at IS NULL`.

**Checks/invariantes locais:** parent_franchise_id <> id; status=officially_ended implica official_end_confirmed=1.

**Índices:** `parent_franchise_id`; `status`.
### 4.9 `franchise_ecosystems`

Associa franquias a ecossistemas sem alegar propriedade jurídica.

- **Classificação:** catálogo público
- **Owner arquitetural:** `FranchiseRepository`
- **Migration:** `0002_reference_catalog`
- **Exclusão:** CASCADE apenas a partir da franquia soft-deleted não ocorre; remoção explícita da associação
- **Atualização:** FranchiseService

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `id` | TEXT UUIDv7 | não | PK |
| `franchise_id` | TEXT UUIDv7 | não | FK franchises ON DELETE CASCADE |
| `ecosystem_id` | TEXT UUIDv7 | não | FK ecosystems ON DELETE RESTRICT |
| `association_type` | TEXT | não | first_party\|second_party\|owned_ip\|historical\|strong_association\|other |
| `valid_from_year` | INTEGER | sim | ano histórico |
| `valid_to_year` | INTEGER | sim | ano histórico |
| `notes` | TEXT | sim |  |

**Unicidades:** `(franchise_id, ecosystem_id, association_type, COALESCE(valid_from_year, -1))`.

**Checks/invariantes locais:** valid_to_year IS NULL OR valid_from_year IS NULL OR valid_to_year >= valid_from_year.

**Índices:** `ecosystem_id`; `franchise_id`.

### 4.10 `platforms`

Plataformas de execução ou distribuição.

- **Classificação:** catálogo público
- **Owner arquitetural:** `PlatformRepository`
- **Migration:** `0002_reference_catalog`
- **Exclusão:** soft delete; RESTRICT
- **Atualização:** PlatformService

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `id` | TEXT UUIDv7 | não | PK |
| `name` | TEXT | não |  |
| `normalized_name` | TEXT | não |  |
| `manufacturer_id` | TEXT UUIDv7 | sim | FK manufacturers |
| `ecosystem_id` | TEXT UUIDv7 | sim | FK ecosystems |
| `platform_type` | TEXT | não | home_console\|portable_console\|hybrid_console\|pc\|arcade\|mobile\|cloud\|other |
| `release_year` | INTEGER | sim | conceito anual, não PartialDate |
| `discontinuation_year` | INTEGER | sim |  |
| `created_at` | TEXT UTC timestamp | não |  |
| `updated_at` | TEXT UTC timestamp | não |  |
| `deleted_at` | TEXT UTC timestamp | sim |  |

**Unicidades:** `normalized_name WHERE deleted_at IS NULL`.

**Checks/invariantes locais:** discontinuation_year IS NULL OR release_year IS NULL OR discontinuation_year >= release_year.

**Índices:** `manufacturer_id`; `ecosystem_id`; `platform_type`.

### 4.11 `games`

Obras conceituais; não contém plataforma, região, mídia ou loja.

- **Classificação:** catálogo público
- **Owner arquitetural:** `GameRepository`
- **Migration:** `0003_game_identity`
- **Exclusão:** soft delete; merges redirecionam dependências antes
- **Atualização:** IdentityService/CatalogService

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `id` | TEXT UUIDv7 | não | PK |
| `canonical_title` | TEXT | não |  |
| `normalized_title` | TEXT | não | busca, não identidade |
| `franchise_id` | TEXT UUIDv7 | sim | FK franchises |
| `game_type` | TEXT | não | main\|spin_off\|remake\|reboot\|compilation\|standalone_expansion\|other |
| `campaign_focus` | TEXT | não | primary\|significant\|minor\|none\|unknown |
| `online_only` | INTEGER boolean | não | default 0 |
| `regional_only` | INTEGER boolean | não | default 0 |
| `historically_relevant` | INTEGER boolean | não | default 0 |
| `collector_relevant` | INTEGER boolean | não | default 0 |
| `notes` | TEXT | sim | público editorial |
| `created_at` | TEXT UTC timestamp | não |  |
| `updated_at` | TEXT UTC timestamp | não |  |
| `deleted_at` | TEXT UTC timestamp | sim |  |

**Índices:** `normalized_title`; `franchise_id`; `game_type`.

### 4.12 `game_editions`

Edições editoriais ou técnicas de um Game. Nome e tipo são atributos corrigíveis; identidade usa discriminator persistido.

- **Classificação:** catálogo público
- **Owner arquitetural:** `EditionRepository`
- **Migration:** `0003_game_identity`
- **Exclusão:** soft delete; RESTRICT
- **Atualização:** IdentityService

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `id` | TEXT UUIDv7 | não | PK |
| `game_id` | TEXT UUIDv7 | não | FK games ON DELETE RESTRICT |
| `identity_discriminator` | TEXT | não | opaco, estável e imutável dentro do Game |
| `name` | TEXT | não | Original, HD Remaster etc. |
| `normalized_name` | TEXT | não | busca, não identidade |
| `edition_type` | TEXT | não | original\|remaster\|enhanced\|directors_cut\|definitive\|complete\|goty\|technical_variant\|regional_variant\|other |
| `is_definitive` | INTEGER boolean | não | default 0 |
| `notes` | TEXT | sim |  |
| `created_at` | TEXT UTC timestamp | não |  |
| `updated_at` | TEXT UTC timestamp | não |  |
| `deleted_at` | TEXT UTC timestamp | sim |  |

**Unicidades:** `(game_id, identity_discriminator) WHERE deleted_at IS NULL`; `game_id WHERE edition_type='original' AND deleted_at IS NULL`.

**Checks/invariantes locais:** identity_discriminator não vazio.

**Índices:** `game_id`; `edition_type`; `normalized_name`.
### 4.13 `releases`

Disponibilização de uma Edition numa plataforma, região e período.

- **Classificação:** catálogo público
- **Owner arquitetural:** `ReleaseRepository`
- **Migration:** `0003_game_identity`
- **Exclusão:** soft delete; RESTRICT
- **Atualização:** IdentityService; reimportação resolve por external ID e chave estrutural estável

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `id` | TEXT UUIDv7 | não | PK |
| `edition_id` | TEXT UUIDv7 | não | FK game_editions ON DELETE RESTRICT |
| `platform_id` | TEXT UUIDv7 | não | FK platforms ON DELETE RESTRICT |
| `region_id` | TEXT UUIDv7 | não | FK regions ON DELETE RESTRICT |
| `release_type` | TEXT | não | original\|port\|rerelease |
| `identity_discriminator` | TEXT | não | opaco, estável e imutável; default `default` quando inequívoco |
| `release_year` | INTEGER | sim | PartialDate.year |
| `release_month` | INTEGER | sim | PartialDate.month |
| `release_day` | INTEGER | sim | PartialDate.day |
| `release_precision` | TEXT | não | unknown\|year\|month\|day |
| `release_qualifier` | TEXT | sim | circa\|before\|after; NULL = exato |
| `identity_key` | TEXT | não | edition/platform/region/discriminator; não inclui release_type/data/título |
| `official` | INTEGER boolean | não | default 1 |
| `notes` | TEXT | sim |  |
| `created_at` | TEXT UTC timestamp | não |  |
| `updated_at` | TEXT UTC timestamp | não |  |
| `deleted_at` | TEXT UTC timestamp | sim |  |

**Unicidades:** `identity_key WHERE deleted_at IS NULL`; `(edition_id, platform_id, region_id, identity_discriminator) WHERE deleted_at IS NULL`.

**Checks/invariantes locais:** contrato PartialDate estrutural; identity_discriminator não vazio; identity_key não usa fatos mutáveis.

**Índices:** `edition_id`; `platform_id`; `(platform_id, region_id)`; `release_year`.
### 4.14 `products`

Item comercial opcional de uma única Release: mídia, formato, loja ou SKU. Bundle multi-Release e produto detalhado de DLC são pós-MVP.

- **Classificação:** catálogo público/external
- **Owner arquitetural:** `ProductRepository`
- **Migration:** `0003_game_identity`
- **Exclusão:** soft delete; RESTRICT por itens pessoais
- **Atualização:** IdentityService

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `id` | TEXT UUIDv7 | não | PK |
| `release_id` | TEXT UUIDv7 | não | FK releases ON DELETE RESTRICT |
| `product_type` | TEXT | não | physical\|digital\|license\|single_release_bundle\|subscription_entitlement\|other |
| `media_format` | TEXT | sim | disc\|cartridge\|download\|code\|cloud\|other |
| `store_company_id` | TEXT UUIDv7 | sim | FK companies; loja/provedor |
| `sku` | TEXT | sim | ID comercial da loja |
| `region_id` | TEXT UUIDv7 | sim | FK regions ON DELETE RESTRICT |
| `display_name` | TEXT | sim | nome comercial |
| `identity_discriminator` | TEXT | não | opaco, estável e imutável |
| `identity_key` | TEXT | não | release UUID + discriminator; não inclui SKU/mídia/nome |
| `created_at` | TEXT UTC timestamp | não |  |
| `updated_at` | TEXT UTC timestamp | não |  |
| `deleted_at` | TEXT UTC timestamp | sim |  |

**Unicidades:** `identity_key WHERE deleted_at IS NULL`; `(release_id, identity_discriminator) WHERE deleted_at IS NULL`; `(store_company_id, sku, COALESCE(region_id, '')) WHERE sku IS NOT NULL AND deleted_at IS NULL`.

**Checks/invariantes locais:** identity_discriminator não vazio.

**Índices:** `release_id`; `store_company_id`; `sku`; `region_id`.
### 4.15 `game_aliases`

Aliases persistidos apenas para busca, região, idioma ou compatibilidade de importação.

- **Classificação:** catálogo público/external
- **Owner arquitetural:** `GameRepository`
- **Migration:** `0003_game_identity`
- **Exclusão:** CASCADE com game apenas após merge/remoção controlada
- **Atualização:** IdentityService; não criar alias cosmético sem uso

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `id` | TEXT UUIDv7 | não | PK |
| `game_id` | TEXT UUIDv7 | não | FK games ON DELETE CASCADE |
| `alias` | TEXT | não |  |
| `normalized_alias` | TEXT | não |  |
| `alias_type` | TEXT | não | regional_title\|original_title\|transliteration\|former_title\|import_alias |
| `language_code` | TEXT | sim | BCP 47 |
| `region_id` | TEXT UUIDv7 | sim | FK regions ON DELETE RESTRICT |
| `source_reference_id` | TEXT UUIDv7 | sim | FK source_references adicionada em 0004; inicialmente nullable |
| `created_at` | TEXT UTC timestamp | não |  |

**Unicidades:** `(game_id, normalized_alias, alias_type, COALESCE(language_code, ''), COALESCE(region_id, ''))`.

**Índices:** `normalized_alias`; `game_id`; `region_id`.
### 4.16 `game_relations`

Relações semânticas entre Games por UUID.

- **Classificação:** catálogo público
- **Owner arquitetural:** `GameRelationRepository`
- **Migration:** `0003_game_identity`
- **Exclusão:** RESTRICT; remoção explícita
- **Atualização:** IdentityService/ReviewService

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `id` | TEXT UUIDv7 | não | PK |
| `source_game_id` | TEXT UUIDv7 | não | FK games ON DELETE RESTRICT |
| `target_game_id` | TEXT UUIDv7 | não | FK games ON DELETE RESTRICT |
| `relation_type` | TEXT | não | remake_of\|reboot_of\|sequel_to\|prequel_to\|spin_off_of\|standalone_expansion_of\|same_title_variant_of\|compilation_contains\|spiritual_successor_of |
| `confidence` | TEXT | não | high\|medium\|low |
| `notes` | TEXT | sim |  |
| `created_at` | TEXT UTC timestamp | não |  |
| `updated_at` | TEXT UTC timestamp | não |  |

**Unicidades:** `(source_game_id, target_game_id, relation_type)`.

**Checks/invariantes locais:** source_game_id <> target_game_id.

**Índices:** `source_game_id`; `target_game_id`; `relation_type`.

### 4.17 `game_contents`

Conteúdo dependente ou episódios que não justificam Game próprio. Título/tipo podem ser corrigidos sem alterar identidade.

- **Classificação:** catálogo público
- **Owner arquitetural:** `GameContentRepository`
- **Migration:** `0003_game_identity`
- **Exclusão:** soft delete
- **Atualização:** CatalogService

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `id` | TEXT UUIDv7 | não | PK |
| `parent_game_id` | TEXT UUIDv7 | não | FK games ON DELETE RESTRICT |
| `identity_discriminator` | TEXT | não | opaco, estável e imutável dentro do Game |
| `title` | TEXT | não |  |
| `normalized_title` | TEXT | não | busca, não identidade |
| `content_type` | TEXT | não | dlc\|expansion\|episode\|campaign\|add_on |
| `requires_base_game` | INTEGER boolean | não |  |
| `sequence_number` | INTEGER | sim | episódios |
| `notes` | TEXT | sim |  |
| `created_at` | TEXT UTC timestamp | não |  |
| `updated_at` | TEXT UTC timestamp | não |  |
| `deleted_at` | TEXT UTC timestamp | sim |  |

**Unicidades:** `(parent_game_id, identity_discriminator) WHERE deleted_at IS NULL`.

**Checks/invariantes locais:** identity_discriminator não vazio; sequence_number IS NULL OR sequence_number > 0.

**Índices:** `parent_game_id`; `content_type`; `normalized_title`.
### 4.18 `sources`

Configuração persistente de fontes e seus contratos.

- **Classificação:** externo operacional
- **Owner arquitetural:** `SourceRepository`
- **Migration:** `0004_sources_and_external_ids`
- **Exclusão:** RESTRICT; desabilitar em vez de excluir
- **Atualização:** SourceService; mudança de contrato bloqueia coletor até revisão

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `id` | TEXT UUIDv7 | não | PK |
| `code` | TEXT | não | chave da configuração |
| `name` | TEXT | não |  |
| `source_type` | TEXT | não | official\|store\|database\|collaborative\|review_aggregator\|duration_aggregator\|archive\|press\|community\|manual\|other |
| `integration_type` | TEXT | não | api\|sparql\|manual\|file\|permitted_http\|none |
| `base_url` | TEXT | sim |  |
| `priority` | INTEGER | não | 0..100 |
| `default_confidence` | TEXT | não | high\|medium\|low |
| `enabled` | INTEGER boolean | não |  |
| `credential_required` | INTEGER boolean | não |  |
| `terms_url` | TEXT | sim |  |
| `terms_reviewed_at` | TEXT UTC timestamp | sim |  |
| `contract_version` | TEXT | sim |  |
| `license_name` | TEXT | sim |  |
| `attribution_text` | TEXT | sim |  |
| `redistribution_policy` | TEXT | não | allowed\|attribution_required\|restricted\|prohibited\|unknown |
| `default_ttl_days` | INTEGER | sim | >=0 |
| `created_at` | TEXT UTC timestamp | não |  |
| `updated_at` | TEXT UTC timestamp | não |  |

**Unicidades:** `code`.

**Checks/invariantes locais:** priority BETWEEN 0 AND 100; default_ttl_days IS NULL OR default_ttl_days >= 0.

**Índices:** `source_type`; `enabled`.

### 4.19 `source_references`

Evidência por registro/alteração; guarda coleta, verificação e validade.

- **Classificação:** externo
- **Owner arquitetural:** `SourceReferenceRepository`
- **Migration:** `0004_sources_and_external_ids`
- **Exclusão:** RESTRICT enquanto referenciada
- **Atualização:** Collector/SourceService; ausência em resposta não apaga referência

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `id` | TEXT UUIDv7 | não | PK |
| `source_id` | TEXT UUIDv7 | não | FK sources ON DELETE RESTRICT |
| `source_record_id` | TEXT | sim | ID na origem |
| `source_url` | TEXT | sim | URL ou locator |
| `retrieved_at` | TEXT UTC timestamp | não | momento da coleta |
| `verified_at` | TEXT UTC timestamp | sim | momento da verificação humana/automática |
| `valid_until` | TEXT UTC timestamp | sim | TTL materializado |
| `content_hash` | TEXT | sim | hash da resposta/arquivo |
| `source_contract_version` | TEXT | sim | snapshot do contrato |
| `notes` | TEXT | sim | sem dados pessoais |
| `created_at` | TEXT UTC timestamp | não |  |

**Unicidades:** `(source_id, source_record_id, content_hash) WHERE source_record_id IS NOT NULL`.

**Checks/invariantes locais:** source_record_id IS NOT NULL OR source_url IS NOT NULL.

**Índices:** `source_id`; `valid_until`; `verified_at`.

### 4.20 `record_source_links`

Proveniência por registro para entidades cujo schema não possui FK de fonte própria. Não substitui assertions de campo.

- **Classificação:** externo operacional
- **Owner arquitetural:** `SourceReferenceRepository`
- **Migration:** `0004_sources_and_external_ids`
- **Exclusão:** RESTRICT; entidade alvo é validada pelo service/auditoria
- **Atualização:** SourceResolutionService

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `id` | TEXT UUIDv7 | não | PK |
| `entity_type` | TEXT | não | allowlist de entidades de catálogo |
| `entity_id` | TEXT UUIDv7 | não | UUID interno |
| `source_reference_id` | TEXT UUIDv7 | não | FK source_references ON DELETE CASCADE |
| `link_role` | TEXT | não | primary\|supporting\|historical |
| `created_at` | TEXT UTC timestamp | não |  |

**Unicidades:** `(entity_type, entity_id, source_reference_id, link_role)`; no máximo um `primary` por entidade via partial unique index.

**Índices:** `(entity_type, entity_id)`; `source_reference_id`.

### 4.21 `catalog_assertions`

Observações por campo apenas para campos sujeitos a conflito independente.

- **Classificação:** externo operacional
- **Owner arquitetural:** `AssertionRepository`
- **Migration:** `0004_sources_and_external_ids`
- **Exclusão:** RESTRICT; superseded preserva histórico
- **Atualização:** SourceResolutionService; não é universal

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `id` | TEXT UUIDv7 | não | PK |
| `entity_type` | TEXT | não | allowlist de entidades de catálogo |
| `entity_id` | TEXT UUIDv7 | não | UUID interno; integridade auditada pelo serviço |
| `field_name` | TEXT | não | allowlist por entidade |
| `value_json` | TEXT JSON | não | valor normalizado |
| `raw_value_json` | TEXT JSON | sim | valor recebido |
| `source_reference_id` | TEXT UUIDv7 | não | FK source_references ON DELETE RESTRICT |
| `confidence` | TEXT | não | high\|medium\|low |
| `status` | TEXT | não | candidate\|accepted\|rejected\|superseded\|conflict |
| `is_manual_override` | INTEGER boolean | não | default 0 |
| `observed_at` | TEXT UTC timestamp | não |  |
| `last_verified_at` | TEXT UTC timestamp | sim |  |
| `created_at` | TEXT UTC timestamp | não |  |
| `updated_at` | TEXT UTC timestamp | não |  |

**Unicidades:** `(entity_type, entity_id, field_name, source_reference_id, value_json)`; `(entity_type, entity_id, field_name) WHERE status='accepted'`.

**Checks/invariantes locais:** is_manual_override=1 implica status='accepted'.

**Índices:** `(entity_type, entity_id, field_name, status)`; `source_reference_id`; `last_verified_at`.
### 4.22 `game_external_ids`

IDs externos de game; nunca são PK interna.

- **Classificação:** externo
- **Owner arquitetural:** `ExternalIdentifierRepository`
- **Migration:** `0004_sources_and_external_ids`
- **Exclusão:** CASCADE com games; merges movem IDs e rejeitam colisão
- **Atualização:** IdentityService/ExternalIdentifierRepository

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `id` | TEXT UUIDv7 | não | PK |
| `game_id` | TEXT UUIDv7 | não | FK games ON DELETE CASCADE |
| `source_id` | TEXT UUIDv7 | não | FK sources ON DELETE RESTRICT |
| `external_id` | TEXT | não | ID opaco da fonte |
| `context` | TEXT | não | default global; região/namespace quando necessário |
| `is_primary` | INTEGER boolean | não | default 0 |
| `created_at` | TEXT UTC timestamp | não |  |
| `updated_at` | TEXT UTC timestamp | não |  |

**Unicidades:** `(source_id, external_id, context)`; `(game_id, source_id, context) WHERE is_primary = 1`.

**Índices:** `game_id`; `(source_id, external_id, context)`.

### 4.23 `edition_external_ids`

IDs externos de edition; nunca são PK interna.

- **Classificação:** externo
- **Owner arquitetural:** `ExternalIdentifierRepository`
- **Migration:** `0004_sources_and_external_ids`
- **Exclusão:** CASCADE com game_editions; merges movem IDs e rejeitam colisão
- **Atualização:** IdentityService/ExternalIdentifierRepository

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `id` | TEXT UUIDv7 | não | PK |
| `edition_id` | TEXT UUIDv7 | não | FK game_editions ON DELETE CASCADE |
| `source_id` | TEXT UUIDv7 | não | FK sources ON DELETE RESTRICT |
| `external_id` | TEXT | não | ID opaco da fonte |
| `context` | TEXT | não | default global; região/namespace quando necessário |
| `is_primary` | INTEGER boolean | não | default 0 |
| `created_at` | TEXT UTC timestamp | não |  |
| `updated_at` | TEXT UTC timestamp | não |  |

**Unicidades:** `(source_id, external_id, context)`; `(edition_id, source_id, context) WHERE is_primary = 1`.

**Índices:** `edition_id`; `(source_id, external_id, context)`.

### 4.24 `release_external_ids`

IDs externos de release; nunca são PK interna.

- **Classificação:** externo
- **Owner arquitetural:** `ExternalIdentifierRepository`
- **Migration:** `0004_sources_and_external_ids`
- **Exclusão:** CASCADE com releases; merges movem IDs e rejeitam colisão
- **Atualização:** IdentityService/ExternalIdentifierRepository

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `id` | TEXT UUIDv7 | não | PK |
| `release_id` | TEXT UUIDv7 | não | FK releases ON DELETE CASCADE |
| `source_id` | TEXT UUIDv7 | não | FK sources ON DELETE RESTRICT |
| `external_id` | TEXT | não | ID opaco da fonte |
| `context` | TEXT | não | default global; região/namespace quando necessário |
| `is_primary` | INTEGER boolean | não | default 0 |
| `created_at` | TEXT UTC timestamp | não |  |
| `updated_at` | TEXT UTC timestamp | não |  |

**Unicidades:** `(source_id, external_id, context)`; `(release_id, source_id, context) WHERE is_primary = 1`.

**Índices:** `release_id`; `(source_id, external_id, context)`.

### 4.25 `platform_external_ids`

IDs externos de platform; nunca são PK interna.

- **Classificação:** externo
- **Owner arquitetural:** `ExternalIdentifierRepository`
- **Migration:** `0004_sources_and_external_ids`
- **Exclusão:** CASCADE com platforms; merges movem IDs e rejeitam colisão
- **Atualização:** IdentityService/ExternalIdentifierRepository

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `id` | TEXT UUIDv7 | não | PK |
| `platform_id` | TEXT UUIDv7 | não | FK platforms ON DELETE CASCADE |
| `source_id` | TEXT UUIDv7 | não | FK sources ON DELETE RESTRICT |
| `external_id` | TEXT | não | ID opaco da fonte |
| `context` | TEXT | não | default global; região/namespace quando necessário |
| `is_primary` | INTEGER boolean | não | default 0 |
| `created_at` | TEXT UTC timestamp | não |  |
| `updated_at` | TEXT UTC timestamp | não |  |

**Unicidades:** `(source_id, external_id, context)`; `(platform_id, source_id, context) WHERE is_primary = 1`.

**Índices:** `platform_id`; `(source_id, external_id, context)`.

### 4.26 `company_external_ids`

IDs externos de company; nunca são PK interna.

- **Classificação:** externo
- **Owner arquitetural:** `ExternalIdentifierRepository`
- **Migration:** `0004_sources_and_external_ids`
- **Exclusão:** CASCADE com companies; merges movem IDs e rejeitam colisão
- **Atualização:** IdentityService/ExternalIdentifierRepository

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `id` | TEXT UUIDv7 | não | PK |
| `company_id` | TEXT UUIDv7 | não | FK companies ON DELETE CASCADE |
| `source_id` | TEXT UUIDv7 | não | FK sources ON DELETE RESTRICT |
| `external_id` | TEXT | não | ID opaco da fonte |
| `context` | TEXT | não | default global; região/namespace quando necessário |
| `is_primary` | INTEGER boolean | não | default 0 |
| `created_at` | TEXT UTC timestamp | não |  |
| `updated_at` | TEXT UTC timestamp | não |  |

**Unicidades:** `(source_id, external_id, context)`; `(company_id, source_id, context) WHERE is_primary = 1`.

**Índices:** `company_id`; `(source_id, external_id, context)`.

### 4.27 `franchise_external_ids`

IDs externos de franchise; nunca são PK interna.

- **Classificação:** externo
- **Owner arquitetural:** `ExternalIdentifierRepository`
- **Migration:** `0004_sources_and_external_ids`
- **Exclusão:** CASCADE com franchises; merges movem IDs e rejeitam colisão
- **Atualização:** IdentityService/ExternalIdentifierRepository

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `id` | TEXT UUIDv7 | não | PK |
| `franchise_id` | TEXT UUIDv7 | não | FK franchises ON DELETE CASCADE |
| `source_id` | TEXT UUIDv7 | não | FK sources ON DELETE RESTRICT |
| `external_id` | TEXT | não | ID opaco da fonte |
| `context` | TEXT | não | default global; região/namespace quando necessário |
| `is_primary` | INTEGER boolean | não | default 0 |
| `created_at` | TEXT UTC timestamp | não |  |
| `updated_at` | TEXT UTC timestamp | não |  |

**Unicidades:** `(source_id, external_id, context)`; `(franchise_id, source_id, context) WHERE is_primary = 1`.

**Índices:** `franchise_id`; `(source_id, external_id, context)`.

### 4.28 `product_external_ids`

IDs externos de product; nunca são PK interna.

- **Classificação:** externo
- **Owner arquitetural:** `ExternalIdentifierRepository`
- **Migration:** `0004_sources_and_external_ids`
- **Exclusão:** CASCADE com products; merges movem IDs e rejeitam colisão
- **Atualização:** IdentityService/ExternalIdentifierRepository

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `id` | TEXT UUIDv7 | não | PK |
| `product_id` | TEXT UUIDv7 | não | FK products ON DELETE CASCADE |
| `source_id` | TEXT UUIDv7 | não | FK sources ON DELETE RESTRICT |
| `external_id` | TEXT | não | ID opaco da fonte |
| `context` | TEXT | não | default global; região/namespace quando necessário |
| `is_primary` | INTEGER boolean | não | default 0 |
| `created_at` | TEXT UTC timestamp | não |  |
| `updated_at` | TEXT UTC timestamp | não |  |

**Unicidades:** `(source_id, external_id, context)`; `(product_id, source_id, context) WHERE is_primary = 1`.

**Índices:** `product_id`; `(source_id, external_id, context)`.

### 4.29 `franchise_ownerships`

Histórico de propriedade/licenciamento de franquia com evidência. A proprietária atual é a linha `ip_owner` com `is_current=1`.

- **Classificação:** catálogo público/external
- **Owner arquitetural:** `FranchiseRepository`
- **Migration:** `0005_catalog_facts_and_availability`
- **Exclusão:** RESTRICT; corrigir por atualização transacional/supersessão documentada
- **Atualização:** FranchiseService/SourceResolutionService

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `id` | TEXT UUIDv7 | não | PK |
| `franchise_id` | TEXT UUIDv7 | não | FK franchises ON DELETE RESTRICT |
| `owner_company_id` | TEXT UUIDv7 | não | FK companies ON DELETE RESTRICT |
| `ownership_type` | TEXT | não | ip_owner\|license_holder\|other |
| `is_current` | INTEGER boolean | não | default 0 |
| `valid_from_year` | INTEGER | sim | PartialDate.year |
| `valid_from_month` | INTEGER | sim |  |
| `valid_from_day` | INTEGER | sim |  |
| `valid_from_precision` | TEXT | não | unknown\|year\|month\|day |
| `valid_from_qualifier` | TEXT | sim | circa\|before\|after |
| `valid_to_year` | INTEGER | sim | PartialDate.year |
| `valid_to_month` | INTEGER | sim |  |
| `valid_to_day` | INTEGER | sim |  |
| `valid_to_precision` | TEXT | não | unknown\|year\|month\|day |
| `valid_to_qualifier` | TEXT | sim | circa\|before\|after |
| `source_reference_id` | TEXT UUIDv7 | não | FK source_references ON DELETE RESTRICT |
| `notes` | TEXT | sim |  |
| `created_at` | TEXT UTC timestamp | não |  |
| `updated_at` | TEXT UTC timestamp | não |  |

**Unicidades:** `(franchise_id) WHERE ownership_type='ip_owner' AND is_current=1`; `(franchise_id, owner_company_id, ownership_type, source_reference_id)`.

**Checks/invariantes locais:** dois contratos PartialDate; término não anterior ao início quando comparável; is_current=1 implica valid_to_precision='unknown' e componentes/qualifier de término nulos.

**Índices:** `franchise_id`; `owner_company_id`; `ownership_type`; `is_current`.
### 4.30 `game_companies`

Créditos e papéis de empresas no Game, Edition ou Release.

- **Classificação:** catálogo público
- **Owner arquitetural:** `CreditRepository`
- **Migration:** `0005_catalog_facts_and_availability`
- **Exclusão:** RESTRICT; associações podem ser removidas explicitamente
- **Atualização:** CatalogService/SourceResolutionService

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `id` | TEXT UUIDv7 | não | PK |
| `game_id` | TEXT UUIDv7 | não | FK games |
| `edition_id` | TEXT UUIDv7 | sim | FK game_editions |
| `release_id` | TEXT UUIDv7 | sim | FK releases |
| `company_id` | TEXT UUIDv7 | não | FK companies |
| `role` | TEXT | não | developer\|publisher\|original_publisher\|port_developer\|support_studio\|distributor\|current_ip_owner\|other |
| `source_reference_id` | TEXT UUIDv7 | sim | FK source_references |
| `notes` | TEXT | sim |  |
| `created_at` | TEXT UTC timestamp | não |  |

**Unicidades:** `(game_id, COALESCE(edition_id, ''), COALESCE(release_id, ''), company_id, role)`.

**Checks/invariantes locais:** release_id IS NULL OR edition_id IS NOT NULL; triggers garantem que Edition/Release pertencem ao Game informado.

**Índices:** `game_id`; `edition_id`; `release_id`; `company_id`.
### 4.31 `game_scores`

Notas publicadas pela fonte para uma Release específica.

- **Classificação:** externo público
- **Owner arquitetural:** `ScoreRepository`
- **Migration:** `0005_catalog_facts_and_availability`
- **Exclusão:** RESTRICT quando selecionada como primária
- **Atualização:** ScoreService

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `id` | TEXT UUIDv7 | não | PK |
| `release_id` | TEXT UUIDv7 | não | FK releases |
| `source_id` | TEXT UUIDv7 | não | FK sources |
| `score_value` | NUMERIC | sim | 0..100; métrica não monetária |
| `review_count` | INTEGER | sim | >=0 |
| `source_reference_id` | TEXT UUIDv7 | não | FK source_references |
| `retrieved_at` | TEXT UTC timestamp | não |  |
| `created_at` | TEXT UTC timestamp | não |  |
| `updated_at` | TEXT UTC timestamp | não |  |

**Unicidades:** `(release_id, source_id)`.

**Checks/invariantes locais:** score_value IS NULL OR score_value BETWEEN 0 AND 100; review_count IS NULL OR review_count >= 0.

**Índices:** `release_id`; `source_id`.
### 4.32 `game_primary_scores`

Seleção editorial de uma única nota primária por Game, sem recalcular média.

- **Classificação:** catálogo público derivado/editorial
- **Owner arquitetural:** `ScoreRepository`
- **Migration:** `0005_catalog_facts_and_availability`
- **Exclusão:** CASCADE com Game; score referenciado usa RESTRICT
- **Atualização:** ScoreService

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `game_id` | TEXT UUIDv7 | não | PK/FK games ON DELETE CASCADE |
| `score_id` | TEXT UUIDv7 | não | UNIQUE FK game_scores ON DELETE RESTRICT |
| `selection_reason` | TEXT | não | regra editorial pública |
| `selected_at` | TEXT UTC timestamp | não |  |
| `source_reference_id` | TEXT UUIDv7 | sim | evidência da decisão, se aplicável |

**Checks/invariantes locais:** trigger/service garante que o score selecionado pertence a Release da Edition do mesmo Game.

**Índices:** `score_id`.

### 4.33 `game_lengths`

Duração no nível Game; não estimar compilações sem fonte.

- **Classificação:** externo público
- **Owner arquitetural:** `LengthRepository`
- **Migration:** `0005_catalog_facts_and_availability`
- **Exclusão:** RESTRICT
- **Atualização:** LengthService

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `id` | TEXT UUIDv7 | não | PK |
| `game_id` | TEXT UUIDv7 | não | FK games |
| `source_id` | TEXT UUIDv7 | não | FK sources |
| `main_story_minutes` | INTEGER | sim | >=0 |
| `main_extra_minutes` | INTEGER | sim | >=0 |
| `completionist_minutes` | INTEGER | sim | >=0 |
| `not_applicable` | INTEGER boolean | não | default 0 |
| `source_reference_id` | TEXT UUIDv7 | não | FK source_references |
| `retrieved_at` | TEXT UTC timestamp | não |  |
| `created_at` | TEXT UTC timestamp | não |  |
| `updated_at` | TEXT UTC timestamp | não |  |

**Unicidades:** `(game_id, source_id)`.

**Checks/invariantes locais:** tempos >= 0; not_applicable = 1 implica tempos NULL.

**Índices:** `game_id`; `source_id`.

### 4.34 `availability_offers`

Histórico de acesso a uma Release; retrocompatibilidade e streaming ficam aqui, não em releases. Uma oferta lógica possui no máximo uma linha corrente.

- **Classificação:** externo público
- **Owner arquitetural:** `AvailabilityRepository`
- **Migration:** `0005_catalog_facts_and_availability`
- **Exclusão:** RESTRICT; transições preservam linhas anteriores
- **Atualização:** AvailabilityService

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `id` | TEXT UUIDv7 | não | PK |
| `release_id` | TEXT UUIDv7 | não | FK releases |
| `access_platform_id` | TEXT UUIDv7 | não | FK platforms; hardware/serviço usado para acessar |
| `provider_company_id` | TEXT UUIDv7 | sim | FK companies |
| `availability_type` | TEXT | não | digital_purchase\|physical_distribution\|subscription\|streaming\|backward_compatibility |
| `region_id` | TEXT UUIDv7 | não | FK regions ON DELETE RESTRICT |
| `offer_identity_key` | TEXT | não | release/access platform/provider/type/region; estável |
| `status` | TEXT | não | available\|unavailable\|unknown |
| `is_current` | INTEGER boolean | não | default 1; uma linha corrente por offer_identity_key |
| `valid_from_year` | INTEGER | sim | PartialDate.year |
| `valid_from_month` | INTEGER | sim |  |
| `valid_from_day` | INTEGER | sim |  |
| `valid_from_precision` | TEXT | não | unknown\|year\|month\|day |
| `valid_from_qualifier` | TEXT | sim | circa\|before\|after |
| `valid_to_year` | INTEGER | sim | PartialDate.year |
| `valid_to_month` | INTEGER | sim |  |
| `valid_to_day` | INTEGER | sim |  |
| `valid_to_precision` | TEXT | não | unknown\|year\|month\|day |
| `valid_to_qualifier` | TEXT | sim | circa\|before\|after |
| `observed_at` | TEXT UTC timestamp | não | momento da observação/canonicalização |
| `last_verified_at` | TEXT UTC timestamp | não |  |
| `valid_until` | TEXT UTC timestamp | sim | TTL da verificação |
| `source_reference_id` | TEXT UUIDv7 | não | FK source_references |
| `created_at` | TEXT UTC timestamp | não |  |
| `updated_at` | TEXT UTC timestamp | não |  |

**Unicidades:** `(offer_identity_key) WHERE is_current=1`; linhas históricas podem repetir a chave.

**Checks/invariantes locais:** dois contratos PartialDate estruturais; valid_to não anterior a valid_from quando comparável.

**Índices:** `release_id`; `access_platform_id`; `(is_current, status, valid_until)`; `region_id`; `offer_identity_key`.
### 4.35 `platform_lock_reasons`

Vocabulário de motivos de aprisionamento.

- **Classificação:** catálogo público
- **Owner arquitetural:** `PlatformLockRepository`
- **Migration:** `0005_catalog_facts_and_availability`
- **Exclusão:** RESTRICT; desativar
- **Atualização:** seed/migration

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `id` | TEXT UUIDv7 | não | PK |
| `code` | TEXT | não |  |
| `name` | TEXT | não |  |
| `description` | TEXT | não |  |
| `active` | INTEGER boolean | não | default 1 |

**Unicidades:** `code`.

**Índices:** `active`.

### 4.36 `platform_lock_assessments`

Resultado derivado por Game, com versão e estado explícitos.

- **Classificação:** derivado público
- **Owner arquitetural:** `PlatformLockRepository`
- **Migration:** `0005_catalog_facts_and_availability`
- **Exclusão:** CASCADE com Game apenas após merge controlado
- **Atualização:** PlatformLockService; mutações de entrada marcam dirty na mesma transação

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `game_id` | TEXT UUIDv7 | não | PK/FK games |
| `locked` | INTEGER boolean | sim | NULL quando nunca calculado |
| `severity_level` | INTEGER | sim | 1..6 |
| `justification` | TEXT | sim |  |
| `minimum_official_hardware` | TEXT | sim | descrição pública |
| `content_lost` | INTEGER boolean | não | default 0 |
| `state` | TEXT | não | dirty\|recalculating\|current\|stale\|failed |
| `rule_version` | TEXT | sim | obrigatório quando current |
| `input_version` | TEXT | sim | obrigatório quando current |
| `calculated_at` | TEXT UTC timestamp | sim |  |
| `stale_since` | TEXT UTC timestamp | sim |  |
| `last_error_redacted` | TEXT | sim |  |

**Checks/invariantes locais:** state=current exige calculated_at, rule_version, input_version e locked não nulos; locked=0 implica severity_level NULL; locked=1 implica severity_level entre 1 e 6; locked IS NULL implica severity_level NULL.

**Índices:** `state`; `severity_level`.
### 4.37 `game_platform_lock_reasons`

Motivos associados ao assessment.

- **Classificação:** derivado público
- **Owner arquitetural:** `PlatformLockRepository`
- **Migration:** `0005_catalog_facts_and_availability`
- **Exclusão:** CASCADE com assessment
- **Atualização:** PlatformLockService

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `game_id` | TEXT UUIDv7 | não | PK/FK platform_lock_assessments ON DELETE CASCADE |
| `reason_id` | TEXT UUIDv7 | não | PK/FK platform_lock_reasons ON DELETE RESTRICT |
| `is_primary` | INTEGER boolean | não | default 0 |
| `notes` | TEXT | sim |  |

**Unicidades:** `PK(game_id, reason_id)`; `um is_primary por game`.

**Índices:** `reason_id`.

### 4.38 `personal_collection_items`

Cada cópia/licença/wishlist é uma linha; preserva múltiplas unidades.

- **Classificação:** pessoal privado
- **Owner arquitetural:** `CollectionRepository`
- **Migration:** `0006_personal_collection`
- **Exclusão:** somente ação explícita do usuário; catálogo usa RESTRICT e merge redireciona
- **Atualização:** CollectionService; importadores proibidos

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `id` | TEXT UUIDv7 | não | PK |
| `game_id` | TEXT UUIDv7 | não | FK games ON DELETE RESTRICT |
| `edition_id` | TEXT UUIDv7 | sim | FK game_editions |
| `release_id` | TEXT UUIDv7 | sim | FK releases |
| `product_id` | TEXT UUIDv7 | sim | FK products |
| `ownership_status` | TEXT | não | owned\|loaned_out\|sold\|lost\|disposed\|wishlist |
| `ownership_format` | TEXT | não | physical\|digital\|license\|unknown |
| `media_condition` | TEXT | sim | sealed\|like_new\|good\|fair\|poor\|damaged\|not_applicable |
| `box_condition` | TEXT | sim | mesmo vocabulário |
| `completeness` | TEXT | sim | complete\|missing_manual\|missing_box\|loose\|unknown\|not_applicable |
| `acquisition_date` | TEXT ISO date | sim | data exata quando conhecida; NULL quando desconhecida |
| `purchase_amount_minor` | INTEGER | sim | >=0; unidade mínima ISO 4217 |
| `purchase_currency_code` | TEXT | sim | ISO 4217; par com amount |
| `acquired_from` | TEXT | sim | privado |
| `loaned_to` | TEXT | sim | privado |
| `loaned_at` | TEXT ISO date | sim |  |
| `loan_due_date` | TEXT ISO date | sim |  |
| `sale_date` | TEXT ISO date | sim | data exata quando conhecida; sold não obriga inventar data |
| `sale_amount_minor` | INTEGER | sim | >=0 |
| `sale_currency_code` | TEXT | sim | par com amount |
| `personal_score` | NUMERIC | sim | 0..10 |
| `played` | INTEGER boolean | não | default 0 |
| `completed` | INTEGER boolean | não | default 0 |
| `private_notes` | TEXT | sim | privado |
| `created_at` | TEXT UTC timestamp | não |  |
| `updated_at` | TEXT UTC timestamp | não |  |

**Checks/invariantes locais:** triggers garantem cadeia Game/Edition/Release/Product; cada par monetário preenchido ou NULL em conjunto; ownership_status=loaned_out implica loaned_to e loaned_at; completed=1 implica played=1; personal_score IS NULL OR BETWEEN 0 AND 10.

**Índices:** `game_id`; `edition_id`; `release_id`; `product_id`; `ownership_status`.
### 4.39 `hardware_models`

Modelos catalogáveis de consoles, revisões e dispositivos necessários.

- **Classificação:** catálogo público
- **Owner arquitetural:** `HardwareModelRepository`
- **Migration:** `0007_hardware_and_playability`
- **Exclusão:** soft delete; RESTRICT
- **Atualização:** HardwareCatalogService

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `id` | TEXT UUIDv7 | não | PK |
| `platform_id` | TEXT UUIDv7 | sim | FK platforms |
| `manufacturer_id` | TEXT UUIDv7 | sim | FK manufacturers |
| `name` | TEXT | não |  |
| `normalized_name` | TEXT | não |  |
| `model_code` | TEXT | sim | código público |
| `hardware_type` | TEXT | não | console\|handheld\|pc\|streaming_device\|adapter\|other |
| `introduced_year` | INTEGER | sim | conceito anual |
| `discontinued_year` | INTEGER | sim |  |
| `notes` | TEXT | sim | público |
| `created_at` | TEXT UTC timestamp | não |  |
| `updated_at` | TEXT UTC timestamp | não |  |
| `deleted_at` | TEXT UTC timestamp | sim |  |

**Unicidades:** `(COALESCE(manufacturer_id, ''), normalized_name, COALESCE(model_code, '')) WHERE deleted_at IS NULL`.

**Checks/invariantes locais:** discontinued_year IS NULL OR introduced_year IS NULL OR discontinued_year >= introduced_year.

**Índices:** `platform_id`; `manufacturer_id`; `normalized_name`.

### 4.40 `hardware_model_external_ids`

IDs externos de hardware_model; nunca são PK interna.

- **Classificação:** externo
- **Owner arquitetural:** `ExternalIdentifierRepository`
- **Migration:** `0007_hardware_and_playability`
- **Exclusão:** CASCADE com hardware_models; merges movem IDs e rejeitam colisão
- **Atualização:** HardwareCatalogService/ExternalIdentifierRepository

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `id` | TEXT UUIDv7 | não | PK |
| `hardware_model_id` | TEXT UUIDv7 | não | FK hardware_models ON DELETE CASCADE |
| `source_id` | TEXT UUIDv7 | não | FK sources ON DELETE RESTRICT |
| `external_id` | TEXT | não | ID opaco da fonte |
| `context` | TEXT | não | default global; região/namespace quando necessário |
| `is_primary` | INTEGER boolean | não | default 0 |
| `created_at` | TEXT UTC timestamp | não |  |
| `updated_at` | TEXT UTC timestamp | não |  |

**Unicidades:** `(source_id, external_id, context)`; `(hardware_model_id, source_id, context) WHERE is_primary = 1`.

**Índices:** `hardware_model_id`; `(source_id, external_id, context)`.

### 4.41 `personal_hardware_units`

Unidades físicas pessoais de hardware.

- **Classificação:** pessoal privado
- **Owner arquitetural:** `HardwareCollectionRepository`
- **Migration:** `0007_hardware_and_playability`
- **Exclusão:** ação explícita do usuário
- **Atualização:** HardwareCollectionService

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `id` | TEXT UUIDv7 | não | PK |
| `hardware_model_id` | TEXT UUIDv7 | não | FK hardware_models ON DELETE RESTRICT |
| `ownership_status` | TEXT | não | owned\|loaned_in\|sold\|lost\|disposed |
| `working_status` | TEXT | não | working\|partially_working\|under_repair\|defective\|for_parts |
| `serial_number` | TEXT | sim | secreto |
| `nickname` | TEXT | sim | privado |
| `storage_capacity_gb` | INTEGER | sim | >=0 |
| `acquisition_date` | TEXT ISO date | sim | data exata |
| `purchase_amount_minor` | INTEGER | sim | >=0 |
| `purchase_currency_code` | TEXT | sim | par monetário |
| `sale_amount_minor` | INTEGER | sim | >=0 |
| `sale_currency_code` | TEXT | sim | par monetário |
| `sale_date` | TEXT ISO date | sim |  |
| `acquired_from` | TEXT | sim | privado |
| `location` | TEXT | sim | privado |
| `private_notes` | TEXT | sim |  |
| `created_at` | TEXT UTC timestamp | não |  |
| `updated_at` | TEXT UTC timestamp | não |  |

**Unicidades:** `(hardware_model_id, serial_number) WHERE serial_number IS NOT NULL`.

**Checks/invariantes locais:** pares monetários; storage_capacity_gb >= 0; sale_date é exata quando conhecida e pode ser NULL.

**Índices:** `hardware_model_id`; `ownership_status`; `working_status`.

### 4.42 `accessory_models`

Modelos de acessórios/periféricos.

- **Classificação:** catálogo público
- **Owner arquitetural:** `AccessoryModelRepository`
- **Migration:** `0007_hardware_and_playability`
- **Exclusão:** soft delete; RESTRICT
- **Atualização:** HardwareCatalogService

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `id` | TEXT UUIDv7 | não | PK |
| `manufacturer_id` | TEXT UUIDv7 | sim | FK manufacturers |
| `name` | TEXT | não |  |
| `normalized_name` | TEXT | não |  |
| `accessory_type` | TEXT | não | controller\|motion_sensor\|camera\|adapter\|storage\|network\|arcade_controller\|other |
| `model_code` | TEXT | sim |  |
| `notes` | TEXT | sim |  |
| `created_at` | TEXT UTC timestamp | não |  |
| `updated_at` | TEXT UTC timestamp | não |  |
| `deleted_at` | TEXT UTC timestamp | sim |  |

**Unicidades:** `(COALESCE(manufacturer_id, ''), normalized_name, COALESCE(model_code, '')) WHERE deleted_at IS NULL`.

**Índices:** `manufacturer_id`; `accessory_type`; `normalized_name`.

### 4.43 `accessory_platforms`

Compatibilidade declarada entre acessório e plataforma.

- **Classificação:** catálogo público
- **Owner arquitetural:** `AccessoryModelRepository`
- **Migration:** `0007_hardware_and_playability`
- **Exclusão:** CASCADE com acessório
- **Atualização:** HardwareCatalogService

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `accessory_model_id` | TEXT UUIDv7 | não | PK/FK accessory_models ON DELETE CASCADE |
| `platform_id` | TEXT UUIDv7 | não | PK/FK platforms ON DELETE RESTRICT |
| `support_level` | TEXT | não | full\|partial\|adapter_required |
| `required_adapter_model_id` | TEXT UUIDv7 | sim | FK accessory_models |
| `notes` | TEXT | sim |  |

**Checks/invariantes locais:** support_level=adapter_required implica required_adapter_model_id; required_adapter_model_id <> accessory_model_id.

**Índices:** `platform_id`.

### 4.44 `personal_accessory_units`

Unidades pessoais de acessórios.

- **Classificação:** pessoal privado
- **Owner arquitetural:** `AccessoryCollectionRepository`
- **Migration:** `0007_hardware_and_playability`
- **Exclusão:** ação explícita do usuário
- **Atualização:** AccessoryCollectionService

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `id` | TEXT UUIDv7 | não | PK |
| `accessory_model_id` | TEXT UUIDv7 | não | FK accessory_models ON DELETE RESTRICT |
| `ownership_status` | TEXT | não | owned\|loaned_in\|sold\|lost\|disposed |
| `working_status` | TEXT | não | working\|partially_working\|under_repair\|defective\|for_parts |
| `serial_number` | TEXT | sim | secreto |
| `acquisition_date` | TEXT ISO date | sim |  |
| `purchase_amount_minor` | INTEGER | sim | >=0 |
| `purchase_currency_code` | TEXT | sim | par monetário |
| `sale_amount_minor` | INTEGER | sim | >=0 |
| `sale_currency_code` | TEXT | sim | par monetário |
| `sale_date` | TEXT ISO date | sim |  |
| `location` | TEXT | sim | privado |
| `private_notes` | TEXT | sim |  |
| `created_at` | TEXT UTC timestamp | não |  |
| `updated_at` | TEXT UTC timestamp | não |  |

**Unicidades:** `(accessory_model_id, serial_number) WHERE serial_number IS NOT NULL`.

**Checks/invariantes locais:** pares monetários; sale_date é exata quando conhecida e pode ser NULL.

**Índices:** `accessory_model_id`; `ownership_status`; `working_status`.

### 4.45 `personal_capabilities`

Capacidades pessoais não representadas por uma unidade física, como rede ou assinatura ativa.

- **Classificação:** pessoal privado
- **Owner arquitetural:** `CapabilityRepository`
- **Migration:** `0007_hardware_and_playability`
- **Exclusão:** ação explícita do usuário
- **Atualização:** PlayabilityService/CollectionService

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `id` | TEXT UUIDv7 | não | PK |
| `capability_code` | TEXT | não | network_access\|active_subscription\|online_account\|other |
| `provider_company_id` | TEXT UUIDv7 | sim | FK companies ON DELETE RESTRICT |
| `platform_id` | TEXT UUIDv7 | sim | FK platforms ON DELETE RESTRICT |
| `status` | TEXT | não | available\|unavailable\|unknown |
| `valid_until` | TEXT UTC timestamp | sim | expiração, quando aplicável |
| `private_notes` | TEXT | sim | privado |
| `created_at` | TEXT UTC timestamp | não |  |
| `updated_at` | TEXT UTC timestamp | não |  |

**Unicidades:** `(capability_code, COALESCE(provider_company_id, ''), COALESCE(platform_id, ''))`.

**Índices:** `capability_code`; `provider_company_id`; `platform_id`; `(status, valid_until)`.

### 4.46 `hardware_compatibility_rules`

Direção: um modelo possuído (source) satisfaz Releases da plataforma alvo.

- **Classificação:** catálogo público
- **Owner arquitetural:** `CompatibilityRepository`
- **Migration:** `0007_hardware_and_playability`
- **Exclusão:** RESTRICT
- **Atualização:** HardwareCompatibilityService

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `id` | TEXT UUIDv7 | não | PK |
| `source_hardware_model_id` | TEXT UUIDv7 | não | FK hardware_models |
| `target_platform_id` | TEXT UUIDv7 | não | FK platforms |
| `compatibility_type` | TEXT | não | native\|backward_compatible\|official_emulation |
| `scope` | TEXT | não | full\|partial\|selected_titles |
| `source_reference_id` | TEXT UUIDv7 | sim | FK source_references |
| `notes` | TEXT | sim |  |
| `created_at` | TEXT UTC timestamp | não |  |
| `updated_at` | TEXT UTC timestamp | não |  |

**Unicidades:** `(source_hardware_model_id, target_platform_id, compatibility_type, scope)`.

**Checks/invariantes locais:** scope=selected_titles exige ao menos uma linha em compatibility_rule_releases, verificada pelo service/auditoria.

**Índices:** `source_hardware_model_id`; `target_platform_id`.
### 4.47 `compatibility_rule_releases`

Allowlist de Releases quando a regra vale apenas para títulos/versões selecionados.

- **Classificação:** catálogo público
- **Owner arquitetural:** `CompatibilityRepository`
- **Migration:** `0007_hardware_and_playability`
- **Exclusão:** CASCADE com regra
- **Atualização:** HardwareCompatibilityService

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `compatibility_rule_id` | TEXT UUIDv7 | não | PK/FK hardware_compatibility_rules ON DELETE CASCADE |
| `release_id` | TEXT UUIDv7 | não | PK/FK releases ON DELETE RESTRICT |
| `support_level` | TEXT | não | full\|partial |
| `notes` | TEXT | sim |  |

**Índices:** `release_id`.
### 4.48 `game_requirement_groups`

Grupos simples all_of/any_of de requisitos por Release.

- **Classificação:** catálogo público
- **Owner arquitetural:** `RequirementRepository`
- **Migration:** `0007_hardware_and_playability`
- **Exclusão:** CASCADE somente ao excluir release após proteção; na prática RESTRICT via serviço
- **Atualização:** RequirementService

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `id` | TEXT UUIDv7 | não | PK |
| `release_id` | TEXT UUIDv7 | não | FK releases |
| `group_operator` | TEXT | não | all_of\|any_of |
| `mandatory` | INTEGER boolean | não | requisito obrigatório ou opcional |
| `description` | TEXT | sim |  |
| `created_at` | TEXT UTC timestamp | não |  |
| `updated_at` | TEXT UTC timestamp | não |  |

**Índices:** `release_id`; `mandatory`.

### 4.49 `game_hardware_requirements`

Itens de requisito; exatamente um alvo principal por linha.

- **Classificação:** catálogo público
- **Owner arquitetural:** `RequirementRepository`
- **Migration:** `0007_hardware_and_playability`
- **Exclusão:** CASCADE com grupo
- **Atualização:** RequirementService

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `id` | TEXT UUIDv7 | não | PK |
| `group_id` | TEXT UUIDv7 | não | FK game_requirement_groups ON DELETE CASCADE |
| `hardware_model_id` | TEXT UUIDv7 | sim | FK hardware_models |
| `accessory_model_id` | TEXT UUIDv7 | sim | FK accessory_models |
| `capability_code` | TEXT | sim | storage_gb\|network_access\|active_subscription\|online_account\|other |
| `capability_provider_company_id` | TEXT UUIDv7 | sim | FK companies; permitido apenas com capability_code |
| `capability_platform_id` | TEXT UUIDv7 | sim | FK platforms; permitido apenas com capability_code |
| `minimum_quantity` | INTEGER | não | default 1 |
| `minimum_value` | INTEGER | sim | ex.: GB; aplicável a storage_gb |
| `notes` | TEXT | sim |  |

**Checks/invariantes locais:** exatamente um de hardware_model_id/accessory_model_id/capability_code não nulo; contextos de capability só existem com capability_code; minimum_quantity > 0; minimum_value IS NULL OR minimum_value >= 0.

**Índices:** `group_id`; `hardware_model_id`; `accessory_model_id`; `capability_code`; `capability_provider_company_id`; `capability_platform_id`.
### 4.50 `personal_playability`

Cache derivado por Release com estado visível.

- **Classificação:** derivado pessoal
- **Owner arquitetural:** `PlayabilityRepository`
- **Migration:** `0007_hardware_and_playability`
- **Exclusão:** CASCADE com release após proteção
- **Atualização:** PlayabilityService; alteração em unidades/capacidades/requisitos marca dirty na mesma transação

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `release_id` | TEXT UUIDv7 | não | PK/FK releases |
| `playable_now` | INTEGER boolean | sim | NULL quando nunca calculado |
| `compatibility_level` | TEXT | sim | full\|partial\|none\|unknown |
| `missing_requirements_json` | TEXT JSON | sim | sem serial/localização |
| `state` | TEXT | não | dirty\|recalculating\|current\|stale\|failed |
| `rule_version` | TEXT | sim | obrigatório quando current |
| `input_version` | TEXT | sim | obrigatório quando current |
| `calculated_at` | TEXT UTC timestamp | sim |  |
| `stale_since` | TEXT UTC timestamp | sim |  |
| `last_error_redacted` | TEXT | sim |  |

**Checks/invariantes locais:** state=current exige calculated_at, rule_version, input_version e playable_now/compatibility_level não nulos.

**Índices:** `state`; `playable_now`.
### 4.51 `run_tasks`

Fila SQLite simples com deduplicação, retry e fencing token.

- **Classificação:** operacional
- **Owner arquitetural:** `RunTaskRepository`
- **Migration:** `0008_incremental_operations`
- **Exclusão:** RESTRICT; retenção junto ao run
- **Atualização:** QueueService com UPDATE condicional por lock_token

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `id` | TEXT UUIDv7 | não | PK |
| `execution_run_id` | TEXT UUIDv7 | não | FK execution_runs ON DELETE RESTRICT |
| `task_type` | TEXT | não | collect\|normalize\|apply\|recalculate_lock\|recalculate_playability\|verify\|other |
| `entity_type` | TEXT | sim |  |
| `entity_id` | TEXT UUIDv7 | sim |  |
| `source_id` | TEXT UUIDv7 | sim | FK sources |
| `priority` | TEXT | não | critical\|high\|normal\|low |
| `status` | TEXT | não | pending\|running\|succeeded\|failed\|dead_letter\|cancelled |
| `idempotency_policy` | TEXT | não | idempotent\|review_required |
| `scheduled_for` | TEXT UTC timestamp | não |  |
| `attempt_count` | INTEGER | não | default 0 |
| `max_attempts` | INTEGER | não | default 3 |
| `deduplication_key` | TEXT | não | canônica |
| `lock_owner` | TEXT | sim |  |
| `lock_token` | TEXT UUIDv7 | sim | fencing token novo a cada claim |
| `locked_at` | TEXT UTC timestamp | sim |  |
| `lock_expires_at` | TEXT UTC timestamp | sim |  |
| `last_error_redacted` | TEXT | sim |  |
| `created_at` | TEXT UTC timestamp | não |  |
| `updated_at` | TEXT UTC timestamp | não |  |
| `finished_at` | TEXT UTC timestamp | sim |  |

**Unicidades:** `deduplication_key WHERE status IN ('pending','running')`.

**Checks/invariantes locais:** attempt_count >= 0; max_attempts > 0; running exige lock_token, locked_at e lock_expires_at; estados não running não mantêm lock_token; terminal exige finished_at.

**Índices:** `(status, scheduled_for)`; `(status, lock_expires_at)`; `execution_run_id`; `(entity_type, entity_id)`.
### 4.52 `review_queue`

Conflitos e decisões humanas, com deduplicação de pendências.

- **Classificação:** operacional privado
- **Owner arquitetural:** `ReviewRepository`
- **Migration:** `0008_incremental_operations`
- **Exclusão:** RESTRICT; resolvido é preservado
- **Atualização:** ReviewService

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `id` | TEXT UUIDv7 | não | PK |
| `entity_type` | TEXT | não | allowlist de catálogo/externo; entidades pessoais proibidas |
| `entity_id` | TEXT UUIDv7 | não |  |
| `field_name` | TEXT | sim |  |
| `current_value_json` | TEXT JSON | sim |  |
| `candidate_value_json` | TEXT JSON | sim |  |
| `reason` | TEXT | não |  |
| `source_reference_id` | TEXT UUIDv7 | sim | FK source_references |
| `priority` | TEXT | não | critical\|high\|normal\|low |
| `status` | TEXT | não | pending\|approved\|rejected\|deferred\|cancelled |
| `deduplication_key` | TEXT | não | estável para o conflito lógico |
| `created_at` | TEXT UTC timestamp | não |  |
| `reviewed_at` | TEXT UTC timestamp | sim |  |
| `reviewed_by` | TEXT | sim |  |
| `review_notes` | TEXT | sim | privado |

**Unicidades:** `deduplication_key WHERE status IN ('pending','deferred')`.

**Checks/invariantes locais:** estados approved/rejected/deferred/cancelled exigem reviewed_at.

**Índices:** `(status, priority, created_at)`; `(entity_type, entity_id)`; `source_reference_id`.
### 4.53 `change_log`

Auditoria das alterações aplicadas, sem prometer event sourcing/rollback universal.

- **Classificação:** operacional privado
- **Owner arquitetural:** `ChangeLogRepository`
- **Migration:** `0008_incremental_operations`
- **Exclusão:** RESTRICT; retenção operacional
- **Atualização:** UnitOfWork/ChangeLogService

| Coluna | Tipo | Nulo | Regra |
|---|---|---:|---|
| `id` | TEXT UUIDv7 | não | PK |
| `execution_run_id` | TEXT UUIDv7 | não | FK execution_runs |
| `entity_type` | TEXT | não |  |
| `entity_id` | TEXT UUIDv7 | não |  |
| `field_name` | TEXT | sim | NULL para mudança estrutural/merge |
| `old_value_json` | TEXT JSON | sim | redigido quando pessoal |
| `new_value_json` | TEXT JSON | sim | redigido quando pessoal |
| `change_type` | TEXT | não | insert\|update\|soft_delete\|merge\|recalculate |
| `source_reference_id` | TEXT UUIDv7 | sim | FK source_references |
| `changed_at` | TEXT UTC timestamp | não |  |
| `notes` | TEXT | sim |  |

**Índices:** `execution_run_id`; `(entity_type, entity_id)`; `changed_at`.

## 5. Invariantes cruzados não expressáveis apenas por FK

- triggers garantem que `personal_collection_items` aponta para Edition/Release/Product pertencentes ao mesmo Game; Product exige Release e Release exige Edition.
- quando Product é conhecido, `ownership_format` deve ser compatível com `product_type/media_format`, validado pelo domínio.
- triggers garantem que `game_companies.release_id`, quando preenchido, pertence à Edition e ao Game indicados.
- partial unique index permite no máximo uma Edition ativa `original` por Game; o serviço cria ao menos uma antes de concluir o cadastro.
- `game_primary_scores` seleciona score cuja Release pertence ao mesmo Game.
- existe no máximo uma linha `ip_owner` corrente em `franchise_ownerships`; a proprietária atual é derivada dessa linha.
- Product sempre pertence a uma Release e é opcional; bundle multi-Release/DLC Product não integra o MVP.
- `catalog_assertions` e `record_source_links` usam allowlists e auditoria de integridade.
- merge preserva dados pessoais e external IDs, ou aborta por colisão não resolvida.
- alteração em entradas de lock/playability marca o derivado correspondente `dirty` no mesmo commit.
- motivos de lock e summaries de derivados só são exportados quando o pai está `current`.
- `hardware_compatibility_rules.scope=selected_titles` exige Releases explícitas e cada Release deve pertencer à plataforma alvo da regra.
- hardware/accessory `partially_working` não satisfaz requisito obrigatório no MVP.

## 6. Diagrama, migrations e ownership

Todas as tabelas acima aparecem no diagrama, possuem migration no documento 26 e owner na matriz 22. Nenhuma tabela conceitual adicional integra o MVP.
