#!/bin/bash
# 🚀 股票分析系统 - 完整服务启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_header() {
    clear
    print_message $CYAN "╔════════════════════════════════════════════════════════════════╗"
    print_message $CYAN "║                    📈 股票分析系统                             ║"
    print_message $CYAN "║                完整服务启动 - 三端同时启动                      ║"
    print_message $CYAN "╚════════════════════════════════════════════════════════════════╝"
    echo
}

check_dependencies() {
    print_message $BLUE "🔍 检查系统依赖..."
    
    # 检查后端环境
    if [ ! -d "backend/venv" ]; then
        print_message $YELLOW "   ⚠️  后端Python虚拟环境未设置，正在创建..."
        cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && cd ..
    fi
    
    # 检查管理后台前端
    if [ ! -d "frontend/node_modules" ]; then
        print_message $YELLOW "   ⚠️  管理后台依赖未安装，正在安装..."
        cd frontend && npm install && cd ..
    fi
    
    # 检查客户端
    if [ ! -d "client/node_modules" ]; then
        print_message $YELLOW "   ⚠️  客户端依赖未安装，正在安装..."
        cd client && npm install && cd ..
    fi
    
    print_message $GREEN "✅ 依赖检查完成"
}

start_backend() {
    print_message $BLUE "🐍 启动后端服务 (端口8000)..."
    cd backend
    source venv/bin/activate
    nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > ../logs/backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > ../.backend_pid
    cd ..
    print_message $GREEN "✅ 后端服务已启动 (PID: $BACKEND_PID)"
    sleep 3
}

start_admin_frontend() {
    print_message $BLUE "🛠  启动管理后台 (端口3000)..."
    cd frontend
    nohup npm start > ../logs/admin-frontend.log 2>&1 &
    ADMIN_PID=$!
    echo $ADMIN_PID > ../.admin_pid
    cd ..
    print_message $GREEN "✅ 管理后台已启动 (PID: $ADMIN_PID)"
    sleep 3
}

start_client() {
    print_message $BLUE "👥 启动客户端 (端口3001)..."
    cd client
    nohup npm run dev > ../logs/client.log 2>&1 &
    CLIENT_PID=$!
    echo $CLIENT_PID > ../.client_pid
    cd ..
    print_message $GREEN "✅ 客户端已启动 (PID: $CLIENT_PID)"
    sleep 3
}

wait_for_services() {
    print_message $BLUE "⏳ 等待所有服务启动完成..."
    
    # 等待后端
    for i in {1..30}; do
        if curl -s http://localhost:8000/health >/dev/null 2>&1; then
            print_message $GREEN "   ✅ 后端服务就绪"
            break
        fi
        sleep 2
    done
    
    # 等待管理后台
    sleep 8
    for i in {1..20}; do
        if curl -s http://localhost:3000 >/dev/null 2>&1; then
            print_message $GREEN "   ✅ 管理后台就绪"
            break
        fi
        sleep 3
    done
    
    # 等待客户端
    sleep 8
    for i in {1..20}; do
        if curl -s http://localhost:3001 >/dev/null 2>&1; then
            print_message $GREEN "   ✅ 客户端就绪"
            break
        fi
        sleep 3
    done
}

