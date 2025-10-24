#!/bin/bash
set -e

# ===== 数据库迁移脚本 =====
# 执行数据库版本迁移，支持升级和回滚

SERVER_IP="82.157.28.35"
SERVER_USER="ubuntu"
SERVER_PASSWORD="chen_188_8_8"
MIGRATIONS_DIR="./migrations"

echo "🔧 数据库迁移脚本"
echo "================================"
echo ""

# 检查参数
if [ -z "$1" ]; then
    echo "❌ 错误：需要指定迁移操作"
    echo ""
    echo "使用方式："
    echo "   ./db-migrate.sh <version> <action>"
    echo ""
    echo "参数说明："
    echo "   version  - 迁移版本号（如: 001, 002 等）或 'latest'（最新版本）"
    echo "   action   - 操作类型：upgrade（升级）或 downgrade（回滚）"
    echo ""
    echo "示例："
    echo "   ./db-migrate.sh 001 upgrade      ← 升级到版本 001"
    echo "   ./db-migrate.sh latest upgrade   ← 升级到最新版本"
    echo "   ./db-migrate.sh 002 downgrade    ← 回滚版本 002"
    echo ""
    echo "可用的迁移版本："
    ls -1 "${MIGRATIONS_DIR}"/*.py 2>/dev/null | grep -v TEMPLATE | sed 's|.*/||;s|\.py||' | sort
    echo ""
    exit 1
fi

VERSION="$1"
ACTION="${2:-upgrade}"

# 处理 latest 关键字
if [ "${VERSION}" = "latest" ]; then
    LATEST=$(ls -1 "${MIGRATIONS_DIR}"/*.py 2>/dev/null | grep -v TEMPLATE | sed 's|.*/||;s|\.py||' | sort | tail -1)
    if [ -z "$LATEST" ]; then
        echo "❌ 错误：找不到任何迁移版本"
        exit 1
    fi
    # 提取版本号部分（如：001_initial_schema -> 001）
    VERSION=$(echo "$LATEST" | cut -d_ -f1)
fi

# 验证版本格式
if ! [[ "$VERSION" =~ ^[0-9]{3}$ ]]; then
    echo "❌ 错误：版本号格式不正确（应为三位数字，如: 001）"
    exit 1
fi

# 查找迁移文件
MIGRATION_FILE=$(ls -1 "${MIGRATIONS_DIR}"/${VERSION}_*.py 2>/dev/null | head -1)

if [ -z "$MIGRATION_FILE" ]; then
    echo "❌ 错误：找不到迁移版本 ${VERSION}"
    echo ""
    echo "可用的迁移版本："
    ls -1 "${MIGRATIONS_DIR}"/*.py 2>/dev/null | grep -v TEMPLATE | sed 's|.*/||;s|\.py||' | sort
    exit 1
fi

MIGRATION_NAME=$(basename "$MIGRATION_FILE" .py)

# 验证操作类型
if [ "${ACTION}" != "upgrade" ] && [ "${ACTION}" != "downgrade" ]; then
    echo "❌ 错误：操作类型必须是 upgrade 或 downgrade"
    exit 1
fi

echo "📋 迁移配置："
echo "   - 版本: ${VERSION} (${MIGRATION_NAME})"
echo "   - 操作: ${ACTION}"
echo "   - 文件: ${MIGRATION_FILE}"
echo ""

# 确认操作
if [ "${ACTION}" = "downgrade" ]; then
    echo "⚠️  警告："
    echo "   - 这将回滚数据库版本！"
    echo "   - 可能会导致数据丢失！"
    echo "   - 请确保已备份数据库！"
    echo ""
    read -p "确认回滚? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ 已取消"
        exit 1
    fi
fi

# 上传迁移文件到服务器
echo ""
echo "📤 上传迁移文件到服务器..."
REMOTE_MIGRATION_DIR="/tmp/migrations"
sshpass -p "${SERVER_PASSWORD}" ssh -o StrictHostKeyChecking=no \
    ${SERVER_USER}@${SERVER_IP} "mkdir -p ${REMOTE_MIGRATION_DIR}"

sshpass -p "${SERVER_PASSWORD}" scp -o StrictHostKeyChecking=no \
    "${MIGRATION_FILE}" \
    ${SERVER_USER}@${SERVER_IP}:${REMOTE_MIGRATION_DIR}/

echo "   ✅ 上传完成"

# 在服务器上执行迁移
echo ""
echo "🔧 执行数据库迁移..."
sshpass -p "${SERVER_PASSWORD}" ssh -o StrictHostKeyChecking=no \
    ${SERVER_USER}@${SERVER_IP} << MIGRATE_SCRIPT

cd /opt/stock-analysis-system/backend

# 激活虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 错误：虚拟环境不存在"
    exit 1
fi
source venv/bin/activate

# 执行迁移
python3 ${REMOTE_MIGRATION_DIR}/${MIGRATION_NAME}.py ${ACTION}
RESULT=\$?

if [ \$RESULT -eq 0 ]; then
    echo ""
    echo "✅ 迁移执行成功"
else
    echo ""
    echo "❌ 迁移执行失败"
    exit 1
fi

MIGRATE_SCRIPT

if [ $? -ne 0 ]; then
    echo "❌ 迁移失败"
    exit 1
fi

echo ""
echo "✅ 数据库迁移完成！"
echo ""
echo "📝 迁移信息："
echo "   - 版本: ${VERSION}"
echo "   - 操作: ${ACTION}"
echo "   - 时间: $(date)"
echo ""
