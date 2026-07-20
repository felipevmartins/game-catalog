# 04 — Catálogo de Franquias

## Escopo

Catalogar franquias first-party, second-party, de IP adquirida, historicamente associadas ou fortemente ligadas a PlayStation, Xbox e Nintendo, sem reescrever a história corporativa.

## Modelo

- `franchise_ownerships` preserva a linha histórica de proprietárias/licenciadas, período e evidência; a linha `ip_owner` corrente é a única fonte da proprietária atual.
- `franchise_ecosystems` representa associação histórica/comercial e seu período, sem substituir propriedade jurídica.
- Bethesda, Activision, Blizzard e King permanecem Companies/seções editoriais dentro de relatórios Microsoft; não viram ecossistemas.
- Sub-série usa `parent_franchise_id`.
- `companies.company_type` é classificação principal não exclusiva; papéis concretos são registrados nas relações de crédito/propriedade e uma Company não é duplicada apenas por exercer outro papel.

## Status

- `active`: jogo novo relevante em até 10 anos ou projeto novo oficialmente anunciado;
- `hiatus`: mais de 10 anos sem jogo novo relevante e sem encerramento oficial;
- `officially_ended`: somente com confirmação oficial;
- `unknown`: evidência insuficiente.

Port, remaster, compilação e relançamento não reativam automaticamente uma franquia. O status guarda justificativa e evidência; alterações críticas entram em revisão.

## Visões

Listagem por ecossistema e associação, linha histórica de proprietária, franquias em hiato, cobertura da coleção e disponibilidade moderna. Todas são derivadas do schema canônico.
