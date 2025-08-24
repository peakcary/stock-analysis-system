#!/bin/bash
# 股票分析系统一键部署脚本
# Stock Analysis System One-Click Deployment Script

set -e

echo "🚀 股票分析系统一键部署开始..."
echo "📅 部署时间: $(date)"
echo "==============================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo -e "${BLUE}📂 项目目录: $PROJECT_DIR${NC}"

# 检查系统要求
check_requirements() {
    echo -e "\n${YELLOW}🔍 检查系统要求...${NC}"
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python3 未安装，请先安装 Python 3.8+${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Python3: $(python3 --version)${NC}"
    
    # 检查Node.js
    if ! command -v node &> /dev/null; then
        echo -e "${RED}❌ Node.js 未安装，请先安装 Node.js 16+${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Node.js: $(node --version)${NC}"
    
    # 检查npm
    if ! command -v npm &> /dev/null; then
        echo -e "${RED}❌ npm 未安装${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ npm: $(npm --version)${NC}"
    
    # 检查MySQL
    if ! command -v mysql &> /dev/null; then
        echo -e "${YELLOW}⚠️  MySQL命令行工具未找到，请确保MySQL服务正在运行${NC}"
    else
        echo -e "${GREEN}✅ MySQL客户端已安装${NC}"
    fi
}

# 创建环境配置文件
create_env_file() {
    echo -e "\n${YELLOW}📝 创建环境配置文件...${NC}"
    
    if [ ! -f ".env" ]; then
        cat > .env << EOF
# 本地开发环境配置
# Local Development Environment Configuration

# 数据库配置
DATABASE_URL=mysql+pymysql://root:Pp123456@localhost:3306/stock_analysis_dev
MYSQL_ROOT_PASSWORD=Pp123456
MYSQL_DATABASE=stock_analysis_dev
MYSQL_USER=root
MYSQL_PASSWORD=Pp123456

# JWT 配置
SECRET_KEY=your_local_secret_key_here_at_least_32_characters_long_$(date +%s)
ACCESS_TOKEN_EXPIRE_MINUTES=60
ALGORITHM=HS256

# 应用配置
ENVIRONMENT=development
LOG_LEVEL=INFO
DEBUG=true

# API 配置
API_V1_STR=/api/v1
PROJECT_NAME="Stock Analysis System - Local Dev"

# 前端配置
REACT_APP_API_URL=http://localhost:8000/api/v1
REACT_APP_ENVIRONMENT=development

# 服务器配置
BACKEND_HOST=localhost
BACKEND_PORT=8000
FRONTEND_PORT=3001

# 微信支付配置 (请填入真实配置)
WECHAT_PAY_APP_ID=your_wechat_app_id
WECHAT_PAY_MCH_ID=your_wechat_mch_id
WECHAT_PAY_API_KEY=your_wechat_api_key
WECHAT_PAY_NOTIFY_URL=http://your-domain.com/api/v1/payment/notify
EOF
        echo -e "${GREEN}✅ 环境配置文件 .env 已创建${NC}"
    else
        echo -e "${BLUE}ℹ️  环境配置文件 .env 已存在，跳过创建${NC}"
    fi
    
    # 创建生产环境示例配置
    if [ ! -f ".env.prod.example" ]; then
        cat > .env.prod.example << EOF
# 生产环境配置示例
# Production Environment Configuration Example

# 数据库配置
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/stock_analysis_prod
MYSQL_ROOT_PASSWORD=your_strong_password
MYSQL_DATABASE=stock_analysis_prod
MYSQL_USER=stock_user
MYSQL_PASSWORD=your_strong_password

# JWT 配置
SECRET_KEY=your_very_strong_secret_key_at_least_32_characters_long
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALGORITHM=HS256

# 应用配置
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=false

# API 配置
API_V1_STR=/api/v1
PROJECT_NAME="Stock Analysis System"

# 前端配置
REACT_APP_API_URL=https://your-domain.com/api/v1
REACT_APP_ENVIRONMENT=production

# 服务器配置
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
FRONTEND_PORT=3000

# 微信支付配置
WECHAT_PAY_APP_ID=your_wechat_app_id
WECHAT_PAY_MCH_ID=your_wechat_mch_id
WECHAT_PAY_API_KEY=your_wechat_api_key
WECHAT_PAY_NOTIFY_URL=https://your-domain.com/api/v1/payment/notify
EOF
        echo -e "${GREEN}✅ 生产环境配置示例 .env.prod.example 已创建${NC}"
    fi
}

# 设置后端环境
setup_backend() {
    echo -e "\n${YELLOW}🐍 设置后端环境...${NC}"
    
    cd backend
    
    # 创建虚拟环境
    if [ ! -d "venv" ]; then
        echo -e "${BLUE}创建Python虚拟环境...${NC}"
        python3 -m venv venv
        echo -e "${GREEN}✅ Python虚拟环境已创建${NC}"
    else
        echo -e "${BLUE}ℹ️  Python虚拟环境已存在${NC}"
    fi
    
    # 激活虚拟环境并安装依赖
    echo -e "${BLUE}激活虚拟环境并安装依赖...${NC}"
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    echo -e "${GREEN}✅ Python依赖安装完成${NC}"
    
    cd ..
}

# 设置前端环境
setup_frontend() {
    echo -e "\n${YELLOW}⚛️  设置前端环境...${NC}"
    
    # 设置用户前端
    if [ -d "client" ]; then
        echo -e "${BLUE}安装用户前端依赖...${NC}"
        cd client
        npm install
        echo -e "${GREEN}✅ 用户前端依赖安装完成${NC}"
        cd ..
    fi
    
    # 设置管理前端
    if [ -d "frontend" ]; then
        echo -e "${BLUE}安装管理前端依赖...${NC}"
        cd frontend  
        npm install
        echo -e "${GREEN}✅ 管理前端依赖安装完成${NC}"
        cd ..
    fi
}

# 初始化数据库
init_database() {
    echo -e "\n${YELLOW}🗄️  初始化数据库...${NC}"
    
    # 提示用户确认数据库配置
    echo -e "${BLUE}请确保MySQL服务正在运行，并且可以使用以下配置连接:${NC}"
    echo -e "${BLUE}  主机: localhost${NC}"
    echo -e "${BLUE}  用户: root${NC}"
    echo -e "${BLUE}  密码: Pp123456${NC}"
    echo -e "${BLUE}  数据库: stock_analysis_dev${NC}"
    
    read -p "$(echo -e "${YELLOW}是否继续初始化数据库? [y/N]: ${NC}")" -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # 创建数据库
        echo -e "${BLUE}创建数据库...${NC}"
        mysql -u root -pPp123456 -e "CREATE DATABASE IF NOT EXISTS stock_analysis_dev CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>/dev/null || {
            echo -e "${RED}❌ 数据库创建失败，请检查MySQL连接配置${NC}"
            echo -e "${YELLOW}手动执行以下命令创建数据库:${NC}"
            echo -e "${BLUE}mysql -u root -p -e \"CREATE DATABASE IF NOT EXISTS stock_analysis_dev CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;\"${NC}"
            return 1
        }
        
        # 执行初始化脚本
        if [ -f "database/init.sql" ]; then
            echo -e "${BLUE}执行基础表结构初始化...${NC}"
            mysql -u root -pPp123456 stock_analysis_dev < database/init.sql 2>/dev/null || {
                echo -e "${YELLOW}⚠️  基础表结构初始化可能失败，请手动检查${NC}"
            }
        fi
        
        if [ -f "database/payment_tables.sql" ]; then
            echo -e "${BLUE}执行支付表结构初始化...${NC}"
            mysql -u root -pPp123456 stock_analysis_dev < database/payment_tables.sql 2>/dev/null || {
                echo -e "${YELLOW}⚠️  支付表结构初始化可能失败，请手动检查${NC}"
            }
        fi
        
        echo -e "${GREEN}✅ 数据库初始化完成${NC}"
    else
        echo -e "${YELLOW}⚠️  跳过数据库初始化，请手动执行数据库脚本${NC}"
    fi
}

