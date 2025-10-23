#!/bin/bash

# ===== 配置 =====
SERVER_IP="82.157.28.35"
SERVER_USER="ubuntu"
SERVER_PASSWORD="chen_188_8_8"

echo "🔍 检查服务状态..."
echo ""

# 检查服务状态
echo "📋 服务运行状态："
sshpass -p "${SERVER_PASSWORD}" ssh -o StrictHostKeyChecking=no \
    ${SERVER_USER}@${SERVER_IP} "sudo systemctl status stock-api --no-pager | head -10"

echo ""
echo "🏥 健康检查："
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" https://qwquant.com/api/v1/health -k)
if [ "$HEALTH" = "200" ]; then
    echo "   ✅ API健康状态: 200 OK"
else
    echo "   ❌ API健康状态: $HEALTH"
fi

echo ""
echo "📊 最近的服务日志 (最后10行)："
sshpass -p "${SERVER_PASSWORD}" ssh -o StrictHostKeyChecking=no \
    ${SERVER_USER}@${SERVER_IP} "sudo journalctl -u stock-api -n 10 --no-pager"

echo ""
echo "💾 备份文件检查："
sshpass -p "${SERVER_PASSWORD}" ssh -o StrictHostKeyChecking=no \
    ${SERVER_USER}@${SERVER_IP} "ls -lh /opt/stock-analysis-system/ | grep -E '^d.*backend'"

echo ""
