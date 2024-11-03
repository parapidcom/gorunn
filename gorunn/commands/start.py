import click
import subprocess
import yaml
from gorunn.config import sys_directory, config_file, load_config
from gorunn.helpers import check_docker, check_port
from gorunn.classes.app_validator import AppValidator
from gorunn.translations import *

@click.command()
@click.option('--app', help='Specify one or more applications to start, separated by commas.', default=None,
              callback=AppValidator().validate_app_callback)
@click.option('--build', is_flag=True, help='Build from the image.', default=None)
def start(app, build):
    """
    Start services. If no application is specified, all services are started.
    """
    try:
        config = load_config()
        stack_name = config['stack_name']
    except:
        click.echo(click.style(NOT_SET_UP, fg='red'))
        click.Abort()
    build_command = ['docker', 'compose', 'build']
    command = ['docker', 'compose', 'up', '-d', '--remove-orphans']
    check_docker()
    # Check for ports 443 and 80 if in use on host. These ports are needed for the gorunn stack proxy to run.
    check_port(80, stack_name)
    check_port(443, stack_name)
    if app:
        build_command.extend(f"{stack_name}-{app}")
        command.append(f"{stack_name}-{app}")
    # Run the Docker Compose command
    try:
        if build:
            subprocess.run(build_command, check=True, cwd=sys_directory)
        subprocess.run(command, check=True, cwd=sys_directory)
        if app:
            click.echo(click.style(f"{app} has started successfully.", fg='green'))
        else:
            click.echo(click.style(f"{stack_name} services stack has started successfully.", fg='green'))
    except subprocess.CalledProcessError as e:
        if app:
            click.echo(f"Failed to start {app}: {e}", err=True)
        else:
            click.echo(f"Failed to start stack: {e}", err=True)
