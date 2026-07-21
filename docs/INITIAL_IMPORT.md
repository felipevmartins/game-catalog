# Initial franchise import

The initial import is intentionally split into reproducible stages. External identity is accepted
only from an exact Wikidata series/franchise match; titles never merge Games automatically.

## Files

- `data/import/franchise_catalog.json`: editorial scope, ecosystem and aliases.
- `data/import/source_registry.json`: reviewed source contract and redistribution policy.
- `data/raw/wikidata/*.json`: local immutable responses (ignored by Git).
- `data/normalized/franchises-games.jsonl`: deterministic import input.
- `data/reports/initial-import.json`: coverage and pending human decisions.

## Commands

```powershell
$env:UV_CACHE_DIR='.uv-cache'
.\.tools\uv.exe run game-catalog db init
.\.tools\uv.exe run game-catalog import discover
.\.tools\uv.exe run game-catalog import normalize
.\.tools\uv.exe run game-catalog import dry-run
.\.tools\uv.exe run game-catalog import apply
```

Running `import apply` again is safe. Exact Wikidata external IDs resolve existing records; the
same normalized snapshot and review conflict are deduplicated.

## Current snapshot

- 47 editorial franchises across PlayStation, Xbox and Nintendo.
- 42 franchise identities resolved automatically.
- 458 Games normalized and imported with an original Edition, including the curated
  `Fable Anniversary` Wikidata exception.
- 5 franchise identities pending human review.
- raw QID labels, missing labels and duplicate external IDs are excluded or reported.

Pending review does not fail the import. The editorial Franchise remains present, but no Wikidata
external ID or discovered Games are accepted for it until the decision is explicit.
