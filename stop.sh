#!/bin/bash

# 股票分析系统 - 停止脚本 v2.7.3
echo "🛑 停止股票分析系统"
echo "==================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_success() { echo -e "${GREEN}[✅]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[⚠️]${NC} $1"; }

# 端口配置 - 与 start.sh 保持一致
BACKEND_PORT=3007
FRONTEND_PORT=8006
CLIENT_PORT=8005

# 停止服务函数
stop_service() {
    local service_name=$1
    local port=$2
    local pid_file="logs/${service_name}.pid"

    echo "  停止 $service_name..."

    # 从PID文件读取进程ID
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 $pid 2>/dev/null; then
            kill -TERM $pid 2>/dev/null
            sleep 2
            # 检查进程是否还在运行
            if kill -0 $pid 2>/dev/null; then
                log_warn "进程未响应，强制杀死..."
                kill -9 $pid 2>/dev/null
            fi
        fi
        rm -f "$pid_file"
    fi

    # 强制清理端口（以防万一）
    if lsof -ti:$port >/dev/null 2>&1; then
        log_warn "强制清理端口 $port..."
        lsof -ti:$port | xargs kill -9 2>/dev/null
    fi
}

# ==================== 停止所有服务 ====================
echo "🔄 停止服务..."
echo ""

stop_service "backend" $BACKEND_PORT
stop_service "frontend" $FRONTEND_PORT
stop_service "client" $CLIENT_PORT

echo ""
echo "⏳ 等待进程清理..."
sleep 2

# ==================== 验证停止 ====================
echo ""
echo "📋 端口状态检查:"
echo ""

all_stopped=true
for port in $BACKEND_PORT $FRONTEND_PORT $CLIENT_PORT; do
    if lsof -ti:$port >/dev/null 2>&1; then
        all_stopped=false
        case $port in
            $BACKEND_PORT) echo -e "  ${RED}⚠️${NC} 后端 API ($port) 仍在运行" ;;
            $FRONTEND_PORT) echo -e "  ${RED}⚠️${NC} 管理端 ($port) 仍在运行" ;;
            $CLIENT_PORT) echo -e "  ${RED}⚠️${NC} 客户端 ($port) 仍在运行" ;;
        esac
    else
        case $port in
            $BACKEND_PORT) echo -e "  ${GREEN}✅${NC} 后端 API ($port) 已停止" ;;
            $FRONTEND_PORT) echo -e "  ${GREEN}✅${NC} 管理端 ($port) 已停止" ;;
            $CLIENT_PORT) echo -e "  ${GREEN}✅${NC} 客户端 ($port) 已停止" ;;
        esac
    fi
done

echo ""

if [ "$all_stopped" = true ]; then
    echo -e "${GREEN}✅ 所有服务已停止${NC}"
    echo ""
    echo "📝 日志文件保留在 logs/ 目录"
    echo "🚀 重新启动: ./start.sh"
    echo ""
else
    log_warn "部分服务停止失败，可能需要手动处理"
    echo "💡 查看进程: lsof -i :3007,8006,8005"
    echo "💡 手动杀死: kill -9 <PID>"
    echo ""
fi
