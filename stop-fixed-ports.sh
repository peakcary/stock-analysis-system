#!/bin/bash

# 固定端口停止脚本
echo "🛑 停止股票分析系统 (固定端口版)"
echo "================================="

# 停止进程函数
stop_service() {
    local pid_file=$1
    local service_name=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null
            sleep 2
            if kill -0 "$pid" 2>/dev/null; then
                kill -9 "$pid" 2>/dev/null
            fi
            echo "✅ $service_name 服务已停止 (PID: $pid)"
        fi
        rm -f "$pid_file"
    fi
}

# 停止各服务
stop_service "logs/backend.pid" "backend"
stop_service "logs/client.pid" "client"  
stop_service "logs/frontend.pid" "frontend"

# 清理固定端口
source fixed-ports.env 2>/dev/null
for port in $BACKEND_PORT $CLIENT_PORT $FRONTEND_PORT; do
    if [ ! -z "$port" ] && lsof -ti:$port &>/dev/null; then
        echo "清理端口 $port..."
        lsof -ti:$port | xargs kill -9 2>/dev/null
    fi
done

echo "🎉 所有服务已停止"