# 27 — Prova Vertical Mínima

## Fixture base

Fontes `manual` e `official`; regions WORLD/JP/NA; plataformas SNES, PS1, DS, PS5; hardware PS5; Games/editions/releases com UUIDv7 e discriminadores fixos de fixture.

## Cenários e resultados

1. **Original:** 1 Game, 1 Edition original, 1 Release, 0 Product.
2. **Port:** adicionar PS1 e DS → 1 Game, 1 Edition, 3 Releases; reimportar não muda contagens.
3. **Correções não identitárias:** renomear/reclassificar Edition e corrigir Release de year/original para day/port → mesmas contagens e mesmos UUIDs/discriminators.
4. **Remaster:** adicionar Edition remaster + Release → 1 Game, 2 Editions, 2 Releases.
5. **Remake:** adicionar novo Game/Edition/Release + `remake_of` → 2/2/2 e 1 relação.
6. **Múltiplas cópias:** físico completo, loose e licença digital do mesmo Game → 3 personal_collection_items; trigger rejeita Product de outro Game.
7. **Propriedade histórica:** duas proprietárias sequenciais → timeline preservada e a proprietária atual é derivada da única linha `ip_owner` corrente.
8. **Disponibilidade:** available→unavailable→available → três linhas históricas e exatamente uma corrente; export current mostra somente a última.
9. **Hardware obrigatório:** Release exige all_of(console, câmera) e any_of(controle A, B), mais assinatura. Sem câmera/assinatura: false; com câmera, B e capability ativa: true; câmera partially_working: false; unidade sold: não satisfaz.
10. **Compatibilidade selecionada:** regra selected_titles inclui Release A, não B; apenas A é compatível.
11. **Atualização incremental:** duas tasks equivalentes deduplicam e prioridades/empates são consumidos em ordem determinística; worker A perde lock, B reclaim; A não conclui; B conclui uma vez.
12. **Run abandonada:** tasks idempotentes fazem run voltar queued; tarefa review_required faz run failed, cancela tasks e cria review. Nenhuma task executável sob run terminal.
13. **Dirty/stale:** nova availability marca platform lock dirty no mesmo commit; leitura não afirma valor/motivo antigo; recálculo volta current.
14. **Falha/recuperação:** falha de backup aborta atualização sem writes funcionais; restore recupera contagens, reconcilia backup pelo sidecar e marca derivados dirty.
15. **Export público:** varrer por serial, preços, acquired_from, loaned_to, private_notes, personal_capabilities, location, caminhos e erro bruto; zero ocorrências. Coluna nova não classificada é omitida/faz teste falhar.

## Gate

A prova usa SQLite real, migrations completas, triggers e services reais; mocks só para resposta de fonte. Resultado é relatório com contagens, IDs, hashes, state/version e ausência de vazamento.
