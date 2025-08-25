#!/bin/bash
# 股票分析系统环境一键安装脚本
# Stock Analysis System Environment Setup Script
# 支持 macOS 和 Linux
# 更新版本：修复IPv4/IPv6兼容性、Node.js版本要求等问题

set -e

echo "🚀 开始安装股票分析系统开发环境..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检测操作系统
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
    echo "📱 检测到 macOS 系统"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    echo "🐧 检测到 Linux 系统"
else
    echo "❌ 不支持的操作系统: $OSTYPE"
    exit 1
fi

# 1. 安装 Homebrew (macOS) 或更新包管理器 (Linux)
install_package_manager() {
    if [[ "$OS" == "macos" ]]; then
        if ! command -v brew &> /dev/null; then
            echo "📦 安装 Homebrew..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        else
            echo "✅ Homebrew 已安装"
        fi
    elif [[ "$OS" == "linux" ]]; then
        echo "📦 更新包管理器..."
        sudo apt update -y
    fi
}

# 2. 安装 Python 3.11+
install_python() {
    echo "🐍 安装 Python 3.11..."
    
    if [[ "$OS" == "macos" ]]; then
        if ! command -v python3.11 &> /dev/null; then
            brew install python@3.11
        else
            echo "✅ Python 3.11 已安装"
        fi
    elif [[ "$OS" == "linux" ]]; then
        sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip
    fi
    
    # 验证安装
    python3 --version || python3.11 --version
}

