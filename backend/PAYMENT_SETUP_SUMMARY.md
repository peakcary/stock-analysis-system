# 💳 支付功能 - 本地开发完整设置总结

## 📌 您现在拥有的

您的项目已经有一个**完整的、生产级别的支付系统**，现在我为您创建了详细的本地开发文档。

---

## ✨ 已为您准备好的内容

### 1️⃣ 配置文件

**文件**: `.env.local`
- ✅ 完整的本地开发环境配置
- ✅ 支付模拟模式启用 (PAYMENT_MOCK_MODE=true)
- ✅ 所有必需的环境变量示例

### 2️⃣ 文档（按优先级）

#### ⚡ 快速开始（优先读）
**文件**: `PAYMENT_QUICK_START.md`
- ⏱️ 5 分钟快速设置
- 🧪 一键测试脚本
- 🎓 核心代码示例
- 📝 常见问题

#### 📚 完整开发指南
**文件**: `LOCAL_DEVELOPMENT.md`
- 🔧 详细的环境设置步骤
- 🏗️ 项目结构说明
- 📊 支付系统架构图
- 🔍 三种测试方法（UI、cURL、Python）
- 🐛 完整的故障排查

#### 📖 API 文档
**文件**: `PAYMENT_API.md`
- 📋 所有 API 端点详解
- 📝 请求/响应示例
- 🔄 完整支付流程说明
- 🚀 生产环境部署指南

### 3️⃣ 现有的支付系统实现

#### 核心模型
```
PaymentOrder         - 支付订单（订单号、金额、状态等）
PaymentPackage       - 支付套餐（pro、premium 等）
PaymentNotification  - 支付通知/回调记录
MembershipLog        - 用户会员权限日志
RefundRecord         - 退款记录
```

#### 核心服务
```
PaymentManager           - 订单创建、查询、管理
WechatPayService        - 真实微信支付 V2 API
WechatPayV3Service      - 微信支付 V3 API（推荐）
MockPaymentService      - 本地模拟支付
UserMembershipService   - 用户会员权限管理
```

#### 核心 API 端点
```
POST   /payment/orders              - 创建订单
GET    /payment/packages            - 获取支付套餐
GET    /payment/orders/{id}         - 查询订单
POST   /payment/notify              - 支付回调处理

POST   /mock/simulate-payment/{no}  - 模拟支付成功（开发用）
GET    /mock/payment-status/{no}    - 查询支付状态（开发用）
GET    /mock/user-membership        - 获取用户会员信息（开发用）
```

---

## 🚀 快速开始（只需 3 步）

### 第 1 步：配置本地环境

```bash
cd /Users/peakom/work/stock-analysis-system/backend

# 复制配置文件
cp .env.local .env

# 创建数据库
mysql -u root << 'SQL'
CREATE DATABASE IF NOT EXISTS stock_analysis_dev
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
SQL
```

### 第 2 步：启动开发服务器

```bash
# 激活虚拟环境
source venv/bin/activate

# 启动服务器（支持热重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 3007
```

### 第 3 步：运行测试

```bash
# 在另一个终端运行完整测试
python3 test_payment_quick.py

# 或者访问 http://localhost:3007/docs 在 Swagger UI 中测试
```

✅ **就这么简单！** 现在您可以开始开发支付功能了。

---

## 📖 文档阅读顺序

```
1. 您正在读这个文件
   ↓
2. PAYMENT_QUICK_START.md    (5分钟，快速理解)
   ↓
3. LOCAL_DEVELOPMENT.md      (15分钟，详细设置)
   ↓
4. PAYMENT_API.md            (20分钟，完整API)
   ↓
5. 开始开发和测试！
```

---

## 💻 支付功能工作流程

### 完整的支付流程

```
1️⃣ 用户发起支付
   ↓
2️⃣ 创建订单 (POST /payment/orders)
   ├─ 获取套餐信息
   ├─ 调用微信支付 API（或模拟）
   └─ 生成订单号、二维码等
   ↓
3️⃣ 用户支付
   ├─ 真实环境：扫描二维码，完成微信支付
   └─ 开发环境：调用 POST /mock/simulate-payment 模拟支付
   ↓
4️⃣ 支付回调 (POST /payment/notify)
   ├─ 接收微信回调通知
   ├─ 验证回调签名
   ├─ 更新订单状态为 PAID
   └─ 自动激活用户权限
   ↓
5️⃣ 用户获得权限
   ├─ 查询次数增加
   └─ 会员类型升级
```

### 关键数据库表

