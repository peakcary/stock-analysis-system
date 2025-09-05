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
from app.models.payment import PaymentPackage, PaymentOrder, PaymentNotification, MembershipLog, PaymentStatus, RefundRecord, RefundStatus
from app.schemas.payment import (
    PaymentPackage as PaymentPackageSchema,
    PaymentOrderCreate, PaymentOrderResponse, PaymentOrderQuery,
    PaymentNotifyResponse, OrderStatusCheck
)
from app.services.wechat_pay import wechat_pay_service, WechatPayException
from app.core.config import settings
from app.services.user_membership import user_membership_service
from app.services.mock_payment import mock_payment_service

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
                PaymentOrder.status == PaymentStatus.PENDING,
                PaymentOrder.expire_time > datetime.now()
            )
        ).first()
        
        if existing_order:
            # 返回现有订单
            return existing_order
        
        # 获取客户端IP
        client_ip = order_data.client_ip or request.client.host
        user_agent = order_data.user_agent or request.headers.get("user-agent", "")
        
        # 调用微信支付统一下单（包括模拟和真实支付）
        trade_type = "NATIVE" if order_data.payment_method == "wechat_native" else "MWEB"
        payment_result = await wechat_pay_service.unified_order(
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
            package_id=package.id,
            out_trade_no=payment_result["out_trade_no"],
            package_type=package.package_type,
            package_name=package.name,
            amount=package.price,
            payment_method=order_data.payment_method,
            prepay_id=payment_result.get("prepay_id"),
            code_url=payment_result.get("code_url"),
            h5_url=payment_result.get("mweb_url"),
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
        
        # 如果订单未支付且未过期，查询支付状态
        if order.status == PaymentStatus.PENDING and order.expire_time > datetime.now():
            try:
                if settings.PAYMENT_MOCK_MODE:
                    # 使用模拟支付服务查询
                    payment_result = await mock_payment_service.query_order(out_trade_no)
                else:
                    # 查询真实微信支付状态
                    payment_result = await wechat_pay_service.query_order(out_trade_no)
                
                # 更新订单状态
                trade_state = payment_result.get("trade_state") if settings.PAYMENT_MOCK_MODE else payment_result.get("trade_state")
                if trade_state == "SUCCESS":
                    order.status = PaymentStatus.PAID
                    order.transaction_id = payment_result.get("transaction_id")
                    order.paid_at = datetime.now()
                    
                    # 处理会员权益
                    result = await user_membership_service.activate_package_for_user(db, order.user_id, order.id)
                    if not result.get('success', False):
                        logger.warning(f"Package activation failed for order {order.id}: {result.get('message', 'Unknown error')}")
                    
                    db.commit()
                elif trade_state in ["CLOSED", "REVOKED", "PAYERROR"]:
                    order.status = PaymentStatus.FAILED
                    db.commit()
                    
            except (WechatPayException, Exception):
                # 查询失败，保持原状态
                pass
        
        # 检查订单是否过期
        elif order.status == PaymentStatus.PENDING and order.expire_time <= datetime.now():
            order.status = PaymentStatus.EXPIRED
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
                PaymentOrder.status == PaymentStatus.PENDING
            )
        ).first()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="支付订单不存在或无法取消"
            )
        
        # 关闭支付订单
        await wechat_pay_service.close_order(out_trade_no)
        
        # 更新订单状态
        order.status = PaymentStatus.CANCELLED
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
            
            if order and order.status == PaymentStatus.PENDING:
                # 更新订单状态
                order.status = PaymentStatus.PAID
                order.transaction_id = notify_data["transaction_id"]
                order.paid_at = datetime.now()
                order.notify_data = notify_data["raw_data"]
                
                # 激活用户套餐权限
                activation_result = await user_membership_service.activate_package_for_user(
                    db, order.user_id, order.id
                )
                
                if not activation_result['success']:
                    logger.warning(f"Package activation failed for order {order.id}: {activation_result['message']}")
                else:
                    logger.info(f"Package activated successfully for user {order.user_id}: {activation_result['message']}")
                
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


# ============ 测试接口（仅在模拟模式下可用） ============

