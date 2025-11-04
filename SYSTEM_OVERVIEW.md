# 🏗️ 股票分析系统 - 项目架构总览

**项目名称**: 股票概念分析系统 (Stock Concept Analysis System)
**架构类型**: 微服务 + 前后端分离
**部署方式**: Docker / 本地开发
**更新时间**: 2025-11-04

---

## 📦 完整系统结构

```
stock-analysis-system/
├── 1️⃣  backend/                    # 后端服务系统
├── 2️⃣  frontend/                   # Web 前端系统
├── 3️⃣  client/                     # 桌面客户端系统
├── 4️⃣  client-system/              # 新版本客户端系统
├── 5️⃣  shared/                     # 共享资源
├── 6️⃣  deploy-tools/               # 部署工具
├── 7️⃣  nginx/                      # Nginx 配置
├── 8️⃣  scripts/                    # 自动化脚本
├── 9️⃣  database/                   # 数据库配置
├── 📄 docker-compose.yml           # Docker 编排
└── 📚 docs/                        # 文档
```

---

## 1️⃣ BACKEND - 后端服务系统

### 📍 位置
```
/backend/
```

### 🛠️ 技术栈
- **框架**: FastAPI (Python Web 框架)
- **数据库**: MySQL 8.0.22 (腾讯云)
- **ORM**: SQLAlchemy 2.0
- **缓存**: Redis
- **服务器**: Uvicorn + Gunicorn
- **认证**: JWT + OAuth2

### 📋 功能模块

| 模块 | 功能 | 状态 |
|------|------|------|
| **认证系统** | 用户注册、登录、JWT | ✅ 完成 |
| **API 接口** | RESTful API (23+ 端点) | ✅ 完成 |
| **股票管理** | 股票数据、行情、分类 | ✅ 完成 |
| **概念系统** | 概念管理、关联、排名 | ✅ 完成 |
| **支付系统** | 微信支付、套餐、订单 | ✅ 完成 |
| **数据导入** | CSV、TXT、Excel 导入 | ✅ 完成 |
| **分析功能** | 每日分析、排名、汇总 | ✅ 完成 |

### 🗄️ 数据库表数
- **总计**: 15+ 个表
- **用户表**: users, admin_users
- **业务表**: stocks, concepts, daily_trading
- **支付表**: payment_orders, payment_packages
- **日志表**: membership_logs, import_batches

### 🚀 启动方式

```bash
# 开发模式
cd backend/
uvicorn app.main:app --host 0.0.0.0 --port 3007 --reload

# 生产模式
gunicorn -w 4 -b 0.0.0.0:3007 "app.main:app" -k uvicorn.workers.UvicornWorker
```

### 📊 API 文档访问
- **Swagger UI**: http://localhost:3007/docs
- **ReDoc**: http://localhost:3007/redoc
- **OpenAPI JSON**: http://localhost:3007/openapi.json

### ✅ 当前状态
- ✅ **已配置**: 腾讯云数据库连接
- ✅ **已启动**: 后端服务运行中
- ✅ **已测试**: 所有端点正常
- ✅ **已优化**: 文档页面修复

---

## 2️⃣ FRONTEND - Web 前端系统

### 📍 位置
```
/frontend/
```

### 🛠️ 技术栈
- **框架**: Vue.js 3
- **状态管理**: Pinia / Vuex
- **UI 框架**: 可能使用 Element Plus 或自定义组件
- **构建工具**: Vite
- **包管理**: npm / yarn
- **语言**: TypeScript + JavaScript

### 📋 功能模块

| 模块 | 功能 |
|------|------|
| **用户系统** | 注册、登录、个人中心 |
| **首页仪表板** | 数据展示、概览统计 |
| **股票查询** | 搜索、浏览、详情 |
| **概念分析** | 概念排名、热度图 |
| **支付系统** | 套餐购买、订单记录 |
| **个人中心** | 账户管理、查询历史 |

### 📦 项目结构

```
frontend/
├── src/
│   ├── components/        # 组件
│   ├── pages/            # 页面
│   ├── stores/           # 状态管理
│   ├── api/              # API 调用
│   ├── utils/            # 工具函数
│   ├── styles/           # 样式
│   └── App.vue
├── public/               # 静态资源
├── dist/                 # 构建输出
├── package.json
├── vite.config.ts
└── tsconfig.json
```

