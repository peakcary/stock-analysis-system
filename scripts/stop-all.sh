#!/bin/bash

# 停止所有服务脚本
# Stop All Services Script

echo "🛑 正在停止股票分析系统所有服务..."

# 停止可能运行的进程
echo "🔍 查找运行中的服务..."

# 停止后端服务 (uvicorn)
BACKEND_PIDS=$(pgrep -f "uvicorn app.main:app" 2>/dev/null || true)
if [ ! -z "$BACKEND_PIDS" ]; then
    echo "⏹️  停止后端服务 (PID: $BACKEND_PIDS)..."
    echo "$BACKEND_PIDS" | xargs kill 2>/dev/null || true
    sleep 2
    # 强制终止如果还在运行
    echo "$BACKEND_PIDS" | xargs kill -9 2>/dev/null || true
    echo "✅ 后端服务已停止"
else
    echo "ℹ️  后端服务未运行"
fi

# 停止前端服务 (react-scripts)
FRONTEND_PIDS=$(pgrep -f "react-scripts start" 2>/dev/null || true)
if [ ! -z "$FRONTEND_PIDS" ]; then
    echo "⏹️  停止前端服务 (PID: $FRONTEND_PIDS)..."
    echo "$FRONTEND_PIDS" | xargs kill 2>/dev/null || true
    sleep 2
    # 强制终止如果还在运行
    echo "$FRONTEND_PIDS" | xargs kill -9 2>/dev/null || true
    echo "✅ 前端服务已停止"
else
    echo "ℹ️  前端服务未运行"
fi

# 停止可能的Node.js进程
NODE_PIDS=$(pgrep -f "node.*3000" 2>/dev/null || true)
if [ ! -z "$NODE_PIDS" ]; then
    echo "⏹️  停止Node.js进程 (PID: $NODE_PIDS)..."
    echo "$NODE_PIDS" | xargs kill 2>/dev/null || true
    echo "✅ Node.js进程已停止"
fi

# 检查端口占用
echo "🔍 检查端口占用情况..."

# 检查8000端口 (后端)
PORT_8000=$(lsof -ti:8000 2>/dev/null || true)
if [ ! -z "$PORT_8000" ]; then
    echo "⚠️  端口8000仍被占用 (PID: $PORT_8000)，强制释放..."
    echo "$PORT_8000" | xargs kill -9 2>/dev/null || true
fi

# 检查3000端口 (前端)
PORT_3000=$(lsof -ti:3000 2>/dev/null || true)
if [ ! -z "$PORT_3000" ]; then
    echo "⚠️  端口3000仍被占用 (PID: $PORT_3000)，强制释放..."
    echo "$PORT_3000" | xargs kill -9 2>/dev/null || true
fi

echo ""
echo "✅ 所有服务已停止"
echo ""
echo "📋 端口状态："
echo "├─ 端口8000 (后端): $(lsof -ti:8000 >/dev/null 2>&1 && echo '占用' || echo '空闲')"
echo "└─ 端口3000 (前端): $(lsof -ti:3000 >/dev/null 2>&1 && echo '占用' || echo '空闲')"
echo ""
echo "🚀 重新启动: ./scripts/start-all.sh"
echo "👋 再见！"