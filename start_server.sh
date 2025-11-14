#!/bin/bash
# Start GymGem application with WebSocket support

echo "==========================================="
echo "  GymGem Application Startup Script"
echo "==========================================="
echo ""

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Virtual environment not activated!"
    echo "   Activating venv..."
    source venv/bin/activate
fi

echo "✓ Virtual environment: $VIRTUAL_ENV"
echo ""

# Check if Redis is running
if ! redis-cli ping &>/dev/null; then
    echo "⚠️  Redis is not running!"
    echo "   Starting Redis..."
    sudo systemctl start redis-server
    sleep 2
    
    if redis-cli ping &>/dev/null; then
        echo "✓ Redis started successfully"
    else
        echo "❌ Failed to start Redis. Please start manually:"
        echo "   sudo systemctl start redis-server"
        exit 1
    fi
else
    echo "✓ Redis is running"
fi

echo ""
echo "==========================================="
echo "  Starting Services"
echo "==========================================="
echo ""
echo "This will start:"
echo "  1. Daphne ASGI Server (port 8000) - HTTP + WebSocket"
echo "  2. Celery Worker - Background tasks"
echo "  3. Celery Beat - Scheduled tasks"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "==========================================="
    echo "  Shutting down services..."
    echo "==========================================="
    kill $DAPHNE_PID $WORKER_PID $BEAT_PID 2>/dev/null
    wait $DAPHNE_PID $WORKER_PID $BEAT_PID 2>/dev/null
    echo "✓ All services stopped"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start Daphne (ASGI server)
echo "▶ Starting Daphne ASGI Server..."
daphne -b 0.0.0.0 -p 8000 GymGem.asgi:application &
DAPHNE_PID=$!
echo "  PID: $DAPHNE_PID"
sleep 2

# Start Celery Worker
echo "▶ Starting Celery Worker..."
celery -A GymGem worker --loglevel=info &>/dev/null &
WORKER_PID=$!
echo "  PID: $WORKER_PID"

# Start Celery Beat
echo "▶ Starting Celery Beat..."
celery -A GymGem beat --loglevel=info &>/dev/null &
BEAT_PID=$!
echo "  PID: $BEAT_PID"

echo ""
echo "==========================================="
echo "  ✅ All Services Running!"
echo "==========================================="
echo ""
echo "Server Information:"
echo "  • HTTP API:     http://127.0.0.1:8000/"
echo "  • WebSocket:    ws://127.0.0.1:8000/ws/chat/{id}/?token={jwt}"
echo "  • Swagger UI:   http://127.0.0.1:8000/api/schema/swagger-ui/"
echo "  • Admin Panel:  http://127.0.0.1:8000/admin/"
echo ""
echo "Services:"
echo "  • Daphne (PID: $DAPHNE_PID) - ASGI Server"
echo "  • Worker (PID: $WORKER_PID) - Background tasks"
echo "  • Beat   (PID: $BEAT_PID) - Scheduled tasks"
echo ""
echo "Press Ctrl+C to stop all services"
echo "==========================================="

# Wait for all processes
wait $DAPHNE_PID $WORKER_PID $BEAT_PID
