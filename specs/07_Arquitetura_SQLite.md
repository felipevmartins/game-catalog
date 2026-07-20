# 07 — Arquitetura SQLite

## Configuração

- SQLite em WAL para operação normal;
- `PRAGMA foreign_keys = ON` em toda conexão;
- `PRAGMA busy_timeout = 5000` configurável;
- um único escritor por processo de aplicação; transações curtas;
- SQLAlchemy 2.x e Alembic.

## IDs e tipos

UUIDv7 é `TEXT` em formato canônico: 36 caracteres, hífens nas posições 9/14/19/24, somente hexadecimal, nibble de versão `7` e variante RFC 4122 (`8|9|a|b`). PKs não são geradas de título, ano, plataforma, data, mídia ou loja. `schema_metadata.id=1` e PKs compostas associativas são exceções técnicas. Timestamps são UTC ISO-8601; datas pessoais exatas usam ISO Date; PartialDate usa colunas componentes. Dinheiro é INTEGER em unidade mínima.

## Integridade

- FKs de catálogo usam `RESTRICT` quando uma exclusão poderia apagar histórico ou dados pessoais.
- CASCADE é permitido apenas em filhos puramente dependentes/associativos.
- entidades de catálogo usam soft delete quando necessário;
- partial unique indexes garantem uma Edition original ativa, uma assertion aceita por campo, uma seleção primária de score e um motivo primário de lock;
- triggers de integridade verificam cadeias cruzadas de `personal_collection_items`, `game_companies` e `game_primary_scores`;
- entidades hierárquicas são verificadas contra ciclos pelo service e por auditoria de integridade;
- merges ocorrem por serviço transacional: validar, criar backup quando exigido, redirecionar dependências, resolver colisões de external IDs, marcar duplicata e registrar change log.

## Concorrência e locks

A fila reclama tarefas com um único `UPDATE ... RETURNING` dentro de transação curta. Cada claim gera novo `lock_token` UUIDv7 e `lock_expires_at`. Conclusão/heartbeat usa `WHERE id=? AND status='running' AND lock_token=?`; após reclaim, o worker antigo não consegue concluir.

Operações globais (migration, restore, merge automático e atualização em massa) usam um lock de arquivo do sistema operacional adjacente ao banco, mantido pelo processo, combinado com `BEGIN IMMEDIATE` antes da fase de escrita. O conteúdo do arquivo registra apenas `execution_run_id` e timestamp; não contém caminho absoluto, credencial ou dado pessoal. Falha em adquirir o lock aborta antes de writes funcionais protegidos.

## Backup/WAL

Não copiar apenas o arquivo `.db` enquanto houver WAL ativo. O BackupService:

1. bloqueia novas escritas pelo lock global da aplicação;
2. espera transações curtas terminarem;
3. executa checkpoint apropriado;
4. usa SQLite Online Backup API para arquivo temporário;
5. sincroniza, abre a cópia e executa `integrity_check` e `foreign_key_check`;
6. calcula SHA-256 e renomeia atomicamente;
7. grava um manifesto sidecar com hash/versões e registra `backups.integrity_status=valid`.

O sidecar é específico do backup, não um manifesto universal. Na restauração, ele permite validar a cópia e reinserir/atualizar o registro do backup após a substituição, mesmo quando o snapshot ainda não continha sua própria linha.

Restauração fecha todas as conexões, valida alvo, cria backup do estado atual, substitui atomicamente, reabre, registra o evento, verifica schema/integridade e marca derivados dirty.

## Migrations

A sequência oficial está no documento 26. Downgrade é destinado a desenvolvimento quando seguro; em produção local, mudanças destrutivas preferem restauração ou migration corretiva. Toda migration destrutiva exige backup validado.

## Critérios

Banco vazio migra até head, FKs/checks/triggers passam, todos os nomes do diagrama existem no catálogo do documento 08 e nenhum comando depende de coluna inexistente.
