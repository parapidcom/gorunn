import re
from pathlib import Path

import click
import yaml
import git
import shutil
from gorunn.commands.trust import trust
import inquirer

from gorunn.config import subnet, env_template, sys_directory, config_file, docker_compose_template, template_directory, \
    envs_directory, db_username, db_password, db_root_password, load_config, default_projects_directory, default_wokspace_directory, default_stack_name
from gorunn.commands.destroy import destroy
from gorunn.helpers import parse_template, getarch
from gorunn.translations import *

def clone_or_pull_repository(repo_url, directory):
    """Clone or pull the repository depending on the existing state."""
    if directory.exists() and any(directory.iterdir()):
        # Assuming directory is a git repository
        try:
            repo = git.Repo(directory)
            origin = repo.remotes.origin

            # Reset local changes
            repo.git.reset('--hard')
            repo.git.clean('-fdx')

            click.echo("Pulling...")
            origin.pull()
            click.echo(click.style("Updated project repository from remote.", fg='green'))
        except Exception as e:
            click.echo(click.style(f"Failed to update repository: {str(e)}", fg='red'))
    else:
        if directory.exists():
            shutil.rmtree(directory)  # Clear the directory if it exists
        try:
            git.Repo.clone_from(repo_url, directory)
            click.echo(click.style("Cloned project repository successfully.", fg='green'))
        except Exception as e:
            click.echo(click.style(f"Failed to clone repository: {str(e)}", fg='red'))


def check_or_create_directory(directory_path):
    """Ensure the directory exists, create if not."""
    path = Path(directory_path)
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        click.echo(click.style(f"Created directory at: {path}", fg='green'))


def remove_directory(directory_path):
    """Remove the directory if it exists."""
    if directory_path.exists():
        shutil.rmtree(directory_path)


def copy_directory(source, destination):
    """Copy entire directory from source to destination."""
    shutil.copytree(source, destination)


def copy_file(source, destination, overwrite=False):
    """Copy file from source to destination, optionally overwriting existing files."""
    if not destination.exists() or overwrite:
        shutil.copy(source, destination)
        action = "Updated" if destination.exists() else "Copied"
        click.echo(click.style(f"{action} file to {destination}", fg='green'))
    else:
        click.echo(click.style(f"File already exists and was not overwritten: {destination}", fg='yellow'))


def save_config(data):
    """Save configuration data to a YAML file."""
    with open(config_file, 'w') as file:
        yaml.dump(data, file)
    click.echo(click.style("Configuration saved successfully.", fg='green'))


def validate_absolute_path(value):
    """Validate that the input is an absolute path starting with '/'."""
    if not value.startswith('/'):
        return False
    return True


# Get path once it is validated as starting with /
def path(prompt_message, fallback):
    while True:
        # Prompt user for the workspace path
        path_from_input = click.prompt(click.style(prompt_message, fg='cyan'), default=fallback, type=str)
        if validate_absolute_path(path_from_input):
            check_or_create_directory(path_from_input)
            return path_from_input
        else:
            click.echo(click.style("The path must be absolute and start with '/'.", fg='red'))


def configure_aider():
    """Handle aider configuration setup through user prompts."""
    aider_enable_question = [
        inquirer.Confirm('setup_aider',
                         message="Would you like to set up aider?",
                         default=False)
    ]

    aider_llm_question = [
        inquirer.List('aider_llm',
                      message="Which AI provider would you like to use?",
                      choices=['Claude', 'OpenAI', 'Not at this moment'])
    ]

    aider_setup = inquirer.prompt(aider_enable_question)
    aider_config = {
        'enabled': False,
        'llm': None,
        'api_key': None,
    }

    if aider_setup['setup_aider']:
        provider_choice = inquirer.prompt(aider_llm_question)
        if provider_choice['aider_llm'] == 'Claude':
            aider_config = {
                'enabled': True,
                'llm': 'claude',
                'api_key': click.prompt(click.style("Please enter your Claude API key", fg='cyan'),
                                        type=str, hide_input=False)
            }
        elif provider_choice['aider_llm'] == 'OpenAI':
            aider_config = {
                'enabled': True,
                'llm': 'openai',
                'api_key': click.prompt(click.style("Please enter your OpenAI API key", fg='cyan'),
                                        type=str, hide_input=False)
            }

    return aider_config



def validate_and_transform_input(input_value):
    """Validate that the input contains only letters and numbers and convert to lowercase."""
    if re.match("^[a-zA-Z0-9]*$", input_value):
        # Input is valid, convert to lowercase
        return input_value.lower()
    else:
        # Input is invalid, raise an exception
        raise click.BadParameter("Input should only contain letters and numbers without spaces.")



