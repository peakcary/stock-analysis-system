# 微信支付证书配置说明

## 📋 需要的证书文件

微信支付V3 API需要以下证书文件：

### 1. 商户API证书 (`apiclient_cert.pem`)
- **用途**: 用于API调用的身份验证
- **获取方式**: 从微信商户平台下载
- **格式**: PEM格式的X.509证书

### 2. 商户私钥文件 (`apiclient_key.pem`)
- **用途**: 用于生成API签名
- **获取方式**: 从微信商户平台下载的证书包中提取
- **格式**: PEM格式的RSA私钥

### 3. 证书序列号
- **用途**: 标识使用的证书版本
- **获取方式**: 从微信商户平台查看，或使用OpenSSL命令提取
- **格式**: 40位十六进制字符串

## 🔧 配置步骤

### 步骤1: 下载证书文件
1. 登录微信商户平台 (https://pay.weixin.qq.com)
2. 进入【账户中心】-【API安全】
3. 下载API证书

### 步骤2: 放置证书文件
将下载的证书文件放在此目录下：
```
backend/certs/
├── apiclient_cert.pem    # 商户证书
├── apiclient_key.pem     # 商户私钥
└── README.md             # 此说明文件
```

### 步骤3: 获取证书序列号
使用OpenSSL命令获取证书序列号：
```bash
openssl x509 -in apiclient_cert.pem -noout -serial | sed 's/serial=//' | tr 'a-f' 'A-F'
```

### 步骤4: 配置环境变量
在 `.env` 文件中配置：
```env
# 微信支付V3配置
WECHAT_APPID=wx1234567890abcdef           # 微信AppID
WECHAT_MCH_ID=1725935616                  # 商户号
WECHAT_API_V3_KEY=your_32_char_api_key    # API v3密钥
WECHAT_CERT_SERIAL=2CFBD918985AEEE2EF5093BFD556D1B14B080963  # 证书序列号
WECHAT_CERT_PATH=certs/apiclient_cert.pem # 证书路径
WECHAT_KEY_PATH=certs/apiclient_key.pem   # 私钥路径
WECHAT_NOTIFY_URL=https://your-domain.com/api/v1/payment/notify  # 回调地址
```

## 🔒 安全注意事项

### 重要提醒
1. **私钥文件安全性极高**，绝对不要提交到代码仓库
2. **定期更换证书**，建议每年更换一次
3. **限制文件访问权限**，设置为仅服务器进程可读
4. **使用HTTPS**，所有支付相关接口必须使用HTTPS

### 文件权限设置
```bash
# 设置证书文件权限
chmod 600 certs/apiclient_cert.pem
chmod 600 certs/apiclient_key.pem
chown www-data:www-data certs/*.pem
```

### Git忽略配置
确保 `.gitignore` 包含：
```
# 微信支付证书文件
certs/*.pem
certs/*.p12
*.key
*.cert
```

## 🧪 测试验证

### 验证证书配置
运行以下命令验证证书是否正确配置：
```bash
python -c "
from app.services.wechat_pay_v3 import wechat_pay_v3_service
print('证书配置:', wechat_pay_v3_service.get_config_status())
"
```

### 开发模式
开发阶段可以启用模拟模式：
```env
PAYMENT_MOCK_MODE=true
```

## 📞 获取帮助

如果遇到证书配置问题：

1. **微信支付官方文档**: https://pay.weixin.qq.com/wiki/doc/apiv3/
2. **商户平台帮助**: 登录商户平台查看帮助文档
3. **技术支持**: 联系微信支付技术支持

## ⚠️ 常见问题

### Q: 证书文件格式错误
A: 确保下载的是PEM格式证书，如果是p12格式需要转换：
```bash
openssl pkcs12 -in apiclient_cert.p12 -out apiclient_cert.pem -clcerts -nokeys
openssl pkcs12 -in apiclient_cert.p12 -out apiclient_key.pem -nocerts -nodes
```

### Q: 签名验证失败
A: 检查证书序列号是否正确，时钟是否同步

### Q: 证书过期
A: 重新从商户平台下载最新证书并更新配置