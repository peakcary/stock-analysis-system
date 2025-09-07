from sqlalchemy import Column, String, Integer, Date, DateTime, Index, Boolean, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from app.core.database import Base
import datetime

class DailyTrading(Base):
    """每日交易数据表"""
    __tablename__ = "daily_trading"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String(20), nullable=False, index=True)  # 股票代码
    trading_date = Column(Date, nullable=False, index=True)  # 交易日期
    trading_volume = Column(Integer, nullable=False)  # 交易量
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # 联合索引，提高查询效率
    __table_args__ = (
        Index('idx_stock_date', 'stock_code', 'trading_date'),
        Index('idx_date_volume', 'trading_date', 'trading_volume'),
    )


class ConceptDailySummary(Base):
    """概念每日汇总表"""
    __tablename__ = "concept_daily_summary"
    
    id = Column(Integer, primary_key=True, index=True)
    concept_name = Column(String(100), nullable=False, index=True)  # 概念名称
    trading_date = Column(Date, nullable=False, index=True)  # 交易日期
    total_volume = Column(Integer, nullable=False)  # 概念总交易量
    stock_count = Column(Integer, nullable=False)  # 概念内股票数量
    average_volume = Column(Float, nullable=False)  # 平均交易量
    max_volume = Column(Integer, nullable=False)  # 最大交易量
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # 联合索引
    __table_args__ = (
        Index('idx_concept_date', 'concept_name', 'trading_date'),
        Index('idx_date_total', 'trading_date', 'total_volume'),
    )


class StockConceptRanking(Base):
    """股票在概念中的每日排名表"""
    __tablename__ = "stock_concept_ranking"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String(20), nullable=False, index=True)  # 股票代码
    concept_name = Column(String(100), nullable=False, index=True)  # 概念名称
    trading_date = Column(Date, nullable=False, index=True)  # 交易日期
    trading_volume = Column(Integer, nullable=False)  # 交易量
    concept_rank = Column(Integer, nullable=False)  # 在概念中的排名
    concept_total_volume = Column(Integer, nullable=False)  # 概念总量
    volume_percentage = Column(Float, nullable=False)  # 占概念的百分比
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # 联合索引
    __table_args__ = (
        Index('idx_stock_concept_date', 'stock_code', 'concept_name', 'trading_date'),
        Index('idx_concept_date_rank', 'concept_name', 'trading_date', 'concept_rank'),
    )


class ConceptHighRecord(Base):
    """概念创新高记录表"""
    __tablename__ = "concept_high_record"
    
    id = Column(Integer, primary_key=True, index=True)
    concept_name = Column(String(100), nullable=False, index=True)  # 概念名称
    trading_date = Column(Date, nullable=False, index=True)  # 创新高日期
    total_volume = Column(Integer, nullable=False)  # 创新高交易量
    days_period = Column(Integer, nullable=False)  # 统计周期（天数）
    is_active = Column(Boolean, default=True)  # 是否为当前活跃的新高
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # 联合索引
    __table_args__ = (
        Index('idx_concept_date_period', 'concept_name', 'trading_date', 'days_period'),
        Index('idx_date_volume_active', 'trading_date', 'total_volume', 'is_active'),
    )


class TxtImportRecord(Base):
    """TXT文件导入记录表"""
    __tablename__ = "txt_import_record"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)  # 原始文件名
    trading_date = Column(Date, nullable=False, index=True)  # 数据交易日期
    file_size = Column(Integer, nullable=False)  # 文件大小（字节）
    import_status = Column(String(20), nullable=False, default="success")  # 导入状态：success, failed, processing
    imported_by = Column(String(50), nullable=False)  # 导入人
    
    # 统计信息
    total_records = Column(Integer, default=0)  # 总记录数
    success_records = Column(Integer, default=0)  # 成功记录数
    error_records = Column(Integer, default=0)  # 错误记录数
    concept_count = Column(Integer, default=0)  # 计算出的概念数
    ranking_count = Column(Integer, default=0)  # 排名记录数
    new_high_count = Column(Integer, default=0)  # 创新高记录数
    
    # 时间信息
    import_started_at = Column(DateTime, nullable=False)  # 导入开始时间
    import_completed_at = Column(DateTime)  # 导入完成时间
    calculation_time = Column(Float)  # 计算耗时（秒）
    
    # 额外信息
    error_message = Column(Text)  # 错误信息
    notes = Column(Text)  # 备注信息
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # 索引
    __table_args__ = (
        Index('idx_trading_date_status', 'trading_date', 'import_status'),
        Index('idx_imported_by_date', 'imported_by', 'trading_date'),
        Index('idx_filename', 'filename'),
    )