# 🚀 生产环境部署检查清单

**域名：** https://qwquant.com
**AppID：** wx629c41da78273de4
**商户号：** 1725935616

---

## 📋 部署前准备

### 1. 服务器准备
- [ ] 服务器已购买（2GB+ RAM, 20GB+ 磁盘）
- [ ] 服务器有公网IP
- [ ] SSH访问已配置
- [ ] 安装Docker和Docker Compose
- [ ] 防火墙开放端口：80, 443

### 2. 域名配置
- [ ] 域名 qwquant.com 已购买
- [ ] DNS A记录已设置（@ → 服务器IP）
- [ ] DNS A记录已设置（www → 服务器IP）
- [ ] DNS解析已生效（执行：`dig +short qwquant.com`）

### 3. 文件准备
- [ ] 微信支付证书已上传（backend/certs/apiclient_cert.pem）
- [ ] 微信支付私钥已上传（backend/certs/apiclient_key.pem）
- [ ] 证书权限设置为600（`chmod 600 backend/certs/*.pem`）
- [ ] .env.prod 已配置
- [ ] backend/.env.production 已配置

---

## 🔧 配置文件检查

### backend/.env
```bash
✅ WECHAT_APPID=wx629c41da78273de4
✅ WECHAT_MCH_ID=1725935616
✅ WECHAT_API_V3_KEY=ChenZhenyuqianqian18861888886137 (32字符)
✅ WECHAT_CERT_SERIAL=69FD5A81E65BFEE1D974F023B21C565C068D7EEE
✅ WECHAT_CERT_PATH=certs/apiclient_cert.pem
✅ WECHAT_KEY_PATH=certs/apiclient_key.pem
✅ WECHAT_NOTIFY_URL=https://qwquant.com/api/v1/payment/notify
✅ BASE_URL=https://qwquant.com
✅ PAYMENT_MOCK_MODE=false
```

### nginx/nginx.prod.conf
```bash
✅ server_name qwquant.com www.qwquant.com
✅ ssl_certificate /etc/letsencrypt/live/qwquant.com/fullchain.pem
✅ ssl_certificate_key /etc/letsencrypt/live/qwquant.com/privkey.pem
```

### .env.prod
```bash
✅ DOMAIN=qwquant.com
⚠️ EMAIL=your-email@example.com (需要修改)
⚠️ MYSQL_ROOT_PASSWORD (需要设置强密码)
⚠️ MYSQL_PASSWORD (需要设置强密码)
⚠️ REDIS_PASSWORD (需要设置强密码)
```

---

## 🚀 部署步骤

### 方式1：自动部署（推荐）

```bash
# 1. 上传项目到服务器
scp -r /Users/peakom/work/stock-analysis-system user@server-ip:/opt/

# 2. SSH登录服务器
ssh user@server-ip

# 3. 执行部署脚本
cd /opt/stock-analysis-system
./deploy-production.sh
```

### 方式2：手动部署

```bash
# 1. 获取SSL证书
sudo certbot certonly --standalone \
  -d qwquant.com \
  -d www.qwquant.com \
  --email your-email@example.com \
  --agree-tos

# 2. 启动服务
docker-compose -f docker-compose.prod.yml up -d --build

# 3. 查看日志
docker-compose -f docker-compose.prod.yml logs -f
```

---

## ✅ 部署后验证

### 1. 基础服务检查
```bash
# 检查容器状态
docker-compose -f docker-compose.prod.yml ps
# 预期：所有容器都是 Up 状态

# 检查后端健康
curl http://localhost:8000/health
# 预期：返回 200 OK

# 检查Nginx
curl http://localhost/nginx-health
# 预期：返回 "healthy"
```

### 2. HTTPS访问检查
```bash
# 测试HTTP重定向
curl -I http://qwquant.com
# 预期：返回 301，重定向到 https://

# 测试HTTPS
curl -I https://qwquant.com
# 预期：返回 200 OK

# 测试API
curl https://qwquant.com/api/v1/health
# 预期：返回健康状态
```

### 3. 微信支付配置检查
```bash
# 运行配置检查工具
docker-compose -f docker-compose.prod.yml exec backend \
  python check_payment_config.py

# 预期：显示所有配置项为 ✅
```

---

## 🔐 微信商户平台配置

### 1. 关联AppID
- [ ] 登录微信商户平台：https://pay.weixin.qq.com/
- [ ] 进入：产品中心 → AppID账号管理
- [ ] 检查 wx629c41da78273de4 是否存在
- [ ] 如果没有，点击"新增关联AppID"添加
- [ ] 确认状态为"已关联"

### 2. 配置支付回调
- [ ] 进入：产品中心 → 开发配置
- [ ] 找到：支付结果通知URL
- [ ] 设置为：`https://qwquant.com/api/v1/payment/notify`
- [ ] 保存配置

### 3. 配置授权域名
- [ ] 进入：产品中心 → JSAPI支付 → 支付授权目录
- [ ] 添加：`https://qwquant.com/`
- [ ] 保存配置

