#!/bin/bash

# 股票分析系统 - 固定端口配置脚本
# Stock Analysis System - Fixed Port Configuration Script

set -e

echo "🛠️  股票分析系统 - 固定端口开发环境配置"
echo "========================================="
echo "🎯 目标：使用固定端口，提供端口冲突处理选项"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✅]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[⚠️]${NC} $1"
}

log_error() {
    echo -e "${RED}[❌]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# ==================== 1. 固定端口配置与冲突处理 ====================
log_step "1️⃣ 固定端口配置与冲突处理"

# 固定端口配置
DEFAULT_BACKEND_PORT=3007
DEFAULT_CLIENT_PORT=8005  
DEFAULT_FRONTEND_PORT=8006

echo "🎯 默认固定端口配置:"
echo "  📊 API服务: $DEFAULT_BACKEND_PORT"
echo "  📱 客户端: $DEFAULT_CLIENT_PORT" 
echo "  🖥️  管理端: $DEFAULT_FRONTEND_PORT"
echo ""

# 端口占用处理函数
handle_port_conflict() {
    local port=$1
    local service_name=$2
    
    if lsof -ti:$port &>/dev/null; then
        local pid=$(lsof -ti:$port)
        local process_info=$(ps -p $pid -o comm= 2>/dev/null || echo "未知进程")
        
        echo ""
        log_warn "端口 $port ($service_name) 被占用"
        echo "  占用进程: $process_info (PID: $pid)"
        echo ""
        echo "🔧 处理选项:"
        echo "  1) Kill 占用进程，继续使用端口 $port (推荐)"
        echo "  2) 使用新端口（自动分配）"
        echo "  3) 手动指定端口"
        echo ""
        
        while true; do
            read -p "请选择处理方式 [1-3]: " choice
            case $choice in
                1)
                    log_info "正在终止占用进程 $pid..."
                    if kill -9 $pid 2>/dev/null; then
                        sleep 2
                        if ! lsof -ti:$port &>/dev/null; then
                            log_success "端口 $port 已释放，继续使用固定端口"
                            echo $port
                            return 0
                        else
                            log_error "进程终止失败，进程可能受保护"
                            return 1
                        fi
                    else
                        log_error "无法终止进程，权限不足"
                        return 1
                    fi
                    ;;
                2)
                    local new_port=$(find_available_port $((port + 1)) "$service_name")
                    if [ $? -eq 0 ]; then
                        log_success "分配新端口: $new_port"
                        echo $new_port
                        return 0
                    else
                        log_error "无法找到可用端口"
                        return 1
                    fi
                    ;;
                3)
                    while true; do
                        read -p "请输入新端口号 (1024-65535): " custom_port
                        if [[ "$custom_port" =~ ^[0-9]+$ ]] && [ "$custom_port" -ge 1024 ] && [ "$custom_port" -le 65535 ]; then
                            if ! lsof -ti:$custom_port &>/dev/null; then
                                log_success "使用自定义端口: $custom_port"
                                echo $custom_port
                                return 0
                            else
                                log_error "端口 $custom_port 已被占用，请选择其他端口"
                            fi
                        else
                            log_error "无效端口号，请输入1024-65535之间的数字"
                        fi
                    done
                    ;;
                *)
                    log_error "无效选择，请输入1、2或3"
                    ;;
            esac
        done
    else
        log_success "$service_name 端口 $port 可用"
        echo $port
        return 0
    fi
}

# 查找可用端口函数  
find_available_port() {
    local base_port=$1
    local service_name=$2
    
    for i in {0..20}; do
        local test_port=$((base_port + i))
        if ! lsof -ti:$test_port &>/dev/null; then
            echo $test_port
            return 0
        fi
    done
    
    log_error "无法找到 $service_name 的可用端口（基础端口: $base_port）"
    return 1
}

# 处理各服务端口
echo "正在检查端口占用情况..."
BACKEND_PORT=$(handle_port_conflict $DEFAULT_BACKEND_PORT "API服务")
CLIENT_PORT=$(handle_port_conflict $DEFAULT_CLIENT_PORT "客户端")
FRONTEND_PORT=$(handle_port_conflict $DEFAULT_FRONTEND_PORT "管理端")

