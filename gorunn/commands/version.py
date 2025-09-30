import click
from gorunn import __version__

@click.command()
def version():
    """Display the current version of the CLI."""
    click.echo(f"version: {__version__}")
