#!/bin/bash

set -e

if [[ "$@" == "" ]]; then
    exec sh
elif [[ "$@" == "supervisord" ]]; then
    exec /usr/bin/supervisord -c /etc/supervisord.conf
else
    exec "$@"
fi
