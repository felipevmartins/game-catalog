"""Apply conservative legacy-platform candidates to existing catalog games."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path

from sqlalchemy import select

from game_catalog.application.franchise_import import utc_now
from game_catalog.application.unit_of_work import UnitOfWork
from game_catalog.domain.identifiers import new_uuid7
from game_catalog.persistence.models import (
    GameExternalId,
    PlatformLockAssessment,
    ReviewItem,
    Source,
    SourceReference,
)


@dataclass
class LegacyApplyResult:
    matched_games: int = 0
    assessments_created: int = 0
    assessments_updated: int = 0
    reviews_created: int = 0
    catalog_candidates_missing: int = 0
    skipped_non_candidates: int = 0
    assessments_staled: int = 0
    reviews_cancelled: int = 0
    dry_run: bool = False

    def to_dict(self) -> dict[str, int | bool]:
        return asdict(self)


class LegacyImportService:
    def __init__(self, unit_of_work: Callable[[], UnitOfWork]) -> None:
        self.unit_of_work = unit_of_work

    def apply(self, normalized_file: Path, *, dry_run: bool) -> LegacyApplyResult:
        records = [
            json.loads(line)
            for line in normalized_file.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        result = LegacyApplyResult(dry_run=dry_run)
        now = utc_now()
        input_version = hashlib.sha256(normalized_file.read_bytes()).hexdigest()
        with self.unit_of_work() as uow:
            if uow.session is None:
                raise RuntimeError("UnitOfWork is not active")
            session = uow.session
            source = session.scalar(select(Source).where(Source.code == "wikidata"))
            if source is None:
                raise ValueError("Wikidata source is not initialized")
            reference = session.scalar(
                select(SourceReference).where(
                    SourceReference.source_id == source.id,
                    SourceReference.content_hash == input_version,
                )
            )
            if reference is None:
                reference = SourceReference(
                    id=str(new_uuid7()),
                    source_id=source.id,
                    source_url="https://query.wikidata.org/sparql",
                    retrieved_at=now,
                    content_hash=input_version,
                    source_contract_version=source.contract_version,
                    created_at=now,
                )
                session.add(reference)
                session.flush()
            for record in records:
                if record["classification"] == "excluded_sports":
                    external = session.scalar(
                        select(GameExternalId).where(
                            GameExternalId.source_id == source.id,
                            GameExternalId.external_id == record["wikidata_id"],
                            GameExternalId.context == "global",
                        )
                    )
                    if external is not None:
                        assessment = session.get(PlatformLockAssessment, external.game_id)
                        if (
                            assessment is not None
                            and assessment.rule_version == record["rule_version"]
                        ):
                            assessment.locked = None
                            assessment.severity_level = None
                            assessment.state = "stale"
                            assessment.justification = (
                                "Excluded by editorial preference: sports video game."
                            )
                            assessment.stale_since = now
                            result.assessments_staled += 1
                        reviews = session.scalars(
                            select(ReviewItem).where(
                                ReviewItem.entity_type == "game",
                                ReviewItem.entity_id == external.game_id,
                                ReviewItem.reason == "legacy_platform_confirmation",
                                ReviewItem.status.in_(("pending", "deferred")),
                            )
                        )
                        for review in reviews:
                            review.status = "cancelled"
                            review.reviewed_at = now
                            review.reviewed_by = "system"
                            review.review_notes = "Excluded by sports-game editorial policy."
                            result.reviews_cancelled += 1
                    result.skipped_non_candidates += 1
                    continue
                if record["classification"] != "candidate_stranded":
                    result.skipped_non_candidates += 1
                    continue
                external = session.scalar(
                    select(GameExternalId).where(
                        GameExternalId.source_id == source.id,
                        GameExternalId.external_id == record["wikidata_id"],
                        GameExternalId.context == "global",
                    )
                )
                if external is None:
                    result.catalog_candidates_missing += 1
                    continue
                result.matched_games += 1
                assessment = session.get(PlatformLockAssessment, external.game_id)
                justification = (
                    "Single-source candidate: Wikidata lists only the originating console; "
                    "confirmation from another release source is required."
                )
                if assessment is None:
                    assessment = PlatformLockAssessment(
                        game_id=external.game_id,
                        locked=None,
                        severity_level=None,
                        justification=justification,
                        minimum_official_hardware=None,
                        content_lost=False,
                        state="dirty",
                        rule_version=record["rule_version"],
                        input_version=input_version,
                        calculated_at=now,
                        stale_since=None,
                        last_error_redacted=None,
                    )
                    session.add(assessment)
                    result.assessments_created += 1
                else:
                    assessment.locked = None
                    assessment.severity_level = None
                    assessment.justification = justification
                    assessment.state = "dirty"
                    assessment.rule_version = record["rule_version"]
                    assessment.input_version = input_version
                    assessment.calculated_at = now
                    result.assessments_updated += 1
                key = f"legacy_platform_confirmation:{external.game_id}"
                existing = session.scalar(
                    select(ReviewItem).where(
                        ReviewItem.entity_type == "game",
                        ReviewItem.entity_id == external.game_id,
                        ReviewItem.reason == "legacy_platform_confirmation",
                        ReviewItem.status.in_(("pending", "deferred")),
                    )
                )
                if existing is None:
                    session.add(
                        ReviewItem(
                            id=str(new_uuid7()),
                            entity_type="game",
                            entity_id=external.game_id,
                            candidate_value_json=json.dumps(record, ensure_ascii=False),
                            reason="legacy_platform_confirmation",
                            source_reference_id=reference.id,
                            priority="normal",
                            status="pending",
                            deduplication_key=key,
                            created_at=now,
                        )
                    )
                    result.reviews_created += 1
            if dry_run:
                uow.rollback()
            else:
                uow.commit()
        return result
