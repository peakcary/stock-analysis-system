"""
每日分析汇总数据模型
"""

from sqlalchemy import Column, BigInteger, String, Integer, DECIMAL, Date, DateTime, Text, Index
from sqlalchemy.sql import func
from app.core.database import Base


class DailyConceptRanking(Base):
    """概念内个股每日排名表"""
    __tablename__ = "daily_stock_concept_rankings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_date = Column(Date, nullable=False, comment='分析日期')
    concept = Column(String(100), nullable=False, comment='概念名称')
    stock_code = Column(String(20), nullable=False, comment='股票代码')
    stock_name = Column(String(100), nullable=False, comment='股票名称')
    
    # 排名指标
    net_inflow_rank = Column(Integer, comment='净流入排名')
    price_rank = Column(Integer, comment='价格排名') 
    turnover_rate_rank = Column(Integer, comment='换手率排名')
    total_reads_rank = Column(Integer, comment='阅读量排名')
    
    # 原始数据
    net_inflow = Column(DECIMAL(15, 2), comment='净流入')
    price = Column(DECIMAL(10, 2), comment='价格')
    turnover_rate = Column(DECIMAL(8, 4), comment='换手率')
    total_reads = Column(BigInteger, comment='总阅读量')
    page_count = Column(Integer, comment='页面数量')
    industry = Column(String(100), comment='行业')
    
    created_at = Column(DateTime, default=func.now())
    
    # 创建复合索引提升查询性能
    __table_args__ = (
        Index('idx_analysis_date_concept', 'analysis_date', 'concept'),
        Index('idx_analysis_date_stock', 'analysis_date', 'stock_code'),
        Index('idx_concept_net_inflow_rank', 'concept', 'net_inflow_rank'),
    )


class DailyConceptSummary(Base):
    """概念每日总和统计表"""
    __tablename__ = "daily_concept_summaries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_date = Column(Date, nullable=False, comment='分析日期')
    concept = Column(String(100), nullable=False, comment='概念名称')
    
    # 统计指标
    stock_count = Column(Integer, nullable=False, comment='个股数量')
    total_net_inflow = Column(DECIMAL(18, 2), nullable=False, comment='净流入总和')
    avg_net_inflow = Column(DECIMAL(15, 2), comment='净流入平均值')
    total_market_value = Column(DECIMAL(18, 2), comment='总市值（价格*某个系数）')
    avg_price = Column(DECIMAL(10, 2), comment='平均价格')
    avg_turnover_rate = Column(DECIMAL(8, 4), comment='平均换手率')
    total_reads = Column(BigInteger, comment='总阅读量')
    total_pages = Column(BigInteger, comment='总页面数')
    
    # 排名数据  
    concept_rank = Column(Integer, comment='概念排名（按净流入总和）')
    
    created_at = Column(DateTime, default=func.now())
    
    # 创建索引
    __table_args__ = (
        Index('idx_analysis_date', 'analysis_date'),
        Index('idx_analysis_date_concept_unique', 'analysis_date', 'concept', unique=True),
        Index('idx_concept_rank', 'analysis_date', 'concept_rank'),
    )


class DailyAnalysisTask(Base):
    """每日分析任务记录表"""
    __tablename__ = "daily_analysis_tasks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_date = Column(Date, nullable=False, comment='分析日期')
    task_type = Column(String(50), nullable=False, comment='任务类型：concept_ranking, concept_summary')
    status = Column(String(20), default='processing', comment='状态：processing, completed, failed')
    
    # 统计信息
    processed_concepts = Column(Integer, default=0, comment='处理的概念数量')
    processed_stocks = Column(Integer, default=0, comment='处理的个股数量')
    source_data_count = Column(Integer, comment='源数据条数')
    
    start_time = Column(DateTime, comment='开始时间')
    end_time = Column(DateTime, comment='结束时间')
    error_message = Column(Text, comment='错误信息')
    created_at = Column(DateTime, default=func.now())
    
    # 创建索引
    __table_args__ = (
        Index('idx_analysis_date_type', 'analysis_date', 'task_type'),
    )