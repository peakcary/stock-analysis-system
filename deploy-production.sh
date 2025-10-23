#!/bin/bash
# ===================================
# 生产环境部署脚本（增强版）
# Production Deployment Script
# 读取 .env.prod 的 DOMAIN/EMAIL 等配置
# 可选非交互模式：--yes
# ===================================

set -euo pipefail

# 读取 .env.prod 中的配置（如果存在）
if [ -f .env.prod ]; then
  # shellcheck source=/dev/null
  export $(grep -E '^(DOMAIN|EMAIL)=' .env.prod | xargs -0 -I{} echo {}) || true
fi

DOMAIN=${DOMAIN:-qwquant.com}
EMAIL=${EMAIL:-admin@${DOMAIN}}

# 非交互开关
NON_INTERACTIVE=false
if [[ "${1:-}" == "--yes" || "${1:-}" == "-y" ]]; then
  NON_INTERACTIVE=true
fi

# 选择 docker compose 命令
if command -v docker-compose >/dev/null 2>&1; then
  COMPOSE="docker-compose"
elif docker compose version >/dev/null 2>&1; then
  COMPOSE="docker compose"
else
  echo "❌ 未找到 docker-compose 或 docker compose"
  exit 1
fi

echo "🚀 开始部署到生产环境 (${DOMAIN})"
echo "======================================"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查是否在项目根目录
if [ ! -f "docker-compose.prod.yml" ]; then
    echo -e "${RED}❌ 错误: 请在项目根目录运行此脚本${NC}"
    exit 1
fi

# 1. 检查必要文件
echo -e "\n${YELLOW}📋 步骤 1/8: 检查必要文件...${NC}"
if [ ! -f ".env.prod" ]; then
    echo -e "${RED}❌ 缺少 .env.prod 文件${NC}"
    echo "请先复制 .env.prod.example 并填写配置"
    exit 1
fi

if [ ! -f "backend/.env.production" ]; then
    echo -e "${RED}❌ 缺少 backend/.env.production 文件${NC}"
    exit 1
fi

if [ ! -f "backend/certs/apiclient_cert.pem" ] || [ ! -f "backend/certs/apiclient_key.pem" ]; then
    echo -e "${RED}❌ 缺少微信支付证书文件${NC}"
    echo "请将证书文件放在 backend/certs/ 目录下"
    exit 1
fi
echo -e "${GREEN}✅ 必要文件检查通过${NC}"

# 2. 检查域名解析
echo -e "\n${YELLOW}📋 步骤 2/8: 检查域名解析...${NC}"
DOMAIN_IP=$(dig +short "$DOMAIN" | head -n 1)
SERVER_IP=$(curl -s ifconfig.me)

if [ -z "$DOMAIN_IP" ]; then
    echo -e "${RED}❌ 域名 $DOMAIN 未解析${NC}"
    echo "请先在DNS设置中添加A记录指向服务器IP: $SERVER_IP"
    exit 1
fi

echo "域名 $DOMAIN 解析到: $DOMAIN_IP"
echo "服务器公网IP: $SERVER_IP"

if [ "$DOMAIN_IP" != "$SERVER_IP" ]; then
    echo -e "${YELLOW}⚠️  警告: 域名解析IP与服务器IP不一致${NC}"
    if ! $NON_INTERACTIVE; then
      read -p "是否继续部署? (y/n) " -n 1 -r; echo
      if [[ ! $REPLY =~ ^[Yy]$ ]]; then exit 1; fi
    fi
fi
echo -e "${GREEN}✅ 域名解析检查完成${NC}"

# 3. 检查端口占用
echo -e "\n${YELLOW}📋 步骤 3/8: 检查端口占用...${NC}"
ports=(80 443 3306 6379 8000)
for port in "${ports[@]}"; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  端口 $port 已被占用${NC}"
        lsof -Pi :$port -sTCP:LISTEN
        read -p "是否停止占用进程并继续? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            sudo lsof -ti:$port | xargs sudo kill -9 || true
        fi
    fi
done
echo -e "${GREEN}✅ 端口检查完成${NC}"

# 4. 备份现有数据（如果存在）
echo -e "\n${YELLOW}📋 步骤 4/8: 备份现有数据...${NC}"
if docker volume ls | grep -q "stock_mysql_data"; then
    BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    echo "正在备份数据库到 $BACKUP_DIR..."
    docker run --rm \
        -v stock_mysql_data:/data \
        -v $(pwd)/$BACKUP_DIR:/backup \
        alpine tar czf /backup/mysql_data.tar.gz -C /data .
    echo -e "${GREEN}✅ 数据库备份完成${NC}"
else
    echo "未发现现有数据，跳过备份"
fi

