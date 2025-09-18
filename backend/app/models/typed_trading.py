"""
类型化交易数据模型
使用type1、type2、type3等简洁命名，方便扩展
"""

from sqlalchemy import Column, String, Integer, Date, DateTime, Index, Boolean, Float, Text
from app.core.database import Base
import datetime


# ==================== Type1 交易数据 ====================

class Type1DailyTrading(Base):
    """Type1-每日交易数据表"""
    __tablename__ = "type1_daily_trading"

    id = Column(Integer, primary_key=True, index=True)
    original_stock_code = Column(String(20), nullable=False, index=True, comment="原始股票代码")
    normalized_stock_code = Column(String(10), nullable=False, index=True, comment="标准化股票代码")
    stock_code = Column(String(20), nullable=False, index=True, comment="股票代码")
    trading_date = Column(Date, nullable=False, index=True, comment="交易日期")
    trading_volume = Column(Integer, nullable=False, comment="交易量")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index('idx_type1_stock_date', 'stock_code', 'trading_date'),
        Index('idx_type1_date_volume', 'trading_date', 'trading_volume'),
    )


class Type1ConceptDailySummary(Base):
    """Type1-概念每日汇总表"""
    __tablename__ = "type1_concept_daily_summary"

    id = Column(Integer, primary_key=True, index=True)
    concept_name = Column(String(100), nullable=False, index=True)
    trading_date = Column(Date, nullable=False, index=True)
    total_volume = Column(Integer, nullable=False)
    stock_count = Column(Integer, nullable=False)
    average_volume = Column(Float, nullable=False)
    max_volume = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index('idx_type1_concept_date', 'concept_name', 'trading_date'),
        Index('idx_type1_date_total', 'trading_date', 'total_volume'),
    )


class Type1StockConceptRanking(Base):
    """Type1-股票在概念中的每日排名表"""
    __tablename__ = "type1_stock_concept_ranking"

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
        Index('idx_type1_stock_concept_date', 'stock_code', 'concept_name', 'trading_date'),
        Index('idx_type1_concept_date_rank', 'concept_name', 'trading_date', 'concept_rank'),
    )


class Type1ConceptHighRecord(Base):
    """Type1-概念创新高记录表"""
    __tablename__ = "type1_concept_high_record"

    id = Column(Integer, primary_key=True, index=True)
    concept_name = Column(String(100), nullable=False, index=True)
    trading_date = Column(Date, nullable=False, index=True)
    total_volume = Column(Integer, nullable=False)
    days_period = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index('idx_type1_concept_date_period', 'concept_name', 'trading_date', 'days_period'),
        Index('idx_type1_date_volume_active', 'trading_date', 'total_volume', 'is_active'),
    )


# ==================== Type2 交易数据 ====================

class Type2DailyTrading(Base):
    """Type2-每日交易数据表"""
    __tablename__ = "type2_daily_trading"

    id = Column(Integer, primary_key=True, index=True)
    original_stock_code = Column(String(20), nullable=False, index=True, comment="原始股票代码")
    normalized_stock_code = Column(String(10), nullable=False, index=True, comment="标准化股票代码")
    stock_code = Column(String(20), nullable=False, index=True, comment="股票代码")
    trading_date = Column(Date, nullable=False, index=True, comment="交易日期")
    trading_volume = Column(Integer, nullable=False, comment="交易量")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index('idx_type2_stock_date', 'stock_code', 'trading_date'),
        Index('idx_type2_date_volume', 'trading_date', 'trading_volume'),
    )


class Type2ConceptDailySummary(Base):
    """Type2-概念每日汇总表"""
    __tablename__ = "type2_concept_daily_summary"

    id = Column(Integer, primary_key=True, index=True)
    concept_name = Column(String(100), nullable=False, index=True)
    trading_date = Column(Date, nullable=False, index=True)
    total_volume = Column(Integer, nullable=False)
    stock_count = Column(Integer, nullable=False)
    average_volume = Column(Float, nullable=False)
    max_volume = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index('idx_type2_concept_date', 'concept_name', 'trading_date'),
        Index('idx_type2_date_total', 'trading_date', 'total_volume'),
    )


class Type2StockConceptRanking(Base):
    """Type2-股票在概念中的每日排名表"""
    __tablename__ = "type2_stock_concept_ranking"

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
        Index('idx_type2_stock_concept_date', 'stock_code', 'concept_name', 'trading_date'),
        Index('idx_type2_concept_date_rank', 'concept_name', 'trading_date', 'concept_rank'),
    )


class Type2ConceptHighRecord(Base):
    """Type2-概念创新高记录表"""
    __tablename__ = "type2_concept_high_record"

    id = Column(Integer, primary_key=True, index=True)
    concept_name = Column(String(100), nullable=False, index=True)
    trading_date = Column(Date, nullable=False, index=True)
    total_volume = Column(Integer, nullable=False)
    days_period = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index('idx_type2_concept_date_period', 'concept_name', 'trading_date', 'days_period'),
        Index('idx_type2_date_volume_active', 'trading_date', 'total_volume', 'is_active'),
    )


