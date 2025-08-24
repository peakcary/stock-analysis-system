"""
股票相关API端点
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Union
from app.core.database import get_db
from app.core.auth import get_optional_user, require_queries_remaining
from app.crud.user import UserCRUD
from app.models import Stock, DailyStockData, StockConcept, Concept, User
from app.models.user import QueryType
from app.schemas.stock import StockResponse, StockWithConcepts, StockChartData
from datetime import date

router = APIRouter()


@router.get("/", response_model=List[StockResponse])
def get_stocks(
    skip: int = 0,
    limit: int = 100,
    is_bond: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """获取股票列表"""
    query = db.query(Stock)
    
    if is_bond is not None:
        query = query.filter(Stock.is_convertible_bond == is_bond)
    
    # 添加索引优化查询
    query = query.order_by(Stock.id)
    
    stocks = query.offset(skip).limit(min(limit, 1000)).all()
    return stocks


@router.get("/{stock_code}", response_model=StockWithConcepts)
def get_stock_by_code(
    stock_code: str, 
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """根据股票代码获取股票信息和所属概念"""
    stock = db.query(Stock).filter(Stock.stock_code == stock_code).first()
    
    if not stock:
        raise HTTPException(status_code=404, detail="股票不存在")
    
    # 如果用户已登录，消费查询次数
    if current_user:
        user_crud = UserCRUD(db)
        if current_user.queries_remaining > 0:
            user_crud.consume_query(
                current_user.id, 
                QueryType.STOCK_SEARCH, 
                {"stock_code": stock_code}
            )
        else:
            raise HTTPException(
                status_code=403, 
                detail="查询次数已用完，请升级会员"
            )
    
    # 获取股票所属的概念 - 优化查询性能
    concepts = db.query(Concept).join(StockConcept).filter(
        StockConcept.stock_id == stock.id
    ).limit(50).all()  # 限制概念数量避免过大查询
    
    return {
        "stock": stock,
        "concepts": concepts
    }


@router.get("/{stock_code}/chart", response_model=List[StockChartData])
def get_stock_chart_data(
    stock_code: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    days: int = Query(default=30, description="获取最近天数的数据"),
    db: Session = Depends(get_db)
):
    """获取股票图表数据"""
    stock = db.query(Stock).filter(Stock.stock_code == stock_code).first()
    
    if not stock:
        raise HTTPException(status_code=404, detail="股票不存在")
    
    query = db.query(DailyStockData).filter(DailyStockData.stock_id == stock.id)
    
    if start_date and end_date:
        query = query.filter(
            DailyStockData.trade_date >= start_date,
            DailyStockData.trade_date <= end_date
        )
    else:
        # 获取最近N天的数据
        query = query.order_by(DailyStockData.trade_date.desc()).limit(days)
    
    chart_data = query.order_by(DailyStockData.trade_date).all()
    
    return chart_data