@router.get("/test/debug-auth")
async def debug_auth(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """调试认证信息"""
    headers = dict(request.headers)
    return {
        "authenticated": True,
        "user_id": current_user.id,
        "username": current_user.username,
        "headers": headers,
        "authorization": headers.get("authorization", "No Authorization header")
    }

@router.post("/test/simulate-success/{out_trade_no}")
async def simulate_payment_success(
    out_trade_no: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """模拟支付成功（仅在测试模式下可用）"""
    if not settings.PAYMENT_MOCK_MODE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="此接口仅在测试模式下可用"
        )
    
    try:
        order = db.query(PaymentOrder).filter(
            and_(
                PaymentOrder.out_trade_no == out_trade_no,
                PaymentOrder.user_id == current_user.id,
                PaymentOrder.status == PaymentStatus.PENDING
            )
        ).first()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="订单不存在或已处理"
            )
        
        # 使用模拟支付服务模拟成功
        success = mock_payment_service.simulate_payment_success(out_trade_no)
        
        if success:
            # 更新订单状态
            order.status = PaymentStatus.PAID
            order.transaction_id = f'4200001234567890{out_trade_no[-8:]}'
            order.paid_at = datetime.now()
            
            # 处理会员权益
            result = await user_membership_service.activate_package_for_user(db, order.user_id, order.id)
            if not result.get('success', False):
                logger.warning(f"Package activation failed for order {order.id}: {result.get('message', 'Unknown error')}")
            
            db.commit()
            
            return {
                "message": "支付成功模拟完成",
                "out_trade_no": out_trade_no,
                "status": "paid"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="模拟支付失败，订单可能不存在"
            )
            
    except Exception as e:
        logger.error(f"Simulate payment success error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="模拟支付成功失败"
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
                    (PaymentOrder.status == PaymentStatus.PAID, PaymentOrder.amount),
                    else_=0
                )
            ).label("total_amount"),
            func.count(
                func.case(
                    (PaymentOrder.status == PaymentStatus.PAID, 1),
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


# ============ 退款相关接口 ============

@router.post("/refund/{order_id}")
async def apply_refund(
    order_id: int,
    refund_reason: str = "用户申请退款",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """申请退款"""
    try:
        # 查找订单
        order = db.query(PaymentOrder).filter(
            and_(
                PaymentOrder.id == order_id,
                PaymentOrder.user_id == current_user.id,
                PaymentOrder.status == PaymentStatus.PAID
            )
        ).first()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="订单不存在或不可退款"
            )
        
        # 检查是否已有退款记录
        existing_refund = db.query(RefundRecord).filter(
            RefundRecord.order_id == order_id
        ).first()
        
        if existing_refund:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该订单已申请过退款"
            )
        
        # 检查是否在退款时限内（例如30天内）
        refund_deadline = order.paid_at + timedelta(days=30)
        if datetime.now() > refund_deadline:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="超过退款时限（支付后30天内）"
            )
        
        # 计算退款金额（单位：分）
        total_fee = int(order.amount * 100)  # 转换为分
        refund_fee = total_fee  # 全额退款
        
        try:
            # 调用微信退款API
            refund_result = await wechat_pay_service.apply_refund(
                out_trade_no=order.out_trade_no,
                total_fee=total_fee,
                refund_fee=refund_fee,
                refund_reason=refund_reason
            )
            
            # 创建退款记录
            refund_record = RefundRecord(
                order_id=order.id,
                out_refund_no=refund_result['out_refund_no'],
                refund_id=refund_result.get('refund_id'),
                refund_amount=Decimal(str(refund_fee / 100)),  # 转换回元
                refund_reason=refund_reason,
                refund_status=RefundStatus.PROCESSING,
                refund_channel=refund_result.get('refund_channel')
            )
            
            db.add(refund_record)
            
            # 更新订单状态
            order.status = PaymentStatus.REFUNDED
            order.refunded_at = datetime.now()
            order.refund_amount = Decimal(str(refund_fee / 100))
            
            db.commit()
            
            return {
                "message": "退款申请已提交",
                "out_refund_no": refund_result['out_refund_no'],
                "refund_fee": refund_fee / 100,
                "refund_status": "processing"
            }
            
        except WechatPayException as e:
            logger.error(f"Apply refund error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"退款申请失败: {str(e)}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Apply refund error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="退款申请失败"
        )


