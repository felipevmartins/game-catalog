# 25 — Testes de Propriedade

Manter apenas propriedades ligadas a riscos reais:

1. **Identidade idempotente:** qualquer ordem/repetição das mesmas entradas com external IDs/discriminators produz as mesmas contagens e relações.
2. **Correção não duplica:** alterar nome/tipo de Edition ou Content, data/release_type de Release, mídia/loja/SKU de Product não altera UUID/discriminator nem cria nova entidade.
3. **Renomeação estável:** alterar título/alias não altera UUID nem FKs.
4. **Port/remaster/remake:** port não aumenta Games; remaster aumenta Editions, não Games; remake aumenta Games e cria relação.
5. **PartialDate round-trip:** valores válidos serializam/persistem sem ganhar/perder precisão; unknown nunca aceita qualifier; inválidos são rejeitados.
6. **Money round-trip:** para expoentes 0, 2 e 3, formatar e parsear preserva amount_minor/moeda; nenhum float é aceito.
7. **Merge preserva pessoal:** para qualquer conjunto válido de itens/unidades relacionados, merge redireciona ou aborta sem perda.
8. **Availability history:** qualquer sequência available→unavailable→available preserva três períodos e exatamente uma linha corrente.
9. **Fencing:** após expiração/reclaim, o token antigo nunca conclui/atualiza a tarefa.
10. **Abandoned run:** recuperação nunca produz task pending/running sob run terminal.
11. **Dirty atomic:** qualquer alteração de entrada que comita deixa o derivado current impossível até recálculo correspondente.
12. **Export deny-by-default:** adicionar coluna aleatória ao model não a inclui em public/shareable.
13. **Backup antes do write:** em falha injetada na criação/validação, nenhuma mutação funcional de risco é observável.

Não usar property tests para regras meramente enumerativas que ficam mais claras como exemplos unitários.
