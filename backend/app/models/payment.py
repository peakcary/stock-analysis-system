"""
支付相关数据模型
Payment related models
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Enum, DECIMAL, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from app.core.database import Base


class PaymentStatus(str, enum.Enum):
    """支付状态枚举"""
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    EXPIRED = "expired"


class PaymentMethod(str, enum.Enum):
    """支付方式枚举"""
    WECHAT_NATIVE = "wechat_native"
    WECHAT_H5 = "wechat_h5"
    WECHAT_MINIPROGRAM = "wechat_miniprogram"
    ALIPAY = "alipay"


class MembershipTypeEnum(str, enum.Enum):
    """会员类型枚举"""
    FREE = "FREE"
    PRO = "PRO"
    PREMIUM = "PREMIUM"


class ActionType(str, enum.Enum):
    """操作类型枚举"""
    UPGRADE = "upgrade"
    RENEW = "renew"
    ADD_QUERIES = "add_queries"
    EXPIRE = "expire"
    MANUAL = "manual"


class NotificationType(str, enum.Enum):
    """通知类型枚举"""
    PAYMENT = "payment"
    REFUND = "refund"


class RefundStatus(str, enum.Enum):
    """退款状态枚举"""
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    CLOSED = "closed"


class PaymentPackage(Base):
    """支付套餐配置表"""
    __tablename__ = "payment_packages"

    id = Column(Integer, primary_key=True, index=True)
    package_type = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(50), nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)
    queries_count = Column(Integer, default=0)
    validity_days = Column(Integer, default=0)
    membership_type = Column(Enum(MembershipTypeEnum), default=MembershipTypeEnum.FREE)
    description = Column(Text)
    is_active = Column(Boolean, default=True, index=True)
    sort_order = Column(Integer, default=0, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关联关系暂时移除，避免配置复杂性


class PaymentOrder(Base):
    """支付订单表"""
    __tablename__ = "payment_orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    out_trade_no = Column(String(64), unique=True, nullable=False, index=True)
    transaction_id = Column(String(64), index=True)
    package_type = Column(String(20), nullable=False, index=True)
    package_name = Column(String(50), nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, index=True)
    payment_method = Column(Enum(PaymentMethod), default=PaymentMethod.WECHAT_NATIVE)
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
    membership_logs = relationship("MembershipLog", back_populates="payment_order")
    refund_records = relationship("RefundRecord", back_populates="payment_order")


class PaymentNotification(Base):
    """支付通知记录表"""
    __tablename__ = "payment_notifications"

    id = Column(Integer, primary_key=True, index=True)
    out_trade_no = Column(String(64), nullable=False, index=True)
    transaction_id = Column(String(64), index=True)
    notification_type = Column(Enum(NotificationType), default=NotificationType.PAYMENT)
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
    action_type = Column(Enum(ActionType), nullable=False, index=True)
    old_membership_type = Column(Enum(MembershipTypeEnum))
    new_membership_type = Column(Enum(MembershipTypeEnum))
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
    refund_status = Column(Enum(RefundStatus), default=RefundStatus.PROCESSING, index=True)
    refund_channel = Column(String(32))
    operator_id = Column(Integer)
    notify_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    completed_at = Column(DateTime(timezone=True))

    # 关联关系
    payment_order = relationship("PaymentOrder", back_populates="refund_records")