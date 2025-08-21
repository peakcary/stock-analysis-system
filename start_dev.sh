#!/bin/bash
# 开发环境一键启动脚本
# Development Environment Quick Start Script

set -e

echo "🚀 股票分析系统开发环境启动"
echo "========================================"

# 检查项目目录
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ 请在项目根目录执行此脚本"
    exit 1
fi

# 检查环境
check_environment() {
    echo "🔍 检查开发环境..."
    
    # 检查 MySQL
    if ! mysql -u root -proot123 -e "SELECT 1;" &>/dev/null; then
        echo "❌ MySQL 连接失败"
        echo "💡 请确保 MySQL 已启动且密码为 root123"
        echo "   macOS: brew services start mysql@8.0"
        echo "   Linux: sudo systemctl start mysql"
        return 1
    fi
    
    # 检查数据库
    if ! mysql -u root -proot123 -e "USE stock_analysis; SELECT 1;" &>/dev/null; then
        echo "❌ stock_analysis 数据库不存在"
        echo "💡 请运行: ./setup_database.sh"
        return 1
    fi
    
    # 检查后端环境
    if [ ! -f "backend/venv/bin/activate" ]; then
        echo "❌ 后端 Python 环境未设置"
        echo "💡 请运行: ./setup_environment.sh"
        return 1
    fi
    
    # 检查前端环境
    if [ ! -d "frontend/node_modules" ]; then
        echo "❌ 前端依赖未安装"
        echo "💡 请运行: cd frontend && npm install"
        return 1
    fi
    
    echo "✅ 环境检查通过"
    return 0
}

# 启动后端服务 (后台运行)
start_backend() {
    echo "🐍 启动后端服务..."
    
    cd backend
    source venv/bin/activate
    
    # 检查端口占用
    if lsof -i :8000 &>/dev/null; then
        echo "⚠️ 端口 8000 已被占用，尝试关闭..."
        pkill -f "uvicorn.*8000" || true
        sleep 2
    fi
    
    # 后台启动
    nohup uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
    BACKEND_PID=$!
    
    cd ..
    
    # 等待服务启动
    echo "⏳ 等待后端服务启动..."
    for i in {1..10}; do
        if curl -s http://localhost:8000/health &>/dev/null; then
            echo "✅ 后端服务启动成功 (PID: $BACKEND_PID)"
            break
        fi
        sleep 1
    done
}

# 启动前端服务 (后台运行)
start_frontend() {
    echo "⚛️ 启动前端服务..."
    
    cd frontend
    
    # 检查端口占用
    if lsof -i :3000 &>/dev/null; then
        echo "⚠️ 端口 3000 已被占用，尝试关闭..."
        pkill -f "vite.*3000" || true
        sleep 2
    fi
    
    # 后台启动
    nohup npm run dev > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    
    cd ..
    
    echo "✅ 前端服务启动成功 (PID: $FRONTEND_PID)"
}

# 显示状态
show_status() {
    echo ""
    echo "🎉 开发环境启动完成！"
    echo "========================================"
    echo "🌐 访问地址:"
    echo "   前端应用: http://localhost:3000"
    echo "   后端API:  http://localhost:8000"
    echo "   API文档:  http://localhost:8000/docs"
    echo ""
    echo "📊 服务状态:"
    
    # 检查后端状态
    if curl -s http://localhost:8000/health &>/dev/null; then
        echo "   ✅ 后端服务: 运行中"
    else
        echo "   ❌ 后端服务: 未运行"
    fi
    
    # 检查前端状态
    if lsof -i :3000 &>/dev/null; then
        echo "   ✅ 前端服务: 运行中"
    else
        echo "   ❌ 前端服务: 未运行"
    fi
    
    echo ""
    echo "📝 开发工具:"
    echo "   查看后端日志: tail -f logs/backend.log"
    echo "   查看前端日志: tail -f logs/frontend.log"
    echo "   数据库连接: mysql -u root -proot123 stock_analysis"
    echo ""
    echo "🛑 停止服务: ./stop_dev.sh"
}

# 创建日志目录
mkdir -p logs

# 主函数
main() {
    if check_environment; then
        start_backend
        start_frontend
        show_status
        
        # 保存进程ID
        echo "BACKEND_PID=$BACKEND_PID" > .dev_pids
        echo "FRONTEND_PID=$FRONTEND_PID" >> .dev_pids
        
    else
        echo ""
        echo "❌ 环境检查失败，请先完成环境设置"
        echo "💡 运行以下命令完成设置:"
        echo "   ./setup_environment.sh   # 安装基础环境"
        echo "   ./setup_database.sh      # 初始化数据库"
        exit 1
    fi
}

# 显示帮助
if [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
    echo "开发环境启动脚本使用说明："
    echo ""
    echo "功能："
    echo "- 检查开发环境完整性"
    echo "- 后台启动后端服务 (端口 8000)"
    echo "- 后台启动前端服务 (端口 3000)"
    echo "- 显示服务状态和访问地址"
    echo ""
    echo "使用方法："
    echo "./start_dev.sh"
    echo ""
    echo "停止服务："
    echo "./stop_dev.sh"
    exit 0
fi

main