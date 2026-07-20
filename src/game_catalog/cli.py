"""Command-line interface entry point."""

import typer

app = typer.Typer(no_args_is_help=True)


@app.callback()
def main() -> None:
    """Manage the local game catalog."""


@app.command()
def version() -> None:
    """Show the application version."""
    from game_catalog import __version__

    typer.echo(__version__)
