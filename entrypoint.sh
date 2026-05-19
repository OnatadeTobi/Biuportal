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
# Optimized for Render Free Tier:
# - Increased timeout to 120s to prevent SIGKILL during heavy tasks (like student lookup)
# - Reduced workers to 2 to stay within memory limits (512MB)
exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-10000} --workers 2 --timeout 120 --log-level info
