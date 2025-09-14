#!/bin/bash

# 数据库优化验证脚本 v2.6.4
echo "⚡ 数据库优化验证工具"
echo "===================="

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_success() { echo -e "${GREEN}[✅]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[⚠️]${NC} $1"; }
log_error() { echo -e "${RED}[❌]${NC} $1"; }

echo ""
echo "🔍 验证数据库优化状态..."

# 1. 检查优化表是否存在
echo ""
echo "1️⃣ 检查优化表结构..."
mysql -u root -p stock_analysis_dev -e "
SELECT 
    TABLE_NAME as '优化表',
    TABLE_ROWS as '记录数',
    ENGINE as '引擎',
    TABLE_COMMENT as '说明'
FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = 'stock_analysis_dev' 
  AND TABLE_NAME IN (
    'daily_trading_unified',
    'concept_daily_metrics', 
    'stock_concept_daily_snapshot',
    'today_trading_cache'
  )
ORDER BY TABLE_NAME;
" 2>/dev/null

if [ $? -eq 0 ]; then
    log_success "优化表结构检查完成"
else
    log_error "优化表结构检查失败"
fi

# 2. 检查视图是否存在
echo ""
echo "2️⃣ 检查高性能视图..."
mysql -u root -p stock_analysis_dev -e "
SELECT 
    TABLE_NAME as '高性能视图'
FROM information_schema.VIEWS 
WHERE TABLE_SCHEMA = 'stock_analysis_dev' 
  AND TABLE_NAME LIKE 'v_%'
ORDER BY TABLE_NAME;
" 2>/dev/null

# 3. 测试查询性能
echo ""
echo "3️⃣ 测试查询性能..."
mysql -u root -p stock_analysis_dev -e "
-- 股票列表查询性能测试
SET @start_time = NOW(3);
SELECT COUNT(*) as '记录数' FROM v_stock_daily_summary LIMIT 1;
SET @end_time = NOW(3);
SELECT CONCAT('股票查询耗时: ', TIMESTAMPDIFF(MICROSECOND, @start_time, @end_time) / 1000, ' 毫秒') as '性能测试';

-- 概念排行查询性能测试  
SET @start_time = NOW(3);
SELECT COUNT(*) as '概念数' FROM v_concept_daily_ranking LIMIT 1;
SET @end_time = NOW(3);
SELECT CONCAT('概念查询耗时: ', TIMESTAMPDIFF(MICROSECOND, @start_time, @end_time) / 1000, ' 毫秒') as '性能测试';
" 2>/dev/null

# 4. 检查环境配置
echo ""
echo "4️⃣ 检查环境配置..."
if [ -f "backend/.env" ]; then
    echo "🔧 优化配置状态:"
    grep -E "(USE_OPTIMIZED_TABLES|ENABLE_PERFORMANCE_LOG|ENABLE_QUERY_CACHE)" backend/.env 2>/dev/null || echo "配置文件需要更新"
else
    log_warn "环境配置文件不存在"
fi

# 5. 检查优化工具
echo ""
echo "5️⃣ 检查优化管理工具..."
if [ -f "scripts/database/enable_optimization.py" ]; then
    echo "🛠️ 优化工具状态:"
    python3 scripts/database/enable_optimization.py status 2>/dev/null || log_warn "优化工具执行失败"
else
    log_error "优化管理工具不存在"
fi

echo ""
echo "✅ 验证完成！"
echo ""
echo "🚀 如果验证失败，请运行:"
echo "  ./scripts/database/deploy_optimization.sh --db-url \"mysql+pymysql://root:PASSWORD@localhost:3306/stock_analysis_dev\""
echo ""
echo "💡 获取更多帮助:"
echo "  ./scripts/database/deploy_optimization.sh --help"