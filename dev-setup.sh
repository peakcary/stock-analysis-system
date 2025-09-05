#!/bin/bash

# 股票概念分析系统 - 开发环境一键配置脚本
# 解决换电脑开发时的端口、接口、数据库等问题

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 日志函数
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✅]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[⚠️]${NC} $1"; }
log_error() { echo -e "${RED}[❌]${NC} $1"; }
log_step() { echo -e "\n${CYAN}[STEP]${NC} $1\n"; }

echo "🛠️  股票分析系统 - 开发环境自动配置"
echo "========================================"
echo "🎯 目标：解决换电脑开发时的所有环境问题"
echo ""

# ==================== 1. 端口冲突智能检测与解决 ====================
log_step "1️⃣ 检测并解决端口冲突问题"

# 智能端口检测函数
find_available_port() {
    local base_port=$1
    local service_name=$2
    
    for i in {0..10}; do
        local test_port=$((base_port + i))
        if ! lsof -ti:$test_port &>/dev/null; then
            echo $test_port
            return 0
        fi
    done
    
    log_error "无法找到 $service_name 的可用端口（基础端口: $base_port）"
    return 1
}

# 清理占用端口的函数
cleanup_port() {
    local port=$1
    local service_name=$2
    
    if lsof -ti:$port &>/dev/null; then
        log_warn "$service_name 端口 $port 被占用，正在清理..."
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
        sleep 2
        
        if lsof -ti:$port &>/dev/null; then
            log_error "端口 $port 清理失败，进程可能受到保护"
            return 1
        else
            log_success "端口 $port 清理成功"
        fi
    else
        log_success "$service_name 端口 $port 可用"
    fi
    return 0
}

# 检测并配置端口
BACKEND_PORT=$(find_available_port 3007 "后端API")
FRONTEND_PORT=$(find_available_port 8005 "后端管理")
CLIENT_PORT=$(find_available_port 8006 "客户端")

# 清理端口
cleanup_port $BACKEND_PORT "后端API"
cleanup_port $FRONTEND_PORT "后端管理"  
cleanup_port $CLIENT_PORT "客户端"

log_success "端口分配完成: API($BACKEND_PORT) | 管理($FRONTEND_PORT) | 客户端($CLIENT_PORT)"

# ==================== 2. 数据库智能配置 ====================
log_step "2️⃣ 检测并配置数据库连接"

# 数据库配置检测
detect_database_config() {
    local config_file="backend/.env"
    
    # 检测MySQL服务
    log_info "检测MySQL服务状态..."
    
    # 尝试不同的MySQL连接方式
    local mysql_hosts=("127.0.0.1" "localhost")
    local mysql_users=("root" "stock_user")
    local mysql_passwords=("" "Pp123456" "root" "123456")
    local mysql_host=""
    local mysql_user=""
    local mysql_password=""
    
    log_info "尝试检测MySQL连接参数..."
    
    for host in "${mysql_hosts[@]}"; do
        for user in "${mysql_users[@]}"; do
            for password in "${mysql_passwords[@]}"; do
                if [ -z "$password" ]; then
                    test_cmd="mysql -h$host -u$user -e 'SELECT 1;' 2>/dev/null"
                else
                    test_cmd="mysql -h$host -u$user -p$password -e 'SELECT 1;' 2>/dev/null"
                fi
                
                if eval $test_cmd; then
                    mysql_host=$host
                    mysql_user=$user
                    mysql_password=$password
                    log_success "找到有效的MySQL连接: $user@$host"
                    break 3
                fi
            done
        done
    done
    
    if [ -z "$mysql_host" ]; then
        log_warn "无法自动检测MySQL连接，将尝试启动MySQL服务..."
        
        # 尝试启动MySQL服务
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            brew services start mysql@8.0 2>/dev/null || brew services start mysql 2>/dev/null || {
                log_error "请手动启动MySQL服务: brew services start mysql@8.0"
                return 1
            }
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            # Linux
            sudo systemctl start mysql 2>/dev/null || sudo service mysql start 2>/dev/null || {
                log_error "请手动启动MySQL服务: sudo systemctl start mysql"
                return 1
            }
        fi
        
        sleep 3
        
        # 重新检测
        mysql_host="127.0.0.1"
        mysql_user="root"
        mysql_password="Pp123456"
    fi
    
    # 创建数据库（如果不存在）
    log_info "创建数据库（如果不存在）..."
    local create_db_cmd
    if [ -z "$mysql_password" ]; then
        create_db_cmd="mysql -h$mysql_host -u$mysql_user -e"
    else
        create_db_cmd="mysql -h$mysql_host -u$mysql_user -p$mysql_password -e"
    fi
    
    $create_db_cmd "CREATE DATABASE IF NOT EXISTS stock_analysis_dev CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>/dev/null || {
        log_warn "数据库创建可能失败，请手动创建数据库"
    }
    
    log_success "数据库配置检测完成: $mysql_user@$mysql_host"
    
    # 更新环境配置文件
    update_env_config "$mysql_host" "$mysql_user" "$mysql_password"
}