### 🚀 启动方式

```bash
# 安装依赖
cd frontend/
npm install

# 开发模式
npm run dev

# 生产构建
npm run build

# 预览
npm run preview
```

### 📊 端口
- **开发**: http://localhost:8005 (或自定义端口)
- **生产**: 通过 Nginx 反向代理

### ✅ 状态
- ⏳ **未启动**: 需要配置和测试

---

## 3️⃣ CLIENT - 桌面客户端系统

### 📍 位置
```
/client/
```

### 🛠️ 技术栈
- **框架**: Electron / Tauri (桌面框架)
- **前端**: React / Vue
- **数据库**: SQLite (本地)
- **网络**: axios / fetch
- **包管理**: npm / yarn

### 📋 功能模块

| 功能 | 说明 |
|------|------|
| **本地数据** | 离线数据存储、缓存 |
| **API 同步** | 与后端数据同步 |
| **客户端认证** | 登录、会话管理 |
| **数据导入导出** | 本地文件操作 |
| **数据可视化** | 图表、报表展示 |

### 📦 项目结构

```
client/
├── src/
│   ├── main/            # 主进程 (Electron)
│   ├── renderer/        # 渲染进程 (UI)
│   ├── components/
│   ├── pages/
│   └── api/
├── public/
├── package.json
└── electron.config.js
```

### 🚀 启动方式

```bash
# 安装依赖
cd client/
npm install

# 开发模式
npm run dev

# 打包为应用
npm run build

# 分发
npm run dist
```

### 📊 应用信息
- **平台**: Windows, macOS, Linux
- **架构**: 64-bit
- **最小化**: ~100-200MB

### ✅ 状态
- ⏳ **未启动**: 需要配置和测试

---

## 4️⃣ CLIENT-SYSTEM - 新版本客户端

### 📍 位置
```
/client-system/
```

### 📋 说明
- **目的**: 可能是客户端的新实现或重构
- **架构**: 与 /client/ 类似，但可能有改进
- **目标**: 提供更好的用户体验或性能

### 🚀 启动方式

```bash
cd client-system/
npm install
npm run dev
```

### ✅ 状态
- ⏳ **未启动**: 需要配置和测试

---

## 5️⃣ SHARED - 共享资源

### 📍 位置
```
/shared/
```

### 📋 内容

| 类别 | 内容 | 用途 |
|------|------|------|
| **类型定义** | TypeScript interfaces | 前端、客户端使用 |
| **常量** | API 路由、枚举 | 全局使用 |
| **工具函数** | 通用方法、辅助函数 | 代码复用 |
| **API 类型** | 请求、响应类型 | 类型安全 |
| **配置** | 全局配置、常量 | 统一管理 |

### 📦 目录结构

```
shared/
├── types/               # TypeScript 类型
├── constants/           # 常量定义
├── utils/              # 工具函数
├── api/                # API 相关
└── config/             # 配置文件
```

### 💡 用途
- 减少代码重复
- 保证类型一致性
- 便于维护和升级
- 多个系统共用

---

## 6️⃣ DEPLOY-TOOLS - 部署工具

### 📍 位置
```
/deploy-tools/
```

### 🛠️ 包含内容

| 工具 | 功能 |
|------|------|
| **Docker 脚本** | 容器化、镜像构建 |
| **K8s 配置** | 容器编排（如有） |
| **环境配置** | 各环境配置文件 |
| **数据库脚本** | SQL、迁移脚本 |
| **监控配置** | 日志、性能监控 |

### 📝 可用脚本

```bash
deploy-tools/
├── docker/              # Docker 相关
├── kubernetes/          # K8s 配置
├── database/           # 数据库脚本
├── monitoring/         # 监控配置
└── scripts/            # 自动化脚本
```

### 🚀 部署方式

```bash
# Docker 部署
docker-compose -f docker-compose.prod.yml up -d

# 或单个服务
docker build -t stock-backend ./backend
docker run -d -p 3007:3007 stock-backend
```

---

## 7️⃣ NGINX - Nginx 配置

