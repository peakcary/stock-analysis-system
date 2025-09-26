#!/bin/bash

# 股票分析系统 - 本地开发启动脚本 v2.7.0
echo "🚀 启动股票分析系统 (本地开发模式)"
echo "======================================"

# 端口配置 - 与生产环境保持一致
BACKEND_PORT=3007
FRONTEND_PORT=8006
CLIENT_PORT=8005

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
echo "💰 支付功能:"
echo "  支付API: http://localhost:$BACKEND_PORT/api/v1/payment/"
echo "  支付配置: 开发模式(模拟支付)"
echo "  会员套餐: 支持多种套餐和微信支付"
echo ""
echo "📊 数据导入:"
echo "  支持格式: TXT、TTX、EEE等多种文件类型"
echo "  导入API: http://localhost:$BACKEND_PORT/api/v1/universal-import/"
echo ""
echo "📝 查看日志: tail -f logs/[backend|frontend|client].log"
echo "🛑 停止服务: ./stop-dev.sh"
echo ""
echo "💡 功能亮点:"
echo "  • 个股查询: 客户端 → 个股查询标签页"
echo "  • 支付管理: 完整的会员和支付系统"
echo "  • 数据分析: 多维度股票概念分析"