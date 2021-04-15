#!/usr/bin/env bash

cd /app/src || exit

# Activate venv
. /app/venv/bin/activate

# exec
exec "$@"
