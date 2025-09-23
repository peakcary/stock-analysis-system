#!/bin/bash

# 股票分析系统 - 本地开发启动脚本 v2.7.0
echo "🚀 启动股票分析系统 (本地开发模式)"
echo "======================================"

# 端口配置
BACKEND_PORT=8000
FRONTEND_PORT=8007
CLIENT_PORT=8008

echo "📊 端口配置: API($BACKEND_PORT) | 管理端($FRONTEND_PORT) | 客户端($CLIENT_PORT)"

# 清理端口占用
clear_port() {
    local port=$1
    if lsof -ti:$port >/dev/null 2>&1; then
        echo "清理端口 $port..."
        lsof -ti:$port | xargs kill -9 2>/dev/null
        sleep 1
    fi
}

echo ""
echo "🧹 清理端口占用..."
clear_port $BACKEND_PORT
clear_port $FRONTEND_PORT
clear_port $CLIENT_PORT

# 创建日志目录
mkdir -p logs

echo ""
echo "🔄 启动服务..."

# 启动后端服务
echo "🔧 启动后端API服务..."
cd backend
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT --reload > ../logs/backend.log 2>&1 &
echo $! > ../logs/backend.pid
cd ..

# 启动前端管理系统
echo "🖥️ 启动前端管理系统..."
cd frontend
nohup npm run dev -- --port $FRONTEND_PORT > ../logs/frontend.log 2>&1 &
echo $! > ../logs/frontend.pid
cd ..

# 启动客户端应用
echo "📱 启动客户端应用..."
cd client
nohup npm run dev -- --port $CLIENT_PORT > ../logs/client.log 2>&1 &
echo $! > ../logs/client.pid
cd ..

echo ""
echo "⏳ 等待服务启动..."
sleep 8

# 检查服务状态
echo ""
echo "📋 服务状态检查:"
for port in $BACKEND_PORT $FRONTEND_PORT $CLIENT_PORT; do
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
echo "  🔗 后端API:    http://localhost:$BACKEND_PORT"
echo "  📖 API文档:    http://localhost:$BACKEND_PORT/docs"
echo "  🖥️ 管理端:    http://localhost:$FRONTEND_PORT"
echo "  📱 客户端:    http://localhost:$CLIENT_PORT"
echo ""
echo "👤 登录信息:"
echo "  管理员: admin / admin123"
echo "  测试用户: fullaccess_user / fullaccess123"
echo ""
echo "📝 查看日志: tail -f logs/[backend|frontend|client].log"
echo "🛑 停止服务: ./stop-dev.sh"
echo ""
echo "💡 个股查询功能: 客户端 → 个股查询标签页"