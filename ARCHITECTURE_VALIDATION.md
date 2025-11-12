# 系统架构验证与修复指南

## 📋 标准三层架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                     标准三层架构模式                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│ 第一层：数据库层                                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ MySQL 数据库                                                │ │
│ │ ├─ users (用户表)                                          │ │
│ │ ├─ concepts (概念表)                                       │ │
│ │ ├─ stocks (股票表)                                         │ │
│ │ └─ ... (其他表)                                            │ │
│ │                                                             │ │
│ │ 初始化脚本：                                                │ │
│ │ ├─ init_database.py (Python 初始化)                       │ │
│ │ ├─ init.sql (SQL 表结构)                                  │ │
│ │ └─ migration files (迁移脚本)                              │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│ 第二层：API 服务层 (Backend)                                     │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ FastAPI 服务器 (端口 3007)                                 │ │
│ │ ├─ 路由：/api/v1/auth (认证)                              │ │
│ │ ├─ 路由：/api/v1/concepts (概念)                          │ │
│ │ ├─ 路由：/api/v1/stocks (股票)                            │ │
│ │ ├─ 路由：/api/v1/payment (支付)                           │ │
│ │ └─ ... (其他路由)                                         │ │
│ │                                                             │ │
│ │ 连接字符串：                                                │ │
│ │ mysql+pymysql://root:Pp123456@127.0.0.1:3306/...         │ │
│ │                                                             │ │
│ │ 启动命令：                                                  │ │
│ │ python -m uvicorn app.main:app --host 0.0.0.0 --port 3007 │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│ 第三层：前端应用层                                                │
│ ┌──────────────────────────────┬──────────────────────────────┐ │
│ │ Frontend (管理后台)           │ Client (用户应用)            │ │
│ │ ├─ 端口：8006               │ ├─ 端口：8005             │ │
│ │ ├─ Vite 代理配置：          │ ├─ Vite 代理配置：        │ │
│ │ │  /api -> :3007           │ │  /api -> :3007          │ │
│ │ ├─ API 地址：/api/v1       │ ├─ API 地址：/api/v1     │ │
│ │ └─ 认证：JWT Token          │ └─ 认证：JWT Token       │ │
│ └──────────────────────────────┴──────────────────────────────┘ │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## ✅ 系统当前配置审查

### 第一层：数据库层 ✓

#### 初始化脚本位置
```
✓ backend/init_database.py          - Python 初始化脚本
✓ scripts/database/init.sql         - 表结构定义
✓ scripts/database/init_database.sh - Shell 初始化脚本
✓ backend/.env                      - 数据库连接配置
```

#### 数据库配置
```
数据库类型：MySQL 8.0+
默认库名：stock_analysis_dev
默认用户：root
默认密码：Pp123456
连接地址：127.0.0.1:3306

连接字符串（配置在 backend/.env）：
mysql+pymysql://root:Pp123456@127.0.0.1:3306/stock_analysis_dev
```

#### 初始化表结构
```
✓ users              - 用户表 (admin, fullaccess_user 等)
✓ concepts           - 概念表
✓ stocks             - 股票表
✓ concept_stocks     - 概念-股票关联
✓ payment_orders     - 支付订单
✓ user_packages      - 用户套餐
✓ import_records     - 导入记录
✓ ... (其他数据表)
```

**状态**: 🟢 正确配置

---

### 第二层：Backend API 服务 ✓

#### 启动配置
```
文件：backend/app/core/config.py

主机：0.0.0.0
端口：3007
API 前缀：/api/v1
基础 URL：http://localhost:3007

完整 API 地址：http://localhost:3007/api/v1
```

#### API 路由注册
```
文件：backend/app/main.py

app.include_router(api_router, prefix="/api/v1")

所有端点都在 /api/v1/ 下：
✓ /api/v1/auth/*
✓ /api/v1/admin-auth/*
✓ /api/v1/concepts/*
✓ /api/v1/stocks/*
✓ /api/v1/payment/*
✓ /api/v1/data/*
✓ ... (等等)
```

