"""
数据导入记录模型
"""

from sqlalchemy import Column, Integer, String, Date, Text, DateTime, Enum, Index
from app.core.database import Base
from datetime import datetime
import enum


class ImportType(str, enum.Enum):
    """导入类型枚举"""
    CSV = "csv"
    TXT = "txt"
    BOTH = "both"


class ImportStatus(str, enum.Enum):
    """导入状态枚举"""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


class DataImportRecord(Base):
    """数据导入记录表"""
    __tablename__ = "data_import_records"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    import_date = Column(Date, nullable=False, comment='导入日期')
    import_type = Column(Enum('csv', 'txt', 'both', name='importtype'), nullable=False, comment='导入类型')
    file_name = Column(String(255), nullable=False, comment='文件名')
    imported_records = Column(Integer, default=0, comment='导入记录数')
    skipped_records = Column(Integer, default=0, comment='跳过记录数')
    import_status = Column(Enum('success', 'failed', 'partial', name='importstatus'), default='success', comment='导入状态')
    error_message = Column(Text, comment='错误信息')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    __table_args__ = (
        Index('idx_import_date', 'import_date'),
        Index('idx_import_type', 'import_type'),
        Index('idx_import_status', 'import_status'),
        Index('uk_date_type_file', 'import_date', 'import_type', 'file_name', unique=True),
        {'comment': '数据导入记录表'}
    )