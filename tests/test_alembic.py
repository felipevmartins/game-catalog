from pathlib import Path

from alembic import command
from alembic.config import Config


def test_alembic_upgrade_head_on_real_sqlite_file(tmp_path: Path) -> None:
    config = Config("alembic.ini")
    database = tmp_path / "migration.db"
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database}")

    command.upgrade(config, "head")

    assert database.exists()
