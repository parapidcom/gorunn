import click
import subprocess
import yaml
from datetime import datetime
from pathlib import Path
from gorunn.config import config_directory, load_config
from gorunn.translations import *

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

        if click.confirm("Do you want to add all changes to the staging area?", default=True):
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
        if click.confirm("Do you want to push the changes to live?", default=True):
            push_result = subprocess.run(['git', 'push', 'origin', 'master'], cwd=projects_directory, capture_output=True, text=True)
            if push_result.returncode == 0:
                click.echo(click.style("Changes pushed to live successfully.", fg='green'))
            else:
                click.echo(click.style("Failed to push changes.", fg='red'))
                click.echo(push_result.stderr)
    else:
        click.echo("There are no new local commits to push.")

if __name__ == '__main__':
    projects()
