# 云服务器部署指南

## 概述

本指南将帮助您将股票分析系统部署到云服务器（如阿里云、腾讯云、AWS等）。系统采用Docker容器化部署，支持自动化SSL证书管理和生产环境优化。

## 前置条件

### 服务器要求
- **CPU**: 2核心或以上
- **内存**: 4GB RAM 或以上 (推荐8GB)
- **存储**: 20GB 或以上 SSD
- **操作系统**: Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- **网络**: 公网IP，开放80、443端口

### 域名要求
- 已购买并解析到服务器IP的域名
- 建议配置：
  - `your-domain.com` -> 管理端
  - `app.your-domain.com` -> 用户端 (可选)

## 快速部署

### 方式一：一键部署脚本

1. **上传项目文件到服务器**
```bash
# 方式1: 使用Git (推荐)
ssh root@your-server-ip
cd /opt
git clone https://github.com/your-username/stock-analysis-system.git
cd stock-analysis-system

# 方式2: 使用scp上传
scp -r ./stock-analysis-system root@your-server-ip:/opt/
```

2. **运行一键部署脚本**
```bash
cd /opt/stock-analysis-system
chmod +x scripts/deploy-server.sh

# 带域名参数运行
./scripts/deploy-server.sh --domain your-domain.com --email your-email@example.com

# 或者交互式运行
./scripts/deploy-server.sh
```

脚本将自动完成：
- 系统更新和依赖安装
- Docker 和 Docker Compose 安装
- 防火墙配置
- SSL证书申请和配置
- 服务部署和启动

### 方式二：手动部署

如果需要更细致的控制，可以按以下步骤手动部署：

#### 1. 准备服务器环境

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装必要工具
sudo apt install -y curl wget git ufw

# 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### 2. 配置防火墙

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
```

#### 3. 部署项目

```bash
# 创建项目目录
sudo mkdir -p /opt/stock-analysis-system
sudo chown -R $USER:$USER /opt/stock-analysis-system
cd /opt/stock-analysis-system

# 上传或克隆项目文件
# ... (上传项目文件)

# 配置环境变量
cp .env.prod .env.production
nano .env.production  # 编辑配置
```

#### 4. 申请SSL证书

```bash
# 安装Certbot
sudo apt install -y snapd
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot

# 申请证书 (需要先停止占用80端口的服务)
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com
```

#### 5. 启动服务

```bash
# 使用生产环境配置启动
docker-compose -f docker-compose.prod.yml --env-file .env.production up -d

# 检查服务状态
docker-compose -f docker-compose.prod.yml ps
```

## 配置详解

### 环境变量配置

编辑 `.env.prod` 文件，重点配置以下项目：

```bash
# 域名配置
DOMAIN=your-domain.com
EMAIL=your-email@example.com

# 数据库安全配置
MYSQL_ROOT_PASSWORD=your_secure_random_password_here
MYSQL_PASSWORD=another_secure_password_here

# JWT密钥 (32字符以上随机字符串)
SECRET_KEY=your_very_secure_secret_key_at_least_32_characters_long

# 微信支付配置 (如果使用)
WECHAT_APPID=your_actual_wechat_appid
WECHAT_MCHID=your_actual_mchid
WECHAT_KEY=your_actual_wechat_key
WECHAT_NOTIFY_URL=https://your-domain.com/api/v1/payment/notify

# Redis密码
REDIS_PASSWORD=your_redis_password
```

### Nginx配置

生产环境使用 `nginx/nginx.prod.conf`，主要特性：
- HTTPS强制重定向
- SSL/TLS配置优化
- Gzip压缩
- 静态文件缓存
- API限流保护
- 安全头设置

如需自定义域名，修改配置文件中的：
```nginx
server_name your-domain.com www.your-domain.com;
```

## 服务管理

### 常用命令

```bash
cd /opt/stock-analysis-system

# 查看服务状态
docker-compose -f docker-compose.prod.yml ps

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f

# 重启服务
docker-compose -f docker-compose.prod.yml restart

# 停止服务
docker-compose -f docker-compose.prod.yml down

# 更新服务
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

### 健康检查

```bash
# 检查各服务健康状态
curl -f http://localhost:8000/health    # 后端健康检查
curl -f https://your-domain.com/nginx-health  # Nginx健康检查

# 查看资源使用情况
docker stats
```

### 数据库管理

```bash
# 连接数据库
docker-compose -f docker-compose.prod.yml exec mysql mysql -u root -p

# 备份数据库
docker-compose -f docker-compose.prod.yml exec mysql mysqldump -u root -p stock_analysis > backup_$(date +%Y%m%d).sql

# 恢复数据库
docker-compose -f docker-compose.prod.yml exec -T mysql mysql -u root -p stock_analysis < backup.sql
```

