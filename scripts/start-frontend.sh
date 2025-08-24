#!/bin/bash

# 启动前端服务脚本
# Start Frontend Service Script

set -e

echo "⚛️  启动 React 前端服务..."

# 检查是否在项目根目录
if [ ! -d "frontend" ]; then
    echo "❌ 错误: 请在项目根目录下运行此脚本"
    exit 1
fi

# 进入前端目录
cd frontend

# 检查node_modules
if [ ! -d "node_modules" ]; then
    echo "❌ 错误: 未找到 node_modules 目录"
    echo "   请先运行: ./scripts/setup-local.sh"
    exit 1
fi

# 检查环境变量文件
if [ ! -f "../.env" ]; then
    echo "❌ 错误: 未找到环境配置文件 .env"
    echo "   请先运行: ./scripts/setup-local.sh"
    exit 1
fi

# 设置前端环境变量
export REACT_APP_API_URL=http://localhost:8000/api/v1
export REACT_APP_ENVIRONMENT=development
export PORT=3000

echo "🚀 启动 React 开发服务器..."
echo "📍 前端地址: http://localhost:3000"
echo "🔗 API地址: http://localhost:8000/api/v1"
echo "🛑 停止服务: Ctrl+C"
echo ""

# 启动开发服务器
npm start