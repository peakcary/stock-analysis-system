# 微信支付功能部署指南

本文档详细说明了如何部署和配置股票分析系统的微信支付功能。

## 🏗️ 架构概览

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   前端客户端     │    │    后端API      │    │   微信支付API    │
│                │    │                │    │                │
│ - PaymentModal  │◄──►│ - WechatPayAPI  │◄──►│ - 统一下单      │
│ - PaymentPkg    │    │ - MemberService │    │ - 支付回调      │
│ - MemberPage    │    │ - PaymentModels │    │ - 订单查询      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    MySQL 数据库                              │
│ - payment_packages    - payment_orders                      │
│ - payment_notifications    - membership_logs               │
└─────────────────────────────────────────────────────────────┘
```

## 📦 已实现功能

### 后端功能
- ✅ 微信支付统一下单
- ✅ 支付结果通知处理
- ✅ 支付订单管理
- ✅ 会员权益自动发放
- ✅ 支付套餐配置管理
- ✅ 支付状态查询和轮询
- ✅ 订单过期处理

### 前端功能
- ✅ 支付套餐选择界面
- ✅ 微信扫码支付流程
- ✅ 支付状态实时监控
- ✅ 用户会员信息展示
- ✅ 支付历史记录
- ✅ 响应式设计支持

### 数据库支持
- ✅ 支付套餐配置表
- ✅ 支付订单记录表
- ✅ 支付通知日志表
- ✅ 会员变更记录表
- ✅ 退款记录表

## 🚀 部署步骤

### 1. 数据库初始化

```bash
# 执行支付相关的数据库表创建
mysql -u root -p stock_analysis_dev < database/payment_tables.sql
```

### 2. 环境变量配置

复制环境变量示例文件：
```bash
cp backend/.env.example backend/.env
```

编辑 `.env` 文件，填入微信支付配置：
```bash
# 微信支付配置
WECHAT_APPID=your_wechat_appid
WECHAT_MCH_ID=your_merchant_id
WECHAT_API_KEY=your_32_char_api_key
WECHAT_CERT_PATH=certs/apiclient_cert.pem
WECHAT_KEY_PATH=certs/apiclient_key.pem

# 应用基础URL（生产环境必须是HTTPS）
BASE_URL=https://your-domain.com

# 支付配置
PAYMENT_ORDER_TIMEOUT_HOURS=2
PAYMENT_ENABLED=true
```

### 3. 微信支付商户配置

#### 3.1 申请微信商户号
1. 访问 [微信支付商户平台](https://pay.weixin.qq.com)
2. 提交企业资质进行申请
3. 获得商户号 (mch_id)

#### 3.2 配置API密钥
1. 登录商户平台
2. 进入"账户中心" -> "API安全"
3. 设置32位API密钥

#### 3.3 配置回调域名
1. 在商户平台设置支付回调URL
2. 回调地址：`https://your-domain.com/api/v1/payment/notify`
3. 确保域名已完成ICP备案

#### 3.4 下载商户证书（可选）
```bash
# 创建证书目录
mkdir -p backend/certs

# 将从商户平台下载的证书放入此目录
# apiclient_cert.pem - 商户证书
# apiclient_key.pem - 商户私钥
```

### 4. 后端服务部署

#### 4.1 安装依赖
```bash
cd backend
pip install -r requirements.txt
```

