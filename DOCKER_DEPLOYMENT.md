# Docker 部署指南

## 项目结构

本项目包含以下服务：
- **MySQL**: 数据库服务
- **Backend**: FastAPI 后端服务 (端口: 8000)
- **Frontend**: 管理端 React 应用 (端口: 3000)
- **Client**: 用户端 React 应用 (端口: 8006)
- **Nginx**: 反向代理服务 (可选，生产环境)

## 快速开始

### 1. 环境准备

确保已安装：
- Docker Engine 20.10+
- Docker Compose V2

### 2. 克隆项目并配置环境变量

```bash
git clone <repository-url>
cd stock-analysis-system

# 检查并调整 .env 文件中的配置
cp .env.example .env  # 如果有 example 文件
```

### 3. 启动所有服务

```bash
# 启动开发环境
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 4. 访问应用

- 管理端：http://localhost:3000
- 用户端：http://localhost:8006
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

## 服务详情

### MySQL 数据库
- 容器名：`stock_analysis_mysql`
- 端口：3306
- 数据库：`stock_analysis`
- 用户：`stockuser` / 密码：`stockpass`
- Root 密码：`root123`

### 后端服务 (FastAPI)
- 容器名：`stock_analysis_backend`
- 端口：8000
- 基于 Python 3.11
- 自动重载开发模式

### 前端服务 (管理端)
- 容器名：`stock_analysis_frontend`
- 端口：3000
- React + Vite
- 热重载开发模式

### 客户端服务 (用户端)
- 容器名：`stock_analysis_client`
- 端口：8006
- React + Vite
- 热重载开发模式

## 常用命令

### 服务管理

```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 重启某个服务
docker-compose restart backend

# 查看服务状态
docker-compose ps

# 查看服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f client
```

### 数据库操作

```bash
# 连接数据库
docker-compose exec mysql mysql -u root -p stock_analysis

# 导入数据库
docker-compose exec mysql mysql -u root -p stock_analysis < database/init.sql

# 备份数据库
docker-compose exec mysql mysqldump -u root -p stock_analysis > backup.sql
```

### 开发调试

```bash
# 进入后端容器
docker-compose exec backend bash

# 进入前端容器
docker-compose exec frontend sh

# 进入客户端容器
docker-compose exec client sh

# 查看容器内文件
docker-compose exec backend ls -la /app
```

## 生产环境部署

### 1. 使用生产配置

```bash
# 使用生产环境 docker-compose 配置
docker-compose -f docker-compose.prod.yml up -d

# 或启用 nginx 代理
docker-compose --profile production up -d
```

### 2. 环境变量配置

生产环境需要修改 `.env` 文件：

```bash
# 数据库安全配置
MYSQL_ROOT_PASSWORD=your_secure_password
MYSQL_PASSWORD=your_secure_password

# JWT 配置
SECRET_KEY=your_very_secure_secret_key_at_least_32_characters

# 环境标识
ENVIRONMENT=production
DEBUG=false

# 微信支付配置
WECHAT_APPID=your_actual_wechat_appid
WECHAT_MCHID=your_actual_mchid
WECHAT_KEY=your_actual_key
WECHAT_NOTIFY_URL=https://your-domain.com/api/v1/payment/notify
```

### 3. SSL/HTTPS 配置

配置 nginx SSL 证书：

```bash
# 将 SSL 证书文件放置到 nginx/certs/ 目录
mkdir -p nginx/certs
cp your-cert.pem nginx/certs/
cp your-key.pem nginx/certs/
```

## 故障排查

### 常见问题

1. **端口冲突**
   ```bash
   # 检查端口占用
   netstat -tulpn | grep :3000
   
   # 修改 docker-compose.yml 中的端口映射
   ports:
     - "3001:3000"  # 将本地端口改为 3001
   ```

2. **数据库连接失败**
   ```bash
   # 检查数据库服务状态
   docker-compose logs mysql
   
   # 检查数据库连接
   docker-compose exec backend python -c "from app.core.database import engine; print(engine)"
   ```

3. **前端构建失败**
   ```bash
   # 清理 node_modules 并重新构建
   docker-compose down
   docker-compose build --no-cache frontend
   docker-compose up -d
   ```

4. **权限问题**
   ```bash
   # 修复文件权限
   sudo chown -R $USER:$USER .
   chmod -R 755 .
   ```

### 日志查看

```bash
# 查看所有服务日志
docker-compose logs

# 查看特定服务日志
docker-compose logs backend
docker-compose logs frontend
docker-compose logs client
docker-compose logs mysql

# 实时查看日志
docker-compose logs -f --tail=100
```

### 数据持久化

数据卷挂载：
- `mysql_data`: MySQL 数据文件
- `backend_uploads`: 后端上传文件

```bash
# 备份数据卷
docker run --rm -v stock_analysis_mysql_data:/data -v $(pwd):/backup ubuntu tar czf /backup/mysql_backup.tar.gz /data

# 恢复数据卷
docker run --rm -v stock_analysis_mysql_data:/data -v $(pwd):/backup ubuntu tar xzf /backup/mysql_backup.tar.gz -C /
```

## 性能优化

### 1. 镜像优化

```bash
# 清理未使用的镜像
docker system prune -af

# 查看镜像大小
docker images
```

### 2. 资源限制

在 `docker-compose.yml` 中添加资源限制：

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          memory: 256M
```

### 3. 健康检查

```yaml
services:
  backend:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## 监控和日志

### 1. 日志管理

```bash
# 配置日志轮转
echo '{"log-driver":"json-file","log-opts":{"max-size":"10m","max-file":"3"}}' | sudo tee /etc/docker/daemon.json
sudo systemctl restart docker
```

### 2. 监控指标

```bash
# 查看容器资源使用情况
docker stats

# 查看特定容器资源使用
docker stats stock_analysis_backend
```

## 安全建议

1. **定期更新基础镜像**
2. **使用非 root 用户运行容器**
3. **限制容器权限**
4. **定期备份数据**
5. **使用 secrets 管理敏感信息**
6. **配置防火墙规则**

## 更新和维护

```bash
# 更新服务
git pull
docker-compose build --no-cache
docker-compose up -d

# 查看更新状态
docker-compose ps
```