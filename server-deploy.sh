#!/bin/bash

# 在服务器上执行的自动部署脚本
# 这个脚本应该在 /opt/stock-analysis-system 目录中执行

set -e

echo "================================"
echo "  自动部署脚本"
echo "================================"
echo ""

# 检查是否在正确的目录
if [ ! -d ".git" ]; then
    echo "❌ 错误：不在项目根目录"
    echo "请在 /opt/stock-analysis-system 目录中执行此脚本"
    exit 1
fi

echo "📦 步骤 1: 拉取最新代码..."
git fetch origin
git reset --hard origin/main
LATEST_COMMIT=$(git log -1 --oneline)
echo "✅ 当前版本: $LATEST_COMMIT"
echo ""

echo "🧹 步骤 2: 清理旧的构建文件..."
rm -rf frontend/dist client/dist
echo "✅ 已清理"
echo ""

echo "🔨 步骤 3: 构建 Frontend..."
cd frontend
npm install --legacy-peer-deps 2>/dev/null || npm install
npm run build > /dev/null 2>&1
echo "✅ Frontend 构建完成"
cd ..
echo ""

echo "🔨 步骤 4: 构建 Client..."
cd client
npm install --legacy-peer-deps 2>/dev/null || npm install
npm run build > /dev/null 2>&1
echo "✅ Client 构建完成"
cd ..
echo ""

echo "🔍 步骤 5: 检查 API 调用格式..."
# 检查是否还有旧的 API 路径
if grep -r "/api/v1/api" frontend/dist client/dist 2>/dev/null > /dev/null; then
    echo "❌ 发现重复的 API 路径 (/api/v1/api)"
    echo "   这表示代码修复可能没有正确应用"
    exit 1
else
    echo "✅ API 路径格式正确"
fi
echo ""

echo "⚙️  步骤 6: 检查 Nginx 配置..."
if [ -f "/etc/nginx/sites-enabled/qwquant.com" ]; then
    CONFIG_FILE="/etc/nginx/sites-enabled/qwquant.com"
elif [ -f "/etc/nginx/conf.d/qwquant.com.conf" ]; then
    CONFIG_FILE="/etc/nginx/conf.d/qwquant.com.conf"
else
    echo "⚠️  无法找到 Nginx 配置文件"
    echo "   请手动检查 Nginx 配置是否包含:"
    echo "   - location /api/v1/ { proxy_pass http://backend; }"
    echo "   - 无 rewrite 规则"
fi

if [ ! -z "$CONFIG_FILE" ]; then
    echo "   配置文件: $CONFIG_FILE"

    # 检查是否有 rewrite 规则
    if grep -q "rewrite.*api" "$CONFIG_FILE"; then
        echo "❌ 发现 rewrite 规则（应该移除）"
        echo "   当前 Nginx 配置中有 rewrite 规则，这会导致路径重复"
        echo ""
        echo "   需要的配置应该是:"
        echo "   location /api/v1/ {"
        echo "       proxy_pass http://backend;"
        echo "   }"
    else
        echo "✅ Nginx 配置正确"
    fi

    # 检查是否有 /api/v1/ location
    if grep -q "location /api/v1/" "$CONFIG_FILE"; then
        echo "✅ 找到 /api/v1/ 代理配置"
    else
        echo "⚠️  未找到 /api/v1/ 代理配置"
    fi
fi
echo ""

echo "✅ 验证 Nginx 配置语法..."
if sudo nginx -t 2>&1 | grep -q "successful"; then
    echo "✅ Nginx 配置语法正确"

    echo ""
    echo "🔄 步骤 7: 重新加载 Nginx..."
    sudo systemctl reload nginx
    echo "✅ Nginx 已重新加载"
else
    echo "❌ Nginx 配置有错误，请先修复"
    exit 1
fi
echo ""

echo "🧪 步骤 8: 验证部署..."
if curl -s http://127.0.0.1:3007/health > /dev/null; then
    echo "✅ Backend 运行正常"
else
    echo "⚠️  Backend 可能未运行"
fi

if curl -s -o /dev/null -w "%{http_code}" https://qwquant.com/api/v1/health | grep -q "200"; then
    echo "✅ API 端点可访问"
else
    echo "⚠️  API 端点可能无法访问"
fi
echo ""

echo "================================"
echo "  ✅ 部署完成！"
echo "================================"
echo ""
echo "接下来的步骤："
echo "1. 在浏览器中打开 https://qwquant.com/admin"
echo "2. 按 F12 打开 DevTools → Network 标签"
echo "3. 刷新页面并检查 API 请求路径"
echo "4. 应该看到 /api/v1/... 而不是 /api/v1/api/v1/..."
echo ""
echo "如果仍然看到 /api/v1/api/v1/，请："
echo "1. 检查浏览器缓存（Ctrl+Shift+Delete）"
echo "2. 检查 Nginx 配置是否有 rewrite 规则"
echo "3. 确认服务器上的 git 版本是最新的"
echo ""
