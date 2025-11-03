#!/bin/bash

# 此脚本在服务器上运行，用于更新 Nginx 配置

SERVER_IP="82.157.28.35"
SERVER_USER="ubuntu"
SERVER_PASSWORD="chen_188_8_8"

echo "更新服务器 Nginx 配置..."

sshpass -p "${SERVER_PASSWORD}" ssh -o StrictHostKeyChecking=no \
    ${SERVER_USER}@${SERVER_IP} << 'NGINX_UPDATE'

# 创建新的 Nginx 配置
sudo tee /etc/nginx/sites-available/default > /dev/null << 'NGINX_CONFIG'
##
# Stock Analysis System - Frontend + Backend
#

server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name www.qwquant.com qwquant.com;

    # Redirect all HTTP to HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2 default_server;
    listen [::]:443 ssl http2 default_server;

    server_name www.qwquant.com qwquant.com;

    # Tencent Cloud SSL Certificate
    ssl_certificate /etc/letsencrypt/live/www.qwquant.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/www.qwquant.com/privkey.pem;

    # SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Frontend - React SPA
    root /opt/stock-analysis-system/frontend/dist;
    index index.html;

    # API Backend
    location /api/v1/ {
        proxy_pass http://127.0.0.1:3007;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;

        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Frontend SPA fallback
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Static files cache
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
NGINX_CONFIG

# Test Nginx configuration
echo "测试 Nginx 配置..."
if sudo nginx -t; then
    echo "✅ Nginx 配置正确"

    # Reload Nginx
    echo "重新加载 Nginx..."
    sudo systemctl reload nginx
    echo "✅ Nginx 已重新加载"
else
    echo "❌ Nginx 配置有错误，请检查"
    exit 1
fi

NGINX_UPDATE

echo "✅ Nginx 配置更新完成"
