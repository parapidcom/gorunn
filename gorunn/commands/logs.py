import click
import subprocess
import yaml
from gorunn.config import sys_directory, config_file, load_config
from gorunn.helpers import check_docker
from gorunn.classes.app_validator import AppValidator
from gorunn.translations import *

@click.command()
@click.option('--follow', is_flag=True, help="Follow log output.")
@click.option('--app', help="Specify application to stream its logs, or omit to stream all logs from the stack.", callback=AppValidator().validate_app_callback)

def logs(follow, app):
    """Stream logs from applications."""
    check_docker()
    try:
        config = load_config()
        stack_name = config['stack_name']
    except:
        click.echo(click.style(NOT_SET_UP, fg='red'))
        click.Abort()
    command = ['docker', 'compose', 'logs']
    if follow:
        command.append('--follow')
    if app:
        command.append(f"{stack_name}-{app}")

    try:
        click.echo("Fetching logs from Docker Compose services...")
        subprocess.run(command, cwd=sys_directory)
    except subprocess.CalledProcessError as e:
        click.echo(click.style(f"Failed to fetch logs: {e}", fg='red'))
    return


if __name__ == "__main__":
    logs()
