#!/bin/bash

# PostgreSQL 本地开发环境初始化脚本
# 用于创建数据库和用户

echo "🚀 初始化 PostgreSQL 本地开发环境"
echo "===================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_success() { echo -e "${GREEN}[✅]${NC} $1"; }
log_error() { echo -e "${RED}[❌]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[⚠️]${NC} $1"; }

# 检查 PostgreSQL 是否安装
if ! command -v psql &> /dev/null; then
    log_error "PostgreSQL 未安装"
    echo "请先安装 PostgreSQL: brew install postgresql@17"
    exit 1
fi

# 启动 PostgreSQL 服务
echo "🔧 检查 PostgreSQL 服务..."
if ! pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
    log_warn "启动 PostgreSQL 服务..."
    brew services start postgresql@17 2>/dev/null || brew services start postgresql 2>/dev/null
    sleep 3
fi

if ! pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
    log_error "PostgreSQL 服务启动失败"
    exit 1
fi

log_success "PostgreSQL 服务运行中"
echo ""

# 检查数据库和用户
echo "📊 检查数据库和用户..."

# 检查 postgres 用户是否存在并设置密码
log_warn "配置 postgres 用户密码..."
psql -U postgres -h localhost << EOF 2>/dev/null
ALTER USER postgres WITH PASSWORD 'Pp123456';
EOF

if [ $? -eq 0 ]; then
    log_success "postgres 用户密码已配置"
else
    log_warn "postgres 用户可能已配置或无权限"
fi

echo ""

# 检查数据库是否存在
echo "🔍 检查 stockdb 数据库..."
psql -U postgres -h localhost -lqt | cut -d \| -f 1 | grep -w stockdb >/dev/null 2>&1

if [ $? -eq 0 ]; then
    log_success "stockdb 数据库已存在"
else
    log_warn "创建 stockdb 数据库..."
    psql -U postgres -h localhost << EOF
CREATE DATABASE stockdb
    ENCODING 'UTF8'
    LC_COLLATE 'C'
    LC_CTYPE 'C'
    TEMPLATE template0;
EOF

    if [ $? -eq 0 ]; then
        log_success "stockdb 数据库已创建"
    else
        log_error "stockdb 数据库创建失败"
        exit 1
    fi
fi

echo ""

# 验证连接
echo "🔗 测试数据库连接..."
psql -U postgres -h localhost -d stockdb -c "SELECT 1;" >/dev/null 2>&1

if [ $? -eq 0 ]; then
    log_success "数据库连接成功"
else
    log_error "数据库连接失败"
    exit 1
fi

echo ""

# 显示连接信息
echo "📋 PostgreSQL 连接信息:"
echo "  主机: localhost"
echo "  端口: 5432"
echo "  用户: postgres"
echo "  密码: Pp123456"
echo "  数据库: stockdb"
echo ""

# 显示常用命令
echo "🛠️  常用命令:"
echo "  # 连接数据库"
echo "  psql -U postgres -h localhost -d stockdb"
echo ""
echo "  # 列出所有表"
echo "  psql -U postgres -h localhost -d stockdb -c '\\dt'"
echo ""
echo "  # 查看表行数"
echo "  psql -U postgres -h localhost -d stockdb -c 'SELECT tablename FROM pg_tables WHERE schemaname=\\'public\\';'"
echo ""

log_success "PostgreSQL 初始化完成！"
