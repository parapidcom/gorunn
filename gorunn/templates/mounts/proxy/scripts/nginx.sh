#!/bin/bash

set -e

COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME:="gorunn"}
mkdir -p /var/www/ && touch /var/www/index.html
echo "Generating main nginx.conf from template..."
dockerize -template /templates/nginx.ctmpl:/usr/local/openresty/nginx/conf/nginx.conf
rm -fr /etc/nginx/conf.d/*

for project in /projects/*.yaml; do
  # Skip iteration if no .yaml files are found
  [ -f "$project" ] || continue
  app=$(basename "$project" .yaml)

  # Use `yq` to extract values directly from the YAML file
  export name=$(yq e '.name' "$project")
  export type=$(yq e '.type' "$project")
  export endpoint=$(yq e '.endpoint' "$project")
  export server=$(yq e '.server' "$project")
  export listen_port=$(yq e '.listen_port' "$project")
  export project=${COMPOSE_PROJECT_NAME}


  if [ -n "$endpoint" ]; then
    echo "Generating $app from template..."
    # Ensure the platform-specific template exists before trying to use it
    if [ -f "/templates/$type.ctmpl" ]; then
      dockerize -template "/templates/$type.ctmpl:/etc/nginx/conf.d/$app.conf"
    else
      echo "Template for platform $type not found."
    fi
  fi
done

exec nginx -g 'daemon off;'
