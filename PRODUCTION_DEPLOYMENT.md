# 生产环境部署指南 - qwquant.com

## 📋 部署概览

- **域名：** https://qwquant.com
- **微信AppID：** wx629c41da78273de4
- **商户号：** 1725935616
- **支付回调：** https://qwquant.com/api/v1/payment/notify

---

## 🚀 快速部署

### 方式1：使用自动部署脚本（推荐）

```bash
# 1. 在服务器上执行
cd /Users/peakom/work/stock-analysis-system
./deploy-production.sh
```

脚本会自动完成以下步骤：
- ✅ 检查必要文件
- ✅ 验证域名解析
- ✅ 获取SSL证书
- ✅ 备份现有数据
- ✅ 启动Docker服务
- ✅ 验证部署结果
- ✅ 设置证书自动续期

---

### 方式2：手动部署

#### 步骤1：准备服务器

**系统要求：**
- Ubuntu 20.04+ / CentOS 7+
- 2GB+ RAM
- 20GB+ 磁盘空间
- 公网IP地址

**安装必要软件：**
```bash
# Docker
curl -fsSL https://get.docker.com | sh
sudo systemctl start docker
sudo systemctl enable docker

# Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Certbot (SSL证书)
sudo apt update
sudo apt install certbot -y
```

---

#### 步骤2：配置域名DNS

登录域名管理平台，添加DNS记录：

```
类型: A
主机记录: @
记录值: 你的服务器公网IP
TTL: 600

类型: A
主机记录: www
记录值: 你的服务器公网IP
TTL: 600
```

**验证DNS解析：**
```bash
dig +short qwquant.com
# 应该返回你的服务器IP
```

---

#### 步骤3：获取SSL证书

```bash
# 停止占用80端口的服务
sudo systemctl stop nginx || true
sudo lsof -ti:80 | xargs sudo kill -9 || true

# 获取证书
sudo certbot certonly --standalone \
  -d qwquant.com \
  -d www.qwquant.com \
  --email your-email@example.com \
  --agree-tos \
  --non-interactive

# 验证证书
sudo certbot certificates
```

证书位置：
- `/etc/letsencrypt/live/qwquant.com/fullchain.pem`
- `/etc/letsencrypt/live/qwquant.com/privkey.pem`

---

#### 步骤4：配置环境变量

**编辑 `.env.prod`：**
```bash
cd /Users/peakom/work/stock-analysis-system
cp .env.prod .env.prod.local
vi .env.prod.local
```

**必须修改的配置：**
```bash
EMAIL=your-email@example.com  # 你的邮箱

# 设置强密码
MYSQL_ROOT_PASSWORD=生成一个强密码
MYSQL_PASSWORD=生成一个强密码
REDIS_PASSWORD=生成一个强密码
```

**生成强密码：**
```bash
openssl rand -base64 32
```

---

#### 步骤5：上传项目文件到服务器

```bash
# 在本地打包
cd /Users/peakom/work/stock-analysis-system
tar czf stock-system.tar.gz \
  --exclude='node_modules' \
  --exclude='venv' \
  --exclude='.git' \
  --exclude='*.log' \
  .

# 上传到服务器
scp stock-system.tar.gz user@your-server-ip:/opt/

# 在服务器上解压
ssh user@your-server-ip
cd /opt
tar xzf stock-system.tar.gz
cd stock-analysis-system
```

---

#### 步骤6：启动服务

```bash
cd /opt/stock-analysis-system

# 使用生产配置启动
docker-compose -f docker-compose.prod.yml up -d --build

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f
```

---

#### 步骤7：验证部署

**检查服务状态：**
```bash
docker-compose -f docker-compose.prod.yml ps
```

预期输出：
```
Name                    State    Ports
stock_backend_prod     Up       0.0.0.0:8000->8000/tcp
stock_mysql_prod       Up       0.0.0.0:3306->3306/tcp
stock_nginx_prod       Up       0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
stock_redis_prod       Up       0.0.0.0:6379->6379/tcp
```

