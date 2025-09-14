"""
优化的交易数据模型 - 数据库优化v2.6.4
支持高性能查询和预计算字段

注意：这些模型是为了数据库优化方案准备的，
在正式启用前不会影响现有系统运行
"""

from sqlalchemy import Column, Integer, BigInteger, String, Date, DateTime, DECIMAL, Boolean, Text, SmallInteger, MediumInt, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

# 使用独立的Base，避免与现有模型冲突
OptimizedBase = declarative_base()


class DailyTradingUnified(OptimizedBase):
    """统一的每日交易表 - 性能优化版"""
    __tablename__ = 'daily_trading_unified'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    stock_code = Column(String(20), nullable=False, comment='股票代码(标准化格式)')
    stock_name = Column(String(100), nullable=False, comment='股票名称')
    trading_date = Column(Date, nullable=False, comment='交易日期')
    trading_volume = Column(BigInteger, nullable=False, default=0, comment='交易量')
    heat_value = Column(DECIMAL(15, 2), default=0, comment='热度值(来自TXT文件)')
    
    # 预计算字段，避免查询时实时计算
    concept_count = Column(SmallInteger, default=0, comment='概念数量(预计算)')
    rank_in_date = Column(MediumInt, default=0, comment='当日排名(预计算)')
    volume_rank_pct = Column(DECIMAL(5, 2), default=0, comment='交易量排名百分位')
    
    # 时间戳
    created_at = Column(DateTime, default=func.current_timestamp(), comment='创建时间')
    updated_at = Column(DateTime, default=func.current_timestamp(), 
                       onupdate=func.current_timestamp(), comment='更新时间')
    
    # 优化索引设计
    __table_args__ = (
        Index('idx_date_volume', 'trading_date', 'trading_volume'),
        Index('idx_date_rank', 'trading_date', 'rank_in_date'),
        Index('idx_stock_date', 'stock_code', 'trading_date'),
        Index('idx_name_search', 'stock_name'),
        Index('uk_stock_date', 'stock_code', 'trading_date', unique=True),
        {'comment': '统一每日交易表-性能优化版'}
    )


class ConceptDailyMetrics(OptimizedBase):
    """概念每日指标表 - 极致优化版"""
    __tablename__ = 'concept_daily_metrics'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    concept_name = Column(String(100), nullable=False, comment='概念名称')
    trading_date = Column(Date, nullable=False, comment='交易日期')
    
    # 核心指标
    total_volume = Column(BigInteger, nullable=False, default=0, comment='概念总交易量')
    stock_count = Column(SmallInteger, nullable=False, default=0, comment='概念包含股票数量')
    avg_volume = Column(DECIMAL(15, 2), nullable=False, default=0, comment='平均交易量')
    max_volume = Column(BigInteger, nullable=False, default=0, comment='概念内最大单股交易量')
    min_volume = Column(BigInteger, nullable=False, default=0, comment='概念内最小单股交易量')
    
    # 预计算排名和趋势
    volume_rank = Column(SmallInteger, default=0, comment='概念交易量排名(预计算)')
    stock_count_rank = Column(SmallInteger, default=0, comment='概念股票数量排名(预计算)')
    
    # 趋势分析
    is_new_high = Column(Boolean, default=False, comment='是否创新高')
    new_high_days = Column(SmallInteger, default=0, comment='新高天数范围')
    volume_change_pct = Column(DECIMAL(5, 2), default=0, comment='交易量变化百分比')
    prev_day_volume = Column(BigInteger, default=0, comment='前一日交易量')
    
    # 时间戳
    created_at = Column(DateTime, default=func.current_timestamp(), comment='创建时间')
    updated_at = Column(DateTime, default=func.current_timestamp(),
                       onupdate=func.current_timestamp(), comment='更新时间')
    
    # 覆盖索引优化
    __table_args__ = (
        Index('idx_date_rank', 'trading_date', 'volume_rank'),
        Index('idx_date_volume', 'trading_date', 'total_volume'),
        Index('idx_concept_date', 'concept_name', 'trading_date'),
        Index('idx_new_high', 'trading_date', 'is_new_high', 'volume_rank'),
        Index('uk_concept_date', 'concept_name', 'trading_date', unique=True),
        {'comment': '概念每日指标表-极致优化版'}
    )


class StockConceptDailySnapshot(OptimizedBase):
    """股票概念关系每日快照表 - 超高速查询版"""
    __tablename__ = 'stock_concept_daily_snapshot'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    stock_code = Column(String(20), nullable=False, comment='股票代码')
    concept_name = Column(String(100), nullable=False, comment='概念名称')
    trading_date = Column(Date, nullable=False, comment='交易日期')
    
    # 股票在概念中的表现
    trading_volume = Column(BigInteger, nullable=False, default=0, comment='股票交易量')
    concept_rank = Column(SmallInteger, nullable=False, default=0, comment='在概念中的排名')
    volume_percentage = Column(DECIMAL(5, 2), nullable=False, default=0, comment='占概念交易量百分比')
    
    # 概念整体数据(冗余存储，避免JOIN)
    concept_total_volume = Column(BigInteger, nullable=False, default=0, comment='概念总交易量')
    concept_stock_count = Column(SmallInteger, nullable=False, default=0, comment='概念股票总数')
    
    # 时间戳
    created_at = Column(DateTime, default=func.current_timestamp(), comment='创建时间')
    
    # 多维度查询优化索引
    __table_args__ = (
        Index('idx_stock_date', 'stock_code', 'trading_date'),
        Index('idx_concept_date_rank', 'concept_name', 'trading_date', 'concept_rank'),
        Index('idx_date_volume', 'trading_date', 'trading_volume'),
        Index('idx_concept_rank', 'concept_name', 'concept_rank'),
        Index('uk_stock_concept_date', 'stock_code', 'concept_name', 'trading_date', unique=True),
        {'comment': '股票概念关系每日快照-超高速查询版'}
    )


class TodayTradingCache(OptimizedBase):
    """当天交易数据缓存表 - 内存引擎"""
    __tablename__ = 'today_trading_cache'
    
    stock_code = Column(String(20), primary_key=True, comment='股票代码')
    stock_name = Column(String(100), nullable=False, comment='股票名称')
    trading_volume = Column(BigInteger, nullable=False, comment='交易量')
    concept_count = Column(SmallInteger, default=0, comment='概念数量')
    rank_in_date = Column(MediumInt, default=0, comment='当日排名')
    last_updated = Column(DateTime, default=func.current_timestamp(),
                         onupdate=func.current_timestamp(), comment='最后更新时间')
    
    __table_args__ = {'comment': '当天交易数据缓存表-内存引擎'}


# 为了避免导入冲突，提供一个工厂函数
def get_optimized_models():
    """获取所有优化模型的字典"""
    return {
        'DailyTradingUnified': DailyTradingUnified,
        'ConceptDailyMetrics': ConceptDailyMetrics,
        'StockConceptDailySnapshot': StockConceptDailySnapshot,
        'TodayTradingCache': TodayTradingCache
    }


# 检查优化表是否存在的工具函数
def check_optimized_tables_exist(engine):
    """检查优化表是否存在"""
    from sqlalchemy import inspect
    
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    required_tables = [
        'daily_trading_unified',
        'concept_daily_metrics',
        'stock_concept_daily_snapshot',
        'today_trading_cache'
    ]
    
    return all(table in existing_tables for table in required_tables)