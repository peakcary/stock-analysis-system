#!/bin/bash

# 智能启动脚本 - 自动使用配置的端口
source dev-ports.env

echo "🚀 启动股票分析系统 (智能配置版)"
echo "================================"
echo "📊 端口配置:"
echo "  - API服务: $BACKEND_PORT"
echo "  - 客户端: $CLIENT_PORT" 
echo "  - 管理端: $FRONTEND_PORT"
echo ""

# 创建日志目录
mkdir -p logs

# 启动后端服务
echo "🔧 启动后端API服务..."
cd backend
source venv/bin/activate
nohup python -m uvicorn app.main:app --reload --host 0.0.0.0 --port $BACKEND_PORT > ../logs/backend.log 2>&1 &
echo $! > ../logs/backend.pid
cd ..

# 启动前端服务
echo "🎨 启动前端服务..."
cd client
nohup npm run dev > ../logs/client.log 2>&1 &
echo $! > ../logs/client.pid
cd ..

# 启动管理端
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
echo "🛑 停止服务: ./smart-stop.sh"
