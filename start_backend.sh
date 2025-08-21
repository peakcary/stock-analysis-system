#!/bin/bash
# 后端启动脚本
# Backend Start Script

set -e

echo "🚀 启动股票分析系统后端服务..."

# 检查是否在项目根目录
if [ ! -d "backend" ]; then
    echo "❌ 请在项目根目录执行此脚本"
    exit 1
fi

# 进入后端目录
cd backend

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ Python 虚拟环境不存在，请先运行 ./setup_environment.sh"
    exit 1
fi

# 激活虚拟环境
echo "🐍 激活 Python 虚拟环境..."
source venv/bin/activate

# 检查依赖
if ! python -c "import fastapi" 2>/dev/null; then
    echo "📦 安装后端依赖..."
    pip install -r requirements.txt
fi

# 检查数据库连接
echo "🔍 检查数据库连接..."
if ! mysql -u root -proot123 -e "USE stock_analysis; SELECT 1;" &>/dev/null; then
    echo "❌ 数据库连接失败，请确保："
    echo "1. MySQL 服务已启动"
    echo "2. 数据库已初始化 (运行 ./setup_database.sh)"
    exit 1
fi

# 创建日志目录
mkdir -p logs uploads

# 启动服务
echo "🌟 启动 FastAPI 服务..."
echo "📡 后端服务地址: http://localhost:8000"
echo "📚 API 文档地址: http://localhost:8000/docs"
echo "🛑 按 Ctrl+C 停止服务"
echo ""

# 启动 uvicorn 服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000