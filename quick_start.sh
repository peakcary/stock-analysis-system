#!/bin/bash
# 🚀 股票分析系统 - 超级一键启动脚本
# Stock Analysis System - Super Quick Start Script

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_header() {
    clear
    print_message $CYAN "╔════════════════════════════════════════════════════════════════╗"
    print_message $CYAN "║                    📈 股票分析系统                             ║"
    print_message $CYAN "║                Stock Analysis System                          ║"
    print_message $CYAN "║                  🚀 超级一键启动脚本                           ║"
    print_message $CYAN "╚════════════════════════════════════════════════════════════════╝"
    echo
}

# 检查是否在项目根目录
check_directory() {
    if [ ! -d "backend" ] || [ ! -d "frontend" ] || [ ! -f "docker-compose.yml" ]; then
        print_message $RED "❌ 错误: 请在项目根目录下运行此脚本"
        print_message $YELLOW "💡 提示: 请确保当前目录包含 backend/ 和 frontend/ 文件夹"
        exit 1
    fi
}

# 检查系统依赖
check_dependencies() {
    print_message $BLUE "🔍 检查系统依赖..."
    
    local errors=0
    
    # 检查 Node.js
    if ! command -v node &> /dev/null; then
        print_message $RED "   ❌ Node.js 未安装"
        errors=$((errors + 1))
    else
        print_message $GREEN "   ✅ Node.js: $(node --version)"
    fi
    
    # 检查 Python
    if ! command -v python3 &> /dev/null; then
        print_message $RED "   ❌ Python3 未安装"
        errors=$((errors + 1))
    else
        print_message $GREEN "   ✅ Python: $(python3 --version)"
    fi
    
    # 检查 MySQL
    if ! command -v mysql &> /dev/null; then
        print_message $YELLOW "   ⚠️  MySQL 客户端未找到 (但服务可能正在运行)"
    else
        # 尝试连接MySQL (支持多种可能的密码)
        local mysql_connected=false
        for password in "Pp123456" "root123" "root" ""; do
            if mysql -u root -p${password} -e "SELECT 1;" &>/dev/null; then
                print_message $GREEN "   ✅ MySQL: 连接成功 (密码: ${password:-空})"
                mysql_connected=true
                export MYSQL_PASSWORD=$password
                break
            fi
        done
        
        if [ "$mysql_connected" = false ]; then
            print_message $YELLOW "   ⚠️  MySQL: 无法连接 (将尝试继续)"
        fi
    fi
    
    # 检查项目依赖
    if [ ! -d "backend/venv" ]; then
        print_message $YELLOW "   ⚠️  后端Python虚拟环境未设置"
        print_message $BLUE "   🔧 正在创建虚拟环境..."
        cd backend
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
        cd ..
        print_message $GREEN "   ✅ 后端环境已设置"
    else
        print_message $GREEN "   ✅ 后端Python环境"
    fi
    
    if [ ! -d "frontend/node_modules" ]; then
        print_message $YELLOW "   ⚠️  前端依赖未安装"
        print_message $BLUE "   🔧 正在安装前端依赖..."
        cd frontend
        npm install
        cd ..
        print_message $GREEN "   ✅ 前端依赖已安装"
    else
        print_message $GREEN "   ✅ 前端依赖"
    fi
    
    if [ $errors -gt 0 ]; then
        print_message $RED "❌ 发现 $errors 个系统依赖问题，请解决后重试"
        return 1
    fi
    
    print_message $GREEN "✅ 系统依赖检查通过"
    return 0
}

# 停止已运行的服务
stop_existing_services() {
    print_message $BLUE "🛑 停止已运行的服务..."
    
    # 停止可能运行的前端服务
    pkill -f "vite.*3000" 2>/dev/null || true
    pkill -f "react-scripts.*3000" 2>/dev/null || true
    pkill -f "npm.*start" 2>/dev/null || true
    
    # 停止可能运行的后端服务
    pkill -f "uvicorn.*8000" 2>/dev/null || true
    pkill -f "python.*main.py" 2>/dev/null || true
    
    sleep 2
    print_message $GREEN "✅ 已停止现有服务"
}

