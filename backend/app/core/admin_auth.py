"""
管理员认证相关的依赖项和工具函数
"""
from typing import Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.admin_user import AdminUser
from app.crud.admin_user import AdminUserCRUD
from app.core.config import settings

# JWT配置
ADMIN_SECRET_KEY = "your-admin-secret-key-here"  # 应该从环境变量读取
ADMIN_ALGORITHM = "HS256"
ADMIN_ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24小时

# HTTP Bearer scheme for admin
admin_security = HTTPBearer()


def create_admin_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建管理员访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ADMIN_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "admin"})
    encoded_jwt = jwt.encode(to_encode, ADMIN_SECRET_KEY, algorithm=ADMIN_ALGORITHM)
    return encoded_jwt


def get_current_admin_user(
    credentials: HTTPAuthorizationCredentials = Depends(admin_security),
    db: Session = Depends(get_db)
) -> AdminUser:
    """获取当前管理员用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate admin credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, ADMIN_SECRET_KEY, algorithms=[ADMIN_ALGORITHM])
        username: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if username is None or token_type != "admin":
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    admin_crud = AdminUserCRUD(db)
    admin_user = admin_crud.get_by_username(username)
    
    if admin_user is None:
        raise credentials_exception
    
    if not admin_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin account is deactivated"
        )
    
    return admin_user


def get_optional_admin_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(admin_security),
    db: Session = Depends(get_db)
) -> Optional[AdminUser]:
    """获取可选的管理员用户（用于可选认证的端点）"""
    if not credentials:
        return None
    
    try:
        return get_current_admin_user(credentials, db)
    except HTTPException:
        return None


def require_superuser(admin_user: AdminUser = Depends(get_current_admin_user)) -> AdminUser:
    """要求超级管理员权限"""
    if not admin_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser access required"
        )
    return admin_user