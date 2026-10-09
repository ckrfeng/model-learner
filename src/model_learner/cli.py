"""Command-line entry point for Model Learner."""

from typing import Annotated

import typer

from model_learner import __version__

app = typer.Typer(
    name="model-learner",
    help="Model Learner: local-first AI-model utility from verified outcomes.",
    no_args_is_help=True,
    invoke_without_command=True,
    add_completion=False,
)


def _show_version(value: bool) -> None:
    if value:
        typer.echo(f"model-learner {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            callback=_show_version,
            is_eager=True,
            help="Show the version and exit.",
        ),
    ] = False,
) -> None:
    """Provide the foundation CLI; milestone commands will be added later."""
