import click
import subprocess
import yaml
from pathlib import Path
from gorunn.config import sys_directory, load_config
from gorunn.helpers import check_docker, get_all_services
from gorunn.classes.app_validator import AppValidator
from gorunn.translations import *


@click.command()
@click.option('--app', help="Specify one or more application to restart.", callback=AppValidator().validate_app_callback)
def restart(app, include_services=True):
    """Restart services."""
    services = get_all_services()
    app_list = []
    check_docker()
    try:
        config = load_config()
        stack_name = config['stack_name']
    except:
        click.echo(click.style(NOT_SET_UP, fg='red'))
        click.Abort()

    if app:
        prefixed_name = f"{stack_name}-{app}"
        if prefixed_name in services:
            app_list.append(prefixed_name)
        else:
            click.echo(click.style(f"Service {prefixed_name} is not part of {stack_name} stack!", fg='red'))
            raise click.Abort()

    command = ['docker', 'compose', 'restart']
    command.extend(app_list)

    try:
        click.echo(f"Restarting services: {', '.join(app_list) if app_list else 'all services'}...")
        subprocess.run(command, cwd=sys_directory, check=True)
        click.echo(click.style("Services restarted successfully.", fg='green'))
    except subprocess.CalledProcessError as e:
        click.echo(click.style(f"Failed to restart services: {e}", fg='red'))


if __name__ == "__main__":
    restart()
