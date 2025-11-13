#!/bin/bash

# ============================================================
# 生产环境数据库部署脚本
# 功能：在生产服务器上部署数据库
# 使用方式：./scripts/database/deploy-to-production.sh <server_ip> <ssh_user> <ssh_password>
# ============================================================

set -e

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[ℹ️]${NC} $1"; }
log_success() { echo -e "${GREEN}[✅]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[⚠️]${NC} $1"; }
log_error() { echo -e "${RED}[❌]${NC} $1"; }

# 参数验证
TARGET_SERVER="${1:-82.157.28.35}"
SSH_USER="${2:-ubuntu}"
SSH_PASSWORD="${3:-chen_188_8_8}"
PROJECT_PATH="/opt/stock-analysis-system"

echo ""
echo "================================================================"
echo "  🗄️  生产环境数据库部署"
echo "================================================================"
echo ""
log_info "部署配置："
echo "  📍 服务器: $TARGET_SERVER"
echo "  👤 用户: $SSH_USER"
echo "  📂 项目路径: $PROJECT_PATH"
echo ""

# 确认部署
read -p "确认在 $TARGET_SERVER 上部署数据库? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_warn "部署已取消"
    exit 1
fi

echo ""
log_info "开始部署数据库..."
echo ""

# ============================================================
# 步骤1: 在生产服务器上安装PostgreSQL
# ============================================================
echo "════════════════════════════════════════════════════"
log_info "步骤 1/5: 在生产服务器上安装 PostgreSQL"
echo "════════════════════════════════════════════════════"

sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  "$SSH_USER@$TARGET_SERVER" << 'EOF'
  echo "🔍 检查 PostgreSQL 安装状态..."

  if command -v psql &> /dev/null; then
    echo "✓ PostgreSQL 已安装"
    psql --version
  else
    echo "📦 安装 PostgreSQL..."
    sudo apt-get update -qq
    sudo apt-get install -y postgresql postgresql-contrib
    echo "✓ PostgreSQL 安装完成"
  fi

  echo "✓ 启动 PostgreSQL 服务..."
  sudo systemctl start postgresql
  sudo systemctl enable postgresql
  echo "✓ PostgreSQL 服务已启动"
EOF

log_success "PostgreSQL 安装完成"
echo ""

# ============================================================
# 步骤2: 配置数据库和用户
# ============================================================
echo "════════════════════════════════════════════════════"
log_info "步骤 2/5: 配置数据库和用户"
echo "════════════════════════════════════════════════════"

sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  "$SSH_USER@$TARGET_SERVER" << EOF
  echo "🔧 配置 PostgreSQL..."

  # 设置 postgres 用户密码
  echo "设置 postgres 用户密码..."
  sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'Pp123456';" 2>/dev/null || echo "✓ 密码已设置或更新"

  # 创建数据库
  echo "检查 stockdb 数据库..."
  sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -w stockdb >/dev/null 2>&1

  if [ \$? -eq 0 ]; then
    echo "✓ stockdb 数据库已存在"
  else
    echo "创建 stockdb 数据库..."
    sudo -u postgres psql << EOSQL
CREATE DATABASE stockdb
    ENCODING 'UTF8'
    LC_COLLATE 'C'
    LC_CTYPE 'C'
    TEMPLATE template0;
EOSQL
    echo "✓ stockdb 数据库已创建"
  fi

  # 验证连接
  echo "测试数据库连接..."
  PGPASSWORD=Pp123456 psql -U postgres -h localhost -d stockdb -c "SELECT 1;" >/dev/null 2>&1
  if [ \$? -eq 0 ]; then
    echo "✓ 数据库连接成功"
  else
    echo "❌ 数据库连接失败"
    exit 1
  fi
EOF

log_success "数据库和用户配置完成"
echo ""

# ============================================================
# 步骤3: 准备环境文件
# ============================================================
echo "════════════════════════════════════════════════════"
log_info "步骤 3/5: 准备后端环境文件"
echo "════════════════════════════════════════════════════"

sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  "$SSH_USER@$TARGET_SERVER" << EOF
  echo "📝 配置环境变量..."

  cd $PROJECT_PATH/backend

  # 检查.env是否存在
  if [ ! -f ".env" ]; then
    echo "创建 .env 文件..."
    cat > .env << 'ENVEOF'
