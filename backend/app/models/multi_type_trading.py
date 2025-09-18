"""
多类型独立交易数据模型
每种导入类型都有独立的数据表，完全隔离
"""

from sqlalchemy import Column, String, Integer, Date, DateTime, Index, Boolean, Float, Text
from app.core.database import Base
import datetime


# ==================== 日常交易数据类型 ====================

class DailyTypeDailyTrading(Base):
    """日常类型-每日交易数据表"""
    __tablename__ = "daily_type_daily_trading"

    id = Column(Integer, primary_key=True, index=True)
    original_stock_code = Column(String(20), nullable=False, index=True, comment="原始股票代码")
    normalized_stock_code = Column(String(10), nullable=False, index=True, comment="标准化股票代码")
    stock_code = Column(String(20), nullable=False, index=True, comment="股票代码")
    trading_date = Column(Date, nullable=False, index=True, comment="交易日期")
    trading_volume = Column(Integer, nullable=False, comment="交易量")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index('idx_daily_stock_date', 'stock_code', 'trading_date'),
        Index('idx_daily_date_volume', 'trading_date', 'trading_volume'),
    )


class DailyTypeConceptDailySummary(Base):
    """日常类型-概念每日汇总表"""
    __tablename__ = "daily_type_concept_daily_summary"

    id = Column(Integer, primary_key=True, index=True)
    concept_name = Column(String(100), nullable=False, index=True)
    trading_date = Column(Date, nullable=False, index=True)
    total_volume = Column(Integer, nullable=False)
    stock_count = Column(Integer, nullable=False)
    average_volume = Column(Float, nullable=False)
    max_volume = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index('idx_daily_concept_date', 'concept_name', 'trading_date'),
        Index('idx_daily_date_total', 'trading_date', 'total_volume'),
    )


class DailyTypeStockConceptRanking(Base):
    """日常类型-股票在概念中的每日排名表"""
    __tablename__ = "daily_type_stock_concept_ranking"

    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String(20), nullable=False, index=True)
    concept_name = Column(String(100), nullable=False, index=True)
    trading_date = Column(Date, nullable=False, index=True)
    trading_volume = Column(Integer, nullable=False)
    concept_rank = Column(Integer, nullable=False)
    concept_total_volume = Column(Integer, nullable=False)
    volume_percentage = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index('idx_daily_stock_concept_date', 'stock_code', 'concept_name', 'trading_date'),
        Index('idx_daily_concept_date_rank', 'concept_name', 'trading_date', 'concept_rank'),
    )


class DailyTypeConceptHighRecord(Base):
    """日常类型-概念创新高记录表"""
    __tablename__ = "daily_type_concept_high_record"

    id = Column(Integer, primary_key=True, index=True)
    concept_name = Column(String(100), nullable=False, index=True)
    trading_date = Column(Date, nullable=False, index=True)
    total_volume = Column(Integer, nullable=False)
    days_period = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index('idx_daily_concept_date_period', 'concept_name', 'trading_date', 'days_period'),
        Index('idx_daily_date_volume_active', 'trading_date', 'total_volume', 'is_active'),
    )


# ==================== 批量交易数据类型 ====================

class BatchTypeDailyTrading(Base):
    """批量类型-每日交易数据表"""
    __tablename__ = "batch_type_daily_trading"

    id = Column(Integer, primary_key=True, index=True)
    original_stock_code = Column(String(20), nullable=False, index=True, comment="原始股票代码")
    normalized_stock_code = Column(String(10), nullable=False, index=True, comment="标准化股票代码")
    stock_code = Column(String(20), nullable=False, index=True, comment="股票代码")
    trading_date = Column(Date, nullable=False, index=True, comment="交易日期")
    trading_volume = Column(Integer, nullable=False, comment="交易量")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index('idx_batch_stock_date', 'stock_code', 'trading_date'),
        Index('idx_batch_date_volume', 'trading_date', 'trading_volume'),
    )


class BatchTypeConceptDailySummary(Base):
    """批量类型-概念每日汇总表"""
    __tablename__ = "batch_type_concept_daily_summary"

    id = Column(Integer, primary_key=True, index=True)
    concept_name = Column(String(100), nullable=False, index=True)
    trading_date = Column(Date, nullable=False, index=True)
    total_volume = Column(Integer, nullable=False)
    stock_count = Column(Integer, nullable=False)
    average_volume = Column(Float, nullable=False)
    max_volume = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index('idx_batch_concept_date', 'concept_name', 'trading_date'),
        Index('idx_batch_date_total', 'trading_date', 'total_volume'),
    )


