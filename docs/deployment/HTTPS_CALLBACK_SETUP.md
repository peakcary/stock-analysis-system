# 微信支付HTTPS回调地址配置指南

## 目录
1. [回调地址要求](#回调地址要求)
2. [开发环境配置（本地测试）](#开发环境配置本地测试)
3. [生产环境配置](#生产环境配置)
4. [配置验证](#配置验证)
5. [常见问题](#常见问题)

---

## 回调地址要求

### 微信支付对回调地址的要求：
- ✅ **必须使用HTTPS协议**（不能是HTTP）
- ✅ **必须是公网可访问的地址**（不能是localhost、127.0.0.1、内网IP）
- ✅ **必须能正常响应微信服务器的POST请求**
- ✅ **响应时间不能超过5秒**
- ✅ **域名需要备案**（在中国大陆部署）

### 回调地址格式：
```
https://yourdomain.com/api/v1/payment/notify
```

---

## 开发环境配置（本地测试）

### 方案1：使用内网穿透工具（推荐用于测试）

#### 1.1 使用 ngrok（最简单）

**安装 ngrok：**
```bash
# macOS
brew install ngrok

# 或下载: https://ngrok.com/download
```

**启动后端服务：**
```bash
cd /Users/peakom/work/stock-analysis-system
./start.sh
# 或
npm run dev
```

**启动 ngrok 隧道：**
```bash
# 映射本地3007端口（假设后端运行在3007）
ngrok http 3007
```

**ngrok 输出示例：**
```
Session Status    online
Account           Your Name (Plan: Free)
Version           3.0.0
Region            United States (us)
Forwarding        https://abc123def456.ngrok.io -> http://localhost:3007
```

**配置环境变量：**
```bash
# 编辑 backend/.env
WECHAT_NOTIFY_URL=https://abc123def456.ngrok.io/api/v1/payment/notify
BASE_URL=https://abc123def456.ngrok.io
PAYMENT_MOCK_MODE=false  # 如果要测试真实支付
```

**优点：**
- ✅ 无需服务器
- ✅ 支持HTTPS
- ✅ 配置简单
- ✅ 实时查看请求日志

**缺点：**
- ❌ 每次重启URL会变化（免费版）
- ❌ 不稳定（免费版有限制）
- ❌ 仅用于测试

---

#### 1.2 使用 localtunnel

**安装：**
```bash
npm install -g localtunnel
```

**启动隧道：**
```bash
lt --port 3007 --subdomain my-stock-app
```

**配置：**
```bash
WECHAT_NOTIFY_URL=https://my-stock-app.loca.lt/api/v1/payment/notify
BASE_URL=https://my-stock-app.loca.lt
```

---

#### 1.3 使用 Cloudflare Tunnel（稳定性更好）

**安装 cloudflared：**
```bash
# macOS
brew install cloudflare/cloudflare/cloudflared

# 或下载: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/
```

**配置隧道：**
```bash
# 登录
cloudflared tunnel login

# 创建隧道
cloudflared tunnel create stock-payment

# 配置路由
cloudflared tunnel route dns stock-payment payment.yourdomain.com
```

**启动隧道：**
```bash
cloudflared tunnel --url http://localhost:3007
```

---

### 方案2：启用模拟支付模式（开发推荐）

**配置：**
```bash
# backend/.env
PAYMENT_MOCK_MODE=true
WECHAT_NOTIFY_URL=http://localhost:3007/api/v1/payment/notify
```

**特点：**
- ✅ 无需真实回调地址
- ✅ 使用模拟支付API测试完整流程
- ✅ 适合功能开发和测试
- ❌ 不能测试真实微信支付

---

## 生产环境配置

### 步骤1：准备域名和服务器

#### 1.1 购买域名
- 阿里云：https://wanwang.aliyun.com/
- 腾讯云：https://dnspod.cloud.tencent.com/
- Cloudflare（国外）：https://www.cloudflare.com/

#### 1.2 域名解析
```bash
# 添加 A 记录
# 主机记录: @
# 记录类型: A
# 记录值: 你的服务器公网IP

# 添加 CNAME 记录（可选）
# 主机记录: www
# 记录类型: CNAME
# 记录值: yourdomain.com
```

#### 1.3 服务器要求
- 公网IP地址
- 开放80端口（HTTP，用于SSL验证）
- 开放443端口（HTTPS）
- 操作系统：Ubuntu 20.04+ / CentOS 7+

---

### 步骤2：配置SSL证书（HTTPS）

#### 2.1 使用 Let's Encrypt（免费，推荐）

**安装 Certbot：**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install certbot python3-certbot-nginx

# CentOS/RHEL
sudo yum install certbot python3-certbot-nginx
```

**获取SSL证书：**
```bash
# 方法1: 使用 Certbot 自动配置 Nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# 方法2: 仅获取证书（手动配置）
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# 方法3: 使用 Docker Compose（项目已配置）
cd /Users/peakom/work/stock-analysis-system
docker-compose -f docker-compose.prod.yml --profile certbot up certbot
```

**证书位置：**
```
/etc/letsencrypt/live/yourdomain.com/fullchain.pem  # 证书
/etc/letsencrypt/live/yourdomain.com/privkey.pem    # 私钥
```

**自动续期：**
```bash
# 测试续期
sudo certbot renew --dry-run

# 添加定时任务
sudo crontab -e
# 添加以下行（每天凌晨2点检查续期）
0 2 * * * /usr/bin/certbot renew --quiet
```

---

#### 2.2 使用阿里云/腾讯云SSL证书（付费或免费）

**阿里云免费SSL证书：**
1. 登录阿里云控制台
2. 产品与服务 → SSL证书
3. 购买证书（选择免费DV证书）
4. 下载证书（Nginx格式）
5. 上传到服务器 `/etc/nginx/ssl/`

**腾讯云免费SSL证书：**
1. 登录腾讯云控制台
2. SSL证书管理
3. 申请免费证书
4. 下载并上传到服务器

---

### 步骤3：配置Nginx

**编辑配置文件：**
```bash
cd /Users/peakom/work/stock-analysis-system/nginx
vi nginx.prod.conf
```

**修改域名配置：**
```nginx
# 第82行 - 修改域名
server_name yourdomain.com www.yourdomain.com;

# 第101-102行 - SSL证书路径
ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

# 第122-139行 - API代理配置（已包含微信支付回调）
location /api/ {
    proxy_pass http://backend;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;  # 重要：告诉后端是HTTPS
}
```

**特别注意微信支付回调路径：**
```nginx
# /api/v1/payment/notify 会被代理到后端
# https://yourdomain.com/api/v1/payment/notify → http://backend:8000/api/v1/payment/notify
```

---

### 步骤4：配置后端环境变量

**编辑生产环境配置：**
```bash
cd /Users/peakom/work/stock-analysis-system

# 创建生产环境变量文件
cp backend/.env backend/.env.production

# 编辑配置
vi backend/.env.production
```

**必需配置：**
```bash
# ===== 域名和回调配置 =====
BASE_URL=https://yourdomain.com
WECHAT_NOTIFY_URL=https://yourdomain.com/api/v1/payment/notify

# ===== 微信支付配置 =====
WECHAT_APPID=wx你的真实AppID
WECHAT_MCH_ID=1725935616
WECHAT_API_KEY=ChenZhenyuqianqian18861888886137
WECHAT_API_V3_KEY=ChenZhenyuqianqian18861888886137
WECHAT_CERT_SERIAL=69FD5A81E65BFEE1D974F023B21C565C068D7EEE
WECHAT_CERT_PATH=certs/apiclient_cert.pem
WECHAT_KEY_PATH=certs/apiclient_key.pem

# ===== 支付模式 =====
PAYMENT_ENABLED=true
PAYMENT_MOCK_MODE=false  # 生产环境设为false
PAYMENT_ORDER_TIMEOUT_HOURS=2

# ===== 安全配置 =====
SECRET_KEY=生成一个随机的32字符以上密钥
ADMIN_SECRET_KEY=生成另一个随机的32字符以上密钥

# ===== 数据库配置 =====
DATABASE_URL=mysql+pymysql://user:password@host:3306/dbname
```

**生成安全密钥：**
```bash
# 生成SECRET_KEY
openssl rand -hex 32

# 生成ADMIN_SECRET_KEY
openssl rand -hex 32
```

---

### 步骤5：部署到生产环境

#### 5.1 使用 Docker Compose（推荐）

**创建环境变量文件：**
```bash
cd /Users/peakom/work/stock-analysis-system

# 创建 .env 文件
cat > .env.prod << 'EOF'
# 域名配置
DOMAIN=yourdomain.com
EMAIL=your-email@example.com

# 数据库配置
MYSQL_ROOT_PASSWORD=强密码1
MYSQL_DATABASE=stock_analysis_prod
MYSQL_USER=stock_user
MYSQL_PASSWORD=强密码2

# Redis配置
REDIS_PASSWORD=强密码3

# JWT密钥
SECRET_KEY=你生成的随机密钥1
ADMIN_SECRET_KEY=你生成的随机密钥2

# Token过期时间
ACCESS_TOKEN_EXPIRE_MINUTES=30
EOF
```

**启动服务：**
```bash
# 1. 先获取SSL证书（首次部署）
docker-compose -f docker-compose.prod.yml --profile certbot up certbot

# 2. 启动所有服务
docker-compose -f docker-compose.prod.yml up -d

# 3. 查看日志
docker-compose -f docker-compose.prod.yml logs -f backend

# 4. 检查服务状态
docker-compose -f docker-compose.prod.yml ps
```

---

#### 5.2 手动部署（不使用Docker）

**安装依赖：**
```bash
# 后端
cd /Users/peakom/work/stock-analysis-system/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 前端
cd ../client
npm install
npm run build
```

**配置 Nginx：**
```bash
sudo cp /path/to/nginx.prod.conf /etc/nginx/nginx.conf
sudo nginx -t  # 测试配置
sudo systemctl restart nginx
```

**启动后端：**
```bash
cd /Users/peakom/work/stock-analysis-system/backend
source venv/bin/activate

# 使用生产环境配置
export $(cat .env.production | xargs)

# 启动服务（使用 gunicorn 或 uvicorn）
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000
```

---

### 步骤6：在微信商户平台配置回调地址

#### 6.1 登录微信商户平台
https://pay.weixin.qq.com/

#### 6.2 配置回调地址
1. 进入 **产品中心** → **开发配置**
2. 找到 **支付结果通知URL**
3. 设置回调地址：
   ```
   https://yourdomain.com/api/v1/payment/notify
   ```

#### 6.3 配置授权域名
1. 进入 **产品中心** → **JSAPI支付** → **支付授权目录**
2. 添加授权目录：
   ```
   https://yourdomain.com/
   ```

---

## 配置验证

### 1. 验证HTTPS证书

```bash
# 方法1: 浏览器访问
https://yourdomain.com

# 方法2: 命令行测试
curl -I https://yourdomain.com

# 方法3: SSL检测
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com
```

**预期结果：**
- ✅ 浏览器显示"连接是安全的"（绿色锁图标）
- ✅ curl返回200状态码
- ✅ SSL协议为TLSv1.2或TLSv1.3

---

### 2. 验证后端API可访问

```bash
# 测试健康检查
curl https://yourdomain.com/api/v1/health

# 测试支付API
curl https://yourdomain.com/api/v1/payment/config \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 3. 验证微信支付配置

```bash
# 在服务器上运行配置检查工具
cd /Users/peakom/work/stock-analysis-system/backend

# 加载生产环境变量
export $(cat .env.production | xargs)

# 运行检查
python check_payment_config.py
```

**预期输出：**
```
🚀 微信支付配置检查工具
==================================================
✅ 所有配置检查通过！微信支付系统可以正常使用。
🎯 当前运行在生产模式，可以处理真实支付。
```

---

### 4. 测试支付回调

**创建测试订单：**
```bash
curl -X POST https://yourdomain.com/api/v1/payment/orders \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "package_type": "basic",
    "payment_method": "wechat_native"
  }'
```

**使用微信扫码支付（或沙箱环境测试）**

**查看回调日志：**
```bash
# Docker方式
docker-compose -f docker-compose.prod.yml logs -f backend | grep "payment"

# 手动部署方式
tail -f /path/to/backend/logs/app.log | grep "payment"
```

---

## 常见问题

### Q1: 回调地址配置后没有收到回调？

**排查步骤：**
1. 检查防火墙是否开放443端口
   ```bash
   sudo firewall-cmd --list-all
   sudo ufw status
   ```

2. 检查Nginx是否正在运行
   ```bash
   sudo systemctl status nginx
   ```

3. 检查后端服务是否正常
   ```bash
   curl http://localhost:8000/api/v1/health
   ```

4. 查看Nginx访问日志
   ```bash
   sudo tail -f /var/log/nginx/access.log
   ```

5. 验证微信服务器能访问你的服务器
   ```bash
   # 使用第三方工具测试
   https://tools.pingdom.com/
   ```

---

### Q2: SSL证书过期怎么办？

**Let's Encrypt证书90天有效期，需要自动续期：**
```bash
# 手动续期
sudo certbot renew

# 设置自动续期
sudo crontab -e
0 2 * * * /usr/bin/certbot renew --quiet && systemctl reload nginx
```

---

### Q3: 本地开发时ngrok URL经常变化怎么办？

**解决方案：**
1. 升级ngrok付费版（固定域名）
2. 使用Cloudflare Tunnel（稳定性更好）
3. 使用模拟支付模式 `PAYMENT_MOCK_MODE=true`

---

### Q4: 回调签名验证失败？

**检查项：**
1. 确认 `WECHAT_API_V3_KEY` 配置正确（32字符）
2. 确认证书序列号匹配
   ```bash
   openssl x509 -in certs/apiclient_cert.pem -noout -serial
   ```
3. 检查系统时间是否正确
   ```bash
   date
   ntpdate -q pool.ntp.org  # 检查时间同步
   ```

---

### Q5: Docker部署时如何挂载SSL证书？

**已在 docker-compose.prod.yml 配置：**
```yaml
nginx:
  volumes:
    - /etc/letsencrypt:/etc/letsencrypt:ro  # SSL证书（只读）
```

**确保证书路径正确：**
```bash
ls -l /etc/letsencrypt/live/yourdomain.com/
```

---

## 快速配置清单

### 开发环境（本地测试）
- [ ] 安装ngrok: `brew install ngrok`
- [ ] 启动后端: `./start.sh`
- [ ] 启动ngrok: `ngrok http 3007`
- [ ] 配置环境变量: `WECHAT_NOTIFY_URL=https://xxx.ngrok.io/api/v1/payment/notify`
- [ ] 测试回调

### 生产环境
- [ ] 购买域名并解析到服务器IP
- [ ] 安装SSL证书（Let's Encrypt）
- [ ] 修改nginx配置中的域名
- [ ] 配置backend/.env.production
- [ ] 部署服务（Docker或手动）
- [ ] 在微信商户平台配置回调地址
- [ ] 运行配置检查工具验证
- [ ] 创建测试订单验证回调

---

## 相关文档

- [微信支付配置指南](./WECHAT_PAYMENT_SETUP.md)
- [部署文档](../../DEPLOYMENT_V2.7.md)
- [微信支付官方文档](https://pay.weixin.qq.com/wiki/doc/apiv3/index.shtml)

---

**创建时间：** 2025-10-20
**最后更新：** 2025-10-20
