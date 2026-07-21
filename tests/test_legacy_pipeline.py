import json
from pathlib import Path
from urllib.error import HTTPError

from game_catalog.integrations import rawg as rawg_module
from game_catalog.integrations.igdb import IgdbValidator
from game_catalog.integrations.legacy import (
    LegacyWikidataCollector,
    load_legacy_platforms,
    normalize_legacy,
)
from game_catalog.integrations.mobygames import MobyGamesValidator
from game_catalog.integrations.rawg import RawgValidator


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
                    {
                        "game": {"value": "http://www.wikidata.org/entity/Q4"},
                        "gameLabel": {"value": "Wii Sports Game"},
                        "platformQids": {"value": "Q8079"},
                        "firstDate": {"value": "2010-01-01T00:00:00Z"},
                        "isSports": {"value": "1"},
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
    assert counts["sports_excluded"] == 1
    assert records["Q1"]["classification"] == "candidate_stranded"
    assert records["Q2"]["classification"] == "ported_to_pc"
    assert records["Q3"]["classification"] == "ported_to_other_platform"
    assert records["Q4"]["classification"] == "excluded_sports"


def test_discovery_uses_windows_safe_cache_names(tmp_path: Path) -> None:
    policy = tmp_path / "policy.json"
    catalog = tmp_path / "platforms.json"
    policy.write_text(
        json.dumps(
            {
                "manufacturers": ["Microsoft"],
                "included_platform_types": ["home_console"],
                "platform_aliases": {},
                "excluded_genre_qids": ["Q868217"],
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


def test_mobygames_validation_is_resumable_and_classifies_ports(tmp_path: Path) -> None:
    input_file = tmp_path / "legacy.jsonl"
    records = [
        {
            "classification": "candidate_stranded",
            "wikidata_id": "Q1",
            "canonical_title": "Console Only",
            "normalized_title": "console only",
            "first_release_year": 2008,
            "source_platform_names": ["Wii"],
        },
        {
            "classification": "candidate_stranded",
            "wikidata_id": "Q2",
            "canonical_title": "Later Port",
            "normalized_title": "later port",
            "first_release_year": 2009,
            "source_platform_names": ["Wii"],
        },
    ]
    input_file.write_text(
        "".join(json.dumps(record) + "\n" for record in records), encoding="utf-8"
    )
    config = tmp_path / "config.json"
    config.write_text(
        json.dumps(
            {
                "request_delay_seconds": 0,
                "release_year_tolerance": 1,
                "platform_aliases": {},
            }
        ),
        encoding="utf-8",
    )
    responses = iter(
        [
            {
                "games": [
                    {
                        "game_id": 1,
                        "title": "Console Only",
                        "platforms": [{"platform_name": "Wii", "first_release_date": "2008"}],
                    }
                ]
            },
            {
                "games": [
                    {
                        "game_id": 2,
                        "title": "Later Port",
                        "platforms": [
                            {"platform_name": "Wii", "first_release_date": "2009"},
                            {"platform_name": "Windows", "first_release_date": "2012"},
                        ],
                    }
                ]
            },
        ]
    )
    cache = tmp_path / "cache"
    output = tmp_path / "validation.jsonl"
    report = tmp_path / "report.json"
    validator = MobyGamesValidator(lambda _: next(responses))

    first = validator.validate(
        input_file,
        config,
        cache,
        output,
        report,
        api_key="test-key",
        max_requests=1,
    )
    second = validator.validate(
        input_file,
        config,
        cache,
        output,
        report,
        api_key="test-key",
        max_requests=1,
    )

    assert first.confirmed_stranded == 1
    assert first.pending == 1
    assert second.confirmed_stranded == 1
    assert second.ported == 1
    assert second.requests_made == 1
    validated = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert validated[1]["validation"]["other_platforms"] == ["windows"]


def test_rawg_validation_uses_same_decision_states(tmp_path: Path) -> None:
    candidate = {
        "classification": "candidate_stranded",
        "wikidata_id": "Q10",
        "canonical_title": "Old Exclusive",
        "normalized_title": "old exclusive",
        "first_release_year": 2005,
        "source_platform_names": ["PlayStation 2"],
    }
    input_file = tmp_path / "legacy.jsonl"
    input_file.write_text(json.dumps(candidate) + "\n", encoding="utf-8")
    config = tmp_path / "rawg.json"
    config.write_text(
        json.dumps(
            {
                "request_delay_seconds": 0,
                "release_year_tolerance": 1,
                "platform_aliases": {},
            }
        ),
        encoding="utf-8",
    )
    response = {
        "results": [
            {
                "id": 10,
                "name": "Old Exclusive",
                "released": "2005-01-01",
                "platforms": [{"platform": {"name": "PlayStation 2"}}],
            }
        ]
    }
    validator = RawgValidator(lambda _: response)

    counts = validator.validate(
        input_file,
        config,
        tmp_path / "cache",
        tmp_path / "output.jsonl",
        tmp_path / "report.json",
        api_key="test-key",
        max_requests=1,
    )

    assert counts.confirmed_stranded == 1
    output = json.loads((tmp_path / "output.jsonl").read_text(encoding="utf-8"))
    assert output["validation"]["source"] == "rawg"
    assert RawgValidator._platform_names({"platforms": None}, {}) == set()


def test_igdb_validation_detects_related_ports(tmp_path: Path) -> None:
    candidate = {
        "classification": "candidate_stranded",
        "wikidata_id": "Q20",
        "canonical_title": "Former Exclusive",
        "normalized_title": "former exclusive",
        "first_release_year": 2005,
        "source_platform_names": ["PlayStation 2"],
    }
    input_file = tmp_path / "legacy.jsonl"
    input_file.write_text(json.dumps(candidate) + "\n", encoding="utf-8")
    config = tmp_path / "igdb.json"
    config.write_text(
        json.dumps(
            {
                "request_delay_seconds": 0,
                "release_year_tolerance": 1,
                "platform_aliases": {},
            }
        ),
        encoding="utf-8",
    )
    games = [
        {
            "id": 20,
            "name": "Former Exclusive",
            "first_release_date": 1104537600,
            "platforms": [{"name": "PlayStation 2"}],
            "ports": [{"name": "Former Exclusive", "platforms": [{"name": "Windows"}]}],
        }
    ]
    validator = IgdbValidator(
        token_transport=lambda _: {"access_token": "token"},
        games_transport=lambda _url, _headers, _body: games,
    )

    counts = validator.validate(
        input_file,
        config,
        tmp_path / "cache",
        tmp_path / "output.jsonl",
        tmp_path / "report.json",
        client_id="client",
        client_secret="secret",
        max_requests=1,
    )

    assert counts.ported == 1
    output = json.loads((tmp_path / "output.jsonl").read_text(encoding="utf-8"))
    assert output["validation"]["related_types"] == ["ports"]
    assert output["validation"]["other_platforms"] == ["windows"]


def test_rawg_transport_retries_transient_gateway_error(monkeypatch: object) -> None:
    class Response:
        def __enter__(self) -> "Response":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        @staticmethod
        def read() -> bytes:
            return b'{"results": []}'

    responses: list[object] = [
        HTTPError("https://api.rawg.io", 502, "bad gateway", {}, None),
        Response(),
    ]

    def urlopen(_request: object, timeout: int) -> object:
        assert timeout == 30
        response = responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    monkeypatch.setattr(rawg_module.urllib.request, "urlopen", urlopen)  # type: ignore[attr-defined]
    monkeypatch.setattr(rawg_module.time, "sleep", lambda _: None)  # type: ignore[attr-defined]

    assert rawg_module.rawg_json("https://api.rawg.io") == {"results": []}
