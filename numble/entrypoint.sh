#!/bin/bash

# echo "Copy all files from static folders into the STATIC_ROOT directory"
# python manage.py collectstatic --noinput

# echo "Apply database migrations"
# python manage.py migrate --noinput

echo "Starting the server"
newrelic-admin run-program gunicorn 'numble.wsgi' --bind=0.0.0.0:8000