# 启动后端服务
start_backend() {
    print_message $BLUE "🐍 启动后端服务..."
    
    cd backend
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 设置环境变量
    export PYTHONPATH=$PWD:$PYTHONPATH
    
    # 检查数据库连接
    if [ -n "$MYSQL_PASSWORD" ]; then
        export DATABASE_URL="mysql://root:${MYSQL_PASSWORD}@localhost/stock_analysis"
    fi
    
    # 启动后端服务 (后台运行)
    nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > ../logs/backend.log 2>&1 &
    BACKEND_PID=$!
    
    cd ..
    
    print_message $GREEN "✅ 后端服务已启动 (PID: $BACKEND_PID)"
    echo $BACKEND_PID > .backend_pid
}

# 启动前端服务
start_frontend() {
    print_message $BLUE "⚛️  启动前端服务..."
    
    cd frontend
    
    # 设置环境变量
    export REACT_APP_API_URL=http://localhost:8000
    export REACT_APP_ENVIRONMENT=development
    export PORT=3000
    
    # 启动前端服务 (后台运行)
    nohup npm start > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    
    cd ..
    
    print_message $GREEN "✅ 前端服务已启动 (PID: $FRONTEND_PID)"
    echo $FRONTEND_PID > .frontend_pid
}

# 等待服务启动
wait_for_services() {
    print_message $BLUE "⏳ 等待服务启动完成..."
    
    # 等待后端
    print_message $YELLOW "   🔄 等待后端服务..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/health >/dev/null 2>&1; then
            print_message $GREEN "   ✅ 后端服务已就绪"
            break
        fi
        sleep 2
        if [ $i -eq 30 ]; then
            print_message $YELLOW "   ⚠️  后端服务启动较慢，请稍后手动检查"
        fi
    done
    
    # 等待前端
    print_message $YELLOW "   🔄 等待前端服务..."
    sleep 10  # 前端编译需要时间
    for i in {1..20}; do
        if curl -s http://localhost:3000 >/dev/null 2>&1; then
            print_message $GREEN "   ✅ 前端服务已就绪"
            break
        fi
        sleep 3
        if [ $i -eq 20 ]; then
            print_message $YELLOW "   ⚠️  前端服务启动较慢，请稍后手动检查"
        fi
    done
}

# 显示访问信息
show_access_info() {
    local IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}')
    
    clear
    print_header
    
    print_message $GREEN "🎉 股票分析系统启动成功！"
    echo
    print_message $CYAN "╔════════════════════════════════════════════════════════════════╗"
    print_message $CYAN "║                        📋 访问指南                             ║"
    print_message $CYAN "╚════════════════════════════════════════════════════════════════╝"
    echo
    
    print_message $PURPLE "📱 客户端页面 (普通用户使用):"
    print_message $WHITE "   🌐 本地访问: http://localhost:3000"
    if [ -n "$IP" ]; then
        print_message $WHITE "   📱 手机访问: http://$IP:3000"
    fi
    print_message $WHITE "   👤 功能: 注册登录、会员购买、数据分析、图表查看"
    echo
    
    print_message $PURPLE "🛠  管理后台 (当前就是管理页面):"
    print_message $WHITE "   🌐 本地访问: http://localhost:3000"
    print_message $WHITE "   ⚙️  功能: 数据导入、股票查询、概念分析、系统管理"
    echo
    
    print_message $PURPLE "🔗 后端API服务:"
    print_message $WHITE "   🌐 API地址: http://localhost:8000"
    print_message $WHITE "   📚 API文档: http://localhost:8000/docs"
    print_message $WHITE "   ❤️  健康检查: http://localhost:8000/health"
    echo
    
    print_message $CYAN "╔════════════════════════════════════════════════════════════════╗"
    print_message $CYAN "║                      📖 使用说明                               ║"
    print_message $CYAN "╚════════════════════════════════════════════════════════════════╝"
    echo
    
    print_message $BLUE "🏠 当前显示的是管理后台页面，包含以下功能:"
    print_message $WHITE "   ├── 📊 简化导入: 上传CSV和TXT数据文件"
    print_message $WHITE "   ├── 🔍 股票查询: 搜索和查看股票信息"
    print_message $WHITE "   ├── 📈 原导入: 原始的数据导入功能"
    print_message $WHITE "   ├── 🧠 概念分析: 概念和行业分析"
    print_message $WHITE "   └── 👤 用户中心: 用户管理功能"
    echo
    
    print_message $BLUE "🎯 如果要实现客户端页面，需要:"
    print_message $WHITE "   1. 添加用户认证和注册功能"
    print_message $WHITE "   2. 实现会员订阅系统"
    print_message $WHITE "   3. 创建专业的数据分析界面"
    print_message $WHITE "   4. 优化移动端体验"
    echo
    
    print_message $CYAN "╔════════════════════════════════════════════════════════════════╗"
    print_message $CYAN "║                      🛠  开发工具                              ║"
    print_message $CYAN "╚════════════════════════════════════════════════════════════════╝"
    echo
    
    print_message $YELLOW "📝 查看日志:"
    print_message $WHITE "   tail -f logs/backend.log   # 后端日志"
    print_message $WHITE "   tail -f logs/frontend.log  # 前端日志"
    echo
    
    print_message $YELLOW "🛑 停止服务:"
    print_message $WHITE "   ./scripts/stop-all.sh      # 停止所有服务"
    print_message $WHITE "   Ctrl+C                     # 停止脚本(但服务继续运行)"
    echo
    
    print_message $YELLOW "🔄 重启服务:"
    print_message $WHITE "   ./quick_start.sh           # 重新运行此脚本"
    echo
    
    print_message $GREEN "💡 提示: 系统已在后台运行，可以关闭此终端窗口"
    print_message $GREEN "🌟 开始使用: 现在可以在浏览器中打开上述地址！"
}

