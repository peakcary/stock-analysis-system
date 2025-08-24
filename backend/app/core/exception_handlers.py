"""
全局异常处理器
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from pydantic import ValidationError
import traceback
from typing import Union
from app.core.logging import get_logger, get_request_logger

logger = get_logger(__name__)


class AppException(Exception):
    """应用程序基础异常类"""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: dict = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class BusinessException(AppException):
    """业务逻辑异常"""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


class AuthenticationException(AppException):
    """认证异常"""
    
    def __init__(self, message: str = "认证失败", details: dict = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details
        )


class AuthorizationException(AppException):
    """授权异常"""
    
    def __init__(self, message: str = "权限不足", details: dict = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details
        )


class ResourceNotFoundException(AppException):
    """资源未找到异常"""
    
    def __init__(self, message: str = "资源未找到", details: dict = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details
        )


class DatabaseException(AppException):
    """数据库异常"""
    
    def __init__(self, message: str = "数据库操作失败", details: dict = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


def create_error_response(
    message: str,
    status_code: int,
    details: dict = None,
    error_code: str = None
) -> JSONResponse:
    """创建标准错误响应"""
    
    error_data = {
        "error": True,
        "message": message,
        "status_code": status_code,
    }
    
    if error_code:
        error_data["error_code"] = error_code
    
    if details:
        error_data["details"] = details
    
    return JSONResponse(
        status_code=status_code,
        content=error_data
    )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """应用程序异常处理器"""
    
    request_logger = get_request_logger(
        __name__,
        request_id=getattr(request.state, 'request_id', None),
        ip_address=request.client.host if request.client else None
    )
    
    request_logger.warning(
        f"AppException occurred: {exc.message}",
        extra={
            "status_code": exc.status_code,
            "details": exc.details,
            "url": str(request.url),
            "method": request.method
        }
    )
    
    return create_error_response(
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """HTTP异常处理器"""
    
    request_logger = get_request_logger(
        __name__,
        request_id=getattr(request.state, 'request_id', None),
        ip_address=request.client.host if request.client else None
    )
    
    request_logger.info(
        f"HTTPException: {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "url": str(request.url),
            "method": request.method
        }
    )
    
    return create_error_response(
        message=exc.detail,
        status_code=exc.status_code
    )


async def validation_exception_handler(
    request: Request, 
    exc: Union[RequestValidationError, ValidationError]
) -> JSONResponse:
    """请求验证异常处理器"""
    
    request_logger = get_request_logger(
        __name__,
        request_id=getattr(request.state, 'request_id', None),
        ip_address=request.client.host if request.client else None
    )
    
    # 格式化验证错误信息
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(x) for x in error["loc"])
        message = error["msg"]
        errors.append(f"{field}: {message}")
    
    error_message = "请求参数验证失败: " + "; ".join(errors)
    
    request_logger.warning(
        error_message,
        extra={
            "validation_errors": exc.errors(),
            "url": str(request.url),
            "method": request.method
        }
    )
    
    return create_error_response(
        message="请求参数验证失败",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details={"validation_errors": exc.errors()}
    )


async def sqlalchemy_exception_handler(
    request: Request, 
    exc: SQLAlchemyError
) -> JSONResponse:
    """SQLAlchemy异常处理器"""
    
    request_logger = get_request_logger(
        __name__,
        request_id=getattr(request.state, 'request_id', None),
        ip_address=request.client.host if request.client else None
    )
    
    request_logger.error(
        f"Database error: {str(exc)}",
        extra={
            "url": str(request.url),
            "method": request.method,
            "exception_type": type(exc).__name__
        },
        exc_info=True
    )
    
    return create_error_response(
        message="数据库操作失败",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code="DATABASE_ERROR"
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """通用异常处理器"""
    
    request_logger = get_request_logger(
        __name__,
        request_id=getattr(request.state, 'request_id', None),
        ip_address=request.client.host if request.client else None
    )
    
    request_logger.error(
        f"Unexpected error: {str(exc)}",
        extra={
            "url": str(request.url),
            "method": request.method,
            "exception_type": type(exc).__name__,
            "traceback": traceback.format_exc()
        },
        exc_info=True
    )
    
    return create_error_response(
        message="服务器内部错误",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code="INTERNAL_SERVER_ERROR"
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """设置异常处理器"""
    
    # 应用程序自定义异常
    app.add_exception_handler(AppException, app_exception_handler)
    
    # FastAPI内置异常
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    
    # 数据库异常
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    
    # 通用异常（必须放在最后）
    app.add_exception_handler(Exception, general_exception_handler)