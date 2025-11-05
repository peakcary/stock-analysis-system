# 💳 支付功能集成指南

## 快速开始

您已经拥有一个完整的 React 支付页面组件 `PaymentPage.tsx`，现在需要将它集成到您的应用中。

### 📋 集成步骤

#### 第1步：更新 `App.tsx` - 添加导入

在 `App.tsx` 文件的顶部，添加以下导入：

```typescript
// 在其他 import 语句下方添加
import PaymentPage from './components/PaymentPage';
```

完整的导入部分应该如下所示：

```typescript
import React, { useState, useEffect } from 'react';
// ... 其他导入 ...
import PackageManagement from './components/PackageManagement';
import PaymentPage from './components/PaymentPage';  // 👈 添加这一行
import StockListPage from './components/StockListPage';
// ... 更多导入 ...
```

#### 第2步：添加菜单项

在 `AdminApp` 组件中找到 `menuItems` 数组（大约在第1096行），添加一个新的菜单项：

```typescript
const menuItems = [
  {
    key: 'simple-import',
    icon: <CloudUploadOutlined />,
    label: '数据导入',
  },
  // ... 其他菜单项 ...
  {
    key: 'packages',
    icon: <GiftOutlined />,
    label: '套餐管理',
  },
  {
    key: 'payment',  // 👈 添加这个新菜单项
    icon: <CreditCardOutlined />,
    label: '支付购买',
  },
];
```

**重要**：确保在导入部分添加 `CreditCardOutlined` 图标：

```typescript
import {
  SearchOutlined, UserOutlined, ApiOutlined, UploadOutlined,
  CloudUploadOutlined, FileTextOutlined, DatabaseOutlined,
  CheckCircleOutlined, ClockCircleOutlined, GiftOutlined, DeleteOutlined,
  FireOutlined, ExclamationCircleOutlined,
  CreditCardOutlined  // 👈 添加这个
} from '@ant-design/icons';
```

#### 第3步：添加页面渲染逻辑

在返回 JSX 的 `return` 语句中的 `AdminApp` 组件中，找到其他 `activeTab` 检查的地方（大约在第1175-1177行），添加：

```typescript
{activeTab === 'client-users' && <UserManagement />}
{activeTab === 'admin-users' && <AdminManagement />}
{activeTab === 'packages' && <PackageManagement />}
{activeTab === 'payment' && <PaymentPage />}  // 👈 添加这一行
```

### 🎨 完整示例

以下是修改后的相关部分代码：

**导入部分：**
```typescript
import React, { useState, useEffect } from 'react';
import {
  Layout, Menu, Button, Input, Card, Table, message, Upload, Space,
  Divider, Alert, Row, Col, Typography, Steps, Progress, Statistic,
  Tag, Badge, Tooltip, Spin, Modal, Tabs
} from 'antd';
import {
  SearchOutlined, UserOutlined, ApiOutlined, UploadOutlined,
  CloudUploadOutlined, FileTextOutlined, DatabaseOutlined,
  CheckCircleOutlined, ClockCircleOutlined, GiftOutlined, DeleteOutlined,
  FireOutlined, ExclamationCircleOutlined, CreditCardOutlined
} from '@ant-design/icons';
import { adminApiClient } from '../../shared/admin-auth';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import LoginPage from './components/LoginPage';
import AdminLayout from './components/AdminLayout';
import Dashboard from './components/Dashboard';
import UserManagement from './components/UserManagement';
import AdminManagement from './components/AdminManagement';
import PackageManagement from './components/PackageManagement';
import PaymentPage from './components/PaymentPage';  // 👈 新增
import StockListPage from './components/StockListPage';
// ... 其他导入 ...
```

**菜单项配置：**
```typescript
const menuItems = [
  {
    key: 'simple-import',
    icon: <CloudUploadOutlined />,
    label: '数据导入',
  },
  {
    key: 'concepts',
    icon: <ApiOutlined />,
    label: '概念分析',
  },
  {
    key: 'stock-analysis',
    icon: <SearchOutlined />,
    label: '个股分析',
  },
  {
    key: 'innovation-analysis',
    icon: <FireOutlined />,
    label: '创新高分析',
  },
  {
    key: 'convertible-bonds',
    icon: <DatabaseOutlined />,
    label: '转债分析',
  },
  {
    key: 'user',
    icon: <UserOutlined />,
    label: '用户管理',
  },
  {
    key: 'packages',
    icon: <GiftOutlined />,
    label: '套餐管理',
  },
  {
    key: 'payment',  // 👈 新增菜单项
    icon: <CreditCardOutlined />,
    label: '支付购买',
  },
];
```

**页面渲染：**
```typescript
return (
  <AdminLayout activeTab={activeTab} onTabChange={setActiveTab}>
    <div>
      {/* 控制台页面 */}
      {activeTab === 'dashboard' && <Dashboard />}

      {/* ... 其他页面 ... */}

      {activeTab === 'client-users' && <UserManagement />}
      {activeTab === 'admin-users' && <AdminManagement />}
      {activeTab === 'packages' && <PackageManagement />}
      {activeTab === 'payment' && <PaymentPage />}  {/* 👈 新增 */}
    </div>

    {/* ... Modal 等 ... */}
  </AdminLayout>
);
```

## ✨ 功能说明

### PaymentPage 组件功能

创建的 `PaymentPage` 组件提供以下功能：

