# Análise das especificações v1.3

## Resumo executivo

O pacote em `specs/` descreve uma aplicação local em Python 3.12+ com SQLite para catalogar jogos, lançamentos, produtos, coleção pessoal, hardware, disponibilidade e proveniência. A especificação está suficientemente detalhada para iniciar a implementação local, mas ainda depende de auditoria independente e de decisões humanas antes de habilitar fontes externas.

A fonte da verdade é o SQLite. CSV, JSON e Excel são exportações derivadas. A identidade central segue `Game → Edition → Release → Product`, com UUIDv7 internos e discriminadores persistidos e imutáveis. Dados pessoais formam um limite explícito de privacidade e nunca podem ser alterados por importadores.

## Inventário analisado

- 31 documentos numerados (`00` a `30`), além do README, casos de identidade e manifesto JSON.
- 53 tabelas físicas no manifesto canônico.
- 9 migrations obrigatórias, de `0001_foundation` a `0009_seed_reference_data`.
- 15 cenários na prova vertical mínima.
- Matrizes separadas para cobertura, persistência, auditoria e invariantes.

## Pontos fortes

- Precedência documental explícita para resolver conflitos.
- Separação clara entre identidade, classificação e dados pessoais.
- Invariantes atribuídos ao mecanismo adequado: FK/check/trigger, domínio, serviço ou auditoria.
- Estratégia de migrations, backup, restore e downgrade documentada.
- Operações incrementais contemplam idempotência, fencing por `lock_token`, retry, dead-letter e recuperação.
- Exportações são deny-by-default, com allowlists e teste contra vazamento.
- A prova vertical reúne os riscos mais importantes em um gate reproduzível.

## Riscos de implementação

| Risco | Impacto | Mitigação no plano |
|---|---|---|
| Divergência entre ORM, migrations e manifesto | Integridade silenciosamente diferente da especificação | Gerar testes de schema em SQLite real e comparar nomes, FKs, checks, triggers e índices |
| Regras cruzadas não representáveis somente por FK | Referências polimórficas inválidas ou estado inconsistente | Centralizar writes em services/Unit of Work e executar auditorias periódicas |
| Identidade instável durante reimportação | Duplicação de Game/Edition/Release/Product | Implementar `IdentityService` cedo e executar casos de identidade e idempotência como gate |
| Vazamento de dados pessoais | Exposição de serial, preço, localização ou notas | Allowlist deny-by-default, redaction e varredura automática de exportações |
| Concorrência SQLite e worker obsoleto | Task concluída duas vezes ou por dono antigo | Transações curtas, WAL/busy timeout e fencing obrigatório por token |
| Migration ou operação em massa sem recuperação | Perda de catálogo ou coleção | Backup validado e restore testado antes de writes de alto risco em banco com dados |
| Escopo prematuro de integrações externas | Dependência de termos, limites e formatos instáveis | Manter HTTP fora do caminho crítico até a prova vertical e revisão humana |

## Decisões bloqueantes

Não bloqueiam a fundação local, o schema ou a prova vertical:

- biblioteca concreta de UUIDv7, a selecionar e validar na fundação;
- região padrão do usuário;
- catálogo seed além do mínimo da prova;
- limites percentuais para alterações em massa;
- discriminadores manuais em casos estruturalmente equivalentes;
- fontes externas e aceite atualizado de seus termos/licenças.

Essas escolhas devem virar registros de decisão antes de afetarem código ou dados persistidos.

## Estratégia recomendada

Implementar em fatias verticais pequenas, com migrations e persistência reais desde o começo. O primeiro marco executável deve provar a cadeia de identidade e uma reimportação idempotente sem HTTP. Recursos pessoais entram depois que a identidade estiver estável; backup/restore deve estar operacional antes de qualquer fluxo destrutivo ou de alto volume. A prova vertical completa é o gate para integrações externas.

O sequenciamento, os entregáveis e os gates executáveis estão em `DEVELOPMENT_PLAN.md`. As decisões já congeladas para impedir deriva estão em `CANONICAL_BASELINE.md`.
