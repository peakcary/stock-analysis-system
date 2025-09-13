#!/bin/bash

# 股票分析系统 - 一键停止脚本
echo "🛑 停止股票分析系统"
echo "=================="

# 停止进程函数
stop_service() {
    local pid_file=$1
    local service_name=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo "🔧 停止 $service_name (PID: $pid)..."
            kill "$pid" 2>/dev/null
            sleep 2
            
            # 如果进程仍存在，强制终止
            if kill -0 "$pid" 2>/dev/null; then
                kill -9 "$pid" 2>/dev/null
            fi
            
            echo "  ✅ $service_name 已停止"
        else
            echo "  ⚠️  $service_name 进程不存在"
        fi
        rm -f "$pid_file"
    else
        echo "  ⚠️  $service_name PID文件不存在"
    fi
}

# 停止各个服务
if [ -d "logs" ]; then
    stop_service "logs/backend.pid" "API服务"
    stop_service "logs/client.pid" "客户端"
    stop_service "logs/frontend.pid" "管理端"
else
    echo "⚠️  日志目录不存在，尝试按端口停止服务..."
fi

# 按端口清理残留进程
if [ -f "ports.env" ]; then
    source ports.env
    echo ""
    echo "🧹 清理端口占用..."
    
    for port in $BACKEND_PORT $CLIENT_PORT $FRONTEND_PORT; do
        if lsof -ti:$port &>/dev/null; then
            echo "  清理端口 $port..."
            lsof -ti:$port | xargs kill -9 2>/dev/null
        fi
    done
else
    echo "⚠️  端口配置文件不存在，清理常用端口..."
    # 清理默认端口
    for port in 3007 8005 8006; do
        if lsof -ti:$port &>/dev/null; then
            echo "  清理端口 $port..."
            lsof -ti:$port | xargs kill -9 2>/dev/null
        fi
    done
fi

echo ""
echo "🎉 所有服务已停止"
echo ""
echo "📋 重新启动:"
echo "  ▶️  启动系统: ./start.sh"
echo "  🔧 重新部署: ./deploy.sh"