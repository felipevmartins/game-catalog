"""IGDB second-source validation for legacy platform candidates."""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError

from game_catalog.application.identity import normalize_name
from game_catalog.integrations.mobygames import ValidationCounts

JsonObject = dict[str, Any]
TokenTransport = Callable[[str], JsonObject]
GamesTransport = Callable[[str, dict[str, str], bytes], list[JsonObject]]


def token_json(url: str) -> JsonObject:
    request = urllib.request.Request(url, method="POST")
    value = _urlopen_json(request)
    if not isinstance(value, dict):
        raise ValueError("IGDB token response must be a JSON object")
    return value


def games_json(url: str, headers: dict[str, str], body: bytes) -> list[JsonObject]:
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    value = _urlopen_json(request)
    if not isinstance(value, list):
        raise ValueError("IGDB games response must be a JSON array")
    return value


def _urlopen_json(request: urllib.request.Request) -> Any:
    for attempt in range(6):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            if error.code not in (429, 500, 502, 503, 504) or attempt == 5:
                raise
            retry_after = error.headers.get("Retry-After")
            seconds = float(retry_after) if retry_after and retry_after.isdigit() else 2**attempt
            time.sleep(min(seconds, 30.0))
        except (TimeoutError, URLError):
            if attempt == 5:
                raise
            time.sleep(min(float(2**attempt), 30.0))
    raise RuntimeError("IGDB retry loop ended unexpectedly")


class IgdbValidator:
    def __init__(
        self,
        token_transport: TokenTransport = token_json,
        games_transport: GamesTransport = games_json,
    ) -> None:
        self.token_transport = token_transport
        self.games_transport = games_transport

    def access_token(self, client_id: str, client_secret: str) -> str:
        query = urllib.parse.urlencode(
            {
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "client_credentials",
            }
        )
        response = self.token_transport(f"https://id.twitch.tv/oauth2/token?{query}")
        token = response.get("access_token")
        if not isinstance(token, str) or not token:
            raise ValueError("IGDB authentication did not return an access token")
        return token

    def search(self, client_id: str, access_token: str, title: str) -> JsonObject:
        escaped = title.replace("\\", "\\\\").replace('"', '\\"')
        body = (
            "fields id,name,first_release_date,platforms.name,"
            "ports.name,ports.platforms.name,remakes.name,remakes.platforms.name,"
            "remasters.name,remasters.platforms.name;"
            f' search "{escaped}"; limit 50;'
        ).encode()
        headers = {
            "Accept": "application/json",
            "Client-ID": client_id,
            "Authorization": f"Bearer {access_token}",
        }
        return {"games": self.games_transport("https://api.igdb.com/v4/games", headers, body)}

    def validate(
        self,
        input_file: Path,
        config_file: Path,
        cache_directory: Path,
        output_file: Path,
        report_file: Path,
        *,
        client_id: str | None,
        client_secret: str | None,
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
        token: str | None = None
        for candidate in candidates:
            cache = cache_directory / f"{candidate['wikidata_id']}.json"
            if cache.exists():
                response = json.loads(cache.read_text(encoding="utf-8"))
            elif counts.requests_made < max_requests:
                if not client_id or not client_secret:
                    raise ValueError(
                        "IGDB_CLIENT_ID and IGDB_CLIENT_SECRET are required for uncached candidates"
                    )
                if token is None:
                    token = self.access_token(client_id, client_secret)
                if counts.requests_made:
                    time.sleep(float(config["request_delay_seconds"]))
                response = self.search(client_id, token, candidate["canonical_title"])
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
            json.dumps({"source": "igdb", "counts": counts.to_dict()}, indent=2),
            encoding="utf-8",
        )
        return counts

    @staticmethod
    def _classify(candidate: JsonObject, response: JsonObject, config: JsonObject) -> JsonObject:
        exact = [
            game
            for game in response.get("games", [])
            if normalize_name(game.get("name", "")) == candidate["normalized_title"]
        ]
        if not exact:
            return {"source": "igdb", "status": "not_found", "reason": "no exact title"}
        year = candidate.get("first_release_year")
        tolerance = int(config["release_year_tolerance"])
        if year is not None:
            dated = [
                game
                for game in exact
                if (game_year := IgdbValidator._release_year(game)) is not None
                and abs(game_year - year) <= tolerance
            ]
            if dated:
                exact = dated
        source_names = {
            IgdbValidator._canonical_platform(name, config)
            for name in candidate["source_platform_names"]
        }
        overlapping = [
            game for game in exact if IgdbValidator._direct_platforms(game, config) & source_names
        ]
        if overlapping:
            exact = overlapping
        if len(exact) != 1:
            return {
                "source": "igdb",
                "status": "review_required",
                "reason": f"{len(exact)} plausible exact-title matches",
                "candidate_ids": [game.get("id") for game in exact],
            }
        game = exact[0]
        direct = IgdbValidator._direct_platforms(game, config)
        related = IgdbValidator._related_platforms(game, config)
        other = sorted((direct | related) - source_names)
        relations = sorted(
            relation for relation in ("ports", "remakes", "remasters") if game.get(relation)
        )
        return {
            "source": "igdb",
            "status": "ported" if other else "confirmed_stranded",
            "igdb_id": game.get("id"),
            "matched_title": game.get("name"),
            "platform_names": sorted(direct),
            "related_platform_names": sorted(related),
            "related_types": relations,
            "other_platforms": other,
            "reason": "additional platform or adaptation found"
            if other
            else "only source console found",
        }

    @staticmethod
    def _canonical_platform(name: str, config: JsonObject) -> str:
        canonical = config.get("platform_aliases", {}).get(name, name)
        return normalize_name(canonical)

    @staticmethod
    def _platforms(items: Any, config: JsonObject) -> set[str]:
        if not isinstance(items, list):
            return set()
        return {
            IgdbValidator._canonical_platform(item["name"], config)
            for item in items
            if isinstance(item, dict) and isinstance(item.get("name"), str)
        }

    @staticmethod
    def _direct_platforms(game: JsonObject, config: JsonObject) -> set[str]:
        return IgdbValidator._platforms(game.get("platforms"), config)

    @staticmethod
    def _related_platforms(game: JsonObject, config: JsonObject) -> set[str]:
        platforms: set[str] = set()
        for relation in ("ports", "remakes", "remasters"):
            items = game.get(relation)
            if not isinstance(items, list):
                continue
            for item in items:
                if isinstance(item, dict):
                    platforms.update(IgdbValidator._platforms(item.get("platforms"), config))
        return platforms

    @staticmethod
    def _release_year(game: JsonObject) -> int | None:
        value = game.get("first_release_date")
        if not isinstance(value, int):
            return None
        return datetime.fromtimestamp(value, tz=UTC).year
