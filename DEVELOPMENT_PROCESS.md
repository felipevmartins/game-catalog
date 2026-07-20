# Processo de desenvolvimento

## Fluxo de trabalho

O projeto evolui em fatias verticais pequenas. Cada mudança deve partir de um item do `DEVELOPMENT_PLAN.md`, preservar os contratos do `CANONICAL_BASELINE.md` e terminar com evidência automatizada do gate afetado.

1. Selecionar uma entrega pequena e registrar seus critérios de aceite.
2. Criar uma branch curta a partir de `main` no formato `feat/...`, `fix/...`, `docs/...` ou `chore/...`.
3. Escrever ou ajustar o teste que demonstra o comportamento e o invariante relevante.
4. Implementar pela camada proprietária da regra, sem writes que contornem services/Unit of Work.
5. Executar `uv run ruff format --check .`, `uv run ruff check .`, `uv run mypy src` e `uv run pytest`.
6. Revisar migrations, privacidade, logs e documentação conforme o risco da mudança.
7. Integrar em `main` somente com CI verde e critérios de aceite satisfeitos.

Commits usam Conventional Commits, são pequenos e não misturam refatoração não relacionada. A branch `main` deve permanecer executável.

## Ambiente reproduzível

- Python 3.12 ou superior.
- `uv` gerencia ambiente, dependências e lockfile.
- `pyproject.toml` declara requisitos amplos; `uv.lock` registra versões exatas e deve ser versionado.
- Testes de persistência usam arquivos SQLite temporários reais, nunca um substituto em memória quando WAL, migrations, triggers ou concorrência fizerem parte do comportamento.

Preparação:

```powershell
uv python install 3.12
uv sync
uv run alembic upgrade head
uv run pytest
```

## Gates por mudança

| Tipo | Evidência obrigatória |
|---|---|
| Domínio/serviço | teste unitário e invariantes afetados |
| Repository/schema | teste de integração em SQLite real |
| Migration | upgrade, downgrade documentado, integridade e preservação quando aplicável |
| Importação/fila | idempotência, transação, retry/fencing e falha parcial |
| Dados pessoais | prova de que importadores não escrevem no agregado pessoal |
| Exportação/log | allowlist, redaction e teste de ausência de campos sensíveis |
| Operação destrutiva ou em massa | backup válido e restore previamente comprovado |

## Definition of Done

- critério de aceite reproduzível e aprovado;
- formatação, lint, tipos e testes verdes;
- migration e downgrade/restore tratados quando houver mudança de schema;
- nenhum novo campo exportado sem classificação explícita;
- logs e mensagens não expõem dados pessoais, caminhos ou erros brutos;
- matrizes, decisões e documentação atualizadas quando o contrato mudar;
- working tree limpa após o commit.

## Decisões e exceções

Decisões arquiteturais novas entram em `docs/decisions/` antes de criarem dependência persistente. Exceções temporárias precisam de responsável, motivo, impacto e condição de remoção; não se resolve ambiguidade das specs inventando comportamento.
