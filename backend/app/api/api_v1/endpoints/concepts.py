"""
概念相关API端点
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.admin_auth import get_current_admin_user
from app.core.cache import cache_result
from app.models import Concept, Stock, StockConcept, DailyConceptSum
from app.schemas.concept import ConceptResponse, ConceptWithStocks, NewHighConcept
from datetime import date, datetime, timedelta

router = APIRouter()


@router.get("/count")
def get_concepts_count(db: Session = Depends(get_db)):
    """获取概念总数"""
    total_count = db.query(Concept).count()
    return {"total": total_count}


@router.get("/", response_model=List[ConceptResponse])
def get_concepts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
):
    """获取概念列表"""
    # 优化查询性能 - 添加排序和限制
    concepts = db.query(Concept).order_by(Concept.id).offset(skip).limit(min(limit, 500)).all()
    return concepts


@router.get("/{concept_name}/stocks", response_model=ConceptWithStocks)
def get_concept_stocks(
    concept_name: str, 
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
):
    """获取概念下的所有股票"""
    concept = db.query(Concept).filter(Concept.concept_name == concept_name).first()
    
    if not concept:
        raise HTTPException(status_code=404, detail="概念不存在")
    
    # 获取概念下的所有股票 - 优化查询性能
    stocks = db.query(Stock).join(StockConcept).filter(
        StockConcept.concept_id == concept.id
    ).limit(200).all()  # 限制股票数量避免过大查询
    
    return {
        "concept": concept,
        "stocks": stocks
    }


@router.get("/top/{n}", response_model=List[ConceptResponse])
@cache_result(ttl=300, key_prefix="top_concepts")  # 缓存5分钟
def get_top_concepts(n: int, trade_date: Optional[date] = None, db: Session = Depends(get_db)):
    """获取前N个概念（按热度值排序）"""
    if trade_date is None:
        trade_date = datetime.now().date()
    
    # 限制查询数量避免过大查询
    limit_n = min(n, 100)
    
    # 查询指定日期的概念总和数据，按热度值排序
    concept_sums = db.query(DailyConceptSum).filter(
        DailyConceptSum.trade_date == trade_date
    ).order_by(DailyConceptSum.total_heat_value.desc()).limit(limit_n).all()
    
    # 获取对应的概念信息
    concept_ids = [cs.concept_id for cs in concept_sums]
    concepts = db.query(Concept).filter(Concept.id.in_(concept_ids)).all()
    
    # 按照热度值排序返回
    concept_dict = {c.id: c for c in concepts}
    sorted_concepts = [concept_dict[cs.concept_id] for cs in concept_sums if cs.concept_id in concept_dict]
    
    return sorted_concepts


@router.get("/new-highs", response_model=List[NewHighConcept])
@cache_result(ttl=600, key_prefix="new_highs")  # 缓存10分钟
def get_new_high_concepts(
    days: int = Query(default=10, description="检查创新高的天数"),
    trade_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """获取创新高的概念"""
    if trade_date is None:
        trade_date = datetime.now().date()
    
    # 查询创新高的概念 - 优化查询性能
    new_high_sums = db.query(DailyConceptSum).join(Concept).filter(
        DailyConceptSum.trade_date == trade_date,
        DailyConceptSum.is_new_high == True,
        DailyConceptSum.days_for_high_check == days
    ).limit(50).all()  # 限制查询结果数量
    
    result = []
    for concept_sum in new_high_sums:
        result.append({
            "concept": concept_sum.concept,
            "total_heat_value": concept_sum.total_heat_value,
            "stock_count": concept_sum.stock_count,
            "average_heat_value": concept_sum.average_heat_value,
            "days_checked": concept_sum.days_for_high_check,
            "trade_date": concept_sum.trade_date
        })
    
    return result