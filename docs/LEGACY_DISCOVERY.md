# Legacy platform discovery

The legacy pipeline searches games by console instead of franchise. Its scope is every home,
portable and hybrid console in the curated Nintendo, PlayStation and Xbox platform catalog.
Arcade systems, cloud services, VR devices and console peripherals are outside this pipeline.

## Commands

```powershell
game-catalog legacy discover
game-catalog legacy normalize
game-catalog legacy dry-run
game-catalog legacy apply
```

Raw Wikidata responses are cached under `data/raw/wikidata-legacy`. Normalized candidates are
written to `data/normalized/legacy-games.jsonl`, and the summary is written to
`data/reports/stranded-games.json`.

## Classification rule

Rule `legacy-platform-lock-v1` classifies a game as:

- `candidate_stranded` when Wikidata lists exactly one platform and the release is old enough;
- `ported_to_pc` when a Windows, Linux, macOS or DOS platform is present;
- `ported_to_other_platform` when more than one platform is present;
- `too_recent` while the configured five-year observation window has not elapsed.

The result is deliberately conservative. Absence of a Wikidata statement is not proof that a
port does not exist. Applying the result only creates a `dirty` platform-lock assessment and a
review item for games already present in the catalog. It never publishes a candidate as a current,
confirmed platform lock. Candidates not yet in the curated catalog stay in the report.

## Re-running

Discovery is resumable: a successful raw platform response is reused. Delete only a specific raw
platform file when that platform must be refreshed. Normalize and dry-run are deterministic and
safe to repeat.
