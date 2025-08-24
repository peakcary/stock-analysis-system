#!/bin/bash

# 本地环境一键部署脚本
# Local Environment One-Click Setup Script

set -e

echo "🚀 开始设置本地开发环境..."
echo "📍 当前目录: $(pwd)"

# 检查是否在项目根目录
if [ ! -d "backend" ] || [ ! -d "frontend" ] || [ ! -d "scripts" ]; then
    echo "❌ 错误: 请在项目根目录下运行此脚本"
    echo "   当前目录应包含: backend/, frontend/, scripts/"
    exit 1
fi

# 检查MySQL是否运行
echo "🔍 检查MySQL服务..."
if ! mysql -u root -pPp123456 -e "SELECT 1;" >/dev/null 2>&1; then
    echo "❌ 错误: 无法连接到MySQL数据库"
    echo "   请确保MySQL服务正在运行，用户名为root，密码为Pp123456"
    echo "   或者修改 .env.local 文件中的数据库配置"
    exit 1
fi

echo "✅ MySQL连接成功"

# 创建数据库
echo "📊 创建数据库..."
mysql -u root -pPp123456 -e "
CREATE DATABASE IF NOT EXISTS stock_analysis_dev CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
SHOW DATABASES;
" || {
    echo "❌ 创建数据库失败"
    exit 1
}

echo "✅ 数据库 stock_analysis_dev 创建成功"

# 初始化数据库表结构
echo "🗃️ 初始化数据库表结构..."
if [ -f "database/init.sql" ]; then
    mysql -u root -pPp123456 stock_analysis_dev < database/init.sql || {
        echo "⚠️  警告: 初始化SQL脚本执行失败，将跳过此步骤"
    }
    echo "✅ 数据库初始化完成"
else
    echo "⚠️  警告: 未找到 database/init.sql 文件，跳过数据库初始化"
fi

# 检查并安装 Python 依赖
echo "🐍 设置 Python 后端环境..."
cd backend

if [ ! -d "venv" ]; then
    echo "📦 创建Python虚拟环境..."
    python3 -m venv venv || {
        echo "❌ 创建虚拟环境失败，请确保已安装Python 3.8+"
        exit 1
    }
fi

echo "🔧 激活虚拟环境并安装依赖..."
source venv/bin/activate

# 升级pip
pip install --upgrade pip

# 安装依赖
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt || {
        echo "❌ 安装Python依赖失败"
        exit 1
    }
else
    echo "📝 创建requirements.txt..."
    cat > requirements.txt << EOF
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
pymysql==1.1.0
cryptography==41.0.8
alembic==1.12.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
pydantic==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.0
EOF
    pip install -r requirements.txt || {
        echo "❌ 安装Python依赖失败"
        exit 1
    }
fi

echo "✅ Python后端环境设置完成"

cd ..

# 检查并安装 Node.js 依赖
echo "⚛️  设置React前端环境..."
cd frontend

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "❌ 错误: 未找到Node.js，请先安装Node.js 16+"
    exit 1
fi

# 检查 npm
if ! command -v npm &> /dev/null; then
    echo "❌ 错误: 未找到npm，请确保npm已正确安装"
    exit 1
fi

echo "📦 安装前端依赖..."
npm install || {
    echo "❌ 安装前端依赖失败"
    exit 1
}

echo "✅ 前端环境设置完成"

cd ..

# 创建日志目录
echo "📂 创建必要目录..."
mkdir -p backend/logs
mkdir -p logs

# 复制环境配置文件
echo "⚙️  配置环境变量..."
if [ ! -f ".env" ]; then
    cp .env.local .env
    echo "✅ 环境配置文件已创建: .env"
else
    echo "⚠️  .env 文件已存在，跳过复制"
fi

echo ""
echo "🎉 本地环境设置完成！"
echo ""
echo "📋 下一步操作："
echo "1. 启动后端服务: ./scripts/start-backend.sh"
echo "2. 启动前端服务: ./scripts/start-frontend.sh"
echo "3. 或者使用一键启动: ./scripts/start-all.sh"
echo ""
echo "🌐 访问地址："
echo "- 前端应用: http://localhost:3000"
echo "- 后端API: http://localhost:8000"
echo "- API文档: http://localhost:8000/docs"
echo ""
echo "💾 数据库信息："
echo "- 数据库名: stock_analysis_dev"
echo "- 用户名: root"
echo "- 密码: Pp123456"
echo ""