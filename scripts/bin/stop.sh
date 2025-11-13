#!/bin/bash

# 股票分析系统 - 停止服务脚本
echo "🛑 停止股票分析系统"
echo "===================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_success() { echo -e "${GREEN}[✅]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[⚠️]${NC} $1"; }
log_error() { echo -e "${RED}[❌]${NC} $1"; }

# 端口配置
BACKEND_PORT=3007
FRONTEND_PORT=8006
CLIENT_PORT=8005

# 创建日志目录
mkdir -p logs

kill_by_port() {
    local port=$1
    local service=$2
    
    if lsof -ti:$port >/dev/null 2>&1; then
        log_warn "正在停止 $service (端口 $port)..."
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
        sleep 1
        log_success "$service 已停止"
    else
        log_warn "$service 未运行 (端口 $port)"
    fi
}

kill_by_pidfile() {
    local pidfile=$1
    local service=$2
    
    if [ -f "$pidfile" ]; then
        local pid=$(cat "$pidfile")
        if kill -0 "$pid" 2>/dev/null; then
            log_warn "正在停止 $service (PID: $pid)..."
            kill -9 "$pid" 2>/dev/null || true
            rm -f "$pidfile"
            sleep 1
            log_success "$service 已停止"
        fi
    fi
}

# 停止服务
echo "⏳ 停止所有服务..."
echo ""

kill_by_pidfile "logs/backend.pid" "后端 API"
kill_by_pidfile "logs/frontend.pid" "管理端"
kill_by_pidfile "logs/client.pid" "客户端"

# 备用方法：按端口停止
kill_by_port $BACKEND_PORT "后端 API"
kill_by_port $FRONTEND_PORT "管理端"
kill_by_port $CLIENT_PORT "客户端"

echo ""
echo -e "${GREEN}✨ 所有服务已停止${NC}"
echo ""
