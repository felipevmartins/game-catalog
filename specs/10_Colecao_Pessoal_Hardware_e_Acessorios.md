# 10 — Coleção Pessoal, Hardware e Acessórios

## Coleção de jogos

`personal_collection_items` representa uma cópia, licença ou intenção de compra. `game_id` é obrigatório e Edition/Release/Product são opcionais conforme a precisão conhecida. Várias linhas para o mesmo Game são válidas.

Triggers e CollectionService validam a cadeia: Product pertence à Release, Release à Edition e Edition ao Game. Importadores externos não recebem repository pessoal. Correções/merges do catálogo redirecionam as FKs pessoais dentro da mesma transação e falham antes do commit se a cadeia ficar inconsistente.

Compra e venda têm pares monetários independentes; o valor original nunca é convertido/destruído. Datas pessoais exatas permanecem `DATE` quando conhecidas e NULL quando desconhecidas; o sistema não inventa dia para permitir status `sold`.

## Hardware

- `hardware_models` e `accessory_models`: catálogo público;
- `personal_hardware_units` e `personal_accessory_units`: unidades pessoais, serial/localização/notas privadas;
- estado vendido, perdido, disposed, defeituoso ou em reparo não satisfaz requisito obrigatório;
- no MVP, `partially_working` não satisfaz requisito obrigatório. Capacidade por componente/defeito detalhado fica pós-MVP.

## Capacidades pessoais

`personal_capabilities` registra rede, assinatura ou conta ativa, com contexto de plataforma/provedor e validade. Mudança/expiração marca jogabilidade dirty/stale. Capacidade `storage_gb` é avaliada na unidade de hardware, não duplicada nessa tabela.

## Compatibilidade

A direção é explícita: `source_hardware_model_id` é o modelo que o usuário possui; `target_platform_id` é a plataforma cujas Releases podem ser executadas. Escopos: `full`, `partial`, `selected_titles`. Para `selected_titles`, `compatibility_rule_releases` é obrigatório. Streaming é disponibilidade, não compatibilidade de hardware.

## Requisitos

Cada Release possui zero ou mais grupos `all_of`/`any_of`, obrigatórios ou opcionais. Um grupo mandatory `all_of` exige todos os itens; mandatory `any_of` exige ao menos um. Grupos opcionais não bloqueiam, mas podem reduzir compatibilidade de `full` para `partial`.

Requisitos de capacidade podem indicar provedor/plataforma. `storage_gb` usa `minimum_value`; assinatura/rede/conta são resolvidas contra `personal_capabilities`.

## Jogabilidade

`personal_playability` é cache por Release. Considera unidades ativas e funcionais, regras de compatibilidade, acessórios e capacidades. Mudanças pessoais ou de catálogo marcam `dirty`; TTL/contrato vencido marca `stale`. `playable_now` não é apresentado como atual quando o estado não é `current`.

## CLI essencial

`collection add/list/update/sell/loan/return`, `hardware add/update/sell`, `accessory add/update/sell`, `capability add/update/remove`, `playability show/recalculate`.

## Privacidade

Perfis público/compartilhável nunca incluem serial, preço, origem, localização, empréstimo, capacidades pessoais ou notas privadas. O perfil pessoal exige seleção explícita.
