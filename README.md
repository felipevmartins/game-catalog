# Game Catalog

Aplicação local em Python e SQLite para catálogo pessoal de jogos, coleção e hardware. O projeto está no início da implementação da especificação v1.3.

- [Análise das especificações](SPEC_ANALYSIS.md)
- [Baseline canônico](CANONICAL_BASELINE.md)
- [Plano de desenvolvimento](DEVELOPMENT_PLAN.md)
- [Processo de desenvolvimento](DEVELOPMENT_PROCESS.md)
- [Pacote completo de especificações](specs/README.md)

## Desenvolvimento

Requer Python 3.12+ e `uv`:

```powershell
uv sync
uv run pytest
uv run ruff check .
uv run mypy src
```

