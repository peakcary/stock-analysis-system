# 客户端支付功能测试指南

本文档为完整的客户端支付流程测试指南。

## 📋 功能概述

客户端支付系统包含以下组件：

### 1. 客户端认证系统 (`ClientAuthContext.tsx`)
- **路径**: `src/contexts/ClientAuthContext.tsx`
- **功能**: 管理普通用户的登录、注册、token管理
- **导出**:
  - `useClientAuth()` - 钩子函数，使用客户端认证
  - `ClientAuthProvider` - 提供者组件

### 2. 客户端登录页面 (`ClientLoginPage.tsx`)
- **路径**: `src/components/ClientLoginPage.tsx`
- **功能**: 用户登录和注册界面
- **特性**:
  - 登录/注册 Tab 切换
  - 表单验证
  - 支持新用户注册

### 3. 客户端支付页面 (`ClientPaymentPage.tsx`)
- **路径**: `src/components/ClientPaymentPage.tsx`
- **功能**: 支付流程页面
- **特性**:
  - 固定金额: ¥0.01 (测试用)
  - 3 步骤: 创建订单 → 扫码支付 → 支付成功
  - 自动轮询支付状态 (3秒一次)
  - 支持模拟支付 (开发测试)
  - 显示 QR 码

### 4. 应用路由 (`App.tsx`)
- **功能**: 支持同时运行管理员和客户端两种模式
- **模式选择**:
  - 默认: 管理员模式 (http://localhost:5173/)
  - 客户端: 支付模式 (http://localhost:5173/payment 或设置 localStorage `app_mode=client`)

---

## 🚀 快速开始测试

### 前置条件
1. 后端服务运行在 http://localhost:3007
2. 前端开发服务器运行在 http://localhost:5173 (Vite)
3. 已启用支付模拟模式 (后端 `.env` 中 `PAYMENT_MOCK_MODE=true`)

### 步骤 1: 启动前端开发服务器

```bash
cd /Users/peakom/work/stock-analysis-system/frontend
npm run dev
```

### 步骤 2: 访问客户端支付页面

```
http://localhost:5173/payment
```

会自动重定向到客户端登录页面。

### 步骤 3: 创建测试账户或登录

**使用现有账户登录**:
- 用户名: `testuser`
- 密码: `testuser`

**或创建新账户**:
1. 点击 "注册" Tab
2. 输入:
   - 用户名: `testpay_001` (自定义)
   - 邮箱: `test@example.com`
   - 密码: `test1234`
3. 点击 "注册"

---

## 🧪 完整支付流程测试

### 场景 1: 通过模拟支付完成测试

1. **登录** ✓
   - 点击 "登录" Tab
   - 输入用户名和密码
   - 点击 "登录" 按钮
   - 预期: 进入支付页面，显示当前用户名和会员等级

2. **创建订单** ✓
   - 显示支付金额: ¥0.01
   - 点击 "创建支付订单" 按钮
   - 预期:
     - 页面进入第二步 (扫码支付)
     - 显示订单号和二维码
     - 显示倒计时 (120分钟有效期)
     - 显示 "模拟支付" 按钮

3. **模拟支付** ✓
   - 点击 "模拟支付（开发测试）" 按钮
   - 弹出确认对话框
   - 点击 "确定支付"
   - 预期:
     - Toast 提示 "模拟支付成功"
     - 页面自动进入第三步 (支付成功)
     - 显示订单信息和支付成功标志

4. **支付成功** ✓
   - 页面显示:
     - 大的绿色✅ 图标
     - "支付成功！" 标题
     - 订单号、支付金额、支付时间
     - "权限已激活" 提示
   - 按钮:
     - "进行新的支付" - 重新开始流程
     - "返回上一页" - 返回上一页

5. **新的支付** ✓
   - 点击 "进行新的支付"
   - 预期: 回到第一步，可以创建新的支付订单

### 场景 2: 取消订单

1. 创建订单后，点击 "取消订单" 按钮
2. 弹出确认对话框，点击 "确定"
3. 预期:
   - 订单被取消
   - 返回第一步
   - 可以重新创建新订单

### 场景 3: 订单过期

1. 创建订单，等待倒计时结束 (120分钟)
2. 预期: 订单自动过期，页面提示

---

## 📊 API 端点验证

客户端支付使用以下 API 端点:

### 1. 创建支付订单
```
POST /api/v1/payment/orders
请求体: {
  "package_type": "test",
  "amount": 0.01
}
```

### 2. 查询支付状态
```
GET /api/v1/mock/payment-status/{out_trade_no}
```

### 3. 模拟支付 (开发用)
```
POST /api/v1/mock/simulate-payment/{out_trade_no}
```

### 验证这些端点

```bash
# 1. 登录获取 token
curl -X POST http://localhost:3007/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testuser"}'

# 获取 token (从响应中提取)
TOKEN="your_token_here"

# 2. 创建订单
curl -X POST http://localhost:3007/api/v1/payment/orders \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"package_type": "test", "amount": 0.01}'

# 获取 out_trade_no (从响应中提取)
ORDER_NO="order_number_here"

# 3. 查询支付状态（支付前）
curl -X GET http://localhost:3007/api/v1/mock/payment-status/$ORDER_NO \
  -H "Authorization: Bearer $TOKEN"

# 4. 模拟支付
curl -X POST http://localhost:3007/api/v1/mock/simulate-payment/$ORDER_NO \
  -H "Authorization: Bearer $TOKEN"

# 5. 查询支付状态（支付后）
curl -X GET http://localhost:3007/api/v1/mock/payment-status/$ORDER_NO \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🔍 调试技巧

### 查看浏览器控制台日志
1. 打开浏览器 F12 开发工具
2. 切换到 "Console" 标签
3. 查看所有请求和错误日志

### 查看网络请求
1. 打开 "Network" 标签
2. 执行支付流程
3. 查看每个 API 请求的详情:
   - 请求 Headers
   - 请求体
   - 响应数据
   - 响应状态码

### 检查本地存储
1. 打开 "Application" 或 "Storage" 标签
2. 查看 "Local Storage"
3. 查找 `client_token` 和 `client_user` 键
4. 验证存储的数据正确性

### 模拟网络错误
1. 打开 Network 标签
2. 勾选 "Offline" 模式
3. 测试应用的错误处理

---

## ⚠️ 常见问题

### Q: 登录失败，提示"用户名或密码错误"

**原因**: 用户不存在或密码错误

**解决**:
1. 确认后端正在运行
2. 使用正确的用户名和密码
3. 或点击 "注册" 创建新用户

### Q: 创建订单失败，提示"API 客户端未初始化"

**原因**: ClientAuthContext 未正确初始化

**解决**:
1. 确保 ClientAuthProvider 包装了应用
2. 刷新页面重新加载
3. 检查浏览器控制台的错误信息

### Q: 支付页面不显示 QR 码

**原因**:
- API 返回的 code_url 为空
- QRCode 组件未正确渲染

**解决**:
1. 检查后端返回的响应
2. 在浏览器控制台查看错误
3. 确认 `qrcode.react` 包已安装

### Q: 支付状态长时间不更新

**原因**: 状态轮询失败，可能是网络问题或 API 错误

**解决**:
1. 检查浏览器的 Network 标签
2. 确认 API 返回 200 状态码
3. 检查响应数据格式

### Q: 模拟支付按钮不工作

**原因**: 可能的原因:
- 后端未启用模拟模式 (PAYMENT_MOCK_MODE=false)
- 用户未认证
- 订单已过期

**解决**:
1. 检查后端 `.env` 中 `PAYMENT_MOCK_MODE=true`
2. 确认用户已登录
3. 创建新的订单重试

---

## 🔗 相关链接和文件

### 前端相关文件
- `src/contexts/ClientAuthContext.tsx` - 客户端认证上下文
- `src/components/ClientLoginPage.tsx` - 客户端登录页面
- `src/components/ClientPaymentPage.tsx` - 客户端支付页面
- `src/App.tsx` - 应用主入口，支持两种模式

### 后端相关文件 (详见 PAYMENT_SETUP_SUMMARY.md)
- `app/models/payment.py` - 支付数据模型
- `app/services/payment_manager.py` - 支付业务逻辑
- `app/api/api_v1/endpoints/payment.py` - 支付 API 路由
- `app/api/api_v1/endpoints/mock_payment.py` - 模拟支付 API

### 后端文档
- `/Users/peakom/work/stock-analysis-system/backend/PAYMENT_SETUP_SUMMARY.md` - 支付系统总结
- `/Users/peakom/work/stock-analysis-system/backend/PAYMENT_QUICK_START.md` - 快速开始
- `/Users/peakom/work/stock-analysis-system/backend/PAYMENT_API.md` - API 文档

---

## ✅ 测试检查清单

- [ ] 后端服务运行在 http://localhost:3007
- [ ] 前端开发服务器运行在 http://localhost:5173
- [ ] 后端启用模拟支付模式 (PAYMENT_MOCK_MODE=true)
- [ ] 能够成功登录或注册新用户
- [ ] 能够创建支付订单
- [ ] 订单显示正确的金额 (¥0.01)
- [ ] 显示了有效期倒计时
- [ ] QR 码正常显示
- [ ] 能够模拟支付
- [ ] 支付状态自动更新
- [ ] 支付成功后显示成功页面
- [ ] 能够进行新的支付
- [ ] 能够取消订单
- [ ] 能够正常登出

---

## 📝 后续步骤

1. **本地测试完成后**:
   - 将客户端代码提交到 git
   - 整理前后端代码

2. **准备部署**:
   - 编译前端代码 (`npm run build`)
   - 部署到服务器

3. **进阶功能** (后续实现):
   - 支持多种支付套餐（而不仅是测试金额）
   - 支持真实的微信支付
   - 支持支付历史查询
   - 支持用户中心（查看会员信息、购买历史）

---

**测试日期**: 2025-10-27
**前端版本**: React 18.2.0 + TypeScript
**后端版本**: FastAPI + SQLAlchemy
**文档维护人**: Claude Code
