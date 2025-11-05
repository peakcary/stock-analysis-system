#!/bin/bash

# ============================================
# 升级到 v2.7.0 脚本
# 功能：为已部署的系统添加原始数据表功能
# ============================================

echo "🚀 升级到 v2.7.0 - CSV原始数据表"
echo "================================"

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_success() { echo -e "${GREEN}[✅]${NC} $1"; }
log_error() { echo -e "${RED}[❌]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[⚠️]${NC} $1"; }

echo "📋 本次升级包含:"
echo "  ✅ 创建 stock_concept_raw_data 表"
echo "  ✅ 更新数据导入逻辑"
echo "  ✅ 新增原始数据API接口"
echo "  ✅ 修复配置问题"
echo ""

# 确认升级
read -p "是否继续升级？(y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "升级已取消"
    exit 0
fi

# 切换到项目根目录
cd "$(dirname "$0")/../.." || exit 1

echo ""
echo "🔍 步骤 1/4: 检查环境..."

# 检查MySQL连接
if ! mysqladmin ping -h127.0.0.1 --silent 2>/dev/null; then
    log_error "MySQL服务未运行"
    echo "请先启动MySQL: brew services start mysql"
    exit 1
fi
log_success "MySQL连接正常"

# 检查后端目录
if [ ! -d "backend" ]; then
    log_error "未找到backend目录"
    exit 1
fi
log_success "项目结构正常"

echo ""
echo "💾 步骤 2/4: 创建原始数据表..."

# 执行SQL创建表
if mysql -u root -pPp123456 stock_analysis_dev < scripts/database/create_raw_data_table.sql 2>&1 | grep -v "Warning"; then
    log_success "原始数据表创建完成"
else
    log_warn "表可能已存在（可忽略）"
fi

# 验证表是否存在
if mysql -u root -pPp123456 stock_analysis_dev -e "DESCRIBE stock_concept_raw_data;" 2>&1 | grep -v "Warning" > /dev/null; then
    log_success "表验证成功"
else
    log_error "表创建失败"
    exit 1
fi

echo ""
echo "⚙️ 步骤 3/4: 检查配置..."

# 检查ADMIN_SECRET_KEY
if grep -q "ADMIN_SECRET_KEY" backend/.env 2>/dev/null; then
    log_success "ADMIN_SECRET_KEY 配置存在"
else
    log_warn "ADMIN_SECRET_KEY 配置缺失，正在添加..."
    echo "ADMIN_SECRET_KEY=admin-secret-key-here-please-change-in-production-32chars" >> backend/.env
    log_success "配置已添加"
fi

echo ""
echo "🔄 步骤 4/4: 重启服务..."

# 停止后端
if [ -f "logs/backend.pid" ]; then
    kill $(cat logs/backend.pid) 2>/dev/null
    sleep 2
    log_success "后端已停止"
fi

# 启动后端
cd backend || exit 1
source venv/bin/activate
nohup python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 3007 > ../logs/backend.log 2>&1 &
echo $! > ../logs/backend.pid
cd ..

sleep 3

# 检查后端是否启动
if lsof -i:3007 > /dev/null 2>&1; then
    log_success "后端启动成功"
else
    log_error "后端启动失败"
    echo "请查看日志: tail -f logs/backend.log"
    exit 1
fi

echo ""
echo "✅ 升级完成！"
echo ""
echo "📊 新功能:"
echo "  ✅ CSV原始数据表 - 完整保存导入数据"
echo "  ✅ 原始数据API - /api/v1/raw-data/*"
echo "  ✅ 快速查询 - 单表查询，无需JOIN"
echo "  ✅ 数据审计 - 完整追溯导入记录"
echo ""
echo "🔗 访问地址:"
echo "  管理后台: http://localhost:8006"
echo "  API文档:  http://localhost:3007/docs"
echo ""
echo "📝 测试步骤:"
echo "  1. 登录管理后台 (admin / admin123)"
echo "  2. 导入CSV文件"
echo "  3. 检查导入日志，应看到原始数据写入信息"
echo "  4. 访问 /api/v1/raw-data/daily?trade_date=YYYY-MM-DD"
echo ""
echo "📚 详细文档: DEPLOYMENT_V2.7.md"
