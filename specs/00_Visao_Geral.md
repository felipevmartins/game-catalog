# 00 — Visão Geral

## Objetivo

Manter um catálogo pessoal, verificável e recuperável de jogos, franquias, plataformas, disponibilidade oficial, coleção e hardware. O sistema é local, usa Python e SQLite e não pretende competir com bases públicas de grande escala.

## Entregáveis da aplicação futura

- banco SQLite versionado por migrations;
- CLI local;
- importações incrementais controladas;
- coleção pessoal de múltiplas cópias;
- cálculo de disponibilidade, aprisionamento e jogabilidade;
- exportações CSV, JSON e Excel por perfis de privacidade;
- backup, restauração, integridade e relatórios de execução.

## Princípios vinculantes

- Identidade interna: UUIDv7 textual, independente de nome, ano, slug ou fonte; apenas singletons técnicos e vocabulários estáticos explicitamente documentados podem usar chave não UUID.
- Identidade editorial: `Game → Edition → Release → Product`, sendo Product opcional e limitado no MVP a um único Release.
- Identidade de importação: external ID primeiro; discriminadores persistidos e imutáveis evitam que correções de data, título ou mídia criem duplicatas.
- Datas incompletas: contrato único `PartialDate`; nunca completar artificialmente.
- Dinheiro: inteiro em unidade mínima + moeda; `float` é proibido.
- Rastreabilidade: fatos externos têm referência por registro, por fato específico ou por assertion seletiva; conflitos críticos são preservados.
- Dados pessoais: segregados e protegidos contra importação, merge e exportação pública.
- Operação: uma máquina de estados de execução, fila SQLite simples, locks com token e derivados com estado/versionamento.
- Recuperabilidade: backup validado antes de migration destrutiva, merge automático ou alteração em massa.
- Simplicidade: sem event sourcing completo, DAG genérico, orquestrador distribuído ou rollback lógico universal.

## Critério de conclusão desta versão

A especificação está pronta para auditoria quando schema, migrations, arquitetura, CLI, exportação, testes e plano usam os mesmos nomes, enums e invariantes. A implementação ainda deverá provar esses contratos em SQLite real.
