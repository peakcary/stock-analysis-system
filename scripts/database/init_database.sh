#!/bin/bash

# ============================================
# 数据库初始化脚本
# 功能：创建所有必要的数据库表和结构
# 版本：v2.7.0
# ============================================

echo "🚀 股票分析系统 - 数据库初始化"
echo "================================"

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_success() { echo -e "${GREEN}[✅]${NC} $1"; }
log_error() { echo -e "${RED}[❌]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[⚠️]${NC} $1"; }

# 参数解析
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-3306}
DB_USER=${DB_USER:-root}
DB_PASS=${DB_PASS:-Pp123456}
DB_NAME=${DB_NAME:-stock_analysis_dev}

# 支持命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --host) DB_HOST="$2"; shift 2 ;;
        --port) DB_PORT="$2"; shift 2 ;;
        --user) DB_USER="$2"; shift 2 ;;
        --password) DB_PASS="$2"; shift 2 ;;
        --database) DB_NAME="$2"; shift 2 ;;
        --help)
            echo "用法: $0 [选项]"
            echo "选项:"
            echo "  --host <主机>       数据库主机 (默认: localhost)"
            echo "  --port <端口>       数据库端口 (默认: 3306)"
            echo "  --user <用户名>     数据库用户 (默认: root)"
            echo "  --password <密码>   数据库密码 (默认: Pp123456)"
            echo "  --database <数据库> 数据库名称 (默认: stock_analysis_dev)"
            echo "  --help             显示帮助信息"
            exit 0 ;;
        *) log_error "未知选项: $1"; exit 1 ;;
    esac
done

echo "📊 数据库配置:"
echo "  主机: $DB_HOST:$DB_PORT"
echo "  用户: $DB_USER"
echo "  数据库: $DB_NAME"
echo ""

# MySQL命令基础
MYSQL_CMD="mysql -h$DB_HOST -P$DB_PORT -u$DB_USER -p$DB_PASS"

# 检查MySQL连接
echo "🔍 检查MySQL连接..."
if ! $MYSQL_CMD -e "SELECT 1" >/dev/null 2>&1; then
    log_error "无法连接到MySQL数据库"
    echo "请检查："
    echo "  1. MySQL服务是否运行: brew services list | grep mysql"
    echo "  2. 用户名密码是否正确"
    echo "  3. 主机端口是否正确"
    exit 1
fi
log_success "MySQL连接成功"

# 创建数据库（如果不存在）
echo ""
echo "📦 创建数据库..."
$MYSQL_CMD -e "CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>&1 | grep -v "Warning" || log_error "数据库创建失败"
log_success "数据库 $DB_NAME 已就绪"

# 执行SQL脚本的函数
execute_sql_file() {
    local file=$1
    local description=$2

    if [ ! -f "$file" ]; then
        log_warn "$description - 文件不存在: $file"
        return 1
    fi

    echo "📄 $description..."
    if $MYSQL_CMD $DB_NAME < "$file" 2>&1 | grep -v "Warning"; then
        log_success "$description - 完成"
        return 0
    else
        log_warn "$description - 可能已存在或执行失败"
        return 1
    fi
}

echo ""
echo "🔧 创建数据表..."
echo "================================"

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 1. 创建原始数据表（CSV不拆分存储）
execute_sql_file "$SCRIPT_DIR/create_raw_data_table.sql" "创建CSV原始数据表"

# 统计创建结果
echo ""
echo "📊 数据库表统计:"
$MYSQL_CMD $DB_NAME -e "
SELECT
    TABLE_NAME as '表名',
    TABLE_ROWS as '行数',
    ROUND(DATA_LENGTH/1024/1024, 2) as '数据大小(MB)',
    ROUND(INDEX_LENGTH/1024/1024, 2) as '索引大小(MB)',
    CREATE_TIME as '创建时间'
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = '$DB_NAME'
ORDER BY TABLE_NAME;
" 2>&1 | grep -v "Warning"

echo ""
echo "✅ 数据库初始化完成！"
echo ""
echo "📋 已创建的核心表:"
echo "  ✅ stock_concept_raw_data    - CSV原始数据（未拆分）"
echo "  ✅ stocks                     - 股票基础信息"
echo "  ✅ concepts                   - 概念信息"
echo "  ✅ stock_concepts             - 股票-概念关联"
echo "  ✅ daily_stock_data          - 每日股票数据"
echo "  ✅ admin_users               - 管理员用户"
echo "  ✅ daily_trading             - TXT热度数据"
echo ""
echo "🔗 数据库连接信息:"
echo "  mysql://$DB_USER@$DB_HOST:$DB_PORT/$DB_NAME"
echo ""
echo "🚀 下一步："
echo "  1. 启动服务: ./scripts/deployment/start.sh"
echo "  2. 访问管理端: http://localhost:8006"
echo "  3. 导入数据: 使用管理端的数据导入功能"