class BatchTypeStockConceptRanking(Base):
    """批量类型-股票在概念中的每日排名表"""
    __tablename__ = "batch_type_stock_concept_ranking"

    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String(20), nullable=False, index=True)
    concept_name = Column(String(100), nullable=False, index=True)
    trading_date = Column(Date, nullable=False, index=True)
    trading_volume = Column(Integer, nullable=False)
    concept_rank = Column(Integer, nullable=False)
    concept_total_volume = Column(Integer, nullable=False)
    volume_percentage = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index('idx_batch_stock_concept_date', 'stock_code', 'concept_name', 'trading_date'),
        Index('idx_batch_concept_date_rank', 'concept_name', 'trading_date', 'concept_rank'),
    )


class BatchTypeConceptHighRecord(Base):
    """批量类型-概念创新高记录表"""
    __tablename__ = "batch_type_concept_high_record"

    id = Column(Integer, primary_key=True, index=True)
    concept_name = Column(String(100), nullable=False, index=True)
    trading_date = Column(Date, nullable=False, index=True)
    total_volume = Column(Integer, nullable=False)
    days_period = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index('idx_batch_concept_date_period', 'concept_name', 'trading_date', 'days_period'),
        Index('idx_batch_date_volume_active', 'trading_date', 'total_volume', 'is_active'),
    )


# ==================== 特殊交易数据类型 ====================

class SpecialTypeDailyTrading(Base):
    """特殊类型-每日交易数据表"""
    __tablename__ = "special_type_daily_trading"

    id = Column(Integer, primary_key=True, index=True)
    original_stock_code = Column(String(20), nullable=False, index=True, comment="原始股票代码")
    normalized_stock_code = Column(String(10), nullable=False, index=True, comment="标准化股票代码")
    stock_code = Column(String(20), nullable=False, index=True, comment="股票代码")
    trading_date = Column(Date, nullable=False, index=True, comment="交易日期")
    trading_volume = Column(Integer, nullable=False, comment="交易量")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index('idx_special_stock_date', 'stock_code', 'trading_date'),
        Index('idx_special_date_volume', 'trading_date', 'trading_volume'),
    )


class SpecialTypeConceptDailySummary(Base):
    """特殊类型-概念每日汇总表"""
    __tablename__ = "special_type_concept_daily_summary"

    id = Column(Integer, primary_key=True, index=True)
    concept_name = Column(String(100), nullable=False, index=True)
    trading_date = Column(Date, nullable=False, index=True)
    total_volume = Column(Integer, nullable=False)
    stock_count = Column(Integer, nullable=False)
    average_volume = Column(Float, nullable=False)
    max_volume = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index('idx_special_concept_date', 'concept_name', 'trading_date'),
        Index('idx_special_date_total', 'trading_date', 'total_volume'),
    )


class SpecialTypeStockConceptRanking(Base):
    """特殊类型-股票在概念中的每日排名表"""
    __tablename__ = "special_type_stock_concept_ranking"

    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String(20), nullable=False, index=True)
    concept_name = Column(String(100), nullable=False, index=True)
    trading_date = Column(Date, nullable=False, index=True)
    trading_volume = Column(Integer, nullable=False)
    concept_rank = Column(Integer, nullable=False)
    concept_total_volume = Column(Integer, nullable=False)
    volume_percentage = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index('idx_special_stock_concept_date', 'stock_code', 'concept_name', 'trading_date'),
        Index('idx_special_concept_date_rank', 'concept_name', 'trading_date', 'concept_rank'),
    )


class SpecialTypeConceptHighRecord(Base):
    """特殊类型-概念创新高记录表"""
    __tablename__ = "special_type_concept_high_record"

    id = Column(Integer, primary_key=True, index=True)
    concept_name = Column(String(100), nullable=False, index=True)
    trading_date = Column(Date, nullable=False, index=True)
    total_volume = Column(Integer, nullable=False)
    days_period = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index('idx_special_concept_date_period', 'concept_name', 'trading_date', 'days_period'),
        Index('idx_special_date_volume_active', 'trading_date', 'total_volume', 'is_active'),
    )


# ==================== 实验交易数据类型 ====================

