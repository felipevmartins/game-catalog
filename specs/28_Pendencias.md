# 28 — Pendências Reais

## Bloqueadores documentais restantes

- nenhum bloqueador documental conhecido; a auditoria independente final pode encontrar novos;
- migrations SQL, triggers e partial indexes ainda precisam ser implementados e testados em SQLite real;
- a implementação deve escolher biblioteca UUIDv7 e provar formato/ordenação.

## Decisões humanas necessárias

- fontes externas habilitadas e revisão atual de termos/licenças;
- lista inicial de regions, plataformas, franquias e razões seed;
- discriminadores manuais para múltiplas Releases/Products estruturalmente equivalentes;
- limites percentuais para alteração em massa;
- região padrão do usuário.

## Melhorias pós-MVP

UI web, pesquisa de preço de usados, bundles multi-Release, produtos comerciais de DLC, capacidade por componente de hardware parcialmente funcional, histórico completo de empréstimos, capas/imagens, relatórios avançados, moedas históricas e sincronização.

## Deliberadamente fora do escopo

Event sourcing completo, rollback lógico universal, DAG/orquestrador distribuído, múltiplos writers, marketplace público, observação por campo para todo dado, motor de regras genérico e cobertura mundial exaustiva.

## Risco residual

SQLite/FKs não garantem diretamente referências polimórficas de `record_source_links`, `catalog_assertions` e `review_queue`; o risco é mitigado por allowlists, services e auditoria periódica. Regras editoriais ambíguas continuam exigindo decisão humana e fonte.