# 更新环境配置
update_env_config() {
    local host=$1
    local user=$2
    local password=$3
    local config_file="backend/.env"
    
    log_info "更新环境配置文件..."
    
    # 创建.env文件（如果不存在）
    if [ ! -f "$config_file" ]; then
        cp backend/.env.example "$config_file" 2>/dev/null || {
            log_info "创建新的环境配置文件..."
            touch "$config_file"
        }
    fi
    
    # 动态生成数据库URL
    local database_url="mysql+pymysql://$user:$password@$host:3306/stock_analysis_dev"
    
    # 更新配置文件
    cat > "$config_file" << EOF
# 应用基本配置
APP_NAME=股票概念分析系统
APP_VERSION=1.0.0
DEBUG=true

# 服务器配置 - 动态端口
HOST=0.0.0.0
PORT=$BACKEND_PORT

# 数据库配置 - 自动检测
DATABASE_URL=$database_url
DATABASE_HOST=$host
DATABASE_PORT=3306
DATABASE_USER=$user
DATABASE_PASSWORD=$password
DATABASE_NAME=stock_analysis_dev

# JWT 配置
SECRET_KEY=dev-secret-key-$(openssl rand -hex 16)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS 配置 - 动态端口
ALLOWED_ORIGINS=["http://localhost:$CLIENT_PORT","http://127.0.0.1:$CLIENT_PORT","http://localhost:$FRONTEND_PORT","http://127.0.0.1:$FRONTEND_PORT","http://localhost:3000","http://127.0.0.1:3000"]

# 分页配置
DEFAULT_PAGE_SIZE=10
MAX_PAGE_SIZE=100

# 文件上传配置
MAX_FILE_SIZE=104857600
UPLOAD_DIR=uploads

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# 支付配置
PAYMENT_ORDER_TIMEOUT_HOURS=2
PAYMENT_ENABLED=true
PAYMENT_MOCK_MODE=true
EOF

    log_success "环境配置文件更新完成"
}

# 执行数据库配置
detect_database_config

# ==================== 3. 前端配置自动化 ====================
log_step "3️⃣ 配置前端服务端口"

# 更新前端package.json脚本
update_frontend_ports() {
    local client_package="client/package.json"
    local frontend_package="frontend/package.json"
    
    # 更新客户端端口
    if [ -f "$client_package" ]; then
        log_info "更新客户端端口配置..."
        sed -i.bak "s/--port [0-9]*/--port $CLIENT_PORT/g" "$client_package"
        log_success "客户端端口设置为: $CLIENT_PORT"
    fi
    
    # 更新后端管理端口
    if [ -f "$frontend_package" ]; then
        log_info "更新后端管理端口配置..."
        sed -i.bak "s/--port [0-9]*/--port $FRONTEND_PORT/g" "$frontend_package"
        log_success "后端管理端口设置为: $FRONTEND_PORT"
    fi
}

update_frontend_ports

# ==================== 4. API接口配置自动更新 ====================
log_step "4️⃣ 更新前端API接口配置"

