"""
用户相关的 Pydantic 模式
"""

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from app.models.user import MembershipType


class UserBase(BaseModel):
    """用户基础模式"""
    username: str
    email: EmailStr


class UserCreate(UserBase):
    """用户创建模式"""
    password: str


class UserUpdate(BaseModel):
    """用户更新模式"""
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None


class UserResponse(UserBase):
    """用户响应模式"""
    id: int
    membership_type: MembershipType
    queries_remaining: int
    membership_expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """用户登录模式"""
    username: str
    password: str


class Token(BaseModel):
    """JWT Token响应模式"""
    access_token: str
    token_type: str
    expires_in: int
    user: UserResponse


class TokenData(BaseModel):
    """JWT Token数据模式"""
    user_id: Optional[int] = None
    username: Optional[str] = None


class PasswordChange(BaseModel):
    """修改密码模式"""
    old_password: str
    new_password: str


class MembershipUpgrade(BaseModel):
    """会员升级模式"""
    membership_type: MembershipType
    queries_to_add: Optional[int] = None
    days_to_add: Optional[int] = None
    payment_method: Optional[str] = None


class UserListResponse(BaseModel):
    """用户列表响应模式"""
    users: list[UserResponse]
    total: int
    skip: int
    limit: int


class AdminUserStats(BaseModel):
    """用户统计信息模式"""
    total_users: int
    free_users: int
    paid_users: int
    monthly_users: int
    yearly_users: int
    total_queries_today: int
    total_payments_today: float
    new_users_today: int