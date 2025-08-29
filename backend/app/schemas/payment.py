"""
支付相关的Pydantic模型
Payment related schemas
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field, validator, field_serializer
from enum import Enum


class PaymentStatusEnum(str, Enum):
    """支付状态枚举"""
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    EXPIRED = "expired"


class PaymentMethodEnum(str, Enum):
    """支付方式枚举"""
    WECHAT_NATIVE = "wechat_native"
    WECHAT_H5 = "wechat_h5"
    WECHAT_MINIPROGRAM = "wechat_miniprogram"
    ALIPAY = "alipay"


class MembershipTypeEnum(str, Enum):
    """会员类型枚举"""
    FREE = "FREE"
    PRO = "PRO"
    PREMIUM = "PREMIUM"


# ============ 支付套餐相关 Schema ============

class PaymentPackageBase(BaseModel):
    """支付套餐基础模型"""
    package_type: str = Field(..., description="套餐类型")
    name: str = Field(..., description="套餐名称")
    price: Decimal = Field(..., description="价格")
    queries_count: int = Field(default=0, description="查询次数")
    validity_days: int = Field(default=0, description="有效天数")
    membership_type: MembershipTypeEnum = Field(default=MembershipTypeEnum.FREE, description="会员类型")
    description: Optional[str] = Field(None, description="套餐描述")
    is_active: bool = Field(default=True, description="是否启用")
    sort_order: int = Field(default=0, description="排序")


class PaymentPackage(PaymentPackageBase):
    """支付套餐响应模型"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ 支付订单相关 Schema ============

class PaymentOrderCreate(BaseModel):
    """创建支付订单请求"""
    package_type: str = Field(..., description="套餐类型")
    payment_method: PaymentMethodEnum = Field(default=PaymentMethodEnum.WECHAT_NATIVE, description="支付方式")
    client_ip: Optional[str] = Field(None, description="客户端IP")
    user_agent: Optional[str] = Field(None, description="用户代理")


class PaymentOrderResponse(BaseModel):
    """支付订单响应"""
    id: int
    out_trade_no: str = Field(..., description="商户订单号")
    package_name: str = Field(..., description="套餐名称")
    amount: str = Field(..., description="支付金额")
    status: str
    payment_method: str
    code_url: Optional[str] = Field(None, description="扫码支付链接")
    h5_url: Optional[str] = Field(None, description="H5支付链接")
    expire_time: datetime = Field(..., description="过期时间")
    created_at: datetime

    @field_serializer('status')
    def serialize_status(self, value):
        return value.value.lower() if hasattr(value, 'value') else str(value).lower()
    
    @field_serializer('payment_method')
    def serialize_payment_method(self, value):
        return value.value.lower() if hasattr(value, 'value') else str(value).lower()

    class Config:
        from_attributes = True


# ============ 支付通知相关 Schema ============

class PaymentNotifyResponse(BaseModel):
    """支付通知响应"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


# ============ 查询参数 Schema ============

class PaymentOrderQuery(BaseModel):
    """支付订单查询参数"""
    status: Optional[PaymentStatusEnum] = None
    payment_method: Optional[PaymentMethodEnum] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)


# ============ 其他工具 Schema ============

class OrderStatusCheck(BaseModel):
    """订单状态检查"""
    out_trade_no: str
    status: str
    paid_at: Optional[datetime] = None
    transaction_id: Optional[str] = None
    
    @field_serializer('status')
    def serialize_status(self, value):
        return value.value.lower() if hasattr(value, 'value') else str(value).lower()


# ============ 兼容旧版API的Schema ============

class PaymentCreate(BaseModel):
    """创建支付请求（兼容旧版）"""
    payment_type: str = Field(..., description="支付类型")
    payment_method: str = Field(default="wechat", description="支付方式")
    
    class Config:
        from_attributes = True


class PaymentResponse(BaseModel):
    """支付响应（兼容旧版）"""
    id: int
    amount: Decimal
    payment_type: str
    payment_status: str
    payment_method: Optional[str] = None
    transaction_id: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True