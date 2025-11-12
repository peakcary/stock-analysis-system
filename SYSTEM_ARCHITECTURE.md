# 股票分析系统架构完整梳理 v2.7.3

## 📌 系统概述

本项目是一个高性能的股票分析系统，包含三个独立的应用系统，分别为：
1. **Backend** - FastAPI 核心后端应用
2. **Client** - React 客户端应用
3. **Frontend** - React 管理后台应用

三个系统通过统一的 RESTful API 接口相互协作，共享业务逻辑和数据。

---

## 🏗️ 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户访问层                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │   Client App     │  │   Frontend App   │  │   API Docs   │  │
│  │  (8005 - 用户)   │  │ (8006 - 管理员)  │  │  (3007/docs) │  │
│  └────────┬─────────┘  └────────┬─────────┘  └──────────────┘  │
│           │                     │                                 │
└───────────┼─────────────────────┼─────────────────────────────────┘
            │                     │
            └─────────────┬───────┘
                          │ HTTP/CORS
            ┌─────────────▼───────────────┐
            │   Backend FastAPI Server    │
            │       (3007)                 │
            ├─────────────────────────────┤
            │  RESTful API 路由            │
            │  - 认证与授权               │
            │  - 数据查询与分析           │
            │  - 用户管理与支付           │
            │  - 文件导入与处理           │
            └──────────┬──────────────────┘
                       │
        ┌──────────────┼──────────────────┐
        │              │                   │
    ┌───▼────┐     ┌───▼────┐        ┌───▼────┐
    │ MySQL  │     │ Redis  │        │ 文件系统 │
    │ 8.0+   │     │ Cache  │        │(导入数据)│
    └────────┘     └────────┘        └────────┘
```

---

## 📊 后端系统 (Backend)

### 基本信息
- **端口**: 3007
- **框架**: FastAPI 0.104.1
- **数据库**: MySQL 8.0+
- **缓存**: Redis
- **认证**: JWT (python-jose)
- **密码加密**: Argon2
- **项目路径**: `/backend`

### API 路由结构

```
/api/v1/
├── /auth                    # 用户认证
│   ├── POST   /login       # 登录
│   ├── POST   /register    # 注册
│   ├── POST   /logout      # 登出
│   └── GET    /me          # 获取当前用户信息
│
├── /admin-auth             # 管理员认证
│   ├── POST   /login       # 管理员登录
│   ├── POST   /logout      # 管理员登出
│   ├── POST   /refresh     # 刷新token
│   └── GET    /me          # 获取管理员信息
│
├── /stocks                 # 个股查询
│   ├── GET    /list        # 股票列表
│   ├── GET    /{code}      # 单个股票详情
│   └── POST   /search      # 股票搜索
│
├── /concepts               # 概念管理
│   ├── GET    /list        # 概念列表
│   ├── GET    /{id}        # 概念详情
│   └── GET    /{id}/stocks # 概念关联股票
│
├── /concept-analysis       # 概念分析
│   ├── GET    /concepts/innovation              # 创新高概念
│   ├── GET    /concepts/{id}/ranking            # 概念排行
│   ├── GET    /convertible-bonds                # 可转债
│   ├── POST   /analysis/trigger                 # 触发分析
│   └── GET    /analysis/status                  # 分析状态
│
├── /daily-analysis         # 每日分析
│   ├── POST   /generate-analysis               # 生成分析
│   ├── GET    /concept-summaries               # 概念汇总
│   ├── GET    /concept-rankings                # 概念排名
│   ├── GET    /top-concepts                    # 热点概念
│   ├── GET    /concept-detail/{concept}        # 概念详情
│   └── GET    /analysis-status                 # 分析状态
│
├── /chart-data             # 图表数据
│   ├── GET    /concept/{id}/heat-trend         # 热度趋势
│   ├── GET    /daily-hot-concepts              # 每日热门
│   ├── GET    /concept/{id}/stock-distribution # 股票分布
│   ├── GET    /innovation-timeline             # 创新时间线
│   ├── GET    /convertible-bonds-analysis      # 可转债图表
│   ├── GET    /concept-comparison              # 概念对比
│   ├── GET    /market-overview                 # 市场概览
│   └── GET    /stock/{id}/concept-performance  # 概念表现
│
├── /payment                # 支付管理
│   ├── POST   /orders                  # 创建订单
│   ├── GET    /orders/{order_id}       # 订单详情
│   ├── GET    /orders                  # 订单列表
│   ├── POST   /callback                # 支付回调
│   └── GET    /packages                # 会员套餐
│
├── /data                   # 数据导入
│   ├── POST   /import                  # 上传文件
│   ├── GET    /import/status/{task_id} # 导入状态
│   └── GET    /import/history          # 导入历史
│
├── /admin                  # 管理员功能
│   ├── GET    /users                   # 用户列表
│   ├── PUT    /users/{user_id}         # 修改用户
│   ├── GET    /packages                # 套餐管理
│   ├── POST   /packages                # 创建套餐
│   ├── DELETE /packages/{id}           # 删除套餐
│   ├── GET    /orders                  # 订单管理
│   └── POST   /orders/{id}/process     # 处理订单
│
└── /system                 # 系统管理
    ├── GET    /status                  # 系统状态
    ├── GET    /health                  # 健康检查
    └── POST   /optimize                # 数据库优化
