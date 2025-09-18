"""
历史数据导入记录模型
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float
from sqlalchemy.sql import func
from app.core.database import Base


class HistoricalImportRecord(Base):
    """历史数据导入记录"""
    __tablename__ = "historical_import_records"

    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    filename = Column(String(255), nullable=False, comment="导入文件名")

    # 日期相关
    total_dates = Column(Integer, nullable=False, default=0, comment="包含的交易日期数量")
    date_range = Column(String(100), nullable=True, comment="日期范围，如'2024-01-01 至 2024-12-31'")
    earliest_date = Column(String(20), nullable=True, comment="最早交易日期")
    latest_date = Column(String(20), nullable=True, comment="最晚交易日期")

    # 导入统计
    total_records = Column(Integer, nullable=False, default=0, comment="文件总记录数")
    imported_records = Column(Integer, nullable=False, default=0, comment="成功导入记录数")
    error_records = Column(Integer, nullable=False, default=0, comment="错误记录数")
    skipped_records = Column(Integer, nullable=False, default=0, comment="跳过记录数")

    # 文件信息
    file_size = Column(Integer, nullable=False, default=0, comment="文件大小(字节)")
    file_encoding = Column(String(20), nullable=True, comment="文件编码")

    # 导入状态
    import_status = Column(String(20), nullable=False, default="processing", comment="导入状态")
    processor_type = Column(String(50), nullable=True, comment="使用的处理器类型")

    # 时间信息
    import_started_at = Column(DateTime, nullable=False, default=func.now(), comment="导入开始时间")
    import_completed_at = Column(DateTime, nullable=True, comment="导入完成时间")
    duration_seconds = Column(Float, nullable=True, comment="导入耗时(秒)")

    # 操作信息
    imported_by = Column(String(100), nullable=False, comment="导入操作人")

    # 错误信息
    error_message = Column(Text, nullable=True, comment="错误消息")
    error_details = Column(Text, nullable=True, comment="详细错误信息")

    # 额外信息
    processing_details = Column(Text, nullable=True, comment="处理详情(JSON格式)")

    # 时间戳
    created_at = Column(DateTime, nullable=False, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<HistoricalImportRecord(id={self.id}, filename='{self.filename}', status='{self.import_status}')>"

    @property
    def duration_display(self):
        """格式化显示耗时"""
        if not self.duration_seconds:
            return None

        seconds = int(self.duration_seconds)
        if seconds < 60:
            return f"{seconds}秒"
        elif seconds < 3600:
            minutes = seconds // 60
            seconds = seconds % 60
            return f"{minutes}分{seconds}秒"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            seconds = seconds % 60
            return f"{hours}时{minutes}分{seconds}秒"

    @property
    def success_rate(self):
        """成功率"""
        if self.total_records == 0:
            return 0.0
        return round((self.imported_records / self.total_records) * 100, 2)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'filename': self.filename,
            'total_dates': self.total_dates,
            'date_range': self.date_range,
            'earliest_date': self.earliest_date,
            'latest_date': self.latest_date,
            'total_records': self.total_records,
            'imported_records': self.imported_records,
            'error_records': self.error_records,
            'skipped_records': self.skipped_records,
            'file_size': self.file_size,
            'file_encoding': self.file_encoding,
            'import_status': self.import_status,
            'processor_type': self.processor_type,
            'import_started_at': self.import_started_at.isoformat() if self.import_started_at else None,
            'import_completed_at': self.import_completed_at.isoformat() if self.import_completed_at else None,
            'duration_seconds': self.duration_seconds,
            'duration': self.duration_display,
            'imported_by': self.imported_by,
            'error_message': self.error_message,
            'success_rate': self.success_rate,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }