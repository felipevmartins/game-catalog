# Instruções do projeto para o Codex

## Indicador de contexto

Comece toda atualização de progresso e toda resposta final ao usuário com uma linha neste formato:

`Contexto estimado: [████████░░] ~80% disponível`

- Use dez blocos na barra, preenchidos com `█` e vazios com `░`.
- Mostre a porcentagem aproximada de contexto ainda disponível.
- Mantenha a palavra `estimado`, pois o agente pode não ter acesso à telemetria real da interface.
- Atualize a estimativa ao longo de sessões extensas; não apresente precisão falsa.
