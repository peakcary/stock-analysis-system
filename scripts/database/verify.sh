#!/bin/bash

# PostgreSQL 数据库验证脚本
# 用于检查数据库连接和数据完整性

echo "🔍 PostgreSQL 数据库验证"
echo "========================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_success() { echo -e "${GREEN}[✅]${NC} $1"; }
log_error() { echo -e "${RED}[❌]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[⚠️]${NC} $1"; }

# 检查 PostgreSQL 连接
echo "🔗 检查 PostgreSQL 连接..."
if pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
    log_success "PostgreSQL 服务正常运行"
else
    log_error "PostgreSQL 服务未运行"
    exit 1
fi

echo ""

# 检查数据库是否存在
echo "📊 检查 stockdb 数据库..."
psql -U postgres -h localhost -lqt | cut -d \| -f 1 | grep -w stockdb >/dev/null 2>&1

if [ $? -eq 0 ]; then
    log_success "stockdb 数据库存在"
else
    log_error "stockdb 数据库不存在"
    exit 1
fi

echo ""

# 统计表数量
echo "📋 检查数据库表..."
TABLE_COUNT=$(psql -U postgres -h localhost -d stockdb -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
log_success "数据库表数量: $TABLE_COUNT"

echo ""

# 列出所有表
echo "📄 数据库表列表:"
psql -U postgres -h localhost -d stockdb -t -c "
SELECT
  tablename,
  (SELECT count(*) FROM information_schema.columns WHERE table_name = t.tablename) as columns,
  (SELECT count(*) FROM $tablename) as rows
FROM pg_tables t
WHERE schemaname = 'public'
ORDER BY tablename;
" 2>/dev/null | while read line; do
    echo "  $line"
done

echo ""

# 检查关键表
echo "✅ 检查核心数据表..."
CORE_TABLES=(
    "concepts"
    "stocks"
    "users"
    "stock_concepts"
    "daily_stock_data"
    "import_batches"
)

for table in "${CORE_TABLES[@]}"; do
    COUNT=$(psql -U postgres -h localhost -d stockdb -t -c "SELECT COUNT(*) FROM $table;" 2>/dev/null)
    if [ $? -eq 0 ]; then
        log_success "$table: $COUNT 行"
    else
        log_warn "$table: 不存在或无权限"
    fi
done

echo ""

# 检查索引
echo "🔑 检查数据库索引..."
INDEX_COUNT=$(psql -U postgres -h localhost -d stockdb -t -c "SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public';")
log_success "索引总数: $INDEX_COUNT"

echo ""

# 测试连接字符串
echo "🧪 测试连接字符串..."
cat << EOF
PostgreSQL 连接字符串:
  postgresql+psycopg2://postgres:Pp123456@localhost/stockdb

环境变量配置:
  DATABASE_URL=postgresql+psycopg2://postgres:Pp123456@localhost/stockdb
  DATABASE_HOST=localhost
  DATABASE_PORT=5432
  DATABASE_USER=postgres
  DATABASE_PASSWORD=Pp123456
  DATABASE_NAME=stockdb
EOF

echo ""

# 最后的状态检查
echo "✅ PostgreSQL 数据库验证完成"
echo ""
echo "💡 下一步:"
echo "  1. 运行部署脚本: ./scripts/deployment/deploy.sh"
echo "  2. 启动应用: ./start.sh"
echo "  3. 访问 API: http://localhost:3007"
