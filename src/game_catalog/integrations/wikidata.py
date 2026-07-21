"""Conservative Wikidata discovery for editorially approved franchises."""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError

from game_catalog.application.identity import normalize_name

JsonObject = dict[str, Any]
JsonTransport = Callable[[str], JsonObject]


@dataclass(frozen=True)
class FranchiseSeed:
    key: str
    canonical_name: str
    ecosystem: str
    aliases: tuple[str, ...]
    inclusion_status: str


def load_franchise_catalog(path: Path) -> list[FranchiseSeed]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    ecosystems = {item["key"] for item in payload["ecosystems"]}
    seeds: list[FranchiseSeed] = []
    keys: set[str] = set()
    for item in payload["franchises"]:
        if item["key"] in keys:
            raise ValueError(f"duplicate franchise key: {item['key']}")
        if item["ecosystem"] not in ecosystems:
            raise ValueError(f"unknown ecosystem: {item['ecosystem']}")
        keys.add(item["key"])
        seeds.append(
            FranchiseSeed(
                key=item["key"],
                canonical_name=item["canonical_name"],
                ecosystem=item["ecosystem"],
                aliases=tuple(item.get("aliases", [])),
                inclusion_status=item.get("inclusion_status", "approved"),
            )
        )
    return seeds


def http_json(url: str) -> JsonObject:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/sparql-results+json, application/json",
            "User-Agent": "game-catalog/0.1 (https://github.com/felipevmartins/game-catalog)",
        },
    )
    for attempt in range(5):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
            break
        except HTTPError as error:
            if error.code not in (429, 502, 503, 504) or attempt == 4:
                raise
            retry_after = error.headers.get("Retry-After")
            wait_seconds = float(retry_after) if retry_after else float(2 ** (attempt + 1))
            time.sleep(min(wait_seconds, 60.0))
    else:  # pragma: no cover
        raise RuntimeError("Wikidata retry loop ended unexpectedly")
    if not isinstance(payload, dict):
        raise ValueError("Wikidata response must be a JSON object")
    return payload


class WikidataCollector:
    def __init__(
        self, transport: JsonTransport = http_json, delay_seconds: float | None = None
    ) -> None:
        self.transport = transport
        self.delay_seconds = (
            1.1 if delay_seconds is None and transport is http_json else (delay_seconds or 0.0)
        )
        self._request_count = 0

    def _get(self, url: str) -> JsonObject:
        if self._request_count and self.delay_seconds:
            time.sleep(self.delay_seconds)
        payload = self.transport(url)
        self._request_count += 1
        return payload

    def search(self, seed: FranchiseSeed) -> JsonObject:
        parameters = urllib.parse.urlencode(
            {
                "action": "wbsearchentities",
                "search": seed.canonical_name,
                "language": "en",
                "uselang": "en",
                "type": "item",
                "limit": 10,
                "format": "json",
                "origin": "*",
            }
        )
        return self._get(f"https://www.wikidata.org/w/api.php?{parameters}")

    def resolve(self, seed: FranchiseSeed, search_payload: JsonObject) -> tuple[str | None, str]:
        accepted_names = {normalize_name(name) for name in (seed.canonical_name, *seed.aliases)}
        matches: list[tuple[int, int, str]] = []
        for candidate in search_payload.get("search", []):
            label = normalize_name(candidate.get("label", ""))
            aliases = {normalize_name(value) for value in candidate.get("aliases", [])}
            description = normalize_name(candidate.get("description", ""))
            rank = self._description_rank(description)
            name_rank = 0 if label in accepted_names else 1 if aliases & accepted_names else None
            if rank is not None and name_rank is not None:
                matches.append((name_rank, rank, candidate["id"]))
        best_rank = min(((name_rank, rank) for name_rank, rank, _ in matches), default=None)
        unique = sorted({qid for name_rank, rank, qid in matches if (name_rank, rank) == best_rank})
        if seed.inclusion_status == "review_required":
            return (unique[0] if len(unique) == 1 else None), "review_required"
        if len(unique) == 1:
            return unique[0], "resolved"
        return None, "ambiguous" if unique else "unresolved"

    @staticmethod
    def _description_rank(description: str) -> int | None:
        series_markers = (
            "video game series",
            "video game subseries",
            "series of video games",
        )
        if any(marker in description for marker in series_markers):
            return 0
        if "video game franchise" in description:
            return 1
        if "media franchise" in description:
            return 2
        return None

    def games(self, qid: str) -> JsonObject:
        query = f"""
SELECT DISTINCT ?game ?gameLabel WHERE {{
  ?game wdt:P179 wd:{qid}; wdt:P31/wdt:P279* wd:Q7889.
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,pt". }}
}}
ORDER BY ?gameLabel
""".strip()
        parameters = urllib.parse.urlencode({"query": query, "format": "json"})
        return self._get(f"https://query.wikidata.org/sparql?{parameters}")

    def collect(self, catalog_path: Path, raw_directory: Path) -> list[JsonObject]:
        raw_directory.mkdir(parents=True, exist_ok=True)
        results: list[JsonObject] = []
        for seed in load_franchise_catalog(catalog_path):
            target = raw_directory / f"{seed.key}.json"
            if target.exists():
                existing = json.loads(target.read_text(encoding="utf-8"))
                if isinstance(existing, dict) and existing.get("schema_version") == 1:
                    qid, status = self.resolve(seed, existing["search_response"])
                    previous = existing["franchise"].get("wikidata_id")
                    existing["franchise"]["wikidata_id"] = qid
                    existing["franchise"]["resolution_status"] = status
                    if qid and status == "resolved" and qid != previous:
                        existing["games_response"] = self.games(qid)
                    elif status != "resolved":
                        existing["games_response"] = {"results": {"bindings": []}}
                    target.write_text(
                        json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8"
                    )
                    results.append(existing)
                    continue
            search_payload = self.search(seed)
            qid, status = self.resolve(seed, search_payload)
            games_payload = (
                self.games(qid) if qid and status == "resolved" else {"results": {"bindings": []}}
            )
            record: JsonObject = {
                "schema_version": 1,
                "source": "wikidata",
                "franchise": {
                    "key": seed.key,
                    "canonical_name": seed.canonical_name,
                    "ecosystem": seed.ecosystem,
                    "aliases": list(seed.aliases),
                    "inclusion_status": seed.inclusion_status,
                    "wikidata_id": qid,
                    "resolution_status": status,
                },
                "search_response": search_payload,
                "games_response": games_payload,
            }
            target.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
            results.append(record)
        return results


