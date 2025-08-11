#!/bin/bash

# Start RTMP Server for Glasses Stream
echo "=== RTMP Server Setup ==="
echo

# Check if nginx with RTMP is installed
if ! command -v nginx &> /dev/null; then
    echo "❌ nginx not found. Installing nginx with RTMP module..."
    brew install nginx
    echo
fi

# Create nginx config for RTMP
NGINX_CONF="/usr/local/etc/nginx/nginx.conf"
NGINX_BACKUP="/usr/local/etc/nginx/nginx.conf.backup"

# Check if we need to add RTMP config
if ! grep -q "rtmp {" "$NGINX_CONF" 2>/dev/null; then
    echo "📝 Adding RTMP configuration to nginx..."
    
    # Backup original
    sudo cp "$NGINX_CONF" "$NGINX_BACKUP" 2>/dev/null || true
    
    # Add RTMP config
    cat << 'EOF' | sudo tee -a "$NGINX_CONF" > /dev/null

# RTMP Configuration
rtmp {
    server {
        listen 1935;
        chunk_size 4096;
        
        application live {
            live on;
            record off;
            
            # Allow publish from localhost only
            allow publish 127.0.0.1;
            deny publish all;
            
            # Allow play from anywhere
            allow play all;
        }
    }
}
EOF
    echo "✅ RTMP config added"
fi

# Start nginx
echo "🚀 Starting nginx with RTMP..."
sudo nginx -s stop 2>/dev/null || true
sleep 1
sudo nginx

echo
echo "✅ RTMP Server running!"
echo
echo "Stream URLs:"
echo "  📤 Publish to: rtmp://localhost/live/stream"
echo "  📺 Watch at:   rtmp://localhost/live/stream"
echo
echo "Test with:"
echo "  ffplay rtmp://localhost/live/stream"
echo
echo "Stop server with: sudo nginx -s stop"