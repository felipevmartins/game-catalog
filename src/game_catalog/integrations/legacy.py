"""Platform-oriented discovery of games potentially stranded on consoles."""

from __future__ import annotations

import json
import re
import urllib.parse
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from game_catalog.application.identity import normalize_name
from game_catalog.integrations.wikidata import JsonTransport, http_json

JsonObject = dict[str, Any]


@dataclass(frozen=True)
class LegacyPlatform:
    name: str
    ecosystem: str
    release_year: int
    aliases: tuple[str, ...]


def load_legacy_platforms(
    policy_file: Path, platform_catalog: Path
) -> tuple[JsonObject, list[LegacyPlatform]]:
    policy = json.loads(policy_file.read_text(encoding="utf-8"))
    catalog = json.loads(platform_catalog.read_text(encoding="utf-8"))
    manufacturers = set(policy["manufacturers"])
    types = set(policy["included_platform_types"])
    excluded = set(policy.get("excluded_platforms", []))
    aliases = policy.get("platform_aliases", {})
    ecosystems = {item["key"]: item["name"] for item in catalog["ecosystems"]}
    records = [
        LegacyPlatform(
            name=item["name"],
            ecosystem=ecosystems[item["ecosystem"]],
            release_year=item["release_year"],
            aliases=tuple(dict.fromkeys([item["name"], *aliases.get(item["name"], [])])),
        )
        for item in catalog["platforms"]
        if item["manufacturer"]
        in {
            manufacturer["key"]
            for manufacturer in catalog["manufacturers"]
            if manufacturer["name"] in manufacturers
        }
        and item["platform_type"] in types
        and item["name"] not in excluded
    ]
    return policy, records


class LegacyWikidataCollector:
    def __init__(self, transport: JsonTransport = http_json) -> None:
        self.transport = transport

    def _get(self, url: str) -> JsonObject:
        return self.transport(url)

    def resolve_platform(self, platform: LegacyPlatform) -> tuple[str | None, JsonObject]:
        candidates: list[JsonObject] = []
        for name in platform.aliases:
            query = urllib.parse.urlencode(
                {
                    "action": "wbsearchentities",
                    "search": name,
                    "language": "en",
                    "uselang": "en",
                    "type": "item",
                    "limit": 10,
                    "format": "json",
                }
            )
            payload = self._get(f"https://www.wikidata.org/w/api.php?{query}")
            candidates.extend(payload.get("search", []))
        accepted = {normalize_name(platform.name), *(normalize_name(x) for x in platform.aliases)}
        matches = []
        for candidate in candidates:
            label = normalize_name(candidate.get("label", ""))
            description = normalize_name(candidate.get("description", ""))
            if label in accepted and any(
                marker in description
                for marker in (
                    "video game console",
                    "handheld game console",
                    "portable game console",
                    "home video game console",
                    "hybrid video game console",
                    "dual-screen handheld",
                    "handheld electronic game",
                    "dedicated console",
                )
            ):
                matches.append(candidate["id"])
        unique = list(dict.fromkeys(matches))
        return (unique[0] if unique else None), {"search": candidates}

    def games(self, platform_qid: str) -> JsonObject:
        sparql = f"""
SELECT ?game ?gameLabel (MIN(?date) AS ?firstDate)
       (GROUP_CONCAT(DISTINCT STRAFTER(STR(?platform), '/entity/'); separator='|') AS ?platformQids)
WHERE {{
  ?game wdt:P31/wdt:P279* wd:Q7889; wdt:P400 wd:{platform_qid}; wdt:P400 ?platform.
  OPTIONAL {{ ?game wdt:P577 ?date. }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,pt". }}
}}
GROUP BY ?game ?gameLabel
ORDER BY ?gameLabel
""".strip()
        query = urllib.parse.urlencode({"query": sparql, "format": "json"})
        return self._get(f"https://query.wikidata.org/sparql?{query}")

    def collect(
        self, policy_file: Path, platform_catalog: Path, raw_directory: Path
    ) -> dict[str, int]:
        _, platforms = load_legacy_platforms(policy_file, platform_catalog)
        raw_directory.mkdir(parents=True, exist_ok=True)
        counts = {"platforms": len(platforms), "resolved": 0, "games": 0}
        for platform in platforms:
            slug = re.sub(r"[^a-z0-9]+", "-", normalize_name(platform.name)).strip("-")
            target = raw_directory / f"{slug}.json"
            if target.exists():
                record = json.loads(target.read_text(encoding="utf-8"))
                qid = record.get("platform", {}).get("wikidata_id")
                if qid:
                    counts["resolved"] += 1
                    counts["games"] += len(
                        record.get("games_response", {}).get("results", {}).get("bindings", [])
                    )
                    continue
            qid, search = self.resolve_platform(platform)
            games = self.games(qid) if qid else {"results": {"bindings": []}}
            record = {
                "schema_version": 1,
                "source": "wikidata",
                "platform": {
                    "name": platform.name,
                    "ecosystem": platform.ecosystem,
                    "release_year": platform.release_year,
                    "wikidata_id": qid,
                    "resolution_status": "resolved" if qid else "unresolved",
                },
                "search_response": search,
                "games_response": games,
            }
            target.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
            if qid:
                counts["resolved"] += 1
                counts["games"] += len(games.get("results", {}).get("bindings", []))
        return counts


