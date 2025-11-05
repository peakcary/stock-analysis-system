#!/bin/bash
set -e

# ===== 数据库恢复脚本 =====
# 从备份文件恢复生产环境数据库

SERVER_IP="82.157.28.35"
SERVER_USER="ubuntu"
SERVER_PASSWORD="chen_188_8_8"

echo "🔄 数据库恢复脚本"
echo "================================"
echo ""

# 检查参数
if [ -z "$1" ]; then
    echo "❌ 错误：需要指定备份文件"
    echo ""
    echo "使用方式："
    echo "   ./db-restore.sh <backup-file>"
    echo ""
    echo "示例："
    echo "   ./db-restore.sh ./db-backups/stock_analysis_prod_20251023_120000.sql"
    echo ""
    echo "查看可用备份："
    echo "   ls -lh ./db-backups/"
    exit 1
fi

BACKUP_FILE="$1"

# 验证备份文件
if [ ! -f "${BACKUP_FILE}" ]; then
    echo "❌ 错误：备份文件不存在"
    echo "   文件: ${BACKUP_FILE}"
    exit 1
fi

if [ ! -s "${BACKUP_FILE}" ]; then
    echo "❌ 错误：备份文件为空"
    exit 1
fi

BACKUP_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
BACKUP_NAME=$(basename "${BACKUP_FILE}")

echo "📋 恢复配置："
echo "   - 备份文件: ${BACKUP_FILE}"
echo "   - 文件大小: ${BACKUP_SIZE}"
echo "   - 数据库: stock_analysis_prod"
echo "   - 服务器: ${SERVER_IP}"
echo ""
echo "⚠️  警告："
echo "   - 这将覆盖当前数据库中的所有数据！"
echo "   - 请确保已备份重要数据！"
echo ""

# 确认
read -p "确认恢复? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ 已取消"
    exit 1
fi

# 二次确认
read -p "再次确认，这将覆盖所有数据 (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ 已取消"
    exit 1
fi

# 上传备份文件到服务器
echo ""
echo "📤 上传备份文件到服务器..."
REMOTE_BACKUP="/tmp/${BACKUP_NAME}"
sshpass -p "${SERVER_PASSWORD}" scp -o StrictHostKeyChecking=no \
    "${BACKUP_FILE}" \
    ${SERVER_USER}@${SERVER_IP}:${REMOTE_BACKUP}
echo "   ✅ 上传完成"

# 执行恢复
echo ""
echo "🔧 执行数据库恢复..."
sshpass -p "${SERVER_PASSWORD}" ssh -o StrictHostKeyChecking=no \
    ${SERVER_USER}@${SERVER_IP} << RESTORE_CMD

echo "   - 停止应用服务..."
sudo systemctl stop stock-api 2>/dev/null || true
sleep 2

echo "   - 删除旧数据库..."
mysql -u root -p'Pp123456' -e "DROP DATABASE IF EXISTS stock_analysis_prod;"

echo "   - 创建新数据库..."
mysql -u root -p'Pp123456' -e "CREATE DATABASE stock_analysis_prod DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

echo "   - 导入备份数据..."
mysql -u root -p'Pp123456' stock_analysis_prod < "${REMOTE_BACKUP}"

echo "   - 验证导入..."
TABLE_COUNT=\$(mysql -u root -p'Pp123456' stock_analysis_prod -e "SHOW TABLES;" | wc -l)
echo "   ✅ 导入完成 (\${TABLE_COUNT} 个表)"

echo "   - 启动应用服务..."
sudo systemctl start stock-api
sleep 4

echo "   - 验证服务..."
if curl -s http://127.0.0.1:3007/health > /dev/null 2>&1; then
    echo "   ✅ 服务运行正常"
else
    echo "   ❌ 服务启动异常"
    exit 1
fi

echo "   - 清理临时文件..."
rm -f "${REMOTE_BACKUP}"

RESTORE_CMD

echo ""
echo "✅ 恢复成功！"
echo ""
echo "📝 恢复信息："
echo "   - 备份文件: ${BACKUP_NAME}"
echo "   - 恢复时间: $(date)"
echo ""
echo "🧪 验证服务："
echo "   curl https://qwquant.com/api/v1/health"
echo ""