```

### 核心模块架构

#### 1. **认证模块** (`core/security.py`)
```python
功能:
  ✓ JWT token 生成与验证
  ✓ 密码哈希（Argon2）与验证
  ✓ Token 过期处理
  ✓ 用户身份验证

关键配置:
  - 密码加密: Argon2
  - Token 算法: HS256
  - Token 有效期: 24小时
  - 刷新阈值: 5分钟
  - 最大重试: 3次
```

#### 2. **数据库模块** (`core/database.py`)
```python
功能:
  ✓ SQLAlchemy ORM
  ✓ 数据库连接管理
  ✓ 会话管理
  ✓ 事务支持

支持的表:
  - users (用户表)
  - concepts (概念表)
  - stocks (股票表)
  - concept_stocks (概念-股票关联表)
  - payment_orders (支付订单表)
  - user_packages (用户套餐表)
  - import_records (导入记录表)
```

#### 3. **API 路由层** (`api/api_v1/`)
```
endpoints/
├── auth.py                 # 用户认证
├── admin_auth.py           # 管理员认证
├── stocks.py               # 股票查询
├── concepts.py             # 概念管理
├── concept_analysis.py     # 概念分析
├── daily_analysis.py       # 每日分析
├── chart_data.py           # 图表数据
├── payment.py              # 支付管理
├── admin_management.py     # 管理员管理
├── client_user_management.py # 用户管理
├── data_import.py          # 数据导入
├── stock_data.py           # 股票数据
├── stock_analysis.py       # 股票分析
├── file_type_management.py # 文件类型管理
└── universal_import.py     # 通用导入
```

#### 4. **业务逻辑层** (`services/`)
```
services/
├── stock_service.py        # 股票相关逻辑
├── concept_service.py      # 概念相关逻辑
├── analysis_service.py     # 分析相关逻辑
├── payment_service.py      # 支付逻辑
├── user_service.py         # 用户管理逻辑
├── import_service.py       # 数据导入逻辑
└── schema.py               # 数据模型
```

#### 5. **中间件** (`middleware/`)
```python
- RequestLoggingMiddleware    # 请求日志
- RateLimitMiddleware         # 速率限制
- CORSMiddleware              # 跨域资源共享
- ErrorHandlingMiddleware     # 统一错误处理
```

### 主要功能模块

| 功能模块 | 说明 | 关键特性 |
|---------|------|--------|
| **认证管理** | 用户和管理员登录认证 | JWT 令牌, 密码加密, 会话管理 |
| **用户管理** | 用户信息和权限管理 | 用户搜索, 权限控制, 查询次数扣费 |
| **会员管理** | 会员等级和套餐管理 | 等级划分(免费/专业/高级), 自动续期 |
| **支付系统** | 订单处理和微信支付集成 | 支付回调, 订单管理, 发票生成 |
| **数据导入** | 多格式数据导入处理 | TXT/TTV/EEE 格式, 覆盖检测, 异步处理 |
| **概念分析** | 股票概念分析和排行 | 热度计算, 排名更新, 创新高检测 |
| **日报生成** | 每日分析报告生成 | 报告计算, 数据聚合, 性能优化 |
| **图表数据** | 用于前端展示的图表数据 | 趋势数据, 对比数据, 排行数据 |

---

## 💻 客户端系统 (Client)

### 基本信息
- **端口**: 8005
- **框架**: React 18 + TypeScript
- **构建工具**: Vite 7.x
- **UI 组件库**: Ant Design 5.x
- **HTTP 客户端**: Axios
- **项目路径**: `/client`

### 项目结构

```
client/src/
├── pages/                          # 页面组件
│   ├── AuthPage.tsx               # 登录/注册页面
│   ├── AnalysisPage.tsx           # 分析展示页面
│   └── MembershipPage.tsx         # 会员管理页面
│
├── components/                     # 可复用组件
│   ├── MobileLayout.tsx           # 移动端布局
│   ├── PaymentHistoryPage.tsx     # 支付历史
│   └── ...其他组件
│
├── services/                       # API 服务层
│   ├── conceptAnalysisApi.ts      # 概念分析 API
│   └── dailyAnalysisApi.ts        # 每日分析 API
│
├── utils/                          # 工具函数
│   └── auth.ts                    # 认证相关
│
├── styles/                         # 样式文件
├── App.tsx                         # 主应用组件
└── main.tsx                        # 应用入口
```

### 核心页面功能

#### 1. **认证页面** (AuthPage.tsx)
- ✓ 用户登录
- ✓ 用户注册
- ✓ 密码重置
- ✓ 错误提示与验证

#### 2. **分析页面** (AnalysisPage.tsx)
- ✓ 概念创新高列表
- ✓ 股票排行展示
- ✓ 实时热度数据
- ✓ 图表可视化
- ✓ 数据搜索与筛选

#### 3. **会员页面** (MembershipPage.tsx)
- ✓ 会员等级展示
- ✓ 套餐对比
- ✓ 升级支付
- ✓ 权益说明

#### 4. **支付历史** (PaymentHistoryPage.tsx)
- ✓ 订单列表
- ✓ 支付状态查询
- ✓ 发票下载
- ✓ 交易明细

### API 服务集成

#### ConceptAnalysisApi 服务
```typescript
- getStockRanking()           // 获取股票概念排名
- getConceptRanking()         // 获取概念股票排名
- getInnovationConcepts()     // 获取创新高概念
- getConvertibleBonds()       // 获取可转债数据
- triggerAnalysis()           // 触发分析
- getAnalysisStatus()         // 获取分析状态
```

#### ChartDataApi 服务
```typescript
- getConceptHeatTrend()       // 概念热度趋势
- getDailyHotConcepts()       // 每日热门概念
- getStockDistribution()      // 股票分布
- getInnovationTimeline()     // 创新时间线
- getConvertibleBondsChart()  // 可转债图表
- getConceptComparison()      // 概念对比
- getMarketOverview()         // 市场概览
- getStockConceptPerformance()// 股票表现
```

#### DailyAnalysisApi 服务
```typescript
- generateAnalysis()          // 生成分析报告
- getConceptSummaries()       // 概念汇总
- getConceptRankings()        // 概念排名
- getTopConcepts()            // 热点概念
- getConceptDetail()          // 概念详情
- getAnalysisStatus()         // 分析状态
```

### 认证与状态管理

#### 统一认证管理器 (UnifiedAuthManager)
```typescript
方法:
  - login()                     // 用户登录
  - register()                  // 用户注册
  - logout()                    // 用户登出
  - getToken()                  // 获取 token
  - setToken()                  // 设置 token
  - removeToken()               // 删除 token
  - checkAuth()                 // 检查认证状态
  - isAuthenticated()           // 是否已认证

