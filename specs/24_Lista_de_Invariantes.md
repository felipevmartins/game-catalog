# 24 — Lista de Invariantes

## Garantidos pelo SQLite

- PK/FK, UUIDv7 canônico, unicidades e partial indexes;
- Edition→Game, Release→Edition, Product→Release;
- region_id válido nas entidades regionais;
- relação de Game não autorreferente;
- external ID único por source/context;
- uma Edition original ativa no máximo por Game;
- uma assertion accepted por entidade/campo;
- uma linha corrente por offer_identity_key;
- um score primário por Game;
- um motivo primário de lock por Game;
- pares monetários e ranges básicos;
- task running exige token/expiração e dedupe ativa;
- triggers de cadeia pessoal, crédito e score primário;
- CASCADE apenas em filhos dependentes e RESTRICT em dados sensíveis.

## Garantidos pelo domínio/application services

- calendário gregoriano de PartialDate e comparação/ordenação;
- discriminator imutável em Edition/Release/Product/Content e independente de nome/tipo/data/mídia/SKU;
- regra editorial port/remaster/remake/reboot;
- merge com redirecionamento pessoal e resolução de colisões;
- uma única propriedade `ip_owner` corrente por franquia;
- seleção de fonte, override, campo ausente e contrato alterado;
- transições de execution/task, ordem determinística e recuperação de run abandonada;
- claim/heartbeat/finish por fencing token;
- tarefas review_required nunca têm retry automático;
- all_of/any_of, capacidades e compatibilidade por Release;
- partially_working não satisfaz requisito obrigatório no MVP;
- marcação dirty no mesmo UnitOfWork;
- allowlist de exportação, current-only e redaction;
- backup válido antes do primeiro write funcional protegido.

## Verificados por auditoria/testes de integridade

- referências polimórficas apontam a entidade permitida;
- existe ao menos uma Edition original ativa por Game completo;
- selected_titles possui ao menos uma Release quando exigido;
- diagrama, manifest, migrations e matriz possuem o mesmo conjunto de tabelas;
- toda coluna exportada está classificada;
- nenhuma regra obsoleta reaparece em documentos;
- restore reproduz contagens/hash lógico e reconcilia registro pelo sidecar;
- derivados current têm versões correspondentes às entradas;
- nenhuma task executável pertence a execution_run terminal e nenhuma run finaliza com task pending/running;
- motivos de lock só são exportados quando assessment current.

A regra é colocada em uma camada principal; outras camadas só fazem defesa quando o custo/risco justifica.
