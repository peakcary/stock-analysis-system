"""
支付相关API路由（重构版 - 使用数据库套餐配置）
"""

from typing import List, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User, Payment, PaymentStatus, PaymentType, MembershipType
from app.models.payment import PaymentPackage
from app.schemas.payment import PaymentCreate, PaymentResponse, PaymentPackage as PaymentPackageSchema

router = APIRouter()


@router.get("/packages", response_model=List[PaymentPackageSchema])
async def get_payment_packages(db: Session = Depends(get_db)):
    """获取所有启用的支付套餐"""
    packages = db.query(PaymentPackage).filter(
        PaymentPackage.is_active == True
    ).order_by(PaymentPackage.sort_order, PaymentPackage.id).all()
    
    return packages


@router.post("/create", response_model=PaymentResponse)
async def create_payment(
    payment_data: PaymentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建支付订单"""
    
    # 查找支付套餐 - 从数据库查询
    package = db.query(PaymentPackage).filter(
        PaymentPackage.package_type == payment_data.payment_type,
        PaymentPackage.is_active == True
    ).first()
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的支付类型或套餐已下架"
        )
    
    # 创建支付记录
    payment = Payment(
        user_id=current_user.id,
        amount=package.price,
        payment_type=payment_data.payment_type,
        payment_status=PaymentStatus.PENDING,
        payment_method=payment_data.payment_method
    )
    
    db.add(payment)
    db.commit()
    db.refresh(payment)
    
    # 这里应该调用实际的支付服务 (微信支付/支付宝等)
    # 目前模拟支付成功
    
    return PaymentResponse(
        id=payment.id,
        amount=payment.amount,
        payment_type=payment.payment_type,
        payment_status=payment.payment_status,
        payment_method=payment.payment_method,
        transaction_id=payment.transaction_id,
        created_at=payment.created_at,
        completed_at=payment.completed_at
    )


@router.post("/{payment_id}/confirm")
async def confirm_payment(
    payment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """确认支付成功（模拟支付回调）"""
    
    # 查找支付记录
    payment = db.query(Payment).filter(
        Payment.id == payment_id,
        Payment.user_id == current_user.id,
        Payment.payment_status == PaymentStatus.PENDING
    ).first()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="支付记录不存在或已处理"
        )
    
    # 从数据库查找套餐配置
    package = db.query(PaymentPackage).filter(
        PaymentPackage.package_type == payment.payment_type
    ).first()
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="套餐配置不存在"
        )
    
    # 更新支付状态
    payment.payment_status = PaymentStatus.COMPLETED
    payment.completed_at = datetime.utcnow()
    payment.transaction_id = f"TXN_{payment.id}_{int(datetime.now().timestamp())}"
    
    # 根据套餐配置更新用户会员状态
    if package.queries_count > 0 and package.validity_days == 0:
        # 查询包 - 增加查询次数
        current_user.queries_remaining += package.queries_count
    else:
        # 会员套餐 - 更新会员类型和到期时间
        # 根据套餐的会员类型更新用户会员类型
        if package.membership_type.value == "FREE":
            current_user.membership_type = MembershipType.FREE
        elif package.membership_type.value == "PRO":
            current_user.membership_type = MembershipType.PRO
        elif package.membership_type.value == "PREMIUM":
            current_user.membership_type = MembershipType.PREMIUM
        
        # 设置会员到期时间
        if package.validity_days > 0:
            current_user.membership_expires_at = datetime.utcnow() + timedelta(days=package.validity_days)
            current_user.queries_remaining = package.queries_count
    
    db.commit()
    
    return {"message": "支付确认成功", "payment_id": payment_id}


@router.get("/history", response_model=List[PaymentResponse])
async def get_payment_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户支付历史"""
    
    payments = db.query(Payment).filter(
        Payment.user_id == current_user.id
    ).order_by(Payment.created_at.desc()).all()
    
    return [
        PaymentResponse(
            id=payment.id,
            amount=payment.amount,
            payment_type=payment.payment_type,
            payment_status=payment.payment_status,
            payment_method=payment.payment_method,
            transaction_id=payment.transaction_id,
            created_at=payment.created_at,
            completed_at=payment.completed_at
        )
        for payment in payments
    ]


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment_detail(
    payment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取支付详情"""
    
    payment = db.query(Payment).filter(
        Payment.id == payment_id,
        Payment.user_id == current_user.id
    ).first()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="支付记录不存在"
        )
    
    return PaymentResponse(
        id=payment.id,
        amount=payment.amount,
        payment_type=payment.payment_type,
        payment_status=payment.payment_status,
        payment_method=payment.payment_method,
        transaction_id=payment.transaction_id,
        created_at=payment.created_at,
        completed_at=payment.completed_at
    )