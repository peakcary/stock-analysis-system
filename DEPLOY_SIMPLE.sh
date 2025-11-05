#!/bin/bash

# 超级简单的部署脚本 - 在服务器上直接执行
# 只做最关键的事情

set -e

echo "===================="
echo "开始部署..."
echo "===================="

cd /opt/stock-analysis-system

# 1. 拉取最新代码
echo ""
echo "📦 正在拉取最新代码..."
git fetch origin
git reset --hard origin/main

# 2. 清理旧的dist文件
echo "🧹 清理旧文件..."
rm -rf frontend/dist client/dist

# 3. 重新构建Frontend
echo "🔨 构建 Frontend..."
cd frontend
npm install > /dev/null 2>&1 || true
npm run build > /dev/null 2>&1
cd ..

# 4. 重新构建Client
echo "🔨 构建 Client..."
cd client
npm install > /dev/null 2>&1 || true
npm run build > /dev/null 2>&1
cd ..

# 5. 重新加载Nginx
echo "⚙️ 重新加载 Nginx..."
sudo systemctl reload nginx

echo ""
echo "✅ 部署完成！"
echo ""
echo "验证方法:"
echo "1. 打开 https://qwquant.com/admin"
echo "2. 按 F12 → Network 标签"
echo "3. 刷新页面"
echo "4. 查看 API 请求路径应该是 /api/v1/... 而不是 /api/v1/api/v1/..."
