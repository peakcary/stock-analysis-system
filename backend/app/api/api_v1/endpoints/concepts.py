"""
概念相关API端点
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.admin_auth import get_current_admin_user
from app.core.auth import get_optional_user
from app.crud.user import UserCRUD
from app.models.user import QueryType, User
from typing import Union
from app.core.cache import cache_result
from app.models import Concept, Stock, StockConcept, DailyConceptSum, DailyConceptRanking
from app.schemas.concept import ConceptResponse, ConceptWithStocks, NewHighConcept
from app.schemas.stock import StockWithConcepts
from datetime import date, datetime, timedelta

router = APIRouter()


@router.get("/count")
def get_concepts_count(db: Session = Depends(get_db)):
    """获取概念总数"""
    total_count = db.query(Concept).count()
    return {"total": total_count}


@router.get("/stocks/{stock_code}/concepts", response_model=StockWithConcepts)
def get_stock_concepts(
    stock_code: str,
    db: Session = Depends(get_db),
    current_user: Optional[Union[User, None]] = Depends(get_optional_user)
):
    """
    获取个股的所有概念

    参数：
    - stock_code: 股票代码

    返回：
    - stock: 股票信息
    - concepts: 该股票所属的概念列表
    """
    # 规范化股票代码（添加前缀如 SZ/SH）
    # 先尝试直接查询，如果不存在则尝试添加常见前缀
    stock = db.query(Stock).filter(Stock.stock_code == stock_code).first()

    if not stock:
        # 尝试添加常见前缀
        for prefix in ['SZ', 'SH']:
            stock = db.query(Stock).filter(Stock.stock_code == f"{prefix}{stock_code}").first()
            if stock:
                break

    if not stock:
        raise HTTPException(status_code=404, detail=f"股票不存在: {stock_code}")

    # 如果是客户端用户，消费查询次数并记录查询
    if current_user:
        user_crud = UserCRUD(db)
        # 检查并消费查询次数
        if not user_crud.consume_query(current_user.id, QueryType.STOCK_SEARCH, {
            "stock_code": stock.stock_code
        }):
            raise HTTPException(status_code=403, detail="查询次数不足，请升级会员或购买查询包")

    # 获取股票所属的所有概念 - 优化查询性能
    concepts = db.query(Concept).join(StockConcept).filter(
        StockConcept.stock_id == stock.id
    ).all()

    return {
        "stock": stock,
        "concepts": concepts
    }


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


@router.get("/{concept_name}/stocks")
def get_concept_stocks(
    concept_name: str,
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(20, ge=1, le=100, description="每页记录数"),
    db: Session = Depends(get_db),
    current_user: Optional[Union[User, None]] = Depends(get_optional_user)
):
    """
    获取概念下的股票（分页）

    参数：
    - concept_name: 概念名称
    - skip: 跳过的记录数（分页）
    - limit: 每页记录数（1-100）

    返回：
    - concept: 概念信息
    - total_count: 总股票数
    - stocks: 该页股票列表
    - page_info: 分页信息
    """
    concept = db.query(Concept).filter(Concept.concept_name == concept_name).first()

    if not concept:
        raise HTTPException(status_code=404, detail=f"概念不存在: {concept_name}")

    # 如果是客户端用户，消费查询次数并记录查询
    if current_user:
        user_crud = UserCRUD(db)
        # 检查并消费查询次数
        if not user_crud.consume_query(current_user.id, QueryType.CONCEPT_SEARCH, {
            "concept_name": concept_name
        }):
            raise HTTPException(status_code=403, detail="查询次数不足，请升级会员或购买查询包")

    # 获取总数
    total_count = db.query(Stock).join(StockConcept).filter(
        StockConcept.concept_id == concept.id
    ).count()

    # 获取分页后的股票 - 优化查询性能
    stocks = db.query(Stock).join(StockConcept).filter(
        StockConcept.concept_id == concept.id
    ).offset(skip).limit(limit).all()

    return {
        "concept": concept,
        "total_count": total_count,
        "stocks": stocks,
        "page_info": {
            "skip": skip,
            "limit": limit,
            "total": total_count,
            "has_more": (skip + limit) < total_count
        }
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


@router.get("/top-stocks/{n}")
@cache_result(ttl=300, key_prefix="top_stocks_per_concept")  # 缓存5分钟
def get_top_stocks_for_all_concepts(
    n: int,
    trade_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    获取每个概念的前N只股票（按热度值排序）

    参数：
    - n: 每个概念的前N只股票数（1-50）
    - trade_date: 交易日期（默认为今天）

    返回：
    - 所有概念及其前N只股票的列表
    """
    if trade_date is None:
        trade_date = datetime.now().date()

    # 限制查询数量
    limit_n = min(n, 50)

    # 获取所有概念
    all_concepts = db.query(Concept).all()

    result = []
    for concept in all_concepts:
        # 获取该概念下按热度值排序的前N只股票
        stocks = db.query(Stock).join(
            DailyConceptRanking,
            DailyConceptRanking.stock_id == Stock.id
        ).filter(
            DailyConceptRanking.concept_id == concept.id,
            DailyConceptRanking.trade_date == trade_date
        ).order_by(DailyConceptRanking.heat_value.desc()).limit(limit_n).all()

        if stocks:  # 只返回有股票的概念
            result.append({
                "concept": concept,
                "top_stocks": stocks,
                "count": len(stocks)
            })

    return result


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


@router.get("/bonds/{bond_code}/concepts", response_model=StockWithConcepts)
def get_bond_concepts(
    bond_code: str,
    db: Session = Depends(get_db),
    current_user: Optional[Union[User, None]] = Depends(get_optional_user)
):
    """
    获取转债所属的所有概念

    参数：
    - bond_code: 转债代码

    返回：
    - stock: 转债信息
    - concepts: 该转债所属的概念列表
    """
    # 规范化转债代码（添加前缀如 SZ/SH）
    bond = db.query(Stock).filter(
        Stock.stock_code == bond_code,
        Stock.is_convertible_bond == True
    ).first()

    if not bond:
        # 尝试添加常见前缀
        for prefix in ['SZ', 'SH']:
            bond = db.query(Stock).filter(
                Stock.stock_code == f"{prefix}{bond_code}",
                Stock.is_convertible_bond == True
            ).first()
            if bond:
                break

    if not bond:
        raise HTTPException(status_code=404, detail=f"转债不存在: {bond_code}")

    # 如果是客户端用户，消费查询次数并记录查询
    if current_user:
        user_crud = UserCRUD(db)
        if not user_crud.consume_query(current_user.id, QueryType.STOCK_SEARCH, {
            "bond_code": bond.stock_code
        }):
            raise HTTPException(status_code=403, detail="查询次数不足，请升级会员或购买查询包")

    # 获取转债所属的所有概念
    concepts = db.query(Concept).join(StockConcept).filter(
        StockConcept.stock_id == bond.id
    ).all()

    return {
        "stock": bond,
        "concepts": concepts
    }