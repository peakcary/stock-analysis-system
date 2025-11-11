# 股票分析系统 v2.7.0

⚡ 高性能股票分析系统，支持多格式数据导入、概念分析、个股查询、会员支付管理

## 🚀 快速开始

### 最简单的方式（推荐）

```bash
# 一键启动（包含环境检查和依赖安装）
./start.sh
```

### 或者分步操作

```bash
# 1. 检查环境
./check-env.sh

# 2. 快速安装依赖（如需要）
./quick-deploy.sh

# 3. 启动服务
./start.sh
```

### 访问系统

启动完成后，访问以下地址：

| 服务 | 地址 | 账户 | 密码 |
|------|------|------|------|
| 后端 API | http://localhost:3007 | - | - |
| API 文档 | http://localhost:3007/docs | - | - |
| 管理端 | http://localhost:8006 | admin | admin123 |
| 客户端 | http://localhost:8005 | fullaccess_user | fullaccess123 |

## 环境要求

- Node.js 16+
- Python 3.8+
- MySQL 8.0+

```bash
# macOS 快速安装
brew install node mysql
brew services start mysql
```

## 主要功能

### 数据导入与分析
- 📊 多格式数据导入 (TXT、TTV、EEE)
- 🔄 智能覆盖检测和确认机制
- 📈 概念创新高检测
- ⚡ 高性能数据库优化

### 查询与分析
- 🔍 个股查询系统 (支持股票代码搜索)
- 🏷️ 概念展示与关联股票查看
- 🏆 股票概念排行榜
- 📱 响应式设计，支持移动端

### 用户与权限管理
- 👥 客户端用户管理系统
- 🎯 查询次数控制和扣费机制
- 💳 会员等级管理 (免费/专业/高级)
- 📊 用户行为统计和分析

### 支付系统
- 💰 完整的会员支付功能
- 🔐 微信支付V3安全集成
- 📈 支付数据统计分析
- ⏰ 订单超时自动处理
- 🛡️ 多层次安全防护机制

## 📋 脚本命令

### 核心命令

| 命令 | 说明 | 用途 |
|------|------|------|
| `./start.sh` | 启动服务 | 一键启动所有服务（推荐） |
| `./stop.sh` | 停止服务 | 优雅地停止所有服务 |
| `./restart.sh` | 重启服务 | 重启所有服务 |
| `./status.sh` | 检查状态 | 查看服务运行状态 |
| `./check-env.sh` | 环境检查 | 验证系统环境是否满足要求 |
| `./quick-deploy.sh` | 快速部署 | 快速安装依赖 |

### 传统命令（兼容）

```bash
# 旧脚本（兼容但不推荐）
./start-dev.sh     # 启动开发服务
./stop-dev.sh      # 停止开发服务

# Docker环境
docker-compose up -d              # 启动容器服务
docker-compose down               # 停止容器服务
docker-compose logs -f [service]  # 查看服务日志
```

### 常见操作

```bash
# 启动所有服务
./start.sh

# 停止所有服务
./stop.sh

# 重启所有服务
./restart.sh

# 检查服务状态
./status.sh

# 查看日志
tail -f logs/backend.log      # 后端日志
tail -f logs/frontend.log     # 前端日志
tail -f logs/client.log       # 客户端日志

# 查看所有日志
tail -f logs/*.log
```

## 服务地址

- **后端API**: http://localhost:3007
- **API文档**: http://localhost:3007/docs
- **管理端**: http://localhost:8006 (admin/admin123)
- **客户端**: http://localhost:8005 (fullaccess_user/fullaccess123)

## 测试账户

### 管理员账户
- 用户名：`admin`
- 密码：`admin123`
- 权限：系统管理、用户管理、数据导入

### 客户端测试账户
- 用户名：`fullaccess_user`
- 密码：`fullaccess123`
- 权限：Premium会员，100000+查询次数

## 常见问题

**数据导入失败**：运行 `python init_database.py` 初始化数据库

**端口冲突**：检查 3007、8006、8005 端口是否被占用

**数据库连接失败**：确保MySQL服务运行中 `docker-compose up -d mysql`

**查询次数不足**：联系管理员升级会员或购买查询包

**支付功能异常**：检查微信支付配置和网络连接

**API权限错误**：检查用户登录状态和token有效性

## 📚 文档指南

项目包含详细的文档和指南：

| 文档 | 说明 | 何时查看 |
|------|------|--------|
| **QUICKSTART.md** | 快速开始指南 | 第一次启动系统 |
| **TROUBLESHOOTING.md** | 故障排除指南 | 遇到问题或错误 |
| **DEVELOPMENT_PROGRESS.md** | 开发进度文档 | 了解项目功能和版本 |
| **README.md** | 项目主文档 | 了解项目概览 |

### 常见问题速查

- ❌ **无法启动？** → 查看 `QUICKSTART.md` [一键启动](#-快速开始)
- ❌ **端口被占用？** → 查看 `TROUBLESHOOTING.md` [端口问题](#端口问题)
- ❌ **数据库连接失败？** → 查看 `TROUBLESHOOTING.md` [数据库问题](#数据库问题)
- ❌ **依赖安装失败？** → 查看 `TROUBLESHOOTING.md` [依赖问题](#依赖问题)
- ❌ **API 返回错误？** → 查看 `TROUBLESHOOTING.md` [API 问题](#api-问题)

## 🛠️ 技术栈

- **后端**: FastAPI + SQLAlchemy + MySQL + Redis
- **前端**: React 18 + TypeScript + Ant Design + Vite
- **部署**: Docker + Nginx + Linux
- **支付**: 微信支付 V2/V3
- **缓存**: Redis + 内存缓存

## 📞 获取帮助

1. **查看文档**:
   ```bash
   # 快速开始指南
   cat QUICKSTART.md

   # 故障排除指南
   cat TROUBLESHOOTING.md

   # 开发进度
   cat DEVELOPMENT_PROGRESS.md
   ```

2. **检查环境**:
   ```bash
   ./check-env.sh
   ```

3. **查看日志**:
   ```bash
   tail -f logs/backend.log
   tail -f logs/frontend.log
   tail -f logs/client.log
   ```

4. **API 文档**:
   访问 http://localhost:3007/docs 查看完整的 API 文档