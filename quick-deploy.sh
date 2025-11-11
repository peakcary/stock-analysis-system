#!/bin/bash

# 快速部署脚本 - 跳过所有数据库检查
echo "🚀 股票分析系统快速部署"
echo "========================="

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_success() { echo -e "${GREEN}[✅]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[⚠️]${NC} $1"; }

# 固定端口
BACKEND_PORT=3007
CLIENT_PORT=8005
FRONTEND_PORT=8006

echo "📊 端口: API($BACKEND_PORT) | 客户端($CLIENT_PORT) | 管理端($FRONTEND_PORT)"

# 后端设置
echo "🔧 设置后端..."
cd backend

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate

# 安装依赖
if ! python -c "import fastapi, sqlalchemy, uvicorn" 2>/dev/null; then
    pip install -r requirements.txt -q
    log_success "后端依赖安装完成"
else
    log_success "后端依赖已存在"
fi

cd ..

# 前端依赖（跳过如果已存在）
if [ ! -d "client/node_modules" ]; then
    echo "📦 安装客户端依赖..."
    cd client && npm install --silent 2>/dev/null && cd ..
fi

if [ ! -d "frontend/node_modules" ]; then
    echo "📦 安装管理端依赖..."
    cd frontend && npm install --silent 2>/dev/null && cd ..
fi

log_success "前端依赖完成"

# 配置文件
echo "⚙️ 生成配置..."
cat > ports.env << ENVEOF
BACKEND_PORT=$BACKEND_PORT
CLIENT_PORT=$CLIENT_PORT
FRONTEND_PORT=$FRONTEND_PORT
ENVEOF

mkdir -p logs
log_success "配置完成"

echo ""
echo "🎉 快速部署完成！"
echo ""
echo "📊 服务地址:"
echo "  🔗 API:     http://localhost:$BACKEND_PORT"
echo "  📱 客户端:   http://localhost:$CLIENT_PORT"
echo "  🖥️ 管理端:   http://localhost:$FRONTEND_PORT"
echo ""
echo "🚀 启动方式: ./start-dev.sh"
echo ""
