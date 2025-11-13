#!/bin/bash

# 生产环境启动脚本
# 用于在服务器上启动股票分析系统

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_success() { echo -e "${GREEN}[✅]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[⚠️]${NC} $1"; }
log_error() { echo -e "${RED}[❌]${NC} $1"; }
log_info() { echo -e "${BLUE}[ℹ️]${NC} $1"; }

# 固定端口配置（生产环境）
BACKEND_PORT=3007
CLIENT_PORT=8005
FRONTEND_PORT=8006

echo "🚀 启动股票分析系统 (生产环境)"
echo "================================"

# 检查环境
log_info "检查环境..."
command -v node >/dev/null || { log_error "Node.js未安装"; exit 1; }
command -v python3 >/dev/null || { log_error "Python3未安装"; exit 1; }

# 检查MySQL服务
if ! mysqladmin ping -h127.0.0.1 --silent 2>/dev/null; then
    log_warn "启动MySQL服务..."
    systemctl start mysqld 2>/dev/null || service mysql start 2>/dev/null || {
        log_error "MySQL启动失败"
        exit 1
    }
    sleep 2
fi
log_success "MySQL服务正常"

# 停止可能运行的服务
log_info "停止现有服务..."
pkill -f "uvicorn.*main" 2>/dev/null || true
pkill -f "npm.*dev" 2>/dev/null || true
pkill -f "node.*dev" 2>/dev/null || true
sleep 2

# 启动后端服务
log_info "启动后端服务 (端口: $BACKEND_PORT)..."
cd backend
source venv/bin/activate

# 使用 nohup 在后台运行
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > ../logs/backend.pid

# 等待后端启动
sleep 5
if curl -s http://localhost:$BACKEND_PORT/health >/dev/null; then
    log_success "后端服务启动成功 (PID: $BACKEND_PID)"
else
    log_error "后端服务启动失败"
    exit 1
fi

cd ..

# 启动前端服务
log_info "启动管理端 (端口: $FRONTEND_PORT)..."
cd frontend
nohup npm run dev -- --host 0.0.0.0 --port $FRONTEND_PORT > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../logs/frontend.pid
cd ..

log_info "启动客户端 (端口: $CLIENT_PORT)..."
cd client
nohup npm run dev -- --host 0.0.0.0 --port $CLIENT_PORT > ../logs/client.log 2>&1 &
CLIENT_PID=$!
echo $CLIENT_PID > ../logs/client.pid
cd ..

# 等待前端启动
sleep 10

# 检查服务状态
log_info "检查服务状态..."

# 检查后端
if curl -s http://localhost:$BACKEND_PORT/health >/dev/null; then
    log_success "✅ 后端API服务正常 (端口: $BACKEND_PORT)"
else
    log_error "❌ 后端API服务异常"
fi

# 检查前端服务
if curl -s http://localhost:$FRONTEND_PORT >/dev/null 2>&1; then
    log_success "✅ 管理端服务正常 (端口: $FRONTEND_PORT)"
else
    log_warn "⚠️  管理端服务可能还在启动中"
fi

if curl -s http://localhost:$CLIENT_PORT >/dev/null 2>&1; then
    log_success "✅ 客户端服务正常 (端口: $CLIENT_PORT)"
else
    log_warn "⚠️  客户端服务可能还在启动中"
fi

# 显示访问信息
echo ""
log_success "🎉 股票分析系统启动完成！"
echo ""
echo "📊 服务访问地址:"
echo "  🔗 API服务:    http://$(hostname -I | awk '{print $1}'):$BACKEND_PORT"
echo "  📱 客户端:     http://$(hostname -I | awk '{print $1}'):$CLIENT_PORT"
echo "  🖥️ 管理端:     http://$(hostname -I | awk '{print $1}'):$FRONTEND_PORT"
echo ""
echo "👤 管理员账号: admin / admin123"
echo ""
echo "📋 进程信息:"
echo "  后端PID: $BACKEND_PID"
echo "  管理端PID: $FRONTEND_PID"
echo "  客户端PID: $CLIENT_PID"
echo ""
echo "📝 日志文件:"
echo "  后端日志: logs/backend.log"
echo "  管理端日志: logs/frontend.log"
echo "  客户端日志: logs/client.log"
echo ""
echo "🔧 管理命令:"
echo "  停止服务: ./scripts/deployment/stop.sh"
echo "  检查状态: ./scripts/deployment/status.sh"