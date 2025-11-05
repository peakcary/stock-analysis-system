#!/bin/bash

# 快速修复脚本 - 在服务器上执行
# 这个脚本会拉取最新代码并重新构建

set -e

echo "🚀 开始快速修复..."
echo ""

cd /opt/stock-analysis-system

echo "📦 拉取最新代码..."
git fetch origin
git reset --hard origin/main

echo "🔨 清理旧的构建文件..."
rm -rf frontend/dist
rm -rf client/dist

echo "🔨 重新构建前端应用..."
cd frontend
npm install --legacy-peer-deps
npm run build
cd ..

echo "🔨 重新构建客户端应用..."
cd client
npm install --legacy-peer-deps
npm run build
cd ..

echo "✅ 快速修复完成！"
echo ""
echo "现在需要检查 Nginx 配置..."
echo ""
echo "运行以下命令来验证和重新加载 Nginx："
echo "  sudo nginx -t"
echo "  sudo systemctl reload nginx"
echo ""
echo "然后访问 https://qwquant.com/admin 来验证修复"
