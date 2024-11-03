import click
import subprocess
import yaml
from gorunn.config import sys_directory, load_config
from gorunn.helpers import check_docker
from gorunn.classes.app_validator import AppValidator
from gorunn.translations import *


@click.command()
@click.option('--app', help='Specify one or more applications to start, separated by commas.', default=None,
              callback=AppValidator().validate_app_callback)
def stop(app):
    """
    Stop services.
    """
    check_docker()
    try:
        config = load_config()
        stack_name = config['stack_name']
    except:
        click.echo(click.style(NOT_SET_UP, fg='red'))
        click.Abort()
    command = ['docker', 'compose', 'stop']

    if app:
        command.append(f"{stack_name}-{app}")

    try:
        subprocess.run(command, check=True, cwd=sys_directory)
        if app:
            click.echo(click.style(f"{app} has stopped successfully.", fg='green'))
        else:
            click.echo(click.style(f"{stack_name} services stack has stopped successfully.", fg='green'))
    except subprocess.CalledProcessError as e:
        if app:
            click.echo(f"Failed to stop {app}: {e}", err=True)
        else:
            click.echo(f"Failed to stop stack: {e}", err=True)


