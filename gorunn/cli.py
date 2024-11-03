import click
from gorunn.commands import (init,
                             start,
                             stop,
                             restart,
                             terminal,
                             build,
                             destroy,
                             parse,
                             logs,
                             docker_exec,
                             trust, info,
                             projects,
                             version,
                             aider)

@click.group()
def cli():
    """A CLI tool to manage local environment."""
    pass

cli.add_command(init.init)
cli.add_command(start.start)
cli.add_command(stop.stop)
cli.add_command(destroy.destroy)
cli.add_command(restart.restart)
cli.add_command(terminal.terminal)
cli.add_command(build.build)
cli.add_command(parse.parse)
cli.add_command(logs.logs)
cli.add_command(docker_exec.docker_exec)
cli.add_command(trust.trust)
cli.add_command(info.info)
cli.add_command(projects.projects)
cli.add_command(version.version)
cli.add_command(aider.aider)

if __name__ == '__main__':
    cli()
