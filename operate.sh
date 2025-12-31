#!/usr/bin/env bash

echo "🚀 Starting GymGem services..."

Activate virtualenv
source venv/bin/activate

Environment
export DJANGO_SETTINGS_MODULE=GymGem.settings
export PYTHONUNBUFFERED=1

Start Redis
echo "🔴 Starting Redis..."
redis-server --daemonize yes

sleep 2

Start Daphne
echo "🌐 Starting Daphne..."
daphne -b 0.0.0.0 -p 8000 GymGem.asgi:application &
DAPHNE_PID=$!

sleep 2

Start Celery Worker
echo "⚙️ Starting Celery Worker..."
celery -A GymGem worker -l info &
WORKER_PID=$!

sleep 2

Start Celery Beat
echo "⏱ Starting Celery Beat..."
celery -A GymGem beat -l info &
BEAT_PID=$!

echo ""
echo "✅ All services are running!"
echo "Daphne PID: $DAPHNE_PID"
echo "Worker PID: $WORKER_PID"
echo "Beat PID:   $BEAT_PID"

Wait for all
wait