class ExperimentalTypeDailyTrading(Base):
    """实验类型-每日交易数据表"""
    __tablename__ = "experimental_type_daily_trading"

    id = Column(Integer, primary_key=True, index=True)
    original_stock_code = Column(String(20), nullable=False, index=True, comment="原始股票代码")
    normalized_stock_code = Column(String(10), nullable=False, index=True, comment="标准化股票代码")
    stock_code = Column(String(20), nullable=False, index=True, comment="股票代码")
    trading_date = Column(Date, nullable=False, index=True, comment="交易日期")
    trading_volume = Column(Integer, nullable=False, comment="交易量")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index('idx_experimental_stock_date', 'stock_code', 'trading_date'),
        Index('idx_experimental_date_volume', 'trading_date', 'trading_volume'),
    )


class ExperimentalTypeConceptDailySummary(Base):
    """实验类型-概念每日汇总表"""
    __tablename__ = "experimental_type_concept_daily_summary"

    id = Column(Integer, primary_key=True, index=True)
    concept_name = Column(String(100), nullable=False, index=True)
    trading_date = Column(Date, nullable=False, index=True)
    total_volume = Column(Integer, nullable=False)
    stock_count = Column(Integer, nullable=False)
    average_volume = Column(Float, nullable=False)
    max_volume = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index('idx_experimental_concept_date', 'concept_name', 'trading_date'),
        Index('idx_experimental_date_total', 'trading_date', 'total_volume'),
    )


class ExperimentalTypeStockConceptRanking(Base):
    """实验类型-股票在概念中的每日排名表"""
    __tablename__ = "experimental_type_stock_concept_ranking"

    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String(20), nullable=False, index=True)
    concept_name = Column(String(100), nullable=False, index=True)
    trading_date = Column(Date, nullable=False, index=True)
    trading_volume = Column(Integer, nullable=False)
    concept_rank = Column(Integer, nullable=False)
    concept_total_volume = Column(Integer, nullable=False)
    volume_percentage = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index('idx_experimental_stock_concept_date', 'stock_code', 'concept_name', 'trading_date'),
        Index('idx_experimental_concept_date_rank', 'concept_name', 'trading_date', 'concept_rank'),
    )


class ExperimentalTypeConceptHighRecord(Base):
    """实验类型-概念创新高记录表"""
    __tablename__ = "experimental_type_concept_high_record"

    id = Column(Integer, primary_key=True, index=True)
    concept_name = Column(String(100), nullable=False, index=True)
    trading_date = Column(Date, nullable=False, index=True)
    total_volume = Column(Integer, nullable=False)
    days_period = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index('idx_experimental_concept_date_period', 'concept_name', 'trading_date', 'days_period'),
        Index('idx_experimental_date_volume_active', 'trading_date', 'total_volume', 'is_active'),
    )


# ==================== 类型映射配置 ====================

MULTI_TYPE_MODELS = {
    'daily': {
        'daily_trading': DailyTypeDailyTrading,
        'concept_daily_summary': DailyTypeConceptDailySummary,
        'stock_concept_ranking': DailyTypeStockConceptRanking,
        'concept_high_record': DailyTypeConceptHighRecord,
    },
    'batch': {
        'daily_trading': BatchTypeDailyTrading,
        'concept_daily_summary': BatchTypeConceptDailySummary,
        'stock_concept_ranking': BatchTypeStockConceptRanking,
        'concept_high_record': BatchTypeConceptHighRecord,
    },
    'special': {
        'daily_trading': SpecialTypeDailyTrading,
        'concept_daily_summary': SpecialTypeConceptDailySummary,
        'stock_concept_ranking': SpecialTypeStockConceptRanking,
        'concept_high_record': SpecialTypeConceptHighRecord,
    },
    'experimental': {
        'daily_trading': ExperimentalTypeDailyTrading,
        'concept_daily_summary': ExperimentalTypeConceptDailySummary,
        'stock_concept_ranking': ExperimentalTypeStockConceptRanking,
        'concept_high_record': ExperimentalTypeConceptHighRecord,
    }
}


def get_models_for_type(import_type: str):
    """获取指定导入类型的所有模型类"""
    if import_type not in MULTI_TYPE_MODELS:
        raise ValueError(f"不支持的导入类型: {import_type}")
    return MULTI_TYPE_MODELS[import_type]


def get_table_names_for_type(import_type: str):
    """获取指定导入类型的所有表名"""
    models = get_models_for_type(import_type)
    return [model.__tablename__ for model in models.values()]