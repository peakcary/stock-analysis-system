#!/bin/bash

set -e

# 🎯 Production Nginx 部署脚本
# 该脚本用于启动完整的生产环境，包括Nginx反向代理和HTTPS

echo "🚀 开始部署完整的生产系统..."
echo ""

# 配置
DOMAIN="qwquant.com"
ENV_FILE=".env.prod"
COMPOSE_FILE="docker-compose.prod.complete.yml"
CERT_PATH="/etc/letsencrypt/live/${DOMAIN}"

# ============================================
# 第1步：检查必要的文件和配置
# ============================================
echo "✅ 第1步：检查必要的文件..."
echo ""

check_file() {
    if [ ! -f "$1" ]; then
        echo "❌ 错误：找不到文件 $1"
        exit 1
    fi
    echo "  ✓ $1"
}

check_file "$ENV_FILE"
check_file "$COMPOSE_FILE"
check_file "nginx/nginx.prod.conf"
check_file "backend/requirements.txt"

# 检查证书（如果是生产环境，证书应该已经存在）
if [ ! -d "$CERT_PATH" ]; then
    echo "⚠️  警告：SSL证书不存在于 $CERT_PATH"
    echo "  将继续部署，但HTTPS可能无法工作"
    echo ""
fi

# ============================================
# 第2步：验证环境变量
# ============================================
echo "✅ 第2步：验证环境变量..."
echo ""

source "$ENV_FILE"

# 检查必要的环境变量
required_vars=(
    "DOMAIN"
    "MYSQL_ROOT_PASSWORD"
    "MYSQL_PASSWORD"
    "REDIS_PASSWORD"
    "SECRET_KEY"
    "ADMIN_SECRET_KEY"
)

for var in "${required_vars[@]}"; do
    value=$(eval echo "\$$var")
    if [ -z "$value" ]; then
        echo "❌ 错误：缺少环境变量 $var"
        exit 1
    fi
    echo "  ✓ $var 已配置"
done

# ============================================
# 第3步：停止旧的容器（如果存在）
# ============================================
echo ""
echo "✅ 第3步：停止旧的容器..."
echo ""

# 先尝试停止旧的compose文件中的容器
if docker-compose -f docker-compose.prod.working.yml ps 2>/dev/null | grep -q "stock_"; then
    echo "  停止旧的服务..."
    docker-compose -f docker-compose.prod.working.yml down -v 2>/dev/null || true
    sleep 5
fi

# ============================================
# 第4步：启动完整的生产系统
# ============================================
echo ""
echo "✅ 第4步：启动完整的生产系统..."
echo "  这可能需要5-10分钟来构建镜像"
echo ""

# 启动所有服务
docker-compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d --build

# 等待服务启动
echo ""
echo "⏳ 等待所有服务启动（120秒）..."
sleep 120

# ============================================
# 第5步：验证服务状态
# ============================================
echo ""
echo "✅ 第5步：验证服务状态..."
echo ""

docker-compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" ps

echo ""
echo "🔍 详细的服务检查："
echo ""

# 检查MySQL
echo -n "  MySQL: "
if docker-compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T mysql mysqladmin ping -h localhost -u "${MYSQL_USER}" -p"${MYSQL_PASSWORD}" > /dev/null 2>&1; then
    echo "✅ 运行中"
else
    echo "❌ 无法连接"
fi

# 检查Redis
echo -n "  Redis: "
if docker-compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T redis redis-cli -a "${REDIS_PASSWORD}" ping > /dev/null 2>&1; then
    echo "✅ 运行中"
else
    echo "❌ 无法连接"
fi

# 检查Backend
echo -n "  Backend: "
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ 运行中"
else
    echo "❌ 无法连接"
fi

# 检查Nginx
echo -n "  Nginx: "
if curl -s http://localhost/nginx-health > /dev/null 2>&1; then
    echo "✅ 运行中"
else
    echo "❌ 无法连接（可能是证书问题或配置问题）"
fi

# ============================================
# 第6步：测试HTTP重定向
# ============================================
echo ""
echo "✅ 第6步：测试HTTP重定向和HTTPS..."
echo ""

echo "  测试 HTTP -> HTTPS 重定向:"
HTTP_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -L http://localhost/)
if [ "$HTTP_RESPONSE" == "200" ] || [ "$HTTP_RESPONSE" == "301" ]; then
    echo "    ✅ HTTP 响应正常"
else
    echo "    ⚠️  HTTP 响应码: $HTTP_RESPONSE"
fi

echo ""
echo "  测试 HTTPS:"
if curl -k -s https://localhost/nginx-health > /dev/null 2>&1; then
    echo "    ✅ HTTPS 响应正常"
else
    echo "    ⚠️  HTTPS 可能存在问题"
fi

# ============================================
# 第7步：显示部署摘要
# ============================================
echo ""
echo "════════════════════════════════════════════════"
echo "✅ 部署完成！"
echo "════════════════════════════════════════════════"
echo ""
echo "📋 部署摘要："
echo "  域名: https://${DOMAIN}"
echo "  后端地址: http://localhost:8000"
echo "  API地址: https://${DOMAIN}/api"
echo ""
echo "📊 服务状态:"
docker-compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" ps | tail -n +2 | awk '{print "  " $0}'
echo ""
echo "📝 实时日志 (Nginx):"
echo "  docker-compose -f $COMPOSE_FILE logs -f nginx"
echo ""
echo "📝 实时日志 (Backend):"
echo "  docker-compose -f $COMPOSE_FILE logs -f backend"
echo ""
echo "📝 查看所有日志:"
echo "  docker-compose -f $COMPOSE_FILE logs"
echo ""
echo "🔐 SSL证书位置:"
echo "  $CERT_PATH"
echo ""
echo "⚙️  下一步操作:"
echo "  1. 访问 https://${DOMAIN} 检查是否正常工作"
echo "  2. 检查 API: https://${DOMAIN}/api/v1/health"
echo "  3. 配置WeChat支付回调 (参考 PRODUCTION_DEPLOYMENT.md)"
echo "  4. 运行支付测试"
echo ""

# ============================================
# 第8步：配置证书自动续期
# ============================================
echo "✅ 第8步：配置证书自动续期..."
echo ""

# 设置定期检查证书是否需要续期
setup_cert_renewal() {
    local renewal_script="/usr/local/bin/renew-certs.sh"

    # 创建续期脚本
    sudo tee "$renewal_script" > /dev/null <<'EOF'
#!/bin/bash
set -e

echo "🔄 检查SSL证书是否需要续期..."

# 尝试续期所有证书
certbot renew --quiet --no-eff-email

# 如果成功续期，重启Nginx
if [ $? -eq 0 ]; then
    echo "✅ 证书续期完成或不需要续期"

    # 检查是否有新证书
    if certbot renew --dry-run --quiet 2>/dev/null | grep -q "cert"; then
        echo "🔄 重启Nginx以加载新证书..."
        docker-compose -f /opt/stock-analysis-system/docker-compose.prod.complete.yml restart nginx
    fi
fi
EOF

    sudo chmod +x "$renewal_script"

    # 添加到crontab（每天凌晨2点运行）
    (crontab -l 2>/dev/null; echo "0 2 * * * $renewal_script") | crontab -

    echo "  ✓ 证书自动续期已配置 (每天凌晨2点检查)"
}

if [ -x "$(command -v certbot)" ]; then
    setup_cert_renewal
else
    echo "  ⚠️  certbot未安装，请手动配置证书续期"
fi

echo ""
echo "✅ 所有步骤完成！"
echo ""
