import json
from pathlib import Path

from game_catalog.integrations.legacy import (
    LegacyWikidataCollector,
    load_legacy_platforms,
    normalize_legacy,
)


def test_policy_covers_every_supported_console_family() -> None:
    _, platforms = load_legacy_platforms(
        Path("data/import/legacy_platform_policy.json"),
        Path("data/import/platform_catalog.json"),
    )

    assert len(platforms) == 30
    assert {platform.ecosystem for platform in platforms} == {"PlayStation", "Xbox", "Nintendo"}
    assert {"PlayStation", "Xbox 360", "Wii", "Nintendo Switch 2"} <= {
        platform.name for platform in platforms
    }


def test_normalize_classifies_single_platform_conservatively(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    payload = {
        "platform": {
            "name": "Wii",
            "ecosystem": "Nintendo",
            "release_year": 2006,
            "wikidata_id": "Q8079",
            "resolution_status": "resolved",
        },
        "games_response": {
            "results": {
                "bindings": [
                    {
                        "game": {"value": "http://www.wikidata.org/entity/Q1"},
                        "gameLabel": {"value": "Only Wii"},
                        "platformQids": {"value": "Q8079"},
                        "firstDate": {"value": "2009-01-01T00:00:00Z"},
                    },
                    {
                        "game": {"value": "http://www.wikidata.org/entity/Q2"},
                        "gameLabel": {"value": "Wii and PC"},
                        "platformQids": {"value": "Q8079|Q1406"},
                        "firstDate": {"value": "2010-01-01T00:00:00Z"},
                    },
                    {
                        "game": {"value": "http://www.wikidata.org/entity/Q3"},
                        "gameLabel": {"value": "Wii and Console"},
                        "platformQids": {"value": "Q8079|Q10683"},
                        "firstDate": {"value": "2011-01-01T00:00:00Z"},
                    },
                ]
            }
        },
    }
    (raw / "wii.json").write_text(json.dumps(payload), encoding="utf-8")
    output = tmp_path / "legacy.jsonl"
    report = tmp_path / "report.json"

    counts = normalize_legacy(raw, Path("data/import/legacy_platform_policy.json"), output, report)
    records = {
        record["wikidata_id"]: record
        for record in map(json.loads, output.read_text(encoding="utf-8").splitlines())
    }

    assert counts["candidates"] == 1
    assert counts["ported"] == 2
    assert records["Q1"]["classification"] == "candidate_stranded"
    assert records["Q2"]["classification"] == "ported_to_pc"
    assert records["Q3"]["classification"] == "ported_to_other_platform"


def test_discovery_uses_windows_safe_cache_names(tmp_path: Path) -> None:
    policy = tmp_path / "policy.json"
    catalog = tmp_path / "platforms.json"
    policy.write_text(
        json.dumps(
            {
                "manufacturers": ["Microsoft"],
                "included_platform_types": ["home_console"],
                "platform_aliases": {},
            }
        ),
        encoding="utf-8",
    )
    catalog.write_text(
        json.dumps(
            {
                "manufacturers": [{"key": "microsoft", "name": "Microsoft"}],
                "ecosystems": [{"key": "xbox", "name": "Xbox"}],
                "platforms": [
                    {
                        "name": "Xbox Series X|S",
                        "manufacturer": "microsoft",
                        "ecosystem": "xbox",
                        "platform_type": "home_console",
                        "release_year": 2020,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    responses = iter(
        [
            {
                "search": [
                    {
                        "id": "Q1",
                        "label": "Xbox Series X|S",
                        "description": "home video game console",
                    }
                ]
            },
            {"results": {"bindings": []}},
        ]
    )

    LegacyWikidataCollector(lambda _: next(responses)).collect(policy, catalog, tmp_path / "raw")

    assert (tmp_path / "raw" / "xbox-series-x-s.json").exists()