#### 🎯 第1步：选择套餐
- 显示所有可用的支付套餐
- 套餐卡片展示：名称、价格、会员类型、查询次数、有效期
- 用户可以选择想要的套餐
- 点击"生成支付二维码"进入下一步

#### 📱 第2步：扫码支付
- 自动生成微信支付二维码
- 展示订单详情（订单号、金额、有效期）
- 实时倒计时显示订单剩余有效期
- 自动监听支付状态（每3秒检查一次）
- 支持手动检查支付状态
- 清晰的支付步骤说明

#### ✅ 第3步：支付成功
- 显示成功提示
- 展示完整的订单信息
- 提供返回首页或继续购买的选项
- 权限自动激活

### 📊 技术细节

**使用的 API 端点：**
- `GET /api/v1/payment/packages` - 获取可用套餐列表
- `POST /api/v1/payment/orders` - 创建支付订单
- `GET /api/v1/payment/orders/{out_trade_no}/status` - 查询支付状态

**认证方式：**
- 自动使用 `useAuth()` 获取当前登录用户
- 所有 API 调用通过 `adminApiClient` 自动附加 JWT 认证令牌
- 无需手动处理认证

**状态管理：**
- 使用 React Hooks (useState, useEffect) 管理组件状态
- 自动轮询支付状态（3秒间隔）
- 支付成功时自动停止轮询

## 🔧 环境要求

确保您的后端配置了以下内容：

1. **WeChat 支付配置**（在 `.env.prod` 或 `.env.production` 中）：
   ```
   WECHAT_APPID=您的AppID
   WECHAT_MCH_ID=您的商户号
   WECHAT_API_V3_KEY=API V3密钥
   WECHAT_CERT_SERIAL=证书序列号
   WECHAT_CERT_PATH=/app/certs/apiclient_cert.pem
   WECHAT_KEY_PATH=/app/certs/apiclient_key.pem
   WECHAT_NOTIFY_URL=https://qwquant.com/api/v1/payment/notify
   ```

2. **商户证书**：
   - 上传证书文件到 `/opt/stock-analysis-system/backend/certs/`
   - 文件：`apiclient_cert.pem` 和 `apiclient_key.pem`

3. **数据库支付表**：
   - 确保 `payment_packages` 表有可用的套餐记录
   - 表结构应包括：package_type, name, price, queries_count, validity_days, membership_type

## 📝 后端 API 说明

### 获取支付套餐
```
GET /api/v1/payment/packages
```
返回可用的支付套餐列表

### 创建支付订单
```
POST /api/v1/payment/orders
Content-Type: application/json

{
  "package_type": "monthly",  // 套餐类型
  "payment_method": "wechat_native"  // 支付方式（Native 扫码）
}
```
返回：
```json
{
  "id": 1,
  "out_trade_no": "...",
  "code_url": "weixin://pay/...",  // 微信支付二维码链接
  "amount": 100.00,
  "status": "PENDING",
  "expire_time": "2025-10-20T14:30:00"
}
```

### 查询支付状态
```
GET /api/v1/payment/orders/{out_trade_no}/status
```
返回：
```json
{
  "out_trade_no": "...",
  "status": "PAID",
  "paid_at": "2025-10-20T14:25:00",
  "transaction_id": "..."
}
```

## 🧪 测试

### 开发环境测试
1. 打开应用登录到后台管理系统
2. 在侧边栏菜单中点击"支付购买"
3. 选择一个支付套餐
4. 点击"生成支付二维码"
5. 查看生成的二维码
6. 使用真实微信账户扫描并完成支付

### 生产环境验证
1. 确保 WeChat 支付配置正确
2. 确保回调地址已在微信商户平台配置
3. 完成一笔真实支付测试
4. 查看后端日志确认回调已收到

## 🐛 常见问题

### Q: 生成二维码失败
**A:** 检查以下项：
- Backend 是否正常运行
- 是否有可用的支付套餐
- WeChat 配置是否完整
- 查看浏览器控制台和服务器日志

### Q: 支付后状态不更新
**A:** 检查以下项：
- 微信支付是否真的成功
- 回调 URL 是否配置正确
- 防火墙是否阻止微信回调
- 查看后端日志中的 payment notify 日志

### Q: 显示"支付订单不存在"
**A:** 这通常表示：
- 订单已过期（2小时）
- 用户不是订单的所有者
- 刷新后重新生成订单

## 📚 相关文件

- **组件文件**: `/frontend/src/components/PaymentPage.tsx`
- **后端路由**: `/backend/app/api/api_v1/endpoints/payment.py`
- **支付服务**: `/backend/app/services/payment_manager.py`

## ✅ 检查清单

实现支付功能后，确保完成以下检查：

- [ ] PaymentPage 组件已正确导入到 App.tsx
- [ ] 菜单项已添加到 AdminLayout
- [ ] 支付页面在导航菜单中可见
- [ ] 可以加载支付套餐列表
- [ ] 可以生成支付二维码
- [ ] 真实支付测试成功完成
- [ ] 支付回调已正确处理
- [ ] 用户权限已正确激活

## 🎉 完成

集成完成后，您的系统现在拥有完整的在线支付功能！

用户可以通过以下流程进行升级：
1. 登录后台管理系统
2. 点击"支付购买"菜单
3. 选择想要购买的套餐
4. 扫描微信二维码完成支付
5. 支付成功后自动获得会员权限

祝您使用愉快！