---

## 🧪 功能测试

### 1. 创建测试订单
```bash
# 获取登录token
TOKEN=$(curl -X POST https://qwquant.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test123"}' \
  | jq -r '.access_token')

# 创建支付订单
curl -X POST https://qwquant.com/api/v1/payment/orders \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "package_type": "basic",
    "payment_method": "wechat_native"
  }'
```

### 2. 扫码支付测试
- [ ] 返回的二维码URL有效
- [ ] 使用微信扫码
- [ ] 支付页面正常显示
- [ ] 可以完成支付（使用微信支付测试账号）

### 3. 回调验证
```bash
# 查看支付回调日志
docker-compose -f docker-compose.prod.yml logs backend | grep "payment.*notify"

# 预期：看到接收到回调的日志
```

### 4. 权限激活验证
```bash
# 查询用户会员状态
curl https://qwquant.com/api/v1/user/membership \
  -H "Authorization: Bearer $TOKEN"

# 预期：显示会员已激活
```

---

## 📊 监控和维护

### 日常检查命令
```bash
# 查看服务状态
docker-compose -f docker-compose.prod.yml ps

# 查看实时日志
docker-compose -f docker-compose.prod.yml logs -f

# 查看资源使用
docker stats

# 查看磁盘空间
df -h

# 查看SSL证书有效期
sudo certbot certificates
```

### 常用操作
```bash
# 重启服务
docker-compose -f docker-compose.prod.yml restart

# 更新代码
git pull && docker-compose -f docker-compose.prod.yml up -d --build

# 查看数据库
docker-compose -f docker-compose.prod.yml exec mysql \
  mysql -u root -p stock_analysis_prod

# 备份数据库
docker-compose -f docker-compose.prod.yml exec mysql \
  mysqldump -u root -p stock_analysis_prod > backup_$(date +%Y%m%d).sql
```

---

## ⚠️ 注意事项

### 安全
- [ ] 所有密码已修改为强密码（16位以上，字母+数字+符号）
- [ ] SSH密钥登录已配置
- [ ] 密码登录已禁用
- [ ] 防火墙只开放必要端口
- [ ] 定期备份已配置

### 性能
- [ ] 服务器资源充足（CPU < 80%, 内存 < 80%）
- [ ] 数据库连接池配置合理
- [ ] Nginx缓存已启用
- [ ] CDN已配置（如果需要）

### 监控
- [ ] SSL证书自动续期已配置
- [ ] 数据库自动备份已配置
- [ ] 日志轮转已配置
- [ ] 监控告警已配置（如果有）

---

## 🆘 故障排查

### 服务无法启动
```bash
# 1. 查看容器日志
docker-compose -f docker-compose.prod.yml logs [service_name]

# 2. 检查端口占用
sudo lsof -i:80
sudo lsof -i:443

# 3. 检查配置文件语法
nginx -t

# 4. 检查磁盘空间
df -h
```

### HTTPS无法访问
```bash
# 1. 检查证书
sudo certbot certificates

# 2. 检查Nginx配置
docker-compose -f docker-compose.prod.yml exec nginx nginx -t

# 3. 检查防火墙
sudo ufw status
sudo firewall-cmd --list-all

# 4. 测试本地访问
curl -k https://localhost
```

### 支付回调失败
```bash
# 1. 检查回调地址可访问性
curl -X POST https://qwquant.com/api/v1/payment/notify

# 2. 查看后端日志
docker-compose -f docker-compose.prod.yml logs backend | grep payment

# 3. 查看Nginx日志
docker-compose -f docker-compose.prod.yml logs nginx | grep payment

# 4. 验证微信商户平台配置
# 登录商户平台检查回调地址是否正确
```

---

## 📞 联系方式

- 微信支付技术支持：https://kf.qq.com/product/wechatpaymentmerchant.html
- Let's Encrypt文档：https://letsencrypt.org/docs/
- Docker文档：https://docs.docker.com/

---

## ✅ 最终检查清单

### 部署完成确认
- [ ] 域名https://qwquant.com可以访问
- [ ] HTTPS证书有效（绿色锁图标）
- [ ] 所有Docker容器运行正常
- [ ] API接口正常响应
- [ ] 微信支付配置检查通过
- [ ] AppID已在商户平台关联
- [ ] 回调地址已配置
- [ ] 测试订单创建成功
- [ ] 扫码支付正常工作
- [ ] 支付回调正常接收
- [ ] 用户权限正常激活
- [ ] SSL证书自动续期已配置
- [ ] 数据库备份已配置

### 安全检查
- [ ] 所有默认密码已修改
- [ ] SECRET_KEY已更新
- [ ] 证书文件权限正确（600）
- [ ] .env文件不在Git中
- [ ] 防火墙配置正确
- [ ] SSH密钥登录已配置

---

**部署日期：** _______________
**负责人：** _______________
**验证人：** _______________

**备注：**
________________________________
________________________________
________________________________

