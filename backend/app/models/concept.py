"""
概念相关数据模型
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Date, DECIMAL, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Concept(Base):
    """概念表"""
    __tablename__ = "concepts"
    
    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    concept_name = Column(String(100), unique=True, nullable=False, index=True, comment="概念名称")
    description = Column(Text, comment="概念描述")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    
    # 关联关系
    stock_concepts = relationship("StockConcept", back_populates="concept", cascade="all, delete-orphan")
    concept_sums = relationship("DailyConceptSum", back_populates="concept", cascade="all, delete-orphan")


class StockConcept(Base):
    """股票概念关联表"""
    __tablename__ = "stock_concepts"
    
    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    stock_id = Column(Integer, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False, index=True, comment="股票ID")
    concept_id = Column(Integer, ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True, comment="概念ID")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    
    # 关联关系
    stock = relationship("Stock", back_populates="stock_concepts")
    concept = relationship("Concept", back_populates="stock_concepts")


class DailyConceptSum(Base):
    """每日概念总和表"""
    __tablename__ = "daily_concept_sums"
    
    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    concept_id = Column(Integer, ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True, comment="概念ID")
    trade_date = Column(Date, nullable=False, index=True, comment="交易日期")
    total_heat_value = Column(DECIMAL(15, 2), nullable=False, index=True, comment="概念总热度值")
    stock_count = Column(Integer, nullable=False, comment="概念包含股票数量")
    average_heat_value = Column(DECIMAL(15, 2), nullable=False, comment="平均热度值")
    is_new_high = Column(Boolean, default=False, index=True, comment="是否创新高")
    days_for_high_check = Column(Integer, default=10, comment="新高检查天数")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    
    # 关联关系
    concept = relationship("Concept", back_populates="concept_sums")