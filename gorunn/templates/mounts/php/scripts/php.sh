#!/bin/bash

set -e

XDEBUG_ON=${XDEBUG_ON:=false}

if $XDEBUG_ON; then
    dockerize -template /templates/php/xdebug.ini:/usr/local/etc/php/conf.d/xdebug.ini;
    docker-php-ext-enable xdebug
fi


start_command=$(yq e '.start_command' /projects/$application_name.yaml)
echo "Starting $start_command as defined in project config"
eval "$start_command"

