# 🔒 生产环境部署指南（安全版本）

> **警告**: 原始的部署脚本存在严重的安全隐患。本指南提供了改进的、生产级别的部署方案。

## 📋 目录

1. [快速开始](#快速开始)
2. [安全配置](#安全配置)
3. [部署流程](#部署流程)
4. [故障排查](#故障排查)
5. [最佳实践](#最佳实践)

---

## 快速开始

### 第1步：生成SSH密钥对

如果您还没有SSH密钥，首先生成一个：

```bash
# 生成SSH密钥（强烈推荐使用ed25519）
ssh-keygen -t ed25519 -f ~/.ssh/prod_key -N ""

# 设置正确的权限
chmod 600 ~/.ssh/prod_key
chmod 644 ~/.ssh/prod_key.pub
```

### 第2步：上传公钥到服务器

```bash
# 将公钥上传到服务器
ssh-copy-id -i ~/.ssh/prod_key.pub ubuntu@82.157.28.35
```

### 第3步：配置环境变量

创建一个 `.env.deploy` 文件来存储部署配置：

```bash
# 创建配置文件
cat > ~/.bash_profile.d/deploy_env << 'EOF'
# 部署配置
export DEPLOY_SERVER="82.157.28.35"
export DEPLOY_USER="ubuntu"
export DEPLOY_SSH_KEY="$HOME/.ssh/prod_key"
export DEPLOY_PATH="/opt/stock-analysis-system"
export MYSQL_ROOT_PASSWORD="your_secure_password_here"
EOF

# 加载配置
source ~/.bash_profile.d/deploy_env
```

### 第4步：测试SSH连接

```bash
# 测试连接
ssh -i $DEPLOY_SSH_KEY $DEPLOY_USER@$DEPLOY_SERVER "echo 'SSH连接成功'"
```

### 第5步：执行部署

```bash
# 先进行DRY RUN测试（不执行实际部署）
./scripts/deployment/deploy-production-secure.sh --dry-run

# 如果DRY RUN通过，执行真实部署
./scripts/deployment/deploy-production-secure.sh
```

---

## 安全配置

### 🔐 密钥管理

#### ❌ 不安全的做法

```bash
# ❌ 永远不要这样做！
sshpass -p "password" ssh ...
export MYSQL_PASSWORD="hardcoded_password"
./script.sh "database_password"
```

#### ✅ 安全的做法

```bash
# ✅ 使用SSH密钥认证
ssh -i ~/.ssh/prod_key ubuntu@server

# ✅ 使用环境变量
export MYSQL_ROOT_PASSWORD=$(aws secretsmanager get-secret-value --secret-id prod/mysql/root | jq -r '.SecretString')

# ✅ 使用密钥管理系统
vault kv get secret/prod/mysql
```

### 🔒 SSH密钥安全性

```bash
# 检查SSH密钥权限
ls -la ~/.ssh/prod_key
# 应该显示: -rw------- (600)

# 检查公钥权限
ls -la ~/.ssh/prod_key.pub
# 应该显示: -rw-r--r-- (644)

# 定期轮换密钥
# 1. 生成新密钥
# 2. 上传新公钥到服务器
# 3. 移除旧公钥
# 4. 删除旧密钥文件
```

### 🛡️ 防火墙配置

```bash
# 限制SSH访问的IP范围
sudo ufw allow from YOUR_IP to any port 22

# 更改SSH默认端口（可选）
sudo nano /etc/ssh/sshd_config
# Port 2222
sudo systemctl restart sshd
```

---

## 部署流程

### 完整部署步骤

```
┌─────────────────────────────────┐
│ 1. 环境验证                      │
│    - 检查SSH连接                 │
│    - 验证环境变量                 │
│    - 验证远程文件存在性           │
└────────────┬────────────────────┘
             │
┌────────────▼────────────────────┐
│ 2. 备份（可选）                   │
│    - MySQL数据库备份              │
│    - 验证备份完整性                │
└────────────┬────────────────────┘
             │
┌────────────▼────────────────────┐
│ 3. 代码更新                       │
│    - git fetch & reset            │
│    - 验证代码完整性                │
└────────────┬────────────────────┘
             │
┌────────────▼────────────────────┐
│ 4. Docker构建                    │
│    - 构建新镜像                   │
│    - 标记镜像                     │
└────────────┬────────────────────┘
             │
┌────────────▼────────────────────┐
│ 5. 启动服务                       │
│    - 启动容器                     │
│    - 等待服务就绪                 │
└────────────┬────────────────────┘
             │
┌────────────▼────────────────────┐
│ 6. 健康检查                       │
│    - 检查所有服务状态             │
│    - 运行测试                     │
└────────────┬────────────────────┘
             │
┌────────────▼────────────────────┐
│ 7. 完成                           │
│    - 生成部署报告                 │
│    - 保存日志                     │
└─────────────────────────────────┘
```

### 部署命令

```bash
# 模拟运行（推荐先执行）
./scripts/deployment/deploy-production-secure.sh --dry-run

# 执行部署
./scripts/deployment/deploy-production-secure.sh

# 跳过备份（谨慎！）
./scripts/deployment/deploy-production-secure.sh --skip-backup
```

### 查看日志

```bash
# 查看最新的部署日志
tail -f logs/deployment/deploy-*.log

# 查看特定的部署日志
cat logs/deployment/deploy-20251023_143022.log

# 查看远程服务日志
ssh -i $DEPLOY_SSH_KEY $DEPLOY_USER@$DEPLOY_SERVER \
    "docker-compose -f docker-compose.prod.yml logs -f backend"
```

---

## 故障排查

### 问题1：SSH连接失败

```bash
# 诊断命令
ssh -i $DEPLOY_SSH_KEY -v $DEPLOY_USER@$DEPLOY_SERVER "echo test"

# 常见原因和解决方案
# 1. SSH密钥不存在
ls -la $DEPLOY_SSH_KEY

# 2. SSH密钥权限错误
chmod 600 $DEPLOY_SSH_KEY

# 3. 公钥未上传到服务器
ssh-copy-id -i $DEPLOY_SSH_KEY.pub $DEPLOY_USER@$DEPLOY_SERVER

# 4. 服务器地址或用户名错误
echo "DEPLOY_SERVER=$DEPLOY_SERVER"
echo "DEPLOY_USER=$DEPLOY_USER"
```

### 问题2：部署超时

```bash
# 检查网络连接
ping -c 5 $DEPLOY_SERVER

# 查看远程系统资源
ssh -i $DEPLOY_SSH_KEY $DEPLOY_USER@$DEPLOY_SERVER \
    "free -h && df -h && top -bn1 | head -10"

# 检查Docker日志
ssh -i $DEPLOY_SSH_KEY $DEPLOY_USER@$DEPLOY_SERVER \
    "docker-compose -f /opt/stock-analysis-system/docker-compose.prod.yml logs --tail=50"
```

### 问题3：数据库连接失败

```bash
# 检查数据库密码
echo $MYSQL_ROOT_PASSWORD

# 测试数据库连接
ssh -i $DEPLOY_SSH_KEY $DEPLOY_USER@$DEPLOY_SERVER \
    "cd /opt/stock-analysis-system && \
     docker exec stock_mysql_prod \
     mysql -uroot -p'$MYSQL_ROOT_PASSWORD' -e 'SELECT 1'"
```

### 问题4：镜像构建失败

```bash
# 查看构建日志
ssh -i $DEPLOY_SSH_KEY $DEPLOY_USER@$DEPLOY_SERVER \
    "cd /opt/stock-analysis-system && \
     docker build -f backend/Dockerfile.prod backend/ 2>&1 | tail -50"

# 使用国内镜像源
ssh -i $DEPLOY_SSH_KEY $DEPLOY_USER@$DEPLOY_SERVER \
    "cd /opt/stock-analysis-system && \
     docker build -f backend/Dockerfile.prod.cn backend/"
```

---

## 最佳实践

### ✅ 部署前检查清单

- [ ] SSH密钥已生成并上传到服务器
- [ ] 环境变量已正确设置
- [ ] 已备份生产数据库（如有重要数据）
- [ ] 已测试SSH连接
- [ ] 已运行 `--dry-run` 验证部署流程
- [ ] 代码已推送到正确的分支
- [ ] 所有依赖已安装

### ✅ 部署中的最佳实践

```bash
# 1. 始终使用 DRY RUN
./scripts/deployment/deploy-production-secure.sh --dry-run

# 2. 运行时保持日志记录
# 日志自动保存到 logs/deployment/

# 3. 监控部署进度
ssh -i $DEPLOY_SSH_KEY $DEPLOY_USER@$DEPLOY_SERVER \
    "docker-compose -f /opt/stock-analysis-system/docker-compose.prod.yml ps"

# 4. 准备回滚计划
# 将备份位置记录下来以便需要时恢复
```

### ✅ 部署后验证

```bash
# 1. 检查所有容器状态
ssh -i $DEPLOY_SSH_KEY $DEPLOY_USER@$DEPLOY_SERVER \
    "docker-compose -f /opt/stock-analysis-system/docker-compose.prod.yml ps"

# 2. 运行健康检查
ssh -i $DEPLOY_SSH_KEY $DEPLOY_USER@$DEPLOY_SERVER \
    "curl http://localhost:8000/health && \
     curl http://localhost/nginx-health"

# 3. 检查应用日志
ssh -i $DEPLOY_SSH_KEY $DEPLOY_USER@$DEPLOY_SERVER \
    "docker-compose -f /opt/stock-analysis-system/docker-compose.prod.yml logs --tail=50 backend"

# 4. 监控资源使用
ssh -i $DEPLOY_SSH_KEY $DEPLOY_USER@$DEPLOY_SERVER \
    "docker stats --no-stream"
```

### ✅ 定期维护

```bash
# 周期性备份
0 2 * * * cd /opt/stock-analysis-system && docker exec stock_mysql_prod mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" --all-databases > /backups/mysql_$(date +\%Y\%m\%d).sql

# 日志轮转
find /opt/stock-analysis-system/logs -name "*.log" -mtime +30 -delete

# 定期更新依赖
0 3 * * 0 cd /opt/stock-analysis-system && docker-compose pull && docker-compose up -d
```

---

## 安全修复总结

| 问题 | 原始做法 | 改进方案 |
|------|--------|--------|
| 密码管理 | 硬编码密码 | 环境变量 + 密钥管理系统 |
| SSH认证 | sshpass + 密码 | SSH密钥对 |
| 错误处理 | 无 | 完整的错误捕获和日志 |
| 日志记录 | 无 | 自动日志保存到 logs/deployment |
| 备份验证 | 无 | 数据库备份检查 |
| 健康检查 | 简单HTTP检查 | 多层服务检查 |
| 回滚机制 | 无 | 备份恢复说明 |

---

## 常用命令参考

```bash
# 环境配置
source ~/.bash_profile.d/deploy_env

# 测试SSH连接
ssh -i $DEPLOY_SSH_KEY $DEPLOY_USER@$DEPLOY_SERVER "echo 'OK'"

# DRY RUN部署
./scripts/deployment/deploy-production-secure.sh --dry-run

# 执行部署
./scripts/deployment/deploy-production-secure.sh

# 查看部署日志
tail -f logs/deployment/deploy-*.log

# 远程服务状态
ssh -i $DEPLOY_SSH_KEY $DEPLOY_USER@$DEPLOY_SERVER \
    "docker-compose -f /opt/stock-analysis-system/docker-compose.prod.yml ps"

# 远程健康检查
ssh -i $DEPLOY_SSH_KEY $DEPLOY_USER@$DEPLOY_SERVER \
    "curl http://localhost:8000/health"
```

---

## 下一步

1. ✅ 完成 SSH 密钥配置
2. ✅ 设置环境变量
3. ✅ 运行 DRY RUN 部署
4. ✅ 审查日志输出
5. ✅ 执行真实部署
6. ✅ 进行部署后验证
7. ✅ 设置定期备份任务

---

## 获取帮助

如果遇到问题，请：

1. 查看部署日志：`logs/deployment/deploy-*.log`
2. 查阅 [故障排查](#故障排查) 章节
3. 检查 [最佳实践](#最佳实践) 中的检查清单
4. 联系技术支持

**注意**: 所有密码和敏感信息应该通过环境变量或密钥管理系统管理，**永远不要**在脚本中硬编码！
