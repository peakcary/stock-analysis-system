"""
日志配置模块
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime
import json


class JSONFormatter(logging.Formatter):
    """JSON格式的日志格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # 添加异常信息
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # 添加额外的上下文信息
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'ip_address'):
            log_entry['ip_address'] = record.ip_address
        
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    use_json_format: bool = False,
) -> None:
    """
    配置应用程序日志
    
    Args:
        log_level: 日志级别
        log_file: 日志文件路径
        max_file_size: 单个日志文件最大大小
        backup_count: 保留的日志文件数量
        use_json_format: 是否使用JSON格式
    """
    
    # 创建根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # 清除现有的处理器
    root_logger.handlers.clear()
    
    # 设置日志格式
    if use_json_format:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 文件处理器
    if log_file:
        # 确保日志目录存在
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 使用RotatingFileHandler实现日志轮转
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # 配置第三方库的日志级别
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的日志器"""
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """日志适配器，用于添加上下文信息"""
    
    def process(self, msg, kwargs):
        # 添加额外的上下文信息到日志记录
        extra = kwargs.get('extra', {})
        
        # 合并适配器的额外信息
        if self.extra:
            extra.update(self.extra)
        
        if extra:
            kwargs['extra'] = extra
        
        return msg, kwargs


def get_request_logger(
    name: str,
    user_id: Optional[int] = None,
    request_id: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> LoggerAdapter:
    """
    获取带有请求上下文信息的日志器
    
    Args:
        name: 日志器名称
        user_id: 用户ID
        request_id: 请求ID
        ip_address: IP地址
    
    Returns:
        配置好上下文信息的日志适配器
    """
    logger = get_logger(name)
    extra = {}
    
    if user_id:
        extra['user_id'] = user_id
    if request_id:
        extra['request_id'] = request_id
    if ip_address:
        extra['ip_address'] = ip_address
    
    return LoggerAdapter(logger, extra)


# 预定义的日志器
app_logger = get_logger("app")
api_logger = get_logger("api")
db_logger = get_logger("database")
auth_logger = get_logger("auth")
payment_logger = get_logger("payment")

# 默认日志器
logger = app_logger