# This methid will create config.yaml
def create_config():
    # Read existing configuration if it exists
    stack_name_message = f"Please enter your project (no spaces or special characters)"
    projects_repo_url_message = f"GitHub repo URL where project files are stored[leave empty if you want to use it without repo]"
    projects_local_path_message = f"Enter full path to the directory where your project stack is or should be pulled from repo"
    workspace_message = f"Enter the workspace path, where your project repos should be"
    subnet_message = f"Which subnet to use for Docker Compose network? Leave empty to use default"
    db_choices = ['mysql', 'postgresql', 'redis', 'chroma', 'opensearch']
    questions = [
        inquirer.Checkbox('databases',
                          message="Select databases to use(multiple choices possible)",
                          choices=db_choices,
                          ),
    ]
    stack_name = click.prompt(click.style(stack_name_message, fg='cyan'),
                              type=str,
                              default=default_stack_name,
                              hide_input=False,
                              value_proc=validate_and_transform_input)
    projects_local_path = path(projects_local_path_message, default_projects_directory)
    projects_repo_url = click.prompt(click.style(projects_repo_url_message, fg='cyan'), default='', type=str)
    workspace_path = path(workspace_message, default_wokspace_directory)
    docker_compose_subnet = click.prompt(click.style(subnet_message, fg='cyan'), default=subnet, type=str)
    database_answers = inquirer.prompt(questions)
    projects_config = {
        'path': projects_local_path,
        'repo_url': projects_repo_url
    }
    db_config = {db: (db in database_answers['databases']) for db in db_choices}
    aider_config = configure_aider()

    # Update and save the new configuration data
    config_yaml= {
        'workspace_path': workspace_path,
        'stack_name': stack_name,
        'projects': projects_config,
        'docker_compose_subnet': docker_compose_subnet,
        'databases': db_config,
        'aider': aider_config
    }
    save_config(config_yaml)


@click.command()
@click.pass_context  # Add this decorator to pass the context automatically
def init(ctx):
    """Initialize configuration and set up docker-compose files."""
    check_or_create_directory(sys_directory)
    check_or_create_directory(envs_directory)

    # Determine if the destroy command needs to be run
    if (sys_directory / 'docker-compose.yaml').exists() and (sys_directory / '.env').exists():
        ctx.invoke(destroy)

    arch = getarch()
    if config_file.exists():
        click.echo(click.style("Existing configuration found at: {}".format(config_file), fg='yellow'))
        if click.confirm(click.style(EXISTING_CONFIGURATION_PROMPT, fg='magenta')):
            # Prompt for new configuration details
            create_config()
        else:
            click.echo(click.style("Keeping existing configuration.", fg='yellow'))
    else:
        create_config()

    config = load_config()
    projects_repo_url = config['projects']['repo_url']
    projects_local_path = Path(config['projects']['path'])
    stack_name = config['stack_name']
    docker_compose_subnet = config['docker_compose_subnet']
    mysql_enabled = config['databases']['mysql']
    postgresql_enabled = config['databases']['postgresql']
    redis_enabled = config['databases']['redis']
    chroma_enabled = config['databases']['chroma']
    opensearch_enabled = config['databases']['opensearch']


    styled_DOCS_LINK_PROJECTS = click.style(DOCS_LINK_PROJECTS, fg='blue')
    styled_projects_local_path = click.style(projects_local_path, fg='red')
    styled_projects_repo_url = click.style(projects_repo_url, fg='blue')
    if projects_local_path.exists() and any(projects_local_path.glob('*.yaml')):
        if projects_repo_url:
            if click.confirm(
                    f"Project directory {styled_projects_local_path} exists with configuration files. Do you want to pull the latest updates from {styled_projects_repo_url}?"):
                clone_or_pull_repository(projects_repo_url, projects_local_path)
        else:
            click.echo(click.style(f"Found existing project directory at {styled_projects_local_path}", fg='yellow'))
    else:
        click.echo(f"No projects configuration found or {styled_projects_local_path} does not exist.")
        if projects_repo_url:
            click.confirm(f"Would you like to clone the project repository {styled_projects_repo_url} into {styled_projects_local_path} ?")
            clone_or_pull_repository(projects_repo_url, projects_local_path)
        else:
            check_or_create_directory(projects_local_path)
            click.echo(click.style(f"Check {styled_DOCS_LINK_PROJECTS} on how to set up projects in {styled_projects_local_path}", fg='yellow'))

    substitutions = {
        'stack_name': stack_name,
        'projects_local_path': projects_local_path,
        'mysql': mysql_enabled,
        'postgresql': postgresql_enabled,
        'redis': redis_enabled,
        'chroma': chroma_enabled,
        'opensearch': opensearch_enabled,
        'docker_compose_subnet': docker_compose_subnet,
        'database_username': db_username,
        'database_password': db_password,
        'database_root_password': db_root_password,
        'arch': arch
    }
    main_docker_compose_contents = parse_template(docker_compose_template, **substitutions)
    with open(f"{sys_directory}/docker-compose.yaml", 'w') as target_file:
        target_file.write(main_docker_compose_contents)
    env_contents = parse_template(env_template, **substitutions)
    with open(f"{sys_directory}/.env", 'w') as target_file:
        target_file.write(env_contents)

    mounts_dir = sys_directory / 'mounts'
    remove_directory(mounts_dir)
    copy_directory(template_directory / 'mounts', mounts_dir)

    click.echo(click.style("System files and directories setup completed.", fg='green'))
    click.echo(click.style("Adding self signed certificate to Apple Keychain, please authorize it.", fg='green'))
    ctx.invoke(trust)

if __name__ == "__main__":
    init()
