"""
股票相关数据模型
"""

from sqlalchemy import Column, Integer, String, Boolean, DECIMAL, Date, DateTime, Text, Enum, ForeignKey
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