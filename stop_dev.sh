#!/bin/bash
# 停止开发环境脚本
# Stop Development Environment Script

set -e

echo "🛑 停止股票分析系统开发环境..."

# 停止服务进程
stop_services() {
    echo "🔍 查找运行中的服务..."
    
    # 停止后端服务
    if lsof -i :8000 &>/dev/null; then
        echo "🐍 停止后端服务..."
        pkill -f "uvicorn.*8000" || true
        echo "✅ 后端服务已停止"
    else
        echo "ℹ️ 后端服务未运行"
    fi
    
    # 停止前端服务
    if lsof -i :3000 &>/dev/null; then
        echo "⚛️ 停止前端服务..."
        pkill -f "vite.*3000" || true
        pkill -f "npm.*dev" || true
        echo "✅ 前端服务已停止"
    else
        echo "ℹ️ 前端服务未运行"
    fi
    
    # 清理进程ID文件
    if [ -f ".dev_pids" ]; then
        rm .dev_pids
    fi
}

# 显示端口状态
show_port_status() {
    echo ""
    echo "📊 端口状态检查:"
    
    if lsof -i :8000 &>/dev/null; then
        echo "   ⚠️ 端口 8000: 仍被占用"
    else
        echo "   ✅ 端口 8000: 已释放"
    fi
    
    if lsof -i :3000 &>/dev/null; then
        echo "   ⚠️ 端口 3000: 仍被占用"
    else
        echo "   ✅ 端口 3000: 已释放"
    fi
}

# 清理临时文件
cleanup() {
    echo "🧹 清理临时文件..."
    
    # 清理日志文件 (保留最新的)
    if [ -d "logs" ]; then
        find logs -name "*.log" -mtime +7 -delete 2>/dev/null || true
    fi
    
    # 清理上传文件的临时文件
    if [ -d "backend/uploads/temp" ]; then
        rm -rf backend/uploads/temp/* 2>/dev/null || true
    fi
    
    echo "✅ 临时文件清理完成"
}

# 主函数
main() {
    stop_services
    show_port_status
    cleanup
    
    echo ""
    echo "🎉 开发环境已完全停止！"
    echo ""
    echo "💡 重新启动:"
    echo "   ./start_dev.sh      # 一键启动开发环境"
    echo "   ./start_backend.sh  # 仅启动后端"
    echo "   ./start_frontend.sh # 仅启动前端"
}

# 显示帮助
if [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
    echo "停止开发环境脚本使用说明："
    echo ""
    echo "功能："
    echo "- 停止后端服务 (端口 8000)"
    echo "- 停止前端服务 (端口 3000)"
    echo "- 清理临时文件"
    echo "- 显示端口释放状态"
    echo ""
    echo "使用方法："
    echo "./stop_dev.sh"
    exit 0
fi

main