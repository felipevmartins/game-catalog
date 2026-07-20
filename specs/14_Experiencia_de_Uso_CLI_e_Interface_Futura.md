# 14 — CLI e Experiência de Uso

## Identificadores

```bash
codex game show --id 0190f2b4-....          # UUIDv7 interno
codex game show --slug chrono-trigger       # busca; pode ser ambígua
codex game show --external-id igdb:12345    # resolve source/context/external_id
```

Slug nunca é FK e um resultado ambíguo exige escolha; external ID não é tratado como UUID. `identity_discriminator` é interno ao serviço e só é exposto em comandos avançados quando há múltiplas Releases/Products estruturalmente equivalentes.

## Comandos essenciais

- `db init|status|migrate|integrity-check`;
- `region|manufacturer|ecosystem|company|franchise|platform list|show|search`;
- `game list|show|search|add|edit|merge`;
- `edition add|list`, `release add|list`, `product add|list`;
- `collection add|list|update|loan|return|sell`;
- `hardware add|list|update|sell`, `accessory ...`, `capability add|list|update|remove`;
- `availability update`, `playability show|recalculate`, `lock show|recalculate`;
- `import run --source ... [--dry-run]`, `update run`, `queue list|retry|cancel`;
- `review list|show|approve|reject|defer`;
- `backup create|list|verify|restore`;
- `export --profile public|shareable|personal|technical`;
- `run show|list`, `doctor`.

Toda mutação manual cria run `manual_edit` e change log redigido.

## Segurança

- merge, restore, migration destrutiva e alteração em massa exigem backup validado;
- modo não interativo falha quando confirmação sensível não foi fornecida;
- export default é `public`;
- `--json` usa códigos estáveis e mensagens redigidas;
- erro não imprime credencial, serial, capacidade pessoal, nota privada ou caminho absoluto.

## Derivados

`show` informa `current|dirty|stale|failed`. Por padrão, valor não current não é apresentado como fato atual; `--include-stale` exibe com aviso e versões. Motivos de lock não current também são ocultados por padrão.

## Interface futura

Uma UI web é pós-MVP e deve chamar os mesmos application services. Não altera schema, regras de privacidade ou modelo de execução.