特性:
  ✓ 单例模式
  ✓ 自动token注入
  ✓ 统一错误处理
  ✓ 重试机制(3次)
  ✓ 安全存储
```

#### 配置管理 (auth-config.ts)
```typescript
USER_AUTH_CONFIG:
  - API 基础 URL: http://localhost:3007/api/v1
  - 登录端点: /auth/login
  - 注册端点: /auth/register
  - Token 有效期: 24小时
  - 刷新阈值: 5分钟
  - 存储键: app_token, app_user

ADMIN_AUTH_CONFIG:
  - API 基础 URL: http://localhost:3007/api/v1
  - 登录端点: /admin-auth/login
  - Token 刷新: 自动启用
  - 存储键: admin_token, admin_user
```

### 主要特性

| 特性 | 说明 |
|------|------|
| **响应式设计** | 支持移动端和桌面端自适应 |
| **实时数据更新** | 支持数据轮询和自动刷新 |
| **错误处理** | 统一的错误提示和重试机制 |
| **缓存管理** | LocalStorage 用户持久化 |
| **Token 管理** | 自动 token 注入和过期处理 |
| **性能优化** | 代码分割, 懒加载, 打包优化 |

---

## 🎨 管理后台系统 (Frontend)

### 基本信息
- **端口**: 8006
- **框架**: React 18 + TypeScript
- **构建工具**: Vite 7.x
- **UI 组件库**: Ant Design 5.x
- **状态管理**: React Context (内置)
- **项目路径**: `/frontend`

### 项目结构

```
frontend/src/
├── components/                     # 可复用组件
│   ├── AdminLayout.tsx           # 管理员布局
│   ├── ...其他组件
│
├── routes/                         # 路由配置
│   └── ProtectedRoute.tsx         # 受保护路由
│
├── contexts/                       # 上下文
│   └── AuthContext.tsx            # 认证上下文
│
├── App.tsx                         # 主应用
├── main.tsx                        # 应用入口
└── assets/                         # 静态资源
```

### 管理员页面功能

#### 1. **登录页面** (LoginPage.tsx)
- ✓ 管理员登录
- ✓ 账户验证
- ✓ 会话管理
- ✓ 权限检查

#### 2. **仪表盘** (Dashboard.tsx)
- ✓ 系统统计概览
- ✓ 关键指标展示
- ✓ 实时监控面板
- ✓ 数据可视化图表

#### 3. **数据导入页面** (DataImportPage.tsx)
- ✓ 多格式文件上传
- ✓ 导入进度跟踪
- ✓ 覆盖检测和确认
- ✓ 导入历史查询
- ✓ 错误日志查看

#### 4. **历史数据导入** (HistoricalDataImport.tsx)
- ✓ 批量导入支持
- ✓ 日期范围选择
- ✓ 数据验证
- ✓ 导入统计

#### 5. **用户管理** (AdminManagement.tsx)
- ✓ 用户列表展示
- ✓ 用户搜索和筛选
- ✓ 用户信息修改
- ✓ 权限管理
- ✓ 用户删除/停用

#### 6. **用户管理-客户端** (StockListPage.tsx)
- ✓ 客户端用户管理
- ✓ 查询次数控制
- ✓ 会员等级调整
- ✓ 用户查询历史

#### 7. **套餐管理** (PackageManagement.tsx)
- ✓ 套餐列表展示
- ✓ 新建套餐
- ✓ 编辑套餐参数
- ✓ 删除套餐
- ✓ 套餐与用户关联

#### 8. **支付管理** (PaymentPage.tsx)
- ✓ 订单列表展示
- ✓ 订单详情查看
- ✓ 订单状态管理
- ✓ 支付验证
- ✓ 发票管理

#### 9. **概念分析** (ConceptAnalysisPage.tsx)
- ✓ 概念创新高检测
- ✓ 概念热度统计
- ✓ 股票概念关联
- ✓ 排行榜展示
- ✓ 数据导出

#### 10. **股票分析** (NewStockAnalysisPage.tsx)
- ✓ 股票详情查询
- ✓ 概念组合分析
- ✓ 性能对标
- ✓ 历史回测
- ✓ 分析报告生成

#### 11. **创新高追踪** (InnovationAnalysisPage.tsx)
- ✓ 创新高概念追踪
- ✓ 创新高时间线
- ✓ 热度趋势分析
- ✓ 预警设置
- ✓ 数据导出

#### 12. **可转债分析** (ConvertibleBondPage.tsx)
- ✓ 可转债列表
- ✓ 转股价格分析
- ✓ 收益率计算
- ✓ 风险评估
- ✓ 市场对比

#### 13. **文件类型管理** (FileTypeManagement.tsx)
- ✓ 自定义文件类型
- ✓ 字段配置
- ✓ 验证规则设置
- ✓ 导入模板生成
- ✓ 版本管理

#### 14. **EEE 文件导入记录** (EeeImportRecords.tsx)
- ✓ 导入记录列表
- ✓ 详细日志查看
- ✓ 错误排查
- ✓ 重新导入
- ✓ 数据回滚

### API 集成

所有管理员功能都通过以下 API 端点进行：

```typescript
// 通过 apiClient 实例
// 基础 URL: http://localhost:3007/api/v1

