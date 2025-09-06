#!/bin/bash

# 数据库初始化脚本
echo "🗄️ 股票分析系统 - 数据库初始化"
echo "=================================="

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

# 数据库配置 (与程序配置保持一致)
DB_HOST="127.0.0.1"
DB_PORT="3306"
DB_USER="root"
DB_PASSWORD="Pp123456"
DB_NAME="stock_analysis_dev"

# ==================== 1. 检查MySQL服务 ====================
log_info "🔍 检查MySQL服务状态..."

if ! command -v mysql &> /dev/null; then
    log_error "MySQL 未安装"
    echo "请安装 MySQL (推荐 v8.0+):"
    echo "  macOS: brew install mysql@8.0"
    exit 1
fi

if ! mysqladmin ping -h$DB_HOST --silent 2>/dev/null; then
    log_warn "MySQL 服务未启动，正在尝试启动..."
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew services start mysql@8.0 2>/dev/null || brew services start mysql 2>/dev/null || {
            log_error "MySQL 服务启动失败"
            echo "请手动启动 MySQL 服务:"
            echo "  brew services start mysql@8.0"
            exit 1
        }
    else
        log_error "请手动启动 MySQL 服务"
        exit 1
    fi
    
    sleep 3
    if ! mysqladmin ping -h$DB_HOST --silent 2>/dev/null; then
        log_error "MySQL 服务启动失败，请检查配置"
        exit 1
    fi
fi

log_success "MySQL 服务运行正常"

# ==================== 2. 测试数据库连接 ====================
log_info "🔐 测试数据库连接..."

mysql -h$DB_HOST -u$DB_USER -p$DB_PASSWORD -e "SELECT 1" > /dev/null 2>&1
if [ $? -ne 0 ]; then
    log_error "数据库连接失败"
    echo "请检查数据库配置:"
    echo "  主机: $DB_HOST"
    echo "  用户: $DB_USER" 
    echo "  密码: $DB_PASSWORD"
    echo ""
    echo "如需修改配置，请编辑: backend/app/core/config.py"
    exit 1
fi

log_success "数据库连接正常"

# ==================== 3. 创建数据库 ====================
log_info "📊 创建数据库 '$DB_NAME'..."

mysql -h$DB_HOST -u$DB_USER -p$DB_PASSWORD -e "CREATE DATABASE IF NOT EXISTS \`$DB_NAME\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>/dev/null

if [ $? -eq 0 ]; then
    log_success "数据库 '$DB_NAME' 创建成功"
else
    log_error "数据库创建失败"
    exit 1
fi

# ==================== 4. 执行初始化SQL脚本 ====================
if [ -f "database/init.sql" ]; then
    log_info "📋 执行初始化SQL脚本..."
    mysql -h$DB_HOST -u$DB_USER -p$DB_PASSWORD $DB_NAME < database/init.sql 2>/dev/null
    if [ $? -eq 0 ]; then
        log_success "初始化SQL脚本执行完成"
    else
        log_warn "初始化SQL脚本执行失败 (可能已存在)"
    fi
fi

# ==================== 5. 创建数据表 (使用SQLAlchemy) ====================
log_info "🏗️ 创建数据表结构..."

cd backend
source venv/bin/activate 2>/dev/null || {
    log_error "请先运行 ./deploy.sh 创建Python虚拟环境"
    exit 1
}

python -c "
import sys
sys.path.append('.')
try:
    from app.database import engine
    from app.models import *
    import app.models
    app.models.Base.metadata.create_all(bind=engine)
    print('✅ 数据表创建完成')
except Exception as e:
    print(f'❌ 数据表创建失败: {e}')
    sys.exit(1)
" 2>/dev/null

if [ $? -ne 0 ]; then
    log_error "数据表创建失败"
    exit 1
fi

cd ..

# ==================== 6. 执行其他SQL脚本 ====================
for sql_file in database/*.sql; do
    if [ -f "$sql_file" ] && [ "$sql_file" != "database/init.sql" ]; then
        filename=$(basename "$sql_file")
        log_info "📋 执行 $filename..."
        mysql -h$DB_HOST -u$DB_USER -p$DB_PASSWORD $DB_NAME < "$sql_file" 2>/dev/null
        if [ $? -eq 0 ]; then
            log_success "$filename 执行完成"
        else
            log_warn "$filename 执行失败 (可能已存在或不适用)"
        fi
    fi
done

# ==================== 7. 创建默认用户 ====================
log_info "👤 创建默认管理员用户..."

cd backend
source venv/bin/activate 2>/dev/null || {
    log_error "请先运行 ./deploy.sh 创建Python虚拟环境"
    exit 1
}

python -c "
import sys
sys.path.append('.')
try:
    from app.database import get_db
    from app.crud.user import user_crud
    from app.schemas.user import UserCreate
    from sqlalchemy.orm import Session
    
    # 获取数据库会话
    db = next(get_db())
    
    # 检查管理员用户是否存在
    existing_admin = user_crud.get_user_by_username('admin')
    if existing_admin:
        print('✅ 管理员用户已存在')
    else:
        # 创建管理员用户
        admin_user = UserCreate(
            username='admin',
            email='admin@example.com',
            password='admin123',
            is_active=True
        )
        user_crud.create_user(admin_user)
        print('✅ 管理员用户创建成功 (用户名: admin, 密码: admin123)')
    
    db.close()
except Exception as e:
    print(f'⚠️  用户创建跳过: {e}')
" 2>/dev/null

cd ..

# ==================== 8. 数据库状态检查 ====================
log_info "📊 数据库状态检查..."

table_count=$(mysql -h$DB_HOST -u$DB_USER -p$DB_PASSWORD $DB_NAME -e "SELECT COUNT(*) as count FROM information_schema.tables WHERE table_schema = '$DB_NAME'" -s -N 2>/dev/null)

if [ "$table_count" -gt 0 ]; then
    log_success "数据库包含 $table_count 个表"
    echo ""
    echo "📋 数据表列表:"
    mysql -h$DB_HOST -u$DB_USER -p$DB_PASSWORD $DB_NAME -e "SHOW TABLES" 2>/dev/null | while read table; do
        echo "  - $table"
    done
else
    log_warn "数据库中没有找到表"
fi

echo ""
echo "🎉 数据库初始化完成！"
echo "======================="
echo ""
echo "📊 数据库信息:"
echo "  🔗 主机: $DB_HOST:$DB_PORT"
echo "  📁 数据库: $DB_NAME"
echo "  👤 用户: $DB_USER"
echo ""
echo "📋 默认登录:"
echo "  👤 管理员: admin / admin123"
echo ""
echo "📝 下一步:"
echo "  ▶️  启动系统: ./start.sh"
echo "  🔧 重新部署: ./deploy.sh"
echo ""
log_success "数据库已准备就绪！"