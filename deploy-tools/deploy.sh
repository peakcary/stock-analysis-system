#!/bin/bash
set -e

# ===== 配置 =====
# ⚠️  重要：修改下面这个路径为你的实际项目路径
PROJECT_PATH="/Users/peakom/work/stock-analysis-system/backend"
DEPLOY_TOOLS_PATH="/Users/peakom/work/stock-analysis-system/deploy-tools"

SERVER_IP="82.157.28.35"
SERVER_USER="ubuntu"
SERVER_PASSWORD="chen_188_8_8"

# ===== 本地执行 =====
echo "🚀 开始部署..."
echo ""

# 读取当前 VERSION 文件中的数据库版本
if [ -f "${DEPLOY_TOOLS_PATH}/VERSION" ]; then
    CURRENT_DB_VERSION=$(grep "^DB_VERSION=" "${DEPLOY_TOOLS_PATH}/VERSION" | cut -d= -f2)
else
    CURRENT_DB_VERSION="001_initial_schema"
fi

echo "📋 版本信息："
echo "   - 当前数据库版本: ${CURRENT_DB_VERSION}"
echo ""

# 打包
echo "1️⃣  打包代码..."
cd ${PROJECT_PATH}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
PACKAGE="backend_${TIMESTAMP}.tar.gz"

echo "   清理虚拟环境和缓存..."
rm -rf venv __pycache__ .venv
find . -type d -name "__pycache__" -delete 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

cd ..
echo "   压缩代码..."
if tar -czf ${PACKAGE} \
    --exclude='backend/venv' \
    --exclude='backend/.git' \
    --exclude='backend/__pycache__' \
    backend/; then
    SIZE=$(du -h ${PACKAGE} | cut -f1)
    echo "   ✅ 打包完成: ${PACKAGE} (${SIZE})"
else
    echo "   ❌ 打包失败"
    exit 1
fi

# 上传
echo ""
echo "2️⃣  上传到服务器..."
sshpass -p "${SERVER_PASSWORD}" scp -o StrictHostKeyChecking=no \
    ${PACKAGE} \
    ${SERVER_USER}@${SERVER_IP}:/tmp/
echo "   ✅ 上传完成"

# 部署
echo ""
echo "3️⃣  服务器部署中..."
sshpass -p "${SERVER_PASSWORD}" ssh -o StrictHostKeyChecking=no \
    ${SERVER_USER}@${SERVER_IP} << 'DEPLOY_SCRIPT'

cd /opt/stock-analysis-system

# 停止服务
echo "   - 停止服务..."
sudo systemctl stop stock-api 2>/dev/null || true
sleep 1

# 备份
echo "   - 备份当前代码..."
sudo rm -rf backend_backup 2>/dev/null || true
sudo mv backend backend_backup 2>/dev/null || true

# 解压
echo "   - 解压新代码..."
mkdir -p backend
cd backend
TARFILE=\$(ls -t /tmp/backend_*.tar.gz 2>/dev/null | head -1)
if [ -z "\$TARFILE" ]; then
    echo "❌ 错误: 找不到tar.gz文件"
    exit 1
fi
tar --strip-components=1 -xzf "\$TARFILE"

# 权限
sudo chown -R ubuntu:ubuntu .

# 依赖
echo "   - 安装依赖..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip setuptools wheel > /dev/null 2>&1
pip install -r requirements.txt

# 检查是否需要数据库迁移
echo "   - 检查数据库版本..."
# 这里可以通过检查代码中的版本标记来决定是否需要迁移
# 如果新代码要求新的数据库版本，可以在这里执行迁移
# 示例：
# if [ -f "db_version.txt" ]; then
#     NEW_DB_VERSION=\$(cat db_version.txt)
#     echo "   - 需要迁移数据库到版本: \${NEW_DB_VERSION}"
# fi

# 启动
echo "   - 启动服务..."
if sudo systemctl start stock-api; then
    sleep 4
    # 验证
    if curl -s http://127.0.0.1:3007/health > /dev/null 2>&1; then
        echo "   ✅ 服务运行正常"
    else
        echo "   ❌ 服务启动异常，查看日志..."
        sudo journalctl -u stock-api -n 20 --no-pager
        exit 1
    fi
else
    echo "   ❌ 启动失败，查看日志..."
    sudo journalctl -u stock-api -n 20 --no-pager
    exit 1
fi

DEPLOY_SCRIPT

echo ""
echo "✅ 部署完成！"
echo ""
echo "📝 部署信息："
echo "   - 包文件: ${PACKAGE}"
echo "   - 应用位置: /opt/stock-analysis-system/backend"
echo "   - 备份位置: /opt/stock-analysis-system/backend_backup"
echo ""

# 更新 VERSION 文件
echo "   - 更新版本信息..."
cat > "${DEPLOY_TOOLS_PATH}/VERSION" << VERSION_END
# 版本信息文件
# 用于跟踪应用版本和数据库版本

# 应用版本 (YYYYMMDD_HHMMSS)
APP_VERSION=${TIMESTAMP}

# 数据库版本 (对应 migrations/ 中的版本)
DB_VERSION=${CURRENT_DB_VERSION}

# 上次更新时间
LAST_UPDATE=$(date +%Y-%m-%d)

# 上次部署描述
DESCRIPTION="Deployed package: ${PACKAGE}"
VERSION_END

echo ""
echo "🧪 测试访问:"
echo "   curl https://qwquant.com/api/v1/health"
echo ""
echo "📚 后续操作:"
echo "   - 如果数据库结构有变化，执行："
echo "     ./db-migrate.sh <version_number> upgrade"
echo "   - 查看备份："
echo "     ls -lh ./db-backups/"
echo "   - 查看当前版本："
echo "     cat ./VERSION"
echo ""
