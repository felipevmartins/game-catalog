# 29 — Relatório de Revisão Cruzada

## Método

Foram comparados o manifesto, as definições do documento 08, a sequência de migrations e a matriz de cobertura. Também foram executadas buscas pelos termos obrigatórios e por nomes obsoletos. Menções históricas permitidas ficam apenas em changelog, README, matriz de resolução, inventário e lista de obsolescência do manifest.

## Manifesto canônico

O pacote possui 53 tabelas físicas do MVP. O conjunto canônico está em `schema_manifest.json`; todos os nomes aparecem no documento 08, na migration correspondente e na matriz 22.

## Correções verificadas

- Edition/Release/Product/Content usam discriminator estável; nome, tipo, data, mídia, SKU e loja não participam da identidade.
- Regiões usam `regions` e FKs `region_id`; `region_code` livre foi removido do schema físico.
- Proveniência possui `record_source_links`, FKs diretas e assertions seletivas.
- Propriedade histórica usa `franchise_ownerships`, sem campo corrente duplicado em `franchises`.
- Scores primários usam `game_primary_scores`; o booleano antigo foi removido.
- Disponibilidade mantém histórico e uma linha corrente por offer key.
- Selected titles referencia Releases.
- Capacidades pessoais têm persistência explícita.
- Runs abandonadas não deixam tarefas executáveis sob run terminal.
- Derivados não current não exportam valor/motivos como atuais.

## Termos substituídos

| Termo antigo | Decisão v1.3 |
|---|---|
| `game_platforms` | removido; `releases.platform_id` |
| `personal_collection` 1:1 | removido; `personal_collection_items` 1:N |
| `import_runs` / `update_runs` | removidos; `execution_runs` |
| `compatibility_rule_games` | removido; `compatibility_rule_releases` |
| `region_code` livre | removido do schema físico; `region_id → regions.code` |
| `is_primary_for_game` | removido; `game_primary_scores` |
| `current_ip_owner_id` | removido; linha corrente em `franchise_ownerships` |
| IDs determinísticos por nome/data | proibidos; UUIDv7 + discriminator persistido |

## Contagem da busca textual

| Termo | Ocorrências |
|---|---:|
| `Game` | 329 |
| `Edition` | 108 |
| `Release` | 218 |
| `Product` | 86 |
| `port` | 109 |
| `remaster` | 19 |
| `remake` | 17 |
| `release_type` | 4 |
| `game_type` | 3 |
| `personal_collection` | 24 |
| `personal_collection_items` | 17 |
| `money` | 9 |
| `Numeric` | 2 |
| `Decimal` | 2 |
| `amount_minor` | 10 |
| `currency` | 12 |
| `Date` | 116 |
| `PartialDate` | 30 |
| `UUID` | 192 |
| `deterministic` | 1 |
| `slug` | 9 |
| `alias` | 31 |
| `external_id` | 93 |
| `import_runs` | 4 |
| `execution_runs` | 21 |
| `backup` | 87 |
| `restore` | 25 |
| `rollback` | 11 |
| `lock` | 98 |
| `dirty` | 30 |
| `stale` | 22 |
| `derived` | 2 |
| `public` | 44 |
| `private` | 7 |
| `serial` | 17 |
| `source_type` | 4 |
| `availability` | 48 |
| `migration` | 111 |
| `region_code` | 0 |
| `compatibility_rule_games` | 3 |
| `is_primary_for_game` | 0 |
| `current_ip_owner_id` | 0 |

## Limitação

Esta revisão é documental. A prova definitiva depende da implementação das migrations, triggers, partial indexes e testes do documento 27 em SQLite real.
