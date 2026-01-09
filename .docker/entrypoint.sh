#!/usr/bin/env bash

cd /opt/screamshotter/src || exit

# Activate venv
. /opt/venv/bin/activate

if [ "$COLLECTSTATIC" == "1" ]
then
  echo "Collect staticfiles"
  ./manage.py collectstatic --no-input
fi;

# exec
exec "$@"
