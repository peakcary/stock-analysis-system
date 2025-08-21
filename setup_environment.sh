#!/bin/bash
# 股票分析系统环境一键安装脚本
# Stock Analysis System Environment Setup Script
# 支持 macOS 和 Linux

set -e

echo "🚀 开始安装股票分析系统开发环境..."

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

# 3. 安装 Node.js 20+
install_nodejs() {
    echo "📦 安装 Node.js 20..."
    
    if [[ "$OS" == "macos" ]]; then
        if ! command -v node &> /dev/null; then
            brew install node@20
        else
            echo "✅ Node.js 已安装: $(node --version)"
        fi
    elif [[ "$OS" == "linux" ]]; then
        curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
        sudo apt install -y nodejs
    fi
    
    # 验证安装
    node --version
    npm --version
}

# 4. 安装 MySQL 8.0
install_mysql() {
    echo "🗄️ 安装 MySQL 8.0..."
    
    if [[ "$OS" == "macos" ]]; then
        if ! command -v mysql &> /dev/null; then
            brew install mysql@8.0
            brew services start mysql@8.0
        else
            echo "✅ MySQL 已安装"
        fi
    elif [[ "$OS" == "linux" ]]; then
        sudo apt install -y mysql-server-8.0
        sudo systemctl start mysql
        sudo systemctl enable mysql
    fi
    
    echo "📝 MySQL 安装完成，请手动设置 root 密码为: root123"
    echo "   执行命令: mysql -u root -p"
    echo "   然后运行: ALTER USER 'root'@'localhost' IDENTIFIED BY 'root123';"
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

# 6. 设置项目环境
setup_project_environment() {
    echo "🔧 设置项目环境..."
    
    # 后端环境
    echo "🐍 配置后端 Python 环境..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    cd ..
    
    # 前端环境
    echo "📦 配置前端 Node.js 环境..."
    cd frontend
    npm install
    cd ..
    
    echo "✅ 项目环境配置完成！"
}

# 7. 创建数据库
setup_database() {
    echo "🗄️ 初始化数据库..."
    
    echo "请确保 MySQL 已启动并且 root 密码设置为 root123"
    read -p "按回车键继续，或 Ctrl+C 取消..."
    
    mysql -u root -proot123 < database/init.sql
    echo "✅ 数据库初始化完成！"
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
    setup_project_environment
    
    echo ""
    echo "🎉 环境安装完成！"
    echo ""
    echo "📋 下一步操作："
    echo "1. 设置 MySQL root 密码为 root123"
    echo "2. 运行: ./setup_database.sh (初始化数据库)"
    echo "3. 启动后端: ./start_backend.sh"
    echo "4. 启动前端: ./start_frontend.sh"
    echo ""
    echo "🌐 访问地址："
    echo "- 前端: http://localhost:3000"
    echo "- 后端API: http://localhost:8000"
    echo "- API文档: http://localhost:8000/docs"
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