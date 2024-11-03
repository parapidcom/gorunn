import os
import subprocess
import click
import yaml
from pathlib import Path
from gorunn.config import config_file, aider_image, load_config

@click.command(context_settings=dict(ignore_unknown_options=True, allow_extra_args=True))
@click.option('--app', required=True, help='The application where you want to run AI engineer.')
@click.option('--browser', is_flag=True, help='Enable browser mode')
@click.option('--no-browser', is_flag=True, help='Disable browser mode')
@click.option('--port', default=8501, help='Port to run the application on')
@click.pass_context
def aider(ctx, app, browser, no_browser, port):
    """Run the Aider AI engineer."""
    config = load_config()
    workspace_path = Path(config['workspace_path'])
    aider_enabled = config['aider']['enabled']
    aider_llm = config['aider']['llm']
    llm_api_key = config['aider']['api_key']
    if aider_enabled and aider_llm and llm_api_key:
        # set llm api key environment variable name based on the main config aider.llm param
        if aider_llm == "openai":
            env_name='OPENAI_API_KEY'
        else:
            env_name='CLAUDE_API_KEY'
        repo_path = (Path(workspace_path) / app).resolve()
        home_directory = os.path.expanduser('~')
        docker_command = [
            "docker", "run", "--rm", "-it",
            "-v", f"{repo_path}:/app",
            "-p", f"{port}:{port}",
            "-v", f"{home_directory}/.gitconfig:/root/.gitconfig",
        ]

        # Add environment variables to the command
        docker_command.extend(["--workdir", "/app"])



        docker_command.extend(["-e", f"{env_name}={llm_api_key}"])
        docker_command.extend([
            aider_image]
        )

        # Handle browser flag
        if browser:
            docker_command.append("--browser")
        elif no_browser:
            docker_command.append("--no-browser")

        # Filter out our script's arguments and pass the rest to the Docker container
        aider_args = [arg for arg in ctx.args if
                      arg not in ('--app', app, '--browser', '--no-browser', '--port', str(port))]
        docker_command.extend(aider_args)

        # Execute Docker run command
        click.echo(f"Starting aider for {app}...")
        subprocess.run(docker_command)
    else:
        click.echo(click.style("Aider is not configured yet!", fg='red'))
        click.echo(click.style("Enable it and provide LLM api keys in main config.yaml.", fg='yellow'))

if __name__ == "__main__":
    aider()
