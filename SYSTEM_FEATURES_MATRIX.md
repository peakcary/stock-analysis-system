# 系统功能矩阵与技术栈关系

## 📋 功能分布矩阵

### 按系统分类

```
┌─────────────────────────────────────────────────────────────────────┐
│                         功能分布矩阵                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  Backend (后端)                 Client (客户端)      Frontend (管理)  │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                        │
│  核心业务逻辑 ────────────┬───> UI展示             UI管理             │
│  数据库管理 ──────────────┤     权限验证 ─────────> 权限验证          │
│  文件处理 ────────────────┤     实时交互           文件导入            │
│  支付集成 ────────────────┤     分析展示 ─────────> 数据管理          │
│  认证授权 ────────────────┤     会员升级 ─────────> 支付审核          │
│                           │     数据查询 ─────────> 报表生成          │
│                           └───> 用户交互           系统监控          │
│                                                                        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 功能流转与数据流

### 1. 用户认证流程

```
Client
┌──────────────────────────┐
│ AuthPage                 │
│ - 输入用户名/密码        │
│ - 验证输入               │
└──────────┬───────────────┘
           │ (POST /auth/login)
           ▼
Backend
┌──────────────────────────┐
│ auth.py                  │
│ - 验证凭证               │
│ - 生成 JWT Token         │
│ - 返回 user info         │
└──────────┬───────────────┘
           │ {access_token, user}
           ▼
Client
┌──────────────────────────┐
│ authManager              │
│ - 保存 Token             │
│ - 保存用户信息           │
│ - 跳转首页               │
└──────────────────────────┘
```

### 2. 数据查询流程

```
Client
┌──────────────────────────┐
│ AnalysisPage             │
│ - 显示列表               │
│ - 分页/筛选              │
└──────────┬───────────────┘
           │ (GET /concept-analysis/concepts/innovation)
           ▼
Backend
┌──────────────────────────┐
│ concept_analysis.py      │
│ - 查询数据库             │
│ - 计算热度值             │
│ - 格式化返回数据         │
└──────────┬───────────────┘
           │ {data: [...], total: N}
           ▼
Client
┌──────────────────────────┐
│ conceptAnalysisApi       │
│ - 显示数据               │
│ - 图表渲染               │
│ - 交互响应               │
└──────────────────────────┘
```

### 3. 数据导入流程 (管理后台)

```
Frontend
┌──────────────────────────┐
│ DataImportPage           │
│ - 选择文件               │
│ - 预览数据               │
│ - 确认导入               │
└──────────┬───────────────┘
           │ (POST /data/import)
           ▼
Backend
┌──────────────────────────┐
│ data_import.py           │
│ - 接收文件               │
│ - 解析数据               │
│ - 验证覆盖               │
│ - 异步导入任务           │
└──────────┬───────────────┘
           │ (async process)
           ▼
Backend
┌──────────────────────────┐
│ import_service.py        │
│ - 批量插入数据库         │
│ - 更新概念关系           │
│ - 计算统计指标           │
│ - 生成导入报告           │
└──────────┬───────────────┘
           │ (update status)
           ▼
