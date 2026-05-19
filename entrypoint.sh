#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

echo "Running Migrations..."
python manage.py migrate --noinput

echo "Seeding MVP Data..."
# This command is idempotent in our implementation (uses update_or_create)
python manage.py seed_mvp_data

echo "Collecting Static Files..."
python manage.py collectstatic --noinput

echo "Starting Gunicorn Server..."
# Bind to the port provided by Render (default is 10000)
exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-10000} --workers 3