```sql
-- 支付订单表
CREATE TABLE payment_orders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    out_trade_no VARCHAR(64) UNIQUE,      -- 订单号
    user_id INT,                          -- 用户ID
    package_type VARCHAR(50),             -- 套餐类型
    amount DECIMAL(10,2),                 -- 金额
    status VARCHAR(20),                   -- 状态（pending, paid, failed）
    transaction_id VARCHAR(128),          -- 微信交易ID
    paid_at TIMESTAMP,                    -- 支付时间
    created_at TIMESTAMP DEFAULT NOW()
);

-- 支付套餐表
CREATE TABLE payment_packages (
    id INT PRIMARY KEY AUTO_INCREMENT,
    package_type VARCHAR(50) UNIQUE,      -- 套餐类型
    name VARCHAR(100),                    -- 显示名称
    price DECIMAL(10,2),                  -- 价格
    queries_count INT,                    -- 查询次数
    validity_days INT,                    -- 有效期（天）
    is_active BOOLEAN DEFAULT TRUE
);

-- 支付通知表
CREATE TABLE payment_notifications (
    id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT,
    out_trade_no VARCHAR(64),
    transaction_id VARCHAR(128),
    raw_data JSON,                        -- 原始通知数据
    created_at TIMESTAMP DEFAULT NOW()
);

-- 用户会员表
CREATE TABLE user_memberships (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT UNIQUE,
    membership_type VARCHAR(50),          -- free, pro, premium
    queries_count INT,                    -- 剩余查询次数
    expiration_date DATE,                 -- 过期日期
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 🧪 测试场景

### 场景 1：完整的支付流程（开发环境）

```bash
# 1. 登录获取 token
curl -X POST http://localhost:3007/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testuser"}'

# 2. 获取支付套餐
curl -X GET http://localhost:3007/api/v1/payment/packages \
  -H "Authorization: Bearer YOUR_TOKEN"

# 3. 创建订单
curl -X POST http://localhost:3007/api/v1/payment/orders \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"package_type": "pro"}'

# 4. 模拟支付
curl -X POST http://localhost:3007/api/v1/mock/simulate-payment/ORDER_NUMBER \
  -H "Authorization: Bearer YOUR_TOKEN"

# 5. 查询订单状态
curl -X GET http://localhost:3007/api/v1/mock/payment-status/ORDER_NUMBER \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 场景 2：添加新的支付套餐

```python
from app.models.payment import PaymentPackage
from sqlalchemy.orm import Session

new_package = PaymentPackage(
    package_type="enterprise",
    name="企业版",
    price=999.99,
    queries_count=5000,
    validity_days=365,
    membership_type="premium",
    description="适合企业使用",
    is_active=True,
    sort_order=3
)
db.add(new_package)
db.commit()
```

### 场景 3：修改支付逻辑

编辑以下文件（服务器会自动热重载）：
- `app/services/payment_manager.py` - 订单创建逻辑
- `app/api/api_v1/endpoints/payment.py` - API 端点
- `app/models/payment.py` - 数据模型

---

## 📋 支付系统关键概念

### PaymentStatus（支付状态）
```python
PENDING    = "pending"      # 待支付
PAID       = "paid"         # 已支付
FAILED     = "failed"       # 支付失败
CANCELLED  = "cancelled"    # 已取消
REFUNDED   = "refunded"     # 已退款
EXPIRED    = "expired"      # 已过期
```

### PaymentMethod（支付方式）
```python
WECHAT_NATIVE      = "wechat_native"      # 扫码支付
WECHAT_H5          = "wechat_h5"          # H5 支付
WECHAT_MINIPROGRAM = "wechat_miniprogram" # 小程序支付
ALIPAY             = "alipay"             # 支付宝（预留）
```

### MembershipType（会员类型）
```python
FREE    = "free"      # 免费版
PRO     = "pro"       # 专业版
PREMIUM = "premium"   # 高级版
```

---

## 🔄 开发工作流程

### 修改支付逻辑的步骤

1. **编辑代码**
   ```bash
   # 编辑支付服务
   vi app/services/payment_manager.py

   # 或编辑 API 路由
   vi app/api/api_v1/endpoints/payment.py
   ```

2. **服务器自动热重载**
   - 无需重启服务器
   - 在终端看到 "Uvicorn running on..." 消息

3. **立即测试修改**
   ```bash
   # 在 http://localhost:3007/docs 测试
   # 或运行你的测试脚本
   python3 test_payment_quick.py
   ```

4. **查看日志**
   - 在服务器终端看到完整的请求日志
   - 快速发现问题

### 修改数据模型的步骤

1. **编辑模型**
   ```bash
   vi app/models/payment.py
   ```