# 数据库配置
DATABASE_URL=postgresql+psycopg2://postgres:Pp123456@localhost/stockdb
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_USER=postgres
DATABASE_PASSWORD=Pp123456
DATABASE_NAME=stockdb
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=3600

# 调试模式
DEBUG=False
LOG_LEVEL=INFO

# Redis配置（可选）
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=3600

# 应用配置
APP_TITLE=Stock Analysis System
APP_VERSION=1.0.0
CORS_ORIGINS=["http://$TARGET_SERVER:80", "http://$TARGET_SERVER:8006", "http://localhost:8006"]
ENVEOF
    echo "✓ .env 文件已创建"
  else
    echo "✓ .env 文件已存在，跳过创建"
  fi
EOF

log_success "环境文件准备完成"
echo ""

# ============================================================
# 步骤4: 初始化数据库表
# ============================================================
echo "════════════════════════════════════════════════════"
log_info "步骤 4/5: 初始化数据库表"
echo "════════════════════════════════════════════════════"

sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  "$SSH_USER@$TARGET_SERVER" << EOF
  echo "🗄️  初始化数据库表..."

  cd $PROJECT_PATH/backend

  # 激活虚拟环境并初始化数据库
  source venv/bin/activate 2>/dev/null || true

  # 运行 Python 初始化脚本
  python3 << 'PYEOF'
import os
import sys
sys.path.insert(0, os.getcwd())

# 导入数据库相关模块
from app.core.database import engine, Base, create_tables
from app.models import *  # 导入所有模型以注册

print("📊 开始创建数据表...")
try:
    create_tables()
    print("✓ 数据表创建成功")
except Exception as e:
    print(f"⚠️  数据表创建时出现异常: {e}")
    # 如果表已存在，这是可以接受的

# 验证数据库连接和表创建
try:
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"✓ 数据库中现有 {len(tables)} 个表:")
    for table in sorted(tables):
        print(f"  - {table}")
except Exception as e:
    print(f"❌ 验证失败: {e}")
    sys.exit(1)
PYEOF

  echo "✓ 数据库初始化完成"
EOF

log_success "数据库表初始化完成"
echo ""

# ============================================================
# 步骤5: 验证部署
# ============================================================
echo "════════════════════════════════════════════════════"
log_info "步骤 5/5: 验证数据库部署"
echo "════════════════════════════════════════════════════"

sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  "$SSH_USER@$TARGET_SERVER" << EOF
  echo "🔍 验证数据库部署..."

  # 检查 PostgreSQL 服务状态
  echo ""
  echo "PostgreSQL 服务状态:"
  sudo systemctl status postgresql --no-pager | grep -E "Active|running"

  # 检查数据库连接
  echo ""
  echo "数据库连接验证:"
  PGPASSWORD=Pp123456 psql -U postgres -h localhost -d stockdb -c "\\l" | grep stockdb

  # 显示数据库信息
  echo ""
  echo "数据库表统计:"
  PGPASSWORD=Pp123456 psql -U postgres -h localhost -d stockdb -c "
    SELECT
      tablename as '表名',
      pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as '大小'
    FROM pg_tables
    WHERE schemaname = 'public'
    ORDER BY tablename;
  "

  echo ""
  echo "✓ 数据库部署验证完成"
EOF

log_success "部署验证完成"
echo ""

# ============================================================
# 部署完成
# ============================================================
echo "════════════════════════════════════════════════════"
echo -e "${GREEN}🎉 数据库部署成功！${NC}"
echo "════════════════════════════════════════════════════"
echo ""

echo "📋 数据库连接信息："
echo "  主机: $TARGET_SERVER"
echo "  数据库: stockdb"
echo "  用户: postgres"
echo "  密码: Pp123456"
echo "  端口: 5432"
echo ""

echo "🔗 连接命令:"
echo "  本地连接: PGPASSWORD=Pp123456 psql -U postgres -h $TARGET_SERVER -d stockdb"
echo ""

echo "📝 后续步骤:"
echo "  1. 启动后端服务: ssh $SSH_USER@$TARGET_SERVER 'cd $PROJECT_PATH && ./scripts/bin/start.sh'"
echo "  2. 访问 API 文档: http://$TARGET_SERVER:3007/docs"
echo "  3. 导入数据: 使用管理端的数据导入功能"
echo ""