## SSL证书管理

### 自动续期

```bash
# 设置自动续期 cron 任务
echo "0 12 * * * /usr/bin/certbot renew --quiet && docker-compose -f /opt/stock-analysis-system/docker-compose.prod.yml restart nginx" | crontab -

# 手动续期
sudo certbot renew --dry-run
```

### 证书更新后重启Nginx

```bash
sudo certbot renew --post-hook "cd /opt/stock-analysis-system && docker-compose -f docker-compose.prod.yml restart nginx"
```

## 监控和日志

### 日志管理

```bash
# 查看应用日志
docker-compose -f docker-compose.prod.yml logs backend
docker-compose -f docker-compose.prod.yml logs frontend
docker-compose -f docker-compose.prod.yml logs nginx

# 日志轮转配置
sudo nano /etc/docker/daemon.json
```

添加日志配置：
```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

### 系统监控

```bash
# 查看服务器资源
htop
df -h
free -h

# 查看Docker资源使用
docker system df
docker stats
```

## 性能优化

### 服务器优化

```bash
# 增加文件描述符限制
echo "* soft nofile 65535" >> /etc/security/limits.conf
echo "* hard nofile 65535" >> /etc/security/limits.conf

# 优化内核参数
echo "net.core.somaxconn = 1024" >> /etc/sysctl.conf
echo "net.ipv4.tcp_max_syn_backlog = 2048" >> /etc/sysctl.conf
sysctl -p
```

### Docker资源限制

在 `docker-compose.prod.yml` 中添加：
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          memory: 512M
```

## 安全加固

### 基础安全设置

```bash
# 禁用root远程登录
sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl restart sshd

# 配置fail2ban
sudo apt install -y fail2ban
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# 启用自动安全更新
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

### Docker安全

```bash
# 创建专用用户
sudo useradd -r -s /bin/false dockerapp
sudo usermod -aG docker dockerapp

# 使用非root用户运行容器
# 在Dockerfile中添加: USER dockerapp
```

## 备份策略

### 自动备份脚本

创建 `/opt/backup.sh`：
```bash
#!/bin/bash
cd /opt/stock-analysis-system

# 备份数据库
docker-compose -f docker-compose.prod.yml exec -T mysql mysqldump -u root -p$MYSQL_ROOT_PASSWORD stock_analysis > backup/db_$(date +%Y%m%d_%H%M%S).sql

# 备份上传文件
tar -czf backup/uploads_$(date +%Y%m%d_%H%M%S).tar.gz backend/uploads/

# 清理7天前的备份
find backup/ -name "*.sql" -mtime +7 -delete
find backup/ -name "*.tar.gz" -mtime +7 -delete
```

设置定时任务：
```bash
chmod +x /opt/backup.sh
echo "0 2 * * * /opt/backup.sh" | crontab -
```

## 故障排查

### 常见问题

1. **SSL证书申请失败**
```bash
# 检查域名解析
nslookup your-domain.com
# 检查80端口占用
netstat -tulpn | grep :80
```

2. **数据库连接失败**
```bash
# 检查数据库服务
docker-compose -f docker-compose.prod.yml logs mysql
# 测试数据库连接
docker-compose -f docker-compose.prod.yml exec backend python -c "from app.core.database import engine; print('DB OK')"
```

3. **前端访问404**
```bash
# 检查Nginx配置
docker-compose -f docker-compose.prod.yml exec nginx nginx -t
# 查看Nginx日志
docker-compose -f docker-compose.prod.yml logs nginx
```

4. **内存不足**
```bash
# 添加swap分区
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### 紧急恢复

```bash
# 快速重启所有服务
cd /opt/stock-analysis-system
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d

# 从备份恢复数据库
docker-compose -f docker-compose.prod.yml exec -T mysql mysql -u root -p stock_analysis < backup/latest_backup.sql
```

## 访问地址

部署完成后，可通过以下地址访问：

- **管理端**: https://your-domain.com
- **用户端**: https://app.your-domain.com (如果配置了子域名)
- **API文档**: https://your-domain.com/docs
- **API接口**: https://your-domain.com/api/v1/

## 维护建议

1. **定期更新**
   - 每周检查并更新Docker镜像
   - 每月更新系统安全补丁

2. **监控告警**
   - 设置服务器资源监控
   - 配置SSL证书过期提醒

3. **数据备份**
   - 每日自动备份数据库
   - 每周备份完整应用数据

4. **安全审计**
   - 定期检查系统日志
   - 监控异常访问记录

## 技术支持

如遇到部署问题，可以：
1. 查看应用日志排查错误
2. 检查系统资源使用情况
3. 验证网络和防火墙配置
4. 确认域名DNS解析状态

部署成功后，记住保存好数据库密码、SSL证书位置等重要信息。