2. **停止服务器**
   - 按 Ctrl+C

3. **初始化数据库**
   ```bash
   # 方式1：重新创建表
   python3 -c "
   from app.core.database import Base, engine
   from app.models import *
   Base.metadata.drop_all(bind=engine)
   Base.metadata.create_all(bind=engine)
   "

   # 方式2：或者删除数据库重建
   mysql -u root << 'SQL'
   DROP DATABASE stock_analysis_dev;
   CREATE DATABASE stock_analysis_dev;
   SQL
   ```

4. **重启服务器**
   ```bash
   uvicorn app.main:app --reload
   ```

---

## 🚨 常见陷阱与解决

### 陷阱 1：模拟支付不工作

**原因**: `PAYMENT_MOCK_MODE=false`

**检查**:
```bash
grep PAYMENT_MOCK_MODE .env
# 应该输出：PAYMENT_MOCK_MODE=true
```

### 陷阱 2：数据库连接失败

**原因**: MySQL 没运行或配置错误

**检查**:
```bash
# 确认 MySQL 运行
mysql -u root -e "SELECT 1;"

# 检查 .env 配置
cat .env | grep DATABASE_
```

### 陷阱 3：热重载不工作

**原因**: 某些编辑器可能延迟保存

**解决**:
```bash
# 手动重启服务器
# Ctrl+C 停止
# 重新启动
uvicorn app.main:app --reload
```

### 陷阱 4：导入错误

**原因**: 虚拟环境未激活

**检查**:
```bash
which python3
# 应该输出 venv/bin/python3
```

---

## ✅ 下一步行动

### 立即（现在）

- [ ] 复制 `.env.local` 为 `.env`
- [ ] 创建本地数据库
- [ ] 启动开发服务器
- [ ] 运行测试脚本

### 今天

- [ ] 阅读 `PAYMENT_QUICK_START.md`
- [ ] 在 Swagger UI 中测试所有端点
- [ ] 理解支付流程

### 本周

- [ ] 阅读 `LOCAL_DEVELOPMENT.md`（详细指南）
- [ ] 阅读 `PAYMENT_API.md`（API 文档）
- [ ] 修改支付逻辑进行测试
- [ ] 添加新的支付套餐
- [ ] 添加自定义业务逻辑

### 准备生产部署时

- [ ] 获取真实的微信支付配置（AppID, MCH_ID 等）
- [ ] 设置 `PAYMENT_MOCK_MODE=false`
- [ ] 配置 `WECHAT_NOTIFY_URL` 指向你的服务器
- [ ] 运行完整的测试
- [ ] 执行 `./deploy.sh` 部署到生产环境

---

## 📚 相关文件

```
backend/
├── .env.local                      ← 本地配置示例
├── PAYMENT_QUICK_START.md         ← ⭐ 快速开始（优先读）
├── LOCAL_DEVELOPMENT.md            ← 详细开发指南
├── PAYMENT_API.md                  ← 完整 API 文档
├── PAYMENT_SETUP_SUMMARY.md       ← 这个文件
├── app/models/payment.py           ← 数据模型
├── app/services/
│   ├── payment_manager.py          ← 核心业务逻辑
│   ├── wechat_pay_v3.py           ← 微信支付 V3
│   ├── mock_payment.py            ← 模拟支付
│   └── user_membership.py         ← 会员管理
└── app/api/api_v1/endpoints/
    ├── payment.py                  ← 支付 API 路由
    └── mock_payment.py            ← 模拟支付 API
```

---

## 🎯 关键要点总结

1. **支付系统已完全实现** - 您无需从零开始
2. **本地模拟支付** - 开发时无需真实微信支付
3. **热重载开发** - 修改代码立即生效
4. **完整文档** - 所有 API 和功能都有详细说明
5. **生产就绪** - 可以直接部署到服务器

---

## 🆘 需要帮助？

1. **快速问题** → 查看 `PAYMENT_QUICK_START.md`
2. **开发问题** → 查看 `LOCAL_DEVELOPMENT.md`
3. **API 问题** → 查看 `PAYMENT_API.md`
4. **代码问题** → 查看源代码中的注释

---

## 🎉 现在可以开始了！

```bash
# 一条命令启动开发
cd /Users/peakom/work/stock-analysis-system/backend && \
source venv/bin/activate && \
uvicorn app.main:app --reload --host 0.0.0.0 --port 3007
```

**祝您开发愉快！** 🚀

---

**生成日期**: 2025-10-24
**系统版本**: 1.0
**支持版本**: Python 3.9+ | FastAPI 0.104+ | MySQL 5.7+
