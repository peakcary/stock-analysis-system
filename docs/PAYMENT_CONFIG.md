# 💳 支付系统配置指南

## 🏗️ 系统架构

```
前端客户端 ◄──► 后端API ◄──► 微信支付API
    │              │              │
    ▼              ▼              ▼
       MySQL优化数据库 (支付订单/套餐/记录)
       v2.6.4: 查询性能提升50-200倍
```

## 📦 功能特性

### ✅ 已实现功能
- 🔄 微信支付统一下单
- 📱 扫码支付流程
- ⚡ 支付状态实时监控
- 💎 4个套餐配置（10次/100次/1000次/无限次）
- 🎖️ 自动会员权益发放
- 📊 支付历史记录
- 🔔 支付结果通知处理

### 🗄️ 数据库表
- `payment_packages` - 支付套餐配置
- `payment_orders` - 支付订单记录
- `payment_notifications` - 支付通知日志
- `membership_logs` - 会员变更记录
- `refund_records` - 退款记录

## 🚀 部署配置

### 1. 环境变量配置

在 `backend/.env` 中配置：

```env
# 微信支付配置
WECHAT_APPID=your_app_id
WECHAT_MCHID=your_merchant_id  
WECHAT_API_KEY=your_api_key
WECHAT_CERT_PATH=path/to/cert.pem
WECHAT_KEY_PATH=path/to/key.pem

# 支付回调地址
PAYMENT_NOTIFY_URL=https://your-domain.com/api/v1/payment/notify

# 开发模式（可选）
PAYMENT_MOCK_MODE=true  # 开发环境使用模拟支付
```

### 2. 微信支付商户配置

1. **申请微信支付商户号**
   - 访问 [微信支付商户平台](https://pay.weixin.qq.com)
   - 提交资质审核
   - 获取商户号(MCHID)

2. **下载API证书**
   - 登录商户平台
   - 账户中心 → API安全 → 下载证书
   - 将证书文件放到 `backend/certs/` 目录

3. **配置API密钥**
   - 商户平台设置32位API密钥
   - 用于签名验证

### 3. 数据库初始化

系统会自动创建支付相关表，并初始化默认套餐：

```sql
-- 默认套餐配置
INSERT INTO payment_packages (name, price, query_limit, duration_days) VALUES
('基础套餐', 9.90, 10, 30),
('标准套餐', 29.90, 100, 30), 
('专业套餐', 99.90, 1000, 90),
('企业套餐', 299.90, -1, 365);
```

## 🔧 开发测试

### 模拟支付模式

开发环境可启用模拟支付：

```env
PAYMENT_MOCK_MODE=true
```

模拟支付流程：
1. 创建订单正常
2. 跳过微信支付API调用
3. 3秒后自动标记支付成功
4. 正常发放会员权益

### 测试流程

```bash
# 1. 启动系统
./start.sh

# 2. 访问客户端
open http://localhost:8005

# 3. 注册/登录用户

# 4. 进入套餐购买页面测试支付流程
```

## 🌐 生产部署

### 1. 域名和SSL配置

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/ssl.crt;
    ssl_certificate_key /path/to/ssl.key;
    
    location /api/ {
        proxy_pass http://localhost:3007;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 2. 支付回调URL配置

确保微信支付回调地址可访问：
```
https://your-domain.com/api/v1/payment/notify
```

### 3. 安全配置

```env
# 生产环境必须关闭模拟模式
PAYMENT_MOCK_MODE=false

# 使用强密钥
SECRET_KEY=your-super-secret-key-here

# 限制CORS域名
CORS_ORIGINS=["https://your-domain.com"]
```

## 📊 监控和维护

### 支付状态监控

```bash
# 查看支付订单状态
./status.sh

# 查看支付相关日志
tail -f logs/backend.log | grep payment
```

### 常见问题排查

1. **支付回调失败**
   - 检查回调URL是否可访问
   - 验证API证书是否正确
   - 查看支付通知日志

2. **订单状态异常**
   - 检查数据库连接
   - 验证支付密钥配置
   - 查看错误日志

3. **会员权益未发放**
   - 检查支付成功回调
   - 验证用户ID匹配
   - 查看membership_logs表

## 🔍 API接口

### 主要支付接口

```bash
# 获取支付套餐
GET /api/v1/payment/packages

# 创建支付订单  
POST /api/v1/payment/create-order

# 查询订单状态
GET /api/v1/payment/order-status/{order_id}

# 微信支付回调
POST /api/v1/payment/notify
```

### 用户会员接口

```bash
# 获取用户信息
GET /api/v1/users/me

# 查询剩余次数
GET /api/v1/users/remaining-queries

# 支付历史
GET /api/v1/payment/history
```

## 🛡️ 安全注意事项

1. **API密钥安全**
   - 不要将密钥提交到代码仓库
   - 定期更换密钥
   - 使用环境变量管理

2. **证书管理**
   - 证书文件权限设置为600
   - 定期检查证书有效期
   - 备份证书文件

3. **回调验证**
   - 验证微信支付签名
   - 检查订单金额一致性
   - 防止重复支付处理

---

💡 **开发提示**: 开发环境使用模拟支付，生产环境配置真实微信支付参数。