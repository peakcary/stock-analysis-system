#!/bin/bash

# 股票分析系统 - 本地开发停止脚本 v2.7.0
echo "🛑 停止股票分析系统"
echo "==================="

# 端口配置 - 与 start-dev.sh 保持一致
BACKEND_PORT=3007
FRONTEND_PORT=8006
CLIENT_PORT=8005

# 停止服务函数
stop_service() {
    local service_name=$1
    local port=$2
    local pid_file="logs/${service_name}.pid"

    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        echo "停止 $service_name (PID: $pid)..."
        kill -TERM $pid 2>/dev/null
        rm -f "$pid_file"
    fi

    # 强制清理端口
    if lsof -ti:$port >/dev/null 2>&1; then
        echo "强制清理端口 $port..."
        lsof -ti:$port | xargs kill -9 2>/dev/null
    fi
}

echo "🔄 停止服务..."
stop_service "backend" $BACKEND_PORT
stop_service "frontend" $FRONTEND_PORT
stop_service "client" $CLIENT_PORT

echo ""
echo "⏳ 等待进程清理..."
sleep 2

# 检查是否还有残留进程
echo ""
echo "📋 端口状态检查:"
for port in $BACKEND_PORT $FRONTEND_PORT $CLIENT_PORT; do
    if lsof -ti:$port >/dev/null 2>&1; then
        echo "  ⚠️ 端口 $port 仍在运行"
    else
        echo "  ✅ 端口 $port 已停止"
    fi
done

echo ""
echo "✅ 停止完成！"
echo ""
echo "📝 日志文件保留在 logs/ 目录中"
echo "🚀 重新启动: ./start-dev.sh"