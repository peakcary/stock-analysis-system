"""
支付安全中间件
Payment Security Middleware
"""

import time
import hashlib
from typing import Dict, Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.logging import logger
from app.core.config import settings


class PaymentSecurityMiddleware(BaseHTTPMiddleware):
    """支付安全中间件"""
    
    def __init__(self, app):
        super().__init__(app)
        # 限流配置：每个IP每分钟最多20次支付相关请求
        self.rate_limit = 20
        self.rate_window = 60  # 秒
        # 防重放攻击：请求缓存5分钟
        self.nonce_cache_duration = 300  # 秒
        
        # 简单的内存存储（生产环境应该使用Redis）
        self.request_counts: Dict[str, Dict[str, int]] = {}
        self.nonce_cache: Dict[str, float] = {}
    
    async def dispatch(self, request: Request, call_next):
        # 只对支付相关接口进行安全检查
        if not self._is_payment_api(request.url.path):
            return await call_next(request)
        
        client_ip = self._get_client_ip(request)
        
        # 1. API限流检查
        if not self._check_rate_limit(client_ip):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="请求过于频繁，请稍后再试"
            )
        
        # 2. 防重放攻击检查（仅对POST/PUT请求）
        if request.method in ['POST', 'PUT']:
            if not await self._check_replay_attack(request):
                logger.warning(f"Potential replay attack from IP: {client_ip}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="请求签名验证失败或请求重复"
                )
        
        # 记录支付API访问
        logger.info(f"Payment API access: {request.method} {request.url.path} from {client_ip}")
        
        response = await call_next(request)
        return response
    
    def _is_payment_api(self, path: str) -> bool:
        """检查是否为支付相关API"""
        payment_paths = [
            '/api/v1/payment/',
            '/api/v1/admin/packages'
        ]
        return any(path.startswith(p) for p in payment_paths)
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP"""
        # 支持代理情况下的真实IP获取
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else '127.0.0.1'
    
    def _check_rate_limit(self, client_ip: str) -> bool:
        """检查API限流"""
        current_time = int(time.time())
        current_minute = current_time // self.rate_window
        
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = {}
        
        # 清理过期的计数器
        self.request_counts[client_ip] = {
            minute: count for minute, count in self.request_counts[client_ip].items()
            if current_minute - minute < 2  # 保留最近2分钟的记录
        }
        
        # 获取当前分钟的请求次数
        current_count = self.request_counts[client_ip].get(current_minute, 0)
        
        if current_count >= self.rate_limit:
            return False
        
        # 增加请求计数
        self.request_counts[client_ip][current_minute] = current_count + 1
        return True
    
    async def _check_replay_attack(self, request: Request) -> bool:
        """检查防重放攻击"""
        try:
            # 获取请求体
            body = await request.body()
            
            # 生成请求的唯一标识（基于URL、时间戳和请求体）
            timestamp = request.headers.get('X-Timestamp')
            if not timestamp:
                # 如果没有时间戳，只检查请求体是否重复
                timestamp = str(int(time.time()))
            
            # 检查时间戳是否在合理范围内（5分钟）
            try:
                request_time = int(timestamp)
                current_time = int(time.time())
                if abs(current_time - request_time) > self.nonce_cache_duration:
                    logger.warning(f"Request timestamp too old or too new: {timestamp}")
                    return False
            except ValueError:
                logger.warning(f"Invalid timestamp format: {timestamp}")
                return False
            
            # 生成请求签名
            nonce_string = f"{request.method}:{request.url.path}:{timestamp}:{body.decode('utf-8', errors='ignore')}"
            nonce_hash = hashlib.sha256(nonce_string.encode()).hexdigest()
            
            current_time = time.time()
            
            # 检查是否为重复请求
            if nonce_hash in self.nonce_cache:
                logger.warning(f"Duplicate request detected: {nonce_hash}")
                return False
            
            # 清理过期的nonce
            self.nonce_cache = {
                key: timestamp for key, timestamp in self.nonce_cache.items()
                if current_time - timestamp < self.nonce_cache_duration
            }
            
            # 记录当前请求
            self.nonce_cache[nonce_hash] = current_time
            
            return True
            
        except Exception as e:
            logger.error(f"Check replay attack error: {e}")
            # 发生错误时，为了不影响正常流程，返回True
            return True
    
    def get_security_stats(self) -> Dict[str, any]:
        """获取安全统计信息"""
        current_time = time.time()
        active_ips = len([
            ip for ip, counts in self.request_counts.items()
            if any(time - (current_time // self.rate_window) < 2 for time in counts.keys())
        ])
        
        active_nonces = len([
            timestamp for timestamp in self.nonce_cache.values()
            if current_time - timestamp < self.nonce_cache_duration
        ])
        
        return {
            "active_ips": active_ips,
            "active_nonces": active_nonces,
            "total_request_records": sum(len(counts) for counts in self.request_counts.values()),
            "nonce_cache_size": len(self.nonce_cache)
        }


# 全局实例
payment_security_middleware = PaymentSecurityMiddleware