# 3. 安装 Node.js 20.19+ (兼容vite 7.x)
install_nodejs() {
    log_info "安装 Node.js 20.19+..."
    local required_version="20.19.0"
    
    if [[ "$OS" == "macos" ]]; then
        # 检查nvm
        if ! command -v nvm &> /dev/null; then
            log_warn "NVM未安装，正在安装..."
            curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
            export NVM_DIR="$HOME/.nvm"
            [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
        fi
        
        # 检查Node.js版本
        if command -v node &> /dev/null; then
            local current_version=$(node --version | sed 's/v//')
            if [[ "$current_version" < "$required_version" ]]; then
                log_warn "Node.js版本过低 ($current_version < $required_version)，正在升级..."
                nvm install $required_version
                nvm use $required_version
                nvm alias default $required_version
            else
                log_info "✅ Node.js版本符合要求：$current_version"
            fi
        else
            log_warn "Node.js未安装，正在安装 $required_version..."
            nvm install $required_version
            nvm use $required_version
            nvm alias default $required_version
        fi
    elif [[ "$OS" == "linux" ]]; then
        curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
        sudo apt install -y nodejs
    fi
    
    # 验证安装
    node --version
    npm --version
}

# 4. 安装和配置 MySQL 8.0
install_mysql() {
    log_info "安装 MySQL 8.0..."
    
    if [[ "$OS" == "macos" ]]; then
        # 检查MySQL是否已安装
        if ! brew list mysql@8.0 &> /dev/null; then
            log_info "安装 MySQL 8.0..."
            brew install mysql@8.0
            
            # 添加到PATH
            echo 'export PATH="/opt/homebrew/opt/mysql@8.0/bin:$PATH"' >> ~/.zshrc
            export PATH="/opt/homebrew/opt/mysql@8.0/bin:$PATH"
        else
            log_info "✅ MySQL 8.0 已安装"
        fi
        
        # 启动MySQL服务
        if ! brew services list | grep mysql@8.0 | grep started &> /dev/null; then
            log_info "启动MySQL服务..."
            brew services start mysql@8.0
            sleep 5
        fi
        
        # 设置MySQL root密码为Pp123456
        if ! mysql -u root -pPp123456 -e "SELECT 1" &> /dev/null; then
            log_warn "设置MySQL root密码为 Pp123456..."
            # 尝试无密码连接设置密码
            if mysql -u root -e "ALTER USER 'root'@'localhost' IDENTIFIED BY 'Pp123456';" &> /dev/null; then
                log_info "✅ MySQL密码设置成功"
            else
                log_warn "需要手动设置MySQL密码，请稍后运行: mysql_secure_installation"
            fi
        fi
        
        # 创建管理员用户（兼容性更好）
        mysql -u root -pPp123456 -e "
            CREATE USER IF NOT EXISTS 'admin'@'%' IDENTIFIED WITH mysql_native_password BY 'Pp123456';
            GRANT ALL PRIVILEGES ON *.* TO 'admin'@'%' WITH GRANT OPTION;
            FLUSH PRIVILEGES;
        " &> /dev/null || true
        
    elif [[ "$OS" == "linux" ]]; then
        sudo apt install -y mysql-server-8.0
        sudo systemctl start mysql
        sudo systemctl enable mysql
    fi
    
    # 创建数据库
    mysql -u root -pPp123456 -e "CREATE DATABASE IF NOT EXISTS stock_analysis_dev;" &> /dev/null || {
        log_error "无法创建数据库，请检查MySQL连接"
        exit 1
    }
    
    log_info "✅ MySQL 8.0 配置完成"
}

# 5. 安装 Git (如果没有)
install_git() {
    if ! command -v git &> /dev/null; then
        echo "📦 安装 Git..."
        if [[ "$OS" == "macos" ]]; then
            brew install git
        elif [[ "$OS" == "linux" ]]; then
            sudo apt install -y git
        fi
    else
        echo "✅ Git 已安装: $(git --version)"
    fi
}

# 6. 修复IPv4/IPv6兼容性配置
fix_network_config() {
    log_info "修复IPv4/IPv6兼容性配置..."
    
    # 修复后端配置
    if [ -f "backend/app/core/config.py" ]; then
        sed -i '' 's/localhost:3306/127.0.0.1:3306/g' backend/app/core/config.py
        sed -i '' 's/"localhost"/"127.0.0.1"/g' backend/app/core/config.py
        log_info "✅ 后端数据库配置已修复"
    fi
    
    # 修复客户端代理配置
    if [ -f "client/vite.config.ts" ]; then
        sed -i '' 's/localhost:3007/127.0.0.1:3007/g' client/vite.config.ts
        log_info "✅ 客户端代理配置已修复"
    fi
    
    # 修复前端管理端配置
    if [ -f "frontend/vite.config.ts" ]; then
        sed -i '' 's/localhost:8000/127.0.0.1:8000/g' frontend/vite.config.ts
        log_info "✅ 前端管理端配置已修复"
    fi
}

# 7. 设置项目环境
setup_project_environment() {
    log_info "设置项目环境..."
    
    # 后端环境
    log_info "配置后端 Python 环境..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    # 安装缺失的依赖
    pip install email-validator
    cd ..
    
    # 客户端环境
    log_info "配置客户端 Node.js 环境..."
    if [ -d "client" ]; then
        cd client
        npm install
        cd ..
    fi
    
    # 前端管理环境
    log_info "配置前端管理 Node.js 环境..."
    if [ -d "frontend" ]; then
        cd frontend
        npm install
        cd ..
    fi
    
    log_info "✅ 项目环境配置完成！"
}

# 8. 创建数据库
setup_database() {
    log_info "初始化数据库..."
    
    # 检查数据库初始化文件
    if [ -f "database/init.sql" ]; then
        mysql -u root -pPp123456 < database/init.sql || {
            log_error "数据库初始化失败，请检查MySQL连接"
            return 1
        }
    fi
    
    # 检查支付表文件
    if [ -f "database/payment_tables.sql" ]; then
        mysql -u root -pPp123456 stock_analysis_dev < database/payment_tables.sql || {
            log_warn "支付表初始化可能失败，请手动检查"
        }
    fi
    
    log_info "✅ 数据库初始化完成！"
}

# 8. 创建启动脚本
create_start_scripts() {
    echo "📝 创建启动脚本..."
    
    # 创建后端启动脚本
    cat > start_backend.sh << 'EOF'
#!/bin/bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
EOF
    
    # 创建前端启动脚本
    cat > start_frontend.sh << 'EOF'
#!/bin/bash
cd frontend
npm run dev
EOF
    
    # 创建数据库启动脚本
    if [[ "$OS" == "macos" ]]; then
        cat > start_mysql.sh << 'EOF'
#!/bin/bash
brew services start mysql@8.0
echo "MySQL 已启动"
EOF
    elif [[ "$OS" == "linux" ]]; then
        cat > start_mysql.sh << 'EOF'
#!/bin/bash
sudo systemctl start mysql
echo "MySQL 已启动"
EOF
    fi
    
    # 设置执行权限
    chmod +x start_backend.sh start_frontend.sh start_mysql.sh
    
    echo "✅ 启动脚本创建完成！"
}

# 主安装流程
main() {
    echo "========================================"
    echo "🎯 股票分析系统环境安装向导"
    echo "========================================"
    
    install_package_manager
    install_git
    install_python
    install_nodejs
    install_mysql
    fix_network_config
    setup_project_environment
    setup_database
    create_start_scripts
    
    echo ""
    log_info "🎉 环境安装完成！"
    echo ""
    echo "📋 下一步操作："
    echo "1. 运行: ./start_all.sh (一键启动所有服务)"
    echo "2. 或分别启动："
    echo "   - 后端: ./start_backend.sh"
    echo "   - 前端管理: ./start_frontend.sh" 
    echo "   - 前端客户端: ./start_client.sh"
    echo ""
    echo "🌐 访问地址："
    echo "- 客户端前端: http://localhost:8006"
    echo "- 管理前端: http://localhost:8005"
    echo "- 后端API: http://localhost:3007"
    echo "- API文档: http://localhost:3007/docs"
    echo ""
    echo "🔑 数据库信息："
    echo "- 用户: root 或 admin"
    echo "- 密码: Pp123456"
    echo "- 端口: 3306"
    echo ""
    echo "📚 更多信息请查看: docs/CURRENT_STATUS.md"
}

# 检查是否需要帮助
if [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
    echo "用法: $0"
    echo "选项:"
    echo "  -h, --help     显示帮助信息"
    echo ""
    echo "此脚本将自动安装以下软件:"
    echo "- Python 3.11+"
    echo "- Node.js 20+"
    echo "- MySQL 8.0"
    echo "- Git"
    echo "- 项目依赖包"
    exit 0
fi

# 运行主安装流程
main

echo "🔄 环境安装完成，请查看上方说明进行下一步操作。"