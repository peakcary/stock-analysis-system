"""
模拟支付API
Mock Payment API for Development and Testing
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.core.logging import logger
from app.core.config import settings
from app.models.user import User
from app.models.payment import PaymentOrder, PaymentStatus
from app.services.wechat_pay import wechat_pay_service
from app.services.user_membership import user_membership_service

router = APIRouter()


@router.post("/simulate-payment/{out_trade_no}")
async def simulate_payment_success(
    out_trade_no: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    模拟支付成功（仅在mock模式下可用）
    Simulate payment success (only available in mock mode)
    """
    if not settings.PAYMENT_MOCK_MODE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="模拟支付功能仅在mock模式下可用"
        )
    
    try:
        # 查找支付订单
        payment_order = db.query(PaymentOrder).filter(
            PaymentOrder.out_trade_no == out_trade_no
        ).first()
        
        if not payment_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="支付订单不存在"
            )
        
        # 检查订单所有权
        if payment_order.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权操作此订单"
            )
        
        # 检查订单状态
        if payment_order.status != PaymentStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"订单状态错误，当前状态: {payment_order.status.value}"
            )
        
        # 调用微信支付服务模拟支付成功
        mock_result = await wechat_pay_service.mock_payment_success(
            out_trade_no, 
            int(payment_order.amount * 100)  # 转换为分
        )
        
        if not mock_result['success']:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"模拟支付失败: {mock_result['message']}"
            )
        
        # 更新订单状态
        from datetime import datetime
        payment_order.status = PaymentStatus.PAID
        payment_order.paid_at = datetime.now()
        payment_order.transaction_id = mock_result['data']['transaction_id']
        
        # 激活用户套餐权限
        activation_result = await user_membership_service.activate_package_for_user(
            db, current_user.id, payment_order.id
        )
        
        if not activation_result['success']:
            logger.warning(f"Package activation failed for order {payment_order.id}: {activation_result['message']}")
        
        db.commit()
        
        logger.info(f"[MOCK] Payment simulated successfully for order: {out_trade_no}")
        
        return {
            "status": "success",
            "message": "模拟支付成功",
            "data": {
                "out_trade_no": out_trade_no,
                "transaction_id": mock_result['data']['transaction_id'],
                "amount": payment_order.amount,
                "package_name": payment_order.payment_package.name,
                "membership_activated": activation_result['success'],
                "paid_at": payment_order.paid_at.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Simulate payment error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"模拟支付失败: {e}"
        )


@router.get("/payment-page/{out_trade_no}")
async def mock_payment_page(
    out_trade_no: str,
    db: Session = Depends(get_db)
):
    """
    模拟支付页面（返回支付信息供前端展示）
    Mock payment page (returns payment info for frontend display)
    """
    if not settings.PAYMENT_MOCK_MODE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="模拟支付功能仅在mock模式下可用"
        )
    
    try:
        # 查找支付订单
        payment_order = db.query(PaymentOrder).filter(
            PaymentOrder.out_trade_no == out_trade_no
        ).first()
        
        if not payment_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="支付订单不存在"
            )
        
        return {
            "status": "success",
            "data": {
                "order_info": {
                    "out_trade_no": out_trade_no,
                    "package_name": payment_order.payment_package.name,
                    "amount": payment_order.amount,
                    "status": payment_order.status.value.lower(),
                    "created_at": payment_order.created_at.isoformat(),
                    "expire_time": payment_order.expire_time.isoformat() if payment_order.expire_time else None
                },
                "payment_info": {
                    "mock_mode": True,
                    "payment_method": payment_order.payment_method.value.lower(),
                    "payment_url": f"{settings.BASE_URL}/api/v1/mock/simulate-payment/{out_trade_no}",
                    "instructions": {
                        "zh": "这是模拟支付环境。点击下方按钮可以模拟支付成功。",
                        "en": "This is a mock payment environment. Click the button below to simulate successful payment."
                    }
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Mock payment page error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取支付页面失败: {e}"
        )


@router.get("/payment-status/{out_trade_no}")
async def check_mock_payment_status(
    out_trade_no: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    检查模拟支付状态
    Check mock payment status
    """
    try:
        # 查找支付订单
        payment_order = db.query(PaymentOrder).filter(
            PaymentOrder.out_trade_no == out_trade_no
        ).first()
        
        if not payment_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="支付订单不存在"
            )
        
        # 检查订单所有权
        if payment_order.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权查看此订单"
            )
        
        # 获取用户会员状态
        membership_status = await user_membership_service.get_user_membership_status(
            db, current_user.id
        )
        
        return {
            "status": "success",
            "data": {
                "order_status": {
                    "out_trade_no": out_trade_no,
                    "status": payment_order.status.value.lower(),
                    "amount": payment_order.amount,
                    "package_name": payment_order.payment_package.name,
                    "created_at": payment_order.created_at.isoformat(),
                    "paid_at": payment_order.paid_at.isoformat() if payment_order.paid_at else None,
                    "transaction_id": payment_order.transaction_id
                },
                "membership_status": membership_status if 'error' not in membership_status else None,
                "mock_mode": settings.PAYMENT_MOCK_MODE
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Check payment status error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询支付状态失败: {e}"
        )


@router.get("/user-membership")
async def get_user_membership_info(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取用户会员信息
    Get user membership information
    """
    try:
        # 获取用户会员状态
        membership_status = await user_membership_service.get_user_membership_status(
            db, current_user.id
        )
        
        # 获取用户购买历史
        purchase_history = await user_membership_service.get_user_purchase_history(
            db, current_user.id
        )
        
        return {
            "status": "success",
            "data": {
                "membership_status": membership_status,
                "purchase_history": purchase_history,
                "mock_mode": settings.PAYMENT_MOCK_MODE
            }
        }
        
    except Exception as e:
        logger.error(f"Get user membership info error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户会员信息失败: {e}"
        )


@router.post("/test-feature-access")
async def test_feature_access(
    feature_name: str = Query(..., description="功能名称"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    测试功能访问权限
    Test feature access permission
    """
    try:
        has_access = await user_membership_service.check_feature_access(
            db, current_user.id, feature_name
        )
        
        return {
            "status": "success",
            "data": {
                "user_id": current_user.id,
                "feature_name": feature_name,
                "has_access": has_access,
                "message": f"用户{'有' if has_access else '无'}访问 {feature_name} 功能的权限"
            }
        }
        
    except Exception as e:
        logger.error(f"Test feature access error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"测试功能权限失败: {e}"
        )