"""
简化导入数据模型
"""

from sqlalchemy import Column, BigInteger, String, Integer, DECIMAL, Date, DateTime, Text, Enum
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class ImportStatus(str, enum.Enum):
    """导入状态"""
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class FileType(str, enum.Enum):
    """文件类型"""
    CSV = "csv"
    TXT = "txt"


class StockConceptData(Base):
    """股票概念数据表"""
    __tablename__ = "stock_concept_data"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_code = Column(String(20), nullable=False, comment='股票代码')
    stock_name = Column(String(100), nullable=False, comment='股票名称')
    page_count = Column(Integer, default=0, comment='全部页数')
    total_reads = Column(BigInteger, default=0, comment='热帖首页页阅读总数')
    price = Column(DECIMAL(10, 2), default=0, comment='价格')
    industry = Column(String(100), comment='行业')
    concept = Column(String(100), comment='概念')
    turnover_rate = Column(DECIMAL(8, 4), default=0, comment='换手率')
    net_inflow = Column(DECIMAL(15, 2), default=0, comment='净流入')
    import_date = Column(Date, nullable=False, comment='导入日期')
    created_at = Column(DateTime, default=func.now())


class StockTimeseriesData(Base):
    """股票时间序列数据表"""
    __tablename__ = "stock_timeseries_data"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_code = Column(String(20), nullable=False, comment='股票代码')
    trade_date = Column(Date, nullable=False, comment='交易日期')
    value = Column(DECIMAL(15, 2), nullable=False, comment='数值')
    import_date = Column(Date, nullable=False, comment='导入日期')
    created_at = Column(DateTime, default=func.now())


class ImportTask(Base):
    """导入任务记录表"""
    __tablename__ = "import_tasks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_name = Column(String(255), nullable=False, comment='文件名')
    file_type = Column(String(10), nullable=False, comment='文件类型')
    file_size = Column(BigInteger, nullable=False, comment='文件大小(字节)')
    total_rows = Column(BigInteger, default=0, comment='总行数')
    success_rows = Column(BigInteger, default=0, comment='成功行数')
    error_rows = Column(BigInteger, default=0, comment='错误行数')
    status = Column(String(20), default='processing', comment='状态')
    error_message = Column(Text, comment='错误信息')
    start_time = Column(DateTime, comment='开始时间')
    end_time = Column(DateTime, comment='结束时间')
    created_at = Column(DateTime, default=func.now())