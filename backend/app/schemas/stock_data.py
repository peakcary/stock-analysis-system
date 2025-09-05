"""
股票数据Pydantic模型
Stock Data Pydantic Schemas
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class StockBase(BaseModel):
    """股票基础模型"""
    code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    market: str = Field(..., description="市场")
    industry: Optional[str] = Field(None, description="所属行业")


class StockCreate(StockBase):
    """创建股票"""
    pass


class StockUpdate(BaseModel):
    """更新股票"""
    name: Optional[str] = None
    industry: Optional[str] = None
    is_active: Optional[bool] = None


class StockResponse(StockBase):
    """股票响应"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TradingDataBase(BaseModel):
    """交易数据基础模型"""
    stock_code: str = Field(..., description="股票代码")
    trade_date: datetime = Field(..., description="交易日期")
    volume: Optional[float] = Field(None, description="成交量")
    price: Optional[float] = Field(None, description="价格")
    turnover_rate: Optional[float] = Field(None, description="换手率")
    net_inflow: Optional[float] = Field(None, description="净流入")


class TradingDataCreate(TradingDataBase):
    """创建交易数据"""
    pass


class TradingDataResponse(TradingDataBase):
    """交易数据响应"""
    id: int
    stock_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class ConceptBase(BaseModel):
    """概念基础模型"""
    name: str = Field(..., description="概念名称")
    category: Optional[str] = Field(None, description="概念分类")
    description: Optional[str] = Field(None, description="概念描述")


class ConceptCreate(ConceptBase):
    """创建概念"""
    pass


class ConceptUpdate(BaseModel):
    """更新概念"""
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ConceptResponse(ConceptBase):
    """概念响应"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class StockConceptBase(BaseModel):
    """股票概念关联基础模型"""
    stock_code: str = Field(..., description="股票代码")
    concept_name: str = Field(..., description="概念名称")


class StockConceptCreate(StockConceptBase):
    """创建股票概念关联"""
    pass


class StockConceptResponse(StockConceptBase):
    """股票概念关联响应"""
    id: int
    stock_id: int
    concept_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class AnalysisDataBase(BaseModel):
    """分析数据基础模型"""
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    total_pages: Optional[int] = Field(None, description="全部页数")
    hot_page_views: Optional[int] = Field(None, description="热帖首页阅读总数")
    price: Optional[float] = Field(None, description="股价")
    industry: Optional[str] = Field(None, description="行业")
    turnover_rate: Optional[float] = Field(None, description="换手率")
    net_inflow: Optional[float] = Field(None, description="净流入")
    analysis_date: datetime = Field(..., description="分析日期")


class AnalysisDataCreate(AnalysisDataBase):
    """创建分析数据"""
    pass


class AnalysisDataResponse(AnalysisDataBase):
    """分析数据响应"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class ImportResult(BaseModel):
    """导入结果"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="结果消息")
    imported_count: int = Field(0, description="成功导入数量")
    failed_count: int = Field(0, description="失败数量")
    details: List[str] = Field(default_factory=list, description="详细信息")


class StockConceptSummary(BaseModel):
    """股票概念汇总"""
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    concepts: List[str] = Field(..., description="概念列表")
    
    class Config:
        from_attributes = True