#!/bin/bash

# 固定端口启动脚本
echo "🚀 启动股票分析系统 (固定端口版)"
echo "================================="

# 加载固定端口配置
source fixed-ports.env

echo "📊 固定端口配置:"
echo "  - API服务: $BACKEND_PORT"  
echo "  - 客户端: $CLIENT_PORT"
echo "  - 管理端: $FRONTEND_PORT"
echo ""

# 端口冲突检查函数
check_and_handle_port() {
    local port=$1
    local service_name=$2
    
    if lsof -ti:$port &>/dev/null; then
        echo "⚠️  端口 $port ($service_name) 被占用，正在清理..."
        lsof -ti:$port | xargs kill -9 2>/dev/null
        sleep 1
    fi
}

# 检查并处理端口冲突
check_and_handle_port $BACKEND_PORT "API服务"
check_and_handle_port $CLIENT_PORT "客户端"  
check_and_handle_port $FRONTEND_PORT "管理端"

# 创建日志目录
mkdir -p logs

# 启动后端服务
echo "🔧 启动后端API服务..."
cd backend
source venv/bin/activate 2>/dev/null || {
    echo "创建虚拟环境..."
    python3 -m venv venv
    source venv/bin/activate
}
nohup python -m uvicorn app.main:app --reload --host 0.0.0.0 --port $BACKEND_PORT > ../logs/backend.log 2>&1 &
echo $! > ../logs/backend.pid
cd ..

# 启动客户端服务  
echo "🎨 启动客户端服务..."
cd client
nohup npm run dev > ../logs/client.log 2>&1 &
echo $! > ../logs/client.pid
cd ..

# 启动管理端服务
echo "🖥️ 启动管理端服务..."
cd frontend
nohup npm run dev > ../logs/frontend.log 2>&1 &  
echo $! > ../logs/frontend.pid
cd ..

echo ""
echo "✅ 所有服务启动完成！"
echo ""
echo "📊 访问地址:"
echo "  🔗 API文档:  http://localhost:$BACKEND_PORT/docs"
echo "  📱 客户端:   http://localhost:$CLIENT_PORT"  
echo "  🖥️ 管理端:   http://localhost:$FRONTEND_PORT"
echo ""
echo "🛑 停止服务: ./stop-fixed-ports.sh"