# ==================== Type3 交易数据 ====================

class Type3DailyTrading(Base):
    """Type3-每日交易数据表"""
    __tablename__ = "type3_daily_trading"

    id = Column(Integer, primary_key=True, index=True)
    original_stock_code = Column(String(20), nullable=False, index=True, comment="原始股票代码")
    normalized_stock_code = Column(String(10), nullable=False, index=True, comment="标准化股票代码")
    stock_code = Column(String(20), nullable=False, index=True, comment="股票代码")
    trading_date = Column(Date, nullable=False, index=True, comment="交易日期")
    trading_volume = Column(Integer, nullable=False, comment="交易量")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index('idx_type3_stock_date', 'stock_code', 'trading_date'),
        Index('idx_type3_date_volume', 'trading_date', 'trading_volume'),
    )


class Type3ConceptDailySummary(Base):
    """Type3-概念每日汇总表"""
    __tablename__ = "type3_concept_daily_summary"

    id = Column(Integer, primary_key=True, index=True)
    concept_name = Column(String(100), nullable=False, index=True)
    trading_date = Column(Date, nullable=False, index=True)
    total_volume = Column(Integer, nullable=False)
    stock_count = Column(Integer, nullable=False)
    average_volume = Column(Float, nullable=False)
    max_volume = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index('idx_type3_concept_date', 'concept_name', 'trading_date'),
        Index('idx_type3_date_total', 'trading_date', 'total_volume'),
    )


class Type3StockConceptRanking(Base):
    """Type3-股票在概念中的每日排名表"""
    __tablename__ = "type3_stock_concept_ranking"

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
        Index('idx_type3_stock_concept_date', 'stock_code', 'concept_name', 'trading_date'),
        Index('idx_type3_concept_date_rank', 'concept_name', 'trading_date', 'concept_rank'),
    )


class Type3ConceptHighRecord(Base):
    """Type3-概念创新高记录表"""
    __tablename__ = "type3_concept_high_record"

    id = Column(Integer, primary_key=True, index=True)
    concept_name = Column(String(100), nullable=False, index=True)
    trading_date = Column(Date, nullable=False, index=True)
    total_volume = Column(Integer, nullable=False)
    days_period = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index('idx_type3_concept_date_period', 'concept_name', 'trading_date', 'days_period'),
        Index('idx_type3_date_volume_active', 'trading_date', 'total_volume', 'is_active'),
    )


# ==================== EEE 交易数据 ====================

class EEEDailyTrading(Base):
    """EEE-每日交易数据表"""
    __tablename__ = "eee_daily_trading"

    id = Column(Integer, primary_key=True, index=True)
    original_stock_code = Column(String(20), nullable=False, index=True, comment="原始股票代码")
    normalized_stock_code = Column(String(10), nullable=False, index=True, comment="标准化股票代码")
    stock_code = Column(String(20), nullable=False, index=True, comment="股票代码")
    trading_date = Column(Date, nullable=False, index=True, comment="交易日期")
    trading_volume = Column(Integer, nullable=False, comment="交易量")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index('idx_eee_stock_date', 'stock_code', 'trading_date'),
        Index('idx_eee_date_volume', 'trading_date', 'trading_volume'),
    )


class EEEConceptDailySummary(Base):
    """EEE-概念每日汇总表"""
    __tablename__ = "eee_concept_daily_summary"

    id = Column(Integer, primary_key=True, index=True)
    concept_name = Column(String(100), nullable=False, index=True)
    trading_date = Column(Date, nullable=False, index=True)
    total_volume = Column(Integer, nullable=False)
    stock_count = Column(Integer, nullable=False)
    average_volume = Column(Float, nullable=False)
    max_volume = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index('idx_eee_concept_date', 'concept_name', 'trading_date'),
        Index('idx_eee_date_total', 'trading_date', 'total_volume'),
    )


class EEEStockConceptRanking(Base):
    """EEE-股票在概念中的每日排名表"""
    __tablename__ = "eee_stock_concept_ranking"

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
        Index('idx_eee_stock_concept_date', 'stock_code', 'concept_name', 'trading_date'),
        Index('idx_eee_concept_date_rank', 'concept_name', 'trading_date', 'concept_rank'),
    )


class EEEConceptHighRecord(Base):
    """EEE-概念创新高记录表"""
    __tablename__ = "eee_concept_high_record"

    id = Column(Integer, primary_key=True, index=True)
    concept_name = Column(String(100), nullable=False, index=True)
    trading_date = Column(Date, nullable=False, index=True)
    total_volume = Column(Integer, nullable=False)
    days_period = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index('idx_eee_concept_date_period', 'concept_name', 'trading_date', 'days_period'),
        Index('idx_eee_date_volume_active', 'trading_date', 'total_volume', 'is_active'),
    )


