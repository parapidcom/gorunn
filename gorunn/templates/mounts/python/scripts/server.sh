#!/bin/bash

set -e

start_command=$(yq e '.start_command' /projects/$application_name.yaml)
if [ -z "$start_command" ] || [ "$start_command" = "null" ]; then
    start_command="tail -f /dev/null"
fi

echo "Starting with $start_command"
source .venv/bin/activate
eval "$start_command"
