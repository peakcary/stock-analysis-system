#!/bin/bash
set -e

# ===== 配置 =====
SERVER_IP="82.157.28.35"
SERVER_USER="ubuntu"
SERVER_PASSWORD="chen_188_8_8"

echo "🔄 开始回滚..."
echo ""

# 连接服务器执行回滚
sshpass -p "${SERVER_PASSWORD}" ssh -o StrictHostKeyChecking=no \
    ${SERVER_USER}@${SERVER_IP} << 'ROLLBACK_SCRIPT'

cd /opt/stock-analysis-system

# 停止服务
echo "   - 停止服务..."
sudo systemctl stop stock-api 2>/dev/null || true
sleep 1

# 删除当前版本
echo "   - 删除当前版本..."
sudo rm -rf backend

# 恢复备份
echo "   - 恢复备份版本..."
sudo mv backend_backup backend

# 设置权限
sudo chown -R ubuntu:ubuntu backend

# 重启服务
echo "   - 重启服务..."
sudo systemctl start stock-api
sleep 3

# 验证
if curl -s http://127.0.0.1:3007/health > /dev/null 2>&1; then
    echo "   ✅ 回滚成功，服务已恢复"
else
    echo "   ❌ 回滚失败，服务未正常启动"
    exit 1
fi

ROLLBACK_SCRIPT

echo ""
echo "✅ 回滚完成！"
echo ""
echo "🧪 测试访问:"
echo "   curl https://qwquant.com/api/v1/health"
echo ""
