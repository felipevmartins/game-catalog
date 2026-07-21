"""RAWG second-source validation for legacy platform candidates."""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Any

from game_catalog.application.identity import normalize_name
from game_catalog.integrations.mobygames import ValidationCounts

JsonObject = dict[str, Any]
JsonTransport = Callable[[str], JsonObject]


def rawg_json(url: str) -> JsonObject:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "game-catalog/0.1 (https://github.com/felipevmartins/game-catalog)",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        value = json.loads(response.read().decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("RAWG response must be a JSON object")
    return value


class RawgValidator:
    def __init__(self, transport: JsonTransport = rawg_json) -> None:
        self.transport = transport

    def search(self, api_key: str, title: str) -> JsonObject:
        query = urllib.parse.urlencode(
            {
                "key": api_key,
                "search": title,
                "search_exact": "true",
                "page_size": 40,
            }
        )
        return self.transport(f"https://api.rawg.io/api/games?{query}")

    def validate(
        self,
        input_file: Path,
        config_file: Path,
        cache_directory: Path,
        output_file: Path,
        report_file: Path,
        *,
        api_key: str | None,
        max_requests: int,
    ) -> ValidationCounts:
        config = json.loads(config_file.read_text(encoding="utf-8"))
        candidates = []
        for line in input_file.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("classification") == "candidate_stranded":
                candidates.append(record)
        cache_directory.mkdir(parents=True, exist_ok=True)
        counts = ValidationCounts()
        output: list[JsonObject] = []
        for candidate in candidates:
            cache = cache_directory / f"{candidate['wikidata_id']}.json"
            if cache.exists():
                response = json.loads(cache.read_text(encoding="utf-8"))
            elif counts.requests_made < max_requests:
                if not api_key:
                    raise ValueError("RAWG_API_KEY is required for uncached candidates")
                if counts.requests_made:
                    time.sleep(float(config["request_delay_seconds"]))
                response = self.search(api_key, candidate["canonical_title"])
                cache.write_text(
                    json.dumps(response, ensure_ascii=False, indent=2), encoding="utf-8"
                )
                counts.requests_made += 1
            else:
                counts.pending += 1
                continue
            validation = self._classify(candidate, response, config)
            candidate["validation"] = validation
            output.append(candidate)
            status = validation["status"]
            setattr(counts, status, getattr(counts, status) + 1)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(
            "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in output),
            encoding="utf-8",
        )
        report_file.parent.mkdir(parents=True, exist_ok=True)
        report_file.write_text(
            json.dumps({"source": "rawg", "counts": counts.to_dict()}, indent=2),
            encoding="utf-8",
        )
        return counts

    @staticmethod
    def _classify(candidate: JsonObject, response: JsonObject, config: JsonObject) -> JsonObject:
        exact = [
            game
            for game in response.get("results", [])
            if normalize_name(game.get("name", "")) == candidate["normalized_title"]
        ]
        if not exact:
            return {"source": "rawg", "status": "not_found", "reason": "no exact title"}
        year = candidate.get("first_release_year")
        tolerance = int(config["release_year_tolerance"])
        if year is not None:
            dated = [
                game
                for game in exact
                if (game_year := RawgValidator._release_year(game)) is not None
                and abs(game_year - year) <= tolerance
            ]
            if dated:
                exact = dated
        source_names = {
            RawgValidator._canonical_platform(name, config)
            for name in candidate["source_platform_names"]
        }
        overlapping = [
            game for game in exact if RawgValidator._platform_names(game, config) & source_names
        ]
        if overlapping:
            exact = overlapping
        if len(exact) != 1:
            return {
                "source": "rawg",
                "status": "review_required",
                "reason": f"{len(exact)} plausible exact-title matches",
                "candidate_ids": [game.get("id") for game in exact],
            }
        game = exact[0]
        platforms = RawgValidator._platform_names(game, config)
        other = sorted(platforms - source_names)
        return {
            "source": "rawg",
            "status": "ported" if other else "confirmed_stranded",
            "rawg_id": game.get("id"),
            "matched_title": game.get("name"),
            "platform_names": sorted(platforms),
            "other_platforms": other,
            "reason": "additional platform release found" if other else "only source console found",
        }

    @staticmethod
    def _canonical_platform(name: str, config: JsonObject) -> str:
        canonical = config.get("platform_aliases", {}).get(name, name)
        return normalize_name(canonical)

    @staticmethod
    def _platform_names(game: JsonObject, config: JsonObject) -> set[str]:
        names = set()
        for wrapper in game.get("platforms") or []:
            platform = wrapper.get("platform", {})
            name = platform.get("name")
            if name:
                names.add(RawgValidator._canonical_platform(name, config))
        return names

    @staticmethod
    def _release_year(game: JsonObject) -> int | None:
        value = str(game.get("released") or "")
        return int(value[:4]) if len(value) >= 4 and value[:4].isdigit() else None