# 更新前端API基础URL
update_api_config() {
    local client_auth_file="client/src/utils/auth.ts"
    local frontend_api_files=$(find frontend/src -name "*.ts" -o -name "*.tsx" | grep -E "(api|service)" || true)
    
    # 更新客户端API配置
    if [ -f "$client_auth_file" ]; then
        log_info "更新客户端API配置..."
        
        # 备份原文件
        cp "$client_auth_file" "$client_auth_file.bak"
        
        # 更新API基础URL
        sed -i.tmp "s/localhost:[0-9]*/localhost:$BACKEND_PORT/g" "$client_auth_file"
        sed -i.tmp "s/127\.0\.0\.1:[0-9]*/127.0.0.1:$BACKEND_PORT/g" "$client_auth_file"
        
        log_success "客户端API配置更新完成"
    fi
    
    # 更新后端管理API配置
    if [ ! -z "$frontend_api_files" ]; then
        log_info "更新后端管理API配置..."
        
        while IFS= read -r file; do
            if [ -f "$file" ]; then
                cp "$file" "$file.bak"
                sed -i.tmp "s/localhost:[0-9]*/localhost:$BACKEND_PORT/g" "$file"
                sed -i.tmp "s/127\.0\.0\.1:[0-9]*/127.0.0.1:$BACKEND_PORT/g" "$file"
            fi
        done <<< "$frontend_api_files"
        
        log_success "后端管理API配置更新完成"
    fi
    
    # 更新Vite配置文件中的代理设置
    log_info "更新Vite配置文件中的API代理设置..."
    
    # 更新客户端Vite配置
    if [ -f "client/vite.config.ts" ]; then
        cp "client/vite.config.ts" "client/vite.config.ts.bak"
        sed -i.tmp "s/target: 'http:\/\/127\.0\.0\.1:[0-9]*'/target: 'http:\/\/127.0.0.1:$BACKEND_PORT'/g" "client/vite.config.ts"
        sed -i.tmp "s/port: [0-9]*/port: $CLIENT_PORT/g" "client/vite.config.ts"
        rm -f "client/vite.config.ts.tmp"
        log_success "客户端Vite配置更新完成"
    fi
    
    # 更新管理端Vite配置
    if [ -f "frontend/vite.config.ts" ]; then
        cp "frontend/vite.config.ts" "frontend/vite.config.ts.bak"
        sed -i.tmp "s/target: 'http:\/\/127\.0\.0\.1:[0-9]*'/target: 'http:\/\/127.0.0.1:$BACKEND_PORT'/g" "frontend/vite.config.ts"
        sed -i.tmp "s/port: [0-9]*/port: $FRONTEND_PORT/g" "frontend/vite.config.ts"
        rm -f "frontend/vite.config.ts.tmp"
        log_success "管理端Vite配置更新完成"
    fi
    
    # 更新管理端性能配置文件（如果存在）
    if [ -f "frontend/vite.config.performance.ts" ]; then
        cp "frontend/vite.config.performance.ts" "frontend/vite.config.performance.ts.bak"
        sed -i.tmp "s/target: 'http:\/\/127\.0\.0\.1:[0-9]*'/target: 'http:\/\/127.0.0.1:$BACKEND_PORT'/g" "frontend/vite.config.performance.ts"
        rm -f "frontend/vite.config.performance.ts.tmp"
        log_success "管理端性能配置更新完成"
    fi
}

update_api_config

# ==================== 5. 依赖检查和自动安装 ====================
log_step "5️⃣ 检查和安装项目依赖"

# 检查Node.js依赖
check_node_deps() {
    local dir=$1
    local service_name=$2
    
    if [ -d "$dir" ] && [ -f "$dir/package.json" ]; then
        log_info "检查 $service_name 依赖..."
        
        cd "$dir"
        
        if [ ! -d "node_modules" ] || [ ! -f "package-lock.json" ]; then
            log_warn "$service_name 依赖不完整，正在安装..."
            npm install
            log_success "$service_name 依赖安装完成"
        else
            log_success "$service_name 依赖已存在"
        fi
        
        cd - > /dev/null
    fi
}

# 检查Python依赖
check_python_deps() {
    log_info "检查后端Python依赖..."
    
    if [ -d "backend" ]; then
        cd backend
        
        # 创建虚拟环境（如果不存在）
        if [ ! -d "venv" ]; then
            log_warn "Python虚拟环境不存在，正在创建..."
            python3 -m venv venv
            log_success "Python虚拟环境创建完成"
        fi
        
        # 激活虚拟环境并安装依赖
        source venv/bin/activate
        
        # 检查关键依赖
        if ! python -c "import fastapi, sqlalchemy, pymysql" 2>/dev/null; then
            log_warn "后端依赖不完整，正在安装..."
            pip install -r requirements.txt
            log_success "后端依赖安装完成"
        else
            log_success "后端依赖已存在"
        fi
        
        cd - > /dev/null
    fi
}