- GET    /admin/users              // 用户列表
- PUT    /admin/users/{id}         // 修改用户
- DELETE /admin/users/{id}         // 删除用户
- GET    /admin/packages           // 套餐列表
- POST   /admin/packages           // 创建套餐
- PUT    /admin/packages/{id}      // 修改套餐
- DELETE /admin/packages/{id}      // 删除套餐
- GET    /admin/orders             // 订单列表
- GET    /admin/orders/{id}        // 订单详情
- POST   /admin/orders/{id}/process// 处理订单
- POST   /data/import              // 文件上传
- GET    /data/import/history      // 导入历史
```

### 认证与授权

```typescript
管理员认证流程:
1. 输入账户密码
2. 调用 /admin-auth/login
3. 获得 JWT token
4. 存储 token 到 LocalStorage
5. 之后请求自动添加 Authorization header
6. Token 过期时重新登录

权限控制:
- 通过 ProtectedRoute 组件保护页面
- 检查 token 有效性
- 未授权自动跳转登录页
```

---

## 🔄 系统间通信与协作

### 1. API 通信流程

```
Client/Frontend
    ↓ (HTTP Request)
FastAPI Backend
    ↓ (处理业务逻辑)
数据库 / Redis 缓存
    ↓ (返回数据)
FastAPI Backend
    ↓ (HTTP Response)
