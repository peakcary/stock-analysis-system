"""
股票概念分析数据模型
Stock Concept Analysis Data Models
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Boolean, ForeignKey, Index, Date, BigInteger
from sqlalchemy.orm import relationship
from datetime import datetime, date

from app.core.database import Base


class StockInfo(Base):
    """股票基础信息表"""
    __tablename__ = "stock_concept_info"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, index=True, nullable=False, comment="股票代码(纯数字)")
    name = Column(String(100), comment="股票名称") 
    market = Column(String(10), comment="市场(SH/SZ)")
    current_industry = Column(String(100), comment="当前行业")
    is_active = Column(Boolean, default=True, comment="是否有效")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    
    def __repr__(self):
        return f"<Stock(code={self.code}, name={self.name})>"


class DailyStockConceptData(Base):
    """每日股票概念数据表"""
    __tablename__ = "stock_concept_daily_data"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String(20), nullable=False, index=True, comment="股票代码")
    stock_name = Column(String(100), comment="股票名称")
    trade_date = Column(Date, nullable=False, index=True, comment="交易日期")
    
    # 从CSV文件导入的数据
    total_pages = Column(Integer, comment="全部页数")
    hot_page_views = Column(Integer, comment="热帖首页页阅读总数") 
    price = Column(Float, comment="价格")
    industry = Column(String(100), comment="行业")
    turnover_rate = Column(Float, comment="换手率")
    net_inflow = Column(Float, comment="净流入")
    
    # 从TXT文件导入的数据
    volume = Column(BigInteger, comment="成交量")
    
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    
    __table_args__ = (
        Index("ix_stock_date_unique", "stock_code", "trade_date", unique=True),
    )
    
    def __repr__(self):
        return f"<DailyStockConceptData(code={self.stock_code}, date={self.trade_date})>"


class StockConceptCategory(Base):
    """股票概念分类表"""
    __tablename__ = "stock_concept_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True, comment="概念名称")
    category = Column(String(50), comment="概念分类(行业/板块/主题/指数等)")
    description = Column(Text, comment="概念描述")
    is_active = Column(Boolean, default=True, comment="是否有效")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    
    def __repr__(self):
        return f"<StockConceptCategory(name={self.name})>"


class DailyStockConcept(Base):
    """每日股票概念关联表"""
    __tablename__ = "stock_concept_daily_relations"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String(20), nullable=False, index=True, comment="股票代码")
    concept_name = Column(String(100), nullable=False, comment="概念名称")
    trade_date = Column(Date, nullable=False, index=True, comment="交易日期")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    
    __table_args__ = (
        Index("ix_stock_concept_date_unique", "stock_code", "concept_name", "trade_date", unique=True),
        Index("ix_concept_date", "concept_name", "trade_date"),
    )
    
    def __repr__(self):
        return f"<DailyStockConcept(code={self.stock_code}, concept={self.concept_name}, date={self.trade_date})>"


class ConceptDailyStats(Base):
    """概念每日统计表"""
    __tablename__ = "stock_concept_daily_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    concept_name = Column(String(100), nullable=False, index=True, comment="概念名称")
    trade_date = Column(Date, nullable=False, index=True, comment="交易日期")
    
    # 统计数据
    total_volume = Column(BigInteger, comment="概念总成交量")
    stock_count = Column(Integer, comment="概念内股票数量")
    avg_volume = Column(Float, comment="平均成交量")
    max_volume = Column(BigInteger, comment="最大成交量")
    min_volume = Column(BigInteger, comment="最小成交量")
    
    # 热度数据
    total_hot_views = Column(BigInteger, comment="总热度页面阅读数")
    avg_hot_views = Column(Float, comment="平均热度")
    
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    
    __table_args__ = (
        Index("ix_concept_stats_date_unique", "concept_name", "trade_date", unique=True),
    )
    
    def __repr__(self):
        return f"<ConceptDailyStats(concept={self.concept_name}, date={self.trade_date})>"


class StockConceptRanking(Base):
    """股票在概念中的每日排名表"""
    __tablename__ = "stock_concept_daily_rankings"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String(20), nullable=False, index=True, comment="股票代码")
    stock_name = Column(String(100), comment="股票名称")
    concept_name = Column(String(100), nullable=False, index=True, comment="概念名称")
    trade_date = Column(Date, nullable=False, index=True, comment="交易日期")
    
    # 排名数据
    volume_rank = Column(Integer, comment="成交量排名")
    volume = Column(BigInteger, comment="成交量")
    volume_ratio = Column(Float, comment="成交量占概念总量比例(%)")
    
    # 热度排名
    hot_views_rank = Column(Integer, comment="热度排名")
    hot_page_views = Column(Integer, comment="热帖页面阅读数")
    hot_views_ratio = Column(Float, comment="热度占概念总热度比例(%)")
    
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    
    __table_args__ = (
        Index("ix_stock_concept_rank_date", "stock_code", "concept_name", "trade_date", unique=True),
        Index("ix_concept_volume_rank", "concept_name", "trade_date", "volume_rank"),
        Index("ix_concept_hot_rank", "concept_name", "trade_date", "hot_views_rank"),
    )
    
    def __repr__(self):
        return f"<StockConceptRanking(code={self.stock_code}, concept={self.concept_name}, date={self.trade_date})>"


class DataImportLog(Base):
    """数据导入日志表"""
    __tablename__ = "stock_concept_import_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    import_date = Column(Date, nullable=False, index=True, comment="导入数据日期")
    import_type = Column(String(20), nullable=False, comment="导入类型(csv/txt/both)")
    file_name = Column(String(200), comment="文件名")
    
    # 统计信息
    total_records = Column(Integer, comment="总记录数")
    success_records = Column(Integer, comment="成功记录数")
    failed_records = Column(Integer, comment="失败记录数")
    
    # 处理结果
    status = Column(String(20), default='processing', comment="状态(processing/success/failed)")
    error_message = Column(Text, comment="错误信息")
    processing_time = Column(Float, comment="处理时间(秒)")
    
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    completed_at = Column(DateTime, comment="完成时间")
    
    def __repr__(self):
        return f"<DataImportLog(date={self.import_date}, type={self.import_type})>"