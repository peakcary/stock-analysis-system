#!/bin/bash
# 数据库设置脚本
# Database Setup Script

set -e

echo "🗄️ 股票分析系统数据库设置向导"
echo "========================================"

# 检查 MySQL 是否运行
check_mysql() {
    echo "🔍 检查 MySQL 服务状态..."
    
    if command -v mysql &> /dev/null; then
        if mysql -u root -proot123 -e "SELECT 1;" &> /dev/null; then
            echo "✅ MySQL 连接成功"
            return 0
        else
            echo "❌ MySQL 连接失败，请检查密码是否为 root123"
            echo "💡 设置 MySQL root 密码的方法："
            echo "   mysql -u root -p"
            echo "   ALTER USER 'root'@'localhost' IDENTIFIED BY 'root123';"
            return 1
        fi
    else
        echo "❌ MySQL 未安装，请先运行 ./setup_environment.sh"
        return 1
    fi
}

# 初始化数据库
init_database() {
    echo "🏗️ 初始化数据库..."
    
    if mysql -u root -proot123 < database/init.sql; then
        echo "✅ 数据库初始化成功！"
        
        # 显示数据库信息
        echo ""
        echo "📊 数据库信息："
        mysql -u root -proot123 -e "USE stock_analysis; SHOW TABLES;"
        
        echo ""
        echo "👤 默认管理员账户："
        echo "   用户名: admin"
        echo "   密码: admin123"
        echo "   邮箱: admin@example.com"
        
    else
        echo "❌ 数据库初始化失败"
        return 1
    fi
}

# 创建开发用的环境变量文件
create_env_files() {
    echo "⚙️ 创建环境配置文件..."
    
    # 后端环境变量
    cat > backend/.env << 'EOF'
# 数据库配置
DATABASE_URL=mysql+pymysql://root:root123@localhost:3306/stock_analysis
DATABASE_HOST=localhost
DATABASE_PORT=3306
DATABASE_USER=root
DATABASE_PASSWORD=root123
DATABASE_NAME=stock_analysis

# 应用配置
DEBUG=True
SECRET_KEY=your-super-secret-key-change-in-production
HOST=0.0.0.0
PORT=8000

# JWT 配置
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALGORITHM=HS256

# 日志配置
LOG_LEVEL=INFO
EOF

    # 前端环境变量
    cat > frontend/.env << 'EOF'
# API 配置
VITE_API_URL=http://localhost:8000

# 应用配置
VITE_APP_NAME=股票概念分析系统
VITE_APP_VERSION=1.0.0
EOF

    echo "✅ 环境配置文件创建完成"
}

# 验证环境设置
verify_setup() {
    echo "🔍 验证环境设置..."
    
    # 检查数据库连接
    if mysql -u root -proot123 -e "USE stock_analysis; SELECT COUNT(*) as table_count FROM information_schema.tables WHERE table_schema='stock_analysis';" | grep -q "9"; then
        echo "✅ 数据库表创建成功 (9张表)"
    else
        echo "⚠️ 数据库表创建可能有问题"
    fi
    
    # 检查后端依赖
    cd backend
    if source venv/bin/activate && python -c "import fastapi, sqlalchemy, pandas" 2>/dev/null; then
        echo "✅ 后端 Python 依赖安装成功"
    else
        echo "⚠️ 后端依赖可能有问题"
    fi
    cd ..
    
    # 检查前端依赖
    cd frontend
    if [ -d "node_modules" ]; then
        echo "✅ 前端 Node.js 依赖安装成功"
    else
        echo "⚠️ 前端依赖可能有问题"
    fi
    cd ..
}

# 主函数
main() {
    # 检查当前目录
    if [ ! -f "docker-compose.yml" ]; then
        echo "❌ 请在项目根目录执行此脚本"
        exit 1
    fi
    
    # 执行设置步骤
    if check_mysql; then
        init_database
        create_env_files
        verify_setup
        
        echo ""
        echo "🎉 数据库设置完成！"
        echo ""
        echo "📋 下一步操作："
        echo "1. 启动后端: ./start_backend.sh"
        echo "2. 启动前端: ./start_frontend.sh"
        echo "3. 访问应用: http://localhost:3000"
        echo ""
        echo "🔧 开发命令："
        echo "- 查看后端日志: tail -f backend/logs/app.log"
        echo "- 数据库连接: mysql -u root -proot123 stock_analysis"
        
    else
        echo "❌ MySQL 连接失败，请先设置 MySQL"
        echo ""
        echo "💡 MySQL 设置步骤："
        echo "1. 启动 MySQL 服务"
        echo "2. 设置 root 密码为 root123"
        echo "3. 重新运行此脚本"
    fi
}

# 显示帮助信息
if [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
    echo "数据库设置脚本使用说明："
    echo ""
    echo "前提条件："
    echo "1. MySQL 8.0 已安装并运行"
    echo "2. MySQL root 密码设置为 root123"
    echo "3. 已执行 ./setup_environment.sh"
    echo ""
    echo "功能："
    echo "- 创建股票分析数据库"
    echo "- 初始化所有数据表"
    echo "- 插入测试数据"
    echo "- 创建环境配置文件"
    echo "- 验证环境设置"
    exit 0
fi

# 运行主程序
main