#!/bin/bash

# 股票分析系统 - 统一启动脚本 v2.7.3
echo "🚀 启动股票分析系统"
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

echo "📊 服务配置:"
echo "  后端 API: http://localhost:$BACKEND_PORT"
echo "  管理端:   http://localhost:$FRONTEND_PORT"
echo "  客户端:   http://localhost:$CLIENT_PORT"
echo ""

# ==================== 环境检查 ====================
echo "🔍 执行环境检查..."
if [ ! -f "check-env.sh" ]; then
    log_error "check-env.sh 脚本不存在"
    exit 1
fi

chmod +x check-env.sh
if ! bash check-env.sh | tail -10 | grep -q "可以开始开发"; then
    log_warn "环境检查发现问题，部分功能可能无法使用"
    echo ""
    read -p "是否继续启动? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_warn "启动已取消"
        exit 1
    fi
fi
echo ""

# ==================== 依赖检查和安装 ====================
echo "📦 检查和安装依赖..."

# 后端依赖
if [ ! -d "backend/venv" ]; then
    log_warn "创建Python虚拟环境..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -q -r requirements.txt
    deactivate
    cd ..
    log_success "后端环境准备完成"
fi

# 前端依赖
if [ ! -d "frontend/node_modules" ]; then
    log_warn "安装前端依赖..."
    cd frontend
    npm install --silent --no-audit --no-fund 2>/dev/null
    cd ..
    log_success "前端依赖安装完成"
fi

# 客户端依赖
if [ ! -d "client/node_modules" ]; then
    log_warn "安装客户端依赖..."
    cd client
    npm install --silent --no-audit --no-fund 2>/dev/null
    cd ..
    log_success "客户端依赖安装完成"
fi

echo ""

# ==================== 清理端口占用 ====================
echo "🧹 清理端口占用..."

clear_port() {
    local port=$1
    local service=$2
    if lsof -ti:$port >/dev/null 2>&1; then
        log_warn "清理端口 $port ($service)..."
        lsof -ti:$port | xargs kill -9 2>/dev/null
        sleep 1
    fi
}

clear_port $BACKEND_PORT "API"
clear_port $FRONTEND_PORT "管理端"
clear_port $CLIENT_PORT "客户端"

echo ""

# ==================== 创建日志目录 ====================
mkdir -p logs

# ==================== 启动服务 ====================
echo "🔄 启动服务..."
echo ""

# 启动后端服务
echo "  ⏳ 启动后端 API ($BACKEND_PORT)..."
cd backend
source venv/bin/activate
nohup python -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port $BACKEND_PORT \
    --reload > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > ../logs/backend.pid
deactivate
cd ..

# 启动前端管理系统
echo "  ⏳ 启动管理端 ($FRONTEND_PORT)..."
cd frontend
nohup npm run dev > ../logs/frontend.log 2>&1 &
echo $! > ../logs/frontend.pid
cd ..

# 启动客户端应用
echo "  ⏳ 启动客户端 ($CLIENT_PORT)..."
cd client
nohup npm run dev > ../logs/client.log 2>&1 &
echo $! > ../logs/client.pid
cd ..

echo ""
echo "⏳ 等待服务启动（约10秒）..."
sleep 10

echo ""

# ==================== 检查服务状态 ====================
echo "📋 服务状态检查:"
echo ""

all_running=true
for port in $BACKEND_PORT $FRONTEND_PORT $CLIENT_PORT; do
    if lsof -ti:$port >/dev/null 2>&1; then
        case $port in
            $BACKEND_PORT) echo -e "  ${GREEN}✅${NC} 后端 API ($port)" ;;
            $FRONTEND_PORT) echo -e "  ${GREEN}✅${NC} 管理端 ($port)" ;;
            $CLIENT_PORT) echo -e "  ${GREEN}✅${NC} 客户端 ($port)" ;;
        esac
    else
        all_running=false
        case $port in
            $BACKEND_PORT) echo -e "  ${RED}❌${NC} 后端 API ($port) - 启动失败" ;;
            $FRONTEND_PORT) echo -e "  ${RED}❌${NC} 管理端 ($port) - 启动失败" ;;
            $CLIENT_PORT) echo -e "  ${RED}❌${NC} 客户端 ($port) - 启动失败" ;;
        esac
    fi
done

echo ""

# ==================== 启动完成提示 ====================
if [ "$all_running" = true ]; then
    echo -e "${GREEN}🎉 所有服务启动成功！${NC}"
    echo ""
    echo "📊 访问地址:"
    echo "  🔗 后端 API: http://localhost:$BACKEND_PORT"
    echo "  📖 API文档:  http://localhost:$BACKEND_PORT/docs"
    echo "  🖥️  管理端:  http://localhost:$FRONTEND_PORT (admin/admin123)"
    echo "  📱 客户端:   http://localhost:$CLIENT_PORT (fullaccess_user/fullaccess123)"
    echo ""
    echo "💾 日志文件:"
    echo "  📄 tail -f logs/backend.log"
    echo "  📄 tail -f logs/frontend.log"
    echo "  📄 tail -f logs/client.log"
    echo ""
    echo "🛑 停止服务:"
    echo "  ./stop.sh"
    echo ""
    echo "✨ 快速命令:"
    echo "  • 检查状态:     ./status.sh"
    echo "  • 重启服务:     ./restart.sh"
    echo "  • 查看日志:     tail -f logs/[backend|frontend|client].log"
    echo ""
else
    echo -e "${YELLOW}⚠️  部分服务启动失败${NC}"
    echo ""
    echo "🔧 故障排除:"
    echo "  1. 查看日志: tail -f logs/[service].log"
    echo "  2. 检查环境: ./check-env.sh"
    echo "  3. 查看文档: cat QUICKSTART.md 或 TROUBLESHOOTING.md"
    echo ""
fi
