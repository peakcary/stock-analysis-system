# 系统架构说明 - API 配置和集成

## 总体架构

```
┌──────────────────────────────────────────────────────────────┐
│                         浏览器                               │
│  https://qwquant.com/admin   https://qwquant.com/app       │
└────────────────────────────────┬────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                        │
                    ▼                        ▼
            ┌──────────────────────────────────────┐
            │         Nginx 反向代理                │
            │  (web server + reverse proxy)        │
            └──────────────┬──────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
    /admin → Frontend   /app → Client    /api/v1 → Backend
    (静态文件)  (静态文件)  (静态文件)       (代理)    (API)
```

## 详细说明

### 1. Backend (API 服务)

**位置**: `/opt/stock-analysis-system/backend`

**运行方式**: Gunicorn + FastAPI

**监听地址**: `127.0.0.1:3007` (内部地址，不直接暴露)

**路由配置**:
```python
# app/main.py
app.include_router(api_router, prefix="/api/v1")
```

**接口格式**: `/api/v1/*`
- `/api/v1/stocks` - 获取股票列表
- `/api/v1/admin/auth/login` - 管理员登录
- `/api/v1/admin/client-users/users` - 客户端用户列表

### 2. Nginx (反向代理 + Web Server)

**配置位置**: `/etc/nginx/sites-enabled/qwquant.com` 或 `/etc/nginx/conf.d/qwquant.conf`

**核心配置**:

#### 2.1 Frontend (管理后台)
```nginx
server {
    listen 443 ssl http2;
    server_name qwquant.com www.qwquant.com;

    # Frontend 应用（静态文件）
    location / {
        root /opt/stock-analysis-system/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
}
```

#### 2.2 Client (客户端应用)
```nginx
# 在同一个server块中
location /app/ {
    alias /opt/stock-analysis-system/client/dist/;
    try_files $uri $uri/ /index.html;
}
```

#### 2.3 API 反向代理
```nginx
# 在同一个server块中
location /api/v1/ {
    proxy_pass http://backend;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

**upstream backend 定义**:
```nginx
upstream backend {
    server 127.0.0.1:3007;
}
```

### 3. Frontend (管理后台)

**位置**: `/opt/stock-analysis-system/frontend`

**构建**: `npm run build` → `frontend/dist/`

**静态资源**:
- HTML, CSS, JS (production builds)
- 由 Nginx 的 `location /` serve

**API 配置** (`shared/auth-config.ts`):
```typescript
export const getApiBaseUrl = (): string => {
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    // 开发环境：直接指向 Backend
    return `http://${hostname}:3007/api/v1`;
  }
  // 生产环境：使用相对路径，通过 Nginx 代理
  return '/api/v1';
};

export const ADMIN_AUTH_CONFIG: AuthConfig = {
  apiBaseUrl: getApiBaseUrl(),  // '/api/v1' (生产)
  endpoints: {
    login: '/admin/auth/login',    // 相对路径
    logout: '/admin/auth/logout',
    refresh: '/admin/auth/refresh',
    me: '/admin/auth/me'
  }
};
```

**API 调用示例** (`frontend/src/App.tsx`):
```typescript
// axios client 配置
const apiClient = axios.create({
  baseURL: '/api/v1',  // 生产环境的 baseURL
});

// API 调用使用相对路径
adminApiClient.get('/stocks/count')
// 完整路径: /api/v1/stocks/count
```

### 4. Client (客户端应用)

**位置**: `/opt/stock-analysis-system/client`

**构建**: `npm run build` → `client/dist/`

**Vite 配置** (`vite.config.ts`):
```typescript
export default defineConfig({
  base: '/app/',  // 生产环境的基础路径
});
```

**API 配置**: 与 Frontend 相同

**API 调用**: 同样使用相对路径

## 请求流程示例

### 场景1: Frontend 获取股票列表

```
1. 前端代码执行:
   adminApiClient.get('/stocks/count')

2. Axios 处理:
   baseURL: '/api/v1'
   + endpoint: '/stocks/count'
   = 完整路径: /api/v1/stocks/count

3. 浏览器发送 HTTP 请求:
   GET https://qwquant.com/api/v1/stocks/count

4. Nginx 接收:
   URL: /api/v1/stocks/count
   匹配: location /api/v1/
   执行: proxy_pass http://backend;