Client/Frontend
```

### 2. 认证流程

```
用户输入凭证
    ↓
Client.login(username, password)
    ↓
POST /api/v1/auth/login
    ↓
Backend 验证密码 (Argon2)
    ↓
生成 JWT Token
    ↓
返回 {access_token, user_info}
    ↓
Client 存储 Token (LocalStorage)
    ↓
后续请求自动添加 Authorization: Bearer <token>
```

### 3. 支付流程

```
用户选择套餐
    ↓
Client.payment.createOrder()
    ↓
POST /api/v1/payment/orders
    ↓
Backend 生成订单
    ↓
返回支付二维码
    ↓
用户微信扫码支付
    ↓
微信回调 /api/v1/payment/callback
    ↓
Backend 更新订单状态
    ↓
更新用户会员等级
    ↓
Client 展示支付成功
```

### 4. 数据导入流程

```
管理员选择文件
    ↓
Frontend.dataImport.upload(file)
    ↓
POST /api/v1/data/import (FormData)
    ↓
Backend 异步处理导入任务
    ↓
Frontend 定时查询导入状态
    ↓
GET /api/v1/data/import/status/{task_id}
    ↓
导入完成，返回统计结果
    ↓
Frontend 展示导入结果
```

---

## 🗄️ 数据库设计

### 核心表结构

```
users (用户表)
├── id (主键)
├── username (用户名)
├── email (邮箱)
├── hashed_password (密码哈希)
├── is_admin (是否管理员)
├── membership_type (会员类型: free/pro/premium)
├── queries_remaining (剩余查询次数)
├── created_at (创建时间)
└── updated_at (更新时间)