check_node_deps "client" "客户端"
check_node_deps "frontend" "后端管理"
check_python_deps

# ==================== 6. 创建智能启动脚本 ====================
log_step "6️⃣ 创建智能启动脚本"

# 生成动态启动脚本
create_smart_start_script() {
    cat > "smart-start.sh" << 'EOF'
#!/bin/bash

# 智能启动脚本 - 自动使用配置的端口
source dev-ports.env

echo "🚀 启动股票分析系统 (智能配置版)"
echo "================================"
echo "📊 端口配置:"
echo "  - API服务: $BACKEND_PORT"
echo "  - 客户端: $CLIENT_PORT" 
echo "  - 管理端: $FRONTEND_PORT"
echo ""

# 创建日志目录
mkdir -p logs

# 启动后端服务
echo "🔧 启动后端API服务..."
cd backend
source venv/bin/activate
nohup python -m uvicorn app.main:app --reload --host 0.0.0.0 --port $BACKEND_PORT > ../logs/backend.log 2>&1 &
echo $! > ../logs/backend.pid
cd ..

# 启动前端服务
echo "🎨 启动前端服务..."
cd client
nohup npm run dev > ../logs/client.log 2>&1 &
echo $! > ../logs/client.pid
cd ..

# 启动管理端
echo "🖥️ 启动管理端服务..."
cd frontend  
nohup npm run dev > ../logs/frontend.log 2>&1 &
echo $! > ../logs/frontend.pid
cd ..

echo ""
echo "✅ 所有服务启动完成！"
echo ""
echo "📊 访问地址:"
echo "  🔗 API文档:  http://localhost:$BACKEND_PORT/docs"
echo "  📱 客户端:   http://localhost:$CLIENT_PORT"
echo "  🖥️ 管理端:   http://localhost:$FRONTEND_PORT"
echo ""
echo "🛑 停止服务: ./smart-stop.sh"
EOF

    chmod +x smart-start.sh
    
    # 生成端口配置文件
    cat > "dev-ports.env" << EOF
# 开发环境端口配置 - 自动生成
BACKEND_PORT=$BACKEND_PORT
CLIENT_PORT=$CLIENT_PORT  
FRONTEND_PORT=$FRONTEND_PORT
EOF
    
    log_success "智能启动脚本创建完成"
}

create_smart_start_script

# ==================== 7. 创建问题检测脚本 ====================
log_step "7️⃣ 创建问题自动检测脚本"

cat > "debug-issues.sh" << 'EOF'
#!/bin/bash

# 问题自动检测和修复脚本
source dev-ports.env 2>/dev/null || {
    echo "❌ 请先运行 ./dev-setup.sh 配置开发环境"
    exit 1
}

echo "🔍 开发环境问题自动检测"
echo "========================"

# 检查端口占用
check_ports() {
    echo "📡 检查端口状态..."
    
    for port in $BACKEND_PORT $CLIENT_PORT $FRONTEND_PORT; do
        if lsof -ti:$port &>/dev/null; then
            pid=$(lsof -ti:$port)
            process_name=$(ps -p $pid -o comm= 2>/dev/null || echo "未知进程")
            echo "  ⚠️  端口 $port 被占用 (PID: $pid, 进程: $process_name)"
        else
            echo "  ✅ 端口 $port 可用"
        fi
    done
}

# 检查数据库连接
check_database() {
    echo "🗄️ 检查数据库连接..."
    
    if [ -f "backend/.env" ]; then
        source backend/.env
        if mysql -h$DATABASE_HOST -u$DATABASE_USER -p$DATABASE_PASSWORD -e "USE $DATABASE_NAME; SELECT 1;" &>/dev/null; then
            echo "  ✅ 数据库连接正常"
        else
            echo "  ❌ 数据库连接失败"
            echo "  💡 建议: 运行 ./dev-setup.sh 重新配置数据库"
        fi
    else
        echo "  ❌ 环境配置文件不存在"
    fi
}

