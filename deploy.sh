#!/bin/bash

# 股票分析系统 - 部署脚本 (最终版)
echo "🚀 股票分析系统部署"
echo "=================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_success() { echo -e "${GREEN}[✅]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[⚠️]${NC} $1"; }
log_error() { echo -e "${RED}[❌]${NC} $1"; }

# 固定端口配置
BACKEND_PORT=3007
CLIENT_PORT=8005
FRONTEND_PORT=8006

echo "📊 端口配置: API($BACKEND_PORT) | 客户端($CLIENT_PORT) | 管理端($FRONTEND_PORT)"
echo ""

# 检查运行模式
MIGRATION_MODE=false
STOCK_CODE_UPGRADE=false

case "$1" in
    --migrate|-m)
        MIGRATION_MODE=true
        echo "🔄 迁移模式: 只更新数据库结构，跳过依赖安装"
        echo ""
        ;;
    --upgrade-stock-codes|-u)
        STOCK_CODE_UPGRADE=true
        echo "📊 股票代码升级: 添加原始代码和标准化代码字段"
        echo ""
        ;;
    --help|-h)
        echo "📖 使用说明:"
        echo "  ./deploy.sh                    - 完整部署"
        echo "  ./deploy.sh --migrate         - 仅更新数据库结构"
        echo "  ./deploy.sh --upgrade-stock-codes - 升级股票代码字段"
        echo "  ./deploy.sh --help            - 显示帮助"
        exit 0
        ;;
esac

# 环境检查
echo "🔍 检查环境..."
command -v node >/dev/null || { log_error "Node.js未安装"; exit 1; }
command -v python3 >/dev/null || { log_error "Python3未安装"; exit 1; }
command -v mysql >/dev/null || { log_error "MySQL未安装"; exit 1; }

# MySQL服务检查
if ! mysqladmin ping -h127.0.0.1 --silent 2>/dev/null; then
    log_warn "启动MySQL服务..."
    brew services start mysql 2>/dev/null || { log_error "MySQL启动失败"; exit 1; }
    sleep 2
fi
log_success "环境检查完成"

# 后端设置
echo "🔧 设置后端..."
cd backend

# 虚拟环境检查
if [ ! -d "venv" ]; then
    if [ "$MIGRATION_MODE" = true ]; then
        log_error "迁移模式需要虚拟环境，请先运行完整部署: ./deploy.sh"
        exit 1
    fi
    python3 -m venv venv
fi

source venv/bin/activate

# 依赖安装（迁移模式可选）
if [ "$MIGRATION_MODE" = false ]; then
    pip install -r requirements.txt -q
    log_success "后端依赖完成"
else
    # 迁移模式：只安装必要依赖
    pip install -r requirements.txt -q --upgrade
    log_success "后端依赖检查完成"
fi

# 创建管理员用户表
echo "👤 创建管理员用户表..."
python create_admin_table.py 2>/dev/null || log_warn "管理员表可能已存在"

# 创建TXT导入相关数据表
echo "📊 创建TXT导入数据表..."
python create_daily_trading_tables.py 2>/dev/null || log_warn "TXT导入表可能已存在"

# 股票代码字段升级
if [ "$STOCK_CODE_UPGRADE" = true ]; then
    echo "🔄 执行股票代码字段升级..."
    if [ -f "migrate_stock_codes.py" ]; then
        python migrate_stock_codes.py
        if [ $? -eq 0 ]; then
            log_success "股票代码字段升级完成"
        else
            log_error "股票代码字段升级失败"
            exit 1
        fi
    else
        log_error "迁移脚本不存在: migrate_stock_codes.py"
        exit 1
    fi
elif [ "$MIGRATION_MODE" = false ]; then
    # 在完整部署时检查是否需要字段升级
    echo "🔍 检查股票代码字段..."
    python -c "
from app.core.database import engine
from sqlalchemy import text
import sys

try:
    with engine.connect() as conn:
        result = conn.execute(text('''
            SELECT COLUMN_NAME 
            FROM information_schema.COLUMNS 
            WHERE TABLE_NAME = 'daily_trading' 
            AND COLUMN_NAME IN ('original_stock_code', 'normalized_stock_code')
        '''))
        existing_columns = [row[0] for row in result.fetchall()]
        
        if len(existing_columns) < 2:
            print('⚠️  股票代码字段需要升级')
            print('💡 运行: ./deploy.sh --upgrade-stock-codes')
            sys.exit(1)
        else:
            print('✅ 股票代码字段已升级')
except Exception as e:
    print(f'⚠️  字段检查失败: {str(e)[:50]}...')
    print('💡 如果是新安装可忽略此警告')
" 2>/dev/null || log_warn "字段检查完成"
fi

cd ..

