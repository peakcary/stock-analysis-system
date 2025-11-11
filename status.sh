#!/bin/bash

# 股票分析系统 - 状态检查脚本 v2.7.3
echo "📊 股票分析系统 - 状态检查"
echo "========================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 端口配置
BACKEND_PORT=3007
FRONTEND_PORT=8006
CLIENT_PORT=8005

check_service() {
    local port=$1
    local service=$2
    local url=$3
    local default_user=$4
    local default_pass=$5

    if lsof -ti:$port >/dev/null 2>&1; then
        echo -e "${GREEN}✅${NC} $service (端口 $port)"
        echo "   URL: $url"
        if [ ! -z "$default_user" ]; then
            echo "   默认账户: $default_user / $default_pass"
        fi
        return 0
    else
        echo -e "${RED}❌${NC} $service (端口 $port) - 未运行"
        return 1
    fi
}

# ==================== 服务状态 ====================
echo -e "${BLUE}🔌 服务状态${NC}"
echo "────────────────────"

check_service $BACKEND_PORT "后端 API" "http://localhost:$BACKEND_PORT" "" ""
check_service $FRONTEND_PORT "管理端" "http://localhost:$FRONTEND_PORT" "admin" "admin123"
check_service $CLIENT_PORT "客户端" "http://localhost:$CLIENT_PORT" "fullaccess_user" "fullaccess123"

echo ""

# ==================== MySQL状态 ====================
echo -e "${BLUE}🗄️  MySQL状态${NC}"
echo "────────────────────"

if command -v mysql >/dev/null 2>&1; then
    if mysqladmin ping -h127.0.0.1 --silent 2>/dev/null; then
        echo -e "${GREEN}✅${NC} MySQL: 运行中 (127.0.0.1:3306)"
        # 检查数据库
        if mysql -u root 2>/dev/null -e "USE stock_analysis_dev" 2>/dev/null; then
            echo -e "${GREEN}✅${NC} 数据库: stock_analysis_dev"
        else
            echo -e "${YELLOW}⚠️${NC} 数据库: stock_analysis_dev 不存在"
        fi
    else
        echo -e "${RED}❌${NC} MySQL: 未运行"
    fi
else
    echo -e "${YELLOW}⚠️${NC} MySQL: 未安装"
fi

echo ""

# ==================== 日志检查 ====================
echo -e "${BLUE}📝 日志文件${NC}"
echo "────────────────────"

if [ -f "logs/backend.log" ]; then
    lines=$(wc -l < logs/backend.log)
    echo -e "${GREEN}✅${NC} 后端日志: $lines 行"
    echo "   查看: tail -f logs/backend.log"
else
    echo -e "${YELLOW}⚠️${NC} 后端日志: 不存在"
fi

if [ -f "logs/frontend.log" ]; then
    lines=$(wc -l < logs/frontend.log)
    echo -e "${GREEN}✅${NC} 前端日志: $lines 行"
    echo "   查看: tail -f logs/frontend.log"
else
    echo -e "${YELLOW}⚠️${NC} 前端日志: 不存在"
fi

if [ -f "logs/client.log" ]; then
    lines=$(wc -l < logs/client.log)
    echo -e "${GREEN}✅${NC} 客户端日志: $lines 行"
    echo "   查看: tail -f logs/client.log"
else
    echo -e "${YELLOW}⚠️${NC} 客户端日志: 不存在"
fi

echo ""

# ==================== 快速命令 ====================
echo -e "${BLUE}⚡ 快速命令${NC}"
echo "────────────────────"
echo "启动:     ./start.sh"
echo "停止:     ./stop.sh"
echo "重启:     ./restart.sh"
echo "检查环境: ./check-env.sh"
echo ""
