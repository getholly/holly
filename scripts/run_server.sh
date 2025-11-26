#!/bin/bash

echo Starting server at `date`
cd /app
source .venv/bin/activate
cd /app/githubme
python manage.py tailwind install
python manage.py tailwind build
python manage.py collectstatic --noinput
python manage.py compress --force
python manage.py collectstatic --noinput
python manage.py migrate
echo Done at `date`
uvicorn config.asgi:application --workers 4 --port 8181 --host 0.0.0.0
