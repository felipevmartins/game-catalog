"""Idempotent application of normalized franchise and game discovery records."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from game_catalog import __version__
from game_catalog.application.identity import normalize_name
from game_catalog.application.unit_of_work import UnitOfWork
from game_catalog.domain.identifiers import new_uuid7
from game_catalog.persistence.models import (
    Ecosystem,
    ExecutionRun,
    Franchise,
    FranchiseEcosystem,
    FranchiseExternalId,
    Game,
    GameEdition,
    GameExternalId,
    RecordSourceLink,
    ReviewItem,
    Source,
    SourceReference,
)


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


@dataclass
class ImportResult:
    franchises_inserted: int = 0
    games_inserted: int = 0
    external_ids_inserted: int = 0
    links_inserted: int = 0
    reviews_created: int = 0
    skipped: int = 0
    conflicts: int = 0
    dry_run: bool = False

    def to_dict(self) -> dict[str, int | bool]:
        return asdict(self)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if value.get("record_type") not in {"franchise", "game"}:
            raise ValueError(f"unsupported record_type at line {line_number}")
        records.append(value)
    return records


class FranchiseImportService:
    def __init__(self, unit_of_work: Callable[[], UnitOfWork]) -> None:
        self.unit_of_work = unit_of_work

    def apply(self, normalized_file: Path, source_registry: Path, *, dry_run: bool) -> ImportResult:
        records = read_jsonl(normalized_file)
        source_config = json.loads(source_registry.read_text(encoding="utf-8"))["sources"][0]
        result = ImportResult(dry_run=dry_run)
        now = utc_now()
        with self.unit_of_work() as uow:
            session = self._session(uow)
            source = self._source(session, source_config, now)
            reference = self._reference(session, source, normalized_file, now)
            franchises: dict[str, Franchise] = {}
            for record in records:
                if record["record_type"] != "franchise":
                    continue
                franchise = self._franchise(session, record, source, reference, now, result)
                franchises[record["key"]] = franchise
            session.flush()
            for record in records:
                if record["record_type"] == "game":
                    game_franchise = franchises.get(record["franchise_key"])
                    if game_franchise is None:
                        result.conflicts += 1
                        continue
                    self._game(session, record, game_franchise, source, reference, now, result)
            if dry_run:
                uow.rollback()
            else:
                run = ExecutionRun(
                    id=str(new_uuid7()),
                    execution_type="import",
                    status="succeeded_with_warnings" if result.conflicts else "succeeded",
                    requested_by="cli",
                    dry_run=False,
                    parameters_json=json.dumps({"file": normalized_file.name}),
                    application_version=__version__,
                    schema_version="0009_seed_reference_data",
                    started_at=now,
                    heartbeat_at=now,
                    finished_at=now,
                    summary_json=json.dumps(result.to_dict()),
                    created_at=now,
                )
                session.add(run)
                uow.commit()
        return result

    @staticmethod
    def _session(uow: UnitOfWork) -> Session:
        if uow.session is None:
            raise RuntimeError("UnitOfWork is not active")
        return uow.session

    @staticmethod
    def _source(session: Session, config: dict[str, Any], now: str) -> Source:
        source = session.scalar(select(Source).where(Source.code == config["code"]))
        if source is not None:
            return source
        source = Source(
            id=str(new_uuid7()),
            code=config["code"],
            name=config["name"],
            source_type=config["source_type"],
            integration_type=config["integration_type"],
            base_url=config["base_url"],
            priority=config["priority"],
            default_confidence=config["default_confidence"],
            enabled=config["enabled"],
            credential_required=False,
            terms_url=config["terms_url"],
            terms_reviewed_at=config["terms_reviewed_at"],
            contract_version=config["contract_version"],
            license_name=config["license_name"],
            redistribution_policy=config["redistribution_policy"],
            created_at=now,
            updated_at=now,
        )
        session.add(source)
        session.flush()
        return source

    @staticmethod
    def _reference(session: Session, source: Source, path: Path, now: str) -> SourceReference:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        existing = session.scalar(
            select(SourceReference).where(
                SourceReference.source_id == source.id,
                SourceReference.content_hash == digest,
            )
        )
        if existing is not None:
            return existing
        reference = SourceReference(
            id=str(new_uuid7()),
            source_id=source.id,
            source_record_id=path.name,
            retrieved_at=now,
            verified_at=now,
            content_hash=digest,
            source_contract_version=source.contract_version,
            created_at=now,
        )
        session.add(reference)
        session.flush()
        return reference

    def _franchise(
        self,
        session: Session,
        record: dict[str, Any],
        source: Source,
        reference: SourceReference,
        now: str,
        result: ImportResult,
    ) -> Franchise:
        normalized = normalize_name(record["canonical_name"])
        franchise = session.scalar(
            select(Franchise).where(
                Franchise.normalized_name == normalized,
                Franchise.parent_franchise_id.is_(None),
                Franchise.deleted_at.is_(None),
            )
        )
        if franchise is None:
            franchise = Franchise(
                id=str(new_uuid7()),
                name=record["canonical_name"],
                normalized_name=normalized,
                status="unknown",
                official_end_confirmed=False,
                created_at=now,
                updated_at=now,
            )
            session.add(franchise)
            session.flush()
            result.franchises_inserted += 1
        else:
            result.skipped += 1
        ecosystem = self._ecosystem(session, record["ecosystem"], now)
        association = session.scalar(
            select(FranchiseEcosystem).where(
                FranchiseEcosystem.franchise_id == franchise.id,
                FranchiseEcosystem.ecosystem_id == ecosystem.id,
                FranchiseEcosystem.association_type == "strong_association",
            )
        )
        if association is None:
            session.add(
                FranchiseEcosystem(
                    id=str(new_uuid7()),
                    franchise_id=franchise.id,
                    ecosystem_id=ecosystem.id,
                    association_type="strong_association",
                    notes="Initial editorial import",
                )
            )
        qid = record.get("wikidata_id")
        if qid and record["resolution_status"] == "resolved":
            result.external_ids_inserted += self._franchise_external_id(
                session, franchise, source, qid, now
            )
            self._close_identity_reviews(session, franchise.id, now)
        else:
            result.reviews_created += self._review(
                session,
                franchise.id,
                f"wikidata_franchise_{record['resolution_status']}",
                record,
                reference,
                now,
            )
        result.links_inserted += self._link(session, "franchise", franchise.id, reference, now)
        return franchise

    @staticmethod
    def _close_identity_reviews(session: Session, franchise_id: str, now: str) -> None:
        reviews = session.scalars(
            select(ReviewItem).where(
                ReviewItem.entity_type == "franchise",
                ReviewItem.entity_id == franchise_id,
                ReviewItem.reason.in_(
                    ("wikidata_franchise_ambiguous", "wikidata_franchise_unresolved")
                ),
                ReviewItem.status.in_(("pending", "deferred")),
            )
        )
        for review in reviews:
            review.status = "cancelled"
            review.reviewed_at = now
            review.reviewed_by = "system"
            review.review_notes = "Resolved by a newer deterministic discovery rule."

    @staticmethod
    def _ecosystem(session: Session, key: str, now: str) -> Ecosystem:
        normalized = normalize_name(key)
        ecosystem = session.scalar(
            select(Ecosystem).where(
                Ecosystem.normalized_name == normalized, Ecosystem.deleted_at.is_(None)
            )
        )
        if ecosystem is not None:
            return ecosystem
        ecosystem = Ecosystem(
            id=str(new_uuid7()),
            name=key.title(),
            normalized_name=normalized,
            ecosystem_type="console_family",
            created_at=now,
            updated_at=now,
        )
        session.add(ecosystem)
        session.flush()
        return ecosystem

    def _game(
        self,
        session: Session,
        record: dict[str, Any],
        franchise: Franchise,
        source: Source,
        reference: SourceReference,
        now: str,
        result: ImportResult,
    ) -> None:
        external = session.scalar(
            select(GameExternalId).where(
                GameExternalId.source_id == source.id,
                GameExternalId.external_id == record["wikidata_id"],
                GameExternalId.context == "global",
            )
        )
        game = session.get(Game, external.game_id) if external is not None else None
        if game is None:
            game = Game(
                id=str(new_uuid7()),
                canonical_title=record["canonical_title"],
                normalized_title=record["normalized_title"],
                franchise_id=franchise.id,
                game_type="main",
                campaign_focus="primary",
                online_only=False,
                regional_only=False,
                historically_relevant=False,
                collector_relevant=False,
                created_at=now,
                updated_at=now,
            )
            session.add(game)
            session.flush()
            session.add(
                GameEdition(
                    id=str(new_uuid7()),
                    game_id=game.id,
                    identity_discriminator="original",
                    name="Original",
                    normalized_name="original",
                    edition_type="original",
                    is_definitive=False,
                    created_at=now,
                    updated_at=now,
                )
            )
            result.games_inserted += 1
        elif game.franchise_id not in (None, franchise.id):
            result.conflicts += 1
            result.reviews_created += self._review(
                session,
                game.id,
                "wikidata_game_franchise_conflict",
                record,
                reference,
                now,
                entity_type="game",
            )
            return
        elif game.franchise_id is None:
            game.franchise_id = franchise.id
        else:
            result.skipped += 1
        if external is None:
            session.add(
                GameExternalId(
                    id=str(new_uuid7()),
                    game_id=game.id,
                    source_id=source.id,
                    external_id=record["wikidata_id"],
                    context="global",
                    is_primary=True,
                    created_at=now,
                    updated_at=now,
                )
            )
            result.external_ids_inserted += 1
        result.links_inserted += self._link(session, "game", game.id, reference, now)

    @staticmethod
    def _franchise_external_id(
        session: Session, franchise: Franchise, source: Source, qid: str, now: str
    ) -> int:
        existing = session.scalar(
            select(FranchiseExternalId).where(
                FranchiseExternalId.source_id == source.id,
                FranchiseExternalId.external_id == qid,
                FranchiseExternalId.context == "global",
            )
        )
        if existing is not None:
            return 0
        session.add(
            FranchiseExternalId(
                id=str(new_uuid7()),
                franchise_id=franchise.id,
                source_id=source.id,
                external_id=qid,
                context="global",
                is_primary=True,
                created_at=now,
                updated_at=now,
            )
        )
        return 1

    @staticmethod
    def _link(
        session: Session,
        entity_type: str,
        entity_id: str,
        reference: SourceReference,
        now: str,
    ) -> int:
        existing = session.scalar(
            select(RecordSourceLink).where(
                RecordSourceLink.entity_type == entity_type,
                RecordSourceLink.entity_id == entity_id,
                RecordSourceLink.source_reference_id == reference.id,
                RecordSourceLink.link_role == "supporting",
            )
        )
        if existing is not None:
            return 0
        session.add(
            RecordSourceLink(
                id=str(new_uuid7()),
                entity_type=entity_type,
                entity_id=entity_id,
                source_reference_id=reference.id,
                link_role="supporting",
                created_at=now,
            )
        )
        return 1

    @staticmethod
    def _review(
        session: Session,
        entity_id: str,
        reason: str,
        candidate: dict[str, Any],
        reference: SourceReference,
        now: str,
        *,
        entity_type: str = "franchise",
    ) -> int:
        key = f"{reason}:{entity_id}"
        existing = session.scalar(
            select(ReviewItem).where(
                ReviewItem.deduplication_key == key,
                ReviewItem.status.in_(("pending", "deferred")),
            )
        )
        if existing is not None:
            return 0
        session.add(
            ReviewItem(
                id=str(new_uuid7()),
                entity_type=entity_type,
                entity_id=entity_id,
                candidate_value_json=json.dumps(candidate, ensure_ascii=False),
                reason=reason,
                source_reference_id=reference.id,
                priority="normal",
                status="pending",
                deduplication_key=key,
                created_at=now,
            )
        )
        return 1
