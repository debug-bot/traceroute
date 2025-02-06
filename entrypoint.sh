#!/bin/sh
set -e

echo "Running Django migrations..."
python manage.py migrate

echo "Creating default superuser..."
python manage.py create_default_superuser

echo "Populating random router data..."
python manage.py populate_random_router_data

echo "Populating commands data..."
python manage.py populate_commands_data

echo "Executing popular command: Run Ping..."
python manage.py execute_popular_command "Run Ping"

echo "Executing popular command: Run Traceroute..."
python manage.py execute_popular_command "Run Traceroute"

# Finally, execute the CMD passed to the container (i.e., start Gunicorn)
exec "$@"