# 5. 获取SSL证书
echo -e "\n${YELLOW}📋 步骤 5/8: 获取SSL证书...${NC}"
if [ ! -d "/etc/letsencrypt/live/${DOMAIN}" ]; then
    echo "首次部署，需要获取SSL证书..."

    # 检查certbot是否安装
    if ! command -v certbot &> /dev/null; then
        echo "正在安装 certbot..."
        if command -v apt-get &> /dev/null; then
            sudo apt-get update
            sudo apt-get install -y certbot
        elif command -v yum &> /dev/null; then
            sudo yum install -y certbot
        else
            echo -e "${RED}❌ 无法自动安装certbot，请手动安装${NC}"
            exit 1
        fi
    fi

    # 获取证书
    echo "正在获取 ${DOMAIN} 的SSL证书..."
    sudo certbot certonly --standalone \
        -d ${DOMAIN} \
        -d www.${DOMAIN} \
        --non-interactive \
        --agree-tos \
        --email "${EMAIL}"

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ SSL证书获取成功${NC}"
    else
        echo -e "${RED}❌ SSL证书获取失败${NC}"
        echo "请检查："
        echo "1. 域名是否正确解析到本服务器"
        echo "2. 80端口是否开放"
        echo "3. 防火墙是否允许访问"
        exit 1
    fi
else
    echo -e "${GREEN}✅ SSL证书已存在${NC}"

    # 检查证书是否即将过期
    if sudo certbot certificates | grep -q "INVALID"; then
        echo -e "${YELLOW}⚠️  证书即将过期或已过期，尝试续期...${NC}"
        sudo certbot renew
    fi
fi

# 6. 停止现有服务
echo -e "\n${YELLOW}📋 步骤 6/8: 停止现有服务...${NC}"
if docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
    echo "正在停止现有服务..."
    docker-compose -f docker-compose.prod.yml down
fi
echo -e "${GREEN}✅ 现有服务已停止${NC}"

# 7. 启动生产环境服务
echo -e "\n${YELLOW}📋 步骤 7/8: 启动生产环境服务...${NC}"
docker-compose -f docker-compose.prod.yml up -d --build

# 等待服务启动
echo "等待服务启动..."
sleep 10

# 检查服务状态
echo -e "\n服务运行状态:"
docker-compose -f docker-compose.prod.yml ps

# 8. 验证部署
echo -e "\n${YELLOW}📋 步骤 8/8: 验证部署...${NC}"

# 检查后端健康
echo "检查后端服务..."
max_retries=30
retry_count=0
while [ $retry_count -lt $max_retries ]; do
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 后端服务正常${NC}"
        break
    fi
    retry_count=$((retry_count + 1))
    echo "等待后端服务启动... ($retry_count/$max_retries)"
    sleep 2
done

if [ $retry_count -eq $max_retries ]; then
    echo -e "${RED}❌ 后端服务启动失败${NC}"
    echo "查看日志："
    docker-compose -f docker-compose.prod.yml logs backend
    exit 1
fi

# 检查Nginx
echo "检查Nginx服务..."
if curl -sf http://localhost/nginx-health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Nginx服务正常${NC}"
else
    echo -e "${RED}❌ Nginx服务异常${NC}"
    docker-compose -f docker-compose.prod.yml logs nginx
fi

# 检查HTTPS访问
echo "检查HTTPS访问..."
if curl -sf https://qwquant.com/nginx-health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ HTTPS访问正常${NC}"
else
    echo -e "${YELLOW}⚠️  HTTPS访问失败，可能需要等待DNS生效${NC}"
fi

# 运行微信支付配置检查
echo -e "\n检查微信支付配置..."
docker-compose -f docker-compose.prod.yml exec -T backend python check_payment_config.py || true

# 9. 设置证书自动续期
echo -e "\n${YELLOW}📋 设置SSL证书自动续期...${NC}"
if ! crontab -l 2>/dev/null | grep -q "certbot renew"; then
    (crontab -l 2>/dev/null; echo "0 2 * * * /usr/bin/certbot renew --quiet && docker-compose -f $(pwd)/docker-compose.prod.yml restart nginx") | crontab -
    echo -e "${GREEN}✅ 已设置证书自动续期（每天凌晨2点检查）${NC}"
else
    echo "证书自动续期任务已存在"
fi

echo -e "\n${GREEN}======================================"
echo "🎉 部署完成！"
echo "======================================${NC}"
echo ""
echo "📊 服务信息："
echo "   主站: https://qwquant.com"
echo "   管理后台: https://qwquant.com/admin"
echo "   API文档: https://qwquant.com/api/docs"
echo "   支付回调: https://qwquant.com/api/v1/payment/notify"
echo ""
echo "🔧 常用命令："
echo "   查看日志: docker-compose -f docker-compose.prod.yml logs -f"
echo "   重启服务: docker-compose -f docker-compose.prod.yml restart"
echo "   停止服务: docker-compose -f docker-compose.prod.yml down"
echo "   查看状态: docker-compose -f docker-compose.prod.yml ps"
echo ""
echo "⚠️  下一步操作："
echo "   1. 访问 https://qwquant.com 验证网站是否正常"
echo "   2. 登录微信商户平台配置回调地址："
echo "      https://qwquant.com/api/v1/payment/notify"
echo "   3. 确认微信商户平台中AppID wx629c41da78273de4 已关联"
echo "   4. 创建测试订单验证支付功能"
echo ""
