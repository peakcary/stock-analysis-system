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


class EeeDailyTrading(Base):
    """EEE热度数据表 - 存储EEE.txt导入的原始热度数据"""
    __tablename__ = "eee_daily_trading"

    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    original_stock_code = Column(String(20), nullable=False, index=True, comment="原始股票代码（含前缀）")
    normalized_stock_code = Column(String(10), nullable=False, index=True, comment="规范化代码")
    stock_code = Column(String(20), nullable=False, index=True, comment="股票代码")
    trading_date = Column(Date, nullable=False, index=True, comment="交易日期")
    trading_volume = Column(Integer, nullable=False, comment="热度值")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")

    # 约束条件
    __table_args__ = (
        Index('idx_eee_stock_date', 'stock_code', 'trading_date'),
        Index('idx_eee_date_volume', 'trading_date', 'trading_volume'),
    )


class EeeImportRecord(Base):
    """EEE导入记录表 - 记录导入元信息"""
    __tablename__ = "eee_import_record"

    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    filename = Column(String(255), nullable=False, comment="文件名")
    trading_date = Column(Date, nullable=False, comment="交易日期")
    file_size = Column(BigInteger, nullable=False, comment="文件大小")
    file_hash = Column(String(64), comment="文件哈希")
    import_status = Column(String(20), nullable=False, default='processing', comment="导入状态")
    imported_by = Column(String(50), nullable=False, comment="导入人")
    import_mode = Column(String(20), comment="导入模式")
    total_records = Column(Integer, default=0, comment="总记录数")
    success_records = Column(Integer, default=0, comment="成功记录数")
    error_records = Column(Integer, default=0, comment="错误记录数")
    duplicate_records = Column(Integer, default=0, comment="重复记录数")
    concept_count = Column(Integer, default=0, comment="概念数")
    ranking_count = Column(Integer, default=0, comment="排名数")
    new_high_count = Column(Integer, default=0, comment="创新高数")
    import_started_at = Column(DateTime, nullable=False, comment="导入开始时间")
    import_completed_at = Column(DateTime, comment="导入完成时间")
    calculation_time = Column(DECIMAL(10, 3), default=0, comment="计算耗时")
    error_message = Column(Text, comment="错误信息")
    notes = Column(Text, comment="备注")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")


class TtvDailyTrading(Base):
    """TTV交易数据表 - 存储TTV.txt导入的原始数据"""
    __tablename__ = "ttv_daily_trading"

    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    original_stock_code = Column(String(20), nullable=False, index=True, comment="原始股票代码（含前缀）")
    normalized_stock_code = Column(String(10), nullable=False, index=True, comment="规范化代码")
    stock_code = Column(String(20), nullable=False, index=True, comment="股票代码")
    trading_date = Column(Date, nullable=False, index=True, comment="交易日期")
    trading_volume = Column(Integer, nullable=False, comment="交易值")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")

    # 约束条件
    __table_args__ = (
        Index('idx_ttv_stock_date', 'stock_code', 'trading_date'),
        Index('idx_ttv_date_volume', 'trading_date', 'trading_volume'),
    )


class TtvImportRecord(Base):
    """TTV导入记录表 - 记录导入元信息"""
    __tablename__ = "ttv_import_record"

    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    filename = Column(String(255), nullable=False, comment="文件名")
    trading_date = Column(Date, nullable=False, comment="交易日期")
    file_size = Column(BigInteger, nullable=False, comment="文件大小")
    file_hash = Column(String(64), comment="文件哈希")
    import_status = Column(String(20), nullable=False, default='processing', comment="导入状态")
    imported_by = Column(String(50), nullable=False, comment="导入人")
    import_mode = Column(String(20), comment="导入模式")
    total_records = Column(Integer, default=0, comment="总记录数")
    success_records = Column(Integer, default=0, comment="成功记录数")
    error_records = Column(Integer, default=0, comment="错误记录数")
    duplicate_records = Column(Integer, default=0, comment="重复记录数")
    concept_count = Column(Integer, default=0, comment="概念数")
    ranking_count = Column(Integer, default=0, comment="排名数")
    new_high_count = Column(Integer, default=0, comment="创新高数")
    import_started_at = Column(DateTime, nullable=False, comment="导入开始时间")
    import_completed_at = Column(DateTime, comment="导入完成时间")
    calculation_time = Column(DECIMAL(10, 3), default=0, comment="计算耗时")
    error_message = Column(Text, comment="错误信息")
    notes = Column(Text, comment="备注")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")


