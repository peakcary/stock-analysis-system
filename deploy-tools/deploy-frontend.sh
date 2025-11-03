#!/bin/bash
set -e

# ===== 配置 =====
FRONTEND_PATH="/Users/peakom/work/stock-analysis-system/frontend"
DEPLOY_TOOLS_PATH="/Users/peakom/work/stock-analysis-system/deploy-tools"

SERVER_IP="82.157.28.35"
SERVER_USER="ubuntu"
SERVER_PASSWORD="chen_188_8_8"

# ===== 本地执行 =====
echo "🚀 开始部署前端..."
echo ""

# 检查是否已编译
if [ ! -d "${FRONTEND_PATH}/dist" ]; then
    echo "❌ 错误: 前端未编译。请先执行 npm run build"
    exit 1
fi

# 打包
echo "1️⃣  打包前端代码..."
cd ${FRONTEND_PATH}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
PACKAGE="frontend_${TIMESTAMP}.tar.gz"

echo "   压缩前端文件..."
if tar -czf ${PACKAGE} dist/; then
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

echo "   - 备份当前前端..."
sudo rm -rf frontend_backup 2>/dev/null || true
sudo mv frontend frontend_backup 2>/dev/null || true

echo "   - 创建新的前端目录..."
mkdir -p frontend
cd frontend

# 解压
echo "   - 解压前端文件..."
TARFILE=$(ls -t /tmp/frontend_*.tar.gz 2>/dev/null | head -1)
if [ -z "$TARFILE" ]; then
    echo "❌ 错误: 找不到tar.gz文件"
    exit 1
fi
tar -xzf "$TARFILE"

# 权限
echo "   - 设置权限..."
sudo chown -R ubuntu:ubuntu .

# 测试 Nginx 配置
echo "   - 测试 Nginx 配置..."
if sudo nginx -t > /dev/null 2>&1; then
    echo "   - 重启 Nginx..."
    sudo systemctl reload nginx
    echo "   ✅ Nginx 配置成功"
else
    echo "   ⚠️  Nginx 配置有问题，请手动检查"
    sudo nginx -t
fi

DEPLOY_SCRIPT

echo ""
echo "✅ 前端部署完成！"
echo ""
echo "📝 部署信息："
echo "   - 包文件: ${PACKAGE}"
echo "   - 应用位置: /opt/stock-analysis-system/frontend"
echo "   - 备份位置: /opt/stock-analysis-system/frontend_backup"
echo ""

# 更新 VERSION 文件
echo "更新版本信息..."
CURRENT_APP_VERSION=$(grep "^APP_VERSION=" "${DEPLOY_TOOLS_PATH}/VERSION" 2>/dev/null | cut -d= -f2)
CURRENT_DB_VERSION=$(grep "^DB_VERSION=" "${DEPLOY_TOOLS_PATH}/VERSION" 2>/dev/null | cut -d= -f2)

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
DESCRIPTION="Frontend deployed: ${PACKAGE}"
VERSION_END

echo ""
echo "🧪 测试访问:"
echo "   https://qwquant.com"
echo "   https://qwquant.com/payment (客户端支付页面)"
echo ""
echo "📚 后续操作:"
echo "   - 查看版本信息："
echo "     cat ./VERSION"
echo ""
