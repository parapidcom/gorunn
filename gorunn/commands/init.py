import re
from pathlib import Path

import click
import yaml
import git
import shutil
from gorunn.commands.trust import trust
import inquirer
import secrets
import base64

from gorunn.config import subnet, env_template, sys_directory, config_file, docker_compose_template, template_directory, \
    supported_services, db_username, db_password, db_root_password, load_config, default_projects_directory, default_wokspace_directory, default_stack_name
from gorunn.commands.destroy import destroy
from gorunn.commands.parse import parse
from gorunn.utils import copy_directory, remove_directory
from gorunn.helpers import getarch, parse_template, check_or_create_directory, check_git_installed
from gorunn.translations import *



# Read existing configuration if it exists
existing_config = {}
if config_file.exists():
    with open(config_file, 'r') as file:
        existing_config = yaml.safe_load(file) or {}

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
            click.echo(click.style(f"Pulling manifests from {repo_url} into {directory}."))
            git.Repo.clone_from(repo_url, directory)
            click.echo(click.style(f"Cloned project manifests from {repo_url} into {directory}.", fg='green'))
        except Exception as e:
            click.echo(click.style(f"Failed to clone repository: {str(e)}", fg='red'))





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
    existing_aider = existing_config.get('aider', {})
    aider_enable_question = [
        inquirer.Confirm('setup_aider',
                         message="\033[36mWould you like to set up aider?\033[0m",
                         default=False)
    ]

    aider_llm_question = [
        inquirer.List('aider_llm',
                      message="Which AI provider would you like to use?",
                      choices=['Claude', 'OpenAI', 'Not at this moment'])
    ]

    aider_config = {
        'enabled': existing_aider.get('enabled', False),
        'llm': existing_aider.get('llm'),
        'api_key': existing_aider.get('api_key')
    }

    aider_setup = inquirer.prompt(aider_enable_question)
    if aider_setup['setup_aider']:
        provider_choice = inquirer.prompt(aider_llm_question)
        if provider_choice['aider_llm'] == 'Claude':
            aider_config = {
                'enabled': True,
                'llm': 'claude',
                'api_key': click.prompt(
                    click.style("Please enter your Claude API key", fg='cyan'),
                    type=str,
                    default=existing_aider.get('api_key', ''),
                    hide_input=False
                )
            }
        elif provider_choice['aider_llm'] == 'OpenAI':
            aider_config = {
                'enabled': True,
                'llm': 'openai',
                'api_key': click.prompt(
                    click.style("Please enter your OpenAI API key", fg='cyan'),
                    type=str,
                    default=existing_aider.get('api_key', ''),
                    hide_input=False
                )
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


def generate_encryption_key():
    """Generate a secure encryption key."""
    return base64.b64encode(secrets.token_bytes(32)).decode('utf-8')


def configure_encryption_key():
    """Handle encryption key configuration through user prompts."""
    try:
        existing_key = existing_config.get('encryption_key')

        # If we already have a key in the config, ask if they want to keep it
        if existing_key:
            if click.confirm(click.style("Existing encryption key found. Would you like to keep it?", fg='cyan'), default=True):
                return existing_key

        encryption_key_question = [
            inquirer.Confirm('has_key',
                            message="\033[36mDo you already have an encryption key?\033[0m",
                            default=False)
        ]

        key_setup = inquirer.prompt(encryption_key_question)
        if key_setup is None:  # User pressed Ctrl+C
            raise click.Abort()

        if key_setup['has_key']:
            encryption_key = click.prompt(
                click.style("Please enter your encryption key", fg='cyan'),
                type=str,
                hide_input=False
            )
        else:
            encryption_key = generate_encryption_key()
            click.echo(click.style("Generated new encryption key.", fg='green'))
            click.echo(click.style("Please save this key securely:", fg='yellow'))
            click.echo(click.style(encryption_key, fg='cyan'))

        return encryption_key
    except (KeyboardInterrupt, click.Abort):
        raise click.Abort()


# This methid will create config.yaml
def create_config(import_repo):

    stack_name_message = f"Please enter your stack name (no spaces or special characters)"
    projects_repo_url_message = f"GitHub repo URL of project manifests[leave empty if you want to use it without repo]"
    project_manifests_dir_message = f"Enter full path to the directory where your project stack is or should be pulled from repo"
    workspace_message = f"Enter the workspace path for the projects"
    subnet_message = f"Which subnet to use for Docker Compose network? Leave empty to use default"
    service_choices = supported_services
    questions = [
        inquirer.Checkbox('services',
                          message="Select services to use(multiple choices possible)",
                          choices=service_choices,
                          default=[service for service in service_choices if existing_config.get('services', {}).get(service, False)]
                          ),
    ]
    stack_name = click.prompt(
        click.style(stack_name_message, fg='cyan'),
        type=str,
        default=existing_config.get('stack_name', default_stack_name),
        hide_input=False,
        value_proc=validate_and_transform_input
    )
    project_manifests_dir = path(
        project_manifests_dir_message,
        existing_config.get('projects', {}).get('path', default_projects_directory)
    )
    projects_repo_url = import_repo if import_repo else click.prompt(
        click.style(projects_repo_url_message, fg='cyan'),
        default=existing_config.get('projects', {}).get('repo_url', ''),
        type=str
    )
    workspace_path = path(
        workspace_message,
        existing_config.get('workspace_path', default_wokspace_directory)
    )
    docker_compose_subnet = click.prompt(
        click.style(subnet_message, fg='cyan'),
        default=existing_config.get('docker_compose_subnet', subnet),
        type=str
    )
    service_answers = inquirer.prompt(questions)
    projects_config = {
        'path': project_manifests_dir,
        'repo_url': projects_repo_url
    }
    service_config = {service: (service in service_answers['services']) for service in service_choices}
    aider_config = configure_aider()
    encryption_key = configure_encryption_key()

    # Update and save the new configuration data
    config_yaml = {
        'workspace_path': workspace_path,
        'stack_name': stack_name,
        'projects': projects_config,
        'docker_compose_subnet': docker_compose_subnet,
        'services': service_config,
        'aider': aider_config,
        'encryption_key': encryption_key
    }
    save_config(config_yaml)


@click.command()
@click.option('--import', 'import_repo', help='Import projects manifests from a Git repository URL')
@click.option('--parse', 'run_parse', help='Run parse after init', is_flag=True)
@click.pass_context
def init(ctx, import_repo, run_parse):
    """Initialize configuration and set up docker-compose files."""
    check_git_installed()  # Ensure Git is installed before proceeding
    check_or_create_directory(sys_directory)

    # Determine if the destroy command needs to be run
    if (sys_directory / 'docker-compose.yaml').exists() and (sys_directory / '.env').exists():
        ctx.invoke(destroy)

    arch = getarch()
    if config_file.exists():
        click.echo(click.style("Existing configuration found at: {}".format(config_file), fg='yellow'))
        if click.confirm(click.style("Would you like to replace the existing configuration?", fg='cyan')):
            # Prompt for new configuration details
            create_config(import_repo)
        else:
            click.echo(click.style("Keeping existing configuration.", fg='yellow'))
    else:
        create_config(import_repo)

    config = load_config()
    projects_repo_url = config.get('projects', {}).get('repo_url', '')
    project_manifests_dir = Path(config.get('projects', {}).get('path', default_projects_directory))
    stack_name = config.get('stack_name', default_stack_name)
    encryption_key = config.get('encryption_key', '')
    docker_compose_subnet = config.get('docker_compose_subnet', subnet)
    mysql_enabled = config.get('services', {}).get('mysql', True)
    postgres_enabled = config.get('services', {}).get('postgres', False)
    redis_enabled = config.get('services', {}).get('redis', True)
    memcached_enabled = config.get('services', {}).get('memcached', False)
    chroma_enabled = config.get('services', {}).get('chroma', False)
    opensearch_enabled = config.get('services', {}).get('opensearch', False)
    mongodb_enabled = config.get('services', {}).get('mongodb', False)
    kafka_enabled = config.get('services', {}).get('kafka', False)
    rabbitmq_enabled = config.get('services', {}).get('rabbitmq', False)

    styled_DOCS_LINK_PROJECTS = click.style(DOCS_LINK_PROJECTS, fg='blue')
    styled_project_manifests_dir = click.style(project_manifests_dir, fg='red')
    styled_projects_repo_url = click.style(projects_repo_url, fg='blue')
    if project_manifests_dir.exists() and any(project_manifests_dir.glob('*.yaml')):
        if projects_repo_url:
            if click.confirm(
                    f"Project directory {styled_project_manifests_dir} exists with project manifests. Do you want to pull the latest updates from {styled_projects_repo_url}?"):
                clone_or_pull_repository(projects_repo_url, project_manifests_dir)
        else:
            click.echo(click.style(f"Found existing project directory at {styled_project_manifests_dir}", fg='yellow'))
    else:
        click.echo(f"No projects configuration found or {styled_project_manifests_dir} does not exist.")
        if projects_repo_url:
            clone_or_pull_repository(projects_repo_url, project_manifests_dir)
        else:
            check_or_create_directory(project_manifests_dir)
            click.echo(click.style(f"Check {styled_DOCS_LINK_PROJECTS} on how to set up projects in {styled_project_manifests_dir}", fg='yellow'))

    # Create envs directory
    # Get existing projects config or empty dict if it doesn't exist
    existing_projects = existing_config.get('projects', {})

    projects_config = {
        'path': existing_projects.get('path', project_manifests_dir),
        'repo_url': existing_projects.get('repo_url', projects_repo_url)
    }
    envs_directory = project_manifests_dir / 'env'
    check_or_create_directory(envs_directory)

    substitutions = {
        'stack_name': stack_name,
        'project_manifests_dir': project_manifests_dir,
        'mysql': mysql_enabled,
        'postgres': postgres_enabled,
        'redis': redis_enabled,
        'chroma': chroma_enabled,
        'opensearch': opensearch_enabled,
        'mongodb': mongodb_enabled,
        'kafka': kafka_enabled,
        'rabbitmq': rabbitmq_enabled,
        'memcached': memcached_enabled,
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
    click.echo(click.style("Adding self signed certificate to system's trusted store, please authorize it.", fg='green'))
    ctx.invoke(trust)
    if run_parse:
        ctx.invoke(parse)

if __name__ == "__main__":
    init()
