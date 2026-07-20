# 13 — Atualização Incremental, Manutenção e Recuperação

## Máquina de estados única

Toda operação relevante usa `execution_runs`:

`queued → running → succeeded | succeeded_with_warnings | failed | cancelled`.

A transição excepcional `running → queued` é permitida somente pela recuperação de run abandonada com tarefas restantes idempotentes. Não existem estados físicos concorrentes em `import_runs`/`update_runs`. Tipo de execução distingue import, update, recalculate, export, backup, restore, migration, merge, maintenance e manual_edit.

## Fila SQLite

`run_tasks` usa estados `pending|running|succeeded|failed|dead_letter|cancelled`. Dedupe key é única enquanto pending/running. Claim escolhe deterministicamente por `critical→high→normal→low`, depois `scheduled_for`, `created_at` e `id`; é transacional e gera novo `lock_token`; heartbeat/conclusão exigem o mesmo token. Reclaim após expiração troca o token, impedindo o worker antigo de concluir.

Cada tarefa declara `idempotency_policy=idempotent|review_required`. Em falha retryable de tarefa idempotente, a transação incrementa `attempt_count`, limpa lock e devolve a tarefa a `pending` com backoff enquanto `attempt_count < max_attempts`. Ao atingir o limite, vira `dead_letter`. Erro não retryable vira `failed`. Tarefa review_required nunca é reexecutada automaticamente. Não há tabela dead-letter separada nem DAG genérico. Uma run só pode ser finalizada quando não houver task pending/running; succeeded_with_warnings admite tasks failed/dead_letter, nunca tasks executáveis.

## Pipeline incremental

1. validar configuração/schema;
2. criar run operacional;
3. adquirir lock global quando a operação escreve em massa/migra/mescla;
4. criar e validar backup se a política exigir;
5. selecionar/claim tarefas;
6. coletar/normalizar/validar;
7. resolver identidade e conflitos;
8. persistir fatos e change log em transação curta;
9. marcar derivados afetados dirty no mesmo commit;
10. recalcular ou deixar tarefa pendente;
11. executar integrity/foreign_key checks conforme risco;
12. finalizar run e relatório.

A criação da run não autoriza writes funcionais antes do backup. Falha do backup finaliza a run como failed sem mutação de catálogo/pessoal/fila funcional.

## Recuperação de execução abandonada

Na inicialização, uma run `running` com heartbeat vencido e sem lock global ativo é analisada atomicamente:

- se todas as tarefas não terminais forem idempotentes, locks expirados são limpos, tarefas voltam a pending e a run volta a queued para retomada;
- se existir tarefa `review_required`, a run vira failed, tarefas não terminais são canceladas e uma revisão deduplicada é criada;
- nunca permanecem tarefas executáveis vinculadas a run terminal.

## Dirty/stale/versionamento

- mudança persistida em entrada marca `platform_lock_assessments`/`personal_playability` dirty no mesmo commit;
- dado vencido ou contrato não verificado marca stale;
- recálculo grava rule_version e input_version usados e só então muda para current;
- linhas novas dirty podem ter versões nulas; current exige versões e resultado;
- falha mantém failed/dirty e não apresenta resultado como atual.

## Dry-run e falhas parciais

Dry-run não escreve dados funcionais, filas ou pessoais. Uma tarefa falha sem invalidar commits anteriores de outras tarefas; a run termina `succeeded_with_warnings` quando há resultado útil e falhas isoladas. Cada tarefa mantém atomicidade própria.

## Backup e restore

Backup íntegro é obrigatório antes do primeiro write funcional em catálogo ou dados pessoais de atualização em massa, migration destrutiva, merge automático ou rotina acima do limite configurado. Falha de backup aborta. Restore fecha conexões, valida hash/integridade/schema, salva o estado atual, substitui atomicamente, reinsere o registro do backup a partir do sidecar, registra a restauração e marca derivados dirty.

## Rollback

- rollback transacional: desfaz a transação atual;
- downgrade Alembic: volta schema quando implementado/seguro;
- restore: substitui banco por backup;
- correção compensatória: nova operação explícita.

Não há rollback lógico universal por entidade e `change_log` não é event sourcing.

## Retenção e manutenção

Política padrão: últimos 10 operacionais, 7 diários, 4 semanais, 12 mensais e todos os backups `release`/`audit_snapshot` ou `retained`. Nunca remover o único backup íntegro conhecido nem qualquer backup com `retained=1` e `retention_reason` preenchido. A política é configurável, mas esses mínimos são o default.

Manutenção executa `integrity_check`, `foreign_key_check`, auditoria de referências polimórficas, checkpoint WAL, ANALYZE e VACUUM sob necessidade.