### 📍 位置
```
/nginx/
```

### 🛠️ 功能

| 功能 | 说明 |
|------|------|
| **反向代理** | 后端 API 代理 |
| **静态文件** | 前端资源托管 |
| **负载均衡** | 多个实例均衡 |
| **SSL/TLS** | HTTPS 配置 |
| **压缩** | Gzip 压缩 |

### 📝 配置文件

```
nginx/
├── nginx.conf          # 主配置文件
├── conf.d/
│   ├── backend.conf    # 后端代理配置
│   └── frontend.conf   # 前端配置
├── ssl/                # SSL 证书
└── logs/               # 日志文件
```

### 🚀 启动方式

```bash
# 使用 Docker
docker run -d -p 80:80 -p 443:443 \
  -v /nginx/conf.d:/etc/nginx/conf.d \
  -v /nginx/ssl:/etc/nginx/ssl \
  nginx:latest

# 或本地运行
nginx -c /nginx/nginx.conf
```

---

## 8️⃣ SCRIPTS - 自动化脚本

### 📍 位置
```
/scripts/
```

### 🛠️ 脚本类型

| 脚本 | 功能 |
|------|------|
| **start-dev.sh** | 启动开发环境 |
| **stop-dev.sh** | 停止开发环境 |
| **deploy.sh** | 部署到生产环境 |
| **backup.sh** | 数据库备份 |
| **restore.sh** | 数据库恢复 |
| **init.sh** | 初始化环境 |

### 🚀 使用示例

```bash
# 启动开发环境
./start-dev.sh

# 停止开发环境
./stop-dev.sh

# 部署到生产
./deploy.sh production

# 备份数据库
./backup.sh
```

---

## 9️⃣ DATABASE - 数据库配置

### 📍 位置
```
/database/
```

### 🗄️ 内容

| 项目 | 说明 |
|------|------|
| **初始化脚本** | 表结构、初始数据 |
| **迁移脚本** | 版本升级脚本 |
| **备份** | 数据备份文件 |
| **恢复** | 数据恢复脚本 |

### 📝 文件结构

```
database/
├── init/               # 初始化脚本
├── migrations/         # 迁移脚本
├── backups/           # 备份文件
└── restore/           # 恢复脚本
```

---

## 🌐 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Clients                             │
├──────────────────┬──────────────────────┬──────────────────────┤
│                  │                      │                      │
│   Frontend       │     Client           │    Client-System     │
│   (Web Browser)  │  (Desktop App)       │    (New Client)      │
│   Vue.js         │  Electron            │    React/Vue         │
│   Port: 8005     │  Port: 3000-3001     │    Port: TBD         │
└────────┬─────────┴──────────┬───────────┴─────────┬────────────┘
         │                    │                     │
         │ HTTP/HTTPS         │ HTTP/HTTPS          │
         │                    │                     │
         └────────────┬───────┴──────────┬──────────┘
                      │                  │
         ┌────────────▼──────────────────▼──────────┐
         │                                          │
         │        NGINX (Reverse Proxy)            │
         │        Port: 80, 443                    │
         │                                          │
         └───────────────────┬──────────────────────┘
                             │
                    ┌────────▼─────────┐
                    │                  │
         ┌──────────▼────────┐   ┌────▼───────────┐
         │                   │   │                │
         │  BACKEND API      │   │  Static Files  │
         │  FastAPI          │   │  (CDN/Nginx)   │
         │  Port: 3007       │   │                │
         │                   │   └────────────────┘
         └────────┬──────────┘
                  │
         ┌────────▼──────────┐
         │                   │
         │   MySQL Database  │
         │   (Tencent Cloud) │
         │                   │
         │   Host: bj-cdb... │
         │   Port: 27126     │
         │   DB: mydb        │
         │                   │
         └───────────────────┘

