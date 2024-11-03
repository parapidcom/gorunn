#!/bin/bash

# Ensure the script stops on error
set -e

# Check if supervisord is available; install it if it isn't
if ! command -v supervisord >/dev/null 2>&1; then
    apk add --no-cache supervisor
fi

# Setup Python virtual environment if it doesn't exist
if [[ ! -d ".venv" ]]; then
    python3 -m venv .venv
    source .venv/bin/activate
else
    source .venv/bin/activate
fi

if [[ "$@" = "supervisord" ]]; then
    if command -v supervisord >/dev/null 2>&1; then
        exec /usr/bin/supervisord -c /etc/supervisord.conf
    else
        # Supervisord not installed for some reason, starting without it
        exec /scripts/server.sh
    fi
elif [[ "$@" = "bash" ]]; then
    # Ensure we're running bash if available, and activate the virtual environment
    if command -v bash >/dev/null 2>&1; then
        exec bash --init-file <(echo "source .venv/bin/activate")
    else
        exec sh
    fi
else
    exec "$@"
fi
