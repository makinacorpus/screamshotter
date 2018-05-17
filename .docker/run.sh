#!/bin/bash
SECRET_KEY=${SECRET_KEY:-paranoid}
ALLOWED_HOSTS=${ALLOWED_HOSTS:-*}
DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-screamshotter.settings}

APP_ROOT=/opt/apps/screamshotter
WSGI=screamshotter.wsgi

cd $APP_ROOT

bin/gunicorn \
    $WSGI:application \
    --workers 4 \
    --bind 0.0.0.0:8000 \
    --max-requests 5000