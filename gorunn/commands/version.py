# src/cli.py
import click
from gorunn import __version__  # Adjust the import based on your package structure

@click.group()
def cli():
    """A CLI tool to manage local environments."""
    pass

@cli.command()
def version():
    """Display the current version of the CLI."""
    click.echo(f"version: {__version__}")

# Add other CLI commands
# ...

if __name__ == '__main__':
    cli()