show_access_info() {
    local IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}')
    
    clear
    print_header
    
    print_message $GREEN "🎉 股票分析系统全部服务启动成功！"
    echo
    print_message $CYAN "╔════════════════════════════════════════════════════════════════╗"
    print_message $CYAN "║                        📋 访问指南                             ║"
    print_message $CYAN "╚════════════════════════════════════════════════════════════════╝"
    echo
    
    print_message $PURPLE "🛠  管理后台页面 (系统管理员使用):"
    print_message $WHITE "   🌐 本地访问: http://localhost:3000"
    if [ -n "$IP" ]; then
        print_message $WHITE "   📱 手机访问: http://$IP:3000"
    fi
    print_message $WHITE "   👨‍💼 功能: 数据导入、股票查询、系统管理"
    echo
    
    print_message $PURPLE "👥 客户端页面 (普通用户使用):"
    print_message $WHITE "   🌐 本地访问: http://localhost:3001"
    if [ -n "$IP" ]; then
        print_message $WHITE "   📱 手机访问: http://$IP:3001"
    fi
    print_message $WHITE "   🎯 功能: 用户注册登录、会员订阅、数据分析、移动端体验"
    echo
    
    print_message $PURPLE "🔗 后端API服务:"
    print_message $WHITE "   🌐 API地址: http://localhost:8000"
    print_message $WHITE "   📚 API文档: http://localhost:8000/docs"
    echo
    
    print_message $CYAN "╔════════════════════════════════════════════════════════════════╗"
    print_message $CYAN "║                      📖 使用说明                               ║"
    print_message $CYAN "╚════════════════════════════════════════════════════════════════╝"
    echo
    
    print_message $BLUE "🎯 两个不同的前端页面:"
    print_message $WHITE "   🛠  管理后台 (端口3000): 给管理员用的数据管理界面"
    print_message $WHITE "   👥 客户端 (端口3001): 给普通用户的现代化分析平台"
    echo
    
    print_message $BLUE "✨ 客户端特色功能:"
    print_message $WHITE "   🔐 用户注册登录系统"
    print_message $WHITE "   💎 三级会员体系 (免费版/专业版/旗舰版)"
    print_message $WHITE "   📊 专业的数据分析界面"
    print_message $WHITE "   📱 完美的移动端体验"
    print_message $WHITE "   🎨 现代化UI设计和交互"
    echo
    
    print_message $CYAN "╔════════════════════════════════════════════════════════════════╗"
    print_message $CYAN "║                      🛠  开发工具                              ║"
    print_message $CYAN "╚════════════════════════════════════════════════════════════════╝"
    echo
    
    print_message $YELLOW "📝 查看日志:"
    print_message $WHITE "   tail -f logs/backend.log        # 后端日志"
    print_message $WHITE "   tail -f logs/admin-frontend.log # 管理后台日志"
    print_message $WHITE "   tail -f logs/client.log         # 客户端日志"
    echo
    
    print_message $YELLOW "🛑 停止服务:"
    print_message $WHITE "   ./stop_all_services.sh          # 停止所有服务"
    echo
    
    print_message $GREEN "🌟 开始使用:"
    print_message $WHITE "   管理员: 打开 http://localhost:3000 进行数据管理"
    print_message $WHITE "   用户: 打开 http://localhost:3001 注册并体验分析功能"
}

cleanup() {
    print_message $YELLOW "\n🛑 停止所有服务..."
    
    if [ -f .backend_pid ]; then
        kill $(cat .backend_pid) 2>/dev/null || true
        rm -f .backend_pid
    fi
    
    if [ -f .admin_pid ]; then
        kill $(cat .admin_pid) 2>/dev/null || true
        rm -f .admin_pid
    fi
    
    if [ -f .client_pid ]; then
        kill $(cat .client_pid) 2>/dev/null || true
        rm -f .client_pid
    fi
    
    pkill -f "uvicorn.*8000" 2>/dev/null || true
    pkill -f "vite.*3000" 2>/dev/null || true  
    pkill -f "vite.*3001" 2>/dev/null || true
    
    print_message $GREEN "✅ 所有服务已停止"
    exit 0
}

trap cleanup SIGINT SIGTERM

# 主函数
main() {
    print_header
    
    # 创建日志目录
    mkdir -p logs
    
    # 检查依赖
    check_dependencies
    
    # 启动所有服务
    start_backend
    start_admin_frontend
    start_client
    
    # 等待服务就绪
    wait_for_services
    
    # 显示访问信息
    show_access_info
    
    # 保持脚本运行
    print_message $CYAN "\n💤 所有服务运行中，按 Ctrl+C 停止..."
    while true; do
        sleep 10
    done
}

main