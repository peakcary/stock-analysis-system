# ⚡ 支付功能快速开始

本指南帮助您快速开始支付功能的本地开发和测试。

---

## 🎯 5 分钟快速设置

### 步骤 1: 复制配置文件

```bash
cd /Users/peakom/work/stock-analysis-system/backend
cp .env.local .env
```

### 步骤 2: 创建数据库

```bash
# 如果数据库不存在，创建它
mysql -u root << 'SQL'
CREATE DATABASE IF NOT EXISTS stock_analysis_dev
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
SQL

# 初始化表
python3 -c "
import os
os.environ['DATABASE_HOST'] = '127.0.0.1'
os.environ['DATABASE_USER'] = 'root'
os.environ['DATABASE_PASSWORD'] = ''
os.environ['DATABASE_NAME'] = 'stock_analysis_dev'

from app.core.database import Base, engine
from app.models import *
Base.metadata.create_all(bind=engine)
print('✅ 数据库初始化完成')
"
```

### 步骤 3: 启动服务器

```bash
# 激活虚拟环境
source venv/bin/activate

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 3007
```

✅ **现在访问 http://localhost:3007/docs 查看 API 文档**

---

## 🧪 开始测试

### 方式 1: 使用 Swagger UI（最简单）

1. 打开 http://localhost:3007/docs
2. 找到支付相关的接口
3. 点击 "Try it out" 测试

### 方式 2: 使用一键测试脚本

创建文件 `test_payment_quick.py`：

```python
#!/usr/bin/env python3
import requests
import json

API = "http://localhost:3007/api/v1"

# 登录获取 token
print("🔐 登录...")
res = requests.post(f"{API}/auth/login", json={
    "username": "testuser",
    "password": "testuser"
})
if res.status_code != 200:
    # 创建默认用户
    print("创建默认用户...")
    # 用户创建需要其他方式，这里假设已存在

token = res.json()['data']['access_token']
headers = {"Authorization": f"Bearer {token}"}

# 获取套餐
print("📋 获取支付套餐...")
pkgs = requests.get(f"{API}/payment/packages", headers=headers).json()
for pkg in pkgs:
    print(f"  - {pkg['package_type']}: {pkg['name']} (¥{pkg['price']})")

# 创建订单
print("📝 创建支付订单...")
order = requests.post(f"{API}/payment/orders",
    headers=headers,
    json={"package_type": "pro"}
).json()['data']
print(f"  ✅ 订单号: {order['out_trade_no']}")
print(f"  💰 金额: ¥{order['amount']}")

# 查询订单（支付前）
out_trade_no = order['out_trade_no']
print(f"🔍 查询订单状态（支付前）...")
status = requests.get(f"{API}/mock/payment-status/{out_trade_no}",
    headers=headers
).json()['data']['order_status']
print(f"  状态: {status['status']}")

# 模拟支付
print("💳 模拟支付...")
requests.post(f"{API}/mock/simulate-payment/{out_trade_no}",
    headers=headers
)
print("  ✅ 支付成功")

# 查询订单（支付后）
print("🔍 查询订单状态（支付后）...")
status = requests.get(f"{API}/mock/payment-status/{out_trade_no}",
    headers=headers
).json()['data']['order_status']
print(f"  状态: {status['status']}")
print(f"  支付时间: {status['paid_at']}")

# 查看会员信息
print("👤 用户会员信息...")
member = requests.get(f"{API}/mock/user-membership",
    headers=headers
).json()['data']['membership_status']
print(f"  会员类型: {member['membership_type']}")
print(f"  剩余查询次数: {member['remaining_queries']}/{member['queries_count']}")

print("\n✅ 完整流程测试完成！")
```

运行：
```bash
python3 test_payment_quick.py
```

---

## 📁 关键文件速查

| 文件 | 说明 |
|------|------|
| `.env.local` | 本地配置示例 |
| `LOCAL_DEVELOPMENT.md` | 详细的开发指南 |
| `PAYMENT_API.md` | 完整的 API 文档 |
| `app/models/payment.py` | 数据模型 |
| `app/services/payment_manager.py` | 支付业务逻辑 |
| `app/api/api_v1/endpoints/payment.py` | 支付 API 路由 |
| `app/api/api_v1/endpoints/mock_payment.py` | 模拟支付 API |

---

## 🎓 支付流程快速理解

```
订单状态流转：
pending (创建订单)
   ↓
paid (支付成功)
   ↓
✅ 用户获得权限

主要系统：
1. PaymentOrder 表    - 存储订单信息
2. PaymentPackage 表  - 存储套餐信息
3. PaymentNotification 表 - 存储支付通知
4. MembershipLog 表   - 记录用户权限变更

核心逻辑：
订单创建 → 微信/模拟支付 → 支付回调 → 激活权限
```