@router.get("/refunds")
async def get_user_refunds(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取用户退款记录"""
    try:
        # 查询用户的退款记录
        refunds = db.query(RefundRecord).join(PaymentOrder).filter(
            PaymentOrder.user_id == current_user.id
        ).order_by(RefundRecord.created_at.desc()).offset(skip).limit(limit).all()
        
        refund_list = []
        for refund in refunds:
            refund_data = {
                "id": refund.id,
                "order_id": refund.order_id,
                "out_refund_no": refund.out_refund_no,
                "refund_id": refund.refund_id,
                "refund_amount": float(refund.refund_amount),
                "refund_reason": refund.refund_reason,
                "refund_status": refund.refund_status.value,
                "refund_channel": refund.refund_channel,
                "created_at": refund.created_at,
                "processed_at": refund.processed_at
            }
            refund_list.append(refund_data)
        
        return {
            "refunds": refund_list,
            "total": len(refund_list),
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Get user refunds error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取退款记录失败"
        )


@router.get("/refund/{refund_id}/status")
async def check_refund_status(
    refund_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """查询退款状态"""
    try:
        # 查找退款记录
        refund = db.query(RefundRecord).join(PaymentOrder).filter(
            and_(
                RefundRecord.id == refund_id,
                PaymentOrder.user_id == current_user.id
            )
        ).first()
        
        if not refund:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="退款记录不存在"
            )
        
        # 如果退款还在处理中，查询微信接口获取最新状态
        if refund.refund_status == RefundStatus.PROCESSING:
            try:
                query_result = await wechat_pay_service.query_refund(
                    out_refund_no=refund.out_refund_no
                )
                
                # 更新退款状态
                refund_status = query_result.get('refund_status_0')  # 微信退款状态
                if refund_status == 'SUCCESS':
                    refund.refund_status = RefundStatus.SUCCESS
                    refund.processed_at = datetime.now()
                elif refund_status == 'REFUNDCLOSE':
                    refund.refund_status = RefundStatus.FAILED
                    refund.processed_at = datetime.now()
                elif refund_status == 'CHANGE':
                    refund.refund_status = RefundStatus.FAILED
                    refund.processed_at = datetime.now()
                
                db.commit()
                
            except WechatPayException as e:
                logger.warning(f"Query refund status error: {e}")
                # 查询失败不影响返回现有状态
        
        return {
            "refund_id": refund.id,
            "out_refund_no": refund.out_refund_no,
            "refund_amount": float(refund.refund_amount),
            "refund_status": refund.refund_status.value,
            "refund_reason": refund.refund_reason,
            "created_at": refund.created_at,
            "processed_at": refund.processed_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Check refund status error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="查询退款状态失败"
        )


@router.post("/refund/notify")
async def handle_refund_notify(request: Request, db: Session = Depends(get_db)):
    """处理微信退款回调通知"""
    try:
        # 读取XML数据
        xml_data = await request.body()
        xml_str = xml_data.decode('utf-8')
        
        logger.info(f"Received refund notify: {xml_str}")
        
        # 处理退款通知
        result = await wechat_pay_service.process_refund_notify(xml_str)
        
        if result['success']:
            notify_data = result['data']
            out_refund_no = notify_data.get('out_refund_no')
            
            # 查找退款记录
            refund = db.query(RefundRecord).filter(
                RefundRecord.out_refund_no == out_refund_no
            ).first()
            
            if refund:
                # 更新退款状态
                refund_status = notify_data.get('refund_status')
                if refund_status == 'SUCCESS':
                    refund.refund_status = RefundStatus.SUCCESS
                    refund.processed_at = datetime.strptime(
                        notify_data.get('success_time'), '%Y-%m-%d %H:%M:%S'
                    ) if notify_data.get('success_time') else datetime.now()
                    
                    # 处理会员权益回收（如果需要）
                    # 这里可以根据业务需求决定是否回收已发放的会员权益
                    
                else:
                    refund.refund_status = RefundStatus.FAILED
                    refund.processed_at = datetime.now()
                
                # 更新其他退款信息
                refund.refund_id = notify_data.get('refund_id')
                
                db.commit()
                logger.info(f"Refund notify processed successfully: {out_refund_no}")
            else:
                logger.warning(f"Refund record not found: {out_refund_no}")
        
        # 返回成功响应给微信
        return Response(
            content=wechat_pay_service.create_success_response(),
            media_type="application/xml"
        )
        
    except Exception as e:
        logger.error(f"Handle refund notify error: {e}")
        return Response(
            content=wechat_pay_service.create_fail_response("系统异常"),
            media_type="application/xml"
        )