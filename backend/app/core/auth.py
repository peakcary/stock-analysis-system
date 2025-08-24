"""
认证相关依赖和中间件
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.schemas.user import TokenData

# HTTP Bearer 认证方案
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 解码JWT令牌
        payload = decode_access_token(credentials.credentials)
        user_id: int = payload.get("user_id")
        username: str = payload.get("username")
        
        if user_id is None or username is None:
            raise credentials_exception
            
        token_data = TokenData(user_id=user_id, username=username)
    except Exception:
        raise credentials_exception
    
    # 从数据库获取用户
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """获取当前活跃用户"""
    # 这里可以添加用户状态检查，如是否被禁用等
    return current_user


def require_membership(membership_types: list = None):
    """要求特定会员等级的装饰器工厂"""
    def membership_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if membership_types and current_user.membership_type.value not in membership_types:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    
    return membership_checker


def require_queries_remaining(current_user: User = Depends(get_current_active_user)) -> User:
    """要求用户有剩余查询次数"""
    if current_user.queries_remaining <= 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No queries remaining. Please upgrade your membership."
        )
    return current_user


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """获取可选用户（用于支持匿名访问的接口）"""
    if not credentials:
        return None
    
    try:
        payload = decode_access_token(credentials.credentials)
        user_id: int = payload.get("user_id")
        
        if user_id is None:
            return None
            
        user = db.query(User).filter(User.id == user_id).first()
        return user
    except Exception:
        return None