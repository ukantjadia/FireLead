#!/bin/bash

# Wait for any initialization tasks to complete
echo "Starting FireLead application..."

# Run database migrations if needed
# python manage.py db upgrade

# Start the Flask application
# exec flask run --host=0.0.0.0 --port=5000 
exec gunicorn -b 0.0.0.0:8000 run:app