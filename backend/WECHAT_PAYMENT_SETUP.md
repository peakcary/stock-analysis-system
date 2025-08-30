# 微信支付系统配置指南

## 概述
本文档详细说明了股票分析系统中微信支付功能的配置和部署步骤。系统已实现完整的微信支付流程，包括模拟支付、真实支付、订单管理、退款处理、权限分配和监控告警等功能。

## 系统架构

### 核心组件
- **微信支付服务** (`app/services/wechat_pay.py`) - 集成微信支付API
- **用户会员服务** (`app/services/user_membership.py`) - 管理用户权限和套餐
- **支付监控服务** (`app/services/payment_monitor.py`) - 系统监控和告警
- **支付安全中间件** (`app/middleware/payment_security.py`) - 安全防护

### API端点
- **支付API** (`/api/v1/payment/`) - 订单创建、查询、回调
- **模拟支付API** (`/api/v1/mock/`) - 开发测试用模拟支付
- **管理员API** (`/api/v1/admin/orders/`) - 订单管理和统计
- **监控API** (`/api/v1/admin/payment-monitor/`) - 系统监控

## 配置步骤

### 1. 环境配置

在 `.env` 文件或环境变量中设置以下配置：

```bash
# 基础配置
PAYMENT_ENABLED=true
PAYMENT_MOCK_MODE=true  # 开发测试时设为true，生产环境设为false
BASE_URL=https://yourdomain.com  # 生产环境的完整域名

# 微信支付配置（生产环境必需）
WECHAT_APPID=your_wechat_appid
WECHAT_MCH_ID=your_merchant_id
WECHAT_API_KEY=your_api_key
WECHAT_CERT_PATH=/path/to/apiclient_cert.pem
WECHAT_KEY_PATH=/path/to/apiclient_key.pem
```

### 2. 数据库初始化

确保数据库中包含以下表：
- `payment_packages` - 支付套餐配置
- `payment_orders` - 支付订单记录
- `payment_notifications` - 支付通知记录
- `refund_records` - 退款记录
- `membership_logs` - 会员变更日志

### 3. 支付套餐配置

在数据库中添加支付套餐：

```sql
INSERT INTO payment_packages (
    package_type, name, price, queries_count, validity_days, 
    membership_type, description, is_active, sort_order
) VALUES 
('basic', '基础套餐', 9.90, 100, 30, 'pro', '适合个人用户', 1, 1),
('premium', '高级套餐', 29.90, 500, 90, 'premium', '适合专业用户', 1, 2),
('enterprise', '企业套餐', 99.90, 2000, 365, 'premium', '适合企业用户', 1, 3);
```

## 开发和测试

### 模拟支付模式

当 `PAYMENT_MOCK_MODE=true` 时，系统运行在模拟支付模式下：

1. **创建订单**：
   ```bash
   curl -X POST http://localhost:3007/api/v1/payment/orders \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"package_type": "basic", "payment_method": "wechat_native"}'
   ```

2. **模拟支付成功**：
   ```bash
   curl -X POST http://localhost:3007/api/v1/mock/simulate-payment/{out_trade_no} \
     -H "Authorization: Bearer $TOKEN"
   ```

3. **查询会员状态**：
   ```bash
   curl -X GET http://localhost:3007/api/v1/mock/user-membership \
     -H "Authorization: Bearer $TOKEN"
   ```

### 测试流程

1. 用户注册/登录
2. 查看可用套餐
3. 创建支付订单
4. 模拟支付成功
5. 验证权限激活
6. 测试功能访问权限

## 生产环境部署

### 1. 微信商户配置

