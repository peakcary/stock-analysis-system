#!/bin/bash
# 切换到本地数据库配置

echo "🔄 切换到本地MySQL数据库..."

# 备份当前配置
cp backend/.env backend/.env.remote.backup

# 生成本地数据库配置
cat > backend/.env << 'ENVEOF'
# 本地数据库配置
DATABASE_URL=mysql+pymysql://root:Pp123456@localhost:3306/stock_analysis_dev
DATABASE_HOST=localhost
DATABASE_PORT=3306
DATABASE_USER=root
DATABASE_PASSWORD=Pp123456
DATABASE_NAME=stock_analysis_dev

# 应用配置
SECRET_KEY=your-secret-key-change-in-production
ENVIRONMENT=development
DEBUG=True
PORT=3007

# Redis
REDIS_URL=redis://localhost:6379
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# 微信支付配置（保持不变）
WECHAT_PAY_ENABLED=true
WECHAT_PAY_MERCHANT_ID=your_merchant_id
WECHAT_PAY_API_V3_KEY=your_api_v3_key
WECHAT_PAY_SERIAL_NO=your_cert_serial_no
WECHAT_PAY_PRIVATE_KEY_PATH=./certs/apiclient_key.pem
WECHAT_PAY_CERT_PATH=./certs/apiclient_cert.pem
ENVEOF

echo "✅ 已切换到本地数据库"
echo "📝 远程配置已备份到: backend/.env.remote.backup"
echo ""
echo "🚀 下一步:"
echo "  1. 启动本地MySQL: brew services start mysql"
echo "  2. 创建数据库: mysql -u root -pPp123456 -e 'CREATE DATABASE IF NOT EXISTS stock_analysis_dev'"
echo "  3. 初始化表: cd backend && python init_database.py"
echo "  4. 部署: ./scripts/deployment/deploy.sh"
