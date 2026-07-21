# First-party platform catalog

`data/import/platform_catalog.json` contains software platform families for PlayStation, Xbox and
Nintendo. The catalog is synchronized with:

```powershell
.\.tools\uv.exe run game-catalog platform sync --dry-run
.\.tools\uv.exe run game-catalog platform sync
.\.tools\uv.exe run game-catalog platform list
```

The synchronization is idempotent and preserves existing platform UUIDs and Release references.

## Modeling boundary

- A platform represents a distinct software/Release target.
- Slim, Pro, OLED, Digital Edition and regional physical revisions belong in `hardware_models`.
- Xbox Series X and Series S share one platform because they share the software generation.
- DSi and New Nintendo 3DS remain separate because they have exclusive software capability.
- PS VR and PS VR2 remain separate compatibility targets.
- PlayStation Portal is not a platform because it is a PS5 remote player.

The current catalog contains 39 platform families: 10 PlayStation, 5 Xbox and 24 Nintendo.
