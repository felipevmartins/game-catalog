# 01 — Escopo e Definições

## Núcleo de identidade

- **Game:** obra. Não carrega plataforma, região, mídia, loja ou SKU.
- **Edition:** edição editorial ou técnica da obra, como original, remaster, Enhanced ou Director's Cut.
- **Release:** disponibilização de uma Edition em uma plataforma, região e período.
- **Product:** item comercial opcional de uma única Release, usado quando mídia, formato, loja, SKU, código ou variante comercial precisam ser distinguidos.

Product pode ser omitido em pesquisa histórica, disponibilidade genérica e coleção quando a cópia exata não é conhecida. No MVP, Product não representa bundle com múltiplos Games/Releases nem produto comercial de DLC independente; esses casos ficam como metadado externo ou pós-MVP.

## Classificações

- **Port:** mesma obra e, por padrão, mesma Edition; cria Release em outra plataforma. Se houver edição técnica comercialmente distinta, primeiro cria Edition e então Release.
- **Remaster:** mesma obra, nova Edition e ao menos uma nova Release.
- **Remake:** nova obra (`Game`), ligada ao original por `remake_of`.
- **Reboot:** novo `Game`; usa `reboot_of` quando houver alvo claro.
- **Relançamento:** nova Release da mesma Edition quando não há edição distinta.
- **Edição definitiva/complete/GOTY:** nova Edition quando agrega conteúdo/identidade editorial; Product apenas para variante comercial da Release.
- **DLC/expansão dependente:** `game_contents`, não Game. Produto comercial detalhado do DLC é pós-MVP.
- **Expansão standalone:** novo Game relacionado por `standalone_expansion_of`.
- **Compilação:** novo Game com relações `compilation_contains` para os Games incluídos.
- **Bundle comercial de uma Release:** pode criar Product. Bundle multi-Release é pós-MVP.
- **Episódios:** a temporada/obra principal é Game e episódios são `game_contents`, salvo venda e identidade realmente independentes.
- **Versão regional:** mesma obra; alias regional e Release regional.
- **Retrocompatibilidade:** `availability_offers`, nunca Release original.
- **Streaming:** `availability_offers`, nunca Release original.

## Outros conceitos

- **Franquia:** conjunto oficialmente relacionado por IP, universo, marca ou continuidade. Sub-série é uma franquia com `parent_franchise_id`.
- **Ecossistema:** família de plataformas; Bethesda, Activision e Blizzard são Companies, não ecossistemas.
- **Região:** vocabulário controlado em `regions`, que inclui países ISO e mercados editoriais como WORLD, EU e NA.
- **Disponibilidade oficial atual:** acesso oficial verificável por compra, distribuição corrente, assinatura, streaming ou retrocompatibilidade, com região, estado corrente e histórico preservado.
- **Jogo preso:** classificação derivada de disponibilidade e requisitos, nunca um fato copiado diretamente de fonte.
