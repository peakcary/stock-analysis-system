#!/bin/bash

# 股票分析系统 - 环境检查脚本 v2.7.3
echo "🔍 股票分析系统 - 环境检查"
echo "==========================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 计数器
CHECK_PASSED=0
CHECK_FAILED=0
CHECK_WARN=0

# 检查函数
check_command() {
    local name=$1
    local cmd=$2
    local min_version=$3

    if command -v $cmd >/dev/null 2>&1; then
        local version=$($cmd --version 2>/dev/null | head -n1)
        echo -e "${GREEN}✅${NC} $name: $version"
        ((CHECK_PASSED++))
        return 0
    else
        echo -e "${RED}❌${NC} $name: 未安装"
        ((CHECK_FAILED++))
        return 1
    fi
}

check_port() {
    local port=$1
    local service=$2

    if lsof -ti:$port >/dev/null 2>&1; then
        local pid=$(lsof -ti:$port | head -1)
        echo -e "${YELLOW}⚠️ ${NC} 端口 $port ($service) 已被占用 (PID: $pid)"
        ((CHECK_WARN++))
        return 1
    else
        echo -e "${GREEN}✅${NC} 端口 $port ($service) 可用"
        ((CHECK_PASSED++))
        return 0
    fi
}

check_directory() {
    local dir=$1
    local desc=$2

    if [ -d "$dir" ]; then
        echo -e "${GREEN}✅${NC} $desc: 存在"
        ((CHECK_PASSED++))
        return 0
    else
        echo -e "${RED}❌${NC} $desc: 缺失"
        ((CHECK_FAILED++))
        return 1
    fi
}

check_file() {
    local file=$1
    local desc=$2

    if [ -f "$file" ]; then
        echo -e "${GREEN}✅${NC} $desc: 存在"
        ((CHECK_PASSED++))
        return 0
    else
        echo -e "${YELLOW}⚠️ ${NC} $desc: 缺失"
        ((CHECK_WARN++))
        return 1
    fi
}

# ==================== 系统依赖检查 ====================
echo -e "${BLUE}📦 系统依赖检查${NC}"
echo "────────────────────"
check_command "Node.js" "node" "16.0"
check_command "Python" "python3" "3.8"
check_command "MySQL" "mysql" "8.0"
check_command "npm" "npm" "8.0"
echo ""

# ==================== 项目结构检查 ====================
echo -e "${BLUE}📁 项目结构检查${NC}"
echo "────────────────────"
check_directory "backend" "后端应用"
check_directory "frontend" "管理端应用"
check_directory "client" "客户端应用"
check_directory "shared" "共享代码"
check_directory "scripts" "脚本目录"
echo ""

# ==================== 配置文件检查 ====================
echo -e "${BLUE}⚙️  配置文件检查${NC}"
echo "────────────────────"
check_file "backend/requirements.txt" "Python依赖"
check_file "frontend/package.json" "前端配置"
check_file "client/package.json" "客户端配置"
check_file ".env.example" "环境变量示例"
check_file "docker-compose.yml" "Docker配置"
echo ""

# ==================== 端口可用性检查 ====================
echo -e "${BLUE}🔌 端口可用性检查${NC}"
echo "────────────────────"
check_port 3007 "API服务"
check_port 8006 "管理端"
check_port 8005 "客户端"
check_port 3306 "MySQL"
check_port 6379 "Redis (可选)"
echo ""

# ==================== 依赖检查 ====================
echo -e "${BLUE}📚 NPM/Python依赖检查${NC}"
echo "────────────────────"

if command -v npm >/dev/null 2>&1; then
    # 检查前端依赖
    if [ -d "frontend/node_modules" ]; then
        echo -e "${GREEN}✅${NC} 前端依赖: 已安装"
        ((CHECK_PASSED++))
    else
        echo -e "${YELLOW}⚠️ ${NC} 前端依赖: 未安装 (运行: cd frontend && npm install)"
        ((CHECK_WARN++))
    fi

    # 检查客户端依赖
    if [ -d "client/node_modules" ]; then
        echo -e "${GREEN}✅${NC} 客户端依赖: 已安装"
        ((CHECK_PASSED++))
    else
        echo -e "${YELLOW}⚠️ ${NC} 客户端依赖: 未安装 (运行: cd client && npm install)"
        ((CHECK_WARN++))
    fi
fi

