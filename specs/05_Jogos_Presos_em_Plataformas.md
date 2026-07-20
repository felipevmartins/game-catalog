# 05 — Jogos Presos em Plataformas

## Unidade de análise

A classificação final é por `Game`, calculada a partir de Releases, `availability_offers`, requisitos e compatibilidade. Retrocompatibilidade e streaming são meios atuais de acesso, não novos Releases.

## Severidade

1. exclusivo atual;
2. restrito à família/ecossistema;
3. depende de hardware antigo;
4. parcialmente perdido ou requer periférico raro;
5. comercialmente indisponível, mas acessível por mídia usada;
6. inacessível oficialmente.

A severidade é uma ordenação editorial e precisa de justificativa. Um Game não preso tem `severity_level = NULL`. `no_pc_version` isoladamente nunca é suficiente para marcar um Game como preso; disponibilidade em hardware moderno, região e meios oficiais também devem ser considerados.

## Motivos seed

`no_pc_version`, `no_modern_release`, `limited_backward_compatibility`, `digital_store_closed`, `delisted`, `expired_license`, `servers_closed`, `peripheral_dependency`, `old_hardware_dependency`, `partially_lost_content`, `regional_limit`, `other`.

## Estado derivado

`platform_lock_assessments` guarda `state`, `rule_version`, `input_version` e `calculated_at`. Mudança em Release, disponibilidade, requisito ou regra marca `dirty` na mesma transação. Dado vencido fica `stale`. Valores e motivos só são exportados como atuais quando o assessment está `current`; a CLI nunca mostra valor dirty/stale como atual sem aviso explícito.

## Relevância

O catálogo prioriza títulos histórica, cultural ou colecionavelmente relevantes; não busca cobertura indiscriminada de todo software antigo.
