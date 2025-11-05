"""
股票相关数据模型
"""

from sqlalchemy import Column, Integer, String, Boolean, DECIMAL, Date, DateTime, Text, Enum, ForeignKey, Index, BigInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class Stock(Base):
    """股票基本信息表"""
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    stock_code = Column(String(10), unique=True, nullable=False, index=True, comment="股票代码（规范化后，无前缀）")
    original_stock_code = Column(String(20), comment="原始股票代码（含SH/SZ等前缀）")
    stock_code_prefix = Column(String(10), comment="股票代码前缀（SH/SZ/BJ/HK等）")
    stock_name = Column(String(100), nullable=False, comment="股票名称")
    industry = Column(String(100), comment="行业")
    is_convertible_bond = Column(Boolean, default=False, index=True, comment="是否为转债")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关联关系
    stock_concepts = relationship("StockConcept", back_populates="stock", cascade="all, delete-orphan")
    daily_data = relationship("DailyStockData", back_populates="stock", cascade="all, delete-orphan")
    concept_rankings = relationship("DailyConceptRanking", back_populates="stock", cascade="all, delete-orphan")


class DailyStockData(Base):
    """每日股票数据表"""
    __tablename__ = "daily_stock_data"
    
    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False, index=True, comment="股票ID")
    trade_date = Column(Date, nullable=False, index=True, comment="交易日期")
    pages_count = Column(Integer, default=0, comment="页数")
    total_reads = Column(Integer, default=0, comment="总阅读数")
    price = Column(DECIMAL(10, 2), default=0, comment="价格")
    turnover_rate = Column(DECIMAL(5, 2), default=0, comment="换手率")
    net_inflow = Column(DECIMAL(15, 2), default=0, comment="净流入")
    heat_value = Column(DECIMAL(15, 2), default=0, index=True, comment="热度值(来自TXT文件)")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")

    # 关联关系
    stock = relationship("Stock", back_populates="daily_data")


class ImportBatch(Base):
    """导入批次管理表 - 记录每次导入的元信息"""
    __tablename__ = "import_batches"

    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    import_date = Column(Date, nullable=False, index=True, comment="导入日期")
    import_type = Column(String(10), nullable=False, index=True, comment="导入类型(csv/txt)")
    file_name = Column(String(255), nullable=False, comment="源文件名")
    record_count = Column(Integer, default=0, comment="记录数")
    status = Column(String(20), default='success', comment="导入状态(success/partial/failed)")
    remark = Column(Text, comment="备注说明")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")

    # 关联关系
    raw_data = relationship("RawImportData", back_populates="batch", cascade="all, delete-orphan")


class RawImportData(Base):
    """原始导入数据表 - 保存导入CSV/TXT的每一行原始信息"""
    __tablename__ = "raw_import_data"

    id = Column(BigInteger, primary_key=True, index=True, comment="主键ID")

    # 批次关联
    import_batch_id = Column(Integer, ForeignKey('import_batches.id'), nullable=False, index=True, comment="导入批次ID")
    row_number = Column(Integer, nullable=False, comment="原始行号")

    # 时间信息
    trade_date = Column(Date, nullable=False, index=True, comment="交易日期")
    import_created_at = Column(DateTime, default=func.now(), comment="导入时间")

    # 股票代码（三列存储）
    stock_code_raw = Column(String(20), nullable=False, comment="原始股票代码(如SH600036)")
    stock_code_normalized = Column(String(10), nullable=False, index=True, comment="规范化代码(如600036)")
    stock_code_prefix = Column(String(10), comment="代码前缀(SH/SZ/BJ/HK等)")

    # 股票基本信息
    stock_name = Column(String(100), nullable=False, comment="股票名称")
    industry = Column(String(100), comment="行业")

    # 交易数据
    price = Column(DECIMAL(10, 2), default=0, comment="价格")
    turnover_rate = Column(DECIMAL(5, 2), default=0, comment="换手率")
    net_inflow = Column(DECIMAL(15, 2), default=0, comment="净流入")
    pages_count = Column(Integer, default=0, comment="全部页数")
    total_reads = Column(Integer, default=0, comment="热帖首页阅读总数")

    # CSV特有字段
    concept = Column(String(100), comment="概念(仅CSV)")

    # TXT特有字段
    heat_value = Column(DECIMAL(15, 2), comment="热度值(仅TXT)")

    # 数据来源
    source_type = Column(String(10), nullable=False, comment="来源类型(csv/txt)")
    source_file = Column(String(255), comment="来源文件名")

    # 关联关系
    batch = relationship("ImportBatch", back_populates="raw_data")
    mappings = relationship("RawDataMapping", back_populates="raw_data", cascade="all, delete-orphan")

    # 索引
    __table_args__ = (
        Index('idx_batch_row', 'import_batch_id', 'row_number'),
        Index('idx_trade_date', 'trade_date'),
        Index('idx_stock_code', 'stock_code_normalized'),
        Index('idx_source_type', 'source_type'),
    )


class RawDataMapping(Base):
    """原始数据到业务数据的映射表 - 用于追踪数据处理过程"""
    __tablename__ = "raw_data_mapping"

    id = Column(Integer, primary_key=True, index=True, comment="主键ID")

    # 原始数据关联
    raw_import_data_id = Column(BigInteger, ForeignKey('raw_import_data.id'), nullable=False, index=True, comment="原始数据ID")

    # 业务数据关联
    stock_id = Column(Integer, comment="股票ID")
    concept_id = Column(Integer, comment="概念ID")
    daily_stock_data_id = Column(Integer, comment="每日股票数据ID")
    stock_concept_id = Column(Integer, comment="股票-概念关联ID")

    # 处理状态
    process_status = Column(String(20), default='pending', index=True, comment="处理状态(pending/success/error)")
    error_message = Column(Text, comment="错误信息")

    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关联关系
    raw_data = relationship("RawImportData", back_populates="mappings")


class StockConceptRawData(Base):
    """CSV原始数据表 - 不拆分存储"""
    __tablename__ = "stock_concept_raw_data"

    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    import_date = Column(Date, nullable=False, index=True, comment="导入日期")
    trade_date = Column(Date, nullable=False, index=True, comment="交易日期")

    # CSV原始字段 - 直接对应
    stock_code = Column(String(10), nullable=False, index=True, comment="股票代码（规范化后）")
    original_stock_code = Column(String(20), comment="原始股票代码（含前缀）")
    stock_code_prefix = Column(String(10), comment="股票代码前缀（SH/SZ/BJ/HK等）")
    stock_name = Column(String(100), nullable=False, comment="股票名称")
    concept = Column(String(100), nullable=False, index=True, comment="概念")
    industry = Column(String(100), comment="行业")

    # 交易数据
    price = Column(DECIMAL(10, 2), default=0, comment="价格")
    turnover_rate = Column(DECIMAL(5, 2), default=0, comment="换手率")
    net_inflow = Column(DECIMAL(15, 2), default=0, comment="净流入")
    pages_count = Column(Integer, default=0, comment="页数")
    total_reads = Column(Integer, default=0, comment="总阅读数")

    # 元数据
    file_name = Column(String(255), comment="来源文件名")
    row_number = Column(Integer, comment="CSV行号")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")

    # 索引
    __table_args__ = (
        Index('idx_raw_trade_date_stock', 'trade_date', 'stock_code'),
        Index('idx_raw_trade_date_concept', 'trade_date', 'concept'),
        Index('idx_raw_stock_concept', 'stock_code', 'concept'),
    )