# 创建启动脚本
create_start_scripts() {
    echo -e "\n${YELLOW}📜 创建启动脚本...${NC}"
    
    # 创建后端启动脚本
    cat > start_backend.sh << 'EOF'
#!/bin/bash
echo "🚀 启动后端服务..."
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
EOF
    chmod +x start_backend.sh
    echo -e "${GREEN}✅ 后端启动脚本 start_backend.sh 已创建${NC}"
    
    # 创建前端启动脚本
    cat > start_client.sh << 'EOF'
#!/bin/bash
echo "🚀 启动用户前端..."
cd client
npm run dev -- --port 3001
EOF
    chmod +x start_client.sh
    echo -e "${GREEN}✅ 用户前端启动脚本 start_client.sh 已创建${NC}"
    
    # 创建管理前端启动脚本
    if [ -d "frontend" ]; then
        cat > start_frontend.sh << 'EOF'
#!/bin/bash
echo "🚀 启动管理前端..."
cd frontend
npm run dev -- --port 3000
EOF
        chmod +x start_frontend.sh
        echo -e "${GREEN}✅ 管理前端启动脚本 start_frontend.sh 已创建${NC}"
    fi
    
    # 创建全服务启动脚本
    cat > start_all.sh << 'EOF'
#!/bin/bash
echo "🚀 启动所有服务..."

# 检查端口是否被占用
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo "⚠️  端口 $1 已被占用"
        return 1
    fi
    return 0
}

