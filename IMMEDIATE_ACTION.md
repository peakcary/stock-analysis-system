# ⚠️ 需要立即采取的行动

## 问题现状

✅ **本地代码已修复完成** (所有源代码和配置)
❌ **服务器上还是旧版本** (dist文件和Nginx配置未更新)

因此仍然看到 `/api/v1/api/v1/...` 的错误

## 需要在服务器上执行

### 方法 1: 使用自动化部署脚本（推荐）

在服务器上执行：

```bash
cd /opt/stock-analysis-system
bash server-deploy.sh
```

这个脚本会：
1. 拉取最新代码
2. 清理旧的dist文件
3. 重新构建 Frontend 和 Client
4. 检查 Nginx 配置和API路径
5. 重新加载 Nginx
6. 验证部署

### 方法 2: 手动步骤（如果脚本不工作）

```bash
ssh ubuntu@82.157.28.35

cd /opt/stock-analysis-system

# 1. 拉取最新代码
git pull origin main

# 2. 清理旧文件
rm -rf frontend/dist client/dist

# 3. 构建Frontend
cd frontend
npm install
npm run build
cd ..

# 4. 构建Client
cd client
npm install
npm run build
cd ..

# 5. 检查Nginx配置
sudo cat /etc/nginx/sites-enabled/qwquant.com | grep -A 5 "location /api"
# 应该显示:
# location /api/v1/ {
#     proxy_pass http://backend;
# }
#
# 不应该有 rewrite 规则

# 6. 重新加载Nginx
sudo systemctl reload nginx

# 7. 验证
curl https://qwquant.com/api/v1/health
```

## 关键检查点

部署完成后，检查以下内容：

### ✅ 检查 1: 本地代码版本

```bash
cd /opt/stock-analysis-system
git log --oneline -1
```

应该显示最新提交 (大约是 `11ece054` 附近)

### ✅ 检查 2: dist 文件的构建时间

```bash
ls -lah frontend/dist/index.html
ls -lah client/dist/index.html
```

应该显示为最近的时间

### ✅ 检查 3: Nginx 配置

```bash
sudo cat /etc/nginx/sites-enabled/qwquant.com | head -50
```

**应该有**:
```nginx
location /api/v1/ {
    proxy_pass http://backend;
    ...
}
```

**不应该有**:
```nginx
rewrite ^/api/(.*)$ /api/v1/$1 break;
```

### ✅ 检查 4: API 路径格式

在浏览器中验证：

1. 打开 https://qwquant.com/admin
2. F12 → Network 标签
3. 刷新页面
4. 查看 API 请求：

✅ **正确**: `/api/v1/stocks`, `/api/v1/admin/auth/login`
❌ **错误**: `/api/v1/api/v1/stocks`, `/api/v1/api/v1/admin/auth/login`

## 为什么会这样

### 原因链路

1. **服务器上的 dist 文件是旧的**
   - Frontend dist 中的 JS 代码还在发送 `/api/v1/stocks` 的请求（旧代码）

2. **加上 Nginx 的 rewrite 规则（如果还有）**
   - 旧的 Nginx 配置有: `rewrite ^/api/(.*)$ /api/v1/$1 break;`
   - `/api/v1/stocks` 被转换为 `/api/v1/api/v1/stocks` ❌

### 修复方式

1. **更新 Frontend dist**
   - 新代码发送: `/stocks` (相对于 baseURL `/api/v1`)
   - 完整路径: `/api/v1/stocks` ✅

2. **更新 Nginx 配置**
   - 移除 rewrite 规则
   - 使用: `location /api/v1/ { proxy_pass http://backend; }`
   - 直接转发，无需路径转换 ✅

## 快速排查

如果部署后仍然看到错误，按以下顺序检查：

### 1️⃣ 浏览器缓存

```
浏览器 → F12 → Network → 清除缓存
或 Ctrl+Shift+Delete 清空缓存后重新加载
```

### 2️⃣ dist 文件是否更新

```bash
# 检查文件修改时间（应该是几分钟前）
stat /opt/stock-analysis-system/frontend/dist/index.html
stat /opt/stock-analysis-system/client/dist/index.html
```

### 3️⃣ Nginx 配置是否正确

```bash
# 查看当前配置
sudo cat /etc/nginx/sites-enabled/qwquant.com | grep -A 3 "location /api"

# 应该没有 rewrite 规则
grep "rewrite" /etc/nginx/sites-enabled/qwquant.com
# 应该无输出或只有注释
```

### 4️⃣ git 版本是否最新

```bash
cd /opt/stock-analysis-system
git log --oneline -1
git status
# 应该显示 "nothing to commit, working tree clean"
```

## 关键文件

- **部署脚本**: `server-deploy.sh` (自动化部署)
- **架构文档**: `ARCHITECTURE.md` (系统设计说明)
- **部署指南**: `DEPLOY_CORRECT.md` (详细步骤)
- **源代码**: `shared/auth-config.ts`, `frontend/src/**`, `client/src/**`
- **Nginx配置**: `nginx/nginx.prod.conf` (配置示例)

## 总结

**本质问题**: 服务器上的应用还是旧版本

**解决方案**: 重新部署（使用脚本或手动步骤）

**验证方法**: 在浏览器 DevTools 中查看 API 请求路径

一旦部署完成，API 路径应该恢复正常！
