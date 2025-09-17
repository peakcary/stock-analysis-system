# 股票分析系统 v2.6.4

⚡ 高性能股票分析系统，支持TXT数据导入、概念分析、创新高检测

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

- 📊 TXT热度数据导入和分析
- 🏆 股票概念排行榜
- 📈 概念创新高检测
- 🔍 个股概念分析
- ⚡ 高性能数据库优化

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

- **管理端**: http://localhost:8006 (admin/admin123)
- **客户端**: http://localhost:8005
- **API**: http://localhost:3007

## 常见问题

**TXT导入失败**：运行 `./scripts/deployment/deploy.sh --migrate`

**端口冲突**：检查 3007、8005、8006 端口是否被占用

**数据库连接失败**：确保MySQL服务运行中

## 技术栈

- 后端：FastAPI + SQLAlchemy + MySQL
- 前端：React + TypeScript + Ant Design
- 部署：Docker支持