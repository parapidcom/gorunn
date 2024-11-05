import click
from pathlib import Path
import yaml
import subprocess
import secrets, base64
import hashlib
from gorunn.commands.init import copy_directory, remove_directory
from gorunn.commands.start import start
from jinja2 import Environment, FileSystemLoader, select_autoescape
from gorunn.config import sys_directory, config_file, template_directory, envs_directory, docker_template_directory, \
    db_username, db_password, load_config
from gorunn.helpers import parse_template, getarch, generate_encryption_string
from gorunn.commands.destroy import destroy
from gorunn.translations import *


def generate_dockerfile_from_template(template_path, substitutions):
    """Generate content from a Jinja2 template with substitutions."""
    env = Environment(loader=FileSystemLoader(template_path.parent), autoescape=select_autoescape(['html', 'xml', 'yaml']))
    template = env.get_template(template_path.name)
    return template.render(**substitutions)

def get_file_checksum(file_path):
    """Calculate the MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def handle_dockerfile(project_path, dockerfile_template_path, substitutions):
    """
    checks if a Dockerfile already exists, compares it against a newly generated
    version from the template, and optionally replaces it if there are differences.
    """
    dockerfile_target = project_path / 'Dockerfile.gorunn'
    dockerfile_content = generate_dockerfile_from_template(dockerfile_template_path, substitutions)
    dockerfile_checksum = hashlib.md5(dockerfile_content.encode('utf-8')).hexdigest()

    if dockerfile_target.exists():
        existing_checksum = get_file_checksum(dockerfile_target)
        if dockerfile_checksum == existing_checksum:
            click.echo("Existing Dockerfile is up to date.")
        else:
            if click.confirm(click.style(f"Dockerfile has changed. Replace {dockerfile_target}?", fg='red')):
                with open(dockerfile_target, 'w') as f:
                    f.write(dockerfile_content)
                click.echo("Dockerfile updated.")
    else:
        with open(dockerfile_target, 'w') as f:
            f.write(dockerfile_content)
        click.echo("Dockerfile created.")

def handle_env_file(project_config, project_path):
    """Generate or update environment file for a project if required."""

    env_file_path = envs_directory / f"{project_config['name']}.env"
    if not env_file_path.exists() and project_config.get('env_vars', False):
        # Determine the template based on the project type
        env_template_path = template_directory / 'envs' / f"{project_config['type']}.env.tmpl"
        env = Environment(loader=FileSystemLoader(env_template_path.parent), autoescape=select_autoescape(['html', 'xml', 'yaml']))
        template = env.get_template(env_template_path.name)

        try:
            config = load_config()
            stack_name = config['stack_name']
        except:
            click.echo(click.style(NOT_SET_UP, fg='red'))
            click.Abort()

        substitutions = {
            'stack_name': stack_name,
            'name': project_config['name'],
            'endpoint': project_config['endpoint'],
            'app_key': generate_encryption_string(),
            'database_username': db_username,
            'database_password': db_password,
        }
        env_content = template.render(**substitutions)
        with open(env_file_path, 'w') as env_file:
            env_file.write(env_content)
        click.echo(click.style(f"Environment file created: {env_file_path}", fg='green'))
    else:
        click.echo(click.style(f"Environment {env_file_path} exists, skipping...", fg='green'))


@click.command()
@click.pass_context
def parse(ctx):
    """Parse local environment configurations from templates."""
    if not (sys_directory / 'docker-compose.yaml').exists() or not (sys_directory / '.env').exists():
        click.echo(click.style(NOT_SET_UP, fg='red', bold=True))
        raise click.Abort()
    ctx.invoke(destroy)
    # If files exist, potentially destructive changes might be made, so confirm continuation
    if not click.confirm("This will stop gorunn stack. Proceed?"):
        click.echo("Operation cancelled by user.")
        raise click.Abort()

    mounts_dir = sys_directory / 'mounts'
    remove_directory(mounts_dir)
    copy_directory(template_directory / 'mounts', mounts_dir)

    click.echo(click.style("Parsing project files...", fg='blue', bold=True))
    config = load_config()
    workspace_path = Path(config['workspace_path'])
    stack_name = config['stack_name']
    projects_local_path = config['projects']['path']

    # Delete existing docker-compose*.yaml files except the main docker-compose.yaml
    for existing_file in sys_directory.glob('docker-compose*.yaml'):
        if existing_file.name != 'docker-compose.yaml':
            existing_file.unlink()

    docker_compose_paths = ['docker-compose.yaml']
    projects_directory = Path(config['projects']['path'])

    for project_file in projects_directory.glob('*.yaml'):
        with open(project_file) as f:
            project_config = yaml.safe_load(f)

        project_path = workspace_path / project_config['name']

        dockerfile_template_path = docker_template_directory / 'dockerfiles' / project_config['type'] / 'Dockerfile.tmpl'

        click.echo(click.style(f"Parsing project: {project_config['name']}", fg='green'))
        if not project_path.exists():
            try:
                click.echo(click.style(f"Cloning repository {project_config['git_repo']}...", fg='yellow'))
                subprocess.run(['git', 'clone', project_config['git_repo'], str(project_path)], check=True)
                click.echo(click.style(f"Repository cloned successfully: {project_path}", fg='green'))
            except subprocess.CalledProcessError as e:
                click.echo(click.style(f"Failed to clone repository {project_config['git_repo']}: {e}", fg='red'), err=True)
                continue  # Skip this project or handle the error as appropriate

        substitutions = {
            'stack_name': stack_name,
            'projects_local_path': projects_local_path,
            'name': project_config['name'],
            'env_vars': project_config.get('env_vars', False),
            'workspace_path': str(workspace_path),
            'server': project_config.get('server', 'dev'),
            'listen_port': project_config.get('listen_port', ''),
            'version': project_config.get('version', '0'),
            'type': project_config.get('type', 'php'),
            'database_username': db_username,
            'database_password': db_password,
            'arch': getarch()
        }

        docker_compose_template_path = docker_template_directory / f"docker-compose.{project_config['type']}.yaml.tmpl"
        docker_compose_target_path = sys_directory / f"docker-compose.{project_config['name']}.yaml"
        # Generate environment file if necessary
        handle_env_file(project_config, project_path)
        # Generate dockerfiles
        handle_dockerfile(project_path, dockerfile_template_path, substitutions)

        docker_compose_content = parse_template(docker_compose_template_path, **substitutions)
        with open(docker_compose_target_path, 'w') as target_file:
            target_file.write(docker_compose_content)
        docker_compose_paths.append(docker_compose_target_path.name)

    # Update the .env file with the correct COMPOSE_FILE order
    env_file_path = sys_directory / '.env'
    with open(env_file_path, 'r+') as ef:
        lines = ef.readlines()
        ef.seek(0)
        ef.truncate()
        updated = False
        for line in lines:
            if line.startswith('COMPOSE_FILE='):
                line = f"COMPOSE_FILE={':'.join(docker_compose_paths)}\n"
                updated = True
            ef.write(line)
        if not updated:  # If COMPOSE_FILE line was not in the file, add it
            ef.write(f"COMPOSE_FILE={':'.join(docker_compose_paths)}\n")

    click.echo(click.style("Successfully updated stack configurations.", fg='green'))
    ctx.invoke(start, build='--build')

if __name__ == "__main__":
    parse()
