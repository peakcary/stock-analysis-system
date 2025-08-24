"""
会员服务类
Membership service
"""

from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.logging import logger
from app.models.user import User
from app.models.payment import PaymentOrder, PaymentPackage, MembershipLog


class MembershipService:
    """会员服务类"""

    async def process_payment_success(self, db: Session, payment_order: PaymentOrder):
        """处理支付成功后的会员权益发放"""
        try:
            # 获取用户
            user = db.query(User).filter(User.id == payment_order.user_id).first()
            if not user:
                raise Exception(f"User not found: {payment_order.user_id}")
            
            # 获取套餐配置
            package = db.query(PaymentPackage).filter(
                PaymentPackage.package_type == payment_order.package_type
            ).first()
            if not package:
                raise Exception(f"Package not found: {payment_order.package_type}")
            
            # 记录原始状态
            old_membership_type = user.membership_type
            old_queries_remaining = user.queries_remaining
            old_expires_at = user.membership_expires_at
            
            # 根据套餐类型处理会员权益
            if package.package_type.startswith('queries_'):
                # 查询包类型 - 只增加查询次数
                user.queries_remaining += package.queries_count
                new_membership_type = user.membership_type
                new_expires_at = user.membership_expires_at
                action_type = "add_queries"
                
            else:
                # 会员套餐类型 - 升级会员并增加查询次数
                user.membership_type = package.membership_type
                user.queries_remaining += package.queries_count
                
                # 计算到期时间
                if user.membership_expires_at and user.membership_expires_at > datetime.now():
                    # 现有会员未过期，在现有基础上延长
                    new_expires_at = user.membership_expires_at + timedelta(days=package.validity_days)
                else:
                    # 新会员或已过期，从现在开始计算
                    new_expires_at = datetime.now() + timedelta(days=package.validity_days)
                
                user.membership_expires_at = new_expires_at
                new_membership_type = user.membership_type
                action_type = "upgrade" if old_membership_type != new_membership_type else "renew"
            
            # 创建会员变更日志
            membership_log = MembershipLog(
                user_id=user.id,
                payment_order_id=payment_order.id,
                action_type=action_type,
                old_membership_type=old_membership_type,
                new_membership_type=new_membership_type,
                old_queries_remaining=old_queries_remaining,
                new_queries_remaining=user.queries_remaining,
                queries_added=package.queries_count,
                old_expires_at=old_expires_at,
                new_expires_at=new_expires_at if action_type != "add_queries" else old_expires_at,
                days_added=package.validity_days if action_type != "add_queries" else 0,
                notes=f"支付成功自动处理 - 套餐: {package.name}"
            )
            
            db.add(membership_log)
            db.commit()
            
            logger.info(f"Membership processed for user {user.id}: {action_type}, "
                       f"queries: {old_queries_remaining} -> {user.queries_remaining}, "
                       f"membership: {old_membership_type} -> {new_membership_type}")
            
            return {
                "success": True,
                "action_type": action_type,
                "queries_added": package.queries_count,
                "new_queries_remaining": user.queries_remaining,
                "new_membership_type": new_membership_type.value,
                "new_expires_at": new_expires_at
            }
            
        except Exception as e:
            logger.error(f"Process payment success error: {e}")
            db.rollback()
            raise e

    async def check_membership_expiry(self, db: Session, user_id: int) -> dict:
        """检查用户会员是否过期"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"expired": False, "message": "用户不存在"}
            
            now = datetime.now()
            
            # 如果没有到期时间，说明是免费用户
            if not user.membership_expires_at:
                return {
                    "expired": False,
                    "is_member": False,
                    "membership_type": user.membership_type.value,
                    "expires_at": None
                }
            
            # 检查是否过期
            is_expired = user.membership_expires_at <= now
            
            if is_expired and user.membership_type.value != "free":
                # 降级为免费用户
                old_membership_type = user.membership_type
                user.membership_type = "free"
                
                # 记录日志
                membership_log = MembershipLog(
                    user_id=user.id,
                    action_type="expire",
                    old_membership_type=old_membership_type,
                    new_membership_type=user.membership_type,
                    old_queries_remaining=user.queries_remaining,
                    new_queries_remaining=user.queries_remaining,
                    old_expires_at=user.membership_expires_at,
                    new_expires_at=None,
                    notes="会员到期自动降级"
                )
                
                db.add(membership_log)
                db.commit()
                
                logger.info(f"User {user_id} membership expired and downgraded to free")
                
                return {
                    "expired": True,
                    "is_member": False,
                    "membership_type": "free",
                    "expires_at": None,
                    "message": "会员已过期，已自动降级为免费用户"
                }
            
            return {
                "expired": is_expired,
                "is_member": not is_expired,
                "membership_type": user.membership_type.value,
                "expires_at": user.membership_expires_at,
                "days_remaining": (user.membership_expires_at - now).days if not is_expired else 0
            }
            
        except Exception as e:
            logger.error(f"Check membership expiry error: {e}")
            raise e

    async def manual_upgrade_membership(
        self,
        db: Session,
        user_id: int,
        membership_type: str,
        queries_to_add: int,
        days_to_add: int,
        operator_id: Optional[int] = None,
        notes: Optional[str] = None
    ) -> dict:
        """手动升级用户会员"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise Exception(f"User not found: {user_id}")
            
            # 记录原始状态
            old_membership_type = user.membership_type
            old_queries_remaining = user.queries_remaining
            old_expires_at = user.membership_expires_at
            
            # 更新会员类型
            if membership_type and membership_type != user.membership_type.value:
                user.membership_type = membership_type
            
            # 增加查询次数
            if queries_to_add > 0:
                user.queries_remaining += queries_to_add
            
            # 延长会员时间
            if days_to_add > 0:
                if user.membership_expires_at and user.membership_expires_at > datetime.now():
                    # 在现有基础上延长
                    user.membership_expires_at += timedelta(days=days_to_add)
                else:
                    # 从现在开始计算
                    user.membership_expires_at = datetime.now() + timedelta(days=days_to_add)
            
            # 创建会员变更日志
            membership_log = MembershipLog(
                user_id=user.id,
                action_type="manual",
                old_membership_type=old_membership_type,
                new_membership_type=user.membership_type,
                old_queries_remaining=old_queries_remaining,
                new_queries_remaining=user.queries_remaining,
                queries_added=queries_to_add,
                old_expires_at=old_expires_at,
                new_expires_at=user.membership_expires_at,
                days_added=days_to_add,
                operator_id=operator_id,
                notes=notes or "管理员手动操作"
            )
            
            db.add(membership_log)
            db.commit()
            
            logger.info(f"Manual membership upgrade for user {user_id} by operator {operator_id}")
            
            return {
                "success": True,
                "old_membership_type": old_membership_type.value,
                "new_membership_type": user.membership_type.value,
                "queries_added": queries_to_add,
                "days_added": days_to_add,
                "new_queries_remaining": user.queries_remaining,
                "new_expires_at": user.membership_expires_at
            }
            
        except Exception as e:
            logger.error(f"Manual upgrade membership error: {e}")
            db.rollback()
            raise e

    async def get_membership_logs(
        self,
        db: Session,
        user_id: int,
        limit: int = 50
    ) -> list:
        """获取用户会员变更日志"""
        try:
            logs = db.query(MembershipLog).filter(
                MembershipLog.user_id == user_id
            ).order_by(MembershipLog.created_at.desc()).limit(limit).all()
            
            return logs
            
        except Exception as e:
            logger.error(f"Get membership logs error: {e}")
            raise e

    async def consume_query(self, db: Session, user_id: int) -> dict:
        """消费一次查询"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise Exception(f"User not found: {user_id}")
            
            # 检查会员是否过期
            await self.check_membership_expiry(db, user_id)
            # 重新获取用户信息（可能已被更新）
            db.refresh(user)
            
            # 检查查询次数
            if user.queries_remaining <= 0:
                return {
                    "success": False,
                    "message": "查询次数不足",
                    "queries_remaining": 0
                }
            
            # 减少查询次数
            user.queries_remaining -= 1
            db.commit()
            
            logger.info(f"Query consumed for user {user_id}, remaining: {user.queries_remaining}")
            
            return {
                "success": True,
                "message": "查询成功",
                "queries_remaining": user.queries_remaining
            }
            
        except Exception as e:
            logger.error(f"Consume query error: {e}")
            db.rollback()
            raise e


# 创建全局实例
membership_service = MembershipService()