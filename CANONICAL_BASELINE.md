# Baseline canônico v1.3

## Fontes e precedência

1. `06_Decisoes_Consolidadas.md` e `17_Decisoes_Canonicas_Datas_Dinheiro_IDs_e_Identidade.md`.
2. `08_Modelo_Relacional_Detalhado.md`.
3. Documentos temáticos `09` a `14`.
4. `15_Plano_de_Implementacao_para_o_Codex.md`.
5. Matrizes, casos e anexos.

Em caso de conflito, esta ordem prevalece. O baseline não substitui as specs; ele registra as decisões necessárias para impedir deriva durante a implementação.

## Stack vinculante

- Python 3.12 ou superior.
- SQLAlchemy 2.x e Alembic.
- Pydantic, Typer e pytest.
- SQLite local como fonte da verdade.
- Arquitetura em camadas: `domain`, `application`, `persistence`, `integrations`, `exports`, `cli` e `maintenance`.

Versões exatas das dependências serão escolhidas e travadas na Etapa 2, após verificar a instalação local e compatibilidade entre pacotes.

## Contratos congelados

### Identidade

- Cadeia: `Game → Edition → Release → Product`; Product é opcional e representa uma única Release no MVP.
- Port e remaster mantêm o Game; remake e reboot criam outro Game.
- IDs internos de domínio, pessoais e operacionais são UUIDv7; exceções técnicas e associativas devem ser explícitas.
- UUID valida formato canônico, versão 7 e variante RFC 4122.
- Slugs, nomes e IDs externos nunca são PK/FK internas.
- `identity_discriminator` de Edition, Release, Product e Content é opaco, persistido e imutável.
- Nome, tipo classificatório, data, mídia, SKU e loja não fazem parte da identidade.
- Resolução tenta: ID externo exato, chave estrutural/discriminador e, apenas como candidato de revisão, similaridade aproximada.

### PartialDate

- Campos: `year`, `month`, `day`, `precision`, `qualifier`.
- Precisões: `unknown`, `year`, `month`, `day`.
- Qualificadores: `circa`, `before`, `after` ou nulo para exato.
- Validação gregoriana completa fica no domínio; SQLite garante estrutura e ranges.
- `unknown` não contém componentes nem qualifier.
- Não existe uma coluna de data completa concorrente para o mesmo evento.

### Money

- `Money(amount_minor: int, currency_code: str)`; floats são proibidos.
- Valor e moeda são ambos nulos ou ambos preenchidos.
- Expoente monetário vem do registro ISO 4217 da aplicação; não se presume duas casas.
- Conversão é somente visão/relatório e não substitui o valor original.

### Persistência e operação

- Migrations seguem estritamente `0001_foundation` até `0009_seed_reference_data`.
- Toda conexão habilita `PRAGMA foreign_keys=ON`.
- Proveniência usa `record_source_links`, FKs específicas e `catalog_assertions` somente onde o conflito é independente por campo.
- Toda mutação manual cria `execution_run` do tipo `manual_edit` e passa por Unit of Work/change log.
- Estados derivados carregam estado e versão; valor stale/dirty não é apresentado como atual.
- Fila usa SQLite e fencing por `lock_token`.
- Exportações usam allowlists explícitas e snapshot consistente.

## Escopo negativo congelado

- Tabelas obsoletas proibidas: `game_platforms`, `personal_collection`, `import_runs`, `update_queue` e `compatibility_rule_games`.
- Sem HTTP ou coletores externos antes da prova vertical.
- Sem escrita de importadores em dados pessoais.
- Sem event sourcing completo, rollback lógico universal, orquestrador distribuído ou múltiplos writers.
- Itens pós-MVP permanecem fora desta implementação inicial, conforme `28_Pendencias.md`.

## Seeds mínimos já especificados

- Prova vertical: fontes `manual` e `official`; regiões `WORLD`, `JP` e `NA`; plataformas SNES, PS1, DS e PS5; hardware PS5.
- Seeds usam UUIDv7 constantes geradas uma vez e versionadas na migration; não são hashes de nomes.

## Decisões humanas ainda abertas

Estas escolhas não serão presumidas durante a implementação:

- fontes externas a habilitar e aceite de seus termos/licenças atuais;
- lista inicial completa de regiões, plataformas, franquias e razões seed além do mínimo da prova;
- discriminadores manuais para Releases/Products estruturalmente equivalentes;
- limites percentuais para operações em massa;
- região padrão do usuário;
- biblioteca concreta de UUIDv7, que deve ser escolhida na Etapa 2 e comprovada por testes de formato e ordenação.

## Critério de conclusão da Etapa 1

- plano incremental registrado;
- contratos acima compatíveis com as fontes canônicas;
- decisões humanas separadas de decisões técnicas;
- nenhuma implementação iniciada sobre uma escolha ainda aberta;
- aprovação humana deste baseline antes da Etapa 2.
