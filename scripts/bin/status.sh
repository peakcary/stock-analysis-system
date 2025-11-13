#!/bin/bash

# 股票分析系统 - 服务状态检查脚本
echo "📋 股票分析系统 - 服务状态检查"
echo "=============================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 端口配置
BACKEND_PORT=3007
FRONTEND_PORT=8006
CLIENT_PORT=8005

# 检查端口状态
check_port() {
    local port=$1
    local service=$2
    
    if lsof -ti:$port >/dev/null 2>&1; then
        echo -e "  ${GREEN}✅${NC} $service 运行中 (端口 $port)"
        return 0
    else
        echo -e "  ${RED}❌${NC} $service 已停止 (端口 $port)"
        return 1
    fi
}

# 检查日志文件
check_logs() {
    local service=$1
    local logfile=$2
    
    if [ ! -f "$logfile" ]; then
        echo -e "    ${YELLOW}⚠️${NC}  日志文件不存在"
        return
    fi
    
    local last_error=$(tail -20 "$logfile" | grep -i "error\|exception" | tail -1)
    if [ -n "$last_error" ]; then
        echo -e "    ${RED}最后错误:${NC} ${last_error:0:100}..."
    else
        echo -e "    ${GREEN}日志正常${NC}"
    fi
}

echo "服务运行状态:"
echo ""
check_port $BACKEND_PORT "后端 API"
check_port $FRONTEND_PORT "管理端"
check_port $CLIENT_PORT "客户端"

echo ""
echo "最近日志信息:"
echo ""

if [ -f "logs/backend.log" ]; then
    echo "  📄 后端日志:"
    check_logs "后端" "logs/backend.log"
fi

if [ -f "logs/frontend.log" ]; then
    echo "  📄 前端日志:"
    check_logs "前端" "logs/frontend.log"
fi

if [ -f "logs/client.log" ]; then
    echo "  📄 客户端日志:"
    check_logs "客户端" "logs/client.log"
fi

echo ""
echo "📊 访问地址:"
echo "  后端 API: http://localhost:$BACKEND_PORT"
echo "  API 文档: http://localhost:$BACKEND_PORT/docs"
echo "  管理端:   http://localhost:$FRONTEND_PORT"
echo "  客户端:   http://localhost:$CLIENT_PORT"
echo ""
