#!/bin/bash
# 股票分析系统 - 一键启动脚本
# Stock Analysis System - One-Click Start Script
# 版本：修复IPv4/IPv6兼容性和端口配置

set -e

echo "🚀 启动所有服务..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查端口是否被占用
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        log_warn "端口 $1 已被占用，跳过启动"
        return 1
    fi
    return 0
}

# 检查MySQL服务状态
check_mysql() {
    if ! brew services list | grep mysql@8.0 | grep started &> /dev/null; then
        log_warn "MySQL服务未启动，正在启动..."
        brew services start mysql@8.0
        sleep 3
    fi
    log_info "✅ MySQL服务正常"
}

# 创建日志目录
create_log_dir() {
    if [ ! -d "logs" ]; then
        mkdir -p logs
        log_info "创建日志目录"
    fi
}

# 主启动流程
main() {
    log_info "========================================="
    log_info "🚀 股票分析系统启动中..."
    log_info "========================================="
    
    # 前置检查
    create_log_dir
    check_mysql
    
    # 启动后端服务
    if check_port 3007; then
        log_info "启动后端服务 (端口 3007)..."
        if [ ! -f "start_backend.sh" ]; then
            log_error "start_backend.sh 不存在"
            exit 1
        fi
        ./start_backend.sh > logs/backend.log 2>&1 &
        log_info "✅ 后端服务已在后台启动"
        sleep 3
    fi
    
    # 启动用户前端客户端
    if check_port 8006; then
        log_info "启动用户前端客户端 (端口 8006)..."
        if [ ! -f "start_client.sh" ]; then
            log_error "start_client.sh 不存在"
        else
            ./start_client.sh > logs/client.log 2>&1 &
            log_info "✅ 用户前端客户端已在后台启动"
        fi
    fi
    
    # 启动管理前端
    if [ -f "start_frontend.sh" ] && check_port 8005; then
        log_info "启动管理前端 (端口 8005)..."
        ./start_frontend.sh > logs/frontend.log 2>&1 &
        log_info "✅ 管理前端已在后台启动"
    fi
    
    sleep 5
    
    echo ""
    log_info "🎉 所有服务启动完成!"
    echo ""
    echo "🌐 服务访问地址："
    echo "   📱 用户前端客户端: http://localhost:8006"
    echo "   🔧 管理前端: http://localhost:8005"  
    echo "   🔗 后端API文档: http://localhost:3007/docs"
    echo "   🔗 后端API: http://localhost:3007"
    echo ""
    echo "🔑 数据库信息："
    echo "   📍 地址: 127.0.0.1:3306"
    echo "   👤 用户: root 或 admin"
    echo "   🔐 密码: Pp123456"
    echo ""
    echo "📝 查看日志："
    echo "   tail -f logs/backend.log    # 后端日志"
    echo "   tail -f logs/client.log     # 用户前端日志"  
    echo "   tail -f logs/frontend.log   # 管理前端日志"
    echo ""
    echo "🛑 停止服务："
    echo "   ./stop_all.sh               # 停止所有服务"
    echo ""
}

# 运行主函数
main
