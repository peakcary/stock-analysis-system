#!/bin/bash

# 完整部署脚本 - 包含所有依赖安装
# Complete deployment script with all dependencies

set -e

echo "=========================================="
echo "完整部署脚本 - API 路径重复修复"
echo "=========================================="

cd /opt/stock-analysis-system

# 1. 拉取最新代码
echo ""
echo "📦 [1/7] 正在拉取最新代码..."
git fetch origin
git reset --hard origin/main

# 2. 安装共享依赖（如果有package.json）
if [ -f "package.json" ]; then
    echo "📦 [2/7] 安装根目录依赖..."
    npm install
fi

# 3. 清理旧的dist文件
echo "🧹 [3/7] 清理旧文件..."
rm -rf frontend/dist client/dist frontend/node_modules client/node_modules

# 4. 构建Frontend
echo "🔨 [4/7] 构建 Frontend..."
cd frontend
echo "   - 安装依赖..."
npm install
echo "   - 编译..."
npm run build
echo "   ✅ Frontend 构建完成"
cd ..

# 5. 构建Client
echo "🔨 [5/7] 构建 Client..."
cd client
echo "   - 安装依赖..."
npm install
echo "   - 编译..."
npm run build
echo "   ✅ Client 构建完成"
cd ..

# 6. 验证dist文件存在
echo "✓ [6/7] 验证构建文件..."
if [ -d "frontend/dist" ]; then
    echo "   ✅ Frontend dist 目录存在"
    ls -lh frontend/dist/index.html
else
    echo "   ❌ Frontend dist 目录缺失！"
    exit 1
fi

if [ -d "client/dist" ]; then
    echo "   ✅ Client dist 目录存在"
    ls -lh client/dist/index.html
else
    echo "   ❌ Client dist 目录缺失！"
    exit 1
fi

# 7. 重新加载Nginx
echo "⚙️  [7/7] 重新加载 Nginx..."
sudo systemctl reload nginx

echo ""
echo "=========================================="
echo "✅ 部署完成！"
echo "=========================================="
echo ""
echo "验证步骤:"
echo "1. 打开浏览器访问: https://qwquant.com/admin"
echo "2. 按 F12 打开开发者工具"
echo "3. 切换到 Network 标签"
echo "4. 刷新页面 (F5)"
echo "5. 查看 API 请求:"
echo "   ✅ 正确: /api/v1/admin/auth/login, /api/v1/stocks/..."
echo "   ❌ 错误: /api/v1/api/v1/admin/auth/login"
echo ""
echo "如果还是看到 /api/v1/api/v1/"
echo "可能的原因:"
echo "  1. 浏览器缓存 - 按 Ctrl+Shift+Delete 清除缓存"
echo "  2. Nginx 配置未更新 - 检查 /etc/nginx/conf.d/nginx.prod.conf"
echo "  3. 检查日志: sudo tail -f /var/log/nginx/error.log"
echo ""
