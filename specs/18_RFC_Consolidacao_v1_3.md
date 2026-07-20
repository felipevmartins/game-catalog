# 18 — RFC de Consolidação v1.3

## Status

Consolidada e pronta para auditoria independente.

## Problema resolvido

A v1.3 integrou os grandes blocos da auditoria, mas manteve inconsistências implementáveis: identity keys dependiam de fatos mutáveis, histórico de disponibilidade era sobrescrito, proveniência por registro não tinha mecanismo comum, propriedade histórica não possuía tabela, selected_titles apontava para Game, requisitos de capacidade não tinham persistência e runs abandonadas podiam deixar tarefas executáveis sob run terminal.

## Solução mínima

SQLite local, um escritor coordenado, fila simples com fencing e política de idempotência, proveniência por registro/fato/assertion seletiva, backup físico íntegro, dois caches derivados versionados e coleção multi-item. Não adota event sourcing, rollback lógico universal, DAG genérico ou motor de regras geral.

## Precedência

Documentos 06/17, depois 08, documentos temáticos, plano e anexos.
