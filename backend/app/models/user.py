"""
用户相关数据模型
"""

from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class MembershipType(enum.Enum):
    """会员类型枚举"""
    FREE = "free"
    PRO = "pro"  # 专业版
    PREMIUM = "premium"  # 旗舰版
    PAID_10 = "paid_10" 
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class QueryType(enum.Enum):
    """查询类型枚举"""
    STOCK_SEARCH = "stock_search"
    CONCEPT_SEARCH = "concept_search"
    TOP_CONCEPTS = "top_concepts"
    NEW_HIGHS = "new_highs"
    BOND_SEARCH = "bond_search"


class PaymentType(enum.Enum):
    """支付类型枚举"""
    TEN_QUERIES = "10_queries"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class PaymentStatus(enum.Enum):
    """支付状态枚举"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    username = Column(String(50), unique=True, nullable=False, index=True, comment="用户名")
    email = Column(String(100), unique=True, nullable=False, index=True, comment="邮箱")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    membership_type = Column(Enum(MembershipType), default=MembershipType.FREE, index=True, comment="会员类型")
    queries_remaining = Column(Integer, default=10, comment="剩余查询次数")
    membership_expires_at = Column(DateTime, nullable=True, comment="会员到期时间")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关联关系
    user_queries = relationship("UserQuery", back_populates="user", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")
    payment_orders = relationship("PaymentOrder", back_populates="user", cascade="all, delete-orphan")


class UserQuery(Base):
    """用户查询记录表"""
    __tablename__ = "user_queries"
    
    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="用户ID")
    query_type = Column(Enum(QueryType), nullable=False, index=True, comment="查询类型")
    query_params = Column(JSON, comment="查询参数")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    
    # 关联关系
    user = relationship("User", back_populates="user_queries")


class Payment(Base):
    """支付记录表"""
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="用户ID")
    amount = Column(DECIMAL(10, 2), nullable=False, comment="支付金额")
    payment_type = Column(Enum(PaymentType), nullable=False, comment="支付类型")
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, index=True, comment="支付状态")
    payment_method = Column(String(50), comment="支付方式")
    transaction_id = Column(String(100), index=True, comment="交易ID")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")
    
    # 关联关系
    user = relationship("User", back_populates="payments")