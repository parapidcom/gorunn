import click
import subprocess
import yaml
from datetime import datetime
from pathlib import Path
from gorunn.config import config_directory, load_config
from gorunn.translations import *
from gorunn.helpers import encrypt_file, decrypt_file

@click.group()
def projects():
    """Manage projects configurations."""
    pass

@projects.command()
@click.option('--branch', default='master', help='Branch to pull projects files from.')
def pull(branch):
    """Pulls the latest changes for the projects."""
    try:
        config = load_config()
        stack_name = config['stack_name']
        projects_directory = Path(config['projects']['path'])
    except:
        click.echo(click.style(NOT_SET_UP, fg='red'))
        click.Abort()

    projects_repo_url = config['projects']['repo_url']
    if projects_repo_url is None:
        click.echo(click.style("Project repo URL is not set, therefore nothing can be pulled.", fg='yellow'))
        return
    if not projects_directory.exists():
        click.echo(f"Project directory does not exist. Cloning it from {projects_repo_url}")
        result = subprocess.run(['git', 'clone', projects_repo_url, projects_directory], cwd=config_directory, capture_output=True, text=True)
    else:
        click.echo("Updating projects configurations...")
        result = subprocess.run(['git', 'pull', 'origin', branch], cwd=projects_directory, capture_output=True, text=True)

    if 'Already up to date.' in result.stdout:
        click.echo(click.style("Project configurations are the latest.", fg='green'))
    else:
        click.echo(click.style("Project configurations updated successfully.", fg='green'))

@projects.command()
def publish():
    """Push changes to the remote repository if there are any pending updates."""
    try:
        config = load_config()
        projects_directory = Path(config['projects']['path'])
    except:
        click.echo(click.style(NOT_SET_UP, fg='red'))
        click.Abort()

    status_result = subprocess.run(['git', 'status', '--porcelain'], cwd=projects_directory, capture_output=True, text=True)
    status_lines = status_result.stdout.strip().split('\n')

    unstaged_changes = [line for line in status_lines]
    if unstaged_changes:
        click.echo("You have changes that are not staged for commit:")
        for change in unstaged_changes:
            click.echo(f"  {change[3:]}")  # Correct slicing to display full filenames

        if click.confirm(click.style("Do you want to add all changes to the staging area?", fg='cyan'), default=True):
            subprocess.run(['git', 'add', '.'], cwd=projects_directory, check=True)

    if subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=projects_directory).returncode != 0:
        now = datetime.now().strftime("%H%M-%d%m%y")
        commit_message = f"Project update {now}"
        commit_result = subprocess.run(['git', 'commit', '-m', commit_message], cwd=projects_directory, capture_output=True, text=True)
        if commit_result.returncode == 0:
            click.echo("Changes committed successfully.")
        else:
            click.echo("No new changes to commit.")

    # Check if there are commits to push using a more robust check
    push_needed_result = subprocess.run(['git', 'log', '--branches', '--not', '--remotes'], cwd=projects_directory, capture_output=True, text=True)
    if push_needed_result.stdout.strip():
        if click.confirm(click.style("Do you want to push the changes to live?", fg='cyan'), default=True):
            push_result = subprocess.run(['git', 'push', 'origin', 'master'], cwd=projects_directory, capture_output=True, text=True)
            if push_result.returncode == 0:
                click.echo(click.style("Changes pushed to live successfully.", fg='green'))
            else:
                click.echo(click.style("Failed to push changes.", fg='red'))
                click.echo(push_result.stderr)
    else:
        click.echo("There are no new local commits to push.")

@projects.command()
@click.option('--encrypt', is_flag=True, help="Encrypt the environment file")
@click.option('--decrypt', is_flag=True, help="Decrypt the environment file")
@click.option('--app', required=True, help="Specify the application name")
def env(encrypt, decrypt, app):
    """Manage environment file encryption/decryption."""
    if encrypt and decrypt:
        click.echo(click.style("Cannot specify both --encrypt and --decrypt", fg='red'))
        return

    if not (encrypt or decrypt):
        click.echo(click.style("Must specify either --encrypt or --decrypt", fg='red'))
        return

    try:
        config = load_config()
        if not config:
            click.echo(click.style(NOT_SET_UP, fg='red'))
            return

        encryption_key = config.get('encryption_key')
        if not encryption_key:
            click.echo(click.style("No encryption key found in configuration", fg='red'))
            return

        projects_path = Path(config['projects']['path'])
        env_directory = projects_path / 'env'
        env_file = env_directory / f"{app}.env"
        encrypted_file = env_directory / f"{app}.env.encrypted"

        if encrypt:
            if not env_file.exists():
                click.echo(click.style(f"Environment file not found: {env_file}", fg='red'))
                return

            if encrypt_file(env_file, encryption_key, encrypted_file):
                click.echo(click.style(f"Successfully encrypted environment file for {app}", fg='green'))

        elif decrypt:
            if not encrypted_file.exists():
                click.echo(click.style(f"Encrypted environment file not found: {encrypted_file}", fg='red'))
                return

            if decrypt_file(encrypted_file, encryption_key, env_file):
                click.echo(click.style(f"Successfully decrypted environment file for {app}", fg='green'))

    except Exception as e:
        click.echo(click.style(f"Operation failed: {str(e)}", fg='red'))

if __name__ == '__main__':
    projects()
