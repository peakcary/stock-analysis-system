"""
概念相关的 Pydantic 模式
"""

from pydantic import BaseModel
from typing import List
from datetime import date, datetime
from decimal import Decimal
from app.schemas.stock import StockResponse, ConceptResponse


class ConceptWithStocks(BaseModel):
    """概念及其股票"""
    concept: ConceptResponse
    stocks: List[StockResponse]


class NewHighConcept(BaseModel):
    """创新高的概念"""
    concept: ConceptResponse
    total_heat_value: Decimal
    stock_count: int
    average_heat_value: Decimal
    days_checked: int
    trade_date: date