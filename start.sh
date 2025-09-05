#!/bin/bash

# 股票分析系统 - 一键启动脚本
echo "🚀 启动股票分析系统"
echo "=================="

# 加载端口配置
if [ ! -f "ports.env" ]; then
    echo "❌ 端口配置文件不存在，请先运行 ./deploy.sh"
    exit 1
fi

source ports.env

echo "📊 端口配置: API($BACKEND_PORT) | 客户端($CLIENT_PORT) | 管理端($FRONTEND_PORT)"

# 端口占用处理
handle_port() {
    local port=$1
    local service=$2
    
    if lsof -ti:$port &>/dev/null; then
        echo "⚠️  端口 $port ($service) 被占用，正在清理..."
        lsof -ti:$port | xargs kill -9 2>/dev/null
        sleep 1
    fi
}

# 清理可能占用的端口
handle_port $BACKEND_PORT "API服务"
handle_port $CLIENT_PORT "客户端"
handle_port $FRONTEND_PORT "管理端"

# 创建日志目录
mkdir -p logs

echo ""
echo "🔧 启动后端API服务..."
cd backend
source venv/bin/activate
nohup python -m uvicorn app.main:app --reload --host 0.0.0.0 --port $BACKEND_PORT > ../logs/backend.log 2>&1 &
echo $! > ../logs/backend.pid
cd ..

echo "🎨 启动客户端服务..."
cd client
nohup npm run dev -- --port $CLIENT_PORT > ../logs/client.log 2>&1 &
echo $! > ../logs/client.pid
cd ..

echo "🖥️ 启动管理端服务..."
cd frontend
nohup npm run dev -- --port $FRONTEND_PORT > ../logs/frontend.log 2>&1 &
echo $! > ../logs/frontend.pid
cd ..

echo ""
echo "⏳ 等待服务启动..."
sleep 8

# 检查服务状态
echo ""
echo "📋 服务状态检查:"

check_service() {
    local port=$1
    local name=$2
    local url=$3
    
    if lsof -ti:$port &>/dev/null; then
        if curl -s "$url" &>/dev/null; then
            echo "  ✅ $name (端口 $port) - 运行正常"
        else
            echo "  ⚠️  $name (端口 $port) - 正在启动中..."
        fi
    else
        echo "  ❌ $name (端口 $port) - 启动失败"
    fi
}

check_service $BACKEND_PORT "API服务" "http://localhost:$BACKEND_PORT/"
check_service $CLIENT_PORT "客户端" "http://localhost:$CLIENT_PORT/"
check_service $FRONTEND_PORT "管理端" "http://localhost:$FRONTEND_PORT/"

echo ""
echo "🎉 系统启动完成！"
echo ""
echo "📊 访问地址:"
echo "  🔗 API文档:  http://localhost:$BACKEND_PORT/docs"
echo "  📱 客户端:   http://localhost:$CLIENT_PORT"
echo "  🖥️ 管理端:   http://localhost:$FRONTEND_PORT"
echo ""
echo "📝 日志文件:"
echo "  - API服务: tail -f logs/backend.log"
echo "  - 客户端: tail -f logs/client.log"
echo "  - 管理端: tail -f logs/frontend.log"
echo ""
echo "🛑 停止系统: ./stop.sh"