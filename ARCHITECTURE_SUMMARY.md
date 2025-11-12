# 系统架构验证与修复总结

## 📌 问题诊断

你指出的问题是正确的。系统应该遵循**标准三层架构**：

### 标准模式
```
┌──────────────┐
│  数据库      │ ← MySQL (stock_analysis_dev)
└──────┬───────┘
       │ SQL
┌──────▼───────┐
│  Backend     │ ← FastAPI 服务器 (端口 3007, /api/v1 前缀)
└──────┬───────┘
       │ REST API
┌──────▼───────────────────┐
│ Frontend  │  Client       │ ← React 应用 (Vite 代理)
│ (8006)    │  (8005)       │
└───────────┴───────────────┘
```

### 当前遇到的问题
系统总是出现 404 错误，原因是 **API 地址配置不正确**。

**根本原因**：
- `shared/auth-config.ts` 中的 `getApiBaseUrl()` 返回完整 URL：`http://localhost:3007/api/v1`
- 这导致前端直接访问 Backend，绕过了 Vite 代理
- 结果：跨域(CORS)错误或 404 错误

---

## ✅ 已修复的问题

### 修复内容

在 `shared/auth-config.ts` 中修改了 `getApiBaseUrl()` 函数：

**之前（错误）**：
```typescript
if (hostname === 'localhost' || hostname === '127.0.0.1') {
  return `http://${hostname}:3007/api/v1`;  // ❌ 完整 URL，绕过代理
}
```

**之后（正确）**：
```typescript
if (isDev) {
  return '/api/v1';  // ✓ 相对路径，让 Vite 代理处理
}
return '/api/v1';  // ✓ 生产环境也用相对路径，Nginx 处理
```

### 为什么这样修复

```
修复前的流程（有问题）：
Frontend/Client (8005/8006)
  ↓ 请求 http://localhost:3007/api/v1/auth/login
绕过 Vite 代理
  ↓ 直接发送到 Backend (跨域请求)
CORS 错误或 404
  ❌ 失败

修复后的流程（正确）：
Frontend/Client (8005/8006)
  ↓ 请求 /api/v1/auth/login
Vite 代理拦截
  ↓ 转发到 http://127.0.0.1:3007/api/v1/auth/login
Backend 接收
  ↓ 处理请求，查询数据库
Database
  ↓ 返回结果
Frontend/Client
  ✓ 成功
```

---

## 🔄 完整的数据流

### 开发环境（推荐）

```
1. Frontend/Client 发起请求
   fetch('/api/v1/auth/login', {...})

2. Vite 开发服务器（vite.config.ts 配置）
   proxy: {
     '/api': {
       target: 'http://127.0.0.1:3007',
       changeOrigin: true
     }
   }
   拦截 /api 前缀，转发请求

3. Backend (FastAPI)
   app.include_router(api_router, prefix="/api/v1")
   接收完整路径 /api/v1/auth/login
   处理请求，返回响应

4. 浏览器
   显示结果
```

### 生产环境

```
1. Frontend/Client 发起请求
   fetch('/api/v1/auth/login', {...})

2. Nginx 反向代理
   location /api/ {
     proxy_pass http://backend:3007;
   }
   拦截 /api 前缀，转发请求

3. Backend (FastAPI)
   接收完整路径 /api/v1/auth/login
   处理请求，返回响应

4. 浏览器
   显示结果
```

---

## 📊 系统配置确认清单

### ✓ 数据库层

- **文件位置**：`backend/init_database.py`, `scripts/database/init.sql`
- **数据库名称**：`stock_analysis_dev`
- **默认用户**：root
- **默认密码**：Pp123456
- **连接字符串**：`mysql+pymysql://root:Pp123456@127.0.0.1:3306/stock_analysis_dev`

### ✓ Backend 服务层

- **文件位置**：`backend/app/main.py`, `backend/app/core/config.py`
- **端口**：3007
- **主机**：0.0.0.0
- **API 前缀**：/api/v1
- **完整 API 地址**：http://localhost:3007/api/v1
- **数据库连接**：MySQL stock_analysis_dev

### ✓ Frontend/Client 应用层

- **Frontend 端口**：8006
- **Client 端口**：8005
- **Vite 代理配置**：`/api` → `http://127.0.0.1:3007`
- **API 基础 URL**：`/api/v1`（相对路径）

### ✓ 已修复项

- **文件**：`shared/auth-config.ts`
- **修复**：`getApiBaseUrl()` 返回相对路径 `/api/v1`
- **目的**：让 Vite 代理处理 API 请求，避免跨域和 404 错误

---

## 🚀 快速启动指南

### 步骤 1：初始化数据库

```bash
# 确保 MySQL 运行
brew services start mysql

# 初始化数据库和表
cd backend
python init_database.py
```

### 步骤 2：启动 Backend

```bash
cd backend
python -m uvicorn app.main:app --reload --port 3007
```

**预期输出**：
```
INFO:     Uvicorn running on http://0.0.0.0:3007
INFO:     Application startup complete
```

### 步骤 3：启动 Frontend

在新终端：
```bash
cd frontend
npm install --legacy-peer-deps  # 首次需要
npm run dev
```

