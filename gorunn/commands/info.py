import sys
from pathlib import Path

import click
import yaml
import boto3
import subprocess
from gorunn.config import config_file, load_config
from gorunn.translations import *


def get_docker_status(container_name):
    """Retrieve the status and port mappings of a Docker container."""
    try:
        result = subprocess.run(
            ['docker', 'inspect', '--format', '{{.State.Status}} (Ports: {{.NetworkSettings.Ports}})', container_name],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        return result.stdout.strip() if result.stdout.strip() else click.style("Container is not running", fg='red')
    except subprocess.CalledProcessError:
        return click.style("Container is not running", fg='red')

@click.command()
def info():
    """Displays information about each project."""
    try:
        config = load_config()
        projects_directory = Path(config['projects']['path'])
        project_files = projects_directory.glob('*.yaml')
        config = load_config()
        stack_name = config['stack_name']
        for project_file in project_files:
            with open(project_file, 'r') as file:
                project = yaml.safe_load(file)
                click.echo(click.style(f"Project Name: {project['name']}", fg='green'))
                click.echo(f"Endpoint: https://{project['endpoint']}")
                click.echo(f"Type: {project['type']}")
                click.echo(f"Version: {project['version']}")
                container_status = get_docker_status(f"{stack_name}-{project['name']}")
                click.echo(f"Docker Status: {container_status}")
                click.echo("---")
    except:
        click.echo(click.style(NOT_SET_UP, fg='red'))
        click.Abort()


if __name__ == '__main__':
    info()