Redis Cache (Optional)
```

---

## 📊 技术栈总结

| 层级 | 技术 | 版本 |
|------|------|------|
| **后端框架** | FastAPI | 0.104.1+ |
| **Web 服务器** | Uvicorn | 0.24.0+ |
| **应用服务器** | Gunicorn | 21.2.0+ |
| **Web 反向代理** | Nginx | 1.24+ |
| **数据库** | MySQL | 8.0.22-txsql |
| **ORM** | SQLAlchemy | 2.0.23+ |
| **缓存** | Redis | 6.1.1+ |
| **前端框架** | Vue.js 3 | 3.3+ |
| **前端构建** | Vite | 4.3+ |
| **桌面应用** | Electron/Tauri | Latest |
| **容器化** | Docker | 20.10+ |
| **编排** | Docker Compose | 2.0+ |

---

## 🚀 系统启动顺序

### 开发环境

```bash
# 1️⃣ 启动后端
cd backend/
uvicorn app.main:app --port 3007 --reload

# 2️⃣ 启动前端（新终端）
cd frontend/
npm run dev

# 3️⃣ 启动客户端（新终端）
cd client/
npm run dev

# 4️⃣ 启动 Nginx 代理（新终端）
docker run -d -p 80:80 nginx
```

### 生产环境

```bash
# 使用 Docker Compose 一键启动
docker-compose -f docker-compose.prod.yml up -d
```

---

## 📊 部署环境

### 本地开发

| 组件 | 地址 | 端口 |
|------|------|------|
| 后端 API | http://localhost:3007 | 3007 |
| 前端应用 | http://localhost:8005 | 8005 |
| Nginx | http://localhost | 80 |

### 生产环境

| 组件 | 地址 | 端口 |
|------|------|------|
| 后端 API | https://api.yourdomain.com | 443 |
| 前端应用 | https://yourdomain.com | 443 |
| Nginx | https://yourdomain.com | 443 |

---

## 🔄 数据流向

```
用户操作
   │
   ▼
┌─────────────┐
│  前端应用   │  (Vue.js 浏览器)
│  客户端应用 │  (Electron/Tauri)
└──────┬──────┘
       │ HTTP/HTTPS
       ▼
┌─────────────┐
│   Nginx     │  (反向代理)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Backend API │  (FastAPI)
└──────┬──────┘
       │
       ├──▶ 业务逻辑
       │
       ├──▶ 数据验证
       │
       └──▶ 数据库操作
            │
            ▼
       ┌──────────────┐
       │MySQL数据库   │
       │(Tencent云)   │
       └──────────────┘
```

---

## 📚 相关文档

| 文档 | 位置 | 内容 |
|------|------|------|
| 部署指南 | DEPLOYMENT_GUIDE.md | 详细部署步骤 |
| 开发指南 | DEVELOPMENT_PROGRESS.md | 开发进度跟踪 |
| 架构文档 | ARCHITECTURE_CHANGES_v2.7.3.md | 架构变更说明 |
| 安全指南 | SECURITY_FIXES.md | 安全加固措施 |
| 微信支付 | WECHAT_PAY_DEPLOYMENT.md | 支付集成 |

---

## ✅ 各系统完成度

| 系统 | 状态 | 完成度 | 备注 |
|------|------|--------|------|
| Backend | ✅ 完成 | 100% | 已配置、已测试、正在运行 |
| Frontend | ⏳ 待启动 | 80% | 代码完成，需测试 |
| Client | ⏳ 待启动 | 75% | 代码完成，需优化 |
| Client-System | ⏳ 待启动 | 60% | 新实现，需完善 |
| Shared | ✅ 完成 | 100% | 类型定义、常量完整 |
| Deploy-Tools | ✅ 完成 | 95% | Docker 脚本完整 |
| Nginx | ✅ 完成 | 90% | 配置基本完成 |
| Scripts | ✅ 完成 | 85% | 主要脚本完整 |

---

## 🎯 后续计划

### 近期 (本周)

- [ ] 启动 Frontend 系统
- [ ] 启动 Client 系统
- [ ] 整体系统集成测试
- [ ] 修复集成过程中的问题

### 中期 (本月)

- [ ] 优化前端界面
- [ ] 性能测试和调优
- [ ] 安全审计
- [ ] 用户体验优化

### 长期 (本季)

- [ ] 功能完善
- [ ] 生产环境部署
- [ ] 用户培训
- [ ] 持续维护

---

**项目维护**
- 最后更新: 2025-11-04
- 配置状态: ✅ Backend 完成
- 系统状态: 📊 多系统协作中
- 联系方式: 见项目文档

