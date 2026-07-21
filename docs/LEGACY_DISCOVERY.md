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
game-catalog legacy validate --source mobygames --max-requests 100
game-catalog legacy validate --source rawg --max-requests 500
game-catalog legacy validate --source igdb --max-requests 100
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
- `excluded_sports` when Wikidata classifies the title as a sports video game (`Q868217`) or a
  subclass; these records do not enter second-source validation.

The result is deliberately conservative. Absence of a Wikidata statement is not proof that a
port does not exist. Applying the result only creates a `dirty` platform-lock assessment and a
review item for games already present in the catalog. It never publishes a candidate as a current,
confirmed platform lock. Candidates not yet in the curated catalog stay in the report.

## Re-running

Discovery is resumable: a successful raw platform response is reused. Delete only a specific raw
platform file when that platform must be refreshed. Normalize and dry-run are deterministic and
safe to repeat.

## Second-source validation

The `--source` option selects `mobygames`, `rawg` or `igdb`. All providers use independent caches,
normalized outputs and aggregate reports, so their evidence can coexist.

MobyGames validates the candidates in resumable batches. Configure the API key only in the
process environment; never commit it:

```powershell
$env:MOBYGAMES_API_KEY = "your-key"
game-catalog legacy validate --max-requests 100
```

At the documented one-request-per-second hobbyist limit, validating every initial candidate takes
multiple sessions. Responses are cached under `data/raw/mobygames-legacy`, so repeating the command
reuses completed work and spends the request budget only on pending candidates. Use
`--max-requests 0` to rebuild reports exclusively from the local cache.

The second-source output is `data/normalized/legacy-validation.jsonl`, with a summary in
`data/reports/legacy-validation.json`. Validation states are:

- `confirmed_stranded`: one exact MobyGames match and no additional platform;
- `ported`: another console or computer platform was found;
- `not_found`: no exact-title match;
- `review_required`: multiple plausible exact-title matches;
- `pending`: no cached response and the current request budget was exhausted.

Matching uses normalized exact titles, release-year tolerance and overlap with the originating
console. A second-source confirmation is evidence for editorial review; current storefront,
backward-compatibility and official availability still require their own checks.

Sports games are excluded by editorial preference from the legacy candidate queue. They remain in
the normalized evidence with `excluded_sports`, allowing a specific title to be curated manually
later without weakening the general rule.

### RAWG

RAWG uses `RAWG_API_KEY` from the process environment or the local `.env` file:

```powershell
$env:RAWG_API_KEY = "your-key"
game-catalog legacy validate --source rawg --max-requests 500
```

Raw responses and the detailed normalized validation stay local because RAWG terms prohibit data
redistribution. Only `data/reports/legacy-validation-rawg.json`, containing aggregate counts, is
eligible for version control. The MobyGames adapter remains available for a later paid validation.
Transient `429`, `502`, `503` and `504` responses are retried up to six times with exponential
backoff and `Retry-After` support. Completed responses remain cached if the provider stays offline.
For long runs, prefer batches of 50 to 100 requests and pause for two minutes between batches:

```powershell
do {
    $output = game-catalog legacy validate --source rawg --max-requests 100
    $output
    $state = $output | ConvertFrom-Json
    if ($state.pending -gt 0 -and $state.requests_made -gt 0) { Start-Sleep -Seconds 120 }
} while ($state.pending -gt 0 -and $state.requests_made -gt 0)
```

### IGDB

IGDB uses Twitch client-credentials OAuth. Store only the application credentials in `.env`:

```dotenv
IGDB_CLIENT_ID=your-client-id
IGDB_CLIENT_SECRET=your-client-secret
```

Run a resumable batch with:

```powershell
game-catalog legacy validate --source igdb --max-requests 100
```

The access token is generated automatically and held only in process memory. IGDB validation
checks direct platforms plus platforms exposed through `ports`, `remakes` and `remasters`. Raw and
detailed responses remain local; only `data/reports/legacy-validation-igdb.json` is versioned.
The client stays below the documented four-request-per-second limit and retries transient
`429`, `500`, `502`, `503` and `504` responses up to six times. For long runs, use batches of 100
with a 60-second pause between them.
