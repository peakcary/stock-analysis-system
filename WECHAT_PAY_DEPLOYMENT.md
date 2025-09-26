# 🚀 微信支付部署指南

本文档详细说明如何配置和部署微信支付功能，确保系统能够正常处理支付业务。

## 📋 部署清单

### 必需项目
- [ ] 微信商户平台账号
- [ ] 微信公众号或小程序（获取AppID）
- [ ] API证书文件
- [ ] 服务器HTTPS域名
- [ ] 环境变量配置

## 🔧 详细配置步骤

### 步骤1: 获取微信支付资质

#### 1.1 申请微信商户号
1. 访问 [微信支付商户平台](https://pay.weixin.qq.com)
2. 提交企业资质进行审核
3. 获得商户号（如：1725935616）

#### 1.2 获取AppID
- **公众号**: 微信公众平台获取AppID
- **小程序**: 微信小程序平台获取AppID
- **APP**: 微信开放平台获取AppID

### 步骤2: 下载API证书

#### 2.1 登录商户平台
1. 登录 [微信支付商户平台](https://pay.weixin.qq.com)
2. 进入【账户中心】→【API安全】

#### 2.2 下载证书
1. 点击【申请API证书】或【下载证书】
2. 验证身份后下载证书包
3. 证书包包含：
   - `apiclient_cert.p12` - PKCS#12格式证书
   - `apiclient_cert.pem` - PEM格式证书
   - `apiclient_key.pem` - PEM格式私钥

### 步骤3: 配置API密钥

#### 3.1 设置API v3密钥
1. 在商户平台【账户中心】→【API安全】
2. 设置32位API v3密钥（如：ChenZhenyuqianqian18861888886137）
3. **重要**: 密钥设置后无法查看，请妥善保存

### 步骤4: 部署证书文件

#### 4.1 创建证书目录
```bash
mkdir -p backend/certs
```

#### 4.2 上传证书文件
将以下文件上传到 `backend/certs/` 目录：
- `apiclient_cert.pem` - 商户API证书
- `apiclient_key.pem` - 商户私钥

#### 4.3 设置文件权限
```bash
chmod 600 backend/certs/*.pem
chown www-data:www-data backend/certs/*.pem
```

### 步骤5: 获取证书序列号

使用OpenSSL命令提取证书序列号：
```bash
openssl x509 -in backend/certs/apiclient_cert.pem -noout -serial | sed 's/serial=//' | tr 'a-f' 'A-F'
```

预期输出格式：`2CFBD918985AEEE2EF5093BFD556D1B14B080963`

### 步骤6: 配置环境变量

#### 6.1 创建环境配置文件
```bash
cp .env.security.example .env
```

#### 6.2 填写微信支付配置
编辑 `.env` 文件：
```env
# 微信支付V3配置
WECHAT_APPID=wx1234567890abcdef                    # 微信AppID
WECHAT_MCH_ID=1725935616                           # 商户号
WECHAT_API_V3_KEY=ChenZhenyuqianqian18861888886137 # API v3密钥
WECHAT_CERT_SERIAL=2CFBD918985AEEE2EF5093BFD556D1B14B080963 # 证书序列号
WECHAT_CERT_PATH=certs/apiclient_cert.pem          # 证书路径
WECHAT_KEY_PATH=certs/apiclient_key.pem            # 私钥路径
WECHAT_NOTIFY_URL=https://your-domain.com/api/v1/payment/notify # 回调地址

# 支付功能开关
PAYMENT_ENABLED=true
PAYMENT_MOCK_MODE=false  # 生产环境设为false
```

### 步骤7: 配置支付回调

#### 7.1 设置回调URL
- **开发环境**: `http://localhost:3007/api/v1/payment/notify`
- **生产环境**: `https://your-domain.com/api/v1/payment/notify`

#### 7.2 配置域名白名单
在商户平台【产品中心】→【开发配置】中添加：
- 支付授权目录
- JS接口安全域名
- H5支付域名

### 步骤8: 验证配置

#### 8.1 运行配置检查
```bash
cd backend
python check_payment_config.py
```

#### 8.2 预期输出
```
🚀 微信支付配置检查工具
==================================================
✅ 所有配置检查通过！微信支付系统可以正常使用。
🎯 当前运行在生产模式，可以处理真实支付。
```

#### 8.3 启动服务测试
```bash
# 启动后端服务
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 3007

# 启动前端服务
cd client
npm run dev
```

### 步骤9: 生产环境部署

#### 9.1 HTTPS配置
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/ssl/cert.pem;
    ssl_certificate_key /path/to/ssl/key.pem;

    location /api/ {
        proxy_pass http://localhost:3007;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### 9.2 进程管理
```bash
# 使用systemd管理服务
sudo systemctl enable stock-analysis-backend
sudo systemctl start stock-analysis-backend
```

## 🔒 安全考虑

### 证书安全
- ✅ 证书文件权限设为 `600`
- ✅ 定期更换证书（建议每年）
- ✅ 私钥文件绝不提交到代码仓库
- ✅ 生产环境使用独立的证书

### 环境隔离
- ✅ 开发/测试/生产使用不同的密钥
- ✅ 生产环境关闭调试模式
- ✅ 使用防火墙限制API访问
- ✅ 定期检查访问日志

### 数据安全
- ✅ 支付数据加密存储
- ✅ 敏感日志脱敏处理
- ✅ 定期备份支付数据
- ✅ 监控异常支付行为

## 🧪 测试验证

### 开发环境测试
```bash
# 启用模拟模式
PAYMENT_MOCK_MODE=true

# 访问测试页面
http://localhost:8005
```

### 生产环境测试
1. 创建小额测试订单
2. 使用真实微信扫码支付
3. 验证支付回调处理
4. 检查会员权益升级
5. 测试退款流程

## 📞 支持和帮助

### 官方文档
- [微信支付开发文档](https://pay.weixin.qq.com/wiki/doc/apiv3/)
- [商户平台帮助中心](https://kf.qq.com/product/weixinpaymentmerchant.html)

### 常见问题解决
- **签名验证失败**: 检查证书序列号和API密钥
- **回调超时**: 确保回调URL能正常访问
- **证书过期**: 重新下载并部署新证书

### 技术支持
- 微信支付技术支持: 商户平台工单系统
- 系统问题: 查看 `logs/app.log` 错误日志

## 🎯 部署检查清单

部署完成后，请确认以下项目：

- [ ] 环境变量配置正确
- [ ] 证书文件权限正确
- [ ] HTTPS域名可正常访问
- [ ] 支付回调URL配置正确
- [ ] 运行配置检查脚本无错误
- [ ] 创建测试订单成功
- [ ] 支付流程完整可用
- [ ] 退款功能正常
- [ ] 日志记录正常
- [ ] 监控告警配置

完成以上所有项目后，微信支付系统即可投入生产使用！