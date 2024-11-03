from pathlib import Path

import click
import subprocess
import yaml
from gorunn.config import sys_directory, config_file, load_config
from gorunn.helpers import check_docker
from gorunn.classes.app_validator import AppValidator
from gorunn.translations import *


def get_all_services():
    """Retrieve all service names from the Docker Compose files in the system directory."""
    services = []
    for yaml_file in sys_directory.glob('docker-compose*.yaml'):
        with open(yaml_file, 'r') as file:
            data = yaml.safe_load(file)
            if 'services' in data:
                services.extend(data['services'].keys())
    return services

def strip_suffixes(name, suffixes):
    """Strip specific suffixes from a service name for project file matching."""
    for suffix in suffixes:
        if name.endswith(suffix):
            return name[:name.rfind(suffix)]
    return name


@click.command()
@click.option('--app', required=True, help="Specify application name.", callback=AppValidator().validate_app_callback)
def terminal(app):
    """Execute a shell inside a Docker container."""
    check_docker()
    try:
        config = load_config()
        stack_name = config['stack_name']
        projects_directory = Path(config['projects']['path'])
    except:
        click.echo(click.style(NOT_SET_UP, fg='red'))
        click.Abort()
    _type = None
    for project_file in projects_directory.glob(f'{app}.yaml'):
        with open(project_file) as f:
            project_config = yaml.safe_load(f)
            _type = project_config.get('type')
            break

    if not app.startswith(f"{stack_name}-"):
        app = f"{stack_name}-{app}"


    services = get_all_services()
    if app not in services:
        click.echo(click.style(f"Service {app} not found in stack.", fg='red'))
        return

    current_dir = sys_directory
    try:
        click.echo(click.style(f"Exec into shell for {app}", fg='green'))
        if _type == "python": # we use different entrypoint for python because virtual env is loaded from within entrypoint.sh
            subprocess.run(['docker', 'compose', 'exec', app, '/scripts/entrypoint.sh', 'bash'], cwd=current_dir, check=True)
        else:
            subprocess.run(['docker', 'compose', 'exec', app, 'sh'], cwd=current_dir, check=True)
    except subprocess.CalledProcessError as e:
        if e.returncode != 130:
            click.echo(click.style("Failed to exec into service.", fg='red'))

if __name__ == "__main__":
    terminal()
