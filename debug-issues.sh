#!/bin/bash

# 问题自动检测和修复脚本
source dev-ports.env 2>/dev/null || {
    echo "❌ 请先运行 ./dev-setup.sh 配置开发环境"
    exit 1
}

echo "🔍 开发环境问题自动检测"
echo "========================"

# 检查端口占用
check_ports() {
    echo "📡 检查端口状态..."
    
    for port in $BACKEND_PORT $CLIENT_PORT $FRONTEND_PORT; do
        if lsof -ti:$port &>/dev/null; then
            pid=$(lsof -ti:$port)
            process_name=$(ps -p $pid -o comm= 2>/dev/null || echo "未知进程")
            echo "  ⚠️  端口 $port 被占用 (PID: $pid, 进程: $process_name)"
        else
            echo "  ✅ 端口 $port 可用"
        fi
    done
}

# 检查数据库连接
check_database() {
    echo "🗄️ 检查数据库连接..."
    
    if [ -f "backend/.env" ]; then
        source backend/.env
        if mysql -h$DATABASE_HOST -u$DATABASE_USER -p$DATABASE_PASSWORD -e "USE $DATABASE_NAME; SELECT 1;" &>/dev/null; then
            echo "  ✅ 数据库连接正常"
        else
            echo "  ❌ 数据库连接失败"
            echo "  💡 建议: 运行 ./dev-setup.sh 重新配置数据库"
        fi
    else
        echo "  ❌ 环境配置文件不存在"
    fi
}

# 检查依赖
check_dependencies() {
    echo "📦 检查项目依赖..."
    
    # 检查后端依赖
    if [ -d "backend/venv" ]; then
        cd backend
        source venv/bin/activate
        if python -c "import fastapi, sqlalchemy, pymysql" 2>/dev/null; then
            echo "  ✅ 后端依赖完整"
        else
            echo "  ❌ 后端依赖缺失"
        fi
        cd ..
    else
        echo "  ❌ 后端虚拟环境不存在"
    fi
    
    # 检查前端依赖
    for dir in "client" "frontend"; do
        if [ -d "$dir/node_modules" ]; then
            echo "  ✅ $dir 依赖完整"
        else
            echo "  ❌ $dir 依赖缺失"
        fi
    done
}

# 检查服务状态
check_services() {
    echo "🚀 检查服务运行状态..."
    
    services=("$BACKEND_PORT:API服务" "$CLIENT_PORT:客户端" "$FRONTEND_PORT:管理端")
    
    for service in "${services[@]}"; do
        port=$(echo $service | cut -d: -f1)
        name=$(echo $service | cut -d: -f2)
        
        if curl -s "http://localhost:$port" &>/dev/null; then
            echo "  ✅ $name (端口 $port) 运行正常"
        else
            echo "  ❌ $name (端口 $port) 无响应"
        fi
    done
}

# 执行所有检查
check_ports
echo ""
check_database  
echo ""
check_dependencies
echo ""
check_services

echo ""
echo "🛠️ 快速修复建议:"
echo "  重新配置环境: ./dev-setup.sh"
echo "  启动所有服务: ./smart-start.sh"  
echo "  停止所有服务: ./smart-stop.sh"