---

## 🔧 修改和开发

### 添加新的支付套餐

```python
# 在数据库中插入新套餐
from app.models.payment import PaymentPackage

package = PaymentPackage(
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
db.add(package)
db.commit()
```

### 修改支付逻辑

编辑 `app/services/payment_manager.py`，服务器会自动热重载。

### 添加新的 API 端点

编辑 `app/api/api_v1/endpoints/payment.py`，服务器会自动热重载。

---

## 🐛 常见问题

### Q: 启动失败，数据库连接不上？

```bash
# 检查 MySQL 是否运行
mysql -u root -e "SELECT 1;"

# 检查 .env 配置
cat .env | grep DATABASE_

# 如果密码错误，编辑 .env
```

### Q: 模拟支付不工作？

```bash
# 确认 PAYMENT_MOCK_MODE=true
grep PAYMENT_MOCK_MODE .env

# 确认已登录
# 确认订单状态为 PENDING
```

### Q: 如何重置测试数据？

```bash
# 清空表（保留结构）
mysql -u root stock_analysis_dev << 'SQL'
TRUNCATE TABLE payment_orders;
TRUNCATE TABLE payment_notifications;
TRUNCATE TABLE membership_logs;
SQL
```

---

## 📝 支付系统核心代码片段

### 创建订单的核心逻辑

```python
# app/services/payment_manager.py

async def create_payment_order(self, user: User, package_type: str, db: Session):
    # 1. 获取套餐信息
    package = db.query(PaymentPackage).filter(
        PaymentPackage.package_type == package_type
    ).first()

    # 2. 调用微信支付 API（或模拟支付）
    pay_result = await self.wechat_pay_v3.unified_order(
        user_id=user.id,
        package_type=package_type,
        total_fee=int(package.price * 100),  # 转换为分
        trade_type="NATIVE"  # 扫码支付
    )

    # 3. 创建订单记录
    order = PaymentOrder(
        out_trade_no=pay_result['out_trade_no'],
        user_id=user.id,
        package_type=package_type,
        amount=Decimal(str(package.price)),
        code_url=pay_result['code_url'],
        status=PaymentStatus.PENDING
    )
    db.add(order)
    db.commit()

    return order
```

### 支付回调的核心逻辑

```python
# app/api/api_v1/endpoints/payment.py

@router.post("/notify")
async def payment_notify(request: Request, db: Session = Depends(get_db)):
    # 1. 获取原始数据
    body = await request.body()

    # 2. 验证签名
    if not wechat_pay_service.verify_notify(body):
        return {"return_code": "FAIL"}

    # 3. 解析数据
    data = parse_xml(body)
    out_trade_no = data['out_trade_no']

    # 4. 更新订单状态
    order = db.query(PaymentOrder).filter(
        PaymentOrder.out_trade_no == out_trade_no
    ).first()
    order.status = PaymentStatus.PAID
    order.transaction_id = data['transaction_id']
    order.paid_at = datetime.now()

    # 5. 激活用户权限
    await user_membership_service.activate_package_for_user(
        db, order.user_id, order.id
    )

    db.commit()
    return {"return_code": "SUCCESS"}
```

---

## ✅ 接下来做什么

1. ✅ 启动开发服务器
2. ✅ 运行测试脚本，完成完整支付流程
3. ✅ 阅读 `LOCAL_DEVELOPMENT.md` 深入了解
4. ✅ 阅读 `PAYMENT_API.md` 了解所有 API 接口
5. ✅ 修改代码，本地测试
6. ✅ 确认无误后，提交到版本控制
7. ✅ 通过 `./deploy.sh` 部署到服务器

---

## 📞 快速命令参考

```bash
# 启动服务器
cd /Users/peakom/work/stock-analysis-system/backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 3007

# 查看 API 文档
http://localhost:3007/docs

# 运行测试
python3 test_payment_quick.py

# 查看数据库
mysql -u root stock_analysis_dev

# 查看订单
mysql -u root stock_analysis_dev -e "SELECT * FROM payment_orders;"

# 清空测试数据
mysql -u root stock_analysis_dev -e "TRUNCATE TABLE payment_orders; TRUNCATE TABLE payment_notifications;"
```

---

**祝您开发愉快！** 🚀

如有问题，详见 `LOCAL_DEVELOPMENT.md` 或 `PAYMENT_API.md`。
