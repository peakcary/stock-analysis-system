# 股票分析系统 v2.7.0

⚡ 高性能股票分析系统，支持多格式数据导入、概念分析、个股查询、用户权限管理

## 快速开始

```bash
# 1. 部署系统
./scripts/deployment/deploy.sh

# 2. 启动服务
./scripts/deployment/start.sh

# 3. 访问系统
# 管理端: http://localhost:8006 (admin/admin123)
# 客户端: http://localhost:8005
```

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

## 管理命令

```bash
# 服务管理
./scripts/deployment/start.sh    # 启动服务
./scripts/deployment/stop.sh     # 停止服务
./scripts/deployment/status.sh   # 检查状态

# 系统管理
./scripts/deployment/deploy.sh --migrate  # 仅更新数据库
./scripts/deployment/deploy.sh --help     # 查看帮助

# 服务器部署
./scripts/deployment/deploy-to-server.sh  # 一键部署到服务器
```

## 服务地址

- **后端API**: http://localhost:8000
- **管理端**: http://localhost:8007 (admin/admin123)
- **客户端**: http://localhost:8008

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

**数据导入失败**：运行 `./scripts/deployment/deploy.sh --migrate`

**端口冲突**：检查 8000、8007、8008 端口是否被占用

**数据库连接失败**：确保MySQL服务运行中

**查询次数不足**：联系管理员升级会员或购买查询包

**API权限错误**：检查用户登录状态和token有效性

## 技术栈

- 后端：FastAPI + SQLAlchemy + MySQL
- 前端：React + TypeScript + Ant Design
- 部署：Docker支持