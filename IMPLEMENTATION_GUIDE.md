# 三层架构实施与验证指南

## 🎯 系统架构标准流程

```
┌─────────────────────────────────────────────────────────────┐
│                  数据库初始化和连接                           │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│ 第一步：初始化数据库                                          │
│  ├─ 创建 MySQL 数据库：stock_analysis_dev                   │
│  ├─ 执行 init.sql 创建所有表                                │
│  ├─ 执行 init_database.py 导入初始数据                      │
│  │  ├─ 创建管理员账户：admin / admin123                    │
│  │  ├─ 创建测试用户：fullaccess_user / fullaccess123      │
│  │  ├─ 创建支付套餐                                         │
│  │  └─ ... 其他初始数据                                    │
│  └─ ✓ 完成                                                  │
│                                                               │
│ 第二步：启动 Backend 服务                                     │
│  ├─ 启动命令：python -m uvicorn app.main:app --port 3007   │
│  ├─ 端口：3007                                              │
│  ├─ API 前缀：/api/v1                                       │
│  ├─ 数据库连接：MySQL stock_analysis_dev                   │
│  └─ ✓ 完成                                                  │
│                                                               │
│ 第三步：启动 Frontend/Client 应用                            │
│  ├─ 启动 Frontend：npm run dev (端口 8006)                  │
│  ├─ 启动 Client：npm run dev (端口 8005)                    │
│  ├─ Vite 代理：/api → http://127.0.0.1:3007               │
│  └─ ✓ 完成                                                  │
│                                                               │
│ 第四步：验证请求流程                                         │
│  ├─ Browser: localhost:8005 (或 :8006)                     │
│  ├─ Request: /api/v1/auth/login                            │
│  ├─ Vite Proxy: 拦截 /api → 转发到 :3007                 │
│  ├─ Backend: 接收 /api/v1/auth/login                       │
│  └─ ✓ 成功                                                  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 完整实施步骤

### 第一阶段：数据库设置

#### 步骤 1.1：检查 MySQL 是否运行

```bash
# macOS
brew services start mysql

# 或使用 Docker
docker run -d \
  --name mysql \
  -e MYSQL_ROOT_PASSWORD=Pp123456 \
  -p 3306:3306 \
  mysql:8.0

# 验证连接
mysql -u root -pPp123456 -h 127.0.0.1 -P 3306
```

#### 步骤 1.2：初始化数据库

```bash
# 方法1：使用 Python 脚本（推荐）
cd backend
python init_database.py

# 输出示例：
# 连接到数据库...
# 创建表...
# 插入初始数据...
# ✓ 数据库初始化成功

# 方法2：使用 Shell 脚本
cd scripts/database
bash init_database.sh \
  --host 127.0.0.1 \
  --port 3306 \
  --user root \
  --password Pp123456 \
  --database stock_analysis_dev
```

#### 步骤 1.3：验证数据库

```bash
# 连接到数据库
mysql -u root -pPp123456

# 查看数据库
SHOW DATABASES;
# 应该看到：stock_analysis_dev

USE stock_analysis_dev;

# 查看表
SHOW TABLES;
# 应该看到：users, concepts, stocks, payment_orders 等

# 验证初始数据
SELECT * FROM users;
# 应该看到：admin, fullaccess_user 等
```

---

### 第二阶段：Backend 启动

#### 步骤 2.1：检查环境配置

```bash
cd backend

# 查看 .env 文件配置
cat .env

# 应该包含：
# DATABASE_HOST=127.0.0.1
# DATABASE_PORT=3306
# DATABASE_USER=root
# DATABASE_PASSWORD=Pp123456
# DATABASE_NAME=stock_analysis_dev
```

#### 步骤 2.2：安装依赖

```bash
# 如果还没有安装
pip install -r requirements.txt

# 或使用 poetry
poetry install
```

#### 步骤 2.3：启动 Backend 服务

```bash
# 开发模式（自动重载）
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 3007

