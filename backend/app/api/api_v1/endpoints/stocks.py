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


@router.get("/count")
def get_stocks_count(
    is_bond: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """获取股票总数"""
    query = db.query(Stock)
    
    if is_bond is not None:
        query = query.filter(Stock.is_convertible_bond == is_bond)
    
    total_count = query.count()
    return {"total": total_count}


@router.get("/", response_model=List[StockResponse])
def get_stocks(
    skip: int = 0,
    limit: int = 100,
    is_bond: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取股票列表"""
    try:
        # 使用 options 来控制关系加载，避免 N+1 查询问题
        from sqlalchemy.orm import lazyload
        
        query = db.query(Stock).options(
            lazyload(Stock.stock_concepts),
            lazyload(Stock.daily_data), 
            lazyload(Stock.concept_rankings)
        )
        
        if is_bond is not None:
            query = query.filter(Stock.is_convertible_bond == is_bond)
        
        # 搜索功能：支持股票代码、名称、行业搜索
        if search and search.strip():
            search_term = f"%{search.strip()}%"
            query = query.filter(
                (Stock.stock_code.like(search_term)) |
                (Stock.stock_name.like(search_term)) |
                (Stock.industry.like(search_term))
            )
        
        # 添加索引优化查询
        query = query.order_by(Stock.id)
        
        stocks = query.offset(skip).limit(limit).all()
        return stocks
    except Exception as e:
        print(f"Error in get_stocks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取股票列表失败: {str(e)}")


@router.get("/test")
def test_stocks(db: Session = Depends(get_db)):
    """测试股票端点"""
    try:
        count = db.query(Stock).count()
        return {"message": f"成功连接，共有 {count} 只股票"}
    except Exception as e:
        return {"error": str(e)}


@router.get("/simple")
def get_stocks_simple(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    include_concepts: bool = Query(default=True, description="是否包含概念信息"),
    db: Session = Depends(get_db)
):
    """简单的股票列表获取（避免关系加载问题）"""
    try:
        from sqlalchemy import text
        
        # 构建基础查询和概念搜索
        if search and search.strip():
            search_term = f"%{search.strip()}%"
            
            # 首先通过概念查找相关的股票ID
            concept_stock_ids_sql = """
            SELECT DISTINCT s.id 
            FROM stocks s
            JOIN stock_concepts sc ON s.id = sc.stock_id 
            JOIN concepts c ON sc.concept_id = c.id 
            WHERE c.concept_name LIKE :concept_search
            """
            
            concept_result = db.execute(text(concept_stock_ids_sql), {'concept_search': search_term})
            concept_stock_ids = [row[0] for row in concept_result.fetchall()]
            
            # 构建主查询，包含基础搜索和概念搜索结果
            if concept_stock_ids:
                concept_ids_placeholder = ','.join([f':concept_stock_id_{i}' for i in range(len(concept_stock_ids))])
                sql = f"""
                SELECT DISTINCT s.id, s.stock_code, s.stock_name, s.industry, s.is_convertible_bond, s.created_at, s.updated_at 
                FROM stocks s
                WHERE s.stock_code LIKE :search 
                   OR s.stock_name LIKE :search 
                   OR s.industry LIKE :search
                   OR s.id IN ({concept_ids_placeholder})
                """
                params = {'search': search_term}
                for i, stock_id in enumerate(concept_stock_ids):
                    params[f'concept_stock_id_{i}'] = stock_id
            else:
                # 如果没有匹配的概念，只使用基础搜索
                sql = """
                SELECT s.id, s.stock_code, s.stock_name, s.industry, s.is_convertible_bond, s.created_at, s.updated_at 
                FROM stocks s
                WHERE s.stock_code LIKE :search 
                   OR s.stock_name LIKE :search 
                   OR s.industry LIKE :search
                """
                params = {'search': search_term}
        else:
            # 没有搜索条件时的基础查询
            sql = "SELECT s.id, s.stock_code, s.stock_name, s.industry, s.is_convertible_bond, s.created_at, s.updated_at FROM stocks s"
            params = {}
        
        sql += " ORDER BY s.id LIMIT :limit OFFSET :offset"
        params.update({'limit': limit, 'offset': skip})
        
        result = db.execute(text(sql), params)
        rows = result.fetchall()
        
        # 手动构建响应数据
        stocks = []
        stock_ids = []
        
        for row in rows:
            stock_data = {
                "id": row[0],
                "stock_code": row[1],
                "stock_name": row[2],
                "industry": row[3],
                "is_convertible_bond": bool(row[4]),
                "created_at": row[5].isoformat() if row[5] else None,
                "updated_at": row[6].isoformat() if row[6] else None,
                "concepts": []
            }
            stocks.append(stock_data)
            stock_ids.append(row[0])
        
        # 如果需要包含概念信息，批量获取（限制每只股票最多3个概念）
        if include_concepts and stock_ids:
            concepts_sql = """
            SELECT sc.stock_id, c.id, c.concept_name
            FROM stock_concepts sc 
            JOIN concepts c ON sc.concept_id = c.id 
            WHERE sc.stock_id IN ({}) 
            ORDER BY sc.stock_id, c.id
            """.format(','.join([':stock_id_' + str(i) for i in range(len(stock_ids))]))
            
            concept_params = {f'stock_id_{i}': stock_id for i, stock_id in enumerate(stock_ids)}
            
            concept_result = db.execute(text(concepts_sql), concept_params)
            concept_rows = concept_result.fetchall()
            
            # 组织概念数据，每只股票显示前3个概念
            concepts_map = {}
            for concept_row in concept_rows:
                stock_id = concept_row[0]
                if stock_id not in concepts_map:
                    concepts_map[stock_id] = []
                if len(concepts_map[stock_id]) < 3:  # 只显示前3个概念
                    concepts_map[stock_id].append({
                        "id": concept_row[1],
                        "concept_name": concept_row[2]
                    })
            
            # 将概念信息添加到股票数据中
            for stock in stocks:
                stock["concepts"] = concepts_map.get(stock["id"], [])
        
        return stocks
    except Exception as e:
        print(f"Error in get_stocks_simple: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取股票列表失败: {str(e)}")


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
    
    # 如果用户已登录且不是管理员，消费查询次数
    if current_user and current_user.username != 'admin':
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


@router.delete("/batch")
def batch_delete_stocks(
    request: dict,
    db: Session = Depends(get_db)
):
    """批量删除股票"""
    try:
        stock_ids = request.get("stock_ids", [])
        if not stock_ids:
            raise HTTPException(status_code=400, detail="请提供要删除的股票ID列表")
        
        # 查找要删除的股票
        stocks = db.query(Stock).filter(Stock.id.in_(stock_ids)).all()
        if not stocks:
            raise HTTPException(status_code=404, detail="未找到要删除的股票")
        
        # 批量删除关联的概念关系
        db.query(StockConcept).filter(StockConcept.stock_id.in_(stock_ids)).delete()
        
        # 批量删除关联的日线数据
        db.query(DailyStockData).filter(DailyStockData.stock_id.in_(stock_ids)).delete()
        
        # 批量删除股票
        db.query(Stock).filter(Stock.id.in_(stock_ids)).delete()
        db.commit()
        
        return {"message": f"成功删除 {len(stocks)} 只股票"}
    except Exception as e:
        db.rollback()
        print(f"批量删除股票失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量删除股票失败: {str(e)}")


@router.delete("/{stock_id}")
def delete_stock(
    stock_id: int,
    db: Session = Depends(get_db)
):
    """删除单个股票"""
    try:
        # 查找股票
        stock = db.query(Stock).filter(Stock.id == stock_id).first()
        if not stock:
            raise HTTPException(status_code=404, detail="股票不存在")
        
        # 删除关联的概念关系
        db.query(StockConcept).filter(StockConcept.stock_id == stock_id).delete()
        
        # 删除关联的日线数据
        db.query(DailyStockData).filter(DailyStockData.stock_id == stock_id).delete()
        
        # 删除股票本身
        db.delete(stock)
        db.commit()
        
        return {"message": f"股票 {stock.stock_name}({stock.stock_code}) 已删除"}
    except Exception as e:
        db.rollback()
        print(f"删除股票失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除股票失败: {str(e)}")