# 系统架构快速参考指南

## 🎯 三系统一览表

### 系统对比

| 特性 | Backend | Client | Frontend |
|------|---------|--------|----------|
| **端口** | 3007 | 8005 | 8006 |
| **用户** | 系统服务 | 普通用户 | 管理员 |
| **框架** | FastAPI | React + Vite | React + Vite |
| **认证** | JWT | JWT | JWT |
| **数据库** | MySQL | - | - |
| **缓存** | Redis | LocalStorage | LocalStorage |
| **主要功能** | 业务逻辑、API、数据处理 | 用户交互、数据展示 | 系统管理、数据导入 |

---

## 🔗 系统间数据流

```
用户 → Client (8005)
            ↓ HTTP API
         Backend (3007)
            ↓ SQL
         MySQL 数据库

管理员 → Frontend (8006)
            ↓ HTTP API
         Backend (3007)
            ↓ SQL
         MySQL 数据库
```

---

## 📱 核心功能清单

### Backend 提供的核心功能

| 功能分类 | 具体功能 | API 前缀 |
|---------|--------|--------|
| 认证 | 用户/管理员登录、token管理 | `/auth`, `/admin-auth` |
| 用户 | 用户信息、权限管理 | `/admin/client-users` |
| 数据 | 数据导入、文件处理 | `/data`, `/universal-import` |
| 概念 | 概念查询、分析计算 | `/concepts`, `/concept-analysis` |
| 股票 | 股票查询、搜索 | `/stocks`, `/stock-data` |
| 分析 | 每日报告、图表数据 | `/daily-analysis`, `/chart-data` |
| 支付 | 订单管理、微信支付 | `/payment`, `/mock` |
| 管理 | 用户管理、套餐管理 | `/admin/` |

### Client 提供的用户功能

| 页面 | 功能 | 关键 API |
|------|------|--------|
| AuthPage | 登录/注册 | `/auth/login`, `/auth/register` |
| AnalysisPage | 概念热度、股票排行 | `/concept-analysis/*` |
| MembershipPage | 会员升级、套餐选择 | `/payment/orders`, `/payment/packages` |
| PaymentHistoryPage | 支付记录查询 | `/payment/orders` |

### Frontend 提供的管理功能

| 页面 | 功能 | 关键 API |
|------|------|--------|
| LoginPage | 管理员登录 | `/admin-auth/login` |
| Dashboard | 系统概览、统计 | `/admin/*` |
| DataImportPage | 数据导入 | `/data/import` |
| UserManagement | 用户管理 | `/admin/users` |
| PackageManagement | 套餐管理 | `/admin/packages` |
| PaymentPage | 支付审核 | `/admin/orders` |

---

## 🗂️ 文件位置速查

### Backend 文件结构

```
backend/app/
├── api/api_v1/
│   ├── endpoints/          # 路由处理 (15+ 模块)
│   └── api.py             # 路由汇总
├── core/
│   ├── security.py        # 密码加密、JWT
│   ├── database.py        # 数据库连接
│   ├── config.py          # 配置管理
│   └── exception_handlers.py
├── models.py              # 数据模型
├── services/              # 业务逻辑
├── middleware/            # 中间件
└── main.py               # 应用入口
```

### Client 文件结构

```
client/src/
├── pages/                 # 页面组件
│   ├── AuthPage.tsx
│   ├── AnalysisPage.tsx
│   └── MembershipPage.tsx
├── components/            # UI 组件
├── services/             # API 调用
│   ├── conceptAnalysisApi.ts
│   └── dailyAnalysisApi.ts
├── utils/auth.ts         # 认证工具
└── App.tsx              # 主应用
```

### Frontend 文件结构

```
frontend/src/
├── components/           # 管理页面
│   ├── AdminLayout.tsx
│   ├── DataImportPage.tsx
│   ├── AdminManagement.tsx
│   └── ... (13+ 页面)
├── contexts/            # 认证上下文
└── App.tsx             # 主应用
```

---

## 🔑 关键技术点

### 认证机制

```
密码 → Argon2 加密 → 存储
登录 → Argon2 验证 → 生成 JWT
请求 → Bearer Token → JWT 验证 → 放行/拒绝
```

### API 基础 URL 配置

```typescript
// 在 shared/auth-config.ts 中定义
const getApiBaseUrl = () => {
  // 开发环境: http://localhost:3007/api/v1
  // 生产环境: {domain}/api/v1
}
```

### 数据缓存策略

```
热数据 → Redis (1小时)
排行榜 → Redis (30分钟)
用户信息 → Redis (会话期间)
前端 → LocalStorage (离线支持)
```

---

## 📊 API 端点速查表

### 认证相关

```bash
POST   /api/v1/auth/login              # 用户登录
POST   /api/v1/auth/register           # 用户注册
POST   /api/v1/admin-auth/login        # 管理员登录
GET    /api/v1/auth/me                 # 获取当前用户
```

### 查询相关

```bash
GET    /api/v1/concept-analysis/concepts/innovation
GET    /api/v1/daily-analysis/concept-summaries
GET    /api/v1/chart-data/daily-hot-concepts
GET    /api/v1/stocks/{code}
```

### 管理相关

