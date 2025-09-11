"""
管理员认证API端点
"""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.crud.admin_user import AdminUserCRUD
from app.core.admin_auth import (
    create_admin_access_token, 
    create_admin_refresh_token,
    verify_admin_refresh_token,
    get_current_admin_user, 
    ADMIN_ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.models.admin_user import AdminUser

router = APIRouter()


class AdminTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    admin_info: dict


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class AdminUserInfo(BaseModel):
    id: int
    username: str
    email: str
    full_name: str = None
    is_active: bool
    is_superuser: bool
    last_login: str = None


class AdminLoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login", response_model=AdminTokenResponse)
def admin_login(
    login_data: AdminLoginRequest,
    db: Session = Depends(get_db)
):
    """管理员登录"""
    admin_crud = AdminUserCRUD(db)
    admin_user = admin_crud.authenticate(login_data.username, login_data.password)
    
    if not admin_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ADMIN_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_admin_access_token(
        data={"sub": admin_user.username}, 
        expires_delta=access_token_expires
    )
    refresh_token = create_admin_refresh_token(
        data={"sub": admin_user.username}
    )
    
    return AdminTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ADMIN_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        admin_info={
            "id": admin_user.id,
            "username": admin_user.username,
            "email": admin_user.email,
            "full_name": admin_user.full_name,
            "is_superuser": admin_user.is_superuser
        }
    )


@router.get("/me", response_model=AdminUserInfo)
def get_admin_me(current_admin: AdminUser = Depends(get_current_admin_user)):
    """获取当前管理员信息"""
    return AdminUserInfo(
        id=current_admin.id,
        username=current_admin.username,
        email=current_admin.email,
        full_name=current_admin.full_name,
        is_active=current_admin.is_active,
        is_superuser=current_admin.is_superuser,
        last_login=current_admin.last_login.isoformat() if current_admin.last_login else None
    )


@router.post("/refresh", response_model=AdminTokenResponse)
def refresh_admin_token(
    refresh_request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """刷新管理员token"""
    username = verify_admin_refresh_token(refresh_request.refresh_token)
    
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    admin_crud = AdminUserCRUD(db)
    admin_user = admin_crud.get_by_username(username)
    
    if not admin_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin user not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 创建新的token对
    access_token_expires = timedelta(minutes=ADMIN_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_admin_access_token(
        data={"sub": admin_user.username}, 
        expires_delta=access_token_expires
    )
    refresh_token = create_admin_refresh_token(
        data={"sub": admin_user.username}
    )
    
    return AdminTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ADMIN_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        admin_info={
            "id": admin_user.id,
            "username": admin_user.username,
            "email": admin_user.email,
            "full_name": admin_user.full_name,
            "is_superuser": admin_user.is_superuser
        }
    )


@router.post("/logout")
def admin_logout():
    """管理员登出（客户端需要删除token）"""
    return {"message": "Successfully logged out"}