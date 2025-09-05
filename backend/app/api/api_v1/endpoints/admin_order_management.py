"""
管理员订单管理API
Admin Order Management API
"""

from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text, desc

from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.core.logging import logger
from app.models.user import User
from app.models.payment import PaymentOrder, PaymentPackage, PaymentStatus, RefundRecord
from app.services.user_membership import user_membership_service
from app.services.wechat_pay import wechat_pay_service

router = APIRouter()


def get_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    """验证管理员权限"""
    if current_user.username != 'admin':  # 简单的管理员验证，可以扩展为角色系统
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


@router.get("/orders")
async def get_all_orders(
    page: int = Query(default=1, ge=1, description="页码"),
    size: int = Query(default=20, ge=1, le=100, description="每页数量"),
    order_status: Optional[str] = Query(default=None, description="订单状态"),
    start_date: Optional[str] = Query(default=None, description="开始日期(YYYY-MM-DD)"),
    end_date: Optional[str] = Query(default=None, description="结束日期(YYYY-MM-DD)"),
    user_id: Optional[int] = Query(default=None, description="用户ID"),
    package_type: Optional[str] = Query(default=None, description="套餐类型"),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """获取所有订单列表（管理员）"""
    try:
        # 构建查询
        query = db.query(PaymentOrder).join(PaymentPackage).join(User)
        
        # 状态过滤
        if order_status:
            status_value = order_status.lower()
            if PaymentStatus.is_valid(status_value):
                query = query.filter(PaymentOrder.status == status_value)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"无效的订单状态: {order_status}"
                )
        
        # 日期过滤
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                query = query.filter(PaymentOrder.created_at >= start_dt)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="开始日期格式错误，请使用 YYYY-MM-DD"
                )
        
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
                query = query.filter(PaymentOrder.created_at < end_dt)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="结束日期格式错误，请使用 YYYY-MM-DD"
                )
        
        # 用户ID过滤
        if user_id:
            query = query.filter(PaymentOrder.user_id == user_id)
        
        # 套餐类型过滤
        if package_type:
            query = query.filter(PaymentPackage.package_type == package_type)
        
        # 分页
        total = query.count()
        offset = (page - 1) * size
        orders = query.order_by(desc(PaymentOrder.created_at)).offset(offset).limit(size).all()
        
        # 格式化订单数据
        orders_data = []
        for order in orders:
            orders_data.append({
                "id": order.id,
                "out_trade_no": order.out_trade_no,
                "user_id": order.user_id,
                "username": order.user.username,
                "package_info": {
                    "name": order.payment_package.name,
                    "type": order.payment_package.package_type,
                    "membership_type": order.payment_package.membership_type,
                    "price": float(order.payment_package.price)
                },
                "amount": float(order.amount),
                "status": order.status,
                "payment_method": order.payment_method,
                "created_at": order.created_at.isoformat(),
                "paid_at": order.paid_at.isoformat() if order.paid_at else None,
                "expire_time": order.expire_time.isoformat() if order.expire_time else None,
                "transaction_id": order.transaction_id,
                "is_active": order.expire_time is None or order.expire_time > datetime.now() if order.status == PaymentStatus.PAID else False
            })
        
        return {
            "status": "success",
            "data": {
                "orders": orders_data,
                "pagination": {
                    "page": page,
                    "size": size,
                    "total": total,
                    "pages": (total + size - 1) // size
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get all orders error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取订单列表失败"
        )


@router.get("/orders/{order_id}")
async def get_order_detail(
    order_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """获取订单详情（管理员）"""
    try:
        order = db.query(PaymentOrder).join(PaymentPackage).join(User).filter(
            PaymentOrder.id == order_id
        ).first()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="订单不存在"
            )
        
        # 获取用户会员状态
        membership_status = await user_membership_service.get_user_membership_status(
            db, order.user_id
        )
        
        # 获取退款记录
        refund_records = db.query(RefundRecord).filter(
            RefundRecord.payment_order_id == order_id
        ).order_by(desc(RefundRecord.created_at)).all()
        
        refunds_data = []
        for refund in refund_records:
            refunds_data.append({
                "id": refund.id,
                "out_refund_no": refund.out_refund_no,
                "refund_amount": float(refund.refund_amount),
                "refund_reason": refund.refund_reason,
                "refund_status": refund.refund_status.value.lower(),
                "created_at": refund.created_at.isoformat(),
                "processed_at": refund.processed_at.isoformat() if refund.processed_at else None
            })
        
        return {
            "status": "success",
            "data": {
                "order": {
                    "id": order.id,
                    "out_trade_no": order.out_trade_no,
                    "user_info": {
                        "id": order.user_id,
                        "username": order.user.username,
                        "email": getattr(order.user, 'email', ''),
                        "created_at": order.user.created_at.isoformat()
                    },
                    "package_info": {
                        "name": order.payment_package.name,
                        "type": order.payment_package.package_type,
                        "membership_type": order.payment_package.membership_type,
                        "price": float(order.payment_package.price),
                        "queries_count": order.payment_package.queries_count,
                        "validity_days": order.payment_package.validity_days,
                        "description": order.payment_package.description
                    },
                    "amount": float(order.amount),
                    "status": order.status.value.lower(),
                    "payment_method": order.payment_method.value.lower(),
                    "created_at": order.created_at.isoformat(),
                    "paid_at": order.paid_at.isoformat() if order.paid_at else None,
                    "expire_time": order.expire_time.isoformat() if order.expire_time else None,
                    "transaction_id": order.transaction_id,
                    "client_ip": order.client_ip,
                    "user_agent": order.user_agent,
                    "is_active": order.expire_time is None or order.expire_time > datetime.now() if order.status == PaymentStatus.PAID else False
                },
                "membership_status": membership_status if 'error' not in membership_status else None,
                "refund_records": refunds_data
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get order detail error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取订单详情失败"
        )


@router.post("/orders/{order_id}/force-complete")
async def force_complete_order(
    order_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """强制完成订单（管理员）"""
    try:
        order = db.query(PaymentOrder).filter(PaymentOrder.id == order_id).first()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="订单不存在"
            )
        
        if order.status != PaymentStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"只能强制完成待支付订单，当前状态: {order.status.value}"
            )
        
        # 更新订单状态
        order.status = PaymentStatus.PAID
        order.paid_at = datetime.now()
        order.transaction_id = f"ADMIN_FORCE_{order.id}_{int(datetime.now().timestamp())}"
        
        # 激活用户套餐权限
        activation_result = await user_membership_service.activate_package_for_user(
            db, order.user_id, order.id
        )
        
        db.commit()
        
        logger.info(f"Order {order_id} force completed by admin {admin_user.username}")
        
        return {
            "status": "success",
            "message": "订单强制完成成功",
            "data": {
                "order_id": order_id,
                "out_trade_no": order.out_trade_no,
                "transaction_id": order.transaction_id,
                "activation_result": activation_result
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Force complete order error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="强制完成订单失败"
        )


@router.post("/orders/{order_id}/cancel")
async def cancel_order_admin(
    order_id: int,
    reason: str = Query(..., description="取消原因"),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """取消订单（管理员）"""
    try:
        order = db.query(PaymentOrder).filter(PaymentOrder.id == order_id).first()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="订单不存在"
            )
        
        if order.status not in [PaymentStatus.PENDING, PaymentStatus.PAID]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无法取消此状态的订单: {order.status.value}"
            )
        
        # 更新订单状态
        order.status = PaymentStatus.CANCELLED
        order.cancelled_at = datetime.now()
        order.cancel_reason = reason
        
        db.commit()
        
        logger.info(f"Order {order_id} cancelled by admin {admin_user.username}: {reason}")
        
        return {
            "status": "success",
            "message": "订单取消成功",
            "data": {
                "order_id": order_id,
                "out_trade_no": order.out_trade_no,
                "cancel_reason": reason,
                "cancelled_at": order.cancelled_at.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Cancel order admin error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="取消订单失败"
        )


@router.get("/statistics")
async def get_order_statistics(
    days: int = Query(default=30, ge=1, le=365, description="统计天数"),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """获取订单统计信息（管理员）"""
    try:
        # 时间范围
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        # 基础统计
        total_orders = db.query(func.count(PaymentOrder.id)).filter(
            PaymentOrder.created_at >= start_time
        ).scalar()
        
        paid_orders = db.query(func.count(PaymentOrder.id)).filter(
            and_(
                PaymentOrder.created_at >= start_time,
                PaymentOrder.status == PaymentStatus.PAID
            )
        ).scalar()
        
        total_revenue = db.query(func.sum(PaymentOrder.amount)).filter(
            and_(
                PaymentOrder.created_at >= start_time,
                PaymentOrder.status == PaymentStatus.PAID
            )
        ).scalar() or 0
        
        # 按状态统计
        status_stats = db.query(
            PaymentOrder.status,
            func.count(PaymentOrder.id).label('count')
        ).filter(
            PaymentOrder.created_at >= start_time
        ).group_by(PaymentOrder.status).all()
        
        status_data = {stat.status.value.lower(): stat.count for stat in status_stats}
        
        # 按套餐类型统计
        package_stats = db.query(
            PaymentPackage.package_type,
            PaymentPackage.name,
            func.count(PaymentOrder.id).label('order_count'),
            func.sum(func.case([(PaymentOrder.status == PaymentStatus.PAID, PaymentOrder.amount)], else_=0)).label('revenue')
        ).join(PaymentOrder).filter(
            PaymentOrder.created_at >= start_time
        ).group_by(PaymentPackage.package_type, PaymentPackage.name).all()
        
        package_data = []
        for stat in package_stats:
            package_data.append({
                "package_type": stat.package_type,
                "package_name": stat.name,
                "order_count": stat.order_count,
                "revenue": float(stat.revenue or 0)
            })
        
        # 按日统计最近7天
        daily_stats = db.execute(text("""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as total_orders,
                SUM(CASE WHEN status = 'PAID' THEN 1 ELSE 0 END) as paid_orders,
                SUM(CASE WHEN status = 'PAID' THEN amount ELSE 0 END) as revenue
            FROM payment_orders 
            WHERE created_at >= :start_date 
            GROUP BY DATE(created_at)
            ORDER BY date DESC
            LIMIT 7
        """), {'start_date': start_time}).fetchall()
        
        daily_data = []
        for row in daily_stats:
            daily_data.append({
                "date": row.date.isoformat(),
                "total_orders": row.total_orders,
                "paid_orders": row.paid_orders,
                "revenue": float(row.revenue or 0)
            })
        
        return {
            "status": "success",
            "data": {
                "period": {
                    "days": days,
                    "start_date": start_time.isoformat(),
                    "end_date": end_time.isoformat()
                },
                "overview": {
                    "total_orders": total_orders,
                    "paid_orders": paid_orders,
                    "success_rate": (paid_orders / total_orders * 100) if total_orders > 0 else 0,
                    "total_revenue": float(total_revenue),
                    "average_order_value": float(total_revenue / paid_orders) if paid_orders > 0 else 0
                },
                "status_breakdown": status_data,
                "package_breakdown": package_data,
                "daily_trends": daily_data
            }
        }
        
    except Exception as e:
        logger.error(f"Get order statistics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取订单统计失败"
        )


@router.post("/orders/{order_id}/extend-validity")
async def extend_order_validity(
    order_id: int,
    extend_days: int = Query(..., ge=1, le=3650, description="延长天数"),
    reason: str = Query(..., description="延长原因"),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """延长订单有效期（管理员）"""
    try:
        order = db.query(PaymentOrder).filter(PaymentOrder.id == order_id).first()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="订单不存在"
            )
        
        if order.status != PaymentStatus.PAID:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只能延长已支付订单的有效期"
            )
        
        # 计算新的过期时间
        current_expire = order.expire_time or datetime.now()
        new_expire_time = current_expire + timedelta(days=extend_days)
        
        order.expire_time = new_expire_time
        db.commit()
        
        logger.info(f"Order {order_id} validity extended by {extend_days} days by admin {admin_user.username}: {reason}")
        
        return {
            "status": "success",
            "message": f"订单有效期延长 {extend_days} 天",
            "data": {
                "order_id": order_id,
                "out_trade_no": order.out_trade_no,
                "old_expire_time": current_expire.isoformat(),
                "new_expire_time": new_expire_time.isoformat(),
                "extend_days": extend_days,
                "reason": reason
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Extend order validity error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="延长订单有效期失败"
        )