Frontend
┌──────────────────────────┐
│ importStatus polling     │
│ - 显示进度               │
│ - 展示结果               │
│ - 导出报告               │
└──────────────────────────┘
```

---

## 🎯 功能模块详细对应表

### Authentication (认证模块)

| 功能 | Backend | Client | Frontend | 技术实现 |
|------|---------|--------|----------|---------|
| **登录** | `auth.py` | `AuthPage.tsx` | `LoginPage.tsx` | JWT + Argon2 |
| **注册** | `auth.py` | `AuthPage.tsx` | - | Email验证 |
| **Token 管理** | `security.py` | `auth.ts` | `auth.ts` | localStorage |
| **权限检查** | middleware | 路由保护 | ProtectedRoute | Bearer Token |
| **管理员认证** | `admin_auth.py` | - | `LoginPage.tsx` | JWT + refresh |
| **Session 管理** | `security.py` | authManager | authManager | 24小时有效 |

### User Management (用户管理)

| 功能 | Backend | Client | Frontend | 技术实现 |
|------|---------|--------|----------|---------|
| **用户列表** | `admin_management.py` | - | `AdminManagement.tsx` | 分页查询 |
| **用户搜索** | `stocks.py` | AnalysisPage | `StockListPage.tsx` | 模糊匹配 |
| **修改用户信息** | endpoints | - | `AdminManagement.tsx` | PUT 请求 |
| **权限管理** | models | 路由检查 | ProtectedRoute | 角色控制 |
| **查询次数控制** | `user_service.py` | - | `PackageManagement.tsx` | 扣费机制 |
| **会员升级** | `payment_service.py` | `MembershipPage.tsx` | `PaymentPage.tsx` | 支付触发 |

### Data Import (数据导入)

| 功能 | Backend | Client | Frontend | 技术实现 |
|------|---------|--------|----------|---------|
| **文件上传** | `data_import.py` | - | `DataImportPage.tsx` | FormData |
| **格式支持** | `import_service.py` | - | `DataImportPage.tsx` | TXT/TTV/EEE |
| **覆盖检测** | `import_service.py` | - | `DataImportPage.tsx` | SQL 查询 |
| **异步处理** | task queue | - | polling | Celery/asyncio |
| **进度跟踪** | `import_service.py` | - | 定时查询 | WebSocket/Poll |
| **错误日志** | logging | - | `EeeImportRecords.tsx` | 数据库存储 |
| **批量导入** | `historical_txt_import.py` | - | `HistoricalDataImport.tsx` | 日期范围 |

### Concept Analysis (概念分析)

| 功能 | Backend | Client | Frontend | 技术实现 |
|------|---------|--------|----------|---------|
| **概念列表** | `concepts.py` | - | `ConceptAnalysisPage.tsx` | 缓存查询 |
| **创新高检测** | `concept_analysis.py` | `AnalysisPage.tsx` | `InnovationAnalysisPage.tsx` | 数据对比 |
| **热度计算** | `analysis_service.py` | - | - | 加权算法 |
| **排行榜** | `daily_analysis.py` | `AnalysisPage.tsx` | `NewStockAnalysisPage.tsx` | 排序查询 |
| **概念对比** | `chart_data.py` | - | `ConceptAnalysisPage.tsx` | 多维数据 |
| **股票关联** | `concept_stocks` | `AnalysisPage.tsx` | `StockListPage.tsx` | JOIN 查询 |

### Chart & Visualization (图表和可视化)

| 功能 | Backend | Client | Frontend | 技术实现 |
|------|---------|--------|----------|---------|
| **热度趋势** | `chart_data.py` | - | `ConceptAnalysisPage.tsx` | ECharts |
| **时间序列** | `daily_analysis.py` | - | `InnovationAnalysisPage.tsx` | 时间线 |
| **股票分布** | `chart_data.py` | - | - | 饼图/柱状图 |
| **市场概览** | `chart_data.py` | `AnalysisPage.tsx` | `Dashboard.tsx` | 仪表盘 |
| **可转债分析** | `chart_data.py` | - | `ConvertibleBondPage.tsx` | 数据表格 |
| **对标对比** | `stock_analysis.py` | - | `NewStockAnalysisPage.tsx` | 并列展示 |

### Payment System (支付系统)

| 功能 | Backend | Client | Frontend | 技术实现 |
|------|---------|--------|----------|---------|
| **订单创建** | `payment.py` | `MembershipPage.tsx` | `PaymentPage.tsx` | 数据库写入 |
| **支付二维码** | `payment_service.py` | `MembershipPage.tsx` | - | 微信 V3 API |
| **支付回调** | `payment.py` | - | - | Webhook |
| **订单查询** | `payment.py` | `PaymentHistoryPage.tsx` | `PaymentPage.tsx` | SQL 查询 |
| **发票生成** | `payment_service.py` | - | - | 模板生成 |
| **交易统计** | `payment.py` | - | `Dashboard.tsx` | 聚合查询 |
| **套餐管理** | `admin_packages.py` | - | `PackageManagement.tsx` | CRUD |

### Stock Analysis (股票分析)

| 功能 | Backend | Client | Frontend | 技术实现 |
|------|---------|--------|----------|---------|
| **股票查询** | `stocks.py` | `AnalysisPage.tsx` | `StockSearchPage.tsx` | 模糊搜索 |
| **股票详情** | `stock_analysis.py` | - | `NewStockAnalysisPage.tsx` | 关联查询 |
| **性能表现** | `stock_analysis.py` | - | `NewStockAnalysisPage.tsx` | 计算指标 |
| **历史回测** | `stock_analysis.py` | - | `NewStockAnalysisPage.tsx` | 时间线数据 |
| **概念表现** | `chart_data.py` | - | - | 排名展示 |

### System Management (系统管理)

| 功能 | Backend | Client | Frontend | 技术实现 |
|------|---------|--------|----------|---------|
| **系统状态** | `system.py` | - | `Dashboard.tsx` | 健康检查 |
| **性能监控** | `optimization_status.py` | - | - | 数据库统计 |
| **数据库优化** | `optimization_status.py` | - | - | 索引管理 |
| **文件类型管理** | `file_type_management.py` | - | `FileTypeManagement.tsx` | 动态配置 |
| **日志查看** | logging | - | - | 文件输出 |

---

## 🛠️ 技术栈与功能对应

### 后端技术栈功能映射

```
FastAPI (Web框架)
├── 路由定义 → 所有 API endpoints
├── 中间件 → CORS, 认证, 速率限制, 日志
└── 依赖注入 → 数据库连接, 权限检查

