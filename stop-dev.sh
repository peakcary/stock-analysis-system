#!/bin/bash

set -euo pipefail

# 股票分析系统 - 本地开发停止脚本 v2.7.1
echo "🛑 停止股票分析系统"
echo "==================="

# 端口配置（与 start-dev.sh 保持一致，便于本地一键启停）
BACKEND_PORT=3007
FRONTEND_PORT=8006
CLIENT_PORT=8005

usage() {
  cat <<USAGE
用法:
  ./stop-dev.sh [all|backend|frontend|client]

说明:
  - 默认 all，停止三个服务；也可只停某一项
USAGE
}

TARGET=${1:-all}

stop_one() {
  local service_name=$1
  local port=$2
  local pid_file="logs/${service_name}.pid"

  if [ -f "$pid_file" ]; then
    local pid
    pid=$(cat "$pid_file" || true)
    if [ -n "${pid:-}" ] && kill -0 "$pid" 2>/dev/null; then
      echo "停止 $service_name (PID: $pid)..."
      kill -TERM "$pid" 2>/dev/null || true
      for _ in {1..20}; do
        if kill -0 "$pid" 2>/dev/null; then sleep 0.2; else break; fi
      done
    fi
    rm -f "$pid_file"
  fi

  # 兜底：端口仍被占用则清理（可能是异常残留）
  if lsof -ti:$port >/dev/null 2>&1; then
    echo "强制清理端口 $port..."
    lsof -ti:$port | xargs kill -9 2>/dev/null || true
  fi
}

echo "🔄 停止服务..."
case "$TARGET" in
  all)
    stop_one backend $BACKEND_PORT
    stop_one frontend $FRONTEND_PORT
    stop_one client $CLIENT_PORT
    ;;
  backend)
    stop_one backend $BACKEND_PORT
    ;;
  frontend)
    stop_one frontend $FRONTEND_PORT
    ;;
  client)
    stop_one client $CLIENT_PORT
    ;;
  -h|--help|help)
    usage; exit 0 ;;
  *)
    echo "未知参数: $TARGET"; usage; exit 1 ;;
esac

echo ""
echo "⏳ 等待进程清理..."
sleep 1

echo "📋 端口状态检查:"
for port in $BACKEND_PORT $FRONTEND_PORT $CLIENT_PORT; do
  if lsof -ti:$port >/dev/null 2>&1; then
    echo "  ⚠️ 端口 $port 仍在运行"
  else
    echo "  ✅ 端口 $port 已停止"
  fi
done

echo ""
echo "✅ 停止完成！"
echo "📝 日志文件在 logs/ 目录"
echo "🚀 重新启动: ./start-dev.sh [all|backend|frontend|client]"
