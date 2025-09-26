import click
import re
from pathlib import Path

@click.command()
def version():
    """Display the current version of the CLI."""
    # Read version from pyproject.toml
    pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"

    try:
        with open(pyproject_path, 'r') as f:
            content = f.read()
            # Simple regex to extract version from pyproject.toml
            match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                version = match.group(1)
                click.echo(f"version: {version}")
            else:
                click.echo("Error: Could not find version in pyproject.toml", err=True)
    except FileNotFoundError:
        click.echo("Error: pyproject.toml not found", err=True)
