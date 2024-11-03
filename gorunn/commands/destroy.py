import click
import subprocess
import shutil
from gorunn.config import sys_directory, src_directory, load_config
from gorunn.helpers import get_all_services, check_docker
from gorunn.translations import *


@click.command()
@click.option('--wipedb', is_flag=True, help="Completely wipe databases.")
@click.option('--app', help="Specify application to destroy.", required=False)

def destroy(app,wipedb=None):
    """
    Destroy containers.
    """
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

    command = ['docker', 'compose', 'down']
    command.extend(app_list)
    command.extend('--remove-orphans')
    try:
        subprocess.run(command, check=True, cwd=sys_directory)
        if app:
            click.echo(click.style(f"{stack_name} containers were destroyed successfully.", fg='green'))
        else:
            click.echo(click.style(f"{app} container destroyed successfully.", fg='green'))
    except subprocess.CalledProcessError as e:
        click.echo(f"Failed to stop services: {e}", err=True)
    finally:
        if wipedb:
            if click.confirm('Do you really want to wipe databases?'):
                click.echo("Wiping databases...")
                shutil.rmtree(src_directory, ignore_errors=True)
                click.echo(click.style("all databases are now wiped.", fg='green'))
            else:
                click.echo(click.style("database data preserved.", fg='green'))