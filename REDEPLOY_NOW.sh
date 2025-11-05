#!/bin/bash

# 快速重新部署脚本 - 只重新构建Client
# Quick redeploy script - rebuild Client only

set -e

echo "=========================================="
echo "快速重新部署 - Client 应用"
echo "=========================================="

cd /opt/stock-analysis-system

# 1. 拉取最新代码
echo ""
echo "📦 [1/4] 正在拉取最新代码..."
git fetch origin
git reset --hard origin/main

# 2. 清理旧的client dist文件
echo "🧹 [2/4] 清理旧文件..."
rm -rf client/dist

# 3. 重新构建Client
echo "🔨 [3/4] 重新构建 Client..."
cd client
npm install > /dev/null 2>&1 || true
npm run build
cd ..

# 4. 重新加载Nginx
echo "⚙️  [4/4] 重新加载 Nginx..."
sudo systemctl reload nginx

echo ""
echo "=========================================="
echo "✅ 快速重新部署完成！"
echo "=========================================="
echo ""
echo "验证步骤:"
echo "1. 打开浏览器访问: https://qwquant.com (Client 应用)"
echo "2. 按 F12 打开开发者工具"
echo "3. 切换到 Network 标签"
echo "4. 刷新页面 (F5)"
echo "5. 检查 API 请求路径:"
echo "   ✅ 正确: /api/v1/payment/v2/orders/history"
echo "   ❌ 错误: /api/v1/api/v1/payment/v2/orders/history"
echo ""
