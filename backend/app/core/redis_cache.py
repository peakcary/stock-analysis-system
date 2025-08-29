"""
Redis缓存配置和工具函数
Redis Cache Configuration and Utilities
"""

import redis
import json
import pickle
from typing import Any, Optional, Union
from datetime import timedelta
from app.core.config import settings


class CacheManager:
    """Redis缓存管理器"""
    
    def __init__(self):
        """初始化Redis连接"""
        self.redis_client = None
        self._connect()
    
    def _connect(self):
        """连接到Redis服务器"""
        try:
            # 从环境变量获取Redis配置
            redis_host = getattr(settings, 'REDIS_HOST', 'localhost')
            redis_port = getattr(settings, 'REDIS_PORT', 6379)
            redis_db = getattr(settings, 'REDIS_DB', 0)
            redis_password = getattr(settings, 'REDIS_PASSWORD', None)
            
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                password=redis_password,
                decode_responses=False,  # 保持二进制数据
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            
            # 测试连接
            self.redis_client.ping()
            print("✅ Redis连接成功")
            
        except Exception as e:
            print(f"⚠️ Redis连接失败: {e}")
            print("📝 将使用内存缓存作为降级方案")
            self.redis_client = None
    
    def set(self, key: str, value: Any, expire: Optional[Union[int, timedelta]] = None) -> bool:
        """设置缓存值"""
        try:
            if self.redis_client is None:
                return False
                
            # 序列化数据
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value, ensure_ascii=False)
            else:
                serialized_value = pickle.dumps(value)
            
            # 设置过期时间
            if isinstance(expire, timedelta):
                expire = int(expire.total_seconds())
            
            # 存储到Redis
            result = self.redis_client.set(key, serialized_value, ex=expire)
            return bool(result)
            
        except Exception as e:
            print(f"缓存设置失败 {key}: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        try:
            if self.redis_client is None:
                return None
                
            value = self.redis_client.get(key)
            if value is None:
                return None
            
            # 尝试JSON反序列化
            try:
                return json.loads(value.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                # 如果JSON解析失败，尝试pickle反序列化
                try:
                    return pickle.loads(value)
                except:
                    return None
                    
        except Exception as e:
            print(f"缓存获取失败 {key}: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            if self.redis_client is None:
                return False
            result = self.redis_client.delete(key)
            return bool(result)
        except Exception as e:
            print(f"缓存删除失败 {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        try:
            if self.redis_client is None:
                return False
            return bool(self.redis_client.exists(key))
        except Exception as e:
            print(f"缓存检查失败 {key}: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """根据模式删除缓存"""
        try:
            if self.redis_client is None:
                return 0
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            print(f"批量缓存删除失败 {pattern}: {e}")
            return 0


# 全局缓存管理器实例
cache = CacheManager()


# 缓存装饰器
def cached(expire: Union[int, timedelta] = 300, key_prefix: str = ""):
    """缓存装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 生成缓存key
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # 尝试从缓存获取
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # 执行函数并缓存结果
            result = await func(*args, **kwargs)
            cache.set(cache_key, result, expire)
            return result
        return wrapper
    return decorator


# 常用缓存键定义
class CacheKeys:
    """缓存键常量"""
    
    # 股票数据缓存
    STOCKS_LIST = "stocks:list"
    STOCK_DETAIL = "stock:detail:{symbol}"
    STOCK_CONCEPTS = "stock:concepts"
    
    # 用户数据缓存
    USER_PROFILE = "user:profile:{user_id}"
    USER_STATS = "user:stats:{user_id}"
    USER_PERMISSIONS = "user:permissions:{user_id}"
    
    # 支付相关缓存
    PAYMENT_PACKAGES = "payment:packages"
    PAYMENT_ORDER = "payment:order:{order_id}"
    PAYMENT_STATS = "payment:stats"
    
    # 系统配置缓存
    SYSTEM_CONFIG = "system:config"
    API_STATS = "api:stats"


# 缓存过期时间常量
class CacheExpiry:
    """缓存过期时间常量（秒）"""
    
    MINUTE_1 = 60
    MINUTE_5 = 300  
    MINUTE_15 = 900
    HOUR_1 = 3600
    HOUR_6 = 21600
    DAY_1 = 86400
    DAY_7 = 604800