def normalize_legacy(
    raw_directory: Path, policy_file: Path, output: Path, report: Path
) -> dict[str, int]:
    policy = json.loads(policy_file.read_text(encoding="utf-8"))
    cutoff = datetime.now(UTC).year - int(policy["minimum_release_age_years"])
    merged: dict[str, JsonObject] = {}
    unresolved: list[str] = []
    platform_names: dict[str, str] = {}
    for path in sorted(raw_directory.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        platform = raw["platform"]
        if platform["resolution_status"] != "resolved":
            unresolved.append(platform["name"])
            continue
        source_qid = platform["wikidata_id"]
        platform_names[source_qid] = platform["name"]
        for binding in raw["games_response"].get("results", {}).get("bindings", []):
            uri = binding.get("game", {}).get("value", "")
            qid = uri.rsplit("/", 1)[-1]
            title = binding.get("gameLabel", {}).get("value", "").strip()
            if not qid.startswith("Q") or not title or title == qid:
                continue
            platform_qids = sorted(
                set(binding.get("platformQids", {}).get("value", "").split("|")) - {""}
            )
            date = binding.get("firstDate", {}).get("value")
            year = int(date[:4]) if date and date[:4].isdigit() else None
            record = merged.setdefault(
                qid,
                {
                    "record_type": "legacy_candidate",
                    "wikidata_id": qid,
                    "canonical_title": title,
                    "normalized_title": normalize_name(title),
                    "source_platforms": [],
                    "source_platform_names": [],
                    "platform_qids": platform_qids,
                    "first_release_year": year,
                    "source": "wikidata",
                },
            )
            if source_qid not in record["source_platforms"]:
                record["source_platforms"].append(source_qid)
            source_name = platform_names[source_qid]
            if source_name not in record["source_platform_names"]:
                record["source_platform_names"].append(source_name)

    pc_qids = set(policy["pc_platform_qids"])
    counts = {
        "candidates": 0,
        "ported": 0,
        "too_recent": 0,
        "unresolved_platforms": len(unresolved),
    }
    for record in merged.values():
        platforms = set(record["platform_qids"])
        if record["first_release_year"] is not None and record["first_release_year"] > cutoff:
            status = "too_recent"
        elif platforms & pc_qids:
            status = "ported_to_pc"
        elif len(platforms) > 1:
            status = "ported_to_other_platform"
        else:
            status = "candidate_stranded"
        record["classification"] = status
        record["rule_version"] = policy["rule_version"]
        counts[
            "candidates"
            if status == "candidate_stranded"
            else "too_recent"
            if status == "too_recent"
            else "ported"
        ] += 1
        record["source_platforms"].sort()
        record["source_platform_names"].sort()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "".join(
            json.dumps(x, ensure_ascii=False, sort_keys=True) + "\n"
            for x in sorted(
                merged.values(), key=lambda x: (x["normalized_title"], x["wikidata_id"])
            )
        ),
        encoding="utf-8",
    )
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        json.dumps(
            {"counts": counts, "unresolved_platforms": unresolved}, ensure_ascii=False, indent=2
        ),
        encoding="utf-8",
    )
    return counts
