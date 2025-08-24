#!/bin/bash
# 停止所有服务脚本

echo "🛑 停止股票分析系统所有服务..."

# 停止通过PID文件记录的进程
if [ -f .backend_pid ]; then
    echo "停止后端服务..."
    kill $(cat .backend_pid) 2>/dev/null || true
    rm -f .backend_pid
fi

if [ -f .admin_pid ]; then
    echo "停止管理后台..."
    kill $(cat .admin_pid) 2>/dev/null || true
    rm -f .admin_pid
fi

if [ -f .client_pid ]; then
    echo "停止客户端..."
    kill $(cat .client_pid) 2>/dev/null || true
    rm -f .client_pid
fi

if [ -f .frontend_pid ]; then
    echo "停止前端服务..."
    kill $(cat .frontend_pid) 2>/dev/null || true
    rm -f .frontend_pid
fi

# 通过端口杀死可能残留的进程
echo "清理可能残留的进程..."
pkill -f "uvicorn.*8000" 2>/dev/null || true
pkill -f "vite.*3000" 2>/dev/null || true  
pkill -f "vite.*3001" 2>/dev/null || true
pkill -f "npm.*start" 2>/dev/null || true
pkill -f "react-scripts" 2>/dev/null || true

echo "✅ 所有服务已停止"