**测试访问：**
```bash
# 测试HTTP（应该重定向到HTTPS）
curl -I http://qwquant.com

# 测试HTTPS
curl -I https://qwquant.com

# 测试API
curl https://qwquant.com/api/v1/health

# 测试支付配置
docker-compose -f docker-compose.prod.yml exec backend python check_payment_config.py
```

---

## 🔧 微信支付配置

### 步骤1：登录微信商户平台

网址：https://pay.weixin.qq.com/

使用商户号 `1725935616` 登录

---

### 步骤2：关联AppID

1. 进入 **产品中心** → **AppID账号管理**
2. 检查 `wx629c41da78273de4` 是否在列表中
3. 如果没有，点击 **新增关联AppID**：
   - 输入：`wx629c41da78273de4`
   - 选择：授权类型（根据实际情况选择）
   - 提交审核（通常即时通过）

**验证关联：**
- 刷新页面，确认AppID出现在列表中
- 状态应该是"已关联"

---

### 步骤3：配置支付回调地址

1. 进入 **产品中心** → **开发配置**
2. 找到 **支付结果通知URL** 配置项
3. 设置回调地址：
   ```
   https://qwquant.com/api/v1/payment/notify
   ```
4. 点击保存

**⚠️ 重要提示：**
- 回调地址必须是HTTPS
- 必须是公网可访问
- 不要包含端口号
- 路径必须准确

---

### 步骤4：配置授权域名

1. 进入 **产品中心** → **JSAPI支付** → **支付授权目录**
2. 添加授权目录：
   ```
   https://qwquant.com/
   ```

**如果使用H5支付，还需配置H5支付域名：**
1. 进入 **产品中心** → **H5支付** → **H5支付域名**
2. 添加域名：
   ```
   qwquant.com
   ```

---

### 步骤5：测试支付功能

**创建测试订单：**
```bash
# 1. 获取登录token
curl -X POST https://qwquant.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "password": "your_password"
  }'

# 2. 创建支付订单
curl -X POST https://qwquant.com/api/v1/payment/orders \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "package_type": "basic",
    "payment_method": "wechat_native"
  }'

# 3. 使用微信扫码支付测试
```

**查看支付日志：**
```bash
docker-compose -f docker-compose.prod.yml logs -f backend | grep payment
```

---

## 📊 监控和维护

### 查看服务状态

```bash
# 查看所有容器
docker-compose -f docker-compose.prod.yml ps

# 查看实时日志
docker-compose -f docker-compose.prod.yml logs -f

# 查看特定服务日志
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f nginx
```

---

### 重启服务

```bash
# 重启所有服务
docker-compose -f docker-compose.prod.yml restart

# 重启特定服务
docker-compose -f docker-compose.prod.yml restart backend
docker-compose -f docker-compose.prod.yml restart nginx
```

---

### 更新代码

```bash
# 停止服务
docker-compose -f docker-compose.prod.yml down

# 拉取最新代码
git pull origin main

# 重新构建并启动
docker-compose -f docker-compose.prod.yml up -d --build
```

---

### SSL证书续期

证书自动续期已配置（每天凌晨2点检查），也可以手动续期：

```bash
# 手动续期
sudo certbot renew

# 续期后重启Nginx
docker-compose -f docker-compose.prod.yml restart nginx

# 测试续期（不实际执行）
sudo certbot renew --dry-run
```

---

### 数据库备份

```bash
# 手动备份
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

docker-compose -f docker-compose.prod.yml exec mysql \
  mysqldump -u root -p stock_analysis_prod > $BACKUP_DIR/database.sql

# 设置自动备份（每天凌晨3点）
(crontab -l 2>/dev/null; echo "0 3 * * * cd /opt/stock-analysis-system && ./backup.sh") | crontab -
```

---

### 查看系统资源使用

```bash
# 查看容器资源使用
docker stats

# 查看磁盘使用
df -h

# 查看内存使用
free -h

# 查看Docker占用空间
docker system df
```

---

## 🔒 安全检查清单

### 部署前检查

