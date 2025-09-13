#!/bin/bash

# 固定端口启动前端服务脚本
# 确保前端服务运行在8006端口

echo "🔍 检查8006端口占用情况..."

# 检查8006端口是否被占用
PORT_PID=$(lsof -ti :8006)

if [ ! -z "$PORT_PID" ]; then
    echo "⚠️  8006端口被进程 $PORT_PID 占用，正在终止..."
    kill -9 $PORT_PID 2>/dev/null || true
    sleep 2
fi

# 再次确认端口已释放
PORT_PID=$(lsof -ti :8006)
if [ ! -z "$PORT_PID" ]; then
    echo "❌ 无法释放8006端口，请手动处理"
    exit 1
fi

echo "✅ 8006端口已释放"

# 进入前端目录
cd /Users/peakom/work/stock-analysis-system/frontend

echo "🚀 启动前端服务到8006端口..."

# 强制指定端口，不允许自动切换
exec npm run dev -- --port 8006 --host 0.0.0.0