**预期输出**：
```
VITE v7.2.2 ready in 245 ms
➜  Local:   http://localhost:8006
```

### 步骤 4：启动 Client

在新终端：
```bash
cd client
npm install --legacy-peer-deps  # 首次需要
npm run dev
```

**预期输出**：
```
VITE v7.2.2 ready in 156 ms
➜  Local:   http://localhost:8005
```

### 步骤 5：验证系统

在浏览器打开 http://localhost:8005 或 http://localhost:8006，尝试登录：

| 应用 | 地址 | 用户 | 密码 |
|------|------|------|------|
| Client | http://localhost:8005 | fullaccess_user | fullaccess123 |
| Frontend | http://localhost:8006 | admin | admin123 |

打开浏览器开发者工具 (Network 标签)，应该看到：
- ✓ 请求 URL：`http://localhost:8005/api/v1/auth/login`（不是 3007）
- ✓ 状态码：422（缺少字段）或 200（成功）
- ✓ 没有 404 或 CORS 错误

---

## 🔍 如何诊断 404 问题

### 方法 1：检查 Network 标签

在浏览器开发者工具的 Network 标签：

**错误的请求**（导致 404）：
```
请求 URL：http://localhost:3007/api/v1/auth/login
原因：绕过了 Vite 代理，直接访问 Backend
```

**正确的请求**（没有 404）：
```
请求 URL：http://localhost:8005/api/v1/auth/login
原因：经过 Vite 代理转发到 Backend
```

### 方法 2：查看浏览器控制台

```javascript
// 在浏览器控制台运行
console.log(window.location.origin);
// 输出：http://localhost:8005 (或 8006)

// 检查 API 基础 URL
fetch('/api/v1/auth/me')
  .then(r => r.status)
  .then(status => {
    if (status === 404) {
      console.log('❌ 404 错误 - 检查路由');
    } else {
      console.log('✓ API 响应 -', status);
    }
  })
```

### 方法 3：直接测试 Backend

```bash
# 测试 Backend API 是否正常
curl http://localhost:3007/api/v1/auth/me

# 预期响应（401 Unauthorized）：
# {"detail":"Not authenticated"}

# 如果 404，说明 Backend 路由未注册
# 如果连接超时，说明 Backend 未启动
```

---

## 💡 关键概念

### Vite 代理的作用

Vite 开发服务器的代理功能允许前端应用：
1. 使用**相对路径**访问 API
2. 在开发时转发到不同的后端地址
3. 避免跨域(CORS)问题

**配置示例**（已验证）：
```typescript
// frontend/vite.config.ts 和 client/vite.config.ts
server: {
  port: 8006, // 或 8005
  proxy: {
    '/api': {
      target: 'http://127.0.0.1:3007',  // Backend 地址
      changeOrigin: true,
      secure: false
    }
  }
}
```

### 为什么 getApiBaseUrl() 应该返回 `/api/v1`

1. **开发环境**：Vite 代理拦截 `/api`，转发到 Backend
2. **生产环境**：Nginx 反向代理拦截 `/api`，转发到 Backend
3. **优势**：前后端代码一致，无需根据环境修改

**对比**：
```typescript
// ❌ 错误做法（返回完整 URL）
return `http://localhost:3007/api/v1`;
// 问题：绕过代理，跨域请求，404 错误

// ✓ 正确做法（返回相对路径）
return '/api/v1';
// 优势：使用代理，无跨域问题，清晰的数据流
```

---

## 📚 参考文档

本项目已生成以下文档，供深入学习：

| 文档 | 用途 |
|------|------|
| `SYSTEM_ARCHITECTURE.md` | 系统完整架构说明 |
| `SYSTEM_FEATURES_MATRIX.md` | 功能与技术的对应关系 |
| `QUICK_REFERENCE.md` | 快速查询表 |
| `ARCHITECTURE_VALIDATION.md` | 架构验证详细指南 |
| `IMPLEMENTATION_GUIDE.md` | 分步实施和测试指南 |

---

## ✨ 总结

### 问题
系统出现 404 错误，原因是 API 配置不遵循标准三层架构。

### 解决方案
修改 `shared/auth-config.ts` 中的 `getApiBaseUrl()` 函数，返回相对路径 `/api/v1` 而不是完整 URL，让 Vite 代理（开发）或 Nginx 反向代理（生产）来处理 API 请求转发。

### 修复内容
```
文件：shared/auth-config.ts
函数：getApiBaseUrl()
改变：从 return `http://${hostname}:3007/api/v1` 改为 return '/api/v1'
结果：Vite 代理正确工作，API 请求不再出现 404 或 CORS 错误
```

### 验证
启动所有服务后，在浏览器 Network 标签查看：
- ✓ 请求 URL：`http://localhost:8005/api/v1/*` 或 `http://localhost:8006/api/v1/*`
- ✓ 响应状态：200（成功）或 422（验证错误），而不是 404
- ✓ 没有 CORS 错误

---

**修复时间**：2025-11-12
**修复版本**：v2.7.3
**架构模式**：标准三层架构 + 代理转发（Vite/Nginx）
**状态**：🟢 修复完成，系统就绪