- [ ] 所有密码使用强密码（字母+数字+符号，16位以上）
- [ ] SECRET_KEY 和 ADMIN_SECRET_KEY 已更新为随机值
- [ ] 数据库密码已修改
- [ ] Redis密码已设置
- [ ] 微信支付证书权限设置为600
- [ ] .env文件不在Git仓库中

### 部署后检查

- [ ] HTTPS正常工作（绿色锁图标）
- [ ] HTTP自动重定向到HTTPS
- [ ] 防火墙只开放必要端口（80, 443）
- [ ] SSH密钥登录已配置，禁用密码登录
- [ ] 数据库只允许本地连接
- [ ] 定期备份已配置

---

## ❓ 常见问题

### Q1: SSL证书获取失败？

**可能原因：**
1. 域名未正确解析
2. 80端口被占用
3. 防火墙阻止访问

**解决方案：**
```bash
# 检查域名解析
dig +short qwquant.com

# 检查80端口
sudo lsof -i:80

# 检查防火墙
sudo ufw status
sudo firewall-cmd --list-all
```

---

### Q2: 微信支付回调收不到？

**排查步骤：**
```bash
# 1. 检查Nginx日志
docker-compose -f docker-compose.prod.yml logs nginx | grep payment

# 2. 检查后端日志
docker-compose -f docker-compose.prod.yml logs backend | grep payment

# 3. 测试回调地址可访问性
curl -X POST https://qwquant.com/api/v1/payment/notify

# 4. 检查防火墙
sudo iptables -L -n | grep 443
```

---

### Q3: 数据库连接失败？

**检查步骤：**
```bash
# 1. 检查MySQL容器状态
docker-compose -f docker-compose.prod.yml ps mysql

# 2. 查看MySQL日志
docker-compose -f docker-compose.prod.yml logs mysql

# 3. 测试连接
docker-compose -f docker-compose.prod.yml exec mysql \
  mysql -u root -p -e "SHOW DATABASES;"

# 4. 检查后端配置
docker-compose -f docker-compose.prod.yml exec backend env | grep DATABASE
```

---

### Q4: 服务无法启动？

**诊断步骤：**
```bash
# 1. 查看所有服务状态
docker-compose -f docker-compose.prod.yml ps

# 2. 查看失败服务的日志
docker-compose -f docker-compose.prod.yml logs [service_name]

# 3. 检查端口占用
sudo lsof -i:80
sudo lsof -i:443
sudo lsof -i:8000

# 4. 检查磁盘空间
df -h

# 5. 检查Docker状态
sudo systemctl status docker
```

---

## 📞 支持和帮助

### 技术支持

- 微信支付问题：https://kf.qq.com/product/wechatpaymentmerchant.html
- 微信商户平台：https://pay.weixin.qq.com/
- Let's Encrypt文档：https://letsencrypt.org/docs/

### 日志位置

```
后端日志: docker-compose -f docker-compose.prod.yml logs backend
Nginx日志: docker-compose -f docker-compose.prod.yml logs nginx
数据库日志: docker-compose -f docker-compose.prod.yml logs mysql
系统日志: /var/log/syslog (Ubuntu) 或 /var/log/messages (CentOS)
```

---

## 🎯 部署成功验证清单

部署完成后，请按以下清单验证：

### 基础功能
- [ ] https://qwquant.com 可以访问
- [ ] HTTP自动跳转到HTTPS
- [ ] SSL证书有效（绿色锁图标）
- [ ] API接口正常：https://qwquant.com/api/v1/health
- [ ] 后台管理可以登录
- [ ] 用户端可以访问

### 微信支付
- [ ] AppID已在商户平台关联
- [ ] 支付回调地址已配置
- [ ] 授权域名已配置
- [ ] 可以创建支付订单
- [ ] 扫码支付正常工作
- [ ] 支付回调正常接收
- [ ] 支付成功后权限正常激活

### 安全和监控
- [ ] 密码已全部修改为强密码
- [ ] SSL证书自动续期已配置
- [ ] 数据库自动备份已配置
- [ ] 日志记录正常
- [ ] 监控告警正常工作

---

**部署完成时间：** _______________
**部署负责人：** _______________
**验证人员：** _______________

---

**最后更新：** 2025-10-20
