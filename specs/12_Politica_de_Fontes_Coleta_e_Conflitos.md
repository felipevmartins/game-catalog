# 12 — Política de Fontes, Coleta e Conflitos

## Contrato de fonte

Cada `sources` registra tipo compatível com configuração, prioridade 0–100, confiança padrão, integração, termos, versão do contrato, licença, atribuição, redistribuição, TTL e estado enabled. Mudança de contrato/termos desabilita o coletor até revisão; dados existentes não são apagados.

Tipos: `official`, `store`, `database`, `collaborative`, `review_aggregator`, `duration_aggregator`, `archive`, `press`, `community`, `manual`, `other`.

## Granularidade de proveniência

- fatos source-specific possuem FK direta para `source_references`;
- entidades/registros gerais usam `record_source_links` com papel primary/supporting/historical;
- `catalog_assertions` é usado apenas em campos com conflitos independentes relevantes, como título canônico, data, propriedade de IP, disponibilidade crítica e identidade;
- não existe obrigação de observação universal para todo campo.

Uma assertion `accepted` é única por entidade/campo. Override manual é uma assertion aceita de fonte manual e prevalece até supersessão explícita.

## Prioridade

Fonte oficial específica vence base secundária para fatos controlados pela publicadora/fabricante. Metacritic e HLTB são autoridade apenas para seus próprios indicadores. Agregadores ajudam descoberta, não decidem sozinhos propriedade, encerramento, retrocompatibilidade, conteúdo perdido ou merge.

## Aplicação de respostas

- campo ausente: não limpa valor existente;
- tombstone/remoção explícita: pode alterar após política e auditoria;
- fonte inferior: não sobrescreve valor aceito de fonte superior;
- conflito relevante: preserva assertions e cria `review_queue` deduplicada;
- override manual: assertion aceita com `is_manual_override=1`, prevalece até ser explicitamente removida/superseded;
- fonte desativada: impede novas coletas, não invalida automaticamente fatos históricos;
- dado expirado: permanece, mas é marcado/interpretado como stale;
- mudança de contrato: pausa integração e registra alerta.

## Validade

`source_references` registra retrieved, verified e valid_until. TTL inicial configurável por fonte/campo: lojas/assinaturas 7 dias, servidores 30, retrocompatibilidade 90, notas 180, duração 365; histórico validado pode não expirar.

`availability_offers` preserva histórico: mudança de estado encerra a linha corrente e cria nova linha corrente com a mesma `offer_identity_key`.

## Identidade e merge

External ID exato e contexto correto podem resolver identidade. Sem external ID, Edition/Release/Product/Content usam discriminador persistido e estável; nome, tipo classificatório, data, SKU ou mídia corrigidos não geram nova identidade. Fuzzy match, nome, ano ou slug nunca fazem merge automático. Colisão entre IDs externos ou mudança Game/Edition exige revisão.

## Coleta responsável

Credenciais apenas em ambiente/secret store; cache, backoff e baixa concorrência; sem contornar bloqueio, autenticação ou termos. Configurações e contratos devem ser revistos na implementação, pois serviços externos mudam.

## Testes

Fonte superior prevalece, campo ausente não limpa, uma única assertion aceita, override manual permanece, expiração gera stale, fonte desativada não coleta, contrato alterado bloqueia, conflito não duplica revisão, fuzzy não faz merge, correção de nome/tipo/data não duplica Edition/Release e dados pessoais não recebem fonte externa.
