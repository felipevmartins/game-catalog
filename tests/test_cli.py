from pathlib import Path

from typer.testing import CliRunner

from game_catalog.cli import app

runner = CliRunner()


def test_version_command() -> None:
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert result.stdout.strip() == "0.1.0"


def test_initialize_add_and_list_game(tmp_path: Path) -> None:
    database = tmp_path / "catalog.db"
    init = runner.invoke(app, ["--database", str(database), "db", "init"])
    assert init.exit_code == 0
    assert database.exists()

    added = runner.invoke(app, ["--database", str(database), "game", "add", "Pokémon Red"])
    assert added.exit_code == 0
    assert "Created game" in added.stdout

    listed = runner.invoke(app, ["--database", str(database), "game", "list"])
    assert listed.exit_code == 0
    assert "Pokémon Red" in listed.stdout


def test_game_commands_require_initialized_database(tmp_path: Path) -> None:
    result = runner.invoke(app, ["--database", str(tmp_path / "missing.db"), "game", "list"])
    assert result.exit_code != 0
    assert "db init" in result.output