def normalize_raw_directory(
    raw_directory: Path, output_file: Path, overrides_file: Path | None = None
) -> dict[str, int]:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    records: list[JsonObject] = []
    counts = {"franchises": 0, "games": 0, "unresolved": 0, "review_required": 0}
    for path in sorted(raw_directory.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        franchise = raw["franchise"]
        status = franchise["resolution_status"]
        if status != "resolved":
            counts[status] = counts.get(status, 0) + 1
        records.append({"record_type": "franchise", **franchise, "source": "wikidata"})
        counts["franchises"] += 1
        if status != "resolved":
            continue
        seen: set[str] = set()
        for binding in raw["games_response"].get("results", {}).get("bindings", []):
            uri = binding.get("game", {}).get("value", "")
            qid = uri.rsplit("/", 1)[-1]
            title = binding.get("gameLabel", {}).get("value", "").strip()
            if not qid.startswith("Q") or not title or title == qid or qid in seen:
                continue
            seen.add(qid)
            records.append(
                {
                    "record_type": "game",
                    "franchise_key": franchise["key"],
                    "canonical_title": title,
                    "normalized_title": normalize_name(title),
                    "wikidata_id": qid,
                    "source": "wikidata",
                }
            )
            counts["games"] += 1
    existing_qids = {record["wikidata_id"] for record in records if record["record_type"] == "game"}
    if overrides_file is not None and overrides_file.exists():
        overrides = json.loads(overrides_file.read_text(encoding="utf-8"))
        for override in overrides.get("games", []):
            if override.get("review_status") != "approved":
                continue
            qid = override["wikidata_id"]
            if qid in existing_qids:
                continue
            title = override["canonical_title"].strip()
            records.append(
                {
                    "record_type": "game",
                    "franchise_key": override["franchise_key"],
                    "canonical_title": title,
                    "normalized_title": normalize_name(title),
                    "wikidata_id": qid,
                    "source": "wikidata",
                }
            )
            existing_qids.add(qid)
            counts["games"] += 1
    with output_file.open("w", encoding="utf-8", newline="\n") as stream:
        for record in records:
            stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    return counts
