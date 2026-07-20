# Codex Game Catalog — Especificação v1.3

Especificação funcional, relacional, arquitetural e operacional de uma aplicação Python local com SQLite para catálogo pessoal de jogos e hardware.

## Estado

A versão v1.3 está **pronta para uma nova auditoria independente**. Isto não constitui aprovação para produção nem autorização para iniciar integrações externas sem revisar seus termos vigentes.

## Fonte da verdade e precedência

1. `06_Decisoes_Consolidadas.md` e `17_Decisoes_Canonicas_Datas_Dinheiro_IDs_e_Identidade.md`;
2. `08_Modelo_Relacional_Detalhado.md`;
3. documentos temáticos 09–14;
4. `15_Plano_de_Implementacao_para_o_Codex.md`;
5. matrizes, casos e anexos.

SQLite é a fonte da verdade. CSV, JSON e Excel são snapshots derivados. Dados pessoais nunca são escritos por importadores externos.

## Ordem de leitura

00 a 17, depois RFC, changelog, matrizes, invariantes, testes, migrations, prova, pendências e revisão cruzada.

## Regra de obsolescência

A v1.3 elimina os modelos antigos `game_platforms`, `personal_collection` 1:1, `import_runs` e `compatibility_rule_games`. Menções históricas aparecem apenas em declarações explícitas de remoção/substituição.
