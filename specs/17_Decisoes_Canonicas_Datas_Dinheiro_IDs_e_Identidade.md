# 17 — Decisões Canônicas de Datas, Dinheiro, IDs e Identidade

## PartialDate

Estrutura: `year`, `month`, `day`, `precision`, `qualifier`.

- precision `unknown`: componentes e qualifier nulos;
- `year`: somente ano;
- `month`: ano e mês;
- `day`: ano, mês e dia;
- qualifier NULL significa exato; `circa`, `before`, `after` qualificam o valor conhecido.

Validação de calendário gregoriano completa ocorre no value object; SQLite garante estrutura e ranges. Serialização JSON usa objeto com os cinco campos. Exibição respeita precisão. Ordenação usa intervalo possível: primeiro limite inferior, depois superior, depois precisão; unknown vem por último. Comparação de igualdade exige mesmos componentes/precision/qualifier; sobreposição de intervalos é operação distinta.

Não existe coluna Date completa paralela para o mesmo evento. Datas pessoais deliberadamente exatas podem usar `DATE`; desconhecidas ficam NULL.

## Money

`Money(amount_minor: int, currency_code: str)`; amount pode ser zero e não pode ser float. O expoente vem do registro ISO 4217 da aplicação: JPY 0, moedas comuns 2, algumas 3. Conversão é uma visão/relatório separado e nunca substitui valor original. Persistência exige amount e currency ambos nulos ou preenchidos.

## IDs

- UUIDv7 interno para entidades de domínio, pessoais e operacionais; singleton técnico e PK associativa são exceções explícitas;
- formato canônico valida versão e variante RFC 4122;
- renomear ou corrigir data não altera ID;
- slug/alias não é PK/FK;
- external ID é opaco, contextual e único na fonte;
- seeds usam constantes UUIDv7 geradas uma vez;
- migration não gera ID por hash de nome;
- Editions, Releases, Products e conteúdos dependentes usam `identity_discriminator` persistido e imutável; identity keys não incluem nome, tipo classificatório, data, mídia, SKU ou loja.

Merges movem external IDs para o sobrevivente; colisão entre dois IDs primários do mesmo source/context exige revisão. Reimportação procura primeiro external ID exato, depois chave estrutural/discriminator; fuzzy match só cria candidato de revisão.

## Identidade

| Caso | Game | Edition | Release | Product |
|---|---|---|---|---|
| Original | cria | original | cria | opcional |
| Port simples | mantém | mantém | cria `port` | opcional |
| Port com edição técnica distinta | mantém | cria técnica | cria | opcional |
| Remaster | mantém | cria `remaster` | cria | opcional |
| Enhanced/Director's Cut/Definitive | mantém | cria | cria | opcional |
| Remake/Reboot | cria | original | cria | opcional |
| Relançamento sem nova edição | mantém | mantém | cria `rerelease` | opcional |
| Região diferente | mantém | mantém | cria | opcional |
| Produto físico/digital/SKU | mantém | mantém | mantém | cria quando necessário |
| Bundle da mesma Release | mantém | mantém | mantém | pode criar Product |
| Bundle multi-Release | mantém | mantém | mantém | pós-MVP |
| Compilação | cria | original | cria | opcional |
| DLC dependente/episódio | mantém | mantém | não cria Game | `game_contents`; Product detalhado pós-MVP |
| Expansão standalone | cria | original | cria | opcional |
| Retrocompatibilidade/streaming | mantém | mantém | não cria | `availability_offers` |

## Invariantes

Toda Edition pertence a um Game; toda Release a uma Edition; todo Product a uma Release. Nenhuma relação usa nome. A mesma versão importada por fontes diferentes converge ao mesmo registro. Correção de nome, tipo classificatório, data, mídia, loja ou SKU não cria nova identidade. O resultado esperado de contagens está em `identity_test_cases.md`.