# 输出示例：
# INFO:     Uvicorn running on http://0.0.0.0:3007
# INFO:     Application startup complete
```

#### 步骤 2.4：验证 Backend API

在另一个终端，测试 API：

```bash
# 测试登录端点
curl -X POST http://localhost:3007/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 预期响应（缺少密码）：
# {"access_token":"eyJ...","token_type":"bearer"}

# 查看 API 文档
curl http://localhost:3007/docs

# 或在浏览器打开：
# http://localhost:3007/docs
```

---

### 第三阶段：Frontend 应用启动

#### 步骤 3.1：安装依赖

```bash
cd frontend

npm install --legacy-peer-deps

# 或使用 yarn
yarn install
```

#### 步骤 3.2：验证 Vite 代理配置

```bash
# 查看 vite.config.ts
cat vite.config.ts | grep -A 10 "proxy:"

# 应该包含：
# proxy: {
#   '/api': {
#     target: 'http://127.0.0.1:3007',
#     changeOrigin: true,
#     secure: false
#   }
# }
```

#### 步骤 3.3：启动 Frontend

```bash
# 开发模式
npm run dev

# 输出示例：
# VITE v7.2.2 ready in 245 ms
# ➜  Local:   http://localhost:8006
# ➜  press h to show help
```

#### 步骤 3.4：验证 Frontend

在浏览器打开 http://localhost:8006：

```javascript
// 在浏览器控制台，测试 API 调用
fetch('/api/v1/auth/login', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    username: 'admin',
    password: 'admin123'
  })
})
.then(r => r.json())
.then(data => console.log('✓ 成功:', data))
.catch(err => console.log('❌ 错误:', err))
```

---

### 第四阶段：Client 应用启动

#### 步骤 4.1：安装依赖

```bash
cd client

npm install --legacy-peer-deps
```

#### 步骤 4.2：启动 Client

```bash
npm run dev

# 输出示例：
# VITE v7.2.2 ready in 156 ms
# ➜  Local:   http://localhost:8005
```

#### 步骤 4.3：验证 Client

在浏览器打开 http://localhost:8005 并查看 Network 标签：

```
正确的请求应该是：
  请求 URL：http://localhost:8005/api/v1/auth/login
  请求方法：POST
  状态码：422 或其他（不是 404）
  代理作用：/api 被 Vite 代理拦截，转发到 :3007
```

---

## 🔍 验证清单

### 验证1：数据库连接

```bash
# 检查数据库是否可访问
mysql -u root -pPp123456 -h 127.0.0.1 -P 3306 -e "SELECT 1"

# 预期输出：
# +---+
# | 1 |
# +---+
```

**应该看到**：✓ 连接成功
**不应该看到**：❌ Connection refused, ❌ Access denied

---

### 验证2：Backend API 是否运行

```bash
# 测试 Backend 服务
curl -s http://localhost:3007/docs | grep -q "title" && echo "✓ Backend 运行中" || echo "❌ Backend 未运行"

# 测试具体端点
curl -s -X GET http://localhost:3007/api/v1/auth/me \
  -H "Authorization: Bearer invalid" | grep -q "detail" && echo "✓ API 响应正常"
```

**应该看到**：✓ Backend 运行中
**不应该看到**：❌ Connection refused

---

### 验证3：Vite 代理配置

在浏览器开发者工具 Network 标签，访问 http://localhost:8005 并登录：

```
正确的流程：
1. 请求 URL：http://localhost:8005/api/v1/auth/login
   ✓ 不是 http://localhost:3007/api/v1/auth/login（这是错的）

2. 请求头：
   ✓ 有 Content-Type: application/json
   ✓ 可能有 Authorization: Bearer (登录后)

3. 响应状态：
   ✓ 200 (成功)
   ✓ 422 (验证错误 - 缺少字段)
   ✗ 404 (路由不存在 - 错误)
   ✗ CORS error (跨域 - 配置错误)

4. 响应体：
   ✓ JSON 格式：{"access_token": "...", "token_type": "bearer"}
   ✓ 错误格式：{"detail": [{"loc": [...], "msg": "..."}]}
