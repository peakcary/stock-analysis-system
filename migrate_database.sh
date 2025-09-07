#!/bin/bash

# 数据库迁移脚本 - 用于现有环境升级到v2.3.0
echo "🔄 数据库迁移脚本 - 升级到v2.3.0"
echo "================================"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_success() { echo -e "${GREEN}[✅]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[⚠️]${NC} $1"; }
log_error() { echo -e "${RED}[❌]${NC} $1"; }

echo "📊 此脚本将为现有环境添加TXT导入功能相关的数据表"
echo ""

# 环境检查
echo "🔍 检查环境..."
if ! command -v mysql >/dev/null 2>&1; then
    log_error "MySQL未安装或不在PATH中"
    exit 1
fi

# MySQL服务检查
if ! mysqladmin ping -h127.0.0.1 --silent 2>/dev/null; then
    log_warn "启动MySQL服务..."
    brew services start mysql 2>/dev/null || { 
        log_error "MySQL启动失败，请手动启动MySQL服务"; 
        exit 1; 
    }
    sleep 3
fi
log_success "MySQL服务运行中"

# 进入后端目录
if [ ! -d "backend" ]; then
    log_error "backend目录不存在，请在项目根目录运行此脚本"
    exit 1
fi

cd backend

# 检查虚拟环境
if [ ! -d "venv" ]; then
    log_warn "虚拟环境不存在，正在创建..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate
log_success "Python虚拟环境已激活"

# 安装依赖
echo "📦 更新Python依赖..."
pip install -r requirements.txt -q
log_success "依赖更新完成"

# 检查现有数据表
echo "🔍 检查现有数据表..."
python -c "
from app.core.database import engine
from sqlalchemy import text

existing_tables = []
try:
    with engine.connect() as conn:
        result = conn.execute(text('SHOW TABLES'))
        existing_tables = [row[0] for row in result.fetchall()]
        print(f'📋 现有数据表: {len(existing_tables)}个')
        for table in sorted(existing_tables):
            print(f'  - {table}')
except Exception as e:
    print(f'❌ 数据库连接失败: {e}')
    exit(1)
"

echo ""

# 创建新的数据表
echo "📊 创建TXT导入相关数据表..."

# 创建管理员表（如果不存在）
echo "👤 检查/创建管理员表..."
python create_admin_table.py

# 创建TXT导入相关表
echo "📈 创建TXT导入数据表..."
python create_daily_trading_tables.py

echo ""

# 验证新表创建
echo "✅ 验证数据表创建..."
python -c "
from app.core.database import engine
from sqlalchemy import text

new_tables = [
    'admin_users',
    'daily_trading',
    'concept_daily_summary', 
    'stock_concept_ranking',
    'concept_high_record',
    'txt_import_record'
]

print('📋 验证关键数据表:')
missing_tables = []

with engine.connect() as conn:
    for table in new_tables:
        try:
            result = conn.execute(text(f'SHOW TABLES LIKE \"{table}\"'))
            if result.fetchone():
                print(f'  ✅ {table}')
            else:
                print(f'  ❌ {table} - 缺失')
                missing_tables.append(table)
        except Exception as e:
            print(f'  ⚠️  {table} - 检查失败: {str(e)[:50]}...')
            missing_tables.append(table)

if missing_tables:
    print(f'')
    print(f'❌ 以下表创建失败: {missing_tables}')
    print(f'请检查数据库权限和配置')
    exit(1)
else:
    print(f'')
    print(f'✅ 所有关键数据表已就绪')
"

cd ..

echo ""
echo "🎉 数据库迁移完成！"
echo ""
echo "📊 新增功能:"
echo "  ✅ TXT热度数据导入"
echo "  ✅ 概念每日汇总计算" 
echo "  ✅ 个股概念排名分析"
echo "  ✅ 概念创新高检测"
echo "  ✅ 管理员认证系统"
echo ""
echo "🚀 下一步："
echo "  1. ./start.sh    - 启动服务"
echo "  2. 访问管理端    - http://localhost:8006"
echo "  3. 登录账号      - admin / admin123"
echo "  4. 导入TXT数据   - 进入'数据导入'页面"
echo ""
echo "📚 详细使用说明请查看: TXT_IMPORT_GUIDE.md"
echo ""