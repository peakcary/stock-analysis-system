#!/bin/bash

set -euo pipefail

# 股票分析系统 - 本地开发启动脚本 v2.7.0
echo "🚀 启动股票分析系统 (本地开发模式)"
echo "======================================"

usage() {
  cat <<USAGE
用法:
  ./start-dev.sh [all|backend|frontend|client] [--skip-install]

说明:
  - 默认 all：依次启动后端、管理端、客户端
  - backend/frontend/client：只启动对应服务
  - --skip-install：跳过 node_modules 检查与安装
USAGE
}

# 端口配置 - 与生产环境保持一致
BACKEND_PORT=3007
FRONTEND_PORT=8006
CLIENT_PORT=8005

TARGET=${1:-all}
SKIP_INSTALL=false
if [[ $# -ge 2 ]]; then
  if [[ "$2" == "--skip-install" ]]; then SKIP_INSTALL=true; fi
fi

echo "📊 端口配置: API($BACKEND_PORT) | 管理端($FRONTEND_PORT) | 客户端($CLIENT_PORT)"

# 优先通过PID文件优雅停止；必要时再清理端口
stop_if_running() {
    local name=$1
    local port=$2
    local pid_file="logs/${name}.pid"
    if [ -f "$pid_file" ]; then
        local pid
        pid=$(cat "$pid_file" || true)
        if [ -n "${pid:-}" ] && kill -0 "$pid" 2>/dev/null; then
            echo "停止 ${name} (PID: $pid)..."
            kill -TERM "$pid" 2>/dev/null || true
            for _ in {1..20}; do
                if kill -0 "$pid" 2>/dev/null; then sleep 0.2; else break; fi
            done
        fi
        rm -f "$pid_file"
    fi

    # 兜底：端口仍被占用则清理（可能是上次异常残留）
    if lsof -ti:$port >/dev/null 2>&1; then
        echo "清理端口 $port..."
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
}

# 等待端口开放（用于数据库等依赖）
wait_for_port() {
    local host=$1
    local port=$2
    local timeout=${3:-20}
    echo "等待 ${host}:${port} 可用 (timeout=${timeout}s)..."
    for _ in $(seq 1 $timeout); do
        if nc -z "$host" "$port" >/dev/null 2>&1; then
            echo "依赖 ${host}:${port} 已就绪"
            return 0
        fi
        sleep 1
    done
    echo "⚠️ 等待 ${host}:${port} 超时，继续尝试启动（若后端连不上DB请检查配置）"
    return 0
}

echo ""
echo "🧹 停止可能已运行的服务并清理端口..."
case "$TARGET" in
  all)
    stop_if_running backend $BACKEND_PORT
    stop_if_running frontend $FRONTEND_PORT
    stop_if_running client $CLIENT_PORT
    ;;
  backend)
    stop_if_running backend $BACKEND_PORT ;;
  frontend)
    stop_if_running frontend $FRONTEND_PORT ;;
  client)
    stop_if_running client $CLIENT_PORT ;;
  -h|--help|help)
    usage; exit 0 ;;
  *)
    echo "未知参数: $TARGET"; usage; exit 1 ;;
esac

# 创建日志目录
mkdir -p logs

echo ""
echo "🔄 启动服务..."

# 可选：数据库就绪检查（仅当目标是本机3306时）
DB_URL=${DATABASE_URL:-}
if [ -z "$DB_URL" ] && [ -f backend/.env ]; then
    # 从后端env抓取DATABASE_URL（简单解析，不处理复杂情况）
    DB_URL=$(grep -E '^DATABASE_URL=' backend/.env | sed -E 's/^DATABASE_URL=//') || true
fi
if echo "$DB_URL" | grep -qE '^mysql\+pymysql://'; then
    DB_HOST=$(echo "$DB_URL" | sed -E 's@^mysql\+pymysql://[^@]+@([^:/]+).*@\1@' -e 's/.*@([^:/]+).*/\1/' || true)
    DB_PORT=$(echo "$DB_URL" | sed -E 's@.*:([0-9]+)/.*@\1@' || echo 3306)
    if [ "$DB_HOST" = "127.0.0.1" ] || [ "$DB_HOST" = "localhost" ]; then
        command -v nc >/dev/null 2>&1 && wait_for_port "$DB_HOST" "${DB_PORT:-3306}" 20 || true
    fi
fi

ensure_node_modules() {
  local dir=$1
  if $SKIP_INSTALL; then return 0; fi
  if [ ! -d "$dir/node_modules" ]; then
    echo "📦 首次安装依赖: $dir"
    (cd "$dir" && npm ci)
  fi
}

start_backend() {
  echo "🔧 启动后端API服务..."
  (cd backend && nohup python -m uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT --reload > ../logs/backend.log 2>&1 & echo $! > ../logs/backend.pid)
}

start_frontend() {
  echo "🖥️ 启动前端管理系统..."
  ensure_node_modules frontend
  (cd frontend && nohup npm run dev -- --port $FRONTEND_PORT > ../logs/frontend.log 2>&1 & echo $! > ../logs/frontend.pid)
}

start_client() {
  echo "📱 启动客户端应用..."
  ensure_node_modules client
  (cd client && nohup npm run dev -- --port $CLIENT_PORT > ../logs/client.log 2>&1 & echo $! > ../logs/client.pid)
}

case "$TARGET" in
  all)
    start_backend; start_frontend; start_client ;;
  backend)
    start_backend ;;
  frontend)
    start_frontend ;;
  client)
    start_client ;;
esac

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
