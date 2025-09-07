#!/bin/bash

# 股票分析系统 - 部署脚本 (最终版)
echo "🚀 股票分析系统部署"
echo "=================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_success() { echo -e "${GREEN}[✅]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[⚠️]${NC} $1"; }
log_error() { echo -e "${RED}[❌]${NC} $1"; }

# 固定端口配置
BACKEND_PORT=3007
CLIENT_PORT=8005
FRONTEND_PORT=8006

echo "📊 端口配置: API($BACKEND_PORT) | 客户端($CLIENT_PORT) | 管理端($FRONTEND_PORT)"
echo ""

# 环境检查
echo "🔍 检查环境..."
command -v node >/dev/null || { log_error "Node.js未安装"; exit 1; }
command -v python3 >/dev/null || { log_error "Python3未安装"; exit 1; }
command -v mysql >/dev/null || { log_error "MySQL未安装"; exit 1; }

# MySQL服务检查
if ! mysqladmin ping -h127.0.0.1 --silent 2>/dev/null; then
    log_warn "启动MySQL服务..."
    brew services start mysql 2>/dev/null || { log_error "MySQL启动失败"; exit 1; }
    sleep 2
fi
log_success "环境检查完成"

# 后端设置
echo "🔧 设置后端..."
cd backend
[ ! -d "venv" ] && python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt -q
log_success "后端依赖完成"

# 创建管理员用户
echo "👤 创建管理员用户..."
python create_admin_table.py 2>/dev/null || log_warn "管理员可能已存在"

cd ..

# 前端设置 - 修复端口配置
echo "🎨 设置前端..."
# 修复客户端端口
if [ -f "client/package.json" ]; then
    sed -i.bak "s/--port [0-9]*/--port $CLIENT_PORT/g" client/package.json
fi
# 修复管理端端口  
if [ -f "frontend/package.json" ]; then
    sed -i.bak "s/--port [0-9]*/--port $FRONTEND_PORT/g" frontend/package.json
fi

# 安装依赖
[ ! -d "client/node_modules" ] && { cd client && npm install -q && cd ..; }
[ ! -d "frontend/node_modules" ] && { cd frontend && npm install -q && cd ..; }
log_success "前端依赖完成"

# 配置文件
echo "⚙️ 生成配置..."
cat > ports.env << EOF
BACKEND_PORT=$BACKEND_PORT
CLIENT_PORT=$CLIENT_PORT
FRONTEND_PORT=$FRONTEND_PORT
EOF

mkdir -p logs
log_success "配置完成"

echo ""
echo "🎉 部署完成！"
echo ""
echo "📊 服务地址:"
echo "  🔗 API:     http://localhost:$BACKEND_PORT"
echo "  📱 客户端:   http://localhost:$CLIENT_PORT" 
echo "  🖥️ 管理端:   http://localhost:$FRONTEND_PORT"
echo ""
echo "👤 管理员账号: admin / admin123"
echo ""
echo "📋 下一步: ./start.sh"