```

---

### 验证4：API 路由是否正确

```bash
# 列出所有可用的 API 端点
curl -s http://localhost:3007/docs | \
  grep -o '"path": "[^"]*"' | \
  sort -u

# 应该包含：
# "path": "/api/v1/auth/login"
# "path": "/api/v1/auth/register"
# "path": "/api/v1/concepts/..."
# 等等
```

---

### 验证5：完整登录流程

```bash
# 1. 启动 Backend
cd backend && python -m uvicorn app.main:app --port 3007 &

# 2. 启动 Frontend
cd frontend && npm run dev &

# 3. 等待服务启动（约 5 秒）
sleep 5

# 4. 测试登录
curl -X POST http://localhost:8006/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  -s | jq .

# 预期响应：
# {
#   "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
#   "token_type": "bearer"
# }
```

**应该看到**：✓ JWT token
**不应该看到**：❌ 404, ❌ CORS error, ❌ Connection refused

---

## 🆘 故障排除

### 问题1：504 错误或连接超时

```
症状：访问 localhost:8005 显示 504 错误

原因可能：
1. Backend 未启动
2. Vite 代理配置错误
3. 端口被占用

解决：
```bash
# 1. 检查 Backend 是否运行
lsof -i :3007
# 如果没有输出，说明 Backend 未运行

# 2. 检查 Vite 代理配置
cat client/vite.config.ts | grep -A 5 "proxy:"
# 应该有 'http://127.0.0.1:3007'

# 3. 检查端口是否被占用
lsof -i :8005
lsof -i :8006

# 4. 重启所有服务
./stop.sh
./start.sh
```

---

### 问题2：404 Not Found

```
症状：API 请求返回 404

原因可能：
1. API 路由不存在
2. 路径错误（重复 /api/v1）
3. Backend 未启动

检查步骤：
```

```bash
# 1. 查看请求 URL（在浏览器 Network 标签）
#    应该是：http://localhost:8005/api/v1/auth/login
#    不应该是：http://localhost:3007/api/v1/auth/login
#    不应该是：http://localhost:8005/api/v1/api/v1/auth/login

# 2. 检查 Backend 是否有该路由
curl http://localhost:3007/docs

# 3. 直接测试 Backend
curl http://localhost:3007/api/v1/auth/me

# 4. 检查 auth-config.ts
cat shared/auth-config.ts | grep "getApiBaseUrl" -A 20
# 应该返回 '/api/v1' 而不是 'http://localhost:3007/api/v1'
```

---

### 问题3：CORS 错误

```
症状：浏览器显示 CORS error

原因可能：
1. Backend CORS 配置不正确
2. 绕过了 Vite 代理

解决：
```

```bash
# 1. 检查 Backend CORS 配置
grep -A 10 "allow_origins" backend/app/main.py

# 应该包含：
# "http://localhost:8005"
# "http://127.0.0.1:8005"
# "http://localhost:8006"
# "http://127.0.0.1:8006"

# 2. 检查是否使用了 Vite 代理
# 在浏览器 Network 标签，请求 URL 应该是 localhost:8005/8006
# 不应该是 localhost:3007

# 3. 检查 auth-config.ts 是否返回完整 URL
grep "return.*3007" shared/auth-config.ts
# 如果返回 http://localhost:3007/api/v1，这是错的
# 应该返回 /api/v1
```

---

### 问题4：数据库连接失败

```
症状：Backend 启动时显示数据库连接错误

原因可能：
1. MySQL 未运行
2. 连接配置错误
3. 数据库不存在

解决：
```

```bash
# 1. 启动 MySQL
brew services start mysql

# 2. 检查连接
mysql -u root -pPp123456 -h 127.0.0.1 -P 3306

# 3. 检查 .env 配置
cat backend/.env
# 应该包含：
# DATABASE_HOST=127.0.0.1
# DATABASE_PORT=3306
# DATABASE_USER=root
# DATABASE_PASSWORD=Pp123456
# DATABASE_NAME=stock_analysis_dev

# 4. 初始化数据库
python backend/init_database.py
```

---

## 📊 快速启动脚本

### 一键启动所有服务

