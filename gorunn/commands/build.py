import click
import subprocess
import yaml
from pathlib import Path
from gorunn.config import sys_directory, config_file, load_config
from gorunn.helpers import check_docker
from gorunn.classes.app_validator import AppValidator

def execute_docker_command(service_name, _type, command):
    """Execute a command inside a Docker service using Docker Compose."""
    try:
        cmd = ['docker', 'compose', 'run', '--rm', service_name, 'bash', '-c', command]
        if _type == "python":
            cmd = ['docker', 'compose', 'run', '--rm', service_name, '/scripts/entrypoint.sh', 'bash', '-c', command]
        subprocess.run(
            cmd,
            cwd=sys_directory,
            check=True
        )
        click.echo(click.style(f"Executed: {command}", fg='green'))
    except subprocess.CalledProcessError as e:
        click.echo(click.style(f"Failed to execute {command}", fg='red'))
        raise click.Abort()

@click.command()
@click.option('--app', required=True, help="Specify application to build code for, or use all to build them all", callback=AppValidator().validate_app_callback)
def build(app):
    """Execute build commands for a specified app."""
    check_docker()
    config = load_config()
    stack_name = config['stack_name']
    projects_directory = Path(config['projects']['path'])
    if app == "all":
        for project_file in projects_directory.glob("*.yaml"):
            with open(project_file, 'r') as file:
                project_config = yaml.safe_load(file)
            app_name = project_config['name']
            _type = project_config['type']
            if 'build_commands' not in project_config:
                click.echo(click.style(f"No build commands found for {app_name}", fg='yellow'))
                return
            service_name = f"{stack_name}-{app_name}"
            for command in project_config['build_commands']:
                click.echo(click.style(f"Building project: {app_name}", fg='cyan'))
                click.echo(click.style(f"Running command for {app_name}: {command}", fg='blue'))
                execute_docker_command(service_name, _type, command)
    else:
        config=load_config()
        project_file_path = config['projects']['path'] / f"{app}.yaml"

        if not project_file_path.exists():
            click.echo(click.style(f"Project configuration not found for {app}", fg='red'))
            raise click.Abort()

        with open(project_file_path, 'r') as file:
            project_config = yaml.safe_load(file)
        _type = project_config['type']

        if 'build_commands' not in project_config:
            click.echo(click.style(f"No build commands found for {app}", fg='yellow'))
            return

        service_name = f"{stack_name}-{app}"
        for command in project_config['build_commands']:
            click.echo(click.style(f"Running command for {app}: {command}", fg='blue'))
            execute_docker_command(service_name, _type, command)

    click.echo(click.style(f"Build process completed for {app}.", fg='green'))

if __name__ == "__main__":
    build()
