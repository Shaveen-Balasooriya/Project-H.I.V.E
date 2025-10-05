import typer
import subcommands.manager

app = typer.Typer()

app.add_typer(subcommands.manager.app, name="manager")


if __name__ == "__main__":
    app()