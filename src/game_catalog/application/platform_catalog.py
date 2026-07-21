"""Idempotent synchronization of the curated first-party platform catalog."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from game_catalog import __version__
from game_catalog.application.franchise_import import utc_now
from game_catalog.application.identity import normalize_name
from game_catalog.application.unit_of_work import UnitOfWork
from game_catalog.domain.identifiers import new_uuid7
from game_catalog.persistence.models import (
    Ecosystem,
    ExecutionRun,
    Manufacturer,
    Platform,
    RecordSourceLink,
    Source,
    SourceReference,
)


@dataclass
class PlatformSyncResult:
    manufacturers_inserted: int = 0
    ecosystems_inserted: int = 0
    platforms_inserted: int = 0
    records_updated: int = 0
    links_inserted: int = 0
    skipped: int = 0
    dry_run: bool = False

    def to_dict(self) -> dict[str, int | bool]:
        return asdict(self)


class PlatformCatalogService:
    def __init__(self, unit_of_work: Callable[[], UnitOfWork]) -> None:
        self.unit_of_work = unit_of_work

    def sync(self, catalog_file: Path, *, dry_run: bool) -> PlatformSyncResult:
        payload = json.loads(catalog_file.read_text(encoding="utf-8"))
        result = PlatformSyncResult(dry_run=dry_run)
        now = utc_now()
        with self.unit_of_work() as uow:
            if uow.session is None:
                raise RuntimeError("UnitOfWork is not active")
            session = uow.session
            manufacturers = {
                item["key"]: self._manufacturer(session, item, now, result)
                for item in payload["manufacturers"]
            }
            ecosystems = {
                item["key"]: self._ecosystem(
                    session, item, manufacturers[item["manufacturer"]], now, result
                )
                for item in payload["ecosystems"]
            }
            sources = {
                item["code"]: self._source_reference(session, item, now)
                for item in payload["sources"]
            }
            for item in payload["platforms"]:
                platform = self._platform(
                    session,
                    item,
                    manufacturers[item["manufacturer"]],
                    ecosystems[item["ecosystem"]],
                    now,
                    result,
                )
                result.links_inserted += self._link(
                    session, platform.id, sources[item["source"]], now
                )
            if dry_run:
                uow.rollback()
            else:
                session.add(
                    ExecutionRun(
                        id=str(new_uuid7()),
                        execution_type="import",
                        status="succeeded",
                        requested_by="cli",
                        dry_run=False,
                        parameters_json=json.dumps({"file": catalog_file.name}),
                        application_version=__version__,
                        schema_version="0009_seed_reference_data",
                        started_at=now,
                        heartbeat_at=now,
                        finished_at=now,
                        summary_json=json.dumps(result.to_dict()),
                        created_at=now,
                    )
                )
                uow.commit()
        return result

    @staticmethod
    def _manufacturer(
        session: Session,
        item: dict[str, Any],
        now: str,
        result: PlatformSyncResult,
    ) -> Manufacturer:
        normalized = normalize_name(item["name"])
        record = session.scalar(
            select(Manufacturer).where(
                Manufacturer.normalized_name == normalized, Manufacturer.deleted_at.is_(None)
            )
        )
        if record is None:
            record = Manufacturer(
                id=str(new_uuid7()),
                name=item["name"],
                normalized_name=normalized,
                country_code=item["country_code"],
                created_at=now,
                updated_at=now,
            )
            session.add(record)
            session.flush()
            result.manufacturers_inserted += 1
        elif record.name != item["name"] or record.country_code != item["country_code"]:
            record.name = item["name"]
            record.country_code = item["country_code"]
            record.updated_at = now
            result.records_updated += 1
        else:
            result.skipped += 1
        return record

    @staticmethod
    def _ecosystem(
        session: Session,
        item: dict[str, Any],
        manufacturer: Manufacturer,
        now: str,
        result: PlatformSyncResult,
    ) -> Ecosystem:
        normalized = normalize_name(item["name"])
        record = session.scalar(
            select(Ecosystem).where(
                Ecosystem.normalized_name == normalized, Ecosystem.deleted_at.is_(None)
            )
        )
        if record is None:
            record = Ecosystem(
                id=str(new_uuid7()),
                name=item["name"],
                normalized_name=normalized,
                manufacturer_id=manufacturer.id,
                ecosystem_type="console_family",
                created_at=now,
                updated_at=now,
            )
            session.add(record)
            session.flush()
            result.ecosystems_inserted += 1
        elif record.manufacturer_id != manufacturer.id:
            record.manufacturer_id = manufacturer.id
            record.updated_at = now
            result.records_updated += 1
        else:
            result.skipped += 1
        return record

    @staticmethod
    def _platform(
        session: Session,
        item: dict[str, Any],
        manufacturer: Manufacturer,
        ecosystem: Ecosystem,
        now: str,
        result: PlatformSyncResult,
    ) -> Platform:
        normalized = normalize_name(item["name"])
        record = session.scalar(
            select(Platform).where(
                Platform.normalized_name == normalized, Platform.deleted_at.is_(None)
            )
        )
        values = (
            manufacturer.id,
            ecosystem.id,
            item["platform_type"],
            item["release_year"],
        )
        if record is None:
            record = Platform(
                id=str(new_uuid7()),
                name=item["name"],
                normalized_name=normalized,
                manufacturer_id=values[0],
                ecosystem_id=values[1],
                platform_type=values[2],
                release_year=values[3],
                created_at=now,
                updated_at=now,
            )
            session.add(record)
            session.flush()
            result.platforms_inserted += 1
        elif (
            record.manufacturer_id,
            record.ecosystem_id,
            record.platform_type,
            record.release_year,
        ) != values:
            record.name = item["name"]
            record.manufacturer_id = values[0]
            record.ecosystem_id = values[1]
            record.platform_type = values[2]
            record.release_year = values[3]
            record.updated_at = now
            result.records_updated += 1
        else:
            result.skipped += 1
        return record

    @staticmethod
    def _source_reference(session: Session, item: dict[str, Any], now: str) -> SourceReference:
        source = session.scalar(select(Source).where(Source.code == item["code"]))
        if source is None:
            source = Source(
                id=str(new_uuid7()),
                code=item["code"],
                name=item["name"],
                source_type="official",
                integration_type="none",
                base_url=item["url"],
                priority=90,
                default_confidence="high",
                enabled=True,
                credential_required=False,
                terms_url=item["url"],
                terms_reviewed_at="2026-07-20T00:00:00.000Z",
                contract_version="platform-history-2026-07",
                redistribution_policy="unknown",
                created_at=now,
                updated_at=now,
            )
            session.add(source)
            session.flush()
        reference = session.scalar(
            select(SourceReference).where(
                SourceReference.source_id == source.id,
                SourceReference.source_url == item["url"],
            )
        )
        if reference is None:
            reference = SourceReference(
                id=str(new_uuid7()),
                source_id=source.id,
                source_url=item["url"],
                retrieved_at=now,
                verified_at=now,
                source_contract_version=source.contract_version,
                created_at=now,
            )
            session.add(reference)
            session.flush()
        return reference

    @staticmethod
    def _link(session: Session, platform_id: str, reference: SourceReference, now: str) -> int:
        existing = session.scalar(
            select(RecordSourceLink).where(
                RecordSourceLink.entity_type == "platform",
                RecordSourceLink.entity_id == platform_id,
                RecordSourceLink.source_reference_id == reference.id,
                RecordSourceLink.link_role == "supporting",
            )
        )
        if existing is not None:
            return 0
        session.add(
            RecordSourceLink(
                id=str(new_uuid7()),
                entity_type="platform",
                entity_id=platform_id,
                source_reference_id=reference.id,
                link_role="supporting",
                created_at=now,
            )
        )
        return 1
