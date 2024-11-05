import sys
from pathlib import Path
import getpass
import os

import click
import yaml

# Get the current login user
current_user = getpass.getuser()
base_domain = "local.gorunn.io"
company_domain = "gorunn.io"
org = "parapidcom"
aider_image = "paulgauthier/aider-full"

# Set the paths for the configuration and system directories
config_directory = Path.home() / 'gorunn'
sys_directory = config_directory / '.system'
src_directory = sys_directory / 'src'
envs_directory = config_directory / 'envs'
config_file = config_directory / 'config.yaml'

default_projects_directory = config_directory / 'projects'
default_wokspace_directory = config_directory / 'wokspace'
default_stack_name = 'gorunn'

# Docker Compose network subnet
subnet = "10.10.0.0/16"
# Database credentials
db_username = "gorunn"
db_password = "password"
db_root_password = "password"

# Template paths
base_dir = Path(__file__).parent
template_directory = base_dir / 'templates/'

docker_template_directory = template_directory / 'docker'
docker_compose_template = docker_template_directory / 'docker-compose.yaml.tmpl'
env_template = docker_template_directory / '.env.tmpl'

def load_config():
    """Load the main configuration file or return None if it doesn't exist."""
    if not os.path.exists(config_file):
        return None
        # else:
        #     styled_config_file = click.style(config_file, fg='red')
        #     styled_script = click.style("gorunn init", fg='green')
        #     styled_config_directory = click.style(config_directory, fg='red')
        #     click.echo(f'{styled_config_file} file not found !')
        #     click.echo(f"Either create {styled_config_file} in {styled_config_directory} or run {styled_script}")
        #     raise sys.exit()
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)

