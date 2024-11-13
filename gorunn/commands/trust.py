import os
import subprocess
import click
import shutil
from pathlib import Path
from gorunn.config import template_directory

def is_root():
    return os.geteuid() == 0

def has_sudo():
    return shutil.which('sudo') is not None

def run_with_privileges(command):
    """Run command with sudo if available and needed"""
    if not is_root() and has_sudo():
        return ['sudo'] + command
    return command

@click.command()
@click.pass_context
def trust(ctx):
    """Add the self-signed certificate to the system's trusted store."""
    cert_path = template_directory / "mounts/proxy/certs/self/gorunn.crt"

    # Check if certificate file exists
    if not cert_path.exists():
        click.echo(click.style(f"Certificate file not found: {cert_path}", fg="red"))
        raise click.Abort()

    # Detect operating system
    os_type = os.name
    if os_type == 'posix':
        if 'darwin' in os.uname().sysname.lower():  # macOS
            keychain_path = Path.home() / "Library/Keychains/login.keychain-db"
            command = [
                "security",
                "add-trusted-cert",
                "-r", "trustRoot",
                "-k", str(keychain_path),
                str(cert_path)
            ]
        elif 'linux' in os.uname().sysname.lower():  # Linux
            try:
                with open("/etc/os-release") as f:
                    release_info = f.read()
            except FileNotFoundError:
                click.echo(click.style("Linux distribution not supported or /etc/os-release missing", fg="red"))
                raise click.Abort()

            if 'ubuntu' in release_info.lower() or 'debian' in release_info.lower():
                # For Debian/Ubuntu
                base_command = [
                    "cp", str(cert_path),
                    "/usr/local/share/ca-certificates/"
                ]
                command = run_with_privileges(base_command)
                subprocess.run(command, check=True)
                command = run_with_privileges(["update-ca-certificates"])
            elif 'fedora' in release_info.lower() or 'centos' in release_info.lower() or 'rhel' in release_info.lower():
                # For Fedora/CentOS/RHEL
                base_command = [
                    "cp", str(cert_path),
                    "/etc/pki/ca-trust/source/anchors/"
                ]
                command = run_with_privileges(base_command)
                subprocess.run(command, check=True)
                command = run_with_privileges(["update-ca-trust"])
            else:
                click.echo(click.style("Linux distribution not recognized.", fg="red"))
                raise click.Abort()
    else:
        click.echo(click.style("Unsupported OS", fg="red"))
        raise click.Abort()

    # Execute the command
    try:
        subprocess.run(command, check=True)
        click.echo(click.style("Certificate added to the system's trusted store successfully.", fg="green"))
    except subprocess.CalledProcessError as e:
        click.echo(click.style(f"Failed to add certificate: {e}", fg="red"))
        raise click.Abort()


if __name__ == "__main__":
    trust()
