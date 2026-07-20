# 06 — Decisões Consolidadas v1.3

## Decisões funcionais preservadas

- Mobile e arcade ficam fora do foco amplo, salvo relevância explícita.
- Exclusivos regionais entram quando necessários à cronologia ou relevância da IP.
- Metacritic é armazenado por Release; a nota principal do Game é uma seleção editorial em `game_primary_scores`, sem média própria.
- HowLongToBeat é opcional; tempos ficam em minutos inteiros e não são estimados.
- Preço médio de usados permanece pós-MVP.
- Franquias adquiridas preservam história corporativa em `franchise_ownerships`.

## Decisões estruturais vinculantes

1. A cadeia é `Game → Edition → Release → Product`, Product opcional e de uma única Release no MVP.
2. `game_platforms` está removida; plataforma pertence a `releases`.
3. `personal_collection` 1:1 está removida; usa-se `personal_collection_items` 1:N.
4. `import_runs` está removida; usa-se `execution_runs` para todos os tipos de operação, inclusive `manual_edit`.
5. Port não cria Game; remaster não cria Game; remake/reboot cria Game.
6. Retrocompatibilidade e streaming são `availability_offers`, com histórico e uma linha corrente por oferta lógica.
7. UUIDv7 é interno; slugs e IDs externos não são chaves relacionais. Discriminadores de identidade são persistidos e não incluem fatos mutáveis.
8. PartialDate e dinheiro têm contratos únicos do documento 17.
9. Proveniência usa `record_source_links` por registro, FKs diretas em fatos específicos e `catalog_assertions` somente para campos com conflito independente.
10. Importadores escrevem apenas catálogo/externo/operacional, nunca tabelas pessoais.
11. Merges redirecionam FKs pessoais na mesma transação e exigem backup quando automáticos/em massa.
12. Fila é SQLite, sem orquestrador distribuído, com `lock_token` de fencing e política de idempotência por tarefa.
13. Derivados têm estado e versões; valor não atual é exibido como não atual.
14. Backup é validado antes do primeiro write funcional protegido de uma operação de risco; metadados da run podem ser criados antes do backup.
15. Rollback transacional, downgrade, restauração e compensação são mecanismos diferentes; não há rollback lógico universal.
16. Exportações são allowlists explícitas e snapshot consistente.
17. Códigos regionais vêm do vocabulário `regions`.
18. Compatibilidade `selected_titles` referencia Releases, não Games.
19. Requisitos de capacidade pessoal dependem de `personal_capabilities`; hardware `partially_working` não satisfaz requisito obrigatório no MVP.
