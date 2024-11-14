import base64
import errno
import secrets
import subprocess
import sys
from pathlib import Path
import click
import yaml
import platform
import socket
from jinja2 import Environment, FileSystemLoader, select_autoescape
from gorunn.config import docker_template_directory, load_config, sys_directory
from cryptography.fernet import Fernet

# Check if docker is running
def check_docker():
    """Check if Docker is running and Docker Compose is available."""
    try:
        # Check if Docker daemon is running
        subprocess.run(["docker", "info"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        # Docker is not running or not installed
        click.echo(click.style("Docker is not running. Please start Docker Desktop.", fg='red'))
        raise click.Abort()

    try:
        # Check if Docker Compose is available
        subprocess.run(["docker", "compose", "--version"], check=True, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        # Docker Compose is not installed or not available
        click.echo(click.style("Docker Compose is not available. Please install Docker Compose.", fg='red'))
        raise click.Abort()

# Check if port is used on host
def check_port(port, project):
    """Check if a given port is being used by any process, skip if example-proxy is running."""
    try:
        # Check if example-proxy container is running
        result = subprocess.run(
            ["docker", "ps", "--filter", f"name={project}-proxy", "--format", "{{.Names}}"],
            capture_output=True,
            text=True
        )
        if f"{project}-proxy" in result.stdout:
            return True
    except subprocess.CalledProcessError:
        pass  # If docker command fails, continue with port check

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            result = s.connect_ex(('127.0.0.1', port))
            if result == 0:
                # Connection succeeded, port is in use
                click.echo(click.style(f"Port {port} is already in use!", fg='red'))
                click.echo(click.style("Close anything holding that port and retry.", fg='red'))
                raise click.Abort()
            else:
                # Connection refused, port is free
                return True
    except socket.error as e:
        click.echo(click.style(f"Error checking port {port}: {str(e)}", fg='red'))
        raise click.Abort()

# Get all stack projects and its names
def get_project_names():
    """Get all project names from manifest filenames."""
    project_names = []
    config = load_config()
    projects_directory = Path(config['projects']['path'])
    for project_file in Path(projects_directory).glob('*.yaml'):
        project_names.append(project_file.stem)
    return project_names

# Get stack projects that has `has_env` set, meaning those have env file
def get_projects_with_env_variables():
    """Get projects that have env_vars enabled."""
    project_names = []
    config = load_config()
    projects_directory = Path(config['projects']['path'])
    for project_file in Path(projects_directory).glob('*.yaml'):
        with open(project_file, 'r') as f:
            project_config = yaml.safe_load(f)
            if project_config.get('env_vars', False):
                project_names.append(project_file.stem)
    return project_names

# Parse template to final config
def parse_template(template_path, **kwargs):
    """Parse template replacing placeholders with actual values."""
    env = Environment(
        loader=FileSystemLoader(docker_template_directory),
        autoescape=select_autoescape(['html', 'xml', 'yaml'])
    )
    template = env.get_template(template_path.name)
    return template.render(**kwargs)

# Obtain host CPU arch
def getarch():
    """Get CPU architecture."""
    arch = platform.machine()
    if arch == 'x86_64':
        arch = 'amd64'
    elif arch.startswith('arm') or arch.startswith('aarch'):
        arch = 'arm64'
    return arch


# Function to load available projects from YAML files
def load_available_projects():
    available_projects = []
    config = load_config()
    if config is None:
        pass
    else:
        projects_directory = Path(config['projects']['path'])
        for project_file in projects_directory.glob('*.yaml'):
            available_projects.append(project_file.stem)
    return available_projects


def generate_encryption_string():
    random_bytes = secrets.token_bytes(32)
    base64_encoded = base64.b64encode(random_bytes).decode('utf-8')
    return f"base64:{base64_encoded}"


def get_all_services():
    """Retrieve all service names from the Docker Compose files in the system directory."""
    services = []
    for yaml_file in sys_directory.glob('docker-compose*.yaml'):
        with open(yaml_file, 'r') as file:
            data = yaml.safe_load(file)
            if 'services' in data:
                services.extend(data['services'].keys())  # Gather all service names
    return services

def encrypt_file(file_path, encryption_key, output_path=None):
    """Encrypt a file using Fernet encryption."""
    try:
        # Convert base64 key to Fernet key
        if encryption_key.startswith('base64:'):
            encryption_key = encryption_key[7:]
        fernet = Fernet(encryption_key.encode())

        with open(file_path, 'rb') as file:
            file_data = file.read()

        encrypted_data = fernet.encrypt(file_data)

        output_path = output_path or f"{file_path}.encrypted"
        with open(output_path, 'wb') as encrypted_file:
            encrypted_file.write(encrypted_data)
        return True
    except Exception as e:
        click.echo(click.style(f"Encryption failed: {str(e)}", fg='red'))
        return False

def decrypt_file(encrypted_file_path, encryption_key, output_path=None):
    """Decrypt a file using Fernet encryption."""
    try:
        # Convert base64 key to Fernet key
        if encryption_key.startswith('base64:'):
            encryption_key = encryption_key[7:]
        fernet = Fernet(encryption_key.encode())

        with open(encrypted_file_path, 'rb') as file:
            encrypted_data = file.read()

        decrypted_data = fernet.decrypt(encrypted_data)

        output_path = output_path or encrypted_file_path.replace('.encrypted', '')
        with open(output_path, 'wb') as decrypted_file:
            decrypted_file.write(decrypted_data)
        return True
    except Exception as e:
        click.echo(click.style(f"Decryption failed: {str(e)}", fg='red'))
        return False

def handle_encrypted_envs(config, projects_path):
    """Handle decryption of encrypted environment files before starting services."""
    try:
        encryption_key = config.get('encryption_key')
        if not encryption_key:
            click.echo(click.style("No encryption key found in configuration", fg='yellow'))
            return

        env_directory = projects_path / 'env'
        for encrypted_file in env_directory.glob('*.env.encrypted'):
            app_name = encrypted_file.stem.replace('.env', '')
            env_file = env_directory / f"{app_name}.env"

            # Skip if unencrypted file already exists
            if env_file.exists():
                continue

            if decrypt_file(encrypted_file, encryption_key, env_file):
                click.echo(click.style(f"Decrypted environment file for {app_name}", fg='green'))
            else:
                click.echo(click.style(f"Failed to decrypt environment file for {app_name}", fg='red'))

    except Exception as e:
        click.echo(click.style(f"Error handling encrypted environment files: {str(e)}", fg='red'))


def check_or_create_directory(directory_path):
    """Ensure the directory exists, create if not."""
    path = Path(directory_path)
    if not path.exists():
        try:
            path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            click.echo(click.style(f"Failed to create directory: {str(e)}", fg='red'))
            raise click.Abort()

def check_git_installed():
    """Check if Git is installed."""
    try:
        subprocess.run(["git", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except (subprocess.CalledProcessError, FileNotFoundError):
        click.echo(click.style("Git is not installed. Please install Git to use gorunn.", fg='red'))
        sys.exit(1)
