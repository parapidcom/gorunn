#!/bin/bash

# Ensure the script stops on error
set -e

# Check if supervisord is available; install it if it isn't
if ! command -v supervisord >/dev/null 2>&1; then
    apk add --no-cache supervisor
fi

if [[ "$@" = "" ]]; then
    exec bash
elif [[ "$@" = "supervisord" ]]; then
    exec /usr/bin/supervisord -c /etc/supervisord.conf
else
    exec "$@"
fi
