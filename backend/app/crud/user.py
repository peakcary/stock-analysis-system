"""
用户相关的数据库操作
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.user import User, UserQuery, Payment, MembershipType, QueryType
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password
from datetime import datetime, timedelta


class UserCRUD:
    """用户CRUD操作类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user(self, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """获取用户列表"""
        return self.db.query(User).offset(skip).limit(limit).all()
    
    def create_user(self, user_create: UserCreate) -> User:
        """创建用户"""
        # 检查用户名和邮箱是否已存在
        if self.get_user_by_username(user_create.username):
            raise ValueError("Username already registered")
        
        if self.get_user_by_email(user_create.email):
            raise ValueError("Email already registered")
        
        # 创建用户
        hashed_password = get_password_hash(user_create.password)
        db_user = User(
            username=user_create.username,
            email=user_create.email,
            password_hash=hashed_password,
            membership_type=MembershipType.FREE,
            queries_remaining=10  # 免费用户默认10次查询
        )
        
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        
        return db_user
    
    def update_user(self, user_id: int, user_update: UserUpdate) -> Optional[User]:
        """更新用户信息"""
        db_user = self.get_user(user_id)
        if not db_user:
            return None
        
        update_data = user_update.dict(exclude_unset=True)
        
        # 检查用户名是否已存在
        if 'username' in update_data:
            existing_user = self.get_user_by_username(update_data['username'])
            if existing_user and existing_user.id != user_id:
                raise ValueError("Username already taken")
        
        # 检查邮箱是否已存在
        if 'email' in update_data:
            existing_user = self.get_user_by_email(update_data['email'])
            if existing_user and existing_user.id != user_id:
                raise ValueError("Email already taken")
        
        # 处理密码更新
        if 'password' in update_data:
            update_data['password_hash'] = get_password_hash(update_data.pop('password'))
        
        # 更新用户信息
        for field, value in update_data.items():
            setattr(db_user, field, value)
        
        self.db.commit()
        self.db.refresh(db_user)
        
        return db_user
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """验证用户身份"""
        user = self.get_user_by_username(username)
        if not user:
            return None
        
        if not verify_password(password, user.password_hash):
            return None
        
        return user
    
    def consume_query(self, user_id: int, query_type: QueryType, query_params: dict = None) -> bool:
        """消费用户查询次数"""
        user = self.get_user(user_id)
        if not user or user.queries_remaining <= 0:
            return False
        
        # 减少查询次数
        user.queries_remaining -= 1
        
        # 记录查询
        query_record = UserQuery(
            user_id=user_id,
            query_type=query_type,
            query_params=query_params
        )
        
        self.db.add(query_record)
        self.db.commit()
        self.db.refresh(user)
        
        return True
    
    def upgrade_membership(self, user_id: int, membership_type: MembershipType, queries_to_add: int = 0, days_to_add: int = 0) -> Optional[User]:
        """升级用户会员"""
        user = self.get_user(user_id)
        if not user:
            return None
        
        # 更新会员类型
        user.membership_type = membership_type
        
        # 添加查询次数
        if queries_to_add > 0:
            user.queries_remaining += queries_to_add
        
        # 设置会员到期时间
        if days_to_add > 0:
            if user.membership_expires_at and user.membership_expires_at > datetime.now():
                # 如果还有剩余时间，则在原基础上延长
                user.membership_expires_at += timedelta(days=days_to_add)
            else:
                # 否则从现在开始计算
                user.membership_expires_at = datetime.now() + timedelta(days=days_to_add)
        
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def get_user_queries(self, user_id: int, skip: int = 0, limit: int = 50) -> List[UserQuery]:
        """获取用户查询记录"""
        return (
            self.db.query(UserQuery)
            .filter(UserQuery.user_id == user_id)
            .order_by(UserQuery.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_user_payments(self, user_id: int, skip: int = 0, limit: int = 50) -> List[Payment]:
        """获取用户支付记录"""
        return (
            self.db.query(Payment)
            .filter(Payment.user_id == user_id)
            .order_by(Payment.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def check_membership_expired(self, user_id: int) -> bool:
        """检查会员是否过期"""
        user = self.get_user(user_id)
        if not user or not user.membership_expires_at:
            return False
        
        return user.membership_expires_at < datetime.now()
    
    def reset_expired_memberships(self):
        """重置过期会员"""
        expired_users = (
            self.db.query(User)
            .filter(
                and_(
                    User.membership_expires_at.isnot(None),
                    User.membership_expires_at < datetime.now(),
                    User.membership_type != MembershipType.FREE
                )
            )
            .all()
        )
        
        for user in expired_users:
            user.membership_type = MembershipType.FREE
            user.queries_remaining = 10  # 重置为免费用户的查询次数
            user.membership_expires_at = None
        
        self.db.commit()
        
        return len(expired_users)
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """根据ID获取用户（管理员专用）"""
        return self.get_user(user_id)
    
    def get_users_with_filters(self, skip: int = 0, limit: int = 50, search: Optional[str] = None, membership_type: Optional[str] = None) -> tuple[List[User], int]:
        """获取用户列表（支持筛选）"""
        query = self.db.query(User)
        
        # 搜索过滤
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                (User.username.ilike(search_filter)) | 
                (User.email.ilike(search_filter))
            )
        
        # 会员类型过滤
        if membership_type:
            try:
                membership_enum = MembershipType(membership_type)
                query = query.filter(User.membership_type == membership_enum)
            except ValueError:
                pass  # 忽略无效的会员类型
        
        # 获取总数
        total = query.count()
        
        # 分页获取用户
        users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
        
        return users, total
    
    def delete_user(self, user_id: int) -> bool:
        """删除用户"""
        user = self.get_user(user_id)
        if not user:
            return False
        
        try:
            self.db.delete(user)
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            return False
    
    def get_user_stats(self) -> dict:
        """获取用户统计信息"""
        from sqlalchemy import func, text
        from datetime import date
        
        # 基础统计
        total_users = self.db.query(func.count(User.id)).scalar() or 0
        free_users = self.db.query(func.count(User.id)).filter(User.membership_type == MembershipType.FREE).scalar() or 0
        paid_users = total_users - free_users
        
        # 会员类型统计
        monthly_users = self.db.query(func.count(User.id)).filter(User.membership_type == MembershipType.MONTHLY).scalar() or 0
        yearly_users = self.db.query(func.count(User.id)).filter(User.membership_type == MembershipType.YEARLY).scalar() or 0
        
        # 今日统计
        today = date.today()
        new_users_today = (
            self.db.query(func.count(User.id))
            .filter(func.date(User.created_at) == today)
            .scalar() or 0
        )
        
        total_queries_today = (
            self.db.query(func.count(UserQuery.id))
            .filter(func.date(UserQuery.created_at) == today)
            .scalar() or 0
        )
        
        total_payments_today = (
            self.db.query(func.sum(Payment.amount))
            .filter(
                (func.date(Payment.created_at) == today) &
                (Payment.payment_status == 'completed')
            )
            .scalar() or 0.0
        )
        
        return {
            "total_users": total_users,
            "free_users": free_users,
            "paid_users": paid_users,
            "monthly_users": monthly_users,
            "yearly_users": yearly_users,
            "total_queries_today": total_queries_today,
            "total_payments_today": float(total_payments_today),
            "new_users_today": new_users_today
        }