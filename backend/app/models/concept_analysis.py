"""
概念分析相关的数据模型
"""

from sqlalchemy import Column, Integer, String, Date, DECIMAL, Boolean, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime


class DailyConceptRanking(Base):
    """每日概念排名表 - 记录每个股票在其所属概念内的排名"""
    __tablename__ = "daily_concept_rankings"

    id = Column(Integer, primary_key=True, index=True)
    concept_id = Column(Integer, ForeignKey("concepts.id"), nullable=False)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    trade_date = Column(Date, nullable=False)
    rank_in_concept = Column(Integer, nullable=False, comment="股票在概念内的排名")
    heat_value = Column(DECIMAL(15, 2), nullable=False, comment="热度值")
    created_at = Column(Date, default=datetime.now)

    # 关联关系
    concept = relationship("Concept", back_populates="daily_rankings")
    stock = relationship("Stock", back_populates="concept_rankings")

    # 索引
    __table_args__ = (
        # 唯一约束：同一概念、同一股票、同一日期只能有一条记录
        Index('idx_unique_concept_stock_date', 'concept_id', 'stock_id', 'trade_date', unique=True),
        Index('idx_concept_date', 'concept_id', 'trade_date'),
        Index('idx_stock_date', 'stock_id', 'trade_date'),
        Index('idx_trade_date', 'trade_date'),
        Index('idx_rank', 'rank_in_concept'),
    )


class DailyConceptSummary(Base):
    """每日概念汇总表 - 记录每个概念的每日汇总统计数据"""
    __tablename__ = "daily_concept_summaries"

    id = Column(Integer, primary_key=True, index=True)
    concept_id = Column(Integer, ForeignKey("concepts.id"), nullable=False)
    trade_date = Column(Date, nullable=False)
    total_heat_value = Column(DECIMAL(15, 2), nullable=False, comment="概念总热度值")
    stock_count = Column(Integer, nullable=False, comment="概念内股票数量")
    avg_heat_value = Column(DECIMAL(15, 2), nullable=False, comment="平均热度值")
    max_heat_value = Column(DECIMAL(15, 2), nullable=False, comment="最高热度值")
    min_heat_value = Column(DECIMAL(15, 2), nullable=False, comment="最低热度值")
    is_new_high = Column(Boolean, default=False, comment="是否创新高")
    new_high_days = Column(Integer, default=0, comment="创多少天新高")
    created_at = Column(Date, default=datetime.now)

    # 关联关系
    concept = relationship("Concept", back_populates="daily_summaries")

    # 索引
    __table_args__ = (
        # 唯一约束：同一概念、同一日期只能有一条记录
        Index('idx_unique_concept_date', 'concept_id', 'trade_date', unique=True),
        Index('idx_concept_id', 'concept_id'),
        Index('idx_trade_date', 'trade_date'),
        Index('idx_total_heat_desc', 'total_heat_value', postgresql_using='btree'),
        Index('idx_new_high', 'is_new_high', 'trade_date'),
        Index('idx_new_high_days', 'new_high_days'),
    )


class DailyAnalysisTask(Base):
    """每日分析任务表 - 记录数据分析任务的执行状态"""
    __tablename__ = "daily_analysis_tasks"

    id = Column(Integer, primary_key=True, index=True)
    trade_date = Column(Date, nullable=False)
    task_type = Column(String(50), nullable=False, comment="任务类型：ranking_calculation, summary_calculation, innovation_analysis")
    status = Column(String(20), default='pending', comment="任务状态：pending, running, completed, failed")
    started_at = Column(Date, nullable=True)
    completed_at = Column(Date, nullable=True)
    error_message = Column(Text, nullable=True)
    processed_records = Column(Integer, default=0)
    total_records = Column(Integer, default=0)
    created_at = Column(Date, default=datetime.now)
    updated_at = Column(Date, default=datetime.now, onupdate=datetime.now)

    # 索引
    __table_args__ = (
        # 唯一约束：同一日期、同一任务类型只能有一条记录
        Index('idx_unique_date_task', 'trade_date', 'task_type', unique=True),
        Index('idx_trade_date', 'trade_date'),
        Index('idx_status', 'status'),
        Index('idx_task_type', 'task_type'),
    )