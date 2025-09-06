"""
图表数据API接口
"""

from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.chart_data import ChartDataService
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/concept/{concept_id}/heat-trend")
async def get_concept_heat_trend(
    concept_id: int,
    days: int = Query(30, ge=7, le=365, description="查询天数"),
    db: Session = Depends(get_db)
):
    """获取概念热度趋势图表数据"""
    
    try:
        chart_service = ChartDataService(db)
        result = chart_service.get_concept_heat_trend_chart(concept_id, days)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"概念 {concept_id} 未找到")
        
        return result
        
    except Exception as e:
        logger.error(f"获取概念热度趋势失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取趋势数据失败: {str(e)}")


@router.get("/daily-hot-concepts")
async def get_daily_hot_concepts_chart(
    trade_date: Optional[date] = Query(None, description="交易日期，默认为最新日期"),
    top_n: int = Query(20, ge=5, le=100, description="显示前N个概念"),
    db: Session = Depends(get_db)
):
    """获取每日热门概念柱状图数据"""
    
    try:
        chart_service = ChartDataService(db)
        result = chart_service.get_daily_hot_concepts_chart(trade_date, top_n)
        
        return result
        
    except Exception as e:
        logger.error(f"获取热门概念图表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取图表数据失败: {str(e)}")


@router.get("/concept/{concept_id}/stock-distribution")
async def get_stock_heat_distribution(
    concept_id: int,
    trade_date: Optional[date] = Query(None, description="交易日期，默认为最新日期"),
    db: Session = Depends(get_db)
):
    """获取概念内股票热度分布图表数据"""
    
    try:
        chart_service = ChartDataService(db)
        result = chart_service.get_stock_heat_distribution_chart(concept_id, trade_date)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"概念 {concept_id} 未找到")
        
        return result
        
    except Exception as e:
        logger.error(f"获取股票分布图表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取分布数据失败: {str(e)}")


@router.get("/innovation-timeline")
async def get_innovation_timeline_chart(
    days: int = Query(30, ge=7, le=365, description="查询天数"),
    db: Session = Depends(get_db)
):
    """获取创新高概念时间线图表数据"""
    
    try:
        chart_service = ChartDataService(db)
        result = chart_service.get_innovation_concepts_timeline_chart(days)
        
        return result
        
    except Exception as e:
        logger.error(f"获取创新高时间线失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取时间线数据失败: {str(e)}")


@router.get("/convertible-bonds-analysis")
async def get_convertible_bonds_chart(
    trade_date: Optional[date] = Query(None, description="交易日期，默认为最新日期"),
    db: Session = Depends(get_db)
):
    """获取可转债分析图表数据"""
    
    try:
        chart_service = ChartDataService(db)
        result = chart_service.get_convertible_bonds_analysis_chart(trade_date)
        
        return result
        
    except Exception as e:
        logger.error(f"获取可转债分析图表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取可转债数据失败: {str(e)}")


@router.get("/concept-comparison")
async def get_multi_concept_comparison(
    concept_ids: str = Query(..., description="概念ID列表，用逗号分隔，如: 1,2,3"),
    days: int = Query(30, ge=7, le=365, description="查询天数"),
    db: Session = Depends(get_db)
):
    """获取多概念对比图表数据"""
    
    try:
        # 解析概念ID列表
        ids = []
        for id_str in concept_ids.split(','):
            try:
                ids.append(int(id_str.strip()))
            except ValueError:
                raise HTTPException(status_code=400, detail=f"无效的概念ID: {id_str}")
        
        if len(ids) < 2:
            raise HTTPException(status_code=400, detail="至少需要2个概念进行对比")
        
        if len(ids) > 10:
            raise HTTPException(status_code=400, detail="最多支持对比10个概念")
        
        chart_service = ChartDataService(db)
        result = chart_service.get_multi_concept_comparison_chart(ids, days)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取概念对比图表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取对比数据失败: {str(e)}")


