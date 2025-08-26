"""
管理员套餐配置API端点
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from decimal import Decimal

from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.models.user import User
from app.models.payment import PaymentPackage, MembershipTypeEnum
from app.schemas.payment import PaymentPackageBase, PaymentPackage as PaymentPackageSchema

router = APIRouter()


def check_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    """检查当前用户是否为管理员"""
    if current_user.username != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要管理员权限"
        )
    return current_user


# ============ 套餐管理相关 Schema ============

class PaymentPackageCreate(PaymentPackageBase):
    """创建套餐请求"""
    pass


class PaymentPackageUpdate(PaymentPackageBase):
    """更新套餐请求"""
    package_type: Optional[str] = None
    name: Optional[str] = None
    price: Optional[Decimal] = None
    queries_count: Optional[int] = None
    validity_days: Optional[int] = None
    membership_type: Optional[MembershipTypeEnum] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


# ============ 套餐管理API ============

@router.get("/packages", response_model=List[PaymentPackageSchema])
async def get_all_packages(
    skip: int = Query(0, description="跳过的记录数"),
    limit: int = Query(100, description="返回的记录数"),
    is_active: Optional[bool] = Query(None, description="是否启用筛选"),
    admin_user: User = Depends(check_admin_user),
    db: Session = Depends(get_db)
):
    """获取所有套餐列表（管理员专用）"""
    query = db.query(PaymentPackage)
    
    # 筛选条件
    if is_active is not None:
        query = query.filter(PaymentPackage.is_active == is_active)
    
    # 排序和分页
    packages = query.order_by(PaymentPackage.sort_order, PaymentPackage.id).offset(skip).limit(limit).all()
    
    return packages


@router.get("/packages/{package_id}", response_model=PaymentPackageSchema)
async def get_package_by_id(
    package_id: int,
    admin_user: User = Depends(check_admin_user),
    db: Session = Depends(get_db)
):
    """根据ID获取套餐详细信息（管理员专用）"""
    package = db.query(PaymentPackage).filter(PaymentPackage.id == package_id).first()
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="套餐不存在"
        )
    
    return package


@router.post("/packages", response_model=PaymentPackageSchema)
async def create_package(
    package_create: PaymentPackageCreate,
    admin_user: User = Depends(check_admin_user),
    db: Session = Depends(get_db)
):
    """创建新套餐（管理员专用）"""
    
    # 检查套餐类型是否已存在
    existing_package = db.query(PaymentPackage).filter(
        PaymentPackage.package_type == package_create.package_type
    ).first()
    
    if existing_package:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"套餐类型 '{package_create.package_type}' 已存在"
        )
    
    # 创建新套餐
    package = PaymentPackage(
        package_type=package_create.package_type,
        name=package_create.name,
        price=package_create.price,
        queries_count=package_create.queries_count,
        validity_days=package_create.validity_days,
        membership_type=package_create.membership_type,
        description=package_create.description,
        is_active=package_create.is_active,
        sort_order=package_create.sort_order
    )
    
    db.add(package)
    db.commit()
    db.refresh(package)
    
    return package


@router.put("/packages/{package_id}", response_model=PaymentPackageSchema)
async def update_package(
    package_id: int,
    package_update: PaymentPackageUpdate,
    admin_user: User = Depends(check_admin_user),
    db: Session = Depends(get_db)
):
    """更新套餐信息（管理员专用）"""
    
    # 查找套餐
    package = db.query(PaymentPackage).filter(PaymentPackage.id == package_id).first()
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="套餐不存在"
        )
    
    # 如果要修改套餐类型，检查是否冲突
    if package_update.package_type and package_update.package_type != package.package_type:
        existing_package = db.query(PaymentPackage).filter(
            PaymentPackage.package_type == package_update.package_type,
            PaymentPackage.id != package_id
        ).first()
        
        if existing_package:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"套餐类型 '{package_update.package_type}' 已存在"
            )
    
    # 更新字段
    update_data = package_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(package, field, value)
    
    db.commit()
    db.refresh(package)
    
    return package


@router.delete("/packages/{package_id}")
async def delete_package(
    package_id: int,
    admin_user: User = Depends(check_admin_user),
    db: Session = Depends(get_db)
):
    """删除套餐（管理员专用）"""
    
    # 查找套餐
    package = db.query(PaymentPackage).filter(PaymentPackage.id == package_id).first()
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="套餐不存在"
        )
    
    # 检查是否有关联的订单（可选，看业务需求）
    # from app.models.payment import PaymentOrder
    # existing_orders = db.query(PaymentOrder).filter(
    #     PaymentOrder.package_type == package.package_type
    # ).first()
    # 
    # if existing_orders:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="该套餐已有订单记录，不能删除"
    #     )
    
    db.delete(package)
    db.commit()
    
    return {"message": f"套餐 '{package.name}' 删除成功"}


@router.post("/packages/{package_id}/toggle-status")
async def toggle_package_status(
    package_id: int,
    admin_user: User = Depends(check_admin_user),
    db: Session = Depends(get_db)
):
    """切换套餐启用/禁用状态（管理员专用）"""
    
    # 查找套餐
    package = db.query(PaymentPackage).filter(PaymentPackage.id == package_id).first()
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="套餐不存在"
        )
    
    # 切换状态
    package.is_active = not package.is_active
    db.commit()
    db.refresh(package)
    
    status_text = "启用" if package.is_active else "禁用"
    
    return {
        "message": f"套餐 '{package.name}' 已{status_text}",
        "package_id": package_id,
        "is_active": package.is_active
    }


@router.post("/packages/batch-update-order")
async def batch_update_package_order(
    package_orders: List[dict],  # [{"id": 1, "sort_order": 1}, ...]
    admin_user: User = Depends(check_admin_user),
    db: Session = Depends(get_db)
):
    """批量更新套餐排序（管理员专用）"""
    
    try:
        for item in package_orders:
            package_id = item.get("id")
            sort_order = item.get("sort_order")
            
            if package_id and sort_order is not None:
                package = db.query(PaymentPackage).filter(PaymentPackage.id == package_id).first()
                if package:
                    package.sort_order = sort_order
        
        db.commit()
        
        return {
            "message": "套餐排序更新成功",
            "updated_count": len(package_orders)
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量更新失败: {str(e)}"
        )


@router.get("/packages/stats")
async def get_package_stats(
    admin_user: User = Depends(check_admin_user),
    db: Session = Depends(get_db)
):
    """获取套餐统计信息（管理员专用）"""
    
    # 基础统计
    total_packages = db.query(PaymentPackage).count()
    active_packages = db.query(PaymentPackage).filter(PaymentPackage.is_active == True).count()
    inactive_packages = total_packages - active_packages
    
    # 按会员类型统计
    from sqlalchemy import func
    membership_stats = db.query(
        PaymentPackage.membership_type,
        func.count(PaymentPackage.id).label('count')
    ).group_by(PaymentPackage.membership_type).all()
    
    return {
        "total_packages": total_packages,
        "active_packages": active_packages,
        "inactive_packages": inactive_packages,
        "membership_distribution": [
            {"membership_type": stat.membership_type, "count": stat.count}
            for stat in membership_stats
        ]
    }