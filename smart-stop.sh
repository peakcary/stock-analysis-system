#!/bin/bash

# 智能停止脚本
source dev-ports.env 2>/dev/null

echo "🛑 停止所有服务..."

# 从PID文件停止
for service in "backend" "client" "frontend"; do
    if [ -f "logs/$service.pid" ]; then
        pid=$(cat "logs/$service.pid")
        if kill -0 $pid 2>/dev/null; then
            kill $pid 2>/dev/null
            echo "✅ $service 服务已停止 (PID: $pid)"
        fi
        rm -f "logs/$service.pid"
    fi
done

# 通过端口清理残留进程
if [ ! -z "$BACKEND_PORT" ]; then
    lsof -ti:$BACKEND_PORT | xargs kill -9 2>/dev/null || true
fi
if [ ! -z "$CLIENT_PORT" ]; then
    lsof -ti:$CLIENT_PORT | xargs kill -9 2>/dev/null || true
fi  
if [ ! -z "$FRONTEND_PORT" ]; then
    lsof -ti:$FRONTEND_PORT | xargs kill -9 2>/dev/null || true
fi

echo "🎉 所有服务已停止"
