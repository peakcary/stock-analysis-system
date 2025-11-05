"""
核心种子数据脚本
 - 创建默认管理员（如不存在）
 - 创建默认支付套餐（如不存在）

运行方法：
  cd backend && source venv/bin/activate && python scripts/seed_core.py

注意：请确保 DATABASE_URL 已正确配置（backend/.env）
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.admin_user import AdminUser
from app.core.security import get_password_hash
from app.models.payment import PaymentPackage


def ensure_admin(db: Session, username: str = "admin", password: str = "admin123", email: str = "admin@example.com") -> None:
    admin = db.execute(select(AdminUser).where(AdminUser.username == username)).scalar_one_or_none()
    if admin:
        print(f"✅ 管理员已存在: {username}")
        return
    admin = AdminUser(
        username=username,
        email=email,
        password_hash=get_password_hash(password),
        full_name="System Admin",
        is_active=True,
        is_superuser=True,
        last_login=None,
        created_at=datetime.now(),
    )
    db.add(admin)
    db.commit()
    print(f"✅ 创建管理员成功: {username} / {password}")


DEFAULT_PACKAGES = [
    {
        "package_type": "queries_10",
        "name": "查询包10次",
        "price": 9.90,
        "queries_count": 10,
        "validity_days": 365,
        "membership_type": "free",
        "description": "一次性增加10次查询次数",
        "sort_order": 10,
    },
    {
        "package_type": "pro_monthly",
        "name": "专业版(月度)",
        "price": 29.90,
        "queries_count": 0,
        "validity_days": 30,
        "membership_type": "pro",
        "description": "开通专业版会员30天",
        "sort_order": 20,
    },
    {
        "package_type": "premium_monthly",
        "name": "旗舰版(月度)",
        "price": 59.90,
        "queries_count": 0,
        "validity_days": 30,
        "membership_type": "premium",
        "description": "开通旗舰版会员30天",
        "sort_order": 30,
    },
]


def ensure_payment_packages(db: Session) -> None:
    created = 0
    for pkg in DEFAULT_PACKAGES:
        existing = db.execute(
            select(PaymentPackage).where(PaymentPackage.package_type == pkg["package_type"])  # type: ignore
        ).scalar_one_or_none()
        if existing:
            print(f"✅ 套餐已存在: {pkg['package_type']}")
            continue
        new_pkg = PaymentPackage(
            package_type=pkg["package_type"],
            name=pkg["name"],
            price=pkg["price"],
            queries_count=pkg["queries_count"],
            validity_days=pkg["validity_days"],
            membership_type=pkg["membership_type"],
            description=pkg.get("description"),
            is_active=True,
            sort_order=pkg["sort_order"],
        )
        db.add(new_pkg)
        created += 1
    if created:
        db.commit()
    print(f"✅ 支付套餐创建完成（新增 {created} 条，存在 {len(DEFAULT_PACKAGES) - created} 条）")


def main() -> None:
    db = SessionLocal()
    try:
        ensure_admin(db)
        ensure_payment_packages(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()

