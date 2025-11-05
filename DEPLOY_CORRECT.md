# 正确的部署步骤 - API 架构修复

## 概述

根据正确的架构设计，已完成以下修改：

1. ✅ **Backend**: 运行在 `127.0.0.1:3007`，提供 `/api/v1/*` 接口
2. ✅ **Frontend**: 使用 `/api/v1` 作为 axios baseURL，相对路径作为端点
3. ✅ **Client**: 同上
4. ✅ **Nginx**: 配置 `location /api/v1/` 直接代理到 Backend

## 最新提交

- **Commit 4d52c286**: 统一 API 配置和路径
- **Commit 9a9f772e**: 简化 Nginx 配置
- **Commit 4d42c753**: 添加架构文档

## 在服务器上执行的步骤

### 步骤 1: 拉取最新代码

```bash
cd /opt/stock-analysis-system
git pull origin main
```

### 步骤 2: 检查和更新 Nginx 配置

**查看当前使用的 Nginx 配置文件**:

```bash
# 通常在以下位置之一
sudo cat /etc/nginx/sites-enabled/qwquant.com
# 或
sudo cat /etc/nginx/conf.d/qwquant.com.conf
```

**需要包含的关键配置**:

```nginx
# upstream 定义
upstream backend {
    server 127.0.0.1:3007;
}

# API 代理
location /api/v1/ {
    proxy_pass http://backend;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

# Frontend
location / {
    root /opt/stock-analysis-system/frontend/dist;
    try_files $uri $uri/ /index.html;
}

# Client
location /app/ {
    alias /opt/stock-analysis-system/client/dist/;
    try_files $uri $uri/ /index.html;
}
```

**如果配置不对，参考以下文件更新**:

```bash
# 查看最新的配置文件示例
cat nginx/nginx.prod.conf        # 完整示例
cat nginx/nginx.prod.complete.conf # 另一个示例
cat nginx/nginx.prod.route.conf   # 路由示例

# 复制到 Nginx 配置目录
# sudo cp nginx/nginx.prod.conf /etc/nginx/sites-available/qwquant.com
# sudo ln -s /etc/nginx/sites-available/qwquant.com /etc/nginx/sites-enabled/
```

**验证 Nginx 配置**:

```bash
sudo nginx -t
# 应该输出:
# nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
# nginx: configuration file /etc/nginx/nginx.conf test is successful
```

**重新加载 Nginx**:

```bash
sudo systemctl reload nginx
```

### 步骤 3: 重新构建应用

```bash
# Frontend
cd frontend
npm install
npm run build
cd ..

# Client
cd client
npm install
npm run build
cd ..
```

### 步骤 4: 验证 Backend 运行

```bash
# 检查 Backend 是否运行
curl http://127.0.0.1:3007/health

# 应该返回:
# {"status":"ok"}

# 或检查 API 端点
curl http://127.0.0.1:3007/api/v1/health
```

### 步骤 5: 验证部署成功

**在浏览器中测试**:

```
1. 打开 https://qwquant.com/admin (Frontend)
2. 打开 https://qwquant.com/app (Client)
3. F12 打开 DevTools → Network 标签
4. 执行任何操作（如登录、加载数据）
5. 查看 API 请求：
   ✅ 应该看到: /api/v1/stocks, /api/v1/admin/auth/login 等
   ❌ 不应该看到: /api/v1/api/v1/... 的重复
```

**命令行验证**:

```bash
# 测试 API 是否可访问
curl https://qwquant.com/api/v1/health

# 应该返回 200 OK
```

## 请求流程验证

以获取股票列表为例：

```
1. Frontend 代码执行:
   adminApiClient.get('/stocks/count')

2. Axios 构建完整路径:
   baseURL: /api/v1
   + endpoint: /stocks/count
   = /api/v1/stocks/count

3. 浏览器发送请求:
   GET https://qwquant.com/api/v1/stocks/count

4. Nginx 处理:
   匹配 location /api/v1/
   proxy_pass http://backend
   转发: GET http://127.0.0.1:3007/api/v1/stocks/count

5. Backend 收到:
   GET /api/v1/stocks/count
   路由匹配: app.include_router(api_router, prefix="/api/v1")
   执行: api_router 中的 /stocks 路由

6. 返回响应:
   ✅ HTTP 200
   {"count": 1234}
```

