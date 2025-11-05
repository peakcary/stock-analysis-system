#!/bin/bash
set -e

# ===== 数据库备份脚本 =====
# 备份生产环境数据库到本地和服务器

SERVER_IP="82.157.28.35"
SERVER_USER="ubuntu"
SERVER_PASSWORD="chen_188_8_8"
BACKUP_DIR="./db-backups"

echo "💾 数据库备份脚本"
echo "================================"
echo ""

# 创建本地备份目录
mkdir -p "${BACKUP_DIR}"

# 生成备份文件名
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="stock_analysis_prod_${TIMESTAMP}.sql"
LOCAL_BACKUP="${BACKUP_DIR}/${BACKUP_FILE}"
REMOTE_BACKUP="/tmp/${BACKUP_FILE}"

echo "📋 备份配置："
echo "   - 数据库: stock_analysis_prod"
echo "   - 服务器: ${SERVER_IP}"
echo "   - 本地路径: ${LOCAL_BACKUP}"
echo "   - 时间戳: ${TIMESTAMP}"
echo ""

# 确认
read -p "确认备份数据库? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ 已取消"
    exit 1
fi

# 在服务器上创建备份
echo ""
echo "🔧 在服务器上创建备份..."
sshpass -p "${SERVER_PASSWORD}" ssh -o StrictHostKeyChecking=no \
    ${SERVER_USER}@${SERVER_IP} << REMOTE_BACKUP_CMD

echo "   - 导出数据库..."
mysqldump -u root -p'Pp123456' stock_analysis_prod > "${REMOTE_BACKUP}"

SIZE=\$(du -h "${REMOTE_BACKUP}" | cut -f1)
echo "   ✅ 备份完成 (\${SIZE})"

REMOTE_BACKUP_CMD

# 下载到本地
echo ""
echo "📥 下载备份到本地..."
sshpass -p "${SERVER_PASSWORD}" scp -o StrictHostKeyChecking=no \
    ${SERVER_USER}@${SERVER_IP}:${REMOTE_BACKUP} \
    ${LOCAL_BACKUP}

LOCAL_SIZE=$(du -h "${LOCAL_BACKUP}" | cut -f1)
echo "   ✅ 下载完成 (${LOCAL_SIZE})"

# 验证备份
echo ""
echo "✅ 验证备份文件..."
if [ -f "${LOCAL_BACKUP}" ] && [ -s "${LOCAL_BACKUP}" ]; then
    echo "   ✅ 备份文件有效"
    echo ""
    echo "✅ 备份成功！"
    echo ""
    echo "📝 备份详情："
    echo "   - 文件: ${LOCAL_BACKUP}"
    echo "   - 大小: ${LOCAL_SIZE}"
    echo "   - 行数: $(wc -l < "${LOCAL_BACKUP}") 行"
    echo ""
    echo "🔄 恢复方式："
    echo "   ./db-restore.sh ${LOCAL_BACKUP}"
else
    echo "   ❌ 备份文件无效"
    exit 1
fi

# 清理服务器上的备份文件（可选）
read -p "清理服务器上的备份文件? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sshpass -p "${SERVER_PASSWORD}" ssh -o StrictHostKeyChecking=no \
        ${SERVER_USER}@${SERVER_IP} "rm -f ${REMOTE_BACKUP} && echo '✅ 已清理'"
fi

echo ""
