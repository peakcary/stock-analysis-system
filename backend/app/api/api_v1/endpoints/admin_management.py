"""
管理员账户管理API端点
管理后台管理员自己的账户系统
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel

from app.core.database import get_db
from app.core.admin_auth import get_current_admin_user
from app.crud.admin_user import AdminUserCRUD
from app.models.admin_user import AdminUser

router = APIRouter()


class AdminUserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str = None
    role: str = "admin"  # 默认角色
    is_active: bool
    is_superuser: bool
    last_login: Optional[str] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True
        
    @classmethod
    def from_admin_user(cls, admin_user: AdminUser):
        """从AdminUser对象创建响应数据"""
        # 由于数据库中role字段被注释，根据is_superuser判断角色
        role = "super_admin" if admin_user.is_superuser else "admin"
        
        return cls(
            id=admin_user.id,
            username=admin_user.username,
            email=admin_user.email,
            full_name=admin_user.full_name,
            role=role,
            is_active=admin_user.is_active,
            is_superuser=admin_user.is_superuser,
            last_login=admin_user.last_login.isoformat() if admin_user.last_login else None,
            created_at=admin_user.created_at.isoformat(),
            updated_at=admin_user.updated_at.isoformat()
        )


class AdminUserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: str = None
    role: str = "admin"  # 暂时使用字符串，默认为普通管理员
    is_active: bool = True


class AdminUserUpdate(BaseModel):
    email: str = None
    full_name: str = None
    role: str = None  # 暂时使用字符串
    is_active: bool = None
    password: str = None


class AdminListResponse(BaseModel):
    admins: List[AdminUserResponse]
    total: int
    skip: int
    limit: int


def check_super_admin(current_admin: AdminUser = Depends(get_current_admin_user)) -> AdminUser:
    """检查当前用户是否为超级管理员"""
    if not current_admin.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要超级管理员权限"
        )
    return current_admin


@router.get("/admins", response_model=AdminListResponse)
async def get_all_admins(
    skip: int = Query(0, description="跳过的记录数"),
    limit: int = Query(50, description="返回的记录数"),
    search: Optional[str] = Query(None, description="搜索用户名或邮箱"),
    role: Optional[str] = Query(None, description="角色筛选"),
    current_admin: AdminUser = Depends(check_super_admin),
    db: Session = Depends(get_db)
):
    """获取所有管理员列表（超级管理员专用）"""
    admin_crud = AdminUserCRUD(db)
    
    # 获取管理员列表
    admins = admin_crud.get_all_admins(
        skip=skip,
        limit=limit,
        search=search,
        role=role
    )
    
    total = admin_crud.count_admins(search=search, role=role)
    
    # 转换为响应格式
    admin_responses = [AdminUserResponse.from_admin_user(admin) for admin in admins]
    
    return {
        "admins": admin_responses,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/admins/{admin_id}", response_model=AdminUserResponse)
async def get_admin_by_id(
    admin_id: int,
    current_admin: AdminUser = Depends(check_super_admin),
    db: Session = Depends(get_db)
):
    """根据ID获取管理员详细信息（超级管理员专用）"""
    admin_crud = AdminUserCRUD(db)
    admin = admin_crud.get_admin_by_id(admin_id)
    
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="管理员不存在"
        )
    
    return AdminUserResponse.from_admin_user(admin)


@router.post("/admins", response_model=AdminUserResponse)
async def create_admin(
    admin_create: AdminUserCreate,
    current_admin: AdminUser = Depends(check_super_admin),
    db: Session = Depends(get_db)
):
    """创建新管理员（超级管理员专用）"""
    try:
        admin_crud = AdminUserCRUD(db)
        admin = admin_crud.create_admin(admin_create)
        return AdminUserResponse.from_admin_user(admin)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/admins/{admin_id}", response_model=AdminUserResponse)
async def update_admin(
    admin_id: int,
    admin_update: AdminUserUpdate,
    current_admin: AdminUser = Depends(check_super_admin),
    db: Session = Depends(get_db)
):
    """更新管理员信息（超级管理员专用）"""
    try:
        admin_crud = AdminUserCRUD(db)
        
        # 防止修改自己的超级管理员权限
        if admin_id == current_admin.id and admin_update.role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能修改自己的角色"
            )
        
        admin = admin_crud.update_admin(admin_id, admin_update)
        
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="管理员不存在"
            )
        
        return AdminUserResponse.from_admin_user(admin)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/admins/{admin_id}")
async def delete_admin(
    admin_id: int,
    current_admin: AdminUser = Depends(check_super_admin),
    db: Session = Depends(get_db)
):
    """删除管理员（超级管理员专用）"""
    admin_crud = AdminUserCRUD(db)
    
    # 检查管理员是否存在
    admin = admin_crud.get_admin_by_id(admin_id)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="管理员不存在"
        )
    
    # 防止删除自己
    if admin_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己的账户"
        )
    
    success = admin_crud.delete_admin(admin_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除管理员失败"
        )
    
    return {"message": f"管理员 {admin.username} 删除成功"}


@router.post("/admins/{admin_id}/reset-password")
async def reset_admin_password(
    admin_id: int,
    new_password: str = Query(..., description="新密码"),
    current_admin: AdminUser = Depends(check_super_admin),
    db: Session = Depends(get_db)
):
    """重置管理员密码（超级管理员专用）"""
    admin_crud = AdminUserCRUD(db)
    
    # 检查管理员是否存在
    admin = admin_crud.get_admin_by_id(admin_id)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="管理员不存在"
        )
    
    # 更新密码
    admin_update = AdminUserUpdate(password=new_password)
    updated_admin = admin_crud.update_admin(admin_id, admin_update)
    
    if not updated_admin:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="密码重置失败"
        )
    
    return {
        "message": f"管理员 {admin.username} 的密码重置成功"
    }


@router.post("/admins/{admin_id}/toggle-status")
async def toggle_admin_status(
    admin_id: int,
    current_admin: AdminUser = Depends(check_super_admin),
    db: Session = Depends(get_db)
):
    """启用/禁用管理员账户（超级管理员专用）"""
    admin_crud = AdminUserCRUD(db)
    
    # 检查管理员是否存在
    admin = admin_crud.get_admin_by_id(admin_id)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="管理员不存在"
        )
    
    # 防止操作自己
    if admin_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能操作自己的账户状态"
        )
    
    # 切换状态
    admin_update = AdminUserUpdate(is_active=not admin.is_active)
    updated_admin = admin_crud.update_admin(admin_id, admin_update)
    
    status_text = "启用" if updated_admin.is_active else "禁用"
    
    return {
        "message": f"管理员 {admin.username} 已{status_text}",
        "is_active": updated_admin.is_active
    }