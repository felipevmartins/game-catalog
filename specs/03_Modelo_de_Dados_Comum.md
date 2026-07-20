# 03 — Modelo de Dados Comum

## Vocabulário canônico

| Conceito | Campo/enum canônico |
|---|---|
| Tipo de Game | `main`, `spin_off`, `remake`, `reboot`, `compilation`, `standalone_expansion`, `other` |
| Tipo de Edition | `original`, `remaster`, `enhanced`, `directors_cut`, `definitive`, `complete`, `goty`, `technical_variant`, `regional_variant`, `other` |
| Tipo de Release | `original`, `port`, `rerelease` |
| Estado derivado | `dirty`, `recalculating`, `current`, `stale`, `failed` |
| Estado de execução | `queued`, `running`, `succeeded`, `succeeded_with_warnings`, `failed`, `cancelled` |
| Estado de tarefa | `pending`, `running`, `succeeded`, `failed`, `dead_letter`, `cancelled` |
| Confiança | `high`, `medium`, `low` |

## IDs

- `id` é UUIDv7 textual canônico nas entidades de domínio, pessoais e operacionais.
- `schema_metadata.id` e chaves compostas de tabelas associativas são exceções técnicas explicitamente documentadas.
- Slug é conveniência calculada/persistida apenas para busca; não é PK/FK.
- IDs externos ficam em tabelas próprias da entidade.
- Seeds usam UUIDv7 fixos gerados uma vez e gravados na migration; não são derivados do nome.
- `identity_discriminator` é opaco, persistido e imutável; correção de data, título, mídia ou loja não altera identidade nem cria nova linha.

## Datas

`PartialDate` usa `year`, `month`, `day`, `precision` e `qualifier`, sem coluna de data completa concorrente. `precision=unknown` exige componentes e qualifier nulos. Datas pessoais conhecidas com exatidão usam `DATE`; quando desconhecidas permanecem NULL, sem data inventada.

## Dinheiro

Cada valor usa `amount_minor` inteiro e `currency_code`; o expoente de casas é obtido do registro ISO 4217 da aplicação. JPY usa expoente 0, moedas de três casas usam 3. Compra e venda preservam moeda/valor originais e nunca são substituídas por conversão estimada.

## Regiões

Releases, Products, aliases e disponibilidade referenciam `regions.id`. O código exportado vem de `regions.code`, evitando mistura não validada entre ISO 3166 e mercados editoriais.

## Separação

- catálogo público: obras, edições, releases, produtos, empresas e hardware-modelo;
- externo: fontes, evidências, vínculos de proveniência e IDs externos;
- pessoal: cópias, unidades, preços, origem, serial, localização, capacidades e notas;
- operacional: runs, tasks, backups, revisão e change log;
- derivado: aprisionamento e jogabilidade com estado/versionamento.