5. Nginx 转发到 Backend:
   GET http://127.0.0.1:3007/api/v1/stocks/count

6. Backend FastAPI 处理:
   app.include_router(api_router, prefix="/api/v1")
   完整路由: /api/v1/stocks
   匹配: api_router 中的 /stocks 路由
   执行: stocks.py 中的 count() 函数

7. 返回响应:
   HTTP 200
   {"count": 1234}

8. 浏览器接收:
   ✅ 成功
```

### 场景2: Client 用户登录

```
1. 前端代码执行:
   authManager.login('user@example.com', 'password')

2. 内部调用:
   adminApiClient.post('/admin/auth/login', ...)

3. 完整请求:
   POST https://qwquant.com/api/v1/admin/auth/login

4. Nginx → Backend:
   POST http://127.0.0.1:3007/api/v1/admin/auth/login

5. Backend 处理:
   路由: /api/v1/admin/auth/login
   返回: {"token": "...", "user": {...}}

6. 成功登录 ✅
```

## 环境差异

### 开发环境

```
Frontend (http://localhost:3000)
  ↓
apiClient.baseURL = http://localhost:3007/api/v1
  ↓
Direct call to Backend (no Nginx)
Backend (http://localhost:3007)
```

### 生产环境

```
Frontend (https://qwquant.com)
  ↓
apiClient.baseURL = /api/v1 (相对路径)
  ↓
Nginx 反向代理 (location /api/v1/)
  ↓
Backend (127.0.0.1:3007，仅内部可访问)
```

## 配置检查清单

部署到生产服务器时，需要检查：

- [ ] Backend 运行在 `127.0.0.1:3007`
- [ ] Nginx 配置包含 `upstream backend { server 127.0.0.1:3007; }`
- [ ] Nginx 配置包含 `location /api/v1/ { proxy_pass http://backend; }`
- [ ] Frontend dist 文件在 `/opt/stock-analysis-system/frontend/dist/`
- [ ] Client dist 文件在 `/opt/stock-analysis-system/client/dist/`
- [ ] Frontend 的 `getApiBaseUrl()` 返回 `/api/v1` (生产环境)
- [ ] Client 的 `getApiBaseUrl()` 返回 `/api/v1` (生产环境)
- [ ] Nginx 配置语法正确: `sudo nginx -t`
- [ ] Nginx 已重新加载: `sudo systemctl reload nginx`

## 常见问题

### Q: 为什么 Frontend/Client 不直接连接 Backend？

A: 安全考虑
- Backend 仅监听内部地址 (127.0.0.1)，外部无法直接访问
- 通过 Nginx 反向代理，可以添加额外的安全层（认证、限流、HTTPS等）
- Nginx 可以路由多个应用到同一 Backend

### Q: 为什么使用相对路径 `/api/v1` 而不是完整 URL？

A: 灵活性
- 相对路径在开发和生产环境自动适应
- 开发环境：可以指向任何 Backend 地址
- 生产环境：通过 Nginx 代理
- 前端代码无需修改就能在不同环境运行

### Q: 如何修改 API 服务器地址？

**开发环境**: 修改 `getApiBaseUrl()` 中的 `localhost:3007`

**生产环境**: Nginx 配置 `upstream backend { server ...; }` 的服务器地址

### Q: 如何验证 API 路由是否正确？

```bash
# 1. 检查 Nginx 配置
grep -n "location /api" /etc/nginx/sites-enabled/qwquant.com

# 2. 检查 Backend 是否运行
curl http://127.0.0.1:3007/api/health

# 3. 测试通过 Nginx 的请求
curl https://qwquant.com/api/v1/health

# 4. 检查浏览器 DevTools
# 打开 https://qwquant.com/admin
# F12 → Network → 查看 API 请求路径
```

## 相关文件

- 前端配置: `shared/auth-config.ts`
- 后端路由: `backend/app/api/api_v1/api.py`, `backend/app/main.py`
- Nginx 配置: `nginx/nginx.prod.conf`, `nginx/nginx.prod.complete.conf`, `nginx/nginx.prod.route.conf`

## 修复历史

- **Commit 4d52c286**: 统一 API 配置，使用 `/api/v1` 作为 baseURL，相对路径作为端点
- **Commit 9a9f772e**: 简化 Nginx 配置，移除不必要的 rewrite 规则，使用 `location /api/v1/` 直接代理
