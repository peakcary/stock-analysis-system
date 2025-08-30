"""
用户会员权限管理服务
User Membership Management Service
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.core.database import get_db
from app.core.logging import logger
from app.models.user import User
from app.models.payment import PaymentOrder, PaymentPackage, PaymentStatus


class UserMembershipService:
    """用户会员权限管理服务"""
    
    def __init__(self):
        # 默认权限配置
        self.membership_limits = {
            'free': {
                'queries_per_day': 5,
                'queries_per_month': 50,
                'access_features': ['basic_stock_info', 'basic_analysis'],
                'description': '免费用户'
            },
            'pro': {
                'queries_per_day': 100,
                'queries_per_month': 2000,
                'access_features': ['basic_stock_info', 'basic_analysis', 'advanced_analysis', 'trend_prediction'],
                'description': '专业用户'
            },
            'premium': {
                'queries_per_day': -1,  # 无限制
                'queries_per_month': -1,
                'access_features': ['basic_stock_info', 'basic_analysis', 'advanced_analysis', 'trend_prediction', 'ai_insight', 'portfolio_management'],
                'description': '高级用户'
            }
        }
    
    async def get_user_membership_status(self, db: Session, user_id: int) -> Dict[str, Any]:
        """获取用户会员状态"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {
                    'error': '用户不存在',
                    'user_id': user_id
                }
            
            # 获取用户当前有效的付费订单
            current_time = datetime.now()
            active_orders = db.query(PaymentOrder).join(PaymentPackage).filter(
                and_(
                    PaymentOrder.user_id == user_id,
                    PaymentOrder.status == PaymentStatus.PAID,
                    or_(
                        PaymentOrder.expire_time.is_(None),
                        PaymentOrder.expire_time > current_time
                    )
                )
            ).order_by(PaymentOrder.paid_at.desc()).all()
            
            # 确定用户当前的会员类型（取最高级别）
            current_membership = 'free'
            active_until = None
            active_package_info = None
            
            for order in active_orders:
                package_membership = order.payment_package.membership_type.lower()
                
                # 会员等级优先级：premium > pro > free
                if (package_membership == 'premium' or 
                    (package_membership == 'pro' and current_membership == 'free')):
                    current_membership = package_membership
                    active_until = order.expire_time
                    active_package_info = {
                        'package_name': order.payment_package.name,
                        'package_type': order.payment_package.package_type,
                        'queries_count': order.payment_package.queries_count,
                        'validity_days': order.payment_package.validity_days,
                        'purchased_at': order.paid_at.isoformat() if order.paid_at else None,
                        'expires_at': order.expire_time.isoformat() if order.expire_time else None
                    }
            
            # 获取权限配置
            membership_config = self.membership_limits.get(current_membership, self.membership_limits['free'])
            
            # 计算今日和本月已使用的查询次数（这里可以扩展为实际的查询记录统计）
            today = datetime.now().date()
            month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            # TODO: 实际项目中应该从查询记录表中统计
            queries_today = 0
            queries_this_month = 0
            
            return {
                'user_id': user_id,
                'username': user.username,
                'current_membership': current_membership,
                'membership_config': membership_config,
                'active_until': active_until.isoformat() if active_until else None,
                'is_active': active_until is None or active_until > current_time,
                'active_package_info': active_package_info,
                'usage_stats': {
                    'queries_today': queries_today,
                    'queries_this_month': queries_this_month,
                    'remaining_today': membership_config['queries_per_day'] - queries_today if membership_config['queries_per_day'] > 0 else -1,
                    'remaining_month': membership_config['queries_per_month'] - queries_this_month if membership_config['queries_per_month'] > 0 else -1
                },
                'permissions': {
                    'can_query': self._can_make_query(membership_config, queries_today, queries_this_month),
                    'access_features': membership_config['access_features'],
                    'queries_per_day_limit': membership_config['queries_per_day'],
                    'queries_per_month_limit': membership_config['queries_per_month']
                }
            }
            
        except Exception as e:
            logger.error(f"Get user membership status error: {e}")
            return {
                'error': str(e),
                'user_id': user_id
            }
    
    def _can_make_query(self, membership_config: Dict[str, Any], queries_today: int, queries_this_month: int) -> bool:
        """检查用户是否可以进行查询"""
        daily_limit = membership_config['queries_per_day']
        monthly_limit = membership_config['queries_per_month']
        
        # -1 表示无限制
        if daily_limit == -1 and monthly_limit == -1:
            return True
        
        if daily_limit > 0 and queries_today >= daily_limit:
            return False
        
        if monthly_limit > 0 and queries_this_month >= monthly_limit:
            return False
        
        return True
    
    async def activate_package_for_user(self, db: Session, user_id: int, payment_order_id: int) -> Dict[str, Any]:
        """为用户激活套餐权限"""
        try:
            # 获取支付订单
            payment_order = db.query(PaymentOrder).filter(
                and_(
                    PaymentOrder.id == payment_order_id,
                    PaymentOrder.user_id == user_id,
                    PaymentOrder.status == PaymentStatus.PAID
                )
            ).first()
            
            if not payment_order:
                return {
                    'success': False,
                    'message': '未找到有效的支付订单'
                }
            
            # 设置套餐有效期
            if payment_order.payment_package.validity_days > 0:
                payment_order.expire_time = datetime.now() + timedelta(days=payment_order.payment_package.validity_days)
            else:
                # 永久有效
                payment_order.expire_time = None
            
            db.commit()
            
            logger.info(f"Package activated for user {user_id}: {payment_order.payment_package.name}")
            
            return {
                'success': True,
                'message': '套餐权限激活成功',
                'package_info': {
                    'package_name': payment_order.payment_package.name,
                    'membership_type': payment_order.payment_package.membership_type,
                    'queries_count': payment_order.payment_package.queries_count,
                    'validity_days': payment_order.payment_package.validity_days,
                    'expires_at': payment_order.expire_time.isoformat() if payment_order.expire_time else None
                }
            }
            
        except Exception as e:
            logger.error(f"Activate package error: {e}")
            db.rollback()
            return {
                'success': False,
                'message': f'激活套餐失败: {e}'
            }
    
    async def check_feature_access(self, db: Session, user_id: int, feature_name: str) -> bool:
        """检查用户是否有访问特定功能的权限"""
        membership_status = await self.get_user_membership_status(db, user_id)
        
        if 'error' in membership_status:
            return False
        
        return feature_name in membership_status['permissions']['access_features']
    
    async def record_query_usage(self, db: Session, user_id: int, query_type: str = 'api') -> Dict[str, Any]:
        """记录用户查询使用情况"""
        try:
            # TODO: 实际项目中应该记录到查询使用记录表
            # 这里可以创建一个 QueryUsageRecord 模型来记录用户的查询使用情况
            
            logger.info(f"Query usage recorded for user {user_id}: {query_type}")
            
            return {
                'success': True,
                'message': '查询记录成功',
                'user_id': user_id,
                'query_type': query_type,
                'recorded_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Record query usage error: {e}")
            return {
                'success': False,
                'message': f'记录查询失败: {e}'
            }
    
    async def get_user_purchase_history(self, db: Session, user_id: int) -> List[Dict[str, Any]]:
        """获取用户购买历史"""
        try:
            orders = db.query(PaymentOrder).join(PaymentPackage).filter(
                PaymentOrder.user_id == user_id
            ).order_by(PaymentOrder.created_at.desc()).all()
            
            purchase_history = []
            for order in orders:
                purchase_history.append({
                    'order_id': order.id,
                    'out_trade_no': order.out_trade_no,
                    'package_name': order.payment_package.name,
                    'package_type': order.payment_package.package_type,
                    'membership_type': order.payment_package.membership_type,
                    'amount': float(order.amount),
                    'status': order.status.value.lower(),
                    'payment_method': order.payment_method.value.lower(),
                    'created_at': order.created_at.isoformat(),
                    'paid_at': order.paid_at.isoformat() if order.paid_at else None,
                    'expire_time': order.expire_time.isoformat() if order.expire_time else None,
                    'is_active': order.expire_time is None or order.expire_time > datetime.now() if order.status == PaymentStatus.PAID else False
                })
            
            return purchase_history
            
        except Exception as e:
            logger.error(f"Get purchase history error: {e}")
            return []
    
    async def upgrade_membership_limits(self, membership_type: str, new_limits: Dict[str, Any]) -> bool:
        """更新会员权限配置（管理员功能）"""
        try:
            if membership_type in self.membership_limits:
                self.membership_limits[membership_type].update(new_limits)
                logger.info(f"Membership limits updated for {membership_type}: {new_limits}")
                return True
            else:
                logger.warning(f"Unknown membership type: {membership_type}")
                return False
                
        except Exception as e:
            logger.error(f"Update membership limits error: {e}")
            return False


# 创建全局实例
user_membership_service = UserMembershipService()