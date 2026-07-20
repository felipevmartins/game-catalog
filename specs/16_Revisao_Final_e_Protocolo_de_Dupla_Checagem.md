# 16 — Revisão Final e Protocolo de Dupla Checagem

## Resultado da consolidação

A v1.3 corrige inconsistências residuais da v1.3 em identidade estável, regiões, proveniência, propriedade histórica, disponibilidade temporal, capacidades pessoais, compatibilidade por Release, recuperação de runs e exportações.

## Gates da auditoria final

### A — Validação determinística

- comparar tabelas do documento 08 com diagrama, migration 26, manifest e matriz 22;
- buscar termos do relatório 29;
- validar enums repetidos;
- verificar todos os comandos contra schema/services;
- confirmar allowlists e classificação de colunas;
- conferir links internos e versão v1.3;
- validar que identity_key não contém data/título/SKU/mídia;
- validar que nenhuma tarefa executável pertence a run terminal.

### B — Auditoria adversarial independente

Usar o prompt 20. Classificar falhas objetivas separadamente de melhorias pós-MVP e não promover complexidade distribuída sem risco concreto.

### C — Prova vertical

Executar fixtures do documento 27 em SQLite real, incluindo correção de data sem duplicata, reimportação, merge seguro, lock expirado, run abandonada, falha de backup, restore, histórico de disponibilidade e export público.

## Veredito permitido

Somente: “a versão corrigida está pronta para uma nova auditoria independente”. Não declarar aprovação para produção.