# 前端设置 - 修复端口配置
echo "🎨 设置前端..."
# 修复客户端端口
if [ -f "client/package.json" ]; then
    sed -i.bak "s/--port [0-9]*/--port $CLIENT_PORT/g" client/package.json
fi
# 修复管理端端口  
if [ -f "frontend/package.json" ]; then
    sed -i.bak "s/--port [0-9]*/--port $FRONTEND_PORT/g" frontend/package.json
fi

# 前端依赖安装（迁移模式跳过）
if [ "$MIGRATION_MODE" = false ]; then
    [ ! -d "client/node_modules" ] && { cd client && npm install -q && cd ..; }
    [ ! -d "frontend/node_modules" ] && { cd frontend && npm install -q && cd ..; }
    log_success "前端依赖完成"
else
    log_success "迁移模式: 跳过前端依赖安装"
fi

# 配置文件
echo "⚙️ 生成配置..."
cat > ports.env << EOF
BACKEND_PORT=$BACKEND_PORT
CLIENT_PORT=$CLIENT_PORT
FRONTEND_PORT=$FRONTEND_PORT
EOF

mkdir -p logs
log_success "配置完成"

# 数据库表验证
echo "🔍 验证数据库表..."
cd backend
source venv/bin/activate

# 验证核心数据表和字段是否存在
python -c "
from app.core.database import engine
from sqlalchemy import text

tables_to_check = [
    'admin_users',
    'daily_trading', 
    'concept_daily_summary',
    'stock_concept_ranking',
    'concept_high_record',
    'txt_import_record'
]

print('📋 检查数据表:')
with engine.connect() as conn:
    for table in tables_to_check:
        try:
            result = conn.execute(text(f'SHOW TABLES LIKE \"{table}\"'))
            if result.fetchone():
                print(f'  ✅ {table}')
                
                # 特别检查 daily_trading 表的字段结构
                if table == 'daily_trading':
                    field_result = conn.execute(text('''
                        SELECT COLUMN_NAME 
                        FROM information_schema.COLUMNS 
                        WHERE TABLE_NAME = 'daily_trading' 
                        AND COLUMN_NAME IN ('original_stock_code', 'normalized_stock_code')
                    '''))
                    existing_fields = [row[0] for row in field_result.fetchall()]
                    if len(existing_fields) >= 2:
                        print(f'    ✅ 股票代码字段已升级 ({len(existing_fields)}/2)')
                    else:
                        print(f'    ⚠️  股票代码字段需要升级 ({len(existing_fields)}/2)')
            else:
                print(f'  ❌ {table} - 缺失')
        except Exception as e:
            print(f'  ⚠️  {table} - 检查失败: {str(e)[:30]}...')
"

cd ..
log_success "数据库验证完成"

echo ""
if [ "$MIGRATION_MODE" = true ]; then
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
    echo "  2. 访问管理端    - http://localhost:$FRONTEND_PORT"
    echo "  3. 登录账号      - admin / admin123"
    echo "  4. 导入TXT数据   - 进入'数据导入'页面"
elif [ "$STOCK_CODE_UPGRADE" = true ]; then
    echo "🎉 股票代码字段升级完成！"
    echo ""
    echo "✨ 新增功能:"
    echo "  ✅ 原始股票代码存储 (original_stock_code)"
    echo "  ✅ 标准化代码存储 (normalized_stock_code)"
    echo "  ✅ SH/SZ前缀自动处理"
    echo "  ✅ 概念匹配问题修复"
    echo "  ✅ 市场分析功能增强"
    echo ""
    echo "🚀 下一步："
    echo "  1. ./start.sh        - 重启服务"
    echo "  2. 测试TXT导入       - 上传包含SH/SZ前缀的文件"
    echo "  3. 验证概念汇总      - 检查概念数据计算是否正常"
    echo "  4. 使用新API        - /api/v1/enhanced-stock-analysis/"
else
    echo "🎉 部署完成！"
    echo ""
    echo "📊 服务地址:"
    echo "  🔗 API:     http://localhost:$BACKEND_PORT"
    echo "  📱 客户端:   http://localhost:$CLIENT_PORT" 
    echo "  🖥️ 管理端:   http://localhost:$FRONTEND_PORT"
    echo ""
    echo "👤 管理员账号: admin / admin123"
    echo ""
    echo "🚀 启动方式:"
    echo "  ./start.sh  - 启动所有服务"
    echo "  ./status.sh - 检查运行状态"
    echo "  ./stop.sh   - 停止所有服务"
    echo ""
    echo "📋 下一步: ./start.sh"
    echo ""
    echo "🔧 可选操作:"
    echo "  ./deploy.sh --upgrade-stock-codes  - 升级股票代码字段"
    echo "  ./deploy.sh --migrate             - 仅更新数据库结构"
fi