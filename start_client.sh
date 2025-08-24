#!/bin/bash
# 启动客户端服务脚本

echo "🚀 启动股票分析系统客户端..."

# 检查是否在正确目录
if [ ! -d "client" ]; then
    echo "❌ 错误: 请在项目根目录下运行此脚本"
    exit 1
fi

# 进入客户端目录
cd client

# 检查依赖是否安装
if [ ! -d "node_modules" ]; then
    echo "📦 正在安装客户端依赖..."
    npm install
fi

# 启动客户端开发服务器
echo "⚛️  启动客户端服务 (端口 3001)..."
npm run dev