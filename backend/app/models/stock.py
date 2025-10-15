"""
股票相关数据模型
"""

from sqlalchemy import Column, Integer, String, Boolean, DECIMAL, Date, DateTime, Text, Enum, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class Stock(Base):
    """股票基本信息表"""
    __tablename__ = "stocks"
    
    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    stock_code = Column(String(10), unique=True, nullable=False, index=True, comment="股票代码")
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


class StockConceptRawData(Base):
    """CSV原始数据表 - 不拆分存储"""
    __tablename__ = "stock_concept_raw_data"

    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    import_date = Column(Date, nullable=False, index=True, comment="导入日期")
    trade_date = Column(Date, nullable=False, index=True, comment="交易日期")

    # CSV原始字段 - 直接对应
    stock_code = Column(String(10), nullable=False, index=True, comment="股票代码")
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