"""
支付服务管理器
Payment Service Manager

统一管理支付相关服务，处理订单创建、状态查询、回调处理等业务逻辑
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Optional, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text

from app.core.database import get_db
from app.core.logging import logger
from app.core.config import settings
from app.models.user import User
from app.models.payment import (
    PaymentPackage, PaymentOrder, PaymentNotification,
    MembershipLog, RefundRecord, PaymentStatus, PaymentMethod,
    ActionType, RefundStatus
)
from app.services.wechat_pay import wechat_pay_service, WechatPayException
from app.services.wechat_pay_v3 import wechat_pay_v3_service, WechatPayV3Exception
from app.services.user_membership import user_membership_service
from app.services.mock_payment import mock_payment_service


class PaymentManager:
    """支付服务管理器"""

    def __init__(self):
        self.wechat_pay = wechat_pay_service  # V2 API
        self.wechat_pay_v3 = wechat_pay_v3_service  # V3 API (推荐)

    async def create_payment_order(
        self,
        user: User,
        package_type: str,
        payment_method: str = PaymentMethod.WECHAT_NATIVE,
        client_ip: str = "127.0.0.1",
        user_agent: str = "",
        db: Session = None
    ) -> Dict[str, Any]:
        """创建支付订单"""
        try:
            # 获取套餐信息
            package = db.query(PaymentPackage).filter(
                and_(
                    PaymentPackage.package_type == package_type,
                    PaymentPackage.is_active == True
                )
            ).first()

            if not package:
                raise ValueError(f"套餐 {package_type} 不存在或已停用")

            # 检查用户是否有待支付订单
            pending_order = db.query(PaymentOrder).filter(
                and_(
                    PaymentOrder.user_id == user.id,
                    PaymentOrder.package_type == package_type,
                    PaymentOrder.status == PaymentStatus.PENDING,
                    PaymentOrder.expire_time > datetime.now()
                )
            ).first()

            if pending_order:
                return {
                    'success': True,
                    'message': '存在待支付订单',
                    'order_id': pending_order.id,
                    'out_trade_no': pending_order.out_trade_no,
                    'code_url': pending_order.code_url,
                    'h5_url': pending_order.h5_url,
                    'expire_time': pending_order.expire_time,
                    'amount': float(pending_order.amount)
                }

            # 调用微信支付V3 API创建订单
            total_amount = int(package.price * 100)  # 转换为分

            if payment_method == PaymentMethod.WECHAT_H5:
                wechat_result = await self.wechat_pay_v3.create_h5_payment(
                    user_id=user.id,
                    package_type=package_type,
                    package_name=package.name,
                    total_amount=total_amount,
                    client_ip=client_ip,
                    description=f"股票分析系统-{package.name}"
                )
            else:  # NATIVE支付
                wechat_result = await self.wechat_pay_v3.create_native_payment(
                    user_id=user.id,
                    package_type=package_type,
                    package_name=package.name,
                    total_amount=total_amount,
                    description=f"股票分析系统-{package.name}"
                )

            # 创建订单记录
            expire_time = datetime.now() + timedelta(hours=settings.PAYMENT_ORDER_TIMEOUT_HOURS)

            order = PaymentOrder(
                user_id=user.id,
                package_id=package.id,
                out_trade_no=wechat_result['out_trade_no'],
                package_type=package_type,
                package_name=package.name,
                amount=package.price,
                status=PaymentStatus.PENDING,
                payment_method=payment_method,
                prepay_id=None,  # V3 API不返回prepay_id
                code_url=wechat_result.get('code_url'),
                h5_url=wechat_result.get('h5_url'),
                expire_time=expire_time,
                client_ip=client_ip,
                user_agent=user_agent
            )

            db.add(order)
            db.commit()
            db.refresh(order)

            logger.info(f"Created payment order {order.id} for user {user.id}")

            return {
                'success': True,
                'message': '订单创建成功',
                'order_id': order.id,
                'out_trade_no': order.out_trade_no,
                'code_url': order.code_url,
                'h5_url': order.h5_url,
                'expire_time': order.expire_time,
                'amount': float(order.amount),
                'mock_mode': wechat_result.get('mock_mode', False)
            }

        except (WechatPayException, WechatPayV3Exception) as e:
            logger.error(f"WeChat pay error: {e}")
            return {
                'success': False,
                'message': f'支付服务异常: {str(e)}',
                'error_type': 'wechat_pay_error'
            }
        except Exception as e:
            logger.error(f"Create payment order error: {e}")
            db.rollback()
            return {
                'success': False,
                'message': f'创建订单失败: {str(e)}',
                'error_type': 'system_error'
            }

    async def process_payment_notify(
        self,
        request_data: str,  # 可能是XML(V2)或JSON(V3)
        headers: dict = None,
        client_ip: str = "",
        db: Session = None
    ) -> Dict[str, Any]:
        """处理支付通知"""
        try:
            # 记录通知数据
            notification = PaymentNotification(
                raw_data=request_data,
                client_ip=client_ip,
                processed=False
            )
            db.add(notification)
            db.flush()

            # 判断通知类型并解析
            if headers and 'Wechatpay-Signature' in headers:
                # V3 API通知
                notify_result = self.wechat_pay_v3.process_notify(headers, request_data)
            else:
                # V2 API通知
                notify_result = self.wechat_pay.process_notify(request_data)

            # 更新通知记录
            notification.is_valid = notify_result['success']
            notification.out_trade_no = notify_result['data'].get('out_trade_no', '') if notify_result['data'] else ''
            notification.transaction_id = notify_result['data'].get('transaction_id', '') if notify_result['data'] else ''

            if not notify_result['success']:
                notification.process_result = f"通知验证失败: {notify_result['message']}"
                db.commit()
                return {
                    'success': False,
                    'message': notify_result['message'],
                    'xml_response': self.wechat_pay.create_fail_response()
                }

            # 查找对应订单
            out_trade_no = notify_result['data']['out_trade_no']
            order = db.query(PaymentOrder).filter(
                PaymentOrder.out_trade_no == out_trade_no
            ).first()

            if not order:
                notification.process_result = f"订单不存在: {out_trade_no}"
                db.commit()
                return {
                    'success': False,
                    'message': '订单不存在',
                    'xml_response': self.wechat_pay.create_fail_response()
                }

            # 检查订单状态
            if order.status == PaymentStatus.PAID:
                notification.process_result = "订单已支付"
                notification.processed = True
                db.commit()
                return {
                    'success': True,
                    'message': '订单已支付',
                    'xml_response': self.wechat_pay.create_success_response()
                }

            # 更新订单状态
            order.status = PaymentStatus.PAID
            order.transaction_id = notify_result['data']['transaction_id']
            order.paid_at = datetime.now()
            order.notify_data = notify_result['data']['raw_data']

            # 处理会员权益
            await self._process_membership_upgrade(order, db)

            # 完成处理
            notification.processed = True
            notification.process_result = "支付成功处理完成"
            notification.processed_at = datetime.now()

            db.commit()

            logger.info(f"Payment notify processed successfully for order {order.id}")

            return {
                'success': True,
                'message': '支付通知处理成功',
                'xml_response': self.wechat_pay.create_success_response()
            }

        except Exception as e:
            logger.error(f"Process payment notify error: {e}")
            db.rollback()
            return {
                'success': False,
                'message': f'处理支付通知失败: {str(e)}',
                'xml_response': self.wechat_pay.create_fail_response()
            }

    async def _process_membership_upgrade(self, order: PaymentOrder, db: Session):
        """处理会员权益升级"""
        try:
            # 获取用户和套餐信息
            user = db.query(User).filter(User.id == order.user_id).first()
            package = db.query(PaymentPackage).filter(PaymentPackage.id == order.package_id).first()

            if not user or not package:
                raise ValueError("用户或套餐不存在")

            # 记录变更前的状态
            old_membership_type = user.membership_type
            old_queries_remaining = user.queries_remaining
            old_expires_at = user.membership_expires_at

            # 使用会员服务处理升级
            upgrade_result = await user_membership_service.upgrade_membership(
                user=user,
                package=package,
                db=db
            )

            # 创建会员变更记录
            membership_log = MembershipLog(
                user_id=user.id,
                payment_order_id=order.id,
                action_type=ActionType.UPGRADE,
                old_membership_type=old_membership_type,
                new_membership_type=user.membership_type,
                old_queries_remaining=old_queries_remaining,
                new_queries_remaining=user.queries_remaining,
                queries_added=package.queries_count,
                old_expires_at=old_expires_at,
                new_expires_at=user.membership_expires_at,
                days_added=package.validity_days,
                notes=f"支付成功升级，订单号：{order.out_trade_no}"
            )

            db.add(membership_log)
            logger.info(f"Membership upgraded for user {user.id}: {old_membership_type} -> {user.membership_type}")

        except Exception as e:
            logger.error(f"Process membership upgrade error: {e}")
            raise

    async def query_order_status(self, out_trade_no: str, db: Session = None) -> Dict[str, Any]:
        """查询订单状态"""
        try:
            # 查询本地订单
            order = db.query(PaymentOrder).filter(
                PaymentOrder.out_trade_no == out_trade_no
            ).first()

            if not order:
                return {
                    'success': False,
                    'message': '订单不存在',
                    'status': 'not_found'
                }

            # 如果订单已支付，直接返回
            if order.status == PaymentStatus.PAID:
                return {
                    'success': True,
                    'message': '订单已支付',
                    'status': PaymentStatus.PAID,
                    'paid_at': order.paid_at,
                    'transaction_id': order.transaction_id
                }

            # 检查订单是否过期
            if datetime.now() > order.expire_time:
                order.status = PaymentStatus.EXPIRED
                db.commit()
                return {
                    'success': True,
                    'message': '订单已过期',
                    'status': PaymentStatus.EXPIRED
                }

            # 查询微信支付状态 (使用V3 API)
            wechat_result = await self.wechat_pay_v3.query_order(out_trade_no)

            if wechat_result.get('trade_state') == 'SUCCESS':
                # 更新订单状态
                order.status = PaymentStatus.PAID
                order.transaction_id = wechat_result.get('transaction_id')
                order.paid_at = datetime.now()

                # 处理会员权益
                await self._process_membership_upgrade(order, db)
                db.commit()

                return {
                    'success': True,
                    'message': '支付成功',
                    'status': PaymentStatus.PAID,
                    'paid_at': order.paid_at,
                    'transaction_id': order.transaction_id
                }

            return {
                'success': True,
                'message': '等待支付',
                'status': PaymentStatus.PENDING,
                'trade_state': wechat_result.get('trade_state', 'NOTPAY')
            }

        except (WechatPayException, WechatPayV3Exception) as e:
            logger.error(f"WeChat query order error: {e}")
            return {
                'success': False,
                'message': f'查询支付状态失败: {str(e)}',
                'status': 'query_error'
            }
        except Exception as e:
            logger.error(f"Query order status error: {e}")
            return {
                'success': False,
                'message': f'系统错误: {str(e)}',
                'status': 'system_error'
            }

    async def cancel_order(self, out_trade_no: str, db: Session = None) -> Dict[str, Any]:
        """取消订单"""
        try:
            order = db.query(PaymentOrder).filter(
                PaymentOrder.out_trade_no == out_trade_no
            ).first()

            if not order:
                return {'success': False, 'message': '订单不存在'}

            if order.status != PaymentStatus.PENDING:
                return {'success': False, 'message': f'订单状态不允许取消: {order.status}'}

            # 关闭微信支付订单 (使用V3 API)
            if not settings.PAYMENT_MOCK_MODE:
                close_success = await self.wechat_pay_v3.close_order(out_trade_no)
                if not close_success:
                    logger.warning(f"Failed to close WeChat order: {out_trade_no}")

            # 更新订单状态
            order.status = PaymentStatus.CANCELLED
            order.cancelled_at = datetime.now()
            db.commit()

            logger.info(f"Order {out_trade_no} cancelled successfully")

            return {
                'success': True,
                'message': '订单已取消'
            }

        except Exception as e:
            logger.error(f"Cancel order error: {e}")
            return {
                'success': False,
                'message': f'取消订单失败: {str(e)}'
            }

    async def get_user_payment_history(
        self,
        user_id: int,
        page: int = 1,
        size: int = 20,
        db: Session = None
    ) -> Dict[str, Any]:
        """获取用户支付历史"""
        try:
            offset = (page - 1) * size

            query = db.query(PaymentOrder).filter(
                PaymentOrder.user_id == user_id
            ).order_by(PaymentOrder.created_at.desc())

            total = query.count()
            orders = query.offset(offset).limit(size).all()

            order_list = []
            for order in orders:
                order_list.append({
                    'id': order.id,
                    'out_trade_no': order.out_trade_no,
                    'package_name': order.package_name,
                    'amount': float(order.amount),
                    'status': order.status,
                    'payment_method': order.payment_method,
                    'created_at': order.created_at,
                    'paid_at': order.paid_at,
                    'expire_time': order.expire_time
                })

            return {
                'success': True,
                'data': {
                    'orders': order_list,
                    'pagination': {
                        'page': page,
                        'size': size,
                        'total': total,
                        'pages': (total + size - 1) // size
                    }
                }
            }

        except Exception as e:
            logger.error(f"Get payment history error: {e}")
            return {
                'success': False,
                'message': f'获取支付历史失败: {str(e)}'
            }

    def get_payment_config_status(self) -> Dict[str, Any]:
        """获取支付配置状态"""
        return {
            'payment_enabled': settings.PAYMENT_ENABLED,
            'mock_mode': settings.PAYMENT_MOCK_MODE,
            'wechat_v2_config': self.wechat_pay.get_config_status(),
            'wechat_v3_config': self.wechat_pay_v3.get_config_status(),
            'order_timeout_hours': settings.PAYMENT_ORDER_TIMEOUT_HOURS,
            'recommended_api': 'v3'
        }


# 创建全局实例
payment_manager = PaymentManager()