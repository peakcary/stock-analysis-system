#!/bin/bash

# 数据库备份脚本
set -e

# 加载环境变量
if [ -f ".env.prod" ]; then
    source .env.prod
else
    echo "❌ 错误: 未找到 .env.prod 文件"
    exit 1
fi

# 设置备份目录
BACKUP_DIR="database/backups"
DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="stock_analysis_backup_${DATE}.sql"

# 创建备份目录
mkdir -p $BACKUP_DIR

echo "🗃️ 开始备份数据库..."

# 执行数据库备份
docker exec stock_mysql_prod mysqldump \
    -u${MYSQL_USER} \
    -p${MYSQL_PASSWORD} \
    --routines \
    --triggers \
    --single-transaction \
    --lock-tables=false \
    ${MYSQL_DATABASE} > "${BACKUP_DIR}/${BACKUP_FILE}"

# 压缩备份文件
gzip "${BACKUP_DIR}/${BACKUP_FILE}"

echo "✅ 备份完成: ${BACKUP_DIR}/${BACKUP_FILE}.gz"

# 清理超过30天的旧备份
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "🧹 清理旧备份完成"