echo ""
log_success "端口配置完成:"
echo "  📊 API服务: $BACKEND_PORT"
echo "  📱 客户端: $CLIENT_PORT"
echo "  🖥️  管理端: $FRONTEND_PORT"

# ==================== 2. 数据库配置检查 ====================
log_step "2️⃣ 数据库连接检查"

log_info "检测MySQL服务状态..."
if ! mysqladmin ping -h127.0.0.1 --silent; then
    log_error "MySQL 服务未启动，请先启动MySQL服务"
    exit 1
fi

log_info "尝试检测MySQL连接参数..."
mysql_hosts=("127.0.0.1" "localhost")
mysql_users=("root")
mysql_passwords=("" "password" "123456" "Pp123456")

mysql_host=""
mysql_user=""
mysql_password=""

for host in "${mysql_hosts[@]}"; do
    for user in "${mysql_users[@]}"; do
        for password in "${mysql_passwords[@]}"; do
            if mysql -h$host -u$user -p$password -e "SELECT 1;" &>/dev/null; then
                mysql_host=$host
                mysql_user=$user
                mysql_password=$password
                break 3
            fi
        done
    done
done

if [ -z "$mysql_host" ]; then
    log_error "无法连接到MySQL数据库，请检查MySQL配置"
    exit 1
fi

log_success "找到有效的MySQL连接: $mysql_user@$mysql_host"

log_info "创建数据库（如果不存在）..."
mysql -h$mysql_host -u$mysql_user -p$mysql_password -e "CREATE DATABASE IF NOT EXISTS stock_analysis_dev;" 2>/dev/null

# ==================== 3. 更新配置文件 ====================
log_step "3️⃣ 更新配置文件"

# 更新环境配置文件
log_info "更新后端环境配置..."
cat > "backend/.env" << EOF
# 数据库配置
DATABASE_HOST=$mysql_host
DATABASE_USER=$mysql_user
DATABASE_PASSWORD=$mysql_password
DATABASE_NAME=stock_analysis_dev

# JWT配置
SECRET_KEY=your-secret-key-here-please-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS配置
ALLOWED_ORIGINS=["http://localhost:$CLIENT_PORT","http://127.0.0.1:$CLIENT_PORT","http://localhost:$FRONTEND_PORT","http://127.0.0.1:$FRONTEND_PORT","http://localhost:3000","http://127.0.0.1:3000"]

# 支付配置
PAYMENT_ENABLED=true
PAYMENT_MOCK_MODE=true
EOF

log_success "环境配置文件更新完成"

# 更新Vite配置文件
log_info "更新客户端Vite配置..."
cat > "client/vite.config.ts" << EOF
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
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

log_info "更新管理端Vite配置..."
cat > "frontend/vite.config.ts" << EOF
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
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

log_success "Vite配置文件更新完成"

# 更新性能配置文件（如果存在）
if [ -f "frontend/vite.config.performance.ts" ]; then
    log_info "更新管理端性能配置..."
    sed -i.bak "s/target: 'http:\/\/127\.0\.0\.1:[0-9]*'/target: 'http:\/\/127.0.0.1:$BACKEND_PORT'/g" "frontend/vite.config.performance.ts"
    log_success "性能配置更新完成"
fi

# ==================== 4. 创建端口配置文件 ====================
cat > "dev-ports.env" << EOF
# 固定端口配置 - 自动生成
BACKEND_PORT=$BACKEND_PORT
CLIENT_PORT=$CLIENT_PORT
FRONTEND_PORT=$FRONTEND_PORT
EOF

# ==================== 5. 创建启动脚本 ====================
log_step "5️⃣ 创建启动和停止脚本"

# 创建固定端口启动脚本
cat > "start-fixed.sh" << EOF
#!/bin/bash

# 固定端口启动脚本
source dev-ports.env

echo "🚀 启动股票分析系统 (固定端口版)"
echo "================================"
echo "📊 端口配置:"
echo "  - API服务: \$BACKEND_PORT"
echo "  - 客户端: \$CLIENT_PORT" 
echo "  - 管理端: \$FRONTEND_PORT"
echo ""

