# Docker 开发环境使用指南

## 🐳 项目概述

本项目使用 Docker 和 Docker Compose 来统一开发环境，解决了开发环境不一致、配置冲突等问题。

## 🚀 快速开始

### 1. 安装 Docker
确保你的系统已安装 Docker 和 Docker Compose：

```bash
# 检查 Docker 是否安装
docker --version
docker-compose --version

# 如果未安装，请访问 https://docs.docker.com/get-docker/
```

### 2. 启动开发环境

```bash
# 启动所有服务
./docker-start.sh start

# 或者直接使用 docker-compose
docker-compose up -d
```

### 3. 访问服务

启动成功后，可以通过以下地址访问各个服务：

- **前端管理端**: http://localhost:3000
- **前端用户端**: http://localhost:8006  
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **数据库**: localhost:3306
- **Redis**: localhost:6379

## 📋 服务架构

```mermaid
graph TB
    A[用户浏览器] --> B[前端管理端:3000]
    A --> C[前端用户端:8006]
    B --> D[后端API:8000]
    C --> D
    D --> E[MySQL:3306]
    D --> F[Redis:6379]
    
    G[Docker启动脚本] --> H[docker-compose.yml]
    H --> I[MySQL容器]
    H --> J[Redis容器]
    H --> K[后端容器]
    H --> L[前端容器]
```

## 🗄️ 数据库配置

### MySQL 配置
- **主机**: mysql
- **端口**: 3306
- **数据库名**: stock_analysis_dev
- **用户名**: dev_user
- **密码**: dev_password
- **Root密码**: dev_root_password

### Redis 配置
- **主机**: redis
- **端口**: 6379
- **数据库**: 0

## 🔧 常用命令

### 启动脚本命令
```bash
# 启动所有服务
./docker-start.sh start

# 停止所有服务
./docker-start.sh stop

# 重启所有服务
./docker-start.sh restart

# 清理容器和镜像
./docker-start.sh clean

# 查看日志
./docker-start.sh logs [service]

# 查看服务状态
./docker-start.sh status

# 进入容器
./docker-start.sh shell [service]
```

### Docker Compose 命令
```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 重启指定服务
docker-compose restart backend

# 查看日志
docker-compose logs -f backend

# 进入容器
docker-compose exec backend bash

# 构建镜像
docker-compose build

# 查看容器状态
docker-compose ps
```

## 🛠️ 开发工作流

### 1. 日常开发
```bash
# 启动环境
./docker-start.sh start

# 查看日志
./docker-start.sh logs backend

# 代码修改后，后端会自动重载（热重载）
# 前端修改后，浏览器会自动刷新
```

### 2. 数据库操作
```bash
# 进入 MySQL 容器
./docker-start.sh shell mysql

# 连接数据库
mysql -u dev_user -p

# 或者使用宿主机连接
mysql -h localhost -P 3306 -u dev_user -p
```

### 3. Redis 操作
```bash
# 进入 Redis 容器
./docker-start.sh shell redis

# 连接 Redis
redis-cli
```

## 📁 文件结构

```
stock-analysis-system/
├── docker-compose.yml          # Docker Compose 配置
├── docker-start.sh            # Docker 启动脚本
├── .env.docker                # Docker 环境变量
├── backend/
│   ├── Dockerfile            # 后端 Dockerfile
│   ├── requirements.txt      # Python 依赖
│   └── app/
│       └── core/
│           └── config.py     # 配置文件
├── client/
│   ├── Dockerfile            # 前端 Dockerfile
│   └── ...                   # 前端代码
├── database/
│   └── init.sql             # 数据库初始化脚本
└── logs/                    # 日志目录
```

## 🔍 故障排除

### 1. 端口冲突
```bash
# 检查端口占用
lsof -i :3000
lsof -i :8000
lsof -i :8006
lsof -i :3306
lsof -i :6379

# 杀死占用进程
kill -9 <PID>
```

### 2. 容器启动失败
```bash
# 查看容器日志
docker-compose logs mysql
docker-compose logs backend
docker-compose logs redis

# 检查容器状态
docker-compose ps

# 重启容器
docker-compose restart [service]
```

### 3. 数据库连接问题
```bash
# 检查 MySQL 容器状态
docker-compose exec mysql mysqladmin ping

# 检查网络连接
docker-compose exec backend ping mysql
```

### 4. 权限问题
```bash
# 确保脚本有执行权限
chmod +x docker-start.sh

# 确保目录权限
chmod 755 backend
chmod 755 client
```

## 🎯 生产环境部署

### 1. 生产环境配置
```bash
# 使用生产环境配置
cp .env.prod .env

# 启动生产环境
docker-compose --profile production up -d
```

### 2. 数据迁移
```bash
# 备份开发环境数据
docker-compose exec mysql mysqldump -u dev_user -p stock_analysis_dev > backup.sql

# 恢复到生产环境
docker-compose --profile production exec mysql mysql -u prod_user -p stock_analysis < backup.sql
```

## 💡 最佳实践

1. **环境隔离**: 使用 Docker 确保开发和生产环境一致
2. **数据持久化**: 使用 Docker volumes 持久化数据库数据
3. **健康检查**: 配置健康检查确保服务可用性
4. **日志管理**: 使用 Docker logs 统一管理日志
5. **安全配置**: 使用专用数据库用户，避免使用 root

## 🔄 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DATABASE_URL` | 数据库连接URL | `mysql+pymysql://dev_user:dev_password@mysql:3306/stock_analysis_dev` |
| `REDIS_URL` | Redis连接URL | `redis://redis:6379` |
| `DEBUG` | 调试模式 | `True` |
| `SECRET_KEY` | JWT密钥 | `dev_secret_key_change_in_production` |
| `ENVIRONMENT` | 环境类型 | `development` |

## 📞 支持

如果遇到问题，请检查：
1. Docker 和 Docker Compose 是否正确安装
2. 端口是否被占用
3. 环境变量是否正确配置
4. 容器日志是否有错误信息

---

**注意**: 此配置仅用于开发环境，生产环境部署需要额外的安全配置和优化。