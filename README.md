# Gorunn CLI

## Usage

- **gorunn --help** will show you all available commands
- **gorunn info** will show status of the current projects and its containers

tbd


## Configfurations

All params are available in container as environment variables.
- *Environment file is located in your `~/gorunn/envs/`. Feel free to edit it to your liking*
- *CLI generates **Dockerfile.gorunn** in project repo. You can commit that file and update it as per need with additional packages. It is used to build local image.

Services are accessible
- **mysql**:
  user(DB_USERNAME): gorunn
  password(DB_PASSWORD): password
  container_port: 3306
  forwarded_port: 13306
- **postgresql**:
  user(DB_USERNAME): gorunn
  password(DB_PASSWORD): password
  container_port: 5432
  forwarded_port: 15432
- **redis**
  container_port: 6379
  forwarded_port: 16379
- **opensearch**
  host_port: 9200
- forwarded_port: 19200
- **chroma**:
  host_port: 8000
- forwarded_port: 18000