#!/bin/bash

# 股票分析系统 - 重启服务脚本
echo "🔄 重启股票分析系统"
echo "===================="
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 停止服务
echo "第一步: 停止现有服务..."
bash "$SCRIPT_DIR/stop.sh"

echo ""
echo "等待 3 秒..."
sleep 3

echo ""
echo "第二步: 启动服务..."
bash "$SCRIPT_DIR/start.sh"
