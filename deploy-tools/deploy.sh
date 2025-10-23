#!/bin/bash
set -e

# ===== 配置 =====
# ⚠️  重要：修改下面这个路径为你的实际项目路径
PROJECT_PATH="/Users/peakom/work/stock-analysis-system/backend"

SERVER_IP="82.157.28.35"
SERVER_USER="ubuntu"
SERVER_PASSWORD="chen_188_8_8"

# ===== 本地执行 =====
echo "🚀 开始部署..."
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
TARFILE=$(ls -t /tmp/backend_*.tar.gz 2>/dev/null | head -1)
if [ -z "$TARFILE" ]; then
    echo "❌ 错误: 找不到tar.gz文件"
    exit 1
fi
tar --strip-components=1 -xzf "$TARFILE"

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
echo "🧪 测试访问:"
echo "   curl https://qwquant.com/api/v1/health"
echo ""