```bash
#!/bin/bash

# 启动 MySQL
echo "启动 MySQL..."
brew services start mysql
sleep 2

# 启动 Backend
echo "启动 Backend..."
cd backend
python -m uvicorn app.main:app --reload --port 3007 > ../logs/backend.log 2>&1 &
sleep 3

# 启动 Frontend
echo "启动 Frontend..."
cd ../frontend
npm run dev > ../logs/frontend.log 2>&1 &
sleep 3

# 启动 Client
echo "启动 Client..."
cd ../client
npm run dev > ../logs/client.log 2>&1 &

echo ""
echo "✓ 所有服务已启动"
echo ""
echo "访问地址："
echo "  Backend API:  http://localhost:3007"
echo "  API 文档：    http://localhost:3007/docs"
echo "  Frontend:     http://localhost:8006 (admin/admin123)"
echo "  Client:       http://localhost:8005 (fullaccess_user/fullaccess123)"
echo ""
echo "查看日志："
echo "  tail -f logs/backend.log"
echo "  tail -f logs/frontend.log"
echo "  tail -f logs/client.log"
```

### 一键停止所有服务

```bash
#!/bin/bash

echo "停止所有服务..."
pkill -f "uvicorn app.main:app"
pkill -f "vite"
echo "✓ 所有服务已停止"
```

---

## ✅ 最终验证清单

启动所有服务后，逐一验证：

- [ ] **数据库**
  - [ ] MySQL 运行在 3306 端口
  - [ ] 可以连接到 stock_analysis_dev 数据库
  - [ ] 表结构完整（users, concepts 等）
  - [ ] 初始数据存在（admin, fullaccess_user）

- [ ] **Backend**
  - [ ] 运行在 3007 端口
  - [ ] API 文档可访问：http://localhost:3007/docs
  - [ ] 数据库连接成功
  - [ ] 所有路由注册正确

- [ ] **Frontend**
  - [ ] 运行在 8006 端口
  - [ ] 可以访问：http://localhost:8006
  - [ ] Vite 代理工作正常
  - [ ] 可以登录（admin/admin123）

- [ ] **Client**
  - [ ] 运行在 8005 端口
  - [ ] 可以访问：http://localhost:8005
  - [ ] Vite 代理工作正常
  - [ ] 可以登录（fullaccess_user/fullaccess123）

- [ ] **API 调用**
  - [ ] 请求 URL 正确：http://localhost:8005/api/v1/*
  - [ ] 响应状态正常：200 或 422（不是 404）
  - [ ] 没有 CORS 错误
  - [ ] 数据返回正确

---

## 🎓 核心概念回顾

### 标准三层架构

```
Layer 1: Database (MySQL)
    ↓ SQL
Layer 2: API Server (Backend:3007, /api/v1/*)
    ↓ REST API
Layer 3: Front Apps (Frontend:8006, Client:8005)
    ↓ Vite Proxy (/api → :3007)
Backend
    ↓ SQL
Database
```

### 请求流程

```
Browser (localhost:8005)
  ↓ 请求 /api/v1/auth/login
Vite Proxy
  ↓ 拦截 /api，转发到 :3007
Backend (localhost:3007)
  ↓ 接收 /api/v1/auth/login，查询数据库
Database (MySQL)
  ↓ 返回数据
Backend
  ↓ 返回 JSON 响应
Vite Proxy
  ↓ 返回给浏览器
Browser
  ↓ 显示结果
```

### 关键要点

1. **开发环境**：使用 Vite 代理，API 基础 URL 应该是 `/api/v1`
2. **生产环境**：使用 Nginx 反向代理，API 基础 URL 也是 `/api/v1`
3. **避免的做法**：不要在前端直接返回完整 URL（如 `http://localhost:3007/api/v1`），这会绕过代理导致跨域问题
4. **调试方法**：使用浏览器 Network 标签检查请求 URL 和响应状态

---

**最后更新**：2025-11-12
**版本**：v2.7.3
**架构模式**：标准三层架构 + Vite 代理（开发）/ Nginx 反向代理（生产）