#### 4.2 启动服务
```bash
# 开发环境
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 生产环境
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 5. 前端部署

#### 5.1 安装依赖
```bash
cd client
npm install
```

#### 5.2 构建生产版本
```bash
npm run build
```

#### 5.3 部署到Nginx
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/your/cert.pem;
    ssl_certificate_key /path/to/your/private.key;
    
    root /path/to/your/dist;
    index index.html;
    
    # 前端路由
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # API代理
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # 支付回调（重要：微信支付回调）
    location /api/v1/payment/notify {
        proxy_pass http://localhost:8000;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## 🔧 配置说明

### 支付套餐配置

系统预置了8种支付套餐：

| 套餐类型 | 名称 | 价格 | 查询次数 | 有效期 | 会员类型 |
|---------|------|------|----------|--------|----------|
| queries_10 | 10次查询包 | ¥9.90 | 10 | 30天 | 免费版 |
| queries_50 | 50次查询包 | ¥39.90 | 50 | 60天 | 免费版 |
| monthly_pro | 专业版月卡 | ¥29.90 | 1000 | 30天 | 专业版 |
| quarterly_pro | 专业版季卡 | ¥79.90 | 3000 | 90天 | 专业版 |
| yearly_pro | 专业版年卡 | ¥299.90 | 12000 | 365天 | 专业版 |
| monthly_premium | 旗舰版月卡 | ¥59.90 | 2000 | 30天 | 旗舰版 |
| quarterly_premium | 旗舰版季卡 | ¥149.90 | 6000 | 90天 | 旗舰版 |
| yearly_premium | 旗舰版年卡 | ¥499.90 | 24000 | 365天 | 旗舰版 |

### API端点

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | /api/v1/payment/packages | 获取支付套餐列表 |
| POST | /api/v1/payment/orders | 创建支付订单 |
| GET | /api/v1/payment/orders/{id}/status | 查询支付状态 |
| POST | /api/v1/payment/notify | 微信支付回调 |
| GET | /api/v1/payment/stats | 获取支付统计 |

## 🧪 测试指南

### 1. 沙箱环境测试

微信支付提供沙箱环境用于开发测试：
```bash
# 修改微信支付服务类中的URL
# 将正式环境URL替换为沙箱环境URL
```

### 2. 本地测试

使用ngrok提供HTTPS回调地址：
```bash
# 安装ngrok
npm install -g ngrok

# 启动隧道
ngrok http 8000

# 使用提供的HTTPS URL作为BASE_URL
```

### 3. 支付流程测试

1. 访问会员页面
2. 选择支付套餐
3. 生成支付订单
4. 扫码支付（或使用测试工具）
5. 验证支付结果和会员权益

## 🔍 监控和日志

### 1. 支付日志
系统会记录所有支付相关的操作：
- 支付订单创建
- 支付通知接收
- 支付状态变更
- 会员权益发放

### 2. 错误处理
常见错误及解决方案：

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| 签名验证失败 | API密钥不正确 | 检查配置中的WECHAT_API_KEY |
| 通知URL访问失败 | 域名未备案或HTTPS配置问题 | 确保域名可访问且使用HTTPS |
| 订单重复 | 商户订单号重复 | 检查订单号生成逻辑 |
| 支付金额不符 | 金额计算错误 | 检查价格计算逻辑 |

## 🔒 安全建议

### 1. 生产环境安全
- ✅ 使用HTTPS协议
- ✅ 设置防火墙规则
- ✅ 定期更新系统和依赖
- ✅ 使用强密码和密钥
- ✅ 定期备份数据

### 2. 支付安全
- ✅ 验证所有支付通知签名
- ✅ 避免重复处理相同订单
- ✅ 记录所有支付操作日志
- ✅ 定期对账和资金核实
- ✅ 设置支付金额限制

### 3. API安全
- ✅ 实现用户认证和授权
- ✅ 限制API访问频率
- ✅ 验证输入参数
- ✅ 使用CORS策略
- ✅ 隐藏敏感信息

## 📞 技术支持

### 开发者资源
- [微信支付官方文档](https://pay.weixin.qq.com/wiki/doc/api/index.html)
- [FastAPI官方文档](https://fastapi.tiangolo.com/)
- [React官方文档](https://reactjs.org/)
- [Ant Design官方文档](https://ant.design/)

### 常见问题
1. **Q: 支付成功但会员权益未生效？**
   A: 检查支付回调是否正常接收，查看membership_logs表记录。

2. **Q: 二维码无法显示？**
   A: 检查微信支付统一下单是否成功，确认trade_type参数。

3. **Q: 支付回调签名验证失败？**
   A: 确认API密钥配置正确，检查签名算法实现。

## 🎉 部署完成检查清单

- [ ] 数据库表创建完成
- [ ] 环境变量配置正确
- [ ] 微信商户号配置完成
- [ ] 后端服务正常启动
- [ ] 前端应用部署成功
- [ ] HTTPS证书配置正确
- [ ] 支付回调地址可访问
- [ ] 支付流程测试通过
- [ ] 会员权益发放正常
- [ ] 日志记录功能正常

部署完成后，您的股票分析系统就具备了完整的微信支付功能！