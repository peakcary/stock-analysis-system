#!/bin/bash

# 股票分析系统 - 重启脚本 v2.7.3
echo "🔄 重启股票分析系统"
echo "==================="
echo ""

# 停止服务
echo "🛑 停止服务..."
bash stop.sh

echo ""

# 启动服务
echo "🚀 启动服务..."
bash start.sh