```bash
GET    /api/v1/admin/users             # 用户列表
PUT    /api/v1/admin/users/{id}        # 修改用户
GET    /api/v1/admin/packages          # 套餐列表
POST   /api/v1/data/import             # 文件上传
```

### 支付相关

```bash
POST   /api/v1/payment/orders          # 创建订单
GET    /api/v1/payment/orders          # 订单列表
POST   /api/v1/payment/callback        # 支付回调
```

---

## 🚀 常用命令速查

### 启动/停止

```bash
./start.sh                 # 启动所有服务
./stop.sh                  # 停止所有服务
./restart.sh               # 重启所有服务
./status.sh                # 查看状态
```

### 日志查看

```bash
tail -f logs/backend.log   # 后端日志
tail -f logs/client.log    # 客户端日志
tail -f logs/frontend.log  # 管理后台日志
tail -f logs/*.log         # 全部日志
```

### 开发模式

```bash
# Backend
cd backend
python -m uvicorn app.main:app --reload --port 3007

# Client
cd client
npm run dev

# Frontend
cd frontend
npm run dev
```

---

## 🔍 常见错误排查

### 404 错误

```
问题: /concept-analysis/concepts/innovation 404
原因: API 基础 URL 缺少 /api/v1
解决: 检查 shared/auth-config.ts 中的 getApiBaseUrl()
```

### 500 认证错误

```
问题: POST /auth/login 返回 500
原因: 密码哈希算法不匹配
解决: 确保使用 argon2 算法
```

### 跨域错误

```
问题: CORS error
原因: 请求地址不在 CORS 白名单
解决: 检查 backend/app/main.py 的 allow_origins 配置
```

### 端口占用

```
问题: Address already in use
原因: 端口被其他服务占用
解决:
  lsof -i :3007    # 查看占用进程
  kill -9 {pid}    # 杀死进程
```

---

## 📝 数据库表清单

### 关键表

| 表名 | 说明 | 关键字段 |
|------|------|--------|
| users | 用户表 | id, username, email, membership_type |
| concepts | 概念表 | id, name, heat_value, stock_count |
| stocks | 股票表 | id, code, name, price |
| concept_stocks | 关联表 | concept_id, stock_id, rank |
| payment_orders | 订单表 | id, user_id, amount, status |
| user_packages | 套餐表 | user_id, package_id, expires_at |
| import_records | 导入表 | id, file_name, status, created_at |

---

## 🔐 安全清单

- ✅ 密码使用 Argon2 加密（无长度限制）
- ✅ API 使用 JWT 认证
- ✅ 请求需要 Authorization header
- ✅ 启用了 CORS 跨域控制
- ✅ 速率限制 200请求/60秒
- ✅ SQL 注入防护 (SQLAlchemy ORM)
- ✅ 敏感数据加密存储
- ✅ 请求日志记录

---

## 🎓 学习路径

### 快速入门 (30分钟)

```
1. 读 README.md 了解项目
2. 运行 ./start.sh 启动系统
3. 访问 http://localhost:8005 (Client)
4. 登录试用: fullaccess_user / fullaccess123
```

### 深入学习 (2小时)

```
1. 读 SYSTEM_ARCHITECTURE.md 了解架构
2. 查看 API 文档: http://localhost:3007/docs
3. 检查代码: backend/app/api/api_v1/
4. 学习认证: shared/auth-config.ts
```

### 开发贡献 (1天)

```
1. 修改代码
2. 测试变更
3. 查看日志: tail -f logs/*.log
4. 理解 SYSTEM_FEATURES_MATRIX.md
5. 按照新功能清单添加代码
```

---

## 📞 快速参考链接

| 资源 | 地址 |
|------|------|
| 系统主文档 | SYSTEM_ARCHITECTURE.md |
| 功能矩阵 | SYSTEM_FEATURES_MATRIX.md |
| 快速开始 | QUICKSTART.md |
| 故障排除 | TROUBLESHOOTING.md |
| API 文档 | http://localhost:3007/docs |
| 开发进度 | DEVELOPMENT_PROGRESS.md |

---

## 💡 关键概念

### Token 生命周期

```
1. 用户登录 → 获得 access_token (24小时有效)
2. 存储在 LocalStorage
3. 每次请求自动添加 Authorization header
4. 后端验证 token 有效性
5. Token 过期 → 跳转登录页面
6. 重新登录 → 获得新 token
```

### 数据导入流程

```
1. 上传文件 (TXT/TTV/EEE格式)
2. Backend 解析和验证
3. 检测覆盖冲突
4. 异步导入到数据库
5. 计算概念热度
6. 更新缓存
```

### 概念热度计算

```
热度值 = f(
  股票数量,
  交易量,
  创新高天数,
  资金流向,
  阅读次数
)

更新频率: 每日计算一次
缓存时间: 1小时
```

---

## 🔄 版本更新说明

| 版本 | 日期 | 关键改进 |
|------|------|--------|
| v2.7.3 | 2025-11 | 修复 API 路由, 切换密码哈希为 Argon2 |
| v2.7.0 | 2025-09 | 项目初始化, 三系统架构完成 |

---

**最后更新**: 2025-11-12
**维护者**: Team
**状态**: 🟢 生产环境就绪
