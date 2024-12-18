<p align="center">
  <img src="logo.png" alt="Gorunn Logo">
</p>

**Gorunn** is a powerful CLI tool for managing local development environments with Docker. It provides a streamlined way to manage multiple projects, handle environment configurations, and orchestrate various services.
![Gorunn Init](init.gif)

Website: https://gorunn.io

## Minimum Requirements:
- Python 3.10+
- [Pipx](https://github.com/pypa/pipx)
- Docker and Docker Compose
- OS:
  - MacOS (Tested on Sequoia 15.0.1)
  - Ubuntu (tested on 24.04)

## Supported languages
- Python
- Node.js / Next.js
- PHP

## Installation

```bash
pipx install gorunn
```

## Quick Start

### Initialize the stack
1. Prepare project manifest by following the [example](https://github.com/parapidcom/gorunn-project-manifests) structure.

2. Initialize the stack and follow the prompts:
```bash
gorunn init
```

When you run gorunn init, you'll be prompted to configure:
- **Stack name** (default: **gorunn**). This will be used as a prefix for all the services.
- **Projects repository URL** (optional). If you have one.
- **Projects local path**. This is where your project manifests will be stored.
- **Workspace path**. This is where your application local directory will be created or cloned.
- **Docker network subnet**. This is the subnet for the Docker network. Leave empty to use default if you don't know what it is, change only in case you have conflict with your existing docker compose network subnet.
- **Service selection** (MySQL, Postgres, Redis, Memcached, Kafka, Chroma, OpenSearch,RabbitMQ, MongoDB). These are the services you want to use.
- **Encryption key for environment variables**. This is the key used to encrypt your environment variables so that you can safely push them to repo together with project manifests.
- **Aider AI assistant**. You will be prompted to enable [Aider](https://aider.chat) AI assistant for your project. If you want to use it, prepare your OpenAI API or Anthropic API key.
You can specify project manifest directory as an option:

```bash
gorunn init --parse --import /path/to/your/projects-manifests
```

or you can specify project manifest repository URL if you have one:

```bash
gorunn init --parse --import git@github.com:yourorg/projects-manifests.git
```

#### Example Stack
Optionally you can use our example project stack with `react`, `laravel` and `django` projects:
```bash
gorunn init --import https://github.com/parapidcom/gorunn-project-manifests.git
```
### Parse the project manifests
```bash
gorunn parse
```
### Build the projects
This command will iterate over build_commands defined in the project manifests and run them inside containers.
You can build all projects:
```bash
gorunn build --app all
```

or specific one:

```bash
gorunn build --app myapp
```

## Configuration

### Main configuration

#### Location
```
$HOME/.config/gorunn/
├── config.yaml           # Main configuration generated by `gorunn init`
```
#### Structure
```yaml
aider: (enable Aider AI assistant for the stack)
  api_key: your_llm_api_key
  enabled: true|false
  llm: OpenAI|Claude
services: (enable one or more services for the stack)
  chroma: true|false
  mysql: true|false
  opensearch: true|false
  postgres: true|false
  redis: true|false
  kafka: true|false
  memcached: true|false
  rabbitmq: true|false
  mongo: true|false
docker_compose_subnet: 10.10.0.0/16 (leave as is if you don't know what it is)
encryption_key: generated by `gorunn init` on first run
projects:
  path: /absolute/path/to/projects/manifests (default: $HOME/gorunn/projects)
  repo_url: git@github.com:parapidcom/gorunn-project-manifests.git (repo to your project manifests, defining local stack)
stack_name: stack_name (default: gorunn) - no spaces or special characters, lowercase. This will be used as a prefix for all the services.
workspace_path: /absolute/path/to/workspace (default: $HOME/gorunn/workspace) - this is where your project local directories will be created or cloned
```

### Project Manifests and Environment files
A project manifest in **Gorunn** is a YAML file that defines the configuration for a project that is part of the stack. Example can be found in the [example stack](https://github.com/parapidcom/gorunn-project-manifests).
#### Location
```
$HOME/gorunn/
├── myreact.yaml            # Project manifest for the myreact app
├── mydjango.yaml           # Project manifest for the mydjango app
├── env/
├─── myreact.env         # Environment files for the myreact app
├─── mydjango.env         # Environment files for the mydjango app
```

#### Structure

- **git_repo**: git@github.com:parapidcom/gorunn-example-react (git repository url of the project)
- **type**: node (type of the project, one of: node, php, python)
- **version**: "20" (version of the platform being used, e.g. node version, php version, python version)
- **endpoint**: myreact.local.gorunn.io (optional, if defined, the CLI will create a virtual host on the local proxy for it. The endpoint must be in the form of `%s.local.gorunn.io`)
- **env_vars**: true (boolean, if true, the CLI will load it from manifests directory (if it does not exist, it will create a new file from a template))
- **start_command**: npm run dev (command used to start the server)
- **listen_port**: 3000 (port on which your local server will listen, allowing the proxy to forward to it as upstream)
- **build_commands**: (list of commands necessary for project bootstrap. These are called with the `gorunn build --app app_name` command)


## Project Manifests and Environment Files Location
Project manifests locations defaults to `$HOME/gorunn/projects/` during `gorunn init`.
Can be manually changed in the main configuration file.


### Environment Variables
Environment files are part of the project manifests directory structure. They are stored in `env/` subdir of the project manifests directory.


#### Encrypt an environment file
```bash
gorunn projects env --encrypt --app myapp
```

#### Decrypt an environment file
```bash
gorunn projects env --decrypt --app myapp
```

### Project Management Commands

#### Pull latest project manifests from remote repository
```bash
gorunn projects pull
```

#### Push project manifests and environment files changes to remote repository
```bash
gorunn projects publish
```

#### Show stack projects information
```bash
gorunn info
```

### Build Commands
#### Build all projects defined in the project manifests directory
```bash
gorunn build --app all
```

#### Build specific project
```bash
gorunn build --app myapp
```

### Container Management

#### Start containers
```bash
gorunn start [--app APP_NAME]
```

#### Stop containers
```bash
gorunn stop [--app APP_NAME]
```

#### Restart containers
```bash
gorunn restart [--app APP_NAME]
```

#### Stream logs
```bash
gorunn logs [--app APP_NAME] [--follow]
```

#### Access terminal
```bash
gorunn terminal --app APP_NAME
```

#### Aider AI assistant
You can use [Aider](https://aider.chat) to help you with your project if you have enabled it and provided your LLM API key.
```bash
gorunn aider --app APP_NAME --browser
```
This will start Aider in browser mode and you can use it to help you code in browser on http://localhost:8501

### Info
Print information about the stack.
```bash
gorunn info
```

### Version
Print currently installed **Gorunn** version.
```bash
gorunn version
```

#### Trust
On MacOS, you can add the **Gorunn**'s self signed certificate for `*.local.gorunn.io domain` to keychain.
It is done automatically during `gorunn init`.

```bash
gorunn trust
```

## Best Practices

### Project Manifests
- Keep manifests in version control
- Use consistent naming conventions

### Environment Variables
  - Always use encryption for sensitive data
  - Keep backup of encryption keys
  - Use separate env files per environment

### Resource Management
  - Stop unused services to free resources
  - Regular cleanup using gorunn destroy
  - Monitor container logs for issues
