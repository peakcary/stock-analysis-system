# 股票分析系统 - 脚本使用指南

本目录包含了所有项目脚本，按功能分类组织。

## 📋 目录结构

```
scripts/
├── bin/                    # 日常开发和运维脚本
│   ├── start.sh           # 启动所有服务（本地开发）
│   ├── stop.sh            # 停止所有服务
│   ├── restart.sh         # 重启所有服务
│   ├── status.sh          # 检查服务状态
│   └── check-env.sh       # 环境检查和验证
├── database/              # 数据库管理脚本
│   ├── init.sh           # 初始化数据库
│   ├── verify.sh         # 验证数据库连接和状态
│   ├── migrate.sh        # 数据库迁移
│   └── optimize.sh       # 数据库优化
├── deploy/               # 部署脚本
│   ├── deploy-local.sh          # 本地部署
│   ├── deploy-production.sh      # 生产环境部署
│   └── deploy-staging.sh        # 预发布环境部署
├── utils/                # 工具脚本
│   ├── setup-database.sh   # 初始化PostgreSQL并创建数据库
│   ├── generate-token.sh   # 生成JWT tokens
│   └── cleanup.sh         # 清理临时文件和日志
└── README.md             # 本文档
```

## 🚀 快速开始

### 1. 本地开发环境启动

```bash
# 启动所有服务（后端 + 前端 + 客户端）
./scripts/bin/start.sh

# 或从项目根目录
./start.sh
```

启动后访问：
- 后端 API: http://localhost:3007
- API 文档: http://localhost:3007/docs
- 管理端: http://localhost:8006 (admin/admin123)
- 客户端: http://localhost:8005 (fullaccess_user/fullaccess123)

### 2. 停止服务

```bash
./scripts/bin/stop.sh
# 或
./stop.sh
```

### 3. 检查服务状态

```bash
./scripts/bin/status.sh
# 或
./status.sh
```

### 4. 重启服务

```bash
./scripts/bin/restart.sh
# 或
./restart.sh
```

## 🗄️ 数据库管理

### 初始化数据库

```bash
# 初始化 PostgreSQL 和创建数据库
./scripts/utils/setup-database.sh

# 只初始化数据库结构
./scripts/database/init.sh
```

### 验证数据库

```bash
./scripts/database/verify.sh
```

### 数据库迁移

```bash
# 执行数据库迁移
./scripts/database/migrate.sh
```

### 数据库优化

```bash
./scripts/database/optimize.sh
```

## 📦 部署

### 本地部署

```bash
./scripts/deploy/deploy-local.sh
```

### 生产环境部署

```bash
./scripts/deploy/deploy-production.sh [target_server_ip]

# 例如
./scripts/deploy/deploy-production.sh 82.157.28.35
```

### 预发布环境部署

```bash
./scripts/deploy/deploy-staging.sh [target_server_ip]
```

## 🛠️ 工具脚本

### 环境检查

```bash
./scripts/bin/check-env.sh
```

检查：
- Python 版本和虚拟环境
- Node.js 和 npm
- PostgreSQL 数据库
- 端口可用性
- 依赖项完整性

## 📝 常见任务

### 完整部署流程（生产）

```bash
# 1. 检查环境
./scripts/bin/check-env.sh

# 2. 初始化数据库
./scripts/utils/setup-database.sh

# 3. 部署到生产环境
./scripts/deploy/deploy-production.sh 82.157.28.35
```

### 日常开发流程

```bash
# 1. 启动所有服务
./scripts/bin/start.sh

# 2. 开发...

# 3. 查看日志
tail -f logs/backend.log   # 后端日志
tail -f logs/frontend.log  # 前端日志
tail -f logs/client.log    # 客户端日志

# 4. 停止服务
./scripts/bin/stop.sh
```

## 📌 注意事项

### 脚本权限

所有脚本都已设置为可执行。如果遇到权限问题：

```bash
chmod +x scripts/bin/*.sh
chmod +x scripts/database/*.sh
chmod +x scripts/deploy/*.sh
chmod +x scripts/utils/*.sh
```

### 日志文件

- 后端日志: logs/backend.log
- 前端日志: logs/frontend.log
- 客户端日志: logs/client.log

