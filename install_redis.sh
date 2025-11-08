#!/bin/bash

# Redis Installation and Setup Script for Django Channels
# Usage: bash install_redis.sh

set -e  # Exit on error

echo "🚀 Installing Redis for Django Channels..."
echo ""

# Update package list
echo "📦 Updating package list..."
sudo apt update

# Install Redis
echo "📥 Installing Redis Server..."
sudo apt install redis-server -y

# Start Redis
echo "▶️  Starting Redis service..."
sudo systemctl start redis-server

# Enable Redis on boot
echo "🔄 Enabling Redis to start on boot..."
sudo systemctl enable redis-server

# Wait a moment for Redis to start
sleep 2

# Test Redis
echo "🧪 Testing Redis connection..."
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is running successfully!"
    echo ""
    redis-cli ping
else
    echo "❌ Redis connection test failed"
    echo "Check status with: sudo systemctl status redis-server"
    exit 1
fi

# Show Redis info
echo ""
echo "📊 Redis Information:"
redis-cli info server | grep redis_version
redis-cli info memory | grep used_memory_human

# Show status
echo ""
echo "🔍 Redis Service Status:"
sudo systemctl status redis-server --no-pager | head -n 10

echo ""
echo "✅ Redis setup complete!"
echo ""
echo "Next steps:"
echo "  1. Test with Django: python manage.py shell"
echo "  2. Run: from channels.layers import get_channel_layer"
echo "  3. Run: get_channel_layer()"
echo ""
echo "To manage Redis:"
echo "  - Start:   sudo systemctl start redis-server"
echo "  - Stop:    sudo systemctl stop redis-server"
echo "  - Restart: sudo systemctl restart redis-server"
echo "  - Status:  sudo systemctl status redis-server"
echo "  - Monitor: redis-cli monitor"
