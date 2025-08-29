#!/bin/bash

# 股票分析系统安全部署脚本
# Stock Analysis System Secure Deployment Script

set -e

echo "🔐 安全部署脚本 - 需要环境变量配置"
echo "================================================="

# 检查必需的环境变量
required_vars=(
    "DEPLOY_SERVER_IP"
    "DEPLOY_SERVER_USER" 
    "DEPLOY_SERVER_PASS"
    "DB_ROOT_PASSWORD"
    "DB_APP_PASSWORD"
    "JWT_SECRET_KEY"
    "ADMIN_PASSWORD"
)

missing_vars=()
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -gt 0 ]; then
    echo "❌ 缺少以下必需的环境变量："
    for var in "${missing_vars[@]}"; do
        echo "   - $var"
    done
    echo ""
    echo "请在 .env.deploy 文件中设置这些变量，或者导出到环境中："
    echo ""
    echo "cat > .env.deploy << EOF"
    echo "DEPLOY_SERVER_IP=your-server-ip"
    echo "DEPLOY_SERVER_USER=root"
    echo "DEPLOY_SERVER_PASS=your-server-password" 
    echo "DB_ROOT_PASSWORD=your-secure-db-password"
    echo "DB_APP_PASSWORD=your-app-db-password"
    echo "JWT_SECRET_KEY=your-32-char-secret-key"
    echo "ADMIN_PASSWORD=your-admin-password"
    echo "EOF"
    echo ""
    echo "然后运行: source .env.deploy"
    exit 1
fi

# 配置变量
SERVER_IP="$DEPLOY_SERVER_IP"
SERVER_USER="$DEPLOY_SERVER_USER"
SERVER_PASS="$DEPLOY_SERVER_PASS"

echo "🚀 开始安全部署股票分析系统到 $SERVER_IP..."
echo "⚠️  请确保已设置所有必需的环境变量"

# 部署前确认
read -p "确认开始部署? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ 部署已取消"
    exit 1
fi

# 后续部署步骤将使用环境变量替代硬编码值...
echo "✅ 环境变量验证通过，准备开始部署"
echo "📋 将使用以下配置："
echo "   服务器: $SERVER_IP"
echo "   用户: $SERVER_USER"
echo "   数据库密码: [已设置]"
echo "   JWT密钥: [已设置]"
echo "   管理员密码: [已设置]"

echo ""
echo "🔧 实际部署逻辑需要继续开发..."
echo "💡 建议使用 Ansible 或 Docker Compose 进行生产部署"