@router.get("/stock/{stock_id}/concept-performance")
async def get_stock_concept_performance_chart(
    stock_id: int,
    trade_date: Optional[date] = Query(None, description="交易日期，默认为最新日期"),
    db: Session = Depends(get_db)
):
    """获取股票在各概念中的表现图表数据"""
    
    try:
        from app.services.concept_analysis import ConceptAnalysisService
        
        analysis_service = ConceptAnalysisService(db)
        concept_rankings = analysis_service.get_stock_concepts_ranking(stock_id, trade_date)
        
        if not concept_rankings:
            raise HTTPException(status_code=404, detail=f"股票 {stock_id} 未找到相关概念数据")
        
        # 构建图表数据
        concept_names = [item["concept_name"] for item in concept_rankings]
        ranks = [item["rank"] for item in concept_rankings]
        heat_values = [item["heat_value"] for item in concept_rankings]
        rank_percentages = [item["rank_percentage"] for item in concept_rankings]
        
        chart_data = {
            "stock_id": stock_id,
            "trade_date": trade_date.isoformat() if trade_date else None,
            "chart_data": {
                "categories": concept_names,
                "series": [
                    {
                        "name": "概念排名",
                        "data": ranks,
                        "type": "bar",
                        "yAxisIndex": 0
                    },
                    {
                        "name": "热度值",
                        "data": heat_values,
                        "type": "line",
                        "yAxisIndex": 1
                    },
                    {
                        "name": "排名百分比",
                        "data": rank_percentages,
                        "type": "line",
                        "yAxisIndex": 2
                    }
                ]
            },
            "performance_summary": {
                "total_concepts": len(concept_rankings),
                "avg_rank": round(sum(ranks) / len(ranks), 1),
                "best_rank": min(ranks),
                "worst_rank": max(ranks),
                "avg_heat": round(sum(heat_values) / len(heat_values), 2),
                "top_3_concepts": concept_rankings[:3]
            }
        }
        
        return chart_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取股票概念表现图表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取表现数据失败: {str(e)}")


@router.get("/market-overview")
async def get_market_overview_chart(
    trade_date: Optional[date] = Query(None, description="交易日期，默认为最新日期"),
    db: Session = Depends(get_db)
):
    """获取市场概览图表数据"""
    
    try:
        from app.models import DailyStockData, DailyConceptSummary
        from sqlalchemy import func
        
        if not trade_date:
            latest_data = db.query(DailyStockData.trade_date).order_by(
                db.query(DailyStockData.trade_date).desc()
            ).first()
            if not latest_data:
                raise HTTPException(status_code=404, detail="没有股票数据")
            trade_date = latest_data.trade_date
        
        # 获取市场统计数据
        stock_stats = db.query(
            func.count(DailyStockData.id).label('total_stocks'),
            func.avg(DailyStockData.heat_value).label('avg_heat'),
            func.sum(DailyStockData.heat_value).label('total_heat'),
            func.max(DailyStockData.heat_value).label('max_heat')
        ).filter(
            DailyStockData.trade_date == trade_date,
            DailyStockData.heat_value > 0
        ).first()
        
        concept_stats = db.query(
            func.count(DailyConceptSummary.id).label('total_concepts'),
            func.sum(DailyConceptSummary.is_new_high).label('innovation_concepts'),
            func.avg(DailyConceptSummary.total_heat_value).label('avg_concept_heat')
        ).filter(
            DailyConceptSummary.trade_date == trade_date
        ).first()
        
        # 热度分布统计
        heat_distribution = db.query(
            func.count(DailyStockData.id).label('count'),
            func.case([
                (DailyStockData.heat_value < 10, '0-10'),
                (DailyStockData.heat_value < 20, '10-20'),
                (DailyStockData.heat_value < 50, '20-50'),
                (DailyStockData.heat_value < 100, '50-100'),
                (DailyStockData.heat_value >= 100, '100+')
            ]).label('range')
        ).filter(
            DailyStockData.trade_date == trade_date,
            DailyStockData.heat_value > 0
        ).group_by('range').all()
        
        distribution_data = {item.range: item.count for item in heat_distribution}
        
        return {
            "trade_date": trade_date.isoformat(),
            "market_stats": {
                "total_stocks": stock_stats.total_stocks if stock_stats else 0,
                "avg_heat_value": round(float(stock_stats.avg_heat), 2) if stock_stats and stock_stats.avg_heat else 0,
                "total_heat_value": round(float(stock_stats.total_heat), 2) if stock_stats and stock_stats.total_heat else 0,
                "max_heat_value": float(stock_stats.max_heat) if stock_stats and stock_stats.max_heat else 0,
                "total_concepts": concept_stats.total_concepts if concept_stats else 0,
                "innovation_concepts": concept_stats.innovation_concepts if concept_stats else 0,
                "avg_concept_heat": round(float(concept_stats.avg_concept_heat), 2) if concept_stats and concept_stats.avg_concept_heat else 0
            },
            "heat_distribution_chart": {
                "categories": ["0-10", "10-20", "20-50", "50-100", "100+"],
                "data": [
                    distribution_data.get("0-10", 0),
                    distribution_data.get("10-20", 0),
                    distribution_data.get("20-50", 0),
                    distribution_data.get("50-100", 0),
                    distribution_data.get("100+", 0)
                ]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取市场概览失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取市场数据失败: {str(e)}")