# ==================== TTV 交易数据 ====================

class TTVDailyTrading(Base):
    """TTV-每日交易数据表"""
    __tablename__ = "ttv_daily_trading"

    id = Column(Integer, primary_key=True, index=True)
    original_stock_code = Column(String(20), nullable=False, index=True, comment="原始股票代码")
    normalized_stock_code = Column(String(10), nullable=False, index=True, comment="标准化股票代码")
    stock_code = Column(String(20), nullable=False, index=True, comment="股票代码")
    trading_date = Column(Date, nullable=False, index=True, comment="交易日期")
    trading_volume = Column(Integer, nullable=False, comment="交易量")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index('idx_ttv_stock_date', 'stock_code', 'trading_date'),
        Index('idx_ttv_date_volume', 'trading_date', 'trading_volume'),
    )


class TTVConceptDailySummary(Base):
    """TTV-概念每日汇总表"""
    __tablename__ = "ttv_concept_daily_summary"

    id = Column(Integer, primary_key=True, index=True)
    concept_name = Column(String(100), nullable=False, index=True)
    trading_date = Column(Date, nullable=False, index=True)
    total_volume = Column(Integer, nullable=False)
    stock_count = Column(Integer, nullable=False)
    average_volume = Column(Float, nullable=False)
    max_volume = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index('idx_ttv_concept_date', 'concept_name', 'trading_date'),
        Index('idx_ttv_date_total', 'trading_date', 'total_volume'),
    )


class TTVStockConceptRanking(Base):
    """TTV-股票在概念中的每日排名表"""
    __tablename__ = "ttv_stock_concept_ranking"

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
        Index('idx_ttv_stock_concept_date', 'stock_code', 'concept_name', 'trading_date'),
        Index('idx_ttv_concept_date_rank', 'concept_name', 'trading_date', 'concept_rank'),
    )


class TTVConceptHighRecord(Base):
    """TTV-概念创新高记录表"""
    __tablename__ = "ttv_concept_high_record"

    id = Column(Integer, primary_key=True, index=True)
    concept_name = Column(String(100), nullable=False, index=True)
    trading_date = Column(Date, nullable=False, index=True)
    total_volume = Column(Integer, nullable=False)
    days_period = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index('idx_ttv_concept_date_period', 'concept_name', 'trading_date', 'days_period'),
        Index('idx_ttv_date_volume_active', 'trading_date', 'total_volume', 'is_active'),
    )


# ==================== 类型映射配置 ====================

TYPED_MODELS = {
    'type1': {
        'daily_trading': Type1DailyTrading,
        'concept_daily_summary': Type1ConceptDailySummary,
        'stock_concept_ranking': Type1StockConceptRanking,
        'concept_high_record': Type1ConceptHighRecord,
    },
    'type2': {
        'daily_trading': Type2DailyTrading,
        'concept_daily_summary': Type2ConceptDailySummary,
        'stock_concept_ranking': Type2StockConceptRanking,
        'concept_high_record': Type2ConceptHighRecord,
    },
    'type3': {
        'daily_trading': Type3DailyTrading,
        'concept_daily_summary': Type3ConceptDailySummary,
        'stock_concept_ranking': Type3StockConceptRanking,
        'concept_high_record': Type3ConceptHighRecord,
    },
    'eee': {
        'daily_trading': EEEDailyTrading,
        'concept_daily_summary': EEEConceptDailySummary,
        'stock_concept_ranking': EEEStockConceptRanking,
        'concept_high_record': EEEConceptHighRecord,
    },
    'ttv': {
        'daily_trading': TTVDailyTrading,
        'concept_daily_summary': TTVConceptDailySummary,
        'stock_concept_ranking': TTVStockConceptRanking,
        'concept_high_record': TTVConceptHighRecord,
    }
}


def get_models_for_type(import_type: str):
    """获取指定导入类型的所有模型类"""
    if import_type not in TYPED_MODELS:
        raise ValueError(f"不支持的导入类型: {import_type}")
    return TYPED_MODELS[import_type]


def get_table_names_for_type(import_type: str):
    """获取指定导入类型的所有表名"""
    models = get_models_for_type(import_type)
    return [model.__tablename__ for model in models.values()]


def add_new_type(type_number: int):
    """
    添加新类型的模板函数
    使用示例: add_new_type(4) 将创建 type4 相关的所有表
    """
    type_name = f"type{type_number}"
    print(f"📝 添加新类型模板: {type_name}")
    print("需要创建以下4个模型类:")
    print(f"  - {type_name.title()}DailyTrading")
    print(f"  - {type_name.title()}ConceptDailySummary")
    print(f"  - {type_name.title()}StockConceptRanking")
    print(f"  - {type_name.title()}ConceptHighRecord")
    print(f"并在TYPED_MODELS中注册'{type_name}'配置")