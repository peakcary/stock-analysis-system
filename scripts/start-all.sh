#!/bin/bash

# 一键启动所有服务脚本
# Start All Services Script

set -e

echo "🚀 一键启动股票分析系统..."

# 检查是否在项目根目录
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ 错误: 请在项目根目录下运行此脚本"
    exit 1
fi

# 检查系统依赖
check_dependencies() {
    echo "🔍 检查系统依赖..."
    
    # 检查MySQL
    if ! mysql -u root -pPp123456 -e "SELECT 1;" >/dev/null 2>&1; then
        echo "❌ MySQL连接失败，请确保MySQL服务运行且密码为 Pp123456"
        return 1
    fi
    
    # 检查Python环境
    if [ ! -d "backend/venv" ]; then
        echo "❌ Python虚拟环境未设置，请先运行 ./scripts/setup-local.sh"
        return 1
    fi
    
    # 检查Node.js依赖
    if [ ! -d "frontend/node_modules" ]; then
        echo "❌ 前端依赖未安装，请先运行 ./scripts/setup-local.sh"
        return 1
    fi
    
    echo "✅ 系统依赖检查通过"
    return 0
}

# 启动后端服务
start_backend() {
    echo "🐍 启动后端服务..."
    cd backend
    source venv/bin/activate
    # 安全地加载环境变量
    set -a  # 自动导出变量
    source ../.env
    set +a  # 关闭自动导出
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level info &
    BACKEND_PID=$!
    cd ..
    echo "✅ 后端服务已启动 (PID: $BACKEND_PID)"
}

# 启动前端服务
start_frontend() {
    echo "⚛️  启动前端服务..."
    cd frontend
    export REACT_APP_API_URL=http://localhost:8000/api/v1
    export REACT_APP_ENVIRONMENT=development
    export PORT=3000
    npm start &
    FRONTEND_PID=$!
    cd ..
    echo "✅ 前端服务已启动 (PID: $FRONTEND_PID)"
}

# 等待服务启动
wait_for_services() {
    echo "⏳ 等待服务启动..."
    
    # 等待后端
    echo "🔄 等待后端服务 (http://localhost:8000)..."
    timeout 60s bash -c 'until curl -s http://localhost:8000/health >/dev/null; do sleep 2; done' || {
        echo "⚠️  后端服务启动超时，但会继续等待..."
    }
    
    # 等待前端
    echo "🔄 等待前端服务 (http://localhost:3000)..."
    sleep 10  # 前端通常需要更长时间编译
    
    echo "✅ 服务启动完成！"
}

# 显示服务信息
show_info() {
    echo ""
    echo "🎉 股票分析系统已启动！"
    echo ""
    echo "📋 服务信息："
    echo "├─ 🌐 前端应用: http://localhost:3000"
    echo "├─ 🔗 后端API: http://localhost:8000"
    echo "├─ 📚 API文档: http://localhost:8000/docs"
    echo "└─ ❤️  健康检查: http://localhost:8000/health"
    echo ""
    echo "💾 数据库信息："
    echo "├─ 数据库名: stock_analysis_dev"
    echo "├─ 用户名: root"
    echo "└─ 密码: Pp123456"
    echo ""
    echo "🛑 停止所有服务: Ctrl+C 或运行 ./scripts/stop-all.sh"
    echo ""
}

# 清理函数
cleanup() {
    echo ""
    echo "🛑 正在停止所有服务..."
    
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        echo "✅ 后端服务已停止"
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        echo "✅ 前端服务已停止"
    fi
    
    # 清理可能的遗留进程
    pkill -f "uvicorn app.main:app" 2>/dev/null || true
    pkill -f "react-scripts start" 2>/dev/null || true
    
    echo "👋 服务已全部停止，再见！"
    exit 0
}

# 设置信号处理
trap cleanup SIGINT SIGTERM

# 主流程
main() {
    # 检查依赖
    if ! check_dependencies; then
        echo ""
        echo "💡 提示: 请先运行以下命令设置环境："
        echo "   ./scripts/setup-local.sh"
        exit 1
    fi
    
    # 启动服务
    start_backend
    sleep 3  # 让后端先启动
    start_frontend
    
    # 等待服务就绪
    wait_for_services
    
    # 显示信息
    show_info
    
    # 保持脚本运行
    echo "💤 服务运行中，按 Ctrl+C 停止..."
    wait
}

# 运行主流程
main