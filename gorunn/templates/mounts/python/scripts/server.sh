#!/bin/bash

set -e

start_command=$(yq e '.start_command' /projects/$application_name.yaml)
echo "Starting with $start_command"
source .venv/bin/activate
eval "$start_command"
