import importlib
from typing import Annotated, Any

import click
import typer

# Lazy subcommand registry: name -> (module_path, attribute, help_text)
# Help text is duplicated here to avoid importing modules just for --help display.
# When updating a subcommand's help text, update it here too.
_SUBCOMMANDS: dict[str, tuple[str, str, str]] = {
    "project": (
        "ecosia_project.cli",
        "cli",
        "Tools for managing and analysing projects in the monorepo",
    ),
}


class _LazySubcommand(click.Group):
    """Holds help text for display in `arbor --help`; imports the real module on invocation."""

    def __init__(self, *, module_path: str, attr: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._module_path = module_path
        self._attr = attr

    def make_context(
        self,
        info_name: str | None,
        args: list[str],
        parent: click.Context | None = None,
        **extra: Any,
    ) -> click.Context:
        mod = importlib.import_module(self._module_path)
        real_group = typer.main.get_group(getattr(mod, self._attr))
        return real_group.make_context(info_name, args, parent=parent, **extra)


class _LazyTyperGroup(typer.core.TyperGroup):
    """Main group that returns lazy stubs instead of eagerly importing all subcommands."""

    def list_commands(self, ctx: click.Context) -> list[str]:
        return sorted(_SUBCOMMANDS.keys())

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        if cmd_name not in _SUBCOMMANDS:
            return None
        module_path, attr, help_text = _SUBCOMMANDS[cmd_name]
        return _LazySubcommand(name=cmd_name, module_path=module_path, attr=attr, help=help_text)


cli = typer.Typer(
    help="core supertool",
    cls=_LazyTyperGroup,
    context_settings=dict(max_content_width=100),
    no_args_is_help=True,
    rich_markup_mode="markdown",
    # Ensure we don't print secrets in tracebacks
    # https://typer.tiangolo.com/tutorial/exceptions/#exceptions-without-rich
    pretty_exceptions_show_locals=False,
)

@cli.callback()
def main() -> None:
    pass


if __name__ == "__main__":
    cli()
