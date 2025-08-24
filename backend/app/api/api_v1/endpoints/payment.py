"""
支付相关API接口
Payment API endpoints
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text

from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.core.logging import logger
from app.models.user import User
from app.models.payment import PaymentPackage, PaymentOrder, PaymentNotification, MembershipLog
from app.schemas.payment import (
    PaymentPackage as PaymentPackageSchema,
    PaymentOrderCreate, PaymentOrderResponse, PaymentOrderQuery,
    PaymentNotifyResponse, OrderStatusCheck
)
from app.services.wechat_pay import wechat_pay_service, WechatPayException
from app.services.membership import membership_service

router = APIRouter()


# ============ 支付套餐管理 ============

@router.get("/packages", response_model=List[PaymentPackageSchema])
async def get_payment_packages(
    is_active: bool = True,
    db: Session = Depends(get_db)
):
    """获取支付套餐列表"""
    try:
        # 使用原生SQL查询避免枚举映射问题
        sql = text("""
        SELECT id, package_type, name, price, queries_count, validity_days, 
               membership_type, description, is_active, sort_order, 
               created_at, updated_at
        FROM payment_packages 
        WHERE is_active = :is_active 
        ORDER BY sort_order, id
        """)
        result = db.execute(sql, {"is_active": is_active})
        rows = result.fetchall()
        
        packages = []
        for row in rows:
            package = {
                'id': row[0],
                'package_type': row[1], 
                'name': row[2],
                'price': row[3],
                'queries_count': row[4],
                'validity_days': row[5],
                'membership_type': row[6],
                'description': row[7],
                'is_active': row[8],
                'sort_order': row[9],
                'created_at': row[10],
                'updated_at': row[11]
            }
            packages.append(package)
        
        return packages
    except Exception as e:
        logger.error(f"Get payment packages error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取支付套餐失败"
        )


@router.get("/packages/{package_type}", response_model=PaymentPackageSchema)
async def get_payment_package(
    package_type: str,
    db: Session = Depends(get_db)
):
    """获取指定支付套餐详情"""
    package = db.query(PaymentPackage).filter(
        PaymentPackage.package_type == package_type
    ).first()
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="支付套餐不存在"
        )
    
    return package


# ============ 支付订单管理 ============

@router.post("/orders", response_model=PaymentOrderResponse)
async def create_payment_order(
    order_data: PaymentOrderCreate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建支付订单"""
    try:
        # 获取套餐配置
        package = db.query(PaymentPackage).filter(
            and_(
                PaymentPackage.package_type == order_data.package_type,
                PaymentPackage.is_active == True
            )
        ).first()
        
        if not package:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="支付套餐不存在或已下架"
            )
        
        # 检查用户是否有未支付的同类型订单
        existing_order = db.query(PaymentOrder).filter(
            and_(
                PaymentOrder.user_id == current_user.id,
                PaymentOrder.package_type == order_data.package_type,
                PaymentOrder.status == "pending",
                PaymentOrder.expire_time > datetime.now()
            )
        ).first()
        
        if existing_order:
            # 返回现有订单
            return existing_order
        
        # 获取客户端IP
        client_ip = order_data.client_ip or request.client.host
        user_agent = order_data.user_agent or request.headers.get("user-agent", "")
        
        # 调用微信支付统一下单
        trade_type = "NATIVE" if order_data.payment_method == "wechat_native" else "MWEB"
        wechat_result = await wechat_pay_service.unified_order(
            user_id=current_user.id,
            package_type=package.package_type,
            package_name=package.name,
            total_fee=int(package.price * 100),  # 转换为分
            trade_type=trade_type,
            client_ip=client_ip
        )
        
        # 创建订单记录
        order = PaymentOrder(
            user_id=current_user.id,
            out_trade_no=wechat_result["out_trade_no"],
            package_type=package.package_type,
            package_name=package.name,
            amount=package.price,
            payment_method=order_data.payment_method,
            prepay_id=wechat_result.get("prepay_id"),
            code_url=wechat_result.get("code_url"),
            h5_url=wechat_result.get("mweb_url"),
            expire_time=datetime.now() + timedelta(hours=2),
            client_ip=client_ip,
            user_agent=user_agent
        )
        
        db.add(order)
        db.commit()
        db.refresh(order)
        
        logger.info(f"Payment order created: {order.out_trade_no} for user {current_user.id}")
        return order
        
    except WechatPayException as e:
        logger.error(f"Wechat pay error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"微信支付失败: {e}"
        )
    except Exception as e:
        logger.error(f"Create payment order error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建支付订单失败"
        )


