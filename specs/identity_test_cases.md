# Casos de Teste de Identidade v1.3

Cada caso parte de banco vazio, salvo indicação. `P=0` significa Product omitido porque não é necessário.

| Caso | Operação | Games | Editions | Releases | Products | Relações | Reimportação/correção |
|---|---|---:|---:|---:|---:|---:|---|
| Original | cadastrar Chrono Trigger SNES | 1 | 1 | 1 | 0 | 0 | mesmas contagens |
| Correção de data | year→day na mesma Release | 1 | 1 | 1 | 0 | 0 | mesmo UUID/discriminator |
| Port | importar versão PS1 e DS do mesmo original | 1 | 1 | 3 | 0 | 0 | mesmas contagens |
| Remaster | original + HD Remaster | 1 | 2 | 2 | 0 | 0 | mesmas contagens |
| Remake | Resident Evil 2 1998 + 2019 | 2 | 2 | 2 | 0 | 1 `remake_of` | mesmas contagens |
| Reboot | obra anterior + reboot | 2 | 2 | 2 | 0 | 1 `reboot_of` | mesmas contagens |
| Director's Cut | original + Director's Cut | 1 | 2 | 2 | 0 | 0 | mesmas contagens |
| Região | Biohazard JP + Resident Evil NA | 1 | 1 | 2 | 0 | 0; 1 alias | region_id válidos |
| Produto | físico e digital da mesma Release | 1 | 1 | 1 | 2 | 0 | correção de SKU/mídia não duplica |
| Bundle da Release | SKU bundle ligado a uma Release | 1 | 1 | 1 | 1 | 0 | mesmas contagens |
| Compilação | Rare Replay + 2 Games incluídos | 3 | 3 | 3 | 0 | 2 `compilation_contains` | mesmas contagens |
| DLC dependente | adicionar DLC | 1 | 1 | 1 | 0 | 0; contents=1 | mesmas contagens |
| Expansão standalone | base + expansão | 2 | 2 | 2 | 0 | 1 `standalone_expansion_of` | mesmas contagens |
| Episódios | temporada + 5 episódios | 1 | 1 | 1 | 0 | 0; contents=5 | mesmas contagens |
| Mesmo nome distinto | duas obras substancialmente diferentes | 2 | 2 | 2 | 0 | 1 `same_title_variant_of` | mesmas contagens |
| Retrocompatibilidade | acesso no hardware novo | 1 | 1 | 1 | 0 | 0; availability=1 | nenhuma Release extra |
| Streaming | acesso por cloud | 1 | 1 | 1 | 0 | 0; availability=1 | nenhuma Release extra |

## Rejeições

Release sem Edition, Edition sem Game, Product sem Release, relação autorreferente, slug como FK, external ID na entidade errada, discriminator alterado silenciosamente, import fuzzy automático, region_id inexistente e cadeia pessoal inconsistente são rejeitados.
