# 09 — Arquitetura Python

## Camadas

```text
domain/          entidades, enums, PartialDate, Money, invariantes
application/     services e DTOs; casos de uso e UnitOfWork
persistence/     modelos SQLAlchemy, repositories, migrations
integrations/    collectors/adapters externos; nunca tabelas pessoais
exports/         perfis allowlist e writers
cli/             parsing/apresentação; sem regra de domínio
maintenance/     backup, restore, queue, integrity, merge
```

## Serviços aprovados

- `IdentityService`: resolve Game/Edition/Release/Product, discriminadores, reimportação e merge.
- `CatalogService`: catálogo geral, aliases, relações, conteúdo e créditos.
- `FranchiseService`: associações e histórico de propriedade.
- `SourceResolutionService`: fontes, referências, vínculos de registro, assertions, prioridade, override e conflitos.
- `ImportService`/`UpdateService`: orquestram execução e UnitOfWork; não acessam tabelas pessoais.
- `CollectionService`: itens pessoais e validação da cadeia de identidade.
- `HardwareCatalogService`, `HardwareCollectionService`, `AccessoryCollectionService`.
- `HardwareCompatibilityService`, `RequirementService`, `PlayabilityService`.
- `AvailabilityService`, `PlatformLockService`, `ScoreService`, `LengthService`.
- `BackupService`, `ExecutionService`, `QueueService`, `ReviewService`, `ExportService`, `MigrationService`.

Não há service/repository vazio apenas por simetria. Tabelas associativas simples podem ser operadas pelo repository do agregado indicado no documento 08.

## Repositories

Repositories executam CRUD, consultas, triggers auxiliares e locking atômico; regras de identidade, prioridade de fonte, privacidade e merge ficam nos services. A UnitOfWork delimita transação e grava `change_log`. Toda mutação manual cria uma `execution_run` do tipo `manual_edit`.

## DTOs

- DTO bruto por integração;
- DTO normalizado com UUIDs resolvidos, regions, PartialDate/Money e discriminadores validados;
- comandos de aplicação independentes da CLI;
- resultado com inserted/updated/skipped/conflicts e IDs internos.

## Pipeline mutável

`validate config → create ExecutionRun → acquire app lock when needed → verified backup when risky → collect/read → normalize → resolve identity → validate → compare → source policy → persist + mark dirty atomically → enqueue tasks → commit → finalize run`.

Criar a linha operacional da run não conta como primeiro write funcional protegido; nenhum dado de catálogo/pessoal nem tarefa de aplicação é persistido antes do backup exigido.

Dry-run não persiste run_tasks, catálogo, pessoal ou change log de dados; pode registrar um ExecutionRun técnico somente se configurado, sem alterar estado funcional.

## Geração de UUIDv7

- runtime: biblioteca UUIDv7 testada e relógio UTC; colisão é rejeitada pela PK;
- seeds/migrations: constantes geradas uma vez no momento de autoria, incluídas no arquivo da migration;
- nenhuma função recebe título/slug/external ID/data para calcular UUID.

## Recuperação de runs

Run abandonada com somente tarefas idempotentes não é marcada failed imediatamente: volta atomicamente a `queued`, preserva `started_at` e é retomada. Se houver tarefa `review_required`, a run termina failed e o conflito é encaminhado à revisão; tarefas não terminais são canceladas ou migradas para uma nova run explícita, nunca executadas sob run terminal.

## Testes

Unitários para value objects e services; integração com SQLite real temporário; migration up/down; triggers de cadeia; concorrência; backup/restore; privacidade; propriedades de identidade e prova vertical. Mocks de repository não substituem os testes de constraints.