concepts (概念表)
├── id (主键)
├── name (概念名称)
├── description (概念描述)
├── heat_value (热度值)
├── stock_count (股票数量)
├── last_updated (最后更新时间)
└── is_active (是否活跃)

stocks (股票表)
├── id (主键)
├── code (股票代码)
├── name (股票名称)
├── price (当前价格)
├── change_percent (涨跌幅%)
├── turnover_rate (换手率)
└── updated_at (更新时间)

concept_stocks (概念-股票关联表)
├── id (主键)
├── concept_id (概念ID)
├── stock_id (股票ID)
├── rank (在概念中的排名)
└── heat_value (热度值)

payment_orders (支付订单表)
├── id (主键)
├── user_id (用户ID)
├── package_id (套餐ID)
├── amount (金额)
├── status (状态: pending/success/failed)
├── wx_order_id (微信订单ID)
├── created_at (创建时间)
└── paid_at (支付时间)

user_packages (用户套餐表)
├── id (主键)
├── user_id (用户ID)
├── package_id (套餐ID)
├── queries_available (可用查询次数)
├── expires_at (过期时间)
└── is_active (是否活跃)
```

---

## 🔐 安全架构

### 认证与授权

```
┌─────────────────────────────────────┐
│     用户提交凭证                      │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│   密码 Argon2 验证 (72字节无限制)    │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│   生成 JWT Token (HS256, 24小时)     │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│   返回 access_token 给客户端          │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│   Client 存储 Token (LocalStorage)   │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  后续请求添加 Authorization Header    │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Backend 验证 Token 有效性           │
└─────────────────────────────────────┘
```

### 其他安全措施

- ✓ CORS 跨域资源共享控制
- ✓ HTTPS 支持
- ✓ 速率限制 (200 请求/分钟)
- ✓ SQL 注入防护 (SQLAlchemy ORM)
- ✓ CSRF 防护
- ✓ 请求日志记录
- ✓ 异常错误隐藏
- ✓ 支付数据加密

---

## 📈 性能优化

### 后端优化

```
缓存策略:
├── Redis 缓存热数据
├── 概念热度缓存 (1小时)
├── 股票排行缓存 (30分钟)
└── 用户信息缓存 (会话期间)

数据库优化:
├── 索引优化
├── 查询优化
├── 连接池配置
├── 异步数据处理
└── 批量导入优化

并发处理:
├── 异步任务队列
├── 多进程数据导入
├── 负载均衡就绪
└── 连接复用
```

### 前端优化

```
代码分割:
├── 路由级别代码分割
├── 组件懒加载
├── 第三方库分离打包
└── 动态导入

打包优化:
├── Tree shaking
├── 混淆压缩
├── Gzip 压缩
└── 静态资源优化

