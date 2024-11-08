#!/bin/bash

set -e

XDEBUG_ON=${XDEBUG_ON:=false}

if $XDEBUG_ON; then
    dockerize -template /templates/php/xdebug.ini:/usr/local/etc/php/conf.d/xdebug.ini;
    docker-php-ext-enable xdebug
fi

start_command=$(yq e '.start_command' /projects/$application_name.yaml)
if [ -z "$start_command" ] || [ "$start_command" = "null" ]; then
    start_command="tail -f /dev/null"
fi

echo "Starting with $start_command"
eval "$start_command"