1. **申请微信商户号**：
   - 访问 [微信支付商户平台](https://pay.weixin.qq.com/)
   - 完成企业认证和开通流程

2. **配置支付参数**：
   - 获取 `APPID`（微信公众号/小程序）
   - 获取 `MCH_ID`（商户号）
   - 设置 `API密钥`（32位字符串）

3. **下载API证书**：
   - 下载 `apiclient_cert.pem`（公钥证书）
   - 下载 `apiclient_key.pem`（私钥）
   - 将证书文件放置在安全路径

### 2. 服务器配置

1. **HTTPS配置**：
   - 微信支付回调要求HTTPS
   - 配置SSL证书
   - 确保回调地址可访问

2. **防火墙配置**：
   - 开放443端口（HTTPS）
   - 配置微信服务器IP白名单

3. **回调地址配置**：
   - 支付结果通知：`{BASE_URL}/api/v1/payment/notify`
   - 退款结果通知：`{BASE_URL}/api/v1/payment/refund/notify`

### 3. 切换到生产模式

更新环境配置：
```bash
PAYMENT_MOCK_MODE=false
BASE_URL=https://yourdomain.com
WECHAT_APPID=wx1234567890abcdef
WECHAT_MCH_ID=1234567890
WECHAT_API_KEY=your_32_character_api_key
WECHAT_CERT_PATH=/etc/ssl/wechat/apiclient_cert.pem
WECHAT_KEY_PATH=/etc/ssl/wechat/apiclient_key.pem
```

## 安全措施

### 1. 支付安全中间件

- **API限流**：每IP每分钟最多20次支付请求
- **防重放攻击**：基于时间戳和请求签名防重复
- **IP追踪**：记录所有支付API访问
- **签名验证**：验证微信回调的数字签名

### 2. 数据安全

- **敏感信息加密**：API密钥和证书安全存储
- **数据备份**：定期备份支付相关数据
- **访问控制**：管理员权限验证
- **日志审计**：完整的操作日志记录

## 监控和运维

### 1. 系统监控

支付监控服务提供以下指标：

- **健康指标**：成功率、失败率、退款率
- **业务指标**：订单总数、交易金额、活跃用户
- **安全指标**：异常访问、大额交易、快速支付
- **趋势分析**：按日/周/月的统计数据

### 2. 告警机制

- **高失败率告警**：失败率超过10%
- **高退款率告警**：退款率超过5%
- **大额交易提醒**：单笔交易超过1000元
- **系统异常告警**：服务不可用或数据异常

### 3. 管理工具

管理员可以通过API进行：

- **订单管理**：查看、取消、强制完成订单
- **统计分析**：获取各维度的数据统计
- **权限管理**：延长用户套餐有效期
- **系统监控**：查看系统状态和告警信息

## 常见问题

### Q: 模拟支付和真实支付如何切换？
A: 通过 `PAYMENT_MOCK_MODE` 环境变量控制。设为 `true` 启用模拟模式，`false` 启用真实支付。

### Q: 支付回调验证失败怎么办？
A: 检查以下项目：
1. 确认API密钥正确
2. 验证回调URL可访问
3. 确保服务器时间同步
4. 检查请求签名算法

### Q: 退款功能需要什么配置？
A: 退款功能需要：
1. 商户API证书文件
2. 证书文件路径配置正确
3. 服务器能访问微信支付API

### Q: 如何测试支付流程？
A: 在模拟模式下：
1. 创建测试用户
2. 创建支付订单
3. 调用模拟支付成功API
4. 验证权限激活结果

## API文档

### 支付订单API

**创建订单**
```
POST /api/v1/payment/orders
Content-Type: application/json
Authorization: Bearer <token>

{
  "package_type": "basic",
  "payment_method": "wechat_native",
  "client_ip": "127.0.0.1"
}
```

**查询订单**
```
GET /api/v1/payment/orders/{out_trade_no}
Authorization: Bearer <token>
```

**模拟支付成功**（仅模拟模式）
```
POST /api/v1/mock/simulate-payment/{out_trade_no}
Authorization: Bearer <token>
```

### 管理员API

**获取订单列表**
```
GET /api/v1/admin/orders
Authorization: Bearer <admin_token>
```

**获取统计数据**
```
GET /api/v1/admin/orders/statistics?days=30
Authorization: Bearer <admin_token>
```

**系统监控**
```
GET /api/v1/admin/payment-monitor/system-status
Authorization: Bearer <admin_token>
```

## 技术支持

如有技术问题，请检查：
1. 日志文件中的错误信息
2. 数据库连接状态
3. 微信支付商户后台配置
4. 服务器网络连接

更多详细信息请参考微信支付官方文档：https://pay.weixin.qq.com/wiki/doc/api/index.html