SQLAlchemy (ORM)
├── 模型定义 → 所有数据表
├── 查询优化 → 性能调优
└── 事务管理 → 数据一致性

MySQL (数据库)
├── 数据存储 → users, concepts, stocks, ...
├── 索引优化 → 查询性能
└── 备份恢复 → 数据安全

Redis (缓存)
├── 热数据缓存 → 概念, 排行榜
├── Session 存储 → 认证令牌
└── 速率限制 → 请求节流

python-jose (JWT)
├── Token 生成 → 登录颁发
├── Token 验证 → 请求验证
└── 声明管理 → 用户身份

argon2 (密码加密)
├── 密码哈希 → 安全存储
├── 密码验证 → 登录验证
└── 版本支持 → 兼容性
```

### 前端技术栈功能映射

```
React (UI框架)
├── 组件化 → AnalysisPage, AuthPage, 等页面
├── 状态管理 → Context API, useState
└── 生命周期 → useEffect, 数据加载

TypeScript (类型系统)
├── 类型定义 → API 响应, 模型对象
├── 接口定义 → 组件 props, 服务方法
└── 编译时检查 → 代码质量

Vite (构建工具)
├── 热更新 → 快速开发
├── 代码分割 → 性能优化
└── 打包优化 → 生产构建

Ant Design (组件库)
├── 表单组件 → 登录, 搜索, 输入
├── 表格组件 → 列表展示
├── 模态框 → 确认对话
└── 通知组件 → 消息提示

Axios (HTTP客户端)
├── API 请求 → 所有后端调用
├── 拦截器 → Token 自动添加
└── 错误处理 → 统一错误提示

ECharts (图表库)
├── 柱状图 → 热度排行
├── 折线图 → 趋势数据
├── 饼图 → 分布数据
└── 热力图 → 概念分布
```

---

## 📊 数据流向图

### 完整的数据流循环

```
用户操作
   ↓
Client/Frontend UI 更新
   ↓
认证检查 (Token 验证)
   ↓
API 请求 (HTTP + JWT)
   ↓
Backend 接收
   ↓
业务逻辑处理
   ├─ 数据库查询 (MySQL)
   ├─ 缓存检查 (Redis)
   ├─ 权限校验
   └─ 数据转换
   ↓
数据库操作
   ├─ SELECT (查询)
   ├─ INSERT (插入)
   ├─ UPDATE (更新)
   └─ DELETE (删除)
   ↓