# 创建日志目录
mkdir -p logs

# 启动后端服务
echo "🔧 启动后端API服务..."
cd backend
source venv/bin/activate 2>/dev/null || {
    echo "⚠️  虚拟环境不存在，正在创建..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
}
nohup python -m uvicorn app.main:app --reload --host 0.0.0.0 --port \$BACKEND_PORT > ../logs/backend.log 2>&1 &
echo \$! > ../logs/backend.pid
cd ..

# 启动客户端服务
echo "🎨 启动客户端服务..."
cd client
if [ ! -d "node_modules" ]; then
    echo "⚠️  客户端依赖不存在，正在安装..."
    npm install
fi
nohup npm run dev > ../logs/client.log 2>&1 &
echo \$! > ../logs/client.pid
cd ..

# 启动管理端服务
echo "🖥️ 启动管理端服务..."
cd frontend  
if [ ! -d "node_modules" ]; then
    echo "⚠️  管理端依赖不存在，正在安装..."
    npm install
fi
nohup npm run dev > ../logs/frontend.log 2>&1 &
echo \$! > ../logs/frontend.pid
cd ..

echo ""
echo "✅ 所有服务启动完成！"
echo ""
echo "📊 访问地址:"
echo "  🔗 API文档:  http://localhost:\$BACKEND_PORT/docs"
echo "  📱 客户端:   http://localhost:\$CLIENT_PORT"
echo "  🖥️ 管理端:   http://localhost:\$FRONTEND_PORT"
echo ""
echo "🛑 停止服务: ./stop-fixed.sh"
echo "🔍 查看状态: ./debug-issues.sh"
EOF

# 创建固定端口停止脚本
cat > "stop-fixed.sh" << EOF
#!/bin/bash

# 固定端口停止脚本
echo "🛑 停止所有服务..."

# 停止进程函数
stop_service() {
    local pid_file=\$1
    local service_name=\$2
    
    if [ -f "\$pid_file" ]; then
        local pid=\$(cat "\$pid_file")
        if kill -0 "\$pid" 2>/dev/null; then
            kill "\$pid" 2>/dev/null
            sleep 2
            if kill -0 "\$pid" 2>/dev/null; then
                kill -9 "\$pid" 2>/dev/null
            fi
            echo "✅ \$service_name 服务已停止 (PID: \$pid)"
        fi
        rm -f "\$pid_file"
    fi
}

stop_service "logs/backend.pid" "backend"
stop_service "logs/client.pid" "client"  
stop_service "logs/frontend.pid" "frontend"

# 清理固定端口
source dev-ports.env 2>/dev/null
for port in \$BACKEND_PORT \$CLIENT_PORT \$FRONTEND_PORT; do
    if [ ! -z "\$port" ] && lsof -ti:\$port &>/dev/null; then
        lsof -ti:\$port | xargs kill -9 2>/dev/null
    fi
done

echo "🎉 所有服务已停止"
EOF

chmod +x start-fixed.sh stop-fixed.sh

log_success "启动和停止脚本创建完成"

# ==================== 6. 完成提示 ====================
echo ""
log_step "🎉 固定端口配置完成！"
echo ""
echo "📋 生成的工具："
echo "  🔧 ./setup-fixed-ports.sh  - 重新配置固定端口（本脚本）"
echo "  🚀 ./start-fixed.sh        - 启动所有服务（固定端口）"
echo "  🛑 ./stop-fixed.sh         - 停止所有服务"
echo "  🔍 ./debug-issues.sh       - 问题检测工具"
echo "  📄 ./dev-ports.env         - 端口配置文件"
echo ""
echo "🎯 固定端口配置："
echo "  📊 API服务端口:    $BACKEND_PORT"
echo "  📱 客户端端口:     $CLIENT_PORT"
echo "  🖥️  管理端端口:     $FRONTEND_PORT"
echo ""
echo "🚀 使用方法："
echo "  启动系统: ./start-fixed.sh"
echo "  停止系统: ./stop-fixed.sh"
echo ""
log_success "🎉 配置完成！现在可以使用 ./start-fixed.sh 启动系统了！"