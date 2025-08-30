"""
支付相关数据模型 - 修复版本
Payment related models - Fixed version

彻底解决enum映射问题：
1. 使用字符串常量类替代Enum
2. 统一数据库存储格式为小写
3. 提供验证方法确保数据一致性
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, DECIMAL, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import List

from app.core.database import Base


# 使用常量类替代Enum - 彻底解决映射问题
class PaymentStatus:
    """支付状态常量"""
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    EXPIRED = "expired"
    
    @classmethod
    def all_values(cls) -> List[str]:
        return [cls.PENDING, cls.PAID, cls.FAILED, cls.CANCELLED, cls.REFUNDED, cls.EXPIRED]
    
    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls.all_values()


class PaymentMethod:
    """支付方式常量"""
    WECHAT_NATIVE = "wechat_native"
    WECHAT_H5 = "wechat_h5"
    WECHAT_MINIPROGRAM = "wechat_miniprogram"
    ALIPAY = "alipay"
    
    @classmethod
    def all_values(cls) -> List[str]:
        return [cls.WECHAT_NATIVE, cls.WECHAT_H5, cls.WECHAT_MINIPROGRAM, cls.ALIPAY]
    
    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls.all_values()


class MembershipTypeEnum:
    """会员类型常量"""
    FREE = "free"
    PRO = "pro"
    PREMIUM = "premium"
    
    @classmethod
    def all_values(cls) -> List[str]:
        return [cls.FREE, cls.PRO, cls.PREMIUM]
    
    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls.all_values()


class ActionType:
    """操作类型常量"""
    UPGRADE = "upgrade"
    RENEW = "renew"
    ADD_QUERIES = "add_queries"
    EXPIRE = "expire"
    MANUAL = "manual"
    
    @classmethod
    def all_values(cls) -> List[str]:
        return [cls.UPGRADE, cls.RENEW, cls.ADD_QUERIES, cls.EXPIRE, cls.MANUAL]
    
    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls.all_values()


class NotificationType:
    """通知类型常量"""
    PAYMENT = "payment"
    REFUND = "refund"
    
    @classmethod
    def all_values(cls) -> List[str]:
        return [cls.PAYMENT, cls.REFUND]
    
    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls.all_values()


class RefundStatus:
    """退款状态常量"""
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    CLOSED = "closed"
    
    @classmethod
    def all_values(cls) -> List[str]:
        return [cls.PROCESSING, cls.SUCCESS, cls.FAILED, cls.CLOSED]
    
    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls.all_values()


class PaymentPackage(Base):
    """支付套餐配置表"""
    __tablename__ = "payment_packages"

    id = Column(Integer, primary_key=True, index=True)
    package_type = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(50), nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)
    queries_count = Column(Integer, default=0)
    validity_days = Column(Integer, default=0)
    membership_type = Column(String(20), default="free")
    description = Column(Text)
    is_active = Column(Boolean, default=True, index=True)
    sort_order = Column(Integer, default=0, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关联关系
    payment_orders = relationship("PaymentOrder", back_populates="payment_package")


class PaymentOrder(Base):
    """支付订单表"""
    __tablename__ = "payment_orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    package_id = Column(Integer, ForeignKey("payment_packages.id", ondelete="RESTRICT"), nullable=False, index=True)
    out_trade_no = Column(String(64), unique=True, nullable=False, index=True)
    transaction_id = Column(String(64), index=True)
    package_type = Column(String(20), nullable=False, index=True)
    package_name = Column(String(50), nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    status = Column(String(20), default=PaymentStatus.PENDING, index=True)
    payment_method = Column(String(30), default=PaymentMethod.WECHAT_NATIVE)
    prepay_id = Column(String(64))
    code_url = Column(Text)
    h5_url = Column(Text)
    expire_time = Column(DateTime(timezone=True), nullable=False, index=True)
    paid_at = Column(DateTime(timezone=True), index=True)
    cancelled_at = Column(DateTime(timezone=True))
    refunded_at = Column(DateTime(timezone=True))
    refund_amount = Column(DECIMAL(10, 2), default=0)
    client_ip = Column(String(45))
    user_agent = Column(Text)
    notify_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关联关系
    user = relationship("User", back_populates="payment_orders")
    payment_package = relationship("PaymentPackage", back_populates="payment_orders")
    membership_logs = relationship("MembershipLog", back_populates="payment_order")
    refund_records = relationship("RefundRecord", back_populates="payment_order")


class PaymentNotification(Base):
    """支付通知记录表"""
    __tablename__ = "payment_notifications"

    id = Column(Integer, primary_key=True, index=True)
    out_trade_no = Column(String(64), nullable=False, index=True)
    transaction_id = Column(String(64), index=True)
    notification_type = Column(String(20), default=NotificationType.PAYMENT)
    return_code = Column(String(16))
    result_code = Column(String(16))
    raw_data = Column(Text, nullable=False)
    is_valid = Column(Boolean, default=False)
    processed = Column(Boolean, default=False, index=True)
    process_result = Column(Text)
    client_ip = Column(String(45))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    processed_at = Column(DateTime(timezone=True))

    # 关联关系暂时移除


class MembershipLog(Base):
    """用户会员变更记录表"""
    __tablename__ = "membership_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    payment_order_id = Column(Integer, ForeignKey("payment_orders.id", ondelete="SET NULL"), index=True)
    action_type = Column(String(20), nullable=False, index=True)
    old_membership_type = Column(String(20))
    new_membership_type = Column(String(20))
    old_queries_remaining = Column(Integer, default=0)
    new_queries_remaining = Column(Integer, default=0)
    queries_added = Column(Integer, default=0)
    old_expires_at = Column(DateTime(timezone=True))
    new_expires_at = Column(DateTime(timezone=True))
    days_added = Column(Integer, default=0)
    operator_id = Column(Integer)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # 关联关系
    user = relationship("User")
    payment_order = relationship("PaymentOrder", back_populates="membership_logs")


class RefundRecord(Base):
    """退款记录表"""
    __tablename__ = "refund_records"

    id = Column(Integer, primary_key=True, index=True)
    payment_order_id = Column(Integer, ForeignKey("payment_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    out_refund_no = Column(String(64), unique=True, nullable=False, index=True)
    refund_id = Column(String(64), index=True)
    refund_amount = Column(DECIMAL(10, 2), nullable=False)
    refund_reason = Column(String(255))
    refund_status = Column(String(20), default=RefundStatus.PROCESSING, index=True)
    refund_channel = Column(String(32))
    operator_id = Column(Integer)
    notify_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    completed_at = Column(DateTime(timezone=True))

    # 关联关系
    payment_order = relationship("PaymentOrder", back_populates="refund_records")