缓存更新 (Redis)
   ↓
API 响应 (JSON)
   ↓
Client/Frontend 接收
   ↓
状态更新 (setState/Context)
   ↓
UI 重新渲染
   ↓
用户看到结果
```

---

## 🔐 安全防护矩阵

### 功能级别的安全实现

| 功能 | 前端防护 | 后端防护 | 数据库防护 | 网络防护 |
|------|---------|---------|-----------|---------|
| **登录** | 表单验证 | 密码哈希 | 凭证加密 | HTTPS |
| **认证** | Token 存储 | JWT 验证 | 权限检查 | CORS |
| **数据查询** | 输入验证 | 权限检查 | SQL 参数化 | 速率限制 |
| **数据导入** | 文件验证 | 覆盖检测 | 事务处理 | 文件大小限制 |
| **支付** | 金额验证 | 订单校验 | 加密存储 | 微信 SSL |
| **管理操作** | 操作确认 | 权限验证 | 审计日志 | SSL 连接 |

---

## 📈 性能优化矩阵

### 各功能模块的性能优化策略

| 模块 | 优化策略 | 实现方式 | 效果 |
|------|---------|---------|------|
| **用户认证** | Token 缓存 | Redis | 减少数据库查询 |
| **概念查询** | 热数据缓存 | Redis + TTL | 降低 DB 负载 |
| **排行榜** | 定时计算 | 异步任务 | 避免高并发 |
| **数据导入** | 异步处理 | Celery/asyncio | 不阻塞 UI |
| **图表数据** | 数据聚合 | 预计算 | 快速响应 |
| **文件上传** | 分块上传 | FormData | 支持大文件 |
| **列表查询** | 分页加载 | offset/limit | 减少数据量 |
| **前端打包** | 代码分割 | Vite chunks | 加快加载 |

---

## 🔄 模块间通信协议

### REST API 通信

```
Request:
  Method: GET/POST/PUT/DELETE
  URL: http://localhost:3007/api/v1/{endpoint}
  Headers:
    - Content-Type: application/json
    - Authorization: Bearer {token}
  Body: {JSON 数据}

Response:
  Status: 200/400/401/403/500
  Headers:
    - Content-Type: application/json
  Body:
    {
      "success": true/false,
      "data": {...},
      "error": {...},
      "message": "..."
    }
```

### 错误处理

```
Client 端:
  1. API 调用失败
  2. 检查错误状态码
  3. 调用错误处理器
  4. 显示用户友好的错误信息
  5. 根据错误类型采取行动
     - 401: 跳转登录页
     - 403: 显示无权限
     - 500: 显示服务器错误

Backend 端:
  1. 捕获异常
  2. 记录错误日志
  3. 生成错误响应
  4. 返回统一格式
  5. 不暴露内部细节
```

---

## 📋 开发清单

### 添加新功能时需要同步的模块

```
新增 API 端点时:
  ☐ Backend: endpoints/{module}.py 添加路由
  ☐ Backend: services/{module}_service.py 添加业务逻辑
  ☐ Backend: models.py 添加数据模型
  ☐ Client: services/{module}Api.ts 添加 API 调用
  ☐ Client/Frontend: 组件添加数据调用
  ☐ 更新 API 文档

修改数据库时:
  ☐ Backend: models.py 更新模型
  ☐ Backend: migrations 生成迁移
  ☐ Backend: services 更新业务逻辑
  ☐ Client/Frontend: API 响应类型更新

优化性能时:
  ☐ Backend: 添加缓存策略
  ☐ Backend: 优化数据库查询
  ☐ Frontend: 代码分割优化
  ☐ Frontend: 组件懒加载

增强安全时:
  ☐ Backend: 添加权限检查
  ☐ Backend: 验证输入数据
  ☐ Backend: 加密敏感数据
  ☐ Frontend: 表单验证
  ☐ Frontend: XSS 防护
```

---

**生成时间**: 2025-11-12
**版本**: v2.7.3
