import subprocess
import click
from pathlib import Path
from gorunn.config import template_directory

@click.command()
@click.pass_context
def trust(ctx):
    """Add the self-signed certificate to the Apple keychain."""
    cert_path = template_directory / "mounts/proxy/certs/self/gorunn.crt"
    keychain_path = Path.home() / "Library/Keychains/login.keychain-db"

    if not cert_path.exists():
        click.echo(cert_path)
        click.echo(click.style("Certificate file not found.", fg="red"))
        raise click.Abort()

    # Build the command to add the certificate to the keychain
    command = [
        "security",
        "add-trusted-cert",
        "-r", "trustRoot",
        "-k", str(keychain_path),
        str(cert_path)
    ]

    try:
        # Execute the command
        subprocess.run(command, check=True)
        click.echo(click.style("Certificate added to the keychain successfully.", fg="green"))
    except subprocess.CalledProcessError as e:
        click.echo(click.style(f"Failed to add certificate: {e}", fg="red"))
        raise click.Abort()

if __name__ == "__main__":
    trust()