运行时优化:
├── 虚拟滚动
├── 防抖/节流
├── 条件渲染
└── 事件委托
```

---

## 🚀 部署架构

### 开发环境

```
开发机器
├── Backend (http://localhost:3007)
├── Client (http://localhost:8005)
├── Frontend (http://localhost:8006)
├── MySQL (docker)
└── Redis (docker)
```

### 生产环境

```
┌────────────────────────────────────────┐
│         Nginx 反向代理                  │
│    (域名解析, HTTPS, 负载均衡)         │
└────────┬─────────────────────┬────────┘
         │                     │
    ┌────▼────┐           ┌───▼────┐
    │ Backend │           │Frontend │
    │ Cluster │           │  Docs   │
    └────┬────┘           └────────┘
         │
    ┌────▼──────────────┐
    │  MySQL + Redis    │
    │    (Cluster)      │
    └───────────────────┘
```

---

## 📊 模块依赖关系

```
Client
├── shared/auth-config.ts (认证配置)
├── shared/auth.ts (认证管理)
├── services/conceptAnalysisApi.ts
├── services/dailyAnalysisApi.ts
└── utils/auth.ts

Frontend
├── shared/auth-config.ts (认证配置)
├── shared/auth.ts (认证管理)
└── API endpoints via authManager

Backend
├── core/security.py (密码加密/JWT)
├── core/database.py (数据库)
├── core/config.py (配置管理)
├── api/api_v1/api.py (路由汇总)
├── api/api_v1/endpoints/* (具体端点)
├── services/* (业务逻辑)
├── models/* (数据模型)
└── middleware/* (中间件)
```

---

## 🔧 技术栈总结

### 后端技术栈

| 层级 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 框架 | FastAPI | 0.104.1 | Web 框架 |
| ORM | SQLAlchemy | 2.0.23 | 数据库 ORM |
| 数据库 | MySQL | 8.0+ | 主数据库 |
| 缓存 | Redis | 6.1.1 | 数据缓存 |
| 认证 | python-jose | 3.3.0 | JWT 生成 |
| 密码 | passlib/argon2 | 1.7.4+ | 密码哈希 |
| 数据处理 | pandas | 2.0.3 | 数据处理 |
| HTTP | httpx/requests | 0.25.2 | HTTP 客户端 |
| 部署 | uvicorn | 0.24.0 | ASGI 服务器 |

### 前端技术栈

| 层级 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 框架 | React | 18.x | UI 框架 |
| 语言 | TypeScript | 5.x | 类型化 |
| 构建 | Vite | 7.x | 构建工具 |
| 路由 | React Router | 6.x | 路由管理 |
| 组件库 | Ant Design | 5.x | UI 组件 |
| 图表 | ECharts | 5.x | 数据可视化 |
| HTTP | Axios | 1.x | HTTP 客户端 |
| 工具 | dayjs | 1.x | 日期处理 |
| 主题 | 自定义主题 | - | UI 主题 |

---

## 📝 常用命令

### 启动服务

```bash
# 启动所有服务
./start.sh

# 启动单个服务
./start-fixed-ports.sh              # 固定端口启动
npm run dev                          # 在 client 目录
npm run dev                          # 在 frontend 目录
python -m uvicorn app.main:app --port 3007  # 在 backend 目录
```

### 停止服务

```bash
# 停止所有服务
./stop.sh

# 查看运行状态
./status.sh
```

### 查看日志

```bash
tail -f logs/backend.log             # 后端日志
tail -f logs/frontend.log            # 前端日志
tail -f logs/client.log              # 客户端日志
```

### 数据库操作

```bash
# 初始化数据库
python init_database.py

# 备份数据库
mysqldump -u root -p stock_db > backup.sql

# 恢复数据库
mysql -u root -p stock_db < backup.sql
```

---

## 🎯 关键配置文件

| 文件 | 位置 | 说明 |
|------|------|------|
| 后端配置 | `backend/app/core/config.py` | FastAPI 配置 |
| 认证配置 | `shared/auth-config.ts` | 统一认证配置 |
| Vite 配置 (客户端) | `client/vite.config.ts` | 前端构建配置 |
| Vite 配置 (管理) | `frontend/vite.config.ts` | 管理后台配置 |
| 数据库连接 | `backend/app/core/database.py` | MySQL 连接 |
| Nginx 配置 | `nginx/nginx.conf` | 反向代理配置 |

---

## 📞 联系与支持

如有问题，请参考以下文档：
- `QUICKSTART.md` - 快速开始
- `TROUBLESHOOTING.md` - 故障排除
- `DEVELOPMENT_PROGRESS.md` - 开发进度
- API 文档: http://localhost:3007/docs

---

**最后更新**: 2025-11-12
**版本**: v2.7.3
**状态**: 🟢 生产就绪