# 检查依赖
check_dependencies() {
    echo "📦 检查项目依赖..."
    
    # 检查后端依赖
    if [ -d "backend/venv" ]; then
        cd backend
        source venv/bin/activate
        if python -c "import fastapi, sqlalchemy, pymysql" 2>/dev/null; then
            echo "  ✅ 后端依赖完整"
        else
            echo "  ❌ 后端依赖缺失"
        fi
        cd ..
    else
        echo "  ❌ 后端虚拟环境不存在"
    fi
    
    # 检查前端依赖
    for dir in "client" "frontend"; do
        if [ -d "$dir/node_modules" ]; then
            echo "  ✅ $dir 依赖完整"
        else
            echo "  ❌ $dir 依赖缺失"
        fi
    done
}

# 检查服务状态
check_services() {
    echo "🚀 检查服务运行状态..."
    
    services=("$BACKEND_PORT:API服务" "$CLIENT_PORT:客户端" "$FRONTEND_PORT:管理端")
    
    for service in "${services[@]}"; do
        port=$(echo $service | cut -d: -f1)
        name=$(echo $service | cut -d: -f2)
        
        if curl -s "http://localhost:$port" &>/dev/null; then
            echo "  ✅ $name (端口 $port) 运行正常"
        else
            echo "  ❌ $name (端口 $port) 无响应"
        fi
    done
}

# 执行所有检查
check_ports
echo ""
check_database  
echo ""
check_dependencies
echo ""
check_services

echo ""
echo "🛠️ 快速修复建议:"
echo "  重新配置环境: ./dev-setup.sh"
echo "  启动所有服务: ./smart-start.sh"  
echo "  停止所有服务: ./smart-stop.sh"
EOF

chmod +x debug-issues.sh

# ==================== 8. 创建智能停止脚本 ====================
cat > "smart-stop.sh" << 'EOF'
#!/bin/bash

# 智能停止脚本
source dev-ports.env 2>/dev/null

echo "🛑 停止所有服务..."

# 从PID文件停止
for service in "backend" "client" "frontend"; do
    if [ -f "logs/$service.pid" ]; then
        pid=$(cat "logs/$service.pid")
        if kill -0 $pid 2>/dev/null; then
            kill $pid 2>/dev/null
            echo "✅ $service 服务已停止 (PID: $pid)"
        fi
        rm -f "logs/$service.pid"
    fi
done

# 通过端口清理残留进程
if [ ! -z "$BACKEND_PORT" ]; then
    lsof -ti:$BACKEND_PORT | xargs kill -9 2>/dev/null || true
fi
if [ ! -z "$CLIENT_PORT" ]; then
    lsof -ti:$CLIENT_PORT | xargs kill -9 2>/dev/null || true
fi  
if [ ! -z "$FRONTEND_PORT" ]; then
    lsof -ti:$FRONTEND_PORT | xargs kill -9 2>/dev/null || true
fi

echo "🎉 所有服务已停止"
EOF

chmod +x smart-stop.sh

# ==================== 完成配置 ====================
log_step "🎉 开发环境配置完成！"

echo "📋 生成的智能开发工具："
echo "  🔧 ./dev-setup.sh     - 重新配置开发环境（本脚本）"
echo "  🚀 ./smart-start.sh   - 智能启动所有服务" 
echo "  🛑 ./smart-stop.sh    - 智能停止所有服务"
echo "  🔍 ./debug-issues.sh  - 自动检测和修复问题"
echo "  📄 ./dev-ports.env    - 端口配置文件"
echo ""

echo "🎯 使用方法："
echo "  1️⃣ 首次使用: ./dev-setup.sh"
echo "  2️⃣ 日常启动: ./smart-start.sh"  
echo "  3️⃣ 遇到问题: ./debug-issues.sh"
echo "  4️⃣ 停止服务: ./smart-stop.sh"
echo ""

echo "✅ 当前配置："
echo "  📊 API服务端口:    $BACKEND_PORT"
echo "  📱 客户端端口:     $CLIENT_PORT"
echo "  🖥️  管理端端口:     $FRONTEND_PORT"
echo "  🗄️ 数据库:        已自动配置"
echo ""

log_success "🎉 开发环境配置完成！现在可以使用 ./smart-start.sh 启动系统了！"