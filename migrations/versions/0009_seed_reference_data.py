"""Seed the minimum deterministic reference vocabulary.

Revision ID: 0009_seed_reference_data
Revises: 0008_incremental_operations
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009_seed_reference_data"
down_revision: str | None = "0008_incremental_operations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NOW = "2026-07-20T00:00:00.000Z"
IDS = {
    "region_world": "018f0000-0000-7000-8000-000000000001",
    "region_jp": "018f0000-0000-7000-8000-000000000002",
    "region_na": "018f0000-0000-7000-8000-000000000003",
    "ecosystem_nintendo": "018f0000-0000-7000-8000-000000000010",
    "ecosystem_playstation": "018f0000-0000-7000-8000-000000000011",
    "platform_snes": "018f0000-0000-7000-8000-000000000020",
    "platform_ps1": "018f0000-0000-7000-8000-000000000021",
    "platform_ds": "018f0000-0000-7000-8000-000000000022",
    "platform_ps5": "018f0000-0000-7000-8000-000000000023",
    "source_manual": "018f0000-0000-7000-8000-000000000030",
    "lock_unavailable": "018f0000-0000-7000-8000-000000000040",
    "lock_hardware": "018f0000-0000-7000-8000-000000000041",
    "lock_online": "018f0000-0000-7000-8000-000000000042",
    "lock_content": "018f0000-0000-7000-8000-000000000043",
}


def execute(statement: str, values: dict[str, object]) -> None:
    op.get_bind().execute(sa.text(statement), values)


def upgrade() -> None:
    for key, code, name, kind in (
        ("region_world", "WORLD", "World", "global"),
        ("region_jp", "JP", "Japan", "country"),
        ("region_na", "NA", "North America", "market"),
    ):
        execute(
            "INSERT INTO regions (id,code,name,region_type,active,created_at,updated_at) VALUES (:id,:code,:name,:kind,1,:now,:now) ON CONFLICT(code) DO UPDATE SET name=excluded.name,region_type=excluded.region_type,active=1,updated_at=excluded.updated_at",
            {"id": IDS[key], "code": code, "name": name, "kind": kind, "now": NOW},
        )
    for key, name, normalized in (
        ("ecosystem_nintendo", "Nintendo", "nintendo"),
        ("ecosystem_playstation", "PlayStation", "playstation"),
    ):
        execute(
            "INSERT INTO ecosystems (id,name,normalized_name,ecosystem_type,created_at,updated_at) VALUES (:id,:name,:normalized,'console_family',:now,:now) ON CONFLICT(normalized_name) WHERE deleted_at IS NULL DO UPDATE SET name=excluded.name,updated_at=excluded.updated_at",
            {"id": IDS[key], "name": name, "normalized": normalized, "now": NOW},
        )
    for key, ecosystem, name, normalized, kind, year in (
        (
            "platform_snes",
            "ecosystem_nintendo",
            "Super Nintendo Entertainment System",
            "super nintendo entertainment system",
            "home_console",
            1990,
        ),
        (
            "platform_ps1",
            "ecosystem_playstation",
            "PlayStation",
            "playstation",
            "home_console",
            1994,
        ),
        (
            "platform_ds",
            "ecosystem_nintendo",
            "Nintendo DS",
            "nintendo ds",
            "portable_console",
            2004,
        ),
        (
            "platform_ps5",
            "ecosystem_playstation",
            "PlayStation 5",
            "playstation 5",
            "home_console",
            2020,
        ),
    ):
        execute(
            "INSERT INTO platforms (id,name,normalized_name,ecosystem_id,platform_type,release_year,created_at,updated_at) VALUES (:id,:name,:normalized,:ecosystem,:kind,:year,:now,:now) ON CONFLICT(normalized_name) WHERE deleted_at IS NULL DO UPDATE SET name=excluded.name,ecosystem_id=excluded.ecosystem_id,platform_type=excluded.platform_type,release_year=excluded.release_year,updated_at=excluded.updated_at",
            {
                "id": IDS[key],
                "name": name,
                "normalized": normalized,
                "ecosystem": IDS[ecosystem],
                "kind": kind,
                "year": year,
                "now": NOW,
            },
        )
    execute(
        "INSERT INTO sources (id,code,name,source_type,integration_type,priority,default_confidence,enabled,credential_required,redistribution_policy,created_at,updated_at) VALUES (:id,'manual','Manual entry','manual','manual',100,'high',1,0,'allowed',:now,:now) ON CONFLICT(code) DO UPDATE SET name=excluded.name,priority=excluded.priority,enabled=1,updated_at=excluded.updated_at",
        {"id": IDS["source_manual"], "now": NOW},
    )
    for key, code, name, description in (
        (
            "lock_unavailable",
            "official_unavailability",
            "Official unavailability",
            "No current official release is available.",
        ),
        (
            "lock_hardware",
            "legacy_hardware_required",
            "Legacy hardware required",
            "Official play requires legacy hardware.",
        ),
        (
            "lock_online",
            "online_dependency",
            "Online dependency",
            "Required online service is unavailable or restricted.",
        ),
        (
            "lock_content",
            "content_loss",
            "Content loss",
            "Current official access omits relevant original content.",
        ),
    ):
        execute(
            "INSERT INTO platform_lock_reasons (id,code,name,description,active) VALUES (:id,:code,:name,:description,1) ON CONFLICT(code) DO UPDATE SET name=excluded.name,description=excluded.description,active=1",
            {"id": IDS[key], "code": code, "name": name, "description": description},
        )
    op.execute(
        "UPDATE schema_metadata SET schema_version='0009_seed_reference_data', updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=1"
    )


def downgrade() -> None:
    # Referenced seeds are intentionally preserved; SQLite RESTRICT remains authoritative.
    op.execute(
        "DELETE FROM platform_lock_reasons WHERE id IN ('018f0000-0000-7000-8000-000000000040','018f0000-0000-7000-8000-000000000041','018f0000-0000-7000-8000-000000000042','018f0000-0000-7000-8000-000000000043') AND NOT EXISTS (SELECT 1 FROM game_platform_lock_reasons WHERE reason_id=platform_lock_reasons.id)"
    )
    op.execute(
        "DELETE FROM sources WHERE id='018f0000-0000-7000-8000-000000000030' AND NOT EXISTS (SELECT 1 FROM source_references WHERE source_id=sources.id)"
    )
    op.execute(
        "DELETE FROM platforms WHERE id IN ('018f0000-0000-7000-8000-000000000020','018f0000-0000-7000-8000-000000000021','018f0000-0000-7000-8000-000000000022','018f0000-0000-7000-8000-000000000023') AND NOT EXISTS (SELECT 1 FROM releases WHERE platform_id=platforms.id) AND NOT EXISTS (SELECT 1 FROM hardware_models WHERE platform_id=platforms.id)"
    )
    op.execute(
        "DELETE FROM ecosystems WHERE id IN ('018f0000-0000-7000-8000-000000000010','018f0000-0000-7000-8000-000000000011') AND NOT EXISTS (SELECT 1 FROM platforms WHERE ecosystem_id=ecosystems.id)"
    )
    op.execute(
        "DELETE FROM regions WHERE id IN ('018f0000-0000-7000-8000-000000000001','018f0000-0000-7000-8000-000000000002','018f0000-0000-7000-8000-000000000003') AND NOT EXISTS (SELECT 1 FROM releases WHERE region_id=regions.id)"
    )
    op.execute(
        "UPDATE schema_metadata SET schema_version='0008_incremental_operations', updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=1"
    )
