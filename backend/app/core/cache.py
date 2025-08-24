"""
简单的内存缓存实现
"""

import time
from typing import Any, Optional, Dict
from functools import wraps
import json
import hashlib


class SimpleCache:
    """简单的内存缓存类"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if key in self._cache:
            cache_item = self._cache[key]
            if cache_item['expires_at'] > time.time():
                return cache_item['value']
            else:
                # 过期删除
                del self._cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """设置缓存值 (ttl单位：秒)"""
        self._cache[key] = {
            'value': value,
            'expires_at': time.time() + ttl
        }
    
    def delete(self, key: str) -> None:
        """删除缓存"""
        if key in self._cache:
            del self._cache[key]
    
    def clear(self) -> None:
        """清空所有缓存"""
        self._cache.clear()
    
    def size(self) -> int:
        """获取缓存项数量"""
        return len(self._cache)


# 全局缓存实例
cache = SimpleCache()


def cache_result(ttl: int = 300, key_prefix: str = ""):
    """
    缓存装饰器
    
    Args:
        ttl: 缓存时间(秒)
        key_prefix: 缓存键前缀
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = _generate_cache_key(func.__name__, key_prefix, args, kwargs)
            
            # 尝试从缓存获取
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator


def _generate_cache_key(func_name: str, prefix: str, args: tuple, kwargs: dict) -> str:
    """生成缓存键"""
    key_parts = [func_name]
    
    if prefix:
        key_parts.append(prefix)
    
    # 处理参数
    if args:
        key_parts.extend([str(arg) for arg in args])
    
    if kwargs:
        sorted_kwargs = sorted(kwargs.items())
        key_parts.extend([f"{k}={v}" for k, v in sorted_kwargs])
    
    key_str = "|".join(key_parts)
    
    # 使用MD5确保键长度合理
    return hashlib.md5(key_str.encode()).hexdigest()


def invalidate_cache_pattern(pattern: str) -> int:
    """
    按模式删除缓存
    
    Args:
        pattern: 要删除的缓存键模式
        
    Returns:
        删除的缓存项数量
    """
    keys_to_delete = []
    
    for key in cache._cache.keys():
        if pattern in key:
            keys_to_delete.append(key)
    
    for key in keys_to_delete:
        cache.delete(key)
    
    return len(keys_to_delete)