#### CORS 配置
```
允许的来源：
✓ http://localhost:8005   (Client)
✓ http://127.0.0.1:8005
✓ http://localhost:8006   (Frontend)
✓ http://127.0.0.1:8006
```

#### 启动命令
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 3007
```

**状态**: 🟢 正确配置

---

### 第三层：Frontend/Client 应用 ⚠️ 配置有问题

#### 问题诊断

**Frontend (8006) Vite 代理配置** ✓ 正确
```typescript
// frontend/vite.config.ts
server: {
  port: 8006,
  proxy: {
    '/api': {
      target: 'http://127.0.0.1:3007',  // 正确指向 Backend
      changeOrigin: true
    }
  }
}
```

**Client (8005) Vite 代理配置** ✓ 正确
```typescript
// client/vite.config.ts
server: {
  port: 8005,
  proxy: {
    '/api': {
      target: 'http://127.0.0.1:3007',  // 正确指向 Backend
      changeOrigin: true
    }
  }
}
```

**但是，认证配置有问题** ⚠️ 这是导致 404 的根本原因

```typescript
// shared/auth-config.ts - 问题代码
export const getApiBaseUrl = (): string => {
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;

    // 开发环境：直接返回完整 URL，绕过了 Vite 代理！
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return `http://${hostname}:3007/api/v1`;  // ⚠️ 问题在这里
    }

    return `${window.location.origin}/api/v1`;
  }
};
```

**为什么会导致 404？**

```
当在 localhost:8005 或 localhost:8006 访问时：

标准做法（使用代理）：
  Frontend/Client
       ↓ (请求 /api/...)
  Vite 代理拦截
       ↓ (转发到 http://127.0.0.1:3007/api/...)
  Backend
       ↓ (处理请求)
  返回结果

当前做法（直接调用）：
  Frontend/Client
       ↓ (请求 http://127.0.0.1:3007/api/v1/...)
  跳过 Vite 代理
       ↓ (直接访问 Backend)
  CORS 跨域 + 404 错误
       ↓ (因为 apiClient 会自动添加 /api/v1)
  失败

问题：共有两个 /api/v1：
  1. 在 getApiBaseUrl() 中返回的 /api/v1
  2. 在 auth-config.ts 中端点已经有 /api/v1

导致重复：
  http://localhost:3007/api/v1 + /auth/login
  = http://localhost:3007/api/v1/api/v1/auth/login  ❌ 错误！
```

**状态**: 🔴 配置错误 - 需要修复

---

## 🔧 修复方案：遵循标准三层架构

### 方案A：使用 Vite 代理（推荐 ✓）

这是标准做法，适合开发和测试环境。

#### 第一步：修改 auth-config.ts

使用**相对路径**而不是绝对 URL，让 Vite 代理处理：

```typescript
// shared/auth-config.ts - 修复后

export const getApiBaseUrl = (): string => {
  if (typeof window !== 'undefined') {
    // 开发环境：使用相对路径，Vite 代理会拦截 /api
    const hostname = window.location.hostname;

    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return '/api/v1';  // ✓ 使用相对路径，Vite 代理会转发到 :3007
    }

    // 生产环境：使用完整 URL（Nginx 会处理）
    return `${window.location.origin}/api/v1`;
  } else {
    // Node.js 环境
    return '/api/v1';
  }
};
```

**结果**：
```
Frontend/Client 请求：
  1. axios.get('/api/v1/auth/login')
  2. Vite 代理拦截 /api
  3. 转发到 http://127.0.0.1:3007/api/v1/auth/login
  4. ✓ Backend 正确处理
```

#### 第二步：确保 apiClient 配置正确

```typescript
// shared/auth.ts

const config = USER_AUTH_CONFIG;

// axios 创建时的 baseURL 应该是相对路径或空
this.apiClient = axios.create({
  baseURL: config.apiBaseUrl,  // '/api/v1' 或完整 URL
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 10000
});
```

**这样工作流程是**：
```
axios.post('/api/v1/auth/login', {...})
  ↓
Vite 代理拦截 /api 前缀
  ↓
转发到 http://127.0.0.1:3007/api/v1/auth/login
  ↓
Backend 接收完整路径 /api/v1/auth/login
  ↓
✓ 成功
```

---

### 方案B：API 地址动态配置（生产环境）

对于生产环境，使用 Nginx 反向代理。

#### Nginx 配置

```nginx
# nginx.conf

upstream backend {
    server 127.0.0.1:3007 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name localhost;

    # API 代理
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Frontend 应用
    location / {
        root /var/www/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
}
```

#### Frontend/Client 配置

```typescript
// shared/auth-config.ts - 生产环境

export const getApiBaseUrl = (): string => {
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;

    // 开发环境
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      // 选项1：使用相对路径（Vite 代理）
      if (import.meta.env.DEV) {
        return '/api/v1';
      }
      // 选项2：直接访问 Backend（有 CORS）
      return 'http://localhost:3007/api/v1';
    }

    // 生产环境：使用相对路径（Nginx 处理）
    return '/api/v1';
  }
};
```

---

## 📊 三种部署模式对比

### 模式1：开发环境（Vite 代理）✓ 推荐

```
Frontend:8006 ─┐
               ├─→ Vite 代理 (/api → :3007) ─→ Backend:3007