@router.get("/orders", response_model=List[PaymentOrderResponse])
async def get_user_payment_orders(
    status: str = None,
    page: int = 1,
    size: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取用户支付订单列表"""
    try:
        query = db.query(PaymentOrder).filter(PaymentOrder.user_id == current_user.id)
        
        if status:
            query = query.filter(PaymentOrder.status == status)
        
        # 分页
        offset = (page - 1) * size
        orders = query.order_by(PaymentOrder.created_at.desc()).offset(offset).limit(size).all()
        
        return orders
    except Exception as e:
        logger.error(f"Get user payment orders error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取支付订单失败"
        )


@router.get("/orders/{out_trade_no}", response_model=PaymentOrderResponse)
async def get_payment_order(
    out_trade_no: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取支付订单详情"""
    order = db.query(PaymentOrder).filter(
        and_(
            PaymentOrder.out_trade_no == out_trade_no,
            PaymentOrder.user_id == current_user.id
        )
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="支付订单不存在"
        )
    
    return order


@router.get("/orders/{out_trade_no}/status", response_model=OrderStatusCheck)
async def check_payment_status(
    out_trade_no: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """检查支付状态"""
    try:
        order = db.query(PaymentOrder).filter(
            and_(
                PaymentOrder.out_trade_no == out_trade_no,
                PaymentOrder.user_id == current_user.id
            )
        ).first()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="支付订单不存在"
            )
        
        # 如果订单未支付且未过期，查询微信支付状态
        if order.status == "pending" and order.expire_time > datetime.now():
            try:
                wechat_result = await wechat_pay_service.query_order(out_trade_no)
                
                # 更新订单状态
                if wechat_result.get("trade_state") == "SUCCESS":
                    order.status = "paid"
                    order.transaction_id = wechat_result.get("transaction_id")
                    order.paid_at = datetime.now()
                    
                    # 处理会员权益
                    await membership_service.process_payment_success(db, order)
                    
                    db.commit()
                elif wechat_result.get("trade_state") in ["CLOSED", "REVOKED", "PAYERROR"]:
                    order.status = "failed"
                    db.commit()
                    
            except WechatPayException:
                # 查询失败，保持原状态
                pass
        
        # 检查订单是否过期
        elif order.status == "pending" and order.expire_time <= datetime.now():
            order.status = "expired"
            db.commit()
        
        return OrderStatusCheck(
            out_trade_no=order.out_trade_no,
            status=order.status,
            paid_at=order.paid_at,
            transaction_id=order.transaction_id
        )
        
    except Exception as e:
        logger.error(f"Check payment status error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="检查支付状态失败"
        )


@router.post("/orders/{out_trade_no}/cancel")
async def cancel_payment_order(
    out_trade_no: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """取消支付订单"""
    try:
        order = db.query(PaymentOrder).filter(
            and_(
                PaymentOrder.out_trade_no == out_trade_no,
                PaymentOrder.user_id == current_user.id,
                PaymentOrder.status == "pending"
            )
        ).first()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="支付订单不存在或无法取消"
            )
        
        # 关闭微信支付订单
        await wechat_pay_service.close_order(out_trade_no)
        
        # 更新订单状态
        order.status = "cancelled"
        order.cancelled_at = datetime.now()
        db.commit()
        
        return {"message": "订单已取消"}
        
    except Exception as e:
        logger.error(f"Cancel payment order error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="取消支付订单失败"
        )


# ============ 支付通知处理 ============

@router.post("/notify", response_class=Response)
async def payment_notify(
    request: Request,
    db: Session = Depends(get_db)
):
    """微信支付通知回调"""
    try:
        # 获取原始XML数据
        xml_data = await request.body()
        client_ip = request.client.host
        
        logger.info(f"Payment notify received from {client_ip}")
        
        # 处理支付通知
        result = wechat_pay_service.process_notify(xml_data.decode('utf-8'))
        
        # 记录通知
        notification = PaymentNotification(
            out_trade_no=result["data"].get("out_trade_no", ""),
            transaction_id=result["data"].get("transaction_id", ""),
            raw_data=xml_data.decode('utf-8'),
            is_valid=result["success"],
            client_ip=client_ip
        )
        db.add(notification)
        
        if result["success"]:
            # 查找对应订单
            notify_data = result["data"]
            order = db.query(PaymentOrder).filter(
                PaymentOrder.out_trade_no == notify_data["out_trade_no"]
            ).first()
            
            if order and order.status == "pending":
                # 更新订单状态
                order.status = "paid"
                order.transaction_id = notify_data["transaction_id"]
                order.paid_at = datetime.now()
                order.notify_data = notify_data["raw_data"]
                
                # 处理会员权益
                await membership_service.process_payment_success(db, order)
                
                notification.processed = True
                notification.process_result = "Payment processed successfully"
                
                logger.info(f"Payment success processed: {order.out_trade_no}")
            else:
                notification.process_result = f"Order not found or already processed: {notify_data['out_trade_no']}"
        else:
            notification.process_result = f"Invalid notification: {result['message']}"
        
        notification.processed_at = datetime.now()
        db.commit()
        
        # 返回响应
        if result["success"]:
            return Response(
                content=wechat_pay_service.create_success_response(),
                media_type="application/xml"
            )
        else:
            return Response(
                content=wechat_pay_service.create_fail_response(),
                media_type="application/xml"
            )
            
    except Exception as e:
        logger.error(f"Payment notify error: {e}")
        db.rollback()
        return Response(
            content=wechat_pay_service.create_fail_response("SYSTEM_ERROR"),
            media_type="application/xml"
        )


# ============ 支付统计 ============

@router.get("/stats")
async def get_payment_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取用户支付统计"""
    try:
        user_stats = db.query(
            func.count(PaymentOrder.id).label("total_orders"),
            func.sum(
                func.case(
                    (PaymentOrder.status == "paid", PaymentOrder.amount),
                    else_=0
                )
            ).label("total_amount"),
            func.count(
                func.case(
                    (PaymentOrder.status == "paid", 1),
                    else_=None
                )
            ).label("paid_orders")
        ).filter(PaymentOrder.user_id == current_user.id).first()
        
        return {
            "total_orders": user_stats.total_orders or 0,
            "paid_orders": user_stats.paid_orders or 0,
            "total_amount": user_stats.total_amount or 0,
            "membership_type": current_user.membership_type.value,
            "queries_remaining": current_user.queries_remaining,
            "membership_expires_at": current_user.membership_expires_at
        }
        
    except Exception as e:
        logger.error(f"Get payment stats error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取支付统计失败"
        )