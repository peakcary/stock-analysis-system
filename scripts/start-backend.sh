#!/bin/bash

# 启动后端服务脚本
# Start Backend Service Script

set -e

echo "🐍 启动 FastAPI 后端服务..."

# 检查是否在项目根目录
if [ ! -d "backend" ]; then
    echo "❌ 错误: 请在项目根目录下运行此脚本"
    exit 1
fi

# 进入后端目录
cd backend

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 错误: 未找到Python虚拟环境"
    echo "   请先运行: ./scripts/setup-local.sh"
    exit 1
fi

# 激活虚拟环境
echo "🔧 激活Python虚拟环境..."
source venv/bin/activate

# 检查环境变量文件
if [ ! -f "../.env" ]; then
    echo "❌ 错误: 未找到环境配置文件 .env"
    echo "   请先运行: ./scripts/setup-local.sh"
    exit 1
fi

# 加载环境变量
set -a  # 自动导出变量
source ../.env
set +a  # 关闭自动导出

# 检查数据库连接
echo "🔍 检查数据库连接..."
python3 -c "
import pymysql
try:
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='Pp123456',
        database='stock_analysis_dev',
        charset='utf8mb4'
    )
    print('✅ 数据库连接成功')
    connection.close()
except Exception as e:
    print(f'❌ 数据库连接失败: {e}')
    exit(1)
" || {
    echo "❌ 数据库连接失败，请检查MySQL服务是否运行"
    exit 1
}

# 创建日志目录
mkdir -p logs

echo "🚀 启动 FastAPI 服务器..."
echo "📍 后端地址: http://localhost:8000"
echo "📚 API文档: http://localhost:8000/docs"
echo "🛑 停止服务: Ctrl+C"
echo ""

# 启动服务器
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --log-level info \
    --access-log \
    --use-colors