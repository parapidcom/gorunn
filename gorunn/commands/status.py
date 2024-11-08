import click
import subprocess
from pathlib import Path
from gorunn.config import load_config, sys_directory
from gorunn.translations import *


def get_container_status(container_name):
    """Retrieve detailed status information about a Docker container."""
    try:
        # Modified format string to get full port mapping details
        format_string = '{{.Name}};{{.State.Status}};{{range $p, $conf := .NetworkSettings.Ports}}{{if $conf}}{{$p}}->{{range $conf}}{{.HostPort}}{{end}},{{end}}{{end}}'
        result = subprocess.run(
            ['docker', 'inspect', '--format', format_string, container_name],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        if result.stdout.strip():
            name, status, ports = result.stdout.strip().split(';')

            # Clean up ports output for better display
            ports = ports.strip(',')  # Remove trailing comma
            ports = 'none' if not ports else ports

            return {
                'name': name.strip('/'),
                'status': status,
                'ports': ports
            }
        return None
    except subprocess.CalledProcessError:
        return None


@click.command()
def status():
    """Display status information about all containers in the stack."""
    try:
        # Get list of all containers in the stack
        result = subprocess.run(
            ['docker', 'compose', 'ps', '--format', '{{.Name}}'],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            cwd=Path(sys_directory)
        )

        containers = result.stdout.strip().split('\n') if result.stdout.strip() else []

        if not containers:
            click.echo(click.style("Stack is not running.", fg='yellow'))
            return

        # Display header and container info
        click.echo("\n" + "=" * 100)
        click.echo(f"{click.style('Container Name', fg='blue'):40} {click.style('Status', fg='blue'):15} {click.style('Ports', fg='blue'):45}")
        click.echo("=" * 100)

        all_running = True
        for container in containers:
            if not container:  # skip empty lines
                continue

            status_info = get_container_status(container)
            if status_info:
                name_color = 'green' if status_info['status'] == 'running' else 'red'
                if status_info['status'] != 'running':
                    all_running = False

                click.echo(
                    f"{click.style(status_info['name'], fg=name_color):40} "
                    f"{click.style(status_info['status'], fg=name_color):15} "
                    f"{status_info['ports']:45}"
                )
            else:
                all_running = False
                click.echo(f"{click.style(container, fg='red'):40} Not found")

        click.echo("=" * 100)

        # Add status summary
        status_msg = "Stack is healthy" if all_running else "Stack is degraded"
        status_color = 'green' if all_running else 'yellow'
        click.echo(click.style(f"\n{status_msg}\n", fg=status_color, bold=True))

    except Exception as e:
        click.echo(click.style(f"Error: {str(e)}", fg='red'))
        click.echo(click.style(NOT_SET_UP, fg='red'))
        raise click.Abort()


if __name__ == '__main__':
    status()
