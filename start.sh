#!/bin/bash

# 股票分析系统 - 启动脚本 (最终版)
echo "🚀 启动股票分析系统"
echo "=================="

# 加载端口配置
if [ -f "ports.env" ]; then
    source ports.env
else
    echo "⚠️ 端口配置不存在，请先运行 ./deploy.sh"
    BACKEND_PORT=3007
    CLIENT_PORT=8005
    FRONTEND_PORT=8006
fi

echo "📊 端口: API($BACKEND_PORT) | 客户端($CLIENT_PORT) | 管理端($FRONTEND_PORT)"

# 清理端口占用
clear_port() {
    local port=$1
    if lsof -ti:$port >/dev/null 2>&1; then
        echo "清理端口 $port..."
        lsof -ti:$port | xargs kill -9 2>/dev/null
        sleep 1
    fi
}

clear_port $BACKEND_PORT
clear_port $CLIENT_PORT  
clear_port $FRONTEND_PORT

mkdir -p logs

echo ""
echo "启动服务..."

# 启动后端
echo "🔧 API服务..."
cd backend
source venv/bin/activate
nohup python -m uvicorn app.main:app --reload --host 0.0.0.0 --port $BACKEND_PORT > ../logs/backend.log 2>&1 &
echo $! > ../logs/backend.pid
cd ..

# 启动客户端
echo "📱 客户端..."
cd client
nohup npm run dev > ../logs/client.log 2>&1 &
echo $! > ../logs/client.pid
cd ..

# 启动管理端
echo "🖥️ 管理端..."
cd frontend
nohup npm run dev > ../logs/frontend.log 2>&1 &
echo $! > ../logs/frontend.pid
cd ..

echo ""
echo "⏳ 等待启动..."
sleep 5

# 检查服务
echo ""
echo "📋 服务状态:"
for port in $BACKEND_PORT $CLIENT_PORT $FRONTEND_PORT; do
    if lsof -ti:$port >/dev/null 2>&1; then
        echo "  ✅ 端口 $port 运行正常"
    else
        echo "  ❌ 端口 $port 启动失败"
    fi
done

echo ""
echo "🎉 启动完成！"
echo ""
echo "📊 访问地址:"
echo "  🔗 API文档: http://localhost:$BACKEND_PORT/docs"
echo "  📱 客户端:  http://localhost:$CLIENT_PORT"
echo "  🖥️ 管理端:  http://localhost:$FRONTEND_PORT"
echo ""
echo "👤 管理员: admin / admin123"
echo ""
echo "📝 日志: tail -f logs/[service].log"
echo "🛑 停止: ./stop.sh"