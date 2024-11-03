import click
import subprocess
import yaml
from gorunn.config import sys_directory, config_file, load_config
from gorunn.classes.app_validator import AppValidator


def get_all_services():
    """Retrieve all service names from the Docker Compose files in the system directory."""
    services = []
    for yaml_file in sys_directory.glob('docker-compose*.yaml'):
        with open(yaml_file, 'r') as file:
            data = yaml.safe_load(file)
            if 'services' in data:
                services.extend(data['services'].keys())  # Gather all service names
    return services

@click.command(name='exec', help="Executes a specified command within container.")
@click.option('--app', required=True, help="Specify application.", callback=AppValidator().validate_app_callback)
@click.option('--command', required=True, help="The command string to execute inside the Docker service.")

def docker_exec(app, command):
    """Execute a specified command within service."""
    with open(config_file) as f:
        main_config = yaml.safe_load(f)

    config = load_config()
    stack_name = config['stack_name']
    services = get_all_services()
    service_name = f"{stack_name}-{app}"


    if service_name not in services:
        click.echo(click.style(f"Service {service_name} not found in stack files.", fg='red'))
        raise click.Abort()

    # Execute the command within the specified Docker service
    try:
        click.echo(f"Executing command in {service_name}: {command}")
        subprocess.run(
            ['docker', 'compose', 'run', '--rm', service_name, 'bash', '-c', command],
            cwd=sys_directory,
            check=True
        )
        click.echo(click.style("Command executed successfully.", fg='green'))
    except subprocess.CalledProcessError as e:
        click.echo(click.style(f"Failed to execute command in {service_name}: {e}", fg='red'))
        raise click.Abort()

if __name__ == "__main__":
    docker_exec()