## 常见问题排查

### 问题1: 仍然看到 `/api/v1/api/v1/...`

**原因**:
- 前端 dist 文件还是旧版本
- 或 Nginx 配置仍有 rewrite 规则

**解决**:
```bash
# 清理旧的 dist
rm -rf frontend/dist client/dist

# 重新构建
cd frontend && npm run build && cd ..
cd client && npm run build && cd ..

# 检查 Nginx 配置中是否有 rewrite
grep -n "rewrite" /etc/nginx/sites-enabled/qwquant.com
# 应该没有或已删除

# 重新加载
sudo systemctl reload nginx
```

### 问题2: API 返回 404

**排查步骤**:
```bash
# 1. 检查 Backend 是否运行
curl http://127.0.0.1:3007/health

# 2. 检查 Nginx 是否正确转发
curl -v https://qwquant.com/api/v1/health

# 3. 检查 Nginx 错误日志
sudo tail -f /var/log/nginx/error.log

# 4. 检查后端日志（路径根据实际情况）
tail -f /opt/stock-analysis-system/logs/app.log
```

### 问题3: CORS 错误

**原因**: Backend 的 CORS 配置未包含生产域名

**解决**: 修改 `backend/app/main.py` 的 CORS 配置
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8005",
        "http://localhost:8006",
        "https://qwquant.com",  # 添加生产域名
    ],
    # ...
)
```

### 问题4: 部分 API 仍然返回错误路径

**原因**: 可能还有其他地方使用了旧的 API 调用方式

**排查**:
```bash
# 搜索旧的 API 路径格式
grep -r "/api/v1/api" frontend/src
grep -r "/api/v1/api" client/src

# 应该没有返回结果
```

## 部署检查清单

- [ ] 代码已拉取 (git pull origin main)
- [ ] Nginx 配置已更新到最新版本
- [ ] Nginx 配置检查通过 (sudo nginx -t)
- [ ] Nginx 已重新加载 (sudo systemctl reload nginx)
- [ ] Backend 运行在 127.0.0.1:3007
- [ ] Frontend 已重新构建 (npm run build)
- [ ] Client 已重新构建 (npm run build)
- [ ] curl http://127.0.0.1:3007/health 返回 200
- [ ] curl https://qwquant.com/api/v1/health 返回 200
- [ ] 浏览器测试 https://qwquant.com/admin - 可以加载
- [ ] 浏览器测试 https://qwquant.com/app - 可以加载
- [ ] DevTools 中 API 请求路径正确 (/api/v1/..., 无重复)

## 关键概念

**baseURL**: Axios 的基础 URL
- 开发: `http://localhost:3007/api/v1`
- 生产: `/api/v1`

**endpoints**: 相对于 baseURL 的路径
- 示例: `/stocks/count`
- 完整路径: baseURL + endpoint = `/api/v1/stocks/count`

**Nginx location**: URL 路径匹配
- `location /api/v1/ { proxy_pass http://backend; }`
- 匹配 `/api/v1/...` 的请求，转发到 backend

**proxy_pass**: Nginx 反向代理
- `proxy_pass http://backend;` 将请求转发到 backend
- Backend 收到原始路径 `/api/v1/...`

## 完整工作流程

```
用户浏览器
    ↓
Nginx (反向代理)
    ↓ (如果是 API 请求)
    ├→ /api/v1 location (代理到 Backend)
    │
    └→ / or /app location (serve 静态文件)

Backend (FastAPI)
    ↓ (收到 /api/v1/...)
    ├→ /api/v1 prefix router
    │   ├→ /stocks → 股票接口
    │   ├→ /admin/auth/login → 登录接口
    │   └→ ...
    │
    └→ 返回响应

响应返回到浏览器
```

## 文档参考

- `ARCHITECTURE.md` - 详细的系统架构说明
- `shared/auth-config.ts` - API 配置文件
- `nginx/nginx.prod.conf` - Nginx 配置示例

一切修复完成，现在部署到服务器即可！