# 启动后端
if check_port 8000; then
    echo "启动后端服务 (端口 8000)..."
    ./start_backend.sh > logs/backend.log 2>&1 &
    echo "后端服务已在后台启动"
fi

# 等待后端启动
sleep 3

# 启动用户前端
if check_port 3001; then
    echo "启动用户前端 (端口 3001)..."
    ./start_client.sh > logs/client.log 2>&1 &
    echo "用户前端已在后台启动"
fi

# 启动管理前端 (如果存在)
if [ -f "start_frontend.sh" ] && check_port 3000; then
    echo "启动管理前端 (端口 3000)..."
    ./start_frontend.sh > logs/frontend.log 2>&1 &
    echo "管理前端已在后台启动"
fi

echo ""
echo "🎉 所有服务启动完成!"
echo "📱 用户前端: http://localhost:3001"
echo "🔧 管理前端: http://localhost:3000"  
echo "🔗 后端API: http://localhost:8000/docs"
echo ""
echo "查看日志:"
echo "tail -f logs/backend.log    # 后端日志"
echo "tail -f logs/client.log     # 用户前端日志"
echo "tail -f logs/frontend.log   # 管理前端日志"
EOF
    chmod +x start_all.sh
    echo -e "${GREEN}✅ 全服务启动脚本 start_all.sh 已创建${NC}"
    
    # 创建停止脚本
    cat > stop_all.sh << 'EOF'
#!/bin/bash
echo "🛑 停止所有服务..."

# 停止指定端口的进程
kill_port() {
    local pid=$(lsof -ti:$1)
    if [ ! -z "$pid" ]; then
        echo "停止端口 $1 的进程 (PID: $pid)..."
        kill -9 $pid
    fi
}

kill_port 8000  # 后端
kill_port 3001  # 用户前端
kill_port 3000  # 管理前端

echo "✅ 所有服务已停止"
EOF
    chmod +x stop_all.sh
    echo -e "${GREEN}✅ 停止脚本 stop_all.sh 已创建${NC}"
}

# 创建日志目录
create_log_dir() {
    echo -e "\n${YELLOW}📋 创建日志目录...${NC}"
    mkdir -p logs
    echo -e "${GREEN}✅ 日志目录已创建${NC}"
}

# 部署完成提示
deployment_complete() {
    echo -e "\n${GREEN}🎉 部署完成!${NC}"
    echo "==============================================="
    echo -e "${BLUE}📖 使用说明:${NC}"
    echo ""
    echo -e "${YELLOW}1. 启动所有服务:${NC}"
    echo -e "${BLUE}   ./start_all.sh${NC}"
    echo ""
    echo -e "${YELLOW}2. 单独启动服务:${NC}"
    echo -e "${BLUE}   ./start_backend.sh    # 后端服务${NC}"
    echo -e "${BLUE}   ./start_client.sh     # 用户前端${NC}"
    if [ -f "start_frontend.sh" ]; then
        echo -e "${BLUE}   ./start_frontend.sh   # 管理前端${NC}"
    fi
    echo ""
    echo -e "${YELLOW}3. 停止所有服务:${NC}"
    echo -e "${BLUE}   ./stop_all.sh${NC}"
    echo ""
    echo -e "${YELLOW}4. 访问地址:${NC}"
    echo -e "${BLUE}   用户前端: http://localhost:3001${NC}"
    echo -e "${BLUE}   管理前端: http://localhost:3000${NC}"
    echo -e "${BLUE}   后端API文档: http://localhost:8000/docs${NC}"
    echo ""
    echo -e "${YELLOW}5. 配置文件:${NC}"
    echo -e "${BLUE}   .env - 开发环境配置${NC}"
    echo -e "${BLUE}   .env.prod.example - 生产环境配置示例${NC}"
    echo ""
    echo -e "${YELLOW}6. 开发文档:${NC}"
    echo -e "${BLUE}   DEVELOPMENT_STATUS.md - 开发进度文档${NC}"
    echo ""
    echo -e "${RED}⚠️  注意事项:${NC}"
    echo -e "${RED}   1. 请确保MySQL服务正在运行${NC}"
    echo -e "${RED}   2. 首次运行前请检查 .env 文件中的数据库配置${NC}"
    echo -e "${RED}   3. 支付功能需要配置微信支付参数${NC}"
    echo "==============================================="
}

# 主函数
main() {
    echo -e "${BLUE}开始一键部署...${NC}"
    
    check_requirements
    create_env_file
    setup_backend
    setup_frontend
    create_log_dir
    init_database
    create_start_scripts
    deployment_complete
    
    echo -e "\n${GREEN}✅ 一键部署脚本执行完成!${NC}"
}

# 执行主函数
main "$@"