class StockDailyMetrics(Base):
    """统一的每日股票指标汇总表 - 支持多种指标类型
    
    用途：存储各种类型的时间序列数据（热度、交易量等）
    设计：单表存储多种指标，通过 metric_type 区分
    支持：EEE热度数据、TTV交易量数据及未来的其他指标
    """
    __tablename__ = "stock_daily_metrics"

    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    
    # 股票关联
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False, index=True, comment="股票ID")
    
    # 时间维度
    trade_date = Column(Date, nullable=False, index=True, comment="交易日期")
    
    # 指标类型（eee_heat, ttv_trading_volume, 等）
    metric_type = Column(String(50), nullable=False, index=True, comment="指标类型")
    
    # 指标值
    metric_value = Column(DECIMAL(15, 2), nullable=False, comment="指标数值")
    
    # 相关的汇总数据（冗余存储，加快查询）
    # 在该概念中的排名（0表示未计算）
    ranking_in_concept = Column(Integer, default=0, comment="在概念中的排名")
    
    # 在该概念中的占比（百分比）
    percentage_in_concept = Column(DECIMAL(5, 2), default=0, comment="在概念中的占比百分比")
    
    # 元数据
    data_source = Column(String(20), comment="数据来源（csv/eee/ttv等）")
    is_recalculated = Column(Boolean, default=False, index=True, comment="是否为重新计算的数据")
    
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关联关系
    stock = relationship("Stock", foreign_keys=[stock_id])
    
    # 索引
    __table_args__ = (
        Index('idx_stock_date_type', 'stock_id', 'trade_date', 'metric_type'),
        Index('idx_metric_type_date', 'metric_type', 'trade_date'),
        Index('idx_date_metric_value', 'trade_date', 'metric_value'),
    )


class ConceptMetricsSummary(Base):
    """概念指标汇总表 - 支持多种指标类型的概念级聚合
    
    用途：存储按概念聚合的各种指标（热度和、热度均值等）
    支持：快速查询概念的日度汇总指标
    """
    __tablename__ = "concept_metrics_summary"

    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    
    # 概念关联
    concept_id = Column(Integer, ForeignKey('concepts.id'), nullable=False, index=True, comment="概念ID")
    
    # 时间维度
    trade_date = Column(Date, nullable=False, index=True, comment="交易日期")
    
    # 指标类型
    metric_type = Column(String(50), nullable=False, index=True, comment="指标类型")
    
    # 聚合指标
    total_value = Column(DECIMAL(15, 2), nullable=False, comment="指标总值")
    avg_value = Column(DECIMAL(15, 2), nullable=False, comment="指标平均值")
    max_value = Column(DECIMAL(15, 2), nullable=False, comment="指标最大值")
    min_value = Column(DECIMAL(15, 2), nullable=False, comment="指标最小值")
    
    # 股票数量
    stock_count = Column(Integer, nullable=False, comment="参与计算的股票数")
    
    # 创新高信息
    is_new_high = Column(Boolean, default=False, comment="是否创新高")
    historical_max = Column(DECIMAL(15, 2), comment="历史最大值")
    
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关联关系
    concept = relationship("Concept", foreign_keys=[concept_id])
    
    # 索引
    __table_args__ = (
        Index('idx_concept_date_type', 'concept_id', 'trade_date', 'metric_type'),
        Index('idx_metric_type_date', 'metric_type', 'trade_date'),
        Index('idx_date_is_new_high', 'trade_date', 'is_new_high'),
    )


class MetricsCalculationTask(Base):
    """指标计算任务表 - 支持可重新计算的计算任务管理
    
    用途：记录指标计算任务的执行情况，支持重新计算和审计
    功能：
      - 追踪计算任务的执行时间和状态
      - 支持失败重试
      - 支持数据版本管理
    """
    __tablename__ = "metrics_calculation_task"

    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    
    # 任务标识
    task_type = Column(String(50), nullable=False, index=True, comment="任务类型（daily_ranking/concept_summary等）")
    
    # 时间维度
    target_date = Column(Date, nullable=False, index=True, comment="目标计算日期")
    
    # 指标类型（可选，用于指定计算特定指标）
    metric_type = Column(String(50), comment="指标类型过滤（留空则处理所有）")
    
    # 任务状态
    status = Column(String(20), nullable=False, default='pending', index=True, 
                   comment="任务状态：pending/processing/success/failed/partial")
    
    # 执行信息
    started_at = Column(DateTime, comment="开始时间")
    completed_at = Column(DateTime, comment="完成时间")
    duration_seconds = Column(Integer, comment="执行耗时（秒）")
    
    # 处理统计
    total_items = Column(Integer, default=0, comment="总处理项数")
    success_items = Column(Integer, default=0, comment="成功项数")
    failed_items = Column(Integer, default=0, comment="失败项数")
    
    # 错误和日志
    error_message = Column(Text, comment="错误信息")
    log_details = Column(Text, comment="详细日志")
    
    # 重试信息
    retry_count = Column(Integer, default=0, comment="重试次数")
    max_retries = Column(Integer, default=3, comment="最大重试次数")
    
    # 数据版本
    data_version = Column(String(50), comment="数据版本标识")
    is_latest = Column(Boolean, default=True, index=True, comment="是否为最新版本")
    
    created_by = Column(String(50), comment="任务创建人")
    remarks = Column(Text, comment="备注说明")
    
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 索引
    __table_args__ = (
        Index('idx_task_type_date', 'task_type', 'target_date'),
        Index('idx_task_status_date', 'status', 'target_date'),
        Index('idx_date_is_latest', 'target_date', 'is_latest'),
    )
