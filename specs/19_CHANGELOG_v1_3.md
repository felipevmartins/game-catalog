# 19 — CHANGELOG v1.3

## Correções estruturais

- adicionada `regions` e substituídos códigos regionais livres por FKs;
- identity keys de Edition/Release/Product/Content deixaram de incluir nome, tipo, data, mídia, SKU ou loja; foi formalizado `identity_discriminator` imutável;
- adicionada `record_source_links` para proveniência por registro sem observações universais;
- adicionada `franchise_ownerships` para linha histórica de propriedade/licença;
- adicionada `game_primary_scores` e removido o booleano sem unicidade de `game_scores`;
- `availability_offers` passou a preservar histórico e possuir uma única linha corrente por oferta lógica;
- `compatibility_rule_games` foi substituída por `compatibility_rule_releases`;
- adicionada `personal_capabilities` para rede/assinatura/conta;
- requisitos de capacidade passaram a ter contexto de provedor/plataforma;
- `partially_working` deixou de satisfazer requisito obrigatório no MVP por ausência deliberada de modelagem por componente.

## Integridade e operações

- UUIDv7 agora valida formato, versão e variante; exceções técnicas foram explicitadas;
- triggers foram exigidos para cadeias pessoais, créditos e score primário;
- uma única assertion aceita por entidade/campo e uma única revisão pendente por conflito;
- `manual_edit` foi adicionado a execution types;
- tarefas passaram a declarar `idempotency_policy`;
- recuperação de run abandonada não deixa tarefas executáveis ligadas a run terminal;
- versões de derivados podem ser NULL antes do primeiro cálculo e são obrigatórias em `current`;
- backup ganhou `retention_reason`; restore reconcilia o registro pelo sidecar específico.

## Escopo esclarecido

- Product do MVP pertence a uma única Release;
- bundle multi-Release e Product detalhado de DLC são pós-MVP;
- datas pessoais desconhecidas ficam NULL, sem data inventada;
- `company_type` é classificação principal e Company é única por nome normalizado.

## Arquivos modificados

Todos os documentos 00–30, README, casos de identidade e `schema_manifest.json` foram atualizados para v1.3.

## Riscos residuais

Referências polimórficas de assertions/record links/review dependem de allowlist e auditoria; SQL real, triggers e migrations ainda devem ser implementados e provados; termos de fontes externas continuam dependentes de revisão vigente.
