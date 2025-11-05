# 🚀 本地开发指南 - 支付功能

本指南涵盖了如何在本地开发环境中开发和测试支付功能。

---

## 📋 目录

1. [环境设置](#环境设置)
2. [项目结构](#项目结构)
3. [支付系统架构](#支付系统架构)
4. [本地开发工作流](#本地开发工作流)
5. [支付功能测试](#支付功能测试)
6. [常见问题](#常见问题)

---

## 环境设置

### 前置要求

```bash
# 检查 Python 版本（3.9+）
python3 --version

# 检查 MySQL 版本（5.7+）
mysql --version

# 检查 pip
pip3 --version
```

### 第1步：克隆项目和进入项目目录

```bash
cd /Users/peakom/work/stock-analysis-system/backend
```

### 第2步：创建虚拟环境

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 如果是 Windows，使用：
# venv\Scripts\activate
```

### 第3步：安装依赖

```bash
# 升级 pip
pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt
```

### 第4步：配置数据库

```bash
# 创建本地开发数据库
mysql -u root -p << 'SQL'
CREATE DATABASE IF NOT EXISTS stock_analysis_dev
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
SQL

# 如果 MySQL 没有密码，使用：
# mysql -u root << 'SQL'
```

### 第5步：配置环境变量

```bash
# 复制本地配置示例
cp .env.local .env

# 编辑 .env 文件（根据需要调整数据库配置）
# 重点注意：
# - DATABASE_HOST=127.0.0.1
# - DATABASE_USER=root
# - DATABASE_PASSWORD=（根据你的MySQL密码）
# - PAYMENT_MOCK_MODE=true （本地开发必须为 true）
```

### 第6步：初始化数据库

```bash
# 创建数据库表和初始数据
python3 << 'PYTHON'
import os
import sys
from pathlib import Path

# 设置项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置环境变量
os.environ["DATABASE_HOST"] = "127.0.0.1"
os.environ["DATABASE_PORT"] = "3306"
os.environ["DATABASE_USER"] = "root"
os.environ["DATABASE_PASSWORD"] = ""
os.environ["DATABASE_NAME"] = "stock_analysis_dev"

try:
    from app.core.database import create_tables, Base, engine
    from app.models import *

    print("🔧 创建数据库表...")
    Base.metadata.create_all(bind=engine, checkfirst=True)
    print("✅ 表创建成功")

    print("👤 创建默认用户...")
    from sqlalchemy.orm import sessionmaker
    from app.models.user import User
    from app.models.admin_user import AdminUser
    from app.core.security import get_password_hash

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    # 创建默认管理员用户
    existing_admin = db.query(AdminUser).filter(AdminUser.username == "admin").first()
    if not existing_admin:
        admin = AdminUser(
            username="admin",
            email="admin@example.com",
            password_hash=get_password_hash("admin"),
            is_superuser=True
        )
        db.add(admin)
        db.commit()
        print("✅ 默认管理员用户已创建 (admin / admin)")
    else:
        print("⚠️  管理员用户已存在")

    # 创建默认客户端用户
    existing_user = db.query(User).filter(User.username == "testuser").first()
    if not existing_user:
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash=get_password_hash("testuser")
        )
        db.add(user)
        db.commit()
        print("✅ 默认客户端用户已创建 (testuser / testuser)")
    else:
        print("⚠️  客户端用户已存在")

    db.close()
    print("\n✅ 数据库初始化完成！")

except Exception as e:
    print(f"❌ 错误: {e}")
    sys.exit(1)
PYTHON
```

### 第7步：启动开发服务器

```bash
# 启动 FastAPI 开发服务器（自动热重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 3007

# 如果需要指定具体的 Python 解释器
/path/to/venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 3007
```

✅ **现在您可以在 http://localhost:3007 访问 API 文档**

```
- Swagger UI: http://localhost:3007/docs
- ReDoc: http://localhost:3007/redoc
- OpenAPI JSON: http://localhost:3007/openapi.json
```

---

## 项目结构

```
backend/
├── app/
│   ├── main.py                    ← FastAPI 应用入口
│   ├── core/
│   │   ├── config.py             ← 配置管理
│   │   ├── database.py           ← 数据库连接
│   │   ├── auth.py               ← 认证逻辑
│   │   └── security.py           ← 加密和安全
│   ├── models/
│   │   ├── payment.py            ← 💳 支付数据模型
│   │   ├── user.py               ← 用户模型
│   │   └── ...
│   ├── schemas/
│   │   ├── payment.py            ← 支付请求/响应 Schema
│   │   └── ...
│   ├── services/
│   │   ├── payment_manager.py    ← 💳 支付业务逻辑
│   │   ├── wechat_pay_v3.py      ← 微信支付 V3 API
│   │   ├── mock_payment.py       ← 💳 模拟支付服务
│   │   ├── user_membership.py    ← 用户会员管理
│   │   └── ...
│   └── api/
│       └── api_v1/
│           └── endpoints/
│               ├── payment.py    ← 💳 支付 API 路由
│               ├── mock_payment.py ← 💳 模拟支付 API
│               └── ...
├── .env.local                     ← 💻 本地开发配置（复制为 .env）
├── requirements.txt               ← 依赖包
└── LOCAL_DEVELOPMENT.md          ← 这个文件
```

**💳 = 支付相关文件**
**💻 = 本地开发文件**

---

## 支付系统架构

### 整体架构图

```
用户发起支付
    ↓
┌─────────────────────────────────────────┐
│ 1. 创建订单 (POST /api/v1/payment/orders)│
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ PaymentManager.create_payment_order()    │
│   ├─ 获取支付套餐信息                    │
│   ├─ 调用微信支付 API（或模拟支付）     │
│   └─ 存储 PaymentOrder 到数据库         │
└─────────────────────────────────────────┘
    ↓
返回支付信息给前端
    ├─ out_trade_no: 订单号
    ├─ code_url: 二维码 URL（模式下为模拟）
    ├─ h5_url: H5 支付链接
    └─ amount: 支付金额
    ↓
┌─────────────────────────────────────────┐
│ 2. 用户支付（模拟或真实）               │
│    模拟: POST /api/v1/mock/simulate-pay │
│    真实: 微信支付平台                    │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 3. 支付回调 (POST /api/v1/payment/notify)│
│   ├─ 验证回调签名                       │
│   ├─ 更新订单状态为 PAID                │
│   ├─ 创建 PaymentNotification 记录      │
│   └─ 触发用户权限激活                   │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 4. 激活用户权限                         │
│    UserMembershipService.activate()     │
│   ├─ 创建 MembershipLog 日志            │
│   ├─ 更新用户会员状态                   │
│   └─ 增加查询次数                       │
└─────────────────────────────────────────┘
    ↓
✅ 支付完成，用户获得权限
```

### 核心数据模型

#### PaymentOrder（支付订单）
```python
{
    id: int,                       # 订单 ID
    out_trade_no: str,            # 微信订单号
    user_id: int,                 # 用户 ID
    package_type: str,            # 套餐类型（basic, pro, premium）
    amount: Decimal,              # 金额（元）
    status: PaymentStatus,        # 状态（pending, paid, failed, cancelled...）
    payment_method: PaymentMethod,# 支付方式（wechat_native, wechat_h5...）
    code_url: str,                # 二维码 URL
    h5_url: str,                  # H5 支付 URL
    transaction_id: str,          # 微信交易 ID
    paid_at: datetime,            # 支付时间
    notify_status: str,           # 通知状态
    expire_time: datetime,        # 订单过期时间
    created_at: datetime,         # 创建时间
    updated_at: datetime,         # 更新时间
}
```

#### PaymentPackage（支付套餐）
```python
{
    id: int,
    package_type: str,            # 套餐类型
    name: str,                    # 显示名称（如"专业版"）
    price: Decimal,               # 价格（元）
    queries_count: int,           # 查询次数
    validity_days: int,           # 有效期（天）
    membership_type: str,         # 会员类型（free, pro, premium）
    description: str,             # 描述
    is_active: bool,              # 是否激活
}
```

#### PaymentNotification（支付通知）
```python
{
    id: int,
    order_id: int,                # 关联的订单 ID
    out_trade_no: str,            # 订单号
    transaction_id: str,          # 微信交易 ID
    notification_type: str,       # 通知类型（payment, refund）
    raw_data: JSON,               # 原始通知数据
    created_at: datetime,
}
```

---

## 本地开发工作流

### 工作流程1：仅修改支付 API 逻辑

```bash
# 1. 激活虚拟环境
source venv/bin/activate

# 2. 启动开发服务器（支持热重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 3007

# 3. 修改支付相关代码
#    编辑 app/services/payment_manager.py
#    或  app/api/api_v1/endpoints/payment.py
#    或  app/models/payment.py

# 4. 服务器会自动重载
#    在终端看到 "Uvicorn running on..." 消息

# 5. 使用 API 测试修改
#    在 http://localhost:3007/docs 测试
```

### 工作流程2：修改数据模型

```bash
# 1. 修改 ORM 模型
#    编辑 app/models/payment.py

# 2. 停止开发服务器 (Ctrl + C)

# 3. 创建数据库迁移（如果需要）
#    或直接重新初始化数据库（开发时）

# 4. 重新启动服务器
#    uvicorn app.main:app --reload --host 0.0.0.0 --port 3007
```

### 工作流程3：测试支付流程

```bash
# 1. 启动服务器
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 3007

# 2. 在另一个终端运行测试脚本
#    看下面的"支付功能测试"部分

# 3. 查看日志
#    在服务器终端看详细日志
```

---

## 支付功能测试

### 方式1：使用 API 文档界面（最简单）

1. 打开浏览器访问 http://localhost:3007/docs
2. 找到支付相关的端点：
   - `GET /api/v1/payment/packages` - 获取支付套餐
   - `POST /api/v1/payment/orders` - 创建订单
   - `GET /api/v1/mock/payment-status/{out_trade_no}` - 查询订单状态
   - `POST /api/v1/mock/simulate-payment/{out_trade_no}` - 模拟支付成功

3. 点击"Try it out"按钮测试

**测试步骤：**
```
1. 先获取套餐列表
   GET /api/v1/payment/packages

2. 创建支付订单
   POST /api/v1/payment/orders
   {
     "package_type": "pro"
   }

3. 获取返回的 out_trade_no，查询订单状态
   GET /api/v1/mock/payment-status/{out_trade_no}

4. 模拟支付成功
   POST /api/v1/mock/simulate-payment/{out_trade_no}

5. 再查询一次订单状态，应该已支付
   GET /api/v1/mock/payment-status/{out_trade_no}
```

### 方式2：使用 cURL 命令行

```bash
#!/bin/bash

# 获取用户 token
TOKEN=$(curl -s -X POST "http://localhost:3007/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testuser"}' \
  | jq -r '.data.access_token')

echo "Token: $TOKEN"

# 获取支付套餐列表
echo "📋 获取支付套餐..."
curl -s -X GET "http://localhost:3007/api/v1/payment/packages" \
  -H "Authorization: Bearer $TOKEN" | jq .

# 创建支付订单
echo "📝 创建支付订单..."
ORDER_RESPONSE=$(curl -s -X POST "http://localhost:3007/api/v1/payment/orders" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"package_type": "pro"}')

echo "$ORDER_RESPONSE" | jq .
OUT_TRADE_NO=$(echo "$ORDER_RESPONSE" | jq -r '.data.out_trade_no')

echo "Out Trade No: $OUT_TRADE_NO"

# 查询订单状态
echo "🔍 查询订单状态（支付前）..."
curl -s -X GET "http://localhost:3007/api/v1/mock/payment-status/$OUT_TRADE_NO" \
  -H "Authorization: Bearer $TOKEN" | jq .

# 模拟支付成功
echo "💳 模拟支付成功..."
curl -s -X POST "http://localhost:3007/api/v1/mock/simulate-payment/$OUT_TRADE_NO" \
  -H "Authorization: Bearer $TOKEN" | jq .

# 再次查询订单状态
echo "🔍 查询订单状态（支付后）..."
curl -s -X GET "http://localhost:3007/api/v1/mock/payment-status/$OUT_TRADE_NO" \
  -H "Authorization: Bearer $TOKEN" | jq .

# 获取用户会员信息
echo "👤 获取用户会员信息..."
curl -s -X GET "http://localhost:3007/api/v1/mock/user-membership" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

### 方式3：使用 Python 脚本

创建文件 `test_payment.py`：

```python
#!/usr/bin/env python3
"""
支付功能测试脚本
Payment Feature Test Script
"""

import requests
import json
from datetime import datetime

# 配置
API_BASE_URL = "http://localhost:3007/api/v1"
TEST_USERNAME = "testuser"
TEST_PASSWORD = "testuser"

class PaymentTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None

    def login(self):
        """用户登录"""
        print("🔐 用户登录...")
        response = self.session.post(
            f"{API_BASE_URL}/auth/login",
            json={
                "username": TEST_USERNAME,
                "password": TEST_PASSWORD
            }
        )

        if response.status_code == 200:
            self.token = response.json()['data']['access_token']
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            print("✅ 登录成功")
            return True
        else:
            print(f"❌ 登录失败: {response.text}")
            return False

    def get_packages(self):
        """获取支付套餐列表"""
        print("\n📋 获取支付套餐...")
        response = self.session.get(f"{API_BASE_URL}/payment/packages")

        if response.status_code == 200:
            packages = response.json()
            print("✅ 套餐列表:")
            for pkg in packages:
                print(f"   - {pkg['package_type']}: {pkg['name']} (¥{pkg['price']})")
            return packages
        else:
            print(f"❌ 获取套餐失败: {response.text}")
            return []

    def create_order(self, package_type="pro"):
        """创建支付订单"""
        print(f"\n📝 创建支付订单 ({package_type})...")
        response = self.session.post(
            f"{API_BASE_URL}/payment/orders",
            json={"package_type": package_type}
        )

        if response.status_code == 200:
            order_data = response.json()['data']
            print("✅ 订单创建成功:")
            print(f"   - 订单号: {order_data['out_trade_no']}")
            print(f"   - 金额: ¥{order_data['amount']}")
            print(f"   - 过期时间: {order_data['expire_time']}")
            return order_data
        else:
            print(f"❌ 创建订单失败: {response.text}")
            return None

    def check_order_status(self, out_trade_no):
        """查询订单状态"""
        print(f"\n🔍 查询订单状态...")
        response = self.session.get(
            f"{API_BASE_URL}/mock/payment-status/{out_trade_no}"
        )

        if response.status_code == 200:
            data = response.json()['data']
            order_status = data['order_status']
            print("✅ 订单状态:")
            print(f"   - 订单号: {order_status['out_trade_no']}")
            print(f"   - 状态: {order_status['status']}")
            print(f"   - 金额: ¥{order_status['amount']}")
            print(f"   - 创建时间: {order_status['created_at']}")
            if order_status['paid_at']:
                print(f"   - 支付时间: {order_status['paid_at']}")
            return order_status
        else:
            print(f"❌ 查询失败: {response.text}")
            return None

    def simulate_payment(self, out_trade_no):
        """模拟支付成功"""
        print(f"\n💳 模拟支付成功...")
        response = self.session.post(
            f"{API_BASE_URL}/mock/simulate-payment/{out_trade_no}"
        )

        if response.status_code == 200:
            payment_data = response.json()['data']
            print("✅ 支付成功:")
            print(f"   - 订单号: {payment_data['out_trade_no']}")
            print(f"   - 交易 ID: {payment_data['transaction_id']}")
            print(f"   - 套餐: {payment_data['package_name']}")
            print(f"   - 权限已激活: {payment_data['membership_activated']}")
            print(f"   - 支付时间: {payment_data['paid_at']}")
            return payment_data
        else:
            print(f"❌ 支付失败: {response.text}")
            return None

    def get_membership_info(self):
        """获取用户会员信息"""
        print(f"\n👤 获取用户会员信息...")
        response = self.session.get(f"{API_BASE_URL}/mock/user-membership")

        if response.status_code == 200:
            data = response.json()['data']
            membership = data['membership_status']
            print("✅ 会员信息:")
            print(f"   - 会员类型: {membership['membership_type']}")
            print(f"   - 查询次数: {membership['remaining_queries']}/{membership['queries_count']}")
            print(f"   - 过期时间: {membership['expiration_date']}")
            if data['purchase_history']:
                print(f"   - 购买历史: {len(data['purchase_history'])} 条")
            return membership
        else:
            print(f"❌ 获取失败: {response.text}")
            return None

    def run_full_test(self):
        """运行完整测试流程"""
        print("=" * 50)
        print("🚀 支付功能完整测试流程")
        print("=" * 50)

        # 1. 登录
        if not self.login():
            return

        # 2. 获取套餐
        packages = self.get_packages()
        if not packages:
            return

        # 3. 创建订单
        order = self.create_order("pro")
        if not order:
            return

        out_trade_no = order['out_trade_no']

        # 4. 查询订单状态（支付前）
        print("\n" + "=" * 50)
        print("支付前状态")
        print("=" * 50)
        self.check_order_status(out_trade_no)

        # 5. 模拟支付
        print("\n" + "=" * 50)
        print("执行支付")
        print("=" * 50)
        self.simulate_payment(out_trade_no)

        # 6. 查询订单状态（支付后）
        print("\n" + "=" * 50)
        print("支付后状态")
        print("=" * 50)
        self.check_order_status(out_trade_no)

        # 7. 获取会员信息
        print("\n" + "=" * 50)
        print("会员信息")
        print("=" * 50)
        self.get_membership_info()

        print("\n" + "=" * 50)
        print("✅ 完整测试流程已完成!")
        print("=" * 50)

if __name__ == "__main__":
    tester = PaymentTester()
    tester.run_full_test()
```

运行测试：
```bash
python3 test_payment.py
```

---

## 常见问题

### Q1: 启动时报错 "No module named 'app'"

**解决方案：**
```bash
# 确保虚拟环境已激活
source venv/bin/activate

# 确保在 backend 目录
cd /Users/peakom/work/stock-analysis-system/backend

# 启动服务器
uvicorn app.main:app --reload
```

### Q2: 数据库连接失败

**检查步骤：**
```bash
# 1. 确认 MySQL 运行
mysql -u root -p -e "SELECT 1;"

# 2. 检查 .env 文件中的数据库配置
cat .env | grep DATABASE

# 3. 尝试直接连接
mysql -u root -p -h 127.0.0.1 -D stock_analysis_dev
```

### Q3: 模拟支付不工作

**检查步骤：**
```bash
# 1. 确认 PAYMENT_MOCK_MODE=true
grep PAYMENT_MOCK_MODE .env

# 2. 确认已登录并有有效的 token
# 3. 确认订单存在且状态为 PENDING
```

### Q4: 如何查看数据库中的支付数据？

```bash
# 连接数据库
mysql -u root -p stock_analysis_dev

# 查看支付套餐
SELECT * FROM payment_packages;

# 查看支付订单
SELECT id, out_trade_no, status, amount, created_at FROM payment_orders;

# 查看支付通知
SELECT * FROM payment_notifications;

# 查看用户会员
SELECT id, username, membership_type, queries_count FROM users;
```

### Q5: 如何重置测试数据？

```bash
# 方式1：清空表（保留结构）
mysql -u root -p stock_analysis_dev << 'SQL'
TRUNCATE TABLE payment_orders;
TRUNCATE TABLE payment_notifications;
TRUNCATE TABLE membership_logs;
SQL

# 方式2：重新初始化整个数据库
mysql -u root -p << 'SQL'
DROP DATABASE stock_analysis_dev;
CREATE DATABASE stock_analysis_dev
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
SQL

# 然后再次运行初始化脚本
```

---

## 🎯 下一步

现在您已经可以：

1. ✅ 在本地启动开发服务器
2. ✅ 测试完整的支付流程
3. ✅ 修改支付相关的代码并实时查看效果
4. ✅ 理解支付系统的整个架构

**准备好部署到服务器时：**
- 修改微信支付配置（真实的 AppID, MCH_ID 等）
- 将 `PAYMENT_MOCK_MODE` 改为 `false`
- 设置正确的 `WECHAT_NOTIFY_URL` 指向服务器
- 执行 `./deploy.sh` 部署到生产环境

---

**需要帮助？** 查看支付系统的详细文档或查看代码注释。

祝您开发愉快！🚀
