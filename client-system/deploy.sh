#!/bin/bash

# 客户端系统部署脚本
# 用于将编译后的客户端系统部署到服务器

set -e

echo "================================"
echo "开始部署客户端系统..."
echo "================================"

# 配置变量
SERVER_HOST="qwquant.com"
SERVER_USER="root"
REMOTE_APP_DIR="/app/client-system"
REMOTE_NGINX_CONF_DIR="/etc/nginx/conf.d"
LOCAL_DIST_DIR="./dist"
DOMAIN="https://qwquant.com"

# 检查build目录是否存在
if [ ! -d "$LOCAL_DIST_DIR" ]; then
    echo "❌ dist目录不存在，请先运行 npm run build"
    exit 1
fi

echo "✓ 发现dist目录"

# 创建临时目录
TEMP_DIR=$(mktemp -d)
echo "✓ 创建临时目录: $TEMP_DIR"

# 复制dist文件到临时目录
cp -r "$LOCAL_DIST_DIR" "$TEMP_DIR/dist"
echo "✓ 复制dist文件到临时目录"

# 创建.env.example文件（用于服务器参考）
cat > "$TEMP_DIR/.env.example" << 'EOF'
# 客户端系统环境变量
# API基础URL（如果需要）
# VITE_API_URL=https://qwquant.com/api/v1
EOF

echo "✓ 创建.env.example文件"

# 创建Nginx配置文件
cat > "$TEMP_DIR/client-system.conf" << 'EOF'
# 客户端系统 Nginx配置
# 将此文件放在 /etc/nginx/conf.d/ 目录下

server {
    listen 80;
    server_name qwquant.com www.qwquant.com;

    # 客户端系统路由 - 访问 https://qwquant.com/client/ 时提供服务
    location /client/ {
        alias /app/client-system/dist/;

        # 配置SPA路由 - 所有非文件请求转发到index.html
        try_files $uri $uri/ /client/index.html;

        # 设置缓存策略
        # HTML文件不缓存
        location ~ \.html$ {
            add_header Cache-Control "no-cache, no-store, must-revalidate";
        }

        # 静态资源使用长期缓存
        location ~ \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # 如果需要在根路径直接访问客户端系统，使用以下配置：
    # location / {
    #     root /app/client-system/dist;
    #     try_files $uri $uri/ /index.html;
    # }

    # HTTPS配置（推荐）
    # listen 443 ssl http2;
    # ssl_certificate /path/to/ssl/cert.pem;
    # ssl_certificate_key /path/to/ssl/key.pem;
    # ssl_protocols TLSv1.2 TLSv1.3;
    # ssl_ciphers HIGH:!aNULL:!MD5;
}

# HTTP重定向到HTTPS（可选）
# server {
#     listen 80;
#     server_name qwquant.com www.qwquant.com;
#     return 301 https://$server_name$request_uri;
# }
EOF

echo "✓ 创建Nginx配置文件"

echo ""
echo "================================"
echo "部署方式："
echo "================================"
echo ""
echo "方式1: 使用SSH部署到远程服务器（自动）"
echo "   运行: bash deploy.sh [server_user] [server_host]"
echo "   例如: bash deploy.sh root qwquant.com"
echo ""
echo "方式2: 手动部署"
echo "   1. 将 $TEMP_DIR/dist 目录上传到服务器的 $REMOTE_APP_DIR/dist"
echo "   2. 将 $TEMP_DIR/client-system.conf 上传到 $REMOTE_NGINX_CONF_DIR/"
echo "   3. 在服务器上运行: nginx -t && systemctl reload nginx"
echo ""
echo "================================"
echo ""

# 如果提供了服务器参数，执行自动部署
if [ $# -eq 2 ]; then
    SERVER_USER=$1
    SERVER_HOST=$2

    echo "开始部署到 $SERVER_USER@$SERVER_HOST..."

    # 通过SSH创建远程目录
    echo "✓ 创建远程目录..."
    ssh "${SERVER_USER}@${SERVER_HOST}" "mkdir -p $REMOTE_APP_DIR"

    # 使用scp上传dist目录
    echo "✓ 上传dist目录..."
    scp -r "$TEMP_DIR/dist" "${SERVER_USER}@${SERVER_HOST}:${REMOTE_APP_DIR}/"

    # 上传Nginx配置
    echo "✓ 上传Nginx配置..."
    scp "$TEMP_DIR/client-system.conf" "${SERVER_USER}@${SERVER_HOST}:${REMOTE_NGINX_CONF_DIR}/"

    # 在远程服务器上测试和重加载Nginx
    echo "✓ 重加载Nginx..."
    ssh "${SERVER_USER}@${SERVER_HOST}" "nginx -t && systemctl reload nginx"

    echo ""
    echo "================================"
    echo "✓ 部署成功！"
    echo "================================"
    echo ""
    echo "客户端系统已部署到: $DOMAIN/client/"
    echo "确保后端API服务运行在: $DOMAIN/api/v1"
    echo ""
else
    echo "✓ 部署文件已准备好，位置: $TEMP_DIR"
    echo "✓ 请手动将文件上传到服务器，或运行带参数的脚本进行自动部署"
    echo ""
fi

# 清理临时文件
# 注意：如果是自动部署，临时文件会在本地保留用于参考
# 如果需要删除，可以手动运行: rm -rf $TEMP_DIR

echo "部署脚本执行完成！"