if command -v python3 >/dev/null 2>&1; then
    # 检查Python虚拟环境
    if [ -d "backend/venv" ]; then
        echo -e "${GREEN}✅${NC} Python虚拟环境: 已创建"
        ((CHECK_PASSED++))

        # 检查关键包
        if source backend/venv/bin/activate 2>/dev/null && python -c "import fastapi, sqlalchemy, uvicorn" 2>/dev/null; then
            echo -e "${GREEN}✅${NC} 后端依赖: 已安装"
            ((CHECK_PASSED++))
            deactivate 2>/dev/null
        else
            echo -e "${YELLOW}⚠️ ${NC} 后端依赖: 不完整 (运行: cd backend && pip install -r requirements.txt)"
            ((CHECK_WARN++))
        fi
    else
        echo -e "${YELLOW}⚠️ ${NC} Python虚拟环境: 未创建 (运行: cd backend && python3 -m venv venv)"
        ((CHECK_WARN++))
    fi
fi

echo ""

# ==================== 数据库检查 ====================
echo -e "${BLUE}🗄️  数据库检查${NC}"
echo "────────────────────"

if command -v mysql >/dev/null 2>&1; then
    # 检查MySQL服务
    if mysqladmin ping -h127.0.0.1 --silent 2>/dev/null; then
        echo -e "${GREEN}✅${NC} MySQL服务: 运行中"
        ((CHECK_PASSED++))

        # 检查数据库
        if mysql -u root 2>/dev/null -e "USE stock_analysis_dev" 2>/dev/null; then
            echo -e "${GREEN}✅${NC} 数据库: stock_analysis_dev 存在"
            ((CHECK_PASSED++))
        else
            echo -e "${YELLOW}⚠️ ${NC} 数据库: stock_analysis_dev 不存在 (需要初始化)"
            ((CHECK_WARN++))
        fi
    else
        echo -e "${YELLOW}⚠️ ${NC} MySQL服务: 未运行 (运行: brew services start mysql)"
        ((CHECK_WARN++))
    fi
else
    echo -e "${YELLOW}⚠️ ${NC} MySQL: 未安装"
    ((CHECK_WARN++))
fi

echo ""

# ==================== 脚本检查 ====================
echo -e "${BLUE}🚀 启动脚本检查${NC}"
echo "────────────────────"
check_file "start-dev.sh" "开发启动脚本"
check_file "stop-dev.sh" "停止脚本"
check_file "scripts/deployment/deploy.sh" "部署脚本"
echo ""

# ==================== 总结 ====================
echo -e "${BLUE}📊 检查总结${NC}"
echo "────────────────────"
echo -e "${GREEN}✅ 通过${NC}: $CHECK_PASSED"
echo -e "${YELLOW}⚠️  警告${NC}: $CHECK_WARN"
echo -e "${RED}❌ 失败${NC}: $CHECK_FAILED"
echo ""

if [ $CHECK_FAILED -eq 0 ] && [ $CHECK_WARN -le 2 ]; then
    echo -e "${GREEN}✨ 环境检查完成！可以开始开发${NC}"
    echo ""
    echo "📖 推荐的下一步："
    echo "  1. ./check-env.sh        - 运行本检查脚本"
    echo "  2. ./quick-deploy.sh     - 快速安装依赖"
    echo "  3. ./start-dev.sh        - 启动开发服务"
    echo ""
    exit 0
elif [ $CHECK_FAILED -eq 0 ]; then
    echo -e "${YELLOW}⚠️  环境检查完成，有些部分需要配置${NC}"
    echo ""
    echo "💡 需要执行的命令："

    if ! command -v node >/dev/null 2>&1; then
        echo "  • 安装Node.js: brew install node"
    fi

    if ! command -v python3 >/dev/null 2>&1; then
        echo "  • 安装Python: brew install python3"
    fi

    if ! command -v mysql >/dev/null 2>&1; then
        echo "  • 安装MySQL: brew install mysql && brew services start mysql"
    fi

    if [ ! -d "frontend/node_modules" ] || [ ! -d "client/node_modules" ]; then
        echo "  • 安装NPM依赖: ./quick-deploy.sh"
    fi

    if ! mysqladmin ping -h127.0.0.1 --silent 2>/dev/null; then
        echo "  • 启动MySQL: brew services start mysql"
    fi

    echo ""
    exit 1
else
    echo -e "${RED}❌ 环境检查失败，请解决以下问题${NC}"
    echo ""
    echo "💡 需要执行的命令："
    echo "  • 安装缺失的系统依赖"
    echo "  • 查看 QUICKSTART.md 获取详细指导"
    echo "  • 运行 ./check-env.sh 验证环境"
    echo ""
    exit 1
fi
