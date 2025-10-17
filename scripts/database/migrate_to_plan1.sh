#!/bin/bash

# ============================================
# 从旧架构迁移到 Plan 1 (v2.7.3)
# 功能：为现有系统添加Plan 1架构表
# 版本：v1.0
# ============================================

echo "🚀 迁移到 Plan 1 - 完整分离架构"
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
BACKUP_BEFORE_MIGRATION=true

while [[ $# -gt 0 ]]; do
    case $1 in
        --host) DB_HOST="$2"; shift 2 ;;
        --port) DB_PORT="$2"; shift 2 ;;
        --user) DB_USER="$2"; shift 2 ;;
        --password) DB_PASS="$2"; shift 2 ;;
        --database) DB_NAME="$2"; shift 2 ;;
        --skip-backup) BACKUP_BEFORE_MIGRATION=false; shift ;;
        --help)
            echo "迁移到 Plan 1 架构"
            echo "用法: $0 [选项]"
            echo "选项:"
            echo "  --host <主机>       数据库主机 (默认: localhost)"
            echo "  --port <端口>       数据库端口 (默认: 3306)"
            echo "  --user <用户名>     数据库用户 (默认: root)"
            echo "  --password <密码>   数据库密码 (默认: Pp123456)"
            echo "  --database <数据库> 数据库名称 (默认: stock_analysis_dev)"
            echo "  --skip-backup       跳过备份"
            echo "  --help             显示帮助信息"
            exit 0
            ;;
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
    exit 1
fi
log_success "MySQL连接成功"

# 备份数据库
if [ "$BACKUP_BEFORE_MIGRATION" = true ]; then
    echo ""
    echo "💾 备份数据库..."
    BACKUP_FILE="stock_analysis_backup_$(date +%Y%m%d_%H%M%S).sql"

    if $MYSQL_CMD --databases $DB_NAME > "$BACKUP_FILE" 2>/dev/null; then
        log_success "数据库备份完成: $BACKUP_FILE"
    else
        log_warn "数据库备份失败，继续迁移"
    fi
fi

# 检查新表是否已存在
echo ""
echo "🔍 检查表状态..."

check_table_exists() {
    local table=$1
    $MYSQL_CMD $DB_NAME -e "SHOW TABLES LIKE '$table'" 2>/dev/null | grep -q "$table"
}

import_batches_exists=false
raw_import_data_exists=false
raw_data_mapping_exists=false

check_table_exists "import_batches" && import_batches_exists=true
check_table_exists "raw_import_data" && raw_import_data_exists=true
check_table_exists "raw_data_mapping" && raw_data_mapping_exists=true

if [ "$import_batches_exists" = true ] && [ "$raw_import_data_exists" = true ] && [ "$raw_data_mapping_exists" = true ]; then
    log_warn "Plan 1表已经存在，无需迁移"
    echo "  ✅ import_batches"
    echo "  ✅ raw_import_data"
    echo "  ✅ raw_data_mapping"
    echo ""
    echo "💡 提示: 系统已经是Plan 1架构"
    exit 0
fi

# 创建新表
echo ""
echo "📋 创建Plan 1表..."

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -f "$SCRIPT_DIR/create_raw_data_tables.sql" ]; then
    log_error "无法找到 create_raw_data_tables.sql"
    exit 1
fi

# 执行创建表脚本
if $MYSQL_CMD $DB_NAME < "$SCRIPT_DIR/create_raw_data_tables.sql" 2>&1 | grep -v "Warning" > /dev/null; then
    log_success "Plan 1表创建完成"
    echo "  ✅ import_batches"
    echo "  ✅ raw_import_data"
    echo "  ✅ raw_data_mapping"
else
    log_error "表创建失败"
    exit 1
fi

# 验证表创建
echo ""
echo "✅ 验证表结构..."

$MYSQL_CMD $DB_NAME -e "
SHOW TABLES LIKE 'import_batches';
SHOW TABLES LIKE 'raw_import_data';
SHOW TABLES LIKE 'raw_data_mapping';
" 2>&1 | grep -E "(import_batches|raw_import_data|raw_data_mapping)" | while read -r table; do
    if [ -n "$table" ]; then
        echo "  ✅ $table"
    fi
done

# 迁移现有数据（可选）
echo ""
echo "📝 数据迁移..."

# 检查是否有现有的导入记录
old_import_count=$($MYSQL_CMD $DB_NAME -e "SELECT COUNT(*) as count FROM stock_concept_raw_data" 2>/dev/null | tail -1)

if [ "$old_import_count" -gt 0 ]; then
    echo "🔄 检测到 $old_import_count 条旧数据"
    echo "⚠️ 旧数据仍保存在 stock_concept_raw_data 表"
    echo "💡 若需迁移旧数据，请参考文档进行手动迁移"
else
    log_success "无旧数据需要迁移"
fi

# 完成提示
echo ""
echo "🎉 迁移完成！"
echo ""
echo "📊 迁移成果:"
echo "  ✅ Plan 1 完整分离架构已部署"
echo "  ✅ 所有新表创建成功"
echo "  ✅ 系统已支持原始数据保存"
echo ""
echo "🚀 后续步骤:"
echo "  1. 运行部署脚本更新配置"
echo "     ./scripts/deployment/deploy.sh"
echo ""
echo "  2. 重启服务生效"
echo "     ./stop.sh && ./start.sh"
echo ""
echo "  3. 验证功能"
echo "     ./status.sh"
echo ""
echo "📚 相关文档:"
echo "  • Plan 1架构设计: ARCHITECTURE_PLAN1.md"
echo "  • 数据导入指南: DATA_IMPORT.md"
echo ""
echo "🔙 回滚方案:"
if [ -n "$BACKUP_FILE" ] && [ -f "$BACKUP_FILE" ]; then
    echo "  备份文件已保存: $BACKUP_FILE"
    echo "  如需回滚，运行:"
    echo "    mysql -u$DB_USER -p$DB_PASS < $BACKUP_FILE"
fi
