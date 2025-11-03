# 💳 支付 API 完整文档

本文档详细说明了所有支付相关的 API 接口，包括请求参数、响应格式和错误处理。

---

## 📋 目录

1. [概述](#概述)
2. [认证](#认证)
3. [支付套餐管理](#支付套餐管理)
4. [订单管理](#订单管理)
5. [支付通知](#支付通知)
6. [本地模拟支付（开发用）](#本地模拟支付开发用)
7. [会员管理](#会员管理)
8. [错误处理](#错误处理)
9. [完整示例](#完整示例)

---

## 概述

### API 基础信息

```
基础 URL: http://localhost:3007/api/v1 (本地开发)
         https://qwquant.com/api/v1       (生产环境)

认证方式: Bearer Token (JWT)
响应格式: JSON
字符编码: UTF-8
```

### 支付流程

```
1. 用户获取支付套餐列表
   GET /payment/packages

2. 用户创建支付订单
   POST /payment/orders

3. 获取二维码或支付链接
   从步骤 2 的返回结果中获取

4. 用户在微信支付平台完成支付
   （或在本地开发环境中模拟支付）

5. 微信服务器发送支付通知
   POST /payment/notify

6. 系统处理通知，激活用户权限
   自动处理，无需前端干预

7. 前端查询订单状态确认支付
   GET /payment/orders/{order_id}
```

---

## 认证

所有需要认证的接口都需要在请求头中包含 JWT Token。

### 登录接口（获取 Token）

```http
POST /auth/login
Content-Type: application/json

{
  "username": "string",
  "password": "string"
}
```

**成功响应 (200):**
```json
{
  "status": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 1800
  }
}
```

### 在请求中使用 Token

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:3007/api/v1/payment/packages
```

---

## 支付套餐管理

### 1. 获取所有支付套餐

**请求:**
```http
GET /payment/packages
Authorization: Bearer {token}
```

**查询参数:**
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| is_active | boolean | 否 | 是否仅显示激活的套餐，默认为 true |

**成功响应 (200):**
```json
[
  {
    "id": 1,
    "package_type": "basic",
    "name": "基础版",
    "price": 99.99,
    "queries_count": 100,
    "validity_days": 30,
    "membership_type": "pro",
    "description": "适合个人使用",
    "is_active": true,
    "sort_order": 1,
    "created_at": "2025-10-24T10:00:00",
    "updated_at": "2025-10-24T10:00:00"
  },
  {
    "id": 2,
    "package_type": "pro",
    "name": "专业版",
    "price": 199.99,
    "queries_count": 500,
    "validity_days": 90,
    "membership_type": "premium",
    "description": "适合专业投资者",
    "is_active": true,
    "sort_order": 2,
    "created_at": "2025-10-24T10:00:00",
    "updated_at": "2025-10-24T10:00:00"
  }
]
```

### 2. 获取特定支付套餐

**请求:**
```http
GET /payment/packages/{package_type}
Authorization: Bearer {token}
```

**路径参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| package_type | string | 套餐类型（basic, pro, premium 等） |

**成功响应 (200):**
```json
{
  "id": 2,
  "package_type": "pro",
  "name": "专业版",
  "price": 199.99,
  "queries_count": 500,
  "validity_days": 90,
  "membership_type": "premium",
  "description": "适合专业投资者",
  "is_active": true,
  "sort_order": 2,
  "created_at": "2025-10-24T10:00:00",
  "updated_at": "2025-10-24T10:00:00"
}
```

**错误响应 (404):**
```json
{
  "detail": "套餐不存在或已停用"
}
```

---

## 订单管理

### 1. 创建支付订单

**请求:**
```http
POST /payment/orders
Authorization: Bearer {token}
Content-Type: application/json

{
  "package_type": "pro",
  "payment_method": "wechat_native"
}
```

**请求体:**
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| package_type | string | 是 | 套餐类型 |
| payment_method | string | 否 | 支付方式，默认 wechat_native |

**支付方式选项:**
- `wechat_native` - 微信扫码支付（PC）
- `wechat_h5` - 微信 H5 支付（手机浏览器）
- `wechat_miniprogram` - 微信小程序支付
- `alipay` - 支付宝（预留）

**成功响应 (200):**
```json
{
  "success": true,
  "message": "订单创建成功",
  "data": {
    "order_id": 12345,
    "out_trade_no": "wx_20251024_143022_001",
    "package_type": "pro",
    "package_name": "专业版",
    "amount": 199.99,
    "status": "pending",
    "payment_method": "wechat_native",
    "code_url": "weixin://wxpay/bizpayurl?pr=...",
    "h5_url": "https://wx.tenpay.com/...",
    "expire_time": "2025-10-24T15:30:22",
    "created_at": "2025-10-24T13:30:22"
  }
}
```

**错误响应 (400):**
```json
{
  "detail": "套餐不存在或已停用"
}
```

### 2. 查询支付订单

**请求:**
```http
GET /payment/orders/{order_id}
Authorization: Bearer {token}
```

**路径参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| order_id | integer | 订单 ID |

**成功响应 (200):**
```json
{
  "id": 12345,
  "out_trade_no": "wx_20251024_143022_001",
  "user_id": 1,
  "package_type": "pro",
  "package_name": "专业版",
  "amount": 199.99,
  "status": "paid",
  "payment_method": "wechat_native",
  "code_url": "weixin://wxpay/bizpayurl?pr=...",
  "h5_url": "https://wx.tenpay.com/...",
  "transaction_id": "4200001234567890",
  "paid_at": "2025-10-24T13:35:00",
  "created_at": "2025-10-24T13:30:22",
  "updated_at": "2025-10-24T13:35:00"
}
```

### 3. 列出用户的订单

**请求:**
```http
GET /payment/orders
Authorization: Bearer {token}
```

**查询参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| status | string | 订单状态过滤（pending, paid, failed 等） |
| skip | integer | 跳过的记录数，默认 0 |
| limit | integer | 返回的记录数，默认 10 |

**成功响应 (200):**
```json
[
  {
    "id": 12345,
    "out_trade_no": "wx_20251024_143022_001",
    "package_type": "pro",
    "package_name": "专业版",
    "amount": 199.99,
    "status": "paid",
    "paid_at": "2025-10-24T13:35:00",
    "created_at": "2025-10-24T13:30:22"
  },
  {
    "id": 12344,
    "out_trade_no": "wx_20251024_130000_001",
    "package_type": "basic",
    "package_name": "基础版",
    "amount": 99.99,
    "status": "paid",
    "paid_at": "2025-10-24T13:05:00",
    "created_at": "2025-10-24T13:00:00"
  }
]
```

---

## 支付通知

### 支付通知回调接口

> ⚠️ **重要**: 这个接口由微信服务器调用，不需要前端手动调用

**请求:**
```http
POST /payment/notify
Content-Type: application/xml

<xml>
  <appid><![CDATA[wx2421b1c4370ec43b]]></appid>
  <attach><![CDATA[支付说明文字说明]]></attach>
  <bank_type><![CDATA[CFT]]></bank_type>
  <billno><![CDATA[1001421C20160425244939305]]></billno>
  <fee_type><![CDATA[CNY]]></fee_type>
  <is_subscribe><![CDATA[N]]></is_subscribe>
  <mch_id>10000100</mch_id>
  <nonce_str><![CDATA[TeqClE41KVxMfmqHvpPK49539qdLXucX]]></nonce_str>
  <openid><![CDATA[oUpF8uMuAJO_M2pxHhQA37NzF-9s]]></openid>
  <out_trade_no><![CDATA[wx_20251024_143022_001]]></out_trade_no>
  <result_code><![CDATA[SUCCESS]]></result_code>
  <return_code><![CDATA[SUCCESS]]></return_code>
  <sign><![CDATA[594B3D97F3EFF242E4FB27D5DF8D47F3]]></sign>
  <time_end>20160425154705</time_end>
  <total_fee>888</total_fee>
  <trade_type><![CDATA[NATIVE]]></trade_type>
  <transaction_id><![CDATA[4008852201602251208786290]]></transaction_id>
</xml>
```

**响应 (成功):**
```xml
<xml>
  <return_code><![CDATA[SUCCESS]]></return_code>
  <return_msg><![CDATA[OK]]></return_msg>
</xml>
```

**系统处理流程:**
1. 验证回调签名
2. 更新订单状态为 PAID
3. 创建 PaymentNotification 记录
4. 自动激活用户权限（创建 MembershipLog）
5. 返回成功响应给微信

---

## 本地模拟支付（开发用）

> 💡 **仅在 PAYMENT_MOCK_MODE=true 时可用**

### 1. 模拟支付成功

**请求:**
```http
POST /mock/simulate-payment/{out_trade_no}
Authorization: Bearer {token}
```

**路径参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| out_trade_no | string | 订单号 |

**成功响应 (200):**
```json
{
  "status": "success",
  "message": "模拟支付成功",
  "data": {
    "out_trade_no": "wx_20251024_143022_001",
    "transaction_id": "4200001234567890abcdef12",
    "amount": 199.99,
    "package_name": "专业版",
    "membership_activated": true,
    "paid_at": "2025-10-24T13:35:00"
  }
}
```

### 2. 获取支付页面（模拟）

**请求:**
```http
GET /mock/payment-page/{out_trade_no}
```

**成功响应 (200):**
```json
{
  "status": "success",
  "data": {
    "order_info": {
      "out_trade_no": "wx_20251024_143022_001",
      "package_name": "专业版",
      "amount": 199.99,
      "status": "pending",
      "created_at": "2025-10-24T13:30:22",
      "expire_time": "2025-10-24T15:30:22"
    },
    "payment_info": {
      "mock_mode": true,
      "payment_method": "wechat_native",
      "payment_url": "http://localhost:3007/api/v1/mock/simulate-payment/wx_20251024_143022_001",
      "instructions": {
        "zh": "这是模拟支付环境。点击下方按钮可以模拟支付成功。",
        "en": "This is a mock payment environment. Click the button below to simulate successful payment."
      }
    }
  }
}
```

### 3. 查询支付状态（模拟）

**请求:**
```http
GET /mock/payment-status/{out_trade_no}
Authorization: Bearer {token}
```

**成功响应 (200):**
```json
{
  "status": "success",
  "data": {
    "order_status": {
      "out_trade_no": "wx_20251024_143022_001",
      "status": "paid",
      "amount": 199.99,
      "package_name": "专业版",
      "created_at": "2025-10-24T13:30:22",
      "paid_at": "2025-10-24T13:35:00",
      "transaction_id": "4200001234567890abcdef12"
    },
    "membership_status": {
      "membership_type": "premium",
      "queries_count": 500,
      "remaining_queries": 498,
      "expiration_date": "2025-01-24",
      "purchase_count": 2
    },
    "mock_mode": true
  }
}
```

---

## 会员管理

### 1. 获取用户会员信息

**请求:**
```http
GET /mock/user-membership
Authorization: Bearer {token}
```

**成功响应 (200):**
```json
{
  "status": "success",
  "data": {
    "membership_status": {
      "user_id": 1,
      "username": "testuser",
      "membership_type": "premium",
      "queries_count": 500,
      "remaining_queries": 498,
      "expiration_date": "2025-01-24",
      "is_expired": false,
      "purchase_count": 2,
      "total_spent": 299.99
    },
    "purchase_history": [
      {
        "order_id": 12345,
        "out_trade_no": "wx_20251024_143022_001",
        "package_name": "专业版",
        "amount": 199.99,
        "status": "paid",
        "purchased_at": "2025-10-24T13:35:00"
      },
      {
        "order_id": 12344,
        "out_trade_no": "wx_20251024_130000_001",
        "package_name": "基础版",
        "amount": 99.99,
        "status": "paid",
        "purchased_at": "2025-10-24T13:05:00"
      }
    ],
    "mock_mode": true
  }
}
```

### 2. 测试功能权限

**请求:**
```http
POST /mock/test-feature-access
Authorization: Bearer {token}

{
  "feature_name": "advanced_analysis"
}
```

**查询参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| feature_name | string | 功能名称 |

**成功响应 (200):**
```json
{
  "status": "success",
  "data": {
    "user_id": 1,
    "feature_name": "advanced_analysis",
    "has_access": true,
    "message": "用户有访问 advanced_analysis 功能的权限"
  }
}
```

---

## 错误处理

### 通用错误响应

#### 401 - 未授权（缺少或无效的 Token）

```json
{
  "detail": "Not authenticated"
}
```

**解决方案:**
- 检查请求头是否包含 `Authorization: Bearer {token}`
- 确认 token 没有过期
- 重新登录获取新的 token

#### 403 - 禁止（无权限操作）

```json
{
  "detail": "无权操作此订单"
}
```

**解决方案:**
- 确认您操作的是自己的订单
- 检查用户权限

#### 404 - 未找到

```json
{
  "detail": "支付订单不存在"
}
```

**解决方案:**
- 确认订单号是否正确
- 检查订单是否属于当前用户

#### 400 - 错误请求

```json
{
  "detail": "套餐不存在或已停用"
}
```

**解决方案:**
- 确认请求参数是否正确
- 检查套餐是否存在

#### 500 - 服务器错误

```json
{
  "detail": "模拟支付失败: [错误详情]"
}
```

**解决方案:**
- 查看服务器日志了解错误原因
- 联系技术支持

---

## 完整示例

### 示例1：完整的购买流程（本地开发）

```bash
#!/bin/bash

# API 基础 URL
API="http://localhost:3007/api/v1"

echo "========== 完整购买流程示例 =========="

# 第1步：登录
echo -e "\n1️⃣ 用户登录..."
LOGIN_RESPONSE=$(curl -s -X POST "$API/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testuser"
  }')

TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.data.access_token')
echo "✅ 获得 Token: ${TOKEN:0:20}..."

# 第2步：获取支付套餐
echo -e "\n2️⃣ 获取支付套餐..."
curl -s -X GET "$API/payment/packages" \
  -H "Authorization: Bearer $TOKEN" | jq '.[] | {package_type, name, price}'

# 第3步：创建支付订单
echo -e "\n3️⃣ 创建支付订单..."
ORDER_RESPONSE=$(curl -s -X POST "$API/payment/orders" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "package_type": "pro",
    "payment_method": "wechat_native"
  }')

echo "$ORDER_RESPONSE" | jq '.data | {order_id, out_trade_no, amount, status}'
OUT_TRADE_NO=$(echo "$ORDER_RESPONSE" | jq -r '.data.out_trade_no')

# 第4步：查看订单（支付前）
echo -e "\n4️⃣ 查询订单状态（支付前）..."
curl -s -X GET "$API/mock/payment-status/$OUT_TRADE_NO" \
  -H "Authorization: Bearer $TOKEN" | jq '.data.order_status | {status, amount}'

# 第5步：模拟支付
echo -e "\n5️⃣ 模拟支付成功..."
PAYMENT_RESPONSE=$(curl -s -X POST "$API/mock/simulate-payment/$OUT_TRADE_NO" \
  -H "Authorization: Bearer $TOKEN")

echo "$PAYMENT_RESPONSE" | jq '.data | {transaction_id, membership_activated}'

# 第6步：查看订单（支付后）
echo -e "\n6️⃣ 查询订单状态（支付后）..."
curl -s -X GET "$API/mock/payment-status/$OUT_TRADE_NO" \
  -H "Authorization: Bearer $TOKEN" | jq '.data.order_status | {status, paid_at}'

# 第7步：查看用户会员信息
echo -e "\n7️⃣ 获取用户会员信息..."
curl -s -X GET "$API/mock/user-membership" \
  -H "Authorization: Bearer $TOKEN" | jq '.data.membership_status | {membership_type, remaining_queries}'

echo -e "\n========== 购买流程完成！=========="
```

---

## 📚 更多资源

- 本地开发设置指南: [LOCAL_DEVELOPMENT.md](LOCAL_DEVELOPMENT.md)
- 数据库模型文档: [models/payment.py](app/models/payment.py)
- 支付服务实现: [services/payment_manager.py](app/services/payment_manager.py)

---

**最后更新**: 2025-10-24
**API 版本**: v1
