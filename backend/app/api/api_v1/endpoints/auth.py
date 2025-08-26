"""
认证相关API端点
"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.core.security import create_access_token
from app.core.auth import get_current_user, get_current_active_user
from app.crud.user import UserCRUD
from app.schemas.user import (
    UserCreate, UserResponse, UserLogin, Token, 
    PasswordChange, UserUpdate
)

router = APIRouter()


@router.post("/register", response_model=UserResponse)
async def register_user(user_create: UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
    try:
        user_crud = UserCRUD(db)
        user = user_crud.create_user(user_create)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=Token)
async def login_user(user_login: UserLogin, db: Session = Depends(get_db)):
    """用户登录"""
    user_crud = UserCRUD(db)
    user = user_crud.authenticate_user(user_login.username, user_login.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 检查会员是否过期
    if user_crud.check_membership_expired(user.id):
        pass  # 会员过期处理逻辑暂时跳过
        # user = user_crud.upgrade_membership(user.id, user.membership_type.FREE, 10, 0)
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"user_id": user.id, "username": user.username},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": user
    }


@router.post("/login/oauth", response_model=Token)
async def login_oauth(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """OAuth2兼容的登录接口"""
    user_crud = UserCRUD(db)
    user = user_crud.authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 检查会员是否过期
    if user_crud.check_membership_expired(user.id):
        pass  # 会员过期处理逻辑暂时跳过
        # user = user_crud.upgrade_membership(user.id, user.membership_type.FREE, 10, 0)
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"user_id": user.id, "username": user.username},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": user
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user = Depends(get_current_active_user)):
    """获取当前用户信息"""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新当前用户信息"""
    try:
        user_crud = UserCRUD(db)
        updated_user = user_crud.update_user(current_user.id, user_update)
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        return updated_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/change-password")
async def change_password(
    password_change: PasswordChange,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """修改密码"""
    user_crud = UserCRUD(db)
    
    # 验证旧密码
    if not user_crud.authenticate_user(current_user.username, password_change.old_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前密码错误"
        )
    
    # 更新密码
    user_update = UserUpdate(password=password_change.new_password)
    updated_user = user_crud.update_user(current_user.id, user_update)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="密码更新失败"
        )
    
    return {"message": "密码修改成功"}


@router.post("/logout")
async def logout_user(current_user = Depends(get_current_active_user)):
    """用户退出登录"""
    # 在实际应用中，可以将token加入黑名单
    # 这里只是简单返回成功消息
    return {"message": "退出登录成功"}


@router.get("/queries")
async def get_user_queries(
    skip: int = 0,
    limit: int = 50,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取用户查询记录"""
    user_crud = UserCRUD(db)
    queries = user_crud.get_user_queries(current_user.id, skip, limit)
    
    return {
        "queries": queries,
        "total": len(queries),
        "user_id": current_user.id
    }


@router.get("/payments")
async def get_user_payments(
    skip: int = 0,
    limit: int = 50,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取用户支付记录"""
    user_crud = UserCRUD(db)
    payments = user_crud.get_user_payments(current_user.id, skip, limit)
    
    return {
        "payments": payments,
        "total": len(payments),
        "user_id": current_user.id
    }