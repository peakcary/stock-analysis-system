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

    async def get_payment_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[int] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """获取支付统计数据"""
        try:
            # 设置默认时间范围（最近30天）
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                start_date = end_date - timedelta(days=30)

            # 基础查询条件
            query_conditions = [
                PaymentOrder.created_at >= start_date,
                PaymentOrder.created_at <= end_date
            ]

            if user_id:
                query_conditions.append(PaymentOrder.user_id == user_id)

            base_query = db.query(PaymentOrder).filter(and_(*query_conditions))

            # 总体统计
            total_orders = base_query.count()
            paid_orders = base_query.filter(PaymentOrder.status == PaymentStatus.PAID).count()
            pending_orders = base_query.filter(PaymentOrder.status == PaymentStatus.PENDING).count()
            failed_orders = base_query.filter(PaymentOrder.status == PaymentStatus.FAILED).count()
            cancelled_orders = base_query.filter(PaymentOrder.status == PaymentStatus.CANCELLED).count()
            expired_orders = base_query.filter(PaymentOrder.status == PaymentStatus.EXPIRED).count()

            # 金额统计
            paid_query = base_query.filter(PaymentOrder.status == PaymentStatus.PAID)
            total_revenue_result = paid_query.with_entities(func.sum(PaymentOrder.amount)).scalar()
            total_revenue = float(total_revenue_result or 0)

            average_order_result = paid_query.with_entities(func.avg(PaymentOrder.amount)).scalar()
            average_order_value = float(average_order_result or 0)

            # 按支付方式统计
            payment_method_stats = db.query(
                PaymentOrder.payment_method,
                func.count(PaymentOrder.id).label('count'),
                func.sum(PaymentOrder.amount).label('total_amount')
            ).filter(
                and_(*query_conditions),
                PaymentOrder.status == PaymentStatus.PAID
            ).group_by(PaymentOrder.payment_method).all()

            method_statistics = {}
            for method, count, amount in payment_method_stats:
                method_statistics[method] = {
                    'orders': count,
                    'revenue': float(amount or 0)
                }

            # 按套餐统计
            package_stats = db.query(
                PaymentOrder.package_type,
                PaymentOrder.package_name,
                func.count(PaymentOrder.id).label('count'),
                func.sum(PaymentOrder.amount).label('total_amount')
            ).filter(
                and_(*query_conditions),
                PaymentOrder.status == PaymentStatus.PAID
            ).group_by(
                PaymentOrder.package_type, PaymentOrder.package_name
            ).all()

            package_statistics = {}
            for pkg_type, pkg_name, count, amount in package_stats:
                package_statistics[pkg_type] = {
                    'name': pkg_name,
                    'orders': count,
                    'revenue': float(amount or 0)
                }

            # 按日期统计（最近7天）
            daily_stats = []
            for i in range(7):
                date = (end_date - timedelta(days=i)).date()
                date_start = datetime.combine(date, datetime.min.time())
                date_end = datetime.combine(date, datetime.max.time())

                daily_query = base_query.filter(
                    and_(
                        PaymentOrder.created_at >= date_start,
                        PaymentOrder.created_at <= date_end
                    )
                )

                daily_total = daily_query.count()
                daily_paid = daily_query.filter(PaymentOrder.status == PaymentStatus.PAID).count()
                daily_revenue_result = daily_query.filter(PaymentOrder.status == PaymentStatus.PAID).with_entities(
                    func.sum(PaymentOrder.amount)
                ).scalar()
                daily_revenue = float(daily_revenue_result or 0)

                daily_stats.append({
                    'date': date.isoformat(),
                    'total_orders': daily_total,
                    'paid_orders': daily_paid,
                    'revenue': daily_revenue,
                    'conversion_rate': (daily_paid / daily_total * 100) if daily_total > 0 else 0
                })

            # 计算转化率和其他指标
            conversion_rate = (paid_orders / total_orders * 100) if total_orders > 0 else 0
            success_rate = (paid_orders / (total_orders - pending_orders) * 100) if (total_orders - pending_orders) > 0 else 0

            # 最近成功交易
            recent_successful_orders = base_query.filter(
                PaymentOrder.status == PaymentStatus.PAID
            ).order_by(PaymentOrder.paid_at.desc()).limit(10).all()

            recent_orders = []
            for order in recent_successful_orders:
                recent_orders.append({
                    'out_trade_no': order.out_trade_no,
                    'package_name': order.package_name,
                    'amount': float(order.amount),
                    'paid_at': order.paid_at,
                    'user_id': order.user_id
                })

            return {
                'success': True,
                'data': {
                    'query_period': {
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat(),
                        'days': (end_date - start_date).days
                    },
                    'overview': {
                        'total_orders': total_orders,
                        'paid_orders': paid_orders,
                        'pending_orders': pending_orders,
                        'failed_orders': failed_orders,
                        'cancelled_orders': cancelled_orders,
                        'expired_orders': expired_orders,
                        'total_revenue': total_revenue,
                        'average_order_value': average_order_value,
                        'conversion_rate': round(conversion_rate, 2),
                        'success_rate': round(success_rate, 2)
                    },
                    'payment_methods': method_statistics,
                    'packages': package_statistics,
                    'daily_trends': list(reversed(daily_stats)),  # 按时间正序
                    'recent_orders': recent_orders
                }
            }

        except Exception as e:
            logger.error(f"Get payment statistics error: {e}")
            return {
                'success': False,
                'message': f'获取支付统计失败: {str(e)}'
            }

    async def get_user_payment_summary(
        self,
        user_id: int,
        db: Session = None
    ) -> Dict[str, Any]:
        """获取用户支付汇总信息"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {
                    'success': False,
                    'message': '用户不存在'
                }

            # 用户订单统计
            user_orders = db.query(PaymentOrder).filter(PaymentOrder.user_id == user_id)

            total_orders = user_orders.count()
            paid_orders = user_orders.filter(PaymentOrder.status == PaymentStatus.PAID).count()
            total_spent_result = user_orders.filter(PaymentOrder.status == PaymentStatus.PAID).with_entities(
                func.sum(PaymentOrder.amount)
            ).scalar()
            total_spent = float(total_spent_result or 0)

            # 最近订单
            recent_order = user_orders.filter(
                PaymentOrder.status == PaymentStatus.PAID
            ).order_by(PaymentOrder.paid_at.desc()).first()

            # 用户会员记录统计
            membership_logs = db.query(MembershipLog).filter(MembershipLog.user_id == user_id)
            total_queries_added = membership_logs.with_entities(
                func.sum(MembershipLog.queries_added)
            ).scalar() or 0
            total_days_added = membership_logs.with_entities(
                func.sum(MembershipLog.days_added)
            ).scalar() or 0

            return {
                'success': True,
                'data': {
                    'user_info': {
                        'id': user.id,
                        'username': user.username,
                        'membership_type': user.membership_type,
                        'queries_remaining': user.queries_remaining,
                        'membership_expires_at': user.membership_expires_at
                    },
                    'payment_summary': {
                        'total_orders': total_orders,
                        'successful_orders': paid_orders,
                        'total_spent': total_spent,
                        'average_order_value': (total_spent / paid_orders) if paid_orders > 0 else 0,
                        'total_queries_purchased': total_queries_added,
                        'total_days_purchased': total_days_added
                    },
                    'recent_activity': {
                        'last_payment_date': recent_order.paid_at if recent_order else None,
                        'last_package': recent_order.package_name if recent_order else None,
                        'last_amount': float(recent_order.amount) if recent_order else 0
                    }
                }
            }

        except Exception as e:
            logger.error(f"Get user payment summary error: {e}")
            return {
                'success': False,
                'message': f'获取用户支付汇总失败: {str(e)}'
            }

    async def get_payment_analytics(
        self,
        period_days: int = 30,
        db: Session = None
    ) -> Dict[str, Any]:
        """获取支付分析数据"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=period_days)

            # 时段分析（按小时）
            hourly_stats = db.query(
                func.extract('hour', PaymentOrder.created_at).label('hour'),
                func.count(PaymentOrder.id).label('order_count'),
                func.sum(
                    func.case([(PaymentOrder.status == PaymentStatus.PAID, 1)], else_=0)
                ).label('paid_count')
            ).filter(
                and_(
                    PaymentOrder.created_at >= start_date,
                    PaymentOrder.created_at <= end_date
                )
            ).group_by(func.extract('hour', PaymentOrder.created_at)).all()

            hourly_data = {}
            for hour, order_count, paid_count in hourly_stats:
                hourly_data[int(hour)] = {
                    'total_orders': order_count,
                    'paid_orders': int(paid_count),
                    'conversion_rate': (paid_count / order_count * 100) if order_count > 0 else 0
                }

            # 失败原因分析
            failed_orders = db.query(PaymentOrder).filter(
                and_(
                    PaymentOrder.created_at >= start_date,
                    PaymentOrder.created_at <= end_date,
                    PaymentOrder.status.in_([PaymentStatus.FAILED, PaymentStatus.CANCELLED, PaymentStatus.EXPIRED])
                )
            ).all()

            failure_analysis = {
                PaymentStatus.FAILED: 0,
                PaymentStatus.CANCELLED: 0,
                PaymentStatus.EXPIRED: 0
            }

            for order in failed_orders:
                if order.status in failure_analysis:
                    failure_analysis[order.status] += 1

            # 支付时长分析（从创建到支付成功的时间）
            paid_orders_with_time = db.query(PaymentOrder).filter(
                and_(
                    PaymentOrder.created_at >= start_date,
                    PaymentOrder.created_at <= end_date,
                    PaymentOrder.status == PaymentStatus.PAID,
                    PaymentOrder.paid_at.isnot(None)
                )
            ).all()

            payment_durations = []
            for order in paid_orders_with_time:
                duration = (order.paid_at - order.created_at).total_seconds() / 60  # 分钟
                payment_durations.append(duration)

            duration_stats = {}
            if payment_durations:
                import statistics
                duration_stats = {
                    'min_minutes': min(payment_durations),
                    'max_minutes': max(payment_durations),
                    'avg_minutes': statistics.mean(payment_durations),
                    'median_minutes': statistics.median(payment_durations),
                    'count': len(payment_durations)
                }

            return {
                'success': True,
                'data': {
                    'period': {
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat(),
                        'days': period_days
                    },
                    'hourly_distribution': hourly_data,
                    'failure_analysis': failure_analysis,
                    'payment_duration': duration_stats,
                    'insights': {
                        'peak_hour': max(hourly_data.keys(), key=lambda h: hourly_data[h]['paid_orders']) if hourly_data else None,
                        'best_conversion_hour': max(hourly_data.keys(), key=lambda h: hourly_data[h]['conversion_rate']) if hourly_data else None,
                        'total_failed_rate': (sum(failure_analysis.values()) / len(paid_orders_with_time + failed_orders) * 100) if (paid_orders_with_time or failed_orders) else 0
                    }
                }
            }

        except Exception as e:
            logger.error(f"Get payment analytics error: {e}")
            return {
                'success': False,
                'message': f'获取支付分析失败: {str(e)}'
            }

    def validate_payment_security(self, request_data: dict, client_ip: str = "") -> Dict[str, Any]:
        """验证支付请求的安全性"""
        try:
            security_warnings = []
            security_score = 100

            # 检查IP地址
            if not client_ip or client_ip == "127.0.0.1":
                security_warnings.append("缺少有效的客户端IP地址")
                security_score -= 15

            # 检查请求频率（简单实现，生产环境需要使用Redis等）
            if hasattr(self, '_request_cache'):
                recent_requests = self._request_cache.get(client_ip, [])
                current_time = datetime.now()
                # 清理1分钟前的请求
                recent_requests = [req_time for req_time in recent_requests
                                 if (current_time - req_time).seconds < 60]

                if len(recent_requests) > 5:  # 1分钟内超过5次请求
                    security_warnings.append("请求频率过高，可能存在恶意行为")
                    security_score -= 25

                recent_requests.append(current_time)
                self._request_cache[client_ip] = recent_requests
            else:
                self._request_cache = {client_ip: [datetime.now()]}

            # 检查金额合理性
            if 'amount' in request_data:
                amount = float(request_data.get('amount', 0))
                if amount <= 0:
                    security_warnings.append("支付金额无效")
                    security_score -= 30
                elif amount > 10000:  # 金额过大
                    security_warnings.append("支付金额异常高，需要额外验证")
                    security_score -= 10

            # 检查用户行为
            if 'user_id' in request_data:
                user_id = request_data.get('user_id')
                if not isinstance(user_id, int) or user_id <= 0:
                    security_warnings.append("用户ID无效")
                    security_score -= 20

            # 检查套餐类型
            if 'package_type' in request_data:
                package_type = request_data.get('package_type', '')
                if not package_type or not isinstance(package_type, str):
                    security_warnings.append("套餐类型无效")
                    security_score -= 15

            # 计算安全等级
            if security_score >= 90:
                security_level = 'HIGH'
            elif security_score >= 70:
                security_level = 'MEDIUM'
            elif security_score >= 50:
                security_level = 'LOW'
            else:
                security_level = 'CRITICAL'

            return {
                'success': True,
                'security_level': security_level,
                'security_score': security_score,
                'warnings': security_warnings,
                'allow_payment': security_score >= 50,  # 50分以上才允许支付
                'require_additional_verification': security_score < 80
            }

        except Exception as e:
            logger.error(f"Validate payment security error: {e}")
            return {
                'success': False,
                'security_level': 'CRITICAL',
                'security_score': 0,
                'warnings': [f'安全验证异常: {str(e)}'],
                'allow_payment': False,
                'require_additional_verification': True
            }

    def detect_suspicious_activity(self, user_id: int, db: Session = None) -> Dict[str, Any]:
        """检测可疑支付活动"""
        try:
            suspicious_indicators = []
            risk_score = 0

            # 检查短时间内大量订单
            recent_time = datetime.now() - timedelta(hours=1)
            recent_orders = db.query(PaymentOrder).filter(
                and_(
                    PaymentOrder.user_id == user_id,
                    PaymentOrder.created_at >= recent_time
                )
            ).count()

            if recent_orders > 5:
                suspicious_indicators.append("短时间内创建大量订单")
                risk_score += 30

            # 检查异常支付模式
            user_orders = db.query(PaymentOrder).filter(
                PaymentOrder.user_id == user_id
            ).order_by(PaymentOrder.created_at.desc()).limit(10).all()

            if len(user_orders) > 1:
                # 检查连续失败的订单
                consecutive_failures = 0
                for order in user_orders:
                    if order.status in [PaymentStatus.FAILED, PaymentStatus.CANCELLED]:
                        consecutive_failures += 1
                    else:
                        break

                if consecutive_failures >= 3:
                    suspicious_indicators.append("连续支付失败")
                    risk_score += 25

                # 检查金额异常
                amounts = [float(order.amount) for order in user_orders]
                if amounts:
                    avg_amount = sum(amounts) / len(amounts)
                    max_amount = max(amounts)
                    if max_amount > avg_amount * 5:  # 金额异常高
                        suspicious_indicators.append("支付金额异常")
                        risk_score += 20

            # 检查IP地址异常（简单实现）
            unique_ips = set()
            for order in user_orders:
                if order.client_ip:
                    unique_ips.add(order.client_ip)

            if len(unique_ips) > 3:  # 使用过多IP地址
                suspicious_indicators.append("使用多个IP地址")
                risk_score += 15

            # 计算风险等级
            if risk_score >= 50:
                risk_level = 'HIGH'
            elif risk_score >= 30:
                risk_level = 'MEDIUM'
            elif risk_score >= 10:
                risk_level = 'LOW'
            else:
                risk_level = 'NORMAL'

            return {
                'success': True,
                'risk_level': risk_level,
                'risk_score': risk_score,
                'suspicious_indicators': suspicious_indicators,
                'recommend_action': self._get_risk_action_recommendation(risk_level),
                'require_manual_review': risk_score >= 50
            }

        except Exception as e:
            logger.error(f"Detect suspicious activity error: {e}")
            return {
                'success': False,
                'risk_level': 'HIGH',
                'risk_score': 100,
                'suspicious_indicators': [f'检测异常: {str(e)}'],
                'recommend_action': 'BLOCK',
                'require_manual_review': True
            }

    def _get_risk_action_recommendation(self, risk_level: str) -> str:
        """获取风险处理建议"""
        recommendations = {
            'NORMAL': 'ALLOW',
            'LOW': 'MONITOR',
            'MEDIUM': 'ADDITIONAL_VERIFICATION',
            'HIGH': 'BLOCK'
        }
        return recommendations.get(risk_level, 'BLOCK')

    async def enhanced_create_payment_order(
        self,
        user: User,
        package_type: str,
        payment_method: str = PaymentMethod.WECHAT_NATIVE,
        client_ip: str = "127.0.0.1",
        user_agent: str = "",
        db: Session = None
    ) -> Dict[str, Any]:
        """增强安全的创建支付订单"""
        try:
            # 安全验证
            security_check = self.validate_payment_security({
                'user_id': user.id,
                'package_type': package_type,
                'client_ip': client_ip
            }, client_ip)

            if not security_check.get('allow_payment', False):
                return {
                    'success': False,
                    'message': '安全验证失败，无法创建订单',
                    'error_type': 'security_violation',
                    'security_info': security_check
                }

            # 可疑活动检测
            suspicious_check = self.detect_suspicious_activity(user.id, db)
            if suspicious_check.get('require_manual_review', False):
                logger.warning(f"Suspicious activity detected for user {user.id}: {suspicious_check}")

            # 如果安全检查通过，继续原有的订单创建流程
            result = await self.create_payment_order(
                user=user,
                package_type=package_type,
                payment_method=payment_method,
                client_ip=client_ip,
                user_agent=user_agent,
                db=db
            )

            # 添加安全信息到返回结果
            if result.get('success'):
                result['security_info'] = {
                    'security_level': security_check.get('security_level'),
                    'risk_level': suspicious_check.get('risk_level'),
                    'additional_verification_required': security_check.get('require_additional_verification', False)
                }

            return result

        except Exception as e:
            logger.error(f"Enhanced create payment order error: {e}")
            return {
                'success': False,
                'message': f'创建订单失败: {str(e)}',
                'error_type': 'system_error'
            }

    def get_security_status(self) -> Dict[str, Any]:
        """获取支付安全状态"""
        return {
            'security_features': {
                'signature_verification': True,
                'data_encryption': True,
                'timeout_handling': True,
                'ip_validation': True,
                'frequency_limiting': True,
                'amount_validation': True,
                'suspicious_activity_detection': True
            },
            'security_policies': {
                'max_requests_per_minute': 5,
                'max_payment_amount': 10000.0,
                'order_timeout_hours': settings.PAYMENT_ORDER_TIMEOUT_HOURS,
                'require_https': True,
                'min_security_score': 50
            },
            'monitoring': {
                'real_time_detection': True,
                'audit_logging': True,
                'alert_system': True
            }
        }


# 创建全局实例
payment_manager = PaymentManager()