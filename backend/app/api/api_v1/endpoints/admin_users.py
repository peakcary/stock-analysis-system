"""
管理员用户管理API端点
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.crud.user import UserCRUD
from app.schemas.user import (
    UserResponse, UserCreate, UserUpdate, UserListResponse,
    MembershipUpgrade, AdminUserStats
)
from app.models.user import MembershipType, User

router = APIRouter()


def check_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    """检查当前用户是否为管理员"""
    # 这里可以根据实际需求设置管理员检查逻辑
    # 例如检查用户角色、特定用户名等
    if current_user.username != "admin":  # 简单的管理员检查
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要管理员权限"
        )
    return current_user


@router.get("/users", response_model=UserListResponse)
async def get_all_users(
    skip: int = Query(0, description="跳过的记录数"),
    limit: int = Query(50, description="返回的记录数"),
    search: Optional[str] = Query(None, description="搜索用户名或邮箱"),
    membership_type: Optional[str] = Query(None, description="会员类型筛选"),
    admin_user: User = Depends(check_admin_user),
    db: Session = Depends(get_db)
):
    """获取所有用户列表（管理员专用）"""
    user_crud = UserCRUD(db)
    
    # 获取用户列表
    users, total = user_crud.get_users_with_filters(
        skip=skip,
        limit=limit,
        search=search,
        membership_type=membership_type
    )
    
    return {
        "users": users,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: int,
    admin_user: User = Depends(check_admin_user),
    db: Session = Depends(get_db)
):
    """根据ID获取用户详细信息（管理员专用）"""
    user_crud = UserCRUD(db)
    user = user_crud.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return user


@router.post("/users", response_model=UserResponse)
async def create_user_by_admin(
    user_create: UserCreate,
    admin_user: User = Depends(check_admin_user),
    db: Session = Depends(get_db)
):
    """管理员创建新用户"""
    try:
        user_crud = UserCRUD(db)
        user = user_crud.create_user(user_create)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user_by_admin(
    user_id: int,
    user_update: UserUpdate,
    admin_user: User = Depends(check_admin_user),
    db: Session = Depends(get_db)
):
    """管理员更新用户信息"""
    try:
        user_crud = UserCRUD(db)
        user = user_crud.update_user(user_id, user_update)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/users/{user_id}")
async def delete_user_by_admin(
    user_id: int,
    admin_user: User = Depends(check_admin_user),
    db: Session = Depends(get_db)
):
    """管理员删除用户"""
    user_crud = UserCRUD(db)
    
    # 检查用户是否存在
    user = user_crud.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 防止删除管理员自己
    if user_id == admin_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己的账户"
        )
    
    success = user_crud.delete_user(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除用户失败"
        )
    
    return {"message": f"用户 {user.username} 删除成功"}


@router.post("/users/{user_id}/membership")
async def upgrade_user_membership(
    user_id: int,
    membership_upgrade: MembershipUpgrade,
    admin_user: User = Depends(check_admin_user),
    db: Session = Depends(get_db)
):
    """管理员修改用户会员等级"""
    user_crud = UserCRUD(db)
    
    # 检查用户是否存在
    user = user_crud.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    try:
        updated_user = user_crud.upgrade_membership(
            user_id=user_id,
            membership_type=membership_upgrade.membership_type,
            queries_to_add=membership_upgrade.queries_to_add or 0,
            days_to_add=membership_upgrade.days_to_add or 0
        )
        
        return {
            "message": "会员等级更新成功",
            "user": updated_user
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/users/{user_id}/queries")
async def get_user_queries_by_admin(
    user_id: int,
    skip: int = Query(0, description="跳过的记录数"),
    limit: int = Query(50, description="返回的记录数"),
    admin_user: User = Depends(check_admin_user),
    db: Session = Depends(get_db)
):
    """管理员查看用户查询记录"""
    user_crud = UserCRUD(db)
    
    # 检查用户是否存在
    user = user_crud.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    queries = user_crud.get_user_queries(user_id, skip, limit)
    
    return {
        "user_id": user_id,
        "username": user.username,
        "queries": queries,
        "total": len(queries),
        "skip": skip,
        "limit": limit
    }


@router.get("/users/{user_id}/payments")
async def get_user_payments_by_admin(
    user_id: int,
    skip: int = Query(0, description="跳过的记录数"),
    limit: int = Query(50, description="返回的记录数"),
    admin_user: User = Depends(check_admin_user),
    db: Session = Depends(get_db)
):
    """管理员查看用户支付记录"""
    user_crud = UserCRUD(db)
    
    # 检查用户是否存在
    user = user_crud.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    payments = user_crud.get_user_payments(user_id, skip, limit)
    
    return {
        "user_id": user_id,
        "username": user.username,
        "payments": payments,
        "total": len(payments),
        "skip": skip,
        "limit": limit
    }


@router.get("/stats", response_model=AdminUserStats)
async def get_user_stats(
    admin_user: User = Depends(check_admin_user),
    db: Session = Depends(get_db)
):
    """获取用户统计信息（管理员专用）"""
    user_crud = UserCRUD(db)
    stats = user_crud.get_user_stats()
    
    return stats


@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    new_password: str = Query(..., description="新密码"),
    admin_user: User = Depends(check_admin_user),
    db: Session = Depends(get_db)
):
    """管理员重置用户密码"""
    user_crud = UserCRUD(db)
    
    # 检查用户是否存在
    user = user_crud.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 更新密码
    user_update = UserUpdate(password=new_password)
    updated_user = user_crud.update_user(user_id, user_update)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="密码重置失败"
        )
    
    return {
        "message": f"用户 {user.username} 的密码重置成功"
    }


@router.post("/users/{user_id}/toggle-status")
async def toggle_user_status(
    user_id: int,
    admin_user: User = Depends(check_admin_user),
    db: Session = Depends(get_db)
):
    """管理员启用/禁用用户（如果有相关字段的话）"""
    user_crud = UserCRUD(db)
    
    # 检查用户是否存在
    user = user_crud.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 防止操作管理员自己
    if user_id == admin_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能操作自己的账户状态"
        )
    
    return {
        "message": f"用户 {user.username} 状态操作成功",
        "user_id": user_id
    }