Client:8005  ─┘

配置：
✓ Vite 配置代理
✓ auth-config.ts 返回 /api/v1
✓ 无跨域问题
✓ CORS 可选

命令：
npm run dev
```

### 模式2：生产环境（Nginx）✓ 标准

```
Frontend
Client     ─→ Nginx (反向代理) ─→ Backend
         :80  └─ /api/ → :3007  :3007

配置：
✓ Nginx 配置反向代理
✓ auth-config.ts 返回 /api/v1
✓ CORS 可选（Nginx 处理）
✓ 单一入口

命令：
npm run build && nginx
```

### 模式3：直接调用（有 CORS）⚠️ 需要 CORS 配置

```
Frontend
Client     ─→ Backend (直接连接)
              ✓ 需要 CORS 配置

配置：
✓ auth-config.ts 返回 http://localhost:3007/api/v1
✓ Backend 启用 CORS
✓ 可能有跨域问题

只在调试时使用
```

---

## 🔍 诊断 404 的步骤

### 第一步：检查 Backend 是否运行

```bash
# 测试 Backend API
curl -v http://localhost:3007/api/v1/auth/login

# 预期结果：
# HTTP/1.1 422 Unprocessable Entity (缺少请求体)
# 或
# HTTP/1.1 200 OK (如果端点存在)

# 如果得到：
# Connection refused → Backend 未启动 ❌
# HTTP/1.1 404 Not Found → 路由不存在 ❌
```

### 第二步：检查 API 路由是否注册

```bash
# 查看 Backend API 文档
curl http://localhost:3007/docs

# 应该看到所有 /api/v1/* 路由
```

### 第三步：检查 Frontend/Client 代理配置

```bash
# 在 Frontend/Client 开发服务器开启的状态下
curl -v http://localhost:8005/api/v1/auth/login

# 应该看到 Vite 代理日志：
# [vite] POST /api/v1/auth/login 422
# 或代理转发的证据
```

### 第四步：检查 JavaScript 控制台

```javascript
// 在浏览器控制台运行
fetch('/api/v1/auth/login', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({username: 'test', password: 'test'})
})
.then(r => r.json())
.then(console.log)

// 预期：
// ✓ 收到 422 或其他 HTTP 响应（不是 404）
// ❌ 404 Not Found → 路由未注册或地址错误
// ❌ CORS error → CORS 配置有问题
```

### 第五步：检查网络标签

```
浏览器开发者工具 → Network 标签：

✓ 正确：
  请求地址：http://localhost:8005/api/v1/auth/login
  状态：422 (Unprocessable Entity)
  响应体：{"detail": [{"loc": [...], "msg": "..."}]}

❌ 错误1：
  请求地址：http://localhost:3007/api/v1/auth/login
  状态：404 或 CORS error
  原因：绕过了 Vite 代理

