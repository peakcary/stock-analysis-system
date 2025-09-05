#!/bin/bash

# 股票分析系统 - 一键部署脚本
echo "🚀 股票分析系统 - 一键部署"
echo "=========================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✅]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[⚠️]${NC} $1"; }
log_error() { echo -e "${RED}[❌]${NC} $1"; }

# 固定端口配置
BACKEND_PORT=3007
CLIENT_PORT=8005
FRONTEND_PORT=8006

echo "📊 固定端口配置: API($BACKEND_PORT) | 客户端($CLIENT_PORT) | 管理端($FRONTEND_PORT)"
echo ""

# ==================== 1. 环境检测 ====================
log_info "🔍 环境依赖检测..."

# 检查 Node.js
if ! command -v node &> /dev/null; then
    log_error "Node.js 未安装"
    echo "请安装 Node.js (推荐 v18+):"
    echo "  macOS: brew install node"
    echo "  或访问: https://nodejs.org/"
    exit 1
else
    NODE_VERSION=$(node --version)
    log_success "Node.js 已安装: $NODE_VERSION"
fi

# 检查 Python3
if ! command -v python3 &> /dev/null; then
    log_error "Python3 未安装"
    echo "请安装 Python3 (推荐 v3.11+):"
    echo "  macOS: brew install python"
    echo "  或访问: https://python.org/"
    exit 1
else
    PYTHON_VERSION=$(python3 --version)
    log_success "Python3 已安装: $PYTHON_VERSION"
fi

# 检查 MySQL
if ! command -v mysql &> /dev/null; then
    log_error "MySQL 未安装"
    echo "请安装 MySQL (推荐 v8.0+):"
    echo "  macOS: brew install mysql"
    echo "  或访问: https://dev.mysql.com/downloads/"
    exit 1
else
    MYSQL_VERSION=$(mysql --version | cut -d' ' -f3 | cut -d',' -f1)
    log_success "MySQL 已安装: $MYSQL_VERSION"
fi

# 检查 MySQL 服务状态
log_info "检查 MySQL 服务状态..."
if ! mysqladmin ping -h127.0.0.1 --silent 2>/dev/null; then
    log_warn "MySQL 服务未启动，正在尝试启动..."
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew services start mysql 2>/dev/null || {
            log_error "MySQL 服务启动失败"
            echo "请手动启动 MySQL 服务:"
            echo "  brew services start mysql"
            exit 1
        }
    else
        log_error "请手动启动 MySQL 服务"
        exit 1
    fi
    
    sleep 3
    if ! mysqladmin ping -h127.0.0.1 --silent 2>/dev/null; then
        log_error "MySQL 服务启动失败，请检查配置"
        exit 1
    fi
fi

log_success "MySQL 服务运行正常"

# ==================== 2. 数据库检查 ====================
log_info "🗄️ 检查数据库..."

log_success "数据库配置已在程序中预设"

# ==================== 3. 后端环境配置 ====================
log_info "🔧 配置后端环境..."

cd backend

# 创建虚拟环境
if [ ! -d "venv" ]; then
    log_info "创建 Python 虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境并安装依赖
log_info "安装后端依赖..."
source venv/bin/activate
pip install -r requirements.txt > /dev/null 2>&1

if [ $? -ne 0 ]; then
    log_error "后端依赖安装失败"
    echo "请检查网络连接或手动执行:"
    echo "  cd backend && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

log_success "后端依赖安装完成"

# 创建环境配置文件
log_info "创建后端环境配置..."
cat > .env << EOF
# JWT 配置
SECRET_KEY=your-secret-key-here-please-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS 配置
ALLOWED_ORIGINS=["http://localhost:$CLIENT_PORT","http://127.0.0.1:$CLIENT_PORT","http://localhost:$FRONTEND_PORT","http://127.0.0.1:$FRONTEND_PORT"]

# 支付配置
PAYMENT_ENABLED=true
PAYMENT_MOCK_MODE=true
EOF

log_success "后端环境配置完成 (数据库配置已内置在程序中)"

# 数据库初始化
log_info "初始化数据库..."
cd ..
./init-database.sh
cd backend

cd ..

# ==================== 4. 前端环境配置 ====================
log_info "🎨 配置前端环境..."

# 安装客户端依赖
if [ ! -d "client/node_modules" ]; then
    log_info "安装客户端依赖..."
    cd client
    npm install > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        log_error "客户端依赖安装失败"
        echo "请手动执行: cd client && npm install"
        exit 1
    fi
    cd ..
    log_success "客户端依赖安装完成"
fi

# 安装管理端依赖
if [ ! -d "frontend/node_modules" ]; then
    log_info "安装管理端依赖..."
    cd frontend
    npm install > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        log_error "管理端依赖安装失败"
        echo "请手动执行: cd frontend && npm install"
        exit 1
    fi
    cd ..
    log_success "管理端依赖安装完成"
fi

# ==================== 5. 配置文件生成 ====================
log_info "⚙️ 生成配置文件..."

# 客户端 Vite 配置
cat > client/vite.config.ts << EOF
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: $CLIENT_PORT,
    host: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:$BACKEND_PORT',
        changeOrigin: true,
        secure: false
      }
    }
  }
})
EOF

# 管理端 Vite 配置
cat > frontend/vite.config.ts << EOF
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: $FRONTEND_PORT,
    host: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:$BACKEND_PORT',
        changeOrigin: true,
        secure: false
      }
    }
  }
})
EOF

# 端口配置文件
cat > ports.env << EOF
BACKEND_PORT=$BACKEND_PORT
CLIENT_PORT=$CLIENT_PORT
FRONTEND_PORT=$FRONTEND_PORT
EOF

# 创建日志目录
mkdir -p logs

log_success "配置文件生成完成"

# ==================== 6. 完成提示 ====================
echo ""
echo "🎉 部署完成！"
echo "=============="
echo ""
echo "📊 服务配置:"
echo "  🔗 API服务:  http://localhost:$BACKEND_PORT"
echo "  📱 客户端:   http://localhost:$CLIENT_PORT"
echo "  🖥️ 管理端:   http://localhost:$FRONTEND_PORT"
echo ""
echo "📋 下一步:"
echo "  ▶️  启动系统: ./start.sh"
echo "  🛑 停止系统: ./stop.sh"
echo ""
log_success "系统部署完成，可以开始使用了！"