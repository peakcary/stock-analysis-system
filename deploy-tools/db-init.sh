#!/bin/bash
set -e

# ===== 数据库初始化脚本 =====
# 用于初始化生产环境数据库：创建表、默认用户等

SERVER_IP="82.157.28.35"
SERVER_USER="ubuntu"
SERVER_PASSWORD="chen_188_8_8"

echo "🚀 数据库初始化脚本"
echo "================================"
echo ""

# 检查是否已经初始化
echo "🔍 检查数据库状态..."
sshpass -p "${SERVER_PASSWORD}" ssh -o StrictHostKeyChecking=no \
    ${SERVER_USER}@${SERVER_IP} << 'CHECK_DB'

mysql -u root -p'Pp123456' -e "USE stock_analysis_prod; SHOW TABLES;" 2>/dev/null | head -5

CHECK_DB

echo ""
echo "📋 准备初始化数据库..."
echo "   - 服务器: ${SERVER_IP}"
echo "   - 项目路径: /opt/stock-analysis-system/backend"
echo ""

# 确认
read -p "确认初始化数据库? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ 已取消"
    exit 1
fi

# 执行初始化
echo ""
echo "⚙️  执行数据库初始化..."
sshpass -p "${SERVER_PASSWORD}" ssh -o StrictHostKeyChecking=no \
    ${SERVER_USER}@${SERVER_IP} << 'INIT_DB'

cd /opt/stock-analysis-system/backend

# 激活虚拟环境
source venv/bin/activate

# 设置环境变量
export DATABASE_HOST=127.0.0.1
export DATABASE_PORT=3306
export DATABASE_USER=root
export DATABASE_PASSWORD=Pp123456
export DATABASE_NAME=stock_analysis_prod
export DATABASE_URL=mysql+pymysql://root:Pp123456@127.0.0.1:3306/stock_analysis_prod

# 运行初始化脚本
echo "🔧 运行 init_database.py..."
python3 init_database.py

echo ""
echo "✅ 数据库初始化完成！"
echo ""
echo "📊 验证表结构..."
mysql -u root -p'Pp123456' stock_analysis_prod -e "SHOW TABLES;" | head -20

INIT_DB

echo ""
echo "✅ 初始化完成！"
echo ""
echo "📝 后续步骤："
echo "   1. 访问 https://qwquant.com/api/docs 查看API文档"
echo "   2. 使用默认管理员账户登录"
echo "   3. 运行 ./check-status.sh 检查服务状态"
echo ""
