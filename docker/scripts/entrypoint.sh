#!/bin/sh

# Wait for PostgreSQL
echo "Waiting for PostgreSQL..."
while ! nc -z db 5432; do
    sleep 0.1
done
echo "PostgreSQL started"

# Wait for Redis
echo "Waiting for Redis..."
while ! nc -z redis 6379; do
    sleep 0.1
done
echo "Redis started"

# Create media directory if it doesn't exist
mkdir -p /app/media

# Run database migrations
flask db upgrade

# Create admin user if it doesn't exist
flask create-admin

# Start Gunicorn server
exec gunicorn --bind 0.0.0.0:5000 \
    --workers 4 \
    --worker-class eventlet \
    --access-logfile - \
    --error-logfile - \
    flask_backend.run:app 