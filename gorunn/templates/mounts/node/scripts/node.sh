#!/bin/bash

set -e

# Use `yq` to extract values directly from the YAML file
export start_command=$(yq e '.start_command' /projects/$application_name.yaml)
echo "Starting with command $start_command"
eval "$start_command"