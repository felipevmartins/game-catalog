"""MobyGames second-source validation for legacy platform candidates."""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from game_catalog.application.identity import normalize_name

JsonObject = dict[str, Any]
JsonTransport = Callable[[str], JsonObject]


def mobygames_json(url: str) -> JsonObject:
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
        raise ValueError("MobyGames response must be a JSON object")
    return value


@dataclass
class ValidationCounts:
    confirmed_stranded: int = 0
    ported: int = 0
    not_found: int = 0
    review_required: int = 0
    pending: int = 0
    requests_made: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            "confirmed_stranded": self.confirmed_stranded,
            "ported": self.ported,
            "not_found": self.not_found,
            "review_required": self.review_required,
            "pending": self.pending,
            "requests_made": self.requests_made,
        }


class MobyGamesValidator:
    def __init__(self, transport: JsonTransport = mobygames_json) -> None:
        self.transport = transport

    def search(self, api_key: str, title: str) -> JsonObject:
        query = urllib.parse.urlencode(
            {"api_key": api_key, "title": title, "format": "normal", "limit": 100}
        )
        return self.transport(f"https://api.mobygames.com/v1/games?{query}")

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
        candidates = [
            json.loads(line)
            for line in input_file.read_text(encoding="utf-8").splitlines()
            if line.strip() and json.loads(line).get("classification") == "candidate_stranded"
        ]
        cache_directory.mkdir(parents=True, exist_ok=True)
        counts = ValidationCounts()
        output: list[JsonObject] = []
        for candidate in candidates:
            cache = cache_directory / f"{candidate['wikidata_id']}.json"
            if cache.exists():
                response = json.loads(cache.read_text(encoding="utf-8"))
            elif counts.requests_made < max_requests:
                if not api_key:
                    raise ValueError("MOBYGAMES_API_KEY is required for uncached candidates")
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
            json.dumps({"counts": counts.to_dict()}, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return counts

    @staticmethod
    def _classify(candidate: JsonObject, response: JsonObject, config: JsonObject) -> JsonObject:
        exact = [
            game
            for game in response.get("games", [])
            if normalize_name(game.get("title", "")) == candidate["normalized_title"]
        ]
        if not exact:
            return {"source": "mobygames", "status": "not_found", "reason": "no exact title"}
        tolerance = int(config["release_year_tolerance"])
        year = candidate.get("first_release_year")
        if year is not None:
            dated = [
                game
                for game in exact
                if (game_year := MobyGamesValidator._first_year(game)) is not None
                and abs(game_year - year) <= tolerance
            ]
            if dated:
                exact = dated
        source_names = {
            MobyGamesValidator._canonical_platform(name, config)
            for name in candidate["source_platform_names"]
        }
        overlapping = [
            game
            for game in exact
            if MobyGamesValidator._platform_names(game, config) & source_names
        ]
        if overlapping:
            exact = overlapping
        if len(exact) != 1:
            return {
                "source": "mobygames",
                "status": "review_required",
                "reason": f"{len(exact)} plausible exact-title matches",
                "candidate_ids": [game.get("game_id") for game in exact],
            }
        game = exact[0]
        platforms = MobyGamesValidator._platform_names(game, config)
        other = sorted(platforms - source_names)
        return {
            "source": "mobygames",
            "status": "ported" if other else "confirmed_stranded",
            "mobygames_id": game.get("game_id"),
            "matched_title": game.get("title"),
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
        return {
            MobyGamesValidator._canonical_platform(item.get("platform_name", ""), config)
            for item in game.get("platforms", [])
            if item.get("platform_name")
        }

    @staticmethod
    def _first_year(game: JsonObject) -> int | None:
        years = []
        for platform in game.get("platforms", []):
            value = str(platform.get("first_release_date") or "")
            if len(value) >= 4 and value[:4].isdigit():
                years.append(int(value[:4]))
        return min(years) if years else None
