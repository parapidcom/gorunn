#!/bin/bash

# Ensure the script stops on error
set -e

if [[ "$@" = "" ]]; then
    sh
elif [[ "$@" = "supervisord" ]]; then
    exec /usr/bin/supervisord -c /etc/supervisord.conf
else
    exec "$@"
fi
