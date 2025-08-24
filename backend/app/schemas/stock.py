"""
股票相关的 Pydantic 模式
"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal


class StockBase(BaseModel):
    """股票基础模式"""
    stock_code: str
    stock_name: str
    industry: Optional[str] = None
    is_convertible_bond: bool = False


class StockResponse(StockBase):
    """股票响应模式"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ConceptBase(BaseModel):
    """概念基础模式"""
    concept_name: str
    description: Optional[str] = None


class ConceptResponse(ConceptBase):
    """概念响应模式"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class StockWithConcepts(BaseModel):
    """股票及其概念"""
    stock: StockResponse
    concepts: List[ConceptResponse]


class StockChartData(BaseModel):
    """股票图表数据"""
    trade_date: date
    price: Decimal
    turnover_rate: Decimal
    net_inflow: Decimal
    heat_value: Decimal
    pages_count: int
    total_reads: int
    
    class Config:
        from_attributes = True