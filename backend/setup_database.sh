#!/bin/bash

# 数据库设置脚本 (Database Setup Script)
# 用于初始化和迁移腾讯云数据库

set -e  # 任何命令失败则退出

echo "=================================================="
echo "股票分析系统 - 数据库初始化脚本"
echo "Database Setup Script for Stock Analysis System"
echo "=================================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查 Python 和必要的包
echo -e "${BLUE}[1/5]${NC} 检查 Python 环境..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ 找不到 Python 3${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python 3 已安装${NC}"
PYTHON_VERSION=$(python3 --version)
echo "   $PYTHON_VERSION"
echo ""

# 检查虚拟环境（可选）
echo -e "${BLUE}[2/5]${NC} 检查依赖包..."
if ! python3 -c "import sqlalchemy" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  SQLAlchemy 未安装，正在安装依赖...${NC}"
    pip install -r requirements.txt
else
    echo -e "${GREEN}✅ 依赖包已安装${NC}"
fi
echo ""

# 测试数据库连接
echo -e "${BLUE}[3/5]${NC} 测试数据库连接..."
if python3 test_db_connection.py; then
    echo -e "${GREEN}✅ 数据库连接成功${NC}"
else
    echo -e "${RED}❌ 数据库连接失败，请检查配置${NC}"
    exit 1
fi
echo ""

# 检查 Alembic
echo -e "${BLUE}[4/5]${NC} 检查 Alembic 迁移工具..."
if ! command -v alembic &> /dev/null; then
    echo -e "${YELLOW}⚠️  Alembic 未安装${NC}"
    pip install alembic
fi
echo -e "${GREEN}✅ Alembic 已就绪${NC}"
echo ""

# 执行数据库迁移
echo -e "${BLUE}[5/5]${NC} 执行数据库迁移..."
echo "   运行: alembic upgrade head"
alembic upgrade head
echo -e "${GREEN}✅ 数据库迁移完成${NC}"
echo ""

# 验证迁移
echo "=================================================="
echo "迁移验证 (Verification)"
echo "=================================================="
echo ""

echo -e "${BLUE}当前迁移状态:${NC}"
alembic current
echo ""

echo -e "${BLUE}迁移历史:${NC}"
alembic history
echo ""

# 数据库表统计
echo "正在检查数据库表..."
python3 test_db_connection.py
echo ""

echo "=================================================="
echo -e "${GREEN}✅ 数据库初始化完成!${NC}"
echo "=================================================="
echo ""
echo "后续步骤:"
echo "1. 启动后端服务:"
echo "   uvicorn app.main:app --host 0.0.0.0 --port 3007 --reload"
echo ""
echo "2. 导入示例数据 (可选):"
echo "   使用 API 端点 POST /api/v1/import/universal"
echo ""
echo "3. 访问 API 文档:"
echo "   http://localhost:3007/docs"
echo ""
