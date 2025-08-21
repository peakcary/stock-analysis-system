#!/bin/bash
# 前端启动脚本
# Frontend Start Script

set -e

echo "🚀 启动股票分析系统前端服务..."

# 检查是否在项目根目录
if [ ! -d "frontend" ]; then
    echo "❌ 请在项目根目录执行此脚本"
    exit 1
fi

# 进入前端目录
cd frontend

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装，请先运行 ./setup_environment.sh"
    exit 1
fi

# 检查依赖
if [ ! -d "node_modules" ]; then
    echo "📦 安装前端依赖..."
    npm install
fi

# 检查后端服务
echo "🔍 检查后端服务..."
if ! curl -s http://localhost:8000/health &>/dev/null; then
    echo "⚠️ 后端服务未启动，请先运行 ./start_backend.sh"
    echo "💡 继续启动前端服务..."
fi

# 启动前端服务
echo "🌟 启动 React 开发服务器..."
echo "🌐 前端服务地址: http://localhost:3000"
echo "🛑 按 Ctrl+C 停止服务"
echo ""

# 启动 Vite 开发服务器
npm run dev