❌ 错误2：
  请求地址：http://localhost:8005/api/v1/api/v1/auth/login
  状态：404
  原因：路径重复
```

---

## 📋 完整修复清单

### Backend 端

- [x] 启动 Backend 服务在 3007 端口
- [x] 确保 API 前缀是 `/api/v1`
- [x] 数据库连接正确
- [x] CORS 配置包含 localhost:8005 和 localhost:8006

### Frontend/Client 共享配置

- [ ] **修改 shared/auth-config.ts**
  - [ ] `getApiBaseUrl()` 在开发环境返回 `/api/v1`（而不是完整 URL）
  - [ ] 在生产环境返回 `/api/v1`（Nginx 处理）

- [ ] 确认 apiClient 的 baseURL 是正确的

### Frontend (8006)

- [x] Vite 配置代理 `/api` → `http://127.0.0.1:3007`
- [x] 启动在 8006 端口

### Client (8005)

- [x] Vite 配置代理 `/api` → `http://127.0.0.1:3007`
- [x] 启动在 8005 端口

### 测试

- [ ] 启动所有三个服务
- [ ] 访问 http://localhost:8005，打开开发者工具 Network 标签
- [ ] 尝试登录，观察请求 URL 和响应
- [ ] 确认请求地址是 http://localhost:8005/api/v1/* 而不是 http://localhost:3007/api/v1/*
- [ ] 确认响应不是 404 或 CORS 错误

---

## 🔑 关键要点总结

### 标准三层架构

```
数据库层
  ↓ SQL
API 服务层 (Backend:3007)
  ↓ HTTP REST API (/api/v1/*)
前端应用层 (Frontend:8006, Client:8005)
  ↓ Vite 代理或 Nginx
Backend
  ↓ SQL
Database
```

### 开发环境请求流程

```
1. Frontend/Client 发起请求
   fetch('/api/v1/auth/login')

2. Vite 代理拦截 /api 前缀
   → 转发到 http://127.0.0.1:3007/api/v1/auth/login

3. Backend 接收完整路径
   → @router.post('/auth/login')

4. 返回响应
   ✓ 成功
```

### 配置要点

| 配置项 | 应该设置为 | 为什么 |
|--------|---------|--------|
| auth-config.ts getApiBaseUrl() | `/api/v1` | 让 Vite 代理处理 |
| Frontend vite.config.ts 代理 | `/api` → `:3007` | 转发 API 请求 |
| Client vite.config.ts 代理 | `/api` → `:3007` | 转发 API 请求 |
| Backend CORS | localhost:8005, 8006 | 允许跨域请求 |
| Backend API 前缀 | `/api/v1` | 统一路由前缀 |

---

## ✨ 推荐最佳实践

### ✓ Do（应该做）

```typescript
// auth-config.ts - 开发环境
export const getApiBaseUrl = (): string => {
  if (typeof window !== 'undefined') {
    return '/api/v1';  // 相对路径，让代理处理
  }
  return '/api/v1';
};
```

```typescript
// vite.config.ts - 代理配置
proxy: {
  '/api': {
    target: 'http://127.0.0.1:3007',
    changeOrigin: true,
    secure: false
  }
}
```

```bash
# 启动顺序
1. python -m uvicorn app.main:app --port 3007  # Backend
2. npm run dev  # Frontend (8006)
3. npm run dev  # Client (8005) - 在不同终端
```

### ✗ Don't（不应该做）

```typescript
// ❌ 不要这样做
export const getApiBaseUrl = (): string => {
  return 'http://localhost:3007/api/v1';  // 完整 URL，绕过代理
};
```

```typescript
// ❌ 不要这样做
axios.create({
  baseURL: 'http://localhost:3007/api/v1',  // 绝对 URL，跨域问题
})
```

```bash
# ❌ 不要混用
// shared/auth-config.ts 返回 http://localhost:3007/api/v1
// vite.config.ts 配置代理 /api → :3007
// 这样会导致路径混乱
```

---

**最后更新**: 2025-11-12
**架构版本**: v2.7.3
**推荐模式**: Vite 代理（开发）+ Nginx 反向代理（生产）
