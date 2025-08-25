#!/bin/bash
echo "🛑 停止所有服务..."

# 停止指定端口的进程
kill_port() {
    local pid=$(lsof -ti:$1)
    if [ ! -z "$pid" ]; then
        echo "停止端口 $1 的进程 (PID: $pid)..."
        kill -9 $pid
    fi
}

kill_port 8000  # 后端
kill_port 3001  # 用户前端
kill_port 3000  # 管理前端

echo "✅ 所有服务已停止"