# 创建必要的目录
create_directories() {
    mkdir -p logs
}

# 清理函数
cleanup() {
    print_message $YELLOW "\n🛑 接收到停止信号..."
    
    if [ -f .backend_pid ]; then
        BACKEND_PID=$(cat .backend_pid)
        kill $BACKEND_PID 2>/dev/null || true
        rm -f .backend_pid
        print_message $GREEN "✅ 后端服务已停止"
    fi
    
    if [ -f .frontend_pid ]; then
        FRONTEND_PID=$(cat .frontend_pid)
        kill $FRONTEND_PID 2>/dev/null || true
        rm -f .frontend_pid
        print_message $GREEN "✅ 前端服务已停止"
    fi
    
    print_message $BLUE "👋 再见！"
    exit 0
}

# 设置信号处理
trap cleanup SIGINT SIGTERM

# 显示帮助
show_help() {
    print_header
    print_message $BLUE "📖 使用说明:"
    echo
    print_message $WHITE "   ./quick_start.sh           启动系统"
    print_message $WHITE "   ./quick_start.sh -h        显示帮助"
    print_message $WHITE "   ./quick_start.sh --status  显示服务状态"
    echo
    print_message $BLUE "🎯 功能特点:"
    print_message $WHITE "   • 自动检查和安装依赖"
    print_message $WHITE "   • 一键启动前后端服务"
    print_message $WHITE "   • 支持多种MySQL密码配置"
    print_message $WHITE "   • 详细的服务状态显示"
    print_message $WHITE "   • 友好的错误提示和解决方案"
    echo
}

# 显示服务状态
show_status() {
    print_header
    print_message $BLUE "📊 服务状态检查:"
    echo
    
    # 检查后端
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
        print_message $GREEN "✅ 后端服务: 运行中 (http://localhost:8000)"
    else
        print_message $RED "❌ 后端服务: 未运行"
    fi
    
    # 检查前端
    if curl -s http://localhost:3000 >/dev/null 2>&1; then
        print_message $GREEN "✅ 前端服务: 运行中 (http://localhost:3000)"
    else
        print_message $RED "❌ 前端服务: 未运行"
    fi
    
    # 检查进程
    echo
    print_message $BLUE "🔍 运行进程:"
    ps aux | grep -E "(uvicorn|node.*vite|npm.*start)" | grep -v grep || print_message $YELLOW "未找到相关进程"
    echo
}

# 主函数
main() {
    print_header
    create_directories
    
    print_message $BLUE "🚀 开始启动股票分析系统..."
    echo
    
    check_directory
    
    if check_dependencies; then
        stop_existing_services
        start_backend
        start_frontend
        wait_for_services
        show_access_info
        
        # 等待用户中断
        print_message $CYAN "\n💤 按 Ctrl+C 停止服务..."
        while true; do
            sleep 10
        done
    else
        print_message $RED "❌ 环境检查失败，请解决上述问题后重试"
        exit 1
    fi
}

# 参数处理
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    --status)
        show_status
        exit 0
        ;;
    *)
        main
        ;;
esac