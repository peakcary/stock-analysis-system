"""
原始数据查询API
提供CSV原始数据（未拆分）的查询、导出功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import date
import csv
from io import StringIO

from app.core.database import get_db
from app.models.stock import StockConceptRawData

router = APIRouter()


@router.get("/daily")
async def get_raw_data_by_date(
    trade_date: date = Query(..., description="交易日期，格式：2025-10-15"),
    stock_code: Optional[str] = Query(None, description="股票代码，如：600036"),
    concept: Optional[str] = Query(None, description="概念名称，支持模糊查询"),
    industry: Optional[str] = Query(None, description="行业，支持模糊查询"),
    sort_by: str = Query("net_inflow", description="排序字段：net_inflow|price|turnover_rate|total_reads"),
    sort_order: str = Query("desc", description="排序方向：asc|desc"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(50, ge=1, le=1000, description="每页数量"),
    db: Session = Depends(get_db)
):
    """
    查询指定日期的CSV原始数据

    - **trade_date**: 交易日期
    - **stock_code**: 可选，筛选指定股票
    - **concept**: 可选，筛选指定概念（支持模糊查询）
    - **industry**: 可选，筛选指定行业（支持模糊查询）
    - **sort_by**: 排序字段
    - **sort_order**: 排序方向
    - **page**: 页码
    - **size**: 每页数量
    """

    # 构建查询
    query = db.query(StockConceptRawData).filter(
        StockConceptRawData.trade_date == trade_date
    )

    # 添加筛选条件
    if stock_code:
        query = query.filter(StockConceptRawData.stock_code == stock_code)

    if concept:
        query = query.filter(StockConceptRawData.concept.like(f'%{concept}%'))

    if industry:
        query = query.filter(StockConceptRawData.industry.like(f'%{industry}%'))

    # 总数统计
    total = query.count()

    # 排序
    sort_column = getattr(StockConceptRawData, sort_by, StockConceptRawData.net_inflow)
    if sort_order.lower() == 'desc':
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # 分页
    offset = (page - 1) * size
    records = query.offset(offset).limit(size).all()

    return {
        "success": True,
        "trade_date": trade_date.isoformat(),
        "total": total,
        "page": page,
        "size": size,
        "total_pages": (total + size - 1) // size,
        "data": [
            {
                "stock_code": r.stock_code,
                "stock_name": r.stock_name,
                "concept": r.concept,
                "industry": r.industry,
                "price": float(r.price) if r.price else 0,
                "turnover_rate": float(r.turnover_rate) if r.turnover_rate else 0,
                "net_inflow": float(r.net_inflow) if r.net_inflow else 0,
                "pages_count": r.pages_count,
                "total_reads": r.total_reads,
                "file_name": r.file_name,
                "row_number": r.row_number
            }
            for r in records
        ]
    }


@router.get("/export/csv")
async def export_raw_data_csv(
    trade_date: date = Query(..., description="交易日期"),
    stock_code: Optional[str] = Query(None, description="股票代码"),
    concept: Optional[str] = Query(None, description="概念名称"),
    db: Session = Depends(get_db)
):
    """
    导出原始数据为CSV文件

    返回与导入时格式一致的CSV文件
    """

    # 查询数据
    query = db.query(StockConceptRawData).filter(
        StockConceptRawData.trade_date == trade_date
    )

    if stock_code:
        query = query.filter(StockConceptRawData.stock_code == stock_code)

    if concept:
        query = query.filter(StockConceptRawData.concept.like(f'%{concept}%'))

    records = query.order_by(StockConceptRawData.net_inflow.desc()).all()

    if not records:
        raise HTTPException(status_code=404, detail=f"未找到 {trade_date} 的数据")

    # 生成CSV
    output = StringIO()
    writer = csv.writer(output)

    # 写入表头（中文格式）
    writer.writerow([
        '股票代码', '股票名称', '全部页数', '热帖首页页阅读总数',
        '价格', '行业', '概念', '换手', '净流入'
    ])

    # 写入数据
    for r in records:
        writer.writerow([
            r.stock_code,
            r.stock_name,
            r.pages_count,
            r.total_reads,
            float(r.price) if r.price else 0,
            r.industry or '',
            r.concept,
            float(r.turnover_rate) if r.turnover_rate else 0,
            float(r.net_inflow) if r.net_inflow else 0
        ])

    # 返回CSV文件
    output.seek(0)
    filename = f"stock_data_{trade_date.strftime('%Y%m%d')}.csv"

    return StreamingResponse(
        iter([output.getvalue().encode('utf-8-sig')]),  # 使用utf-8-sig支持Excel打开
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/stats/daily")
async def get_daily_stats(
    trade_date: date = Query(..., description="交易日期"),
    db: Session = Depends(get_db)
):
    """
    获取指定日期的数据统计

    返回：
    - 总记录数
    - 股票数量
    - 概念数量
    - 行业数量
    - 净流入总额
    """

    stats = db.query(
        func.count(StockConceptRawData.id).label('total_records'),
        func.count(func.distinct(StockConceptRawData.stock_code)).label('stock_count'),
        func.count(func.distinct(StockConceptRawData.concept)).label('concept_count'),
        func.count(func.distinct(StockConceptRawData.industry)).label('industry_count'),
        func.sum(StockConceptRawData.net_inflow).label('total_net_inflow'),
        func.avg(StockConceptRawData.net_inflow).label('avg_net_inflow'),
        func.max(StockConceptRawData.net_inflow).label('max_net_inflow'),
        func.min(StockConceptRawData.net_inflow).label('min_net_inflow')
    ).filter(
        StockConceptRawData.trade_date == trade_date
    ).first()

    if not stats or stats.total_records == 0:
        raise HTTPException(status_code=404, detail=f"未找到 {trade_date} 的数据")

    return {
        "success": True,
        "trade_date": trade_date.isoformat(),
        "total_records": stats.total_records or 0,
        "stock_count": stats.stock_count or 0,
        "concept_count": stats.concept_count or 0,
        "industry_count": stats.industry_count or 0,
        "total_net_inflow": float(stats.total_net_inflow) if stats.total_net_inflow else 0,
        "avg_net_inflow": float(stats.avg_net_inflow) if stats.avg_net_inflow else 0,
        "max_net_inflow": float(stats.max_net_inflow) if stats.max_net_inflow else 0,
        "min_net_inflow": float(stats.min_net_inflow) if stats.min_net_inflow else 0
    }


@router.get("/concepts")
async def get_concepts_by_date(
    trade_date: date = Query(..., description="交易日期"),
    db: Session = Depends(get_db)
):
    """
    获取指定日期的所有概念及统计
    """

    concepts = db.query(
        StockConceptRawData.concept,
        func.count(StockConceptRawData.id).label('stock_count'),
        func.sum(StockConceptRawData.net_inflow).label('total_net_inflow'),
        func.avg(StockConceptRawData.net_inflow).label('avg_net_inflow')
    ).filter(
        StockConceptRawData.trade_date == trade_date
    ).group_by(
        StockConceptRawData.concept
    ).order_by(
        func.sum(StockConceptRawData.net_inflow).desc()
    ).all()

    return {
        "success": True,
        "trade_date": trade_date.isoformat(),
        "total_concepts": len(concepts),
        "data": [
            {
                "concept": c.concept,
                "stock_count": c.stock_count,
                "total_net_inflow": float(c.total_net_inflow) if c.total_net_inflow else 0,
                "avg_net_inflow": float(c.avg_net_inflow) if c.avg_net_inflow else 0
            }
            for c in concepts
        ]
    }


@router.get("/stock/{stock_code}")
async def get_stock_raw_data(
    stock_code: str,
    trade_date: date = Query(..., description="交易日期"),
    db: Session = Depends(get_db)
):
    """
    获取指定股票在指定日期的所有概念数据

    一个股票可能属于多个概念，返回该股票在所有概念下的数据
    """

    records = db.query(StockConceptRawData).filter(
        StockConceptRawData.stock_code == stock_code,
        StockConceptRawData.trade_date == trade_date
    ).all()

    if not records:
        raise HTTPException(
            status_code=404,
            detail=f"未找到股票 {stock_code} 在 {trade_date} 的数据"
        )

    return {
        "success": True,
        "stock_code": stock_code,
        "stock_name": records[0].stock_name,
        "trade_date": trade_date.isoformat(),
        "concept_count": len(records),
        "data": [
            {
                "concept": r.concept,
                "industry": r.industry,
                "price": float(r.price) if r.price else 0,
                "turnover_rate": float(r.turnover_rate) if r.turnover_rate else 0,
                "net_inflow": float(r.net_inflow) if r.net_inflow else 0,
                "pages_count": r.pages_count,
                "total_reads": r.total_reads
            }
            for r in records
        ]
    }


@router.get("/dates")
async def get_available_dates(
    limit: int = Query(30, ge=1, le=365, description="返回最近N天"),
    db: Session = Depends(get_db)
):
    """
    获取有数据的日期列表
    """

    dates = db.query(
        StockConceptRawData.trade_date,
        func.count(StockConceptRawData.id).label('record_count')
    ).group_by(
        StockConceptRawData.trade_date
    ).order_by(
        StockConceptRawData.trade_date.desc()
    ).limit(limit).all()

    return {
        "success": True,
        "total_dates": len(dates),
        "data": [
            {
                "date": d.trade_date.isoformat(),
                "record_count": d.record_count
            }
            for d in dates
        ]
    }
