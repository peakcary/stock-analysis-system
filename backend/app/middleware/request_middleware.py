"""
请求处理中间件
"""

import time
import uuid
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import get_request_logger

logger = get_request_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""
    
    def __init__(self, app, log_requests: bool = True, log_responses: bool = False):
        super().__init__(app)
        self.log_requests = log_requests
        self.log_responses = log_responses
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 生成请求ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # 记录请求开始时间
        start_time = time.time()
        
        # 获取客户端IP
        client_ip = self.get_client_ip(request)
        
        # 创建带上下文的日志器
        request_logger = get_request_logger(
            __name__,
            request_id=request_id,
            ip_address=client_ip
        )
        
        # 记录请求信息
        if self.log_requests:
            request_logger.info(
                f"Request started: {request.method} {request.url}",
                extra={
                    "method": request.method,
                    "url": str(request.url),
                    "headers": dict(request.headers),
                    "query_params": dict(request.query_params),
                }
            )
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录响应信息
            if self.log_responses or response.status_code >= 400:
                log_level = "error" if response.status_code >= 400 else "info"
                getattr(request_logger, log_level)(
                    f"Request completed: {request.method} {request.url} - {response.status_code}",
                    extra={
                        "status_code": response.status_code,
                        "process_time": round(process_time, 4),
                        "response_headers": dict(response.headers) if hasattr(response, 'headers') else {}
                    }
                )
            
            # 添加响应头
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(round(process_time, 4))
            
            return response
            
        except Exception as e:
            # 记录异常
            process_time = time.time() - start_time
            request_logger.error(
                f"Request failed: {request.method} {request.url} - {str(e)}",
                extra={
                    "process_time": round(process_time, 4),
                    "exception": str(e)
                },
                exc_info=True
            )
            raise
    
    def get_client_ip(self, request: Request) -> str:
        """获取客户端真实IP地址"""
        # 检查代理头
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For 可能包含多个IP，取第一个
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # 使用连接的客户端IP
        return request.client.host if request.client else "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """简单的速率限制中间件"""
    
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}  # {ip: [(timestamp, count), ...]}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = self.get_client_ip(request)
        current_time = time.time()
        
        # 清理过期的请求记录
        self.cleanup_expired_requests(current_time)
        
        # 检查当前IP的请求次数
        if not self.is_allowed(client_ip, current_time):
            return JSONResponse(
                status_code=429,
                content={
                    "error": True,
                    "message": "请求过于频繁，请稍后再试",
                    "status_code": 429
                }
            )
        
        # 记录当前请求
        self.record_request(client_ip, current_time)
        
        return await call_next(request)
    
    def get_client_ip(self, request: Request) -> str:
        """获取客户端IP"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    def cleanup_expired_requests(self, current_time: float) -> None:
        """清理过期的请求记录"""
        cutoff_time = current_time - self.window_seconds
        
        for ip in list(self.requests.keys()):
            self.requests[ip] = [
                (timestamp, count) for timestamp, count in self.requests[ip]
                if timestamp > cutoff_time
            ]
            
            # 如果该IP没有活跃请求，删除记录
            if not self.requests[ip]:
                del self.requests[ip]
    
    def is_allowed(self, client_ip: str, current_time: float) -> bool:
        """检查是否允许请求"""
        if client_ip not in self.requests:
            return True
        
        # 计算当前时间窗口内的总请求数
        total_requests = sum(count for _, count in self.requests[client_ip])
        return total_requests < self.max_requests
    
    def record_request(self, client_ip: str, current_time: float) -> None:
        """记录请求"""
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        
        # 如果最近的请求在同一秒内，增加计数
        if (self.requests[client_ip] and 
            current_time - self.requests[client_ip][-1][0] < 1.0):
            # 更新最后一个记录的计数
            last_timestamp, last_count = self.requests[client_ip][-1]
            self.requests[client_ip][-1] = (current_time, last_count + 1)
        else:
            # 添加新的请求记录
            self.requests[client_ip].append((current_time, 1))


class CORSMiddleware(BaseHTTPMiddleware):
    """简单的CORS中间件"""
    
    def __init__(
        self, 
        app, 
        allow_origins: list = None,
        allow_methods: list = None,
        allow_headers: list = None,
        allow_credentials: bool = False
    ):
        super().__init__(app)
        self.allow_origins = allow_origins or ["*"]
        self.allow_methods = allow_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self.allow_headers = allow_headers or ["*"]
        self.allow_credentials = allow_credentials
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 处理预检请求
        if request.method == "OPTIONS":
            response = Response()
            self.add_cors_headers(response, request)
            return response
        
        # 处理实际请求
        response = await call_next(request)
        self.add_cors_headers(response, request)
        return response
    
    def add_cors_headers(self, response: Response, request: Request) -> None:
        """添加CORS头"""
        origin = request.headers.get("Origin")
        
        if self.allow_origins == ["*"] or origin in self.allow_origins:
            response.headers["Access-Control-Allow-Origin"] = origin or "*"
        
        response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allow_methods)
        response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allow_headers)
        
        if self.allow_credentials:
            response.headers["Access-Control-Allow-Credentials"] = "true"