from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.daily_trading import (
    DailyTrading, ConceptDailySummary, 
    StockConceptRanking, ConceptHighRecord
)
from app.models.stock import Stock
from app.models.concept import Concept, StockConcept
from app.core.admin_auth import get_current_admin_user
from app.models.admin_user import AdminUser
from datetime import date, datetime, timedelta
import logging
from sqlalchemy import desc, func, and_

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/concepts/daily-summary")
async def get_concepts_daily_summary(
    trading_date: Optional[str] = Query(None, description="交易日期 YYYY-MM-DD"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(50, ge=1, le=200, description="每页数量"),
    sort_by: str = Query("total_volume", description="排序字段: total_volume|stock_count|avg_volume"),
    sort_order: str = Query("desc", description="排序方式: desc|asc"),
    search: Optional[str] = Query(None, description="概念名称搜索"),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """获取指定日期所有概念的每日汇总 - 增强版"""
    try:
        # 解析交易日期
        if trading_date:
            parsed_date = datetime.strptime(trading_date, '%Y-%m-%d').date()
        else:
            # 获取最新的交易日期
            latest_date = db.query(ConceptDailySummary.trading_date).order_by(
                ConceptDailySummary.trading_date.desc()
            ).first()
            parsed_date = latest_date[0] if latest_date else date.today()
        
        # 构建查询
        query = db.query(ConceptDailySummary).filter(
            ConceptDailySummary.trading_date == parsed_date
        )
        
        # 添加搜索条件
        if search:
            query = query.filter(ConceptDailySummary.concept_name.like(f"%{search}%"))
        
        # 添加排序
        sort_column = {
            "total_volume": ConceptDailySummary.total_volume,
            "stock_count": ConceptDailySummary.stock_count,
            "avg_volume": ConceptDailySummary.average_volume
        }.get(sort_by, ConceptDailySummary.total_volume)
        
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)
        
        # 获取总数
        total_count = query.count()
        
        # 分页
        offset = (page - 1) * size
        summaries = query.offset(offset).limit(size).all()
        
        if not summaries:
            return {
                "trading_date": parsed_date.strftime('%Y-%m-%d'),
                "summaries": [],
                "pagination": {
                    "page": page,
                    "size": size,
                    "total": 0,
                    "pages": 0
                },
                "statistics": {
                    "total_concepts": 0,
                    "total_volume": 0,
                    "total_stocks": 0
                }
            }
        
        # 格式化数据
        summary_data = []
        total_volume_all = 0
        total_stocks_all = 0
        
        for summary in summaries:
            total_volume_all += summary.total_volume
            total_stocks_all += summary.stock_count
            
            summary_data.append({
                "concept_name": summary.concept_name,
                "total_volume": summary.total_volume,
                "stock_count": summary.stock_count,
                "avg_volume": round(summary.average_volume, 2),
                "max_volume": summary.max_volume,
                "trading_date": summary.trading_date.strftime('%Y-%m-%d'),
                "volume_percentage": 0  # 将在下面计算
            })
        
        # 计算百分比（基于当前页面的数据）
        if total_volume_all > 0:
            for item in summary_data:
                item["volume_percentage"] = round((item["total_volume"] / total_volume_all) * 100, 2)
        
        return {
            "trading_date": parsed_date.strftime('%Y-%m-%d'),
            "summaries": summary_data,
            "pagination": {
                "page": page,
                "size": size,
                "total": total_count,
                "pages": (total_count + size - 1) // size
            },
            "statistics": {
                "total_concepts": total_count,
                "current_page_volume": total_volume_all,
                "current_page_stocks": total_stocks_all,
                "avg_volume_per_concept": round(total_volume_all / len(summary_data), 2) if summary_data else 0
            },
            "filters": {
                "search": search,
                "sort_by": sort_by,
                "sort_order": sort_order
            }
        }
        
    except Exception as e:
        logger.error(f"获取概念每日汇总失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取概念每日汇总失败: {str(e)}")

@router.get("/concepts/{concept_name}/rankings")
async def get_concept_stock_rankings(
    concept_name: str,
    trading_date: Optional[str] = Query(None, description="交易日期 YYYY-MM-DD"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """获取指定概念在指定日期的所有股票排名 - 增强版"""
    try:
        # 解析交易日期
        if trading_date:
            parsed_date = datetime.strptime(trading_date, '%Y-%m-%d').date()
        else:
            # 获取最新的交易日期
            latest_date = db.query(StockConceptRanking.trading_date).order_by(
                StockConceptRanking.trading_date.desc()
            ).first()
            parsed_date = latest_date[0] if latest_date else date.today()
        
        # 获取概念汇总信息
        concept_summary = db.query(ConceptDailySummary).filter(
            ConceptDailySummary.concept_name == concept_name,
            ConceptDailySummary.trading_date == parsed_date
        ).first()
        
        if not concept_summary:
            return {
                "concept_name": concept_name,
                "trading_date": parsed_date.strftime('%Y-%m-%d'),
                "rankings": [],
                "concept_info": None,
                "pagination": {
                    "page": page,
                    "size": size,
                    "total": 0,
                    "pages": 0
                }
            }
        
        # 查询股票排名数据
        query = db.query(StockConceptRanking, Stock.stock_name).outerjoin(
            Stock, StockConceptRanking.stock_code == Stock.stock_code
        ).filter(
            StockConceptRanking.concept_name == concept_name,
            StockConceptRanking.trading_date == parsed_date
        ).order_by(StockConceptRanking.concept_rank.asc())
        
        # 获取总数
        total_count = query.count()
        
        # 分页
        offset = (page - 1) * size
        rankings = query.offset(offset).limit(size).all()
        
        # 构建返回数据
        ranking_data = []
        for ranking, stock_name in rankings:
            ranking_data.append({
                "stock_code": ranking.stock_code,
                "stock_name": stock_name or f"股票{ranking.stock_code}",
                "concept_name": ranking.concept_name,
                "trading_volume": ranking.trading_volume,
                "concept_rank": ranking.concept_rank,
                "volume_percentage": round(ranking.volume_percentage, 2),
                "trading_date": ranking.trading_date.strftime('%Y-%m-%d'),
                "concept_total_volume": ranking.concept_total_volume
            })
        
        return {
            "concept_name": concept_name,
            "trading_date": parsed_date.strftime('%Y-%m-%d'),
            "concept_info": {
                "total_volume": concept_summary.total_volume,
                "stock_count": concept_summary.stock_count,
                "avg_volume": round(concept_summary.average_volume, 2),
                "max_volume": concept_summary.max_volume
            },
            "rankings": ranking_data,
            "pagination": {
                "page": page,
                "size": size,
                "total": total_count,
                "pages": (total_count + size - 1) // size
            }
        }
        
    except Exception as e:
        logger.error(f"获取概念股票排名失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取概念股票排名失败: {str(e)}")

@router.get("/stock/{stock_code}/concepts")
async def get_stock_concepts(
    stock_code: str,
    trading_date: Optional[str] = Query(None, description="交易日期 YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """获取股票的所有概念及其排名信息"""
    try:
        # 解析交易日期
        if trading_date:
            parsed_date = datetime.strptime(trading_date, '%Y-%m-%d').date()
        else:
            # 获取最新的交易日期
            latest_date = db.query(DailyTrading.trading_date).order_by(
                DailyTrading.trading_date.desc()
            ).first()
            parsed_date = latest_date[0] if latest_date else date.today()
        
        # 标准化股票代码（去除前缀）
        normalized_stock_code = stock_code
        if stock_code.startswith(('SH', 'SZ', 'BJ')):
            normalized_stock_code = stock_code[2:]
        
        # 获取股票基本信息
        stock = db.query(Stock).filter(Stock.stock_code == normalized_stock_code).first()
        if not stock:
            raise HTTPException(status_code=404, detail="股票不存在")
        
        # 获取股票的交易量数据
        trading_data = db.query(DailyTrading).filter(
            DailyTrading.stock_code == normalized_stock_code,
            DailyTrading.trading_date == parsed_date
        ).first()
        
        if not trading_data:
            raise HTTPException(status_code=404, detail="该日期没有交易数据")
        
        # 获取股票在各概念中的排名信息，按交易量从高到低排序
        concepts = []
        try:
            concept_rankings = db.query(StockConceptRanking).filter(
                StockConceptRanking.stock_code == normalized_stock_code,
                StockConceptRanking.trading_date == parsed_date
            ).order_by(StockConceptRanking.trading_volume.desc()).all()
            
            # 构造返回数据
            for ranking in concept_rankings:
                concepts.append({
                    "concept_name": ranking.concept_name,
                    "trading_volume": ranking.trading_volume,
                    "concept_rank": ranking.concept_rank,
                    "concept_total_volume": ranking.concept_total_volume,
                    "volume_percentage": ranking.volume_percentage,
                    "trading_date": parsed_date.strftime('%Y-%m-%d')
                })
        except Exception as e:
            # 如果概念排名表不存在，返回空的概念列表但不报错
            logger.warning(f"概念排名表查询失败，可能表不存在: {str(e)}")
            concepts = []
        
        return {
            "stock_code": stock.stock_code,
            "stock_name": stock.stock_name,
            "trading_date": parsed_date.strftime('%Y-%m-%d'),
            "total_trading_volume": trading_data.trading_volume,
            "concepts": concepts
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式错误，请使用YYYY-MM-DD格式")
    except Exception as e:
        logger.error(f"获取股票概念信息时出错: {e}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")

@router.get("/concept/{concept_name}/stocks")
async def get_concept_stocks(
    concept_name: str,
    trading_date: Optional[str] = Query(None, description="交易日期 YYYY-MM-DD"),
    limit: int = Query(100, description="返回股票数量限制"),
    offset: int = Query(0, description="偏移量"),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """获取概念的所有股票排名"""
    try:
        # 解析交易日期
        if trading_date:
            parsed_date = datetime.strptime(trading_date, '%Y-%m-%d').date()
        else:
            # 获取最新的交易日期
            latest_date = db.query(DailyTrading.trading_date).order_by(
                DailyTrading.trading_date.desc()
            ).first()
            parsed_date = latest_date[0] if latest_date else date.today()
        
        # 获取概念信息
        concept = db.query(Concept).filter(
            Concept.concept_name == concept_name
        ).first()
        
        if not concept:
            raise HTTPException(status_code=404, detail="概念不存在")
        
        # 获取概念汇总信息
        concept_summary = db.query(ConceptDailySummary).filter(
            ConceptDailySummary.concept_name == concept_name,
            ConceptDailySummary.trading_date == parsed_date
        ).first()
        
        # 获取概念股票排名
        query = db.query(
            StockConceptRanking,
            Stock.stock_name
        ).join(
            Stock, StockConceptRanking.stock_code == Stock.stock_code
        ).filter(
            StockConceptRanking.concept_name == concept_name,
            StockConceptRanking.trading_date == parsed_date
        ).order_by(StockConceptRanking.concept_rank.asc())
        
        # 分页
        total_count = query.count()
        rankings = query.offset(offset).limit(limit).all()
        
        # 构造返回数据
        stocks = []
        for ranking, stock_name in rankings:
            stocks.append({
                "stock_code": ranking.stock_code,
                "stock_name": stock_name,
                "trading_volume": ranking.trading_volume,
                "concept_rank": ranking.concept_rank,
                "volume_percentage": ranking.volume_percentage
            })
        
        return {
            "concept_name": concept_name,
            "trading_date": parsed_date.strftime('%Y-%m-%d'),
            "total_volume": concept_summary.total_volume if concept_summary else 0,
            "stock_count": concept_summary.stock_count if concept_summary else 0,
            "average_volume": concept_summary.average_volume if concept_summary else 0,
            "max_volume": concept_summary.max_volume if concept_summary else 0,
            "total_stocks": total_count,
            "stocks": stocks,
            "pagination": {
                "offset": offset,
                "limit": limit,
                "total": total_count,
                "has_more": offset + limit < total_count
            }
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式错误，请使用YYYY-MM-DD格式")
    except Exception as e:
        logger.error(f"获取概念股票信息时出错: {e}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")

@router.get("/concepts/top/{top_n}")
async def get_top_concepts(
    top_n: int,
    trading_date: Optional[str] = Query(None, description="交易日期 YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """获取前N名的所有概念股（第六条功能）"""
    try:
        # 解析交易日期
        if trading_date:
            parsed_date = datetime.strptime(trading_date, '%Y-%m-%d').date()
        else:
            # 获取最新的交易日期
            latest_date = db.query(DailyTrading.trading_date).order_by(
                DailyTrading.trading_date.desc()
            ).first()
            parsed_date = latest_date[0] if latest_date else date.today()
        
        # 获取所有概念的前N名股票
        result = []
        
        # 获取所有概念
        concepts = db.query(Concept).all()
        
        for concept in concepts:
            # 获取概念的前N名股票
            top_stocks = db.query(
                StockConceptRanking,
                Stock.stock_name
            ).join(
                Stock, StockConceptRanking.stock_code == Stock.stock_code
            ).filter(
                StockConceptRanking.concept_name == concept.concept_name,
                StockConceptRanking.trading_date == parsed_date,
                StockConceptRanking.concept_rank <= top_n
            ).order_by(StockConceptRanking.concept_rank.asc()).all()
            
            if top_stocks:
                stocks_data = []
                for ranking, stock_name in top_stocks:
                    stocks_data.append({
                        "stock_code": ranking.stock_code,
                        "stock_name": stock_name,
                        "trading_volume": ranking.trading_volume,
                        "concept_rank": ranking.concept_rank,
                        "volume_percentage": ranking.volume_percentage
                    })
                
                result.append({
                    "concept_name": concept.concept_name,
                    "stocks": stocks_data
                })
        
        return {
            "trading_date": parsed_date.strftime('%Y-%m-%d'),
            "top_n": top_n,
            "concepts": result,
            "total_concepts": len(result)
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式错误，请使用YYYY-MM-DD格式")
    except Exception as e:
        logger.error(f"获取概念前N名股票时出错: {e}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")

@router.get("/concepts/new-highs")
async def get_concept_new_highs(
    days: int = Query(10, description="统计天数"),
    trading_date: Optional[str] = Query(None, description="交易日期 YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """获取创新高的概念（第七条功能）"""
    try:
        # 解析交易日期
        if trading_date:
            parsed_date = datetime.strptime(trading_date, '%Y-%m-%d').date()
        else:
            # 获取最新的交易日期
            latest_date = db.query(DailyTrading.trading_date).order_by(
                DailyTrading.trading_date.desc()
            ).first()
            parsed_date = latest_date[0] if latest_date else date.today()
        
        # 获取创新高的概念记录
        new_high_records = db.query(ConceptHighRecord).filter(
            ConceptHighRecord.trading_date == parsed_date,
            ConceptHighRecord.days_period == days,
            ConceptHighRecord.is_active == True
        ).order_by(ConceptHighRecord.total_volume.desc()).all()
        
        result = []
        for record in new_high_records:
            # 获取该概念的股票排名
            concept_stocks = db.query(
                StockConceptRanking,
                Stock.stock_name
            ).join(
                Stock, StockConceptRanking.stock_code == Stock.stock_code
            ).filter(
                StockConceptRanking.concept_name == record.concept_name,
                StockConceptRanking.trading_date == parsed_date
            ).order_by(StockConceptRanking.concept_rank.asc()).all()
            
            stocks_data = []
            for ranking, stock_name in concept_stocks:
                stocks_data.append({
                    "stock_code": ranking.stock_code,
                    "stock_name": stock_name,
                    "trading_volume": ranking.trading_volume,
                    "concept_rank": ranking.concept_rank,
                    "volume_percentage": ranking.volume_percentage
                })
            
            result.append({
                "concept_name": record.concept_name,
                "total_volume": record.total_volume,
                "days_period": record.days_period,
                "trading_date": record.trading_date.strftime('%Y-%m-%d'),
                "stocks": stocks_data
            })
        
        return {
            "trading_date": parsed_date.strftime('%Y-%m-%d'),
            "days_period": days,
            "new_high_concepts": result,
            "total_concepts": len(result)
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式错误，请使用YYYY-MM-DD格式")
    except Exception as e:
        logger.error(f"获取创新高概念时出错: {e}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")

@router.get("/stock/{stock_code}/chart-data")
async def get_stock_chart_data(
    stock_code: str,
    concept_name: Optional[str] = Query(None, description="概念名称"),
    days: int = Query(30, description="查询天数"),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """获取股票图表数据，支持个股排名趋势和概念总和数据"""
    try:
        # 标准化股票代码（去除前缀）
        normalized_stock_code = stock_code
        if stock_code.startswith(('SH', 'SZ', 'BJ')):
            normalized_stock_code = stock_code[2:]
        
        # 计算日期范围
        end_date_query = db.query(DailyTrading.trading_date).order_by(
            DailyTrading.trading_date.desc()
        ).first()
        if not end_date_query:
            raise HTTPException(status_code=404, detail="没有交易数据")
        
        end_date = end_date_query[0]
        start_date = end_date - timedelta(days=days)
        
        # 获取股票基本信息
        stock = db.query(Stock).filter(Stock.stock_code == normalized_stock_code).first()
        if not stock:
            raise HTTPException(status_code=404, detail="股票不存在")
        
        # 获取股票交易数据
        trading_data = db.query(DailyTrading).filter(
            DailyTrading.stock_code == normalized_stock_code,
            DailyTrading.trading_date >= start_date,
            DailyTrading.trading_date <= end_date
        ).order_by(DailyTrading.trading_date.asc()).all()
        
        chart_data = []
        concept_data = []
        ranking_data = []
        concept_summary_data = []
        
        # 如果指定了概念，获取概念相关数据
        if concept_name:
            try:
                # 获取股票在指定概念中的排名数据
                ranking_data = db.query(StockConceptRanking).filter(
                    StockConceptRanking.stock_code == normalized_stock_code,
                    StockConceptRanking.concept_name == concept_name,
                    StockConceptRanking.trading_date >= start_date,
                    StockConceptRanking.trading_date <= end_date
                ).order_by(StockConceptRanking.trading_date.asc()).all()
                
                # 获取概念每日总和数据
                concept_summary_data = db.query(ConceptDailySummary).filter(
                    ConceptDailySummary.concept_name == concept_name,
                    ConceptDailySummary.trading_date >= start_date,
                    ConceptDailySummary.trading_date <= end_date
                ).order_by(ConceptDailySummary.trading_date.asc()).all()
                
            except Exception as e:
                # 如果概念排名表不存在，记录警告但不影响基础数据返回
                logger.warning(f"概念排名数据查询失败，可能表不存在: {str(e)}")
                ranking_data = []
                concept_summary_data = []
        
        # 合并所有数据
        for trading in trading_data:
            date_str = trading.trading_date.strftime('%Y-%m-%d')
            ranking = next((r for r in ranking_data if r.trading_date == trading.trading_date), None)
            concept_summary = next((c for c in concept_summary_data if c.trading_date == trading.trading_date), None)
            
            # 基础股票数据
            stock_data_point = {
                "date": date_str,
                "trading_volume": trading.trading_volume
            }
            
            # 如果有概念排名数据，添加排名信息
            if ranking:
                stock_data_point.update({
                    "concept_rank": ranking.concept_rank,
                    "volume_percentage": ranking.volume_percentage,
                    "concept_total_volume": ranking.concept_total_volume
                })
            
            chart_data.append(stock_data_point)
            
            # 概念总和数据（概念中所有股票的总和）
            if concept_summary:
                concept_data.append({
                    "date": date_str,
                    "total_volume": concept_summary.total_volume,
                    "stock_count": concept_summary.stock_count,
                    "average_volume": concept_summary.average_volume,
                    "max_volume": concept_summary.max_volume
                })
        
        return {
            "stock_code": stock.stock_code,
            "stock_name": stock.stock_name,
            "concept_name": concept_name,
            "chart_data": chart_data,
            "concept_summary_data": concept_data,
            "period": {
                "start_date": start_date.strftime('%Y-%m-%d'),
                "end_date": end_date.strftime('%Y-%m-%d'),
                "days": days
            },
            "data_availability": {
                "has_ranking_data": len(ranking_data) > 0,
                "has_concept_summary": len(concept_summary_data) > 0,
                "stock_data_points": len(chart_data)
            }
        }
        
    except Exception as e:
        logger.error(f"获取股票图表数据时出错: {e}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")

@router.get("/convertible-bonds/concepts")
async def get_convertible_bond_concepts(
    trading_date: Optional[str] = Query(None, description="交易日期 YYYY-MM-DD"),
    limit: int = Query(50, description="返回数量限制"),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """获取转债概念排行（第九条功能）"""
    try:
        # 解析交易日期
        if trading_date:
            parsed_date = datetime.strptime(trading_date, '%Y-%m-%d').date()
        else:
            # 获取最新的交易日期
            latest_date = db.query(DailyTrading.trading_date).order_by(
                DailyTrading.trading_date.desc()
            ).first()
            parsed_date = latest_date[0] if latest_date else date.today()
        
        # 获取转债股票（股票代码以1开头的）
        convertible_bonds = db.query(Stock).filter(
            Stock.stock_code.like('1%')
        ).all()
        
        convertible_codes = [bond.stock_code for bond in convertible_bonds]
        
        if not convertible_codes:
            return {
                "trading_date": parsed_date.strftime('%Y-%m-%d'),
                "concepts": [],
                "total_concepts": 0
            }
        
        # 获取转债在各概念中的排名
        convertible_rankings = db.query(StockConceptRanking).filter(
            StockConceptRanking.stock_code.in_(convertible_codes),
            StockConceptRanking.trading_date == parsed_date
        ).all()
        
        # 按概念分组
        concept_groups = {}
        for ranking in convertible_rankings:
            if ranking.concept_name not in concept_groups:
                concept_groups[ranking.concept_name] = []
            concept_groups[ranking.concept_name].append(ranking)
        
        # 构造返回数据
        result = []
        for concept_name, rankings in concept_groups.items():
            # 按排名排序
            rankings.sort(key=lambda x: x.concept_rank)
            
            concept_total_volume = rankings[0].concept_total_volume if rankings else 0
            convertible_volume = sum(r.trading_volume for r in rankings)
            
            bonds_data = []
            for ranking in rankings[:limit]:  # 限制返回数量
                bond = next((b for b in convertible_bonds if b.stock_code == ranking.stock_code), None)
                bonds_data.append({
                    "stock_code": ranking.stock_code,
                    "stock_name": bond.stock_name if bond else ranking.stock_code,
                    "trading_volume": ranking.trading_volume,
                    "concept_rank": ranking.concept_rank,
                    "volume_percentage": ranking.volume_percentage
                })
            
            result.append({
                "concept_name": concept_name,
                "convertible_bond_count": len(rankings),
                "total_convertible_volume": convertible_volume,
                "concept_total_volume": concept_total_volume,
                "convertible_percentage": (convertible_volume / concept_total_volume * 100) if concept_total_volume > 0 else 0,
                "bonds": bonds_data
            })
        
        # 按转债交易量排序
        result.sort(key=lambda x: x['total_convertible_volume'], reverse=True)
        
        return {
            "trading_date": parsed_date.strftime('%Y-%m-%d'),
            "concepts": result,
            "total_concepts": len(result)
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式错误，请使用YYYY-MM-DD格式")
    except Exception as e:
        logger.error(f"获取转债概念排行时出错: {e}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")

@router.get("/recent-dates")
async def get_recent_trading_dates(
    limit: int = Query(10, description="返回日期数量"),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """获取最近的交易日期"""
    try:
        dates = db.query(DailyTrading.trading_date).distinct().order_by(
            DailyTrading.trading_date.desc()
        ).limit(limit).all()
        
        return {
            "trading_dates": [date[0].strftime('%Y-%m-%d') for date in dates]
        }
        
    except Exception as e:
        logger.error(f"获取交易日期时出错: {e}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/concepts/innovation-high")
async def get_innovation_high_concepts(
    days: int = Query(10, ge=1, le=365, description="查询天数范围"),
    trading_date: Optional[str] = Query(None, description="基准交易日期 YYYY-MM-DD，默认为最新日期"),
    limit: int = Query(20, ge=1, le=100, description="返回概念数量限制"),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """获取创新高的概念及其股票排名
    
    查找在指定天数内概念总交易量创新高的概念，并返回这些概念内股票的排名情况
    """
    try:
        # 解析基准日期
        if trading_date:
            base_date = datetime.strptime(trading_date, '%Y-%m-%d').date()
        else:
            # 获取最新的交易日期
            latest_date = db.query(ConceptDailySummary.trading_date).order_by(
                ConceptDailySummary.trading_date.desc()
            ).first()
            base_date = latest_date[0] if latest_date else date.today()
        
        # 计算查询日期范围
        start_date = base_date - timedelta(days=days-1)
        
        logger.info(f"查询创新高概念: {start_date} 到 {base_date}, 天数: {days}")
        
        # 获取每个概念在指定期间内的最大总交易量
        concept_max_query = db.query(
            ConceptDailySummary.concept_name,
            func.max(ConceptDailySummary.total_volume).label('max_volume'),
            func.max(ConceptDailySummary.trading_date).label('max_date')
        ).filter(
            and_(
                ConceptDailySummary.trading_date >= start_date,
                ConceptDailySummary.trading_date <= base_date
            )
        ).group_by(ConceptDailySummary.concept_name).subquery()
        
        # 获取基准日期当天创新高的概念
        innovation_concepts = db.query(
            ConceptDailySummary.concept_name,
            ConceptDailySummary.total_volume,
            ConceptDailySummary.stock_count,
            ConceptDailySummary.avg_volume,
            ConceptDailySummary.trading_date
        ).join(
            concept_max_query,
            and_(
                ConceptDailySummary.concept_name == concept_max_query.c.concept_name,
                ConceptDailySummary.total_volume == concept_max_query.c.max_volume,
                ConceptDailySummary.trading_date == base_date
            )
        ).order_by(
            ConceptDailySummary.total_volume.desc()
        ).limit(limit).all()
        
        if not innovation_concepts:
            return {
                "trading_date": base_date.strftime('%Y-%m-%d'),
                "query_days": days,
                "innovation_concepts": [],
                "total_concepts": 0
            }
        
        # 获取这些创新高概念内的股票排名
        result = []
        for concept in innovation_concepts:
            # 获取该概念在基准日期的股票排名
            stock_rankings = db.query(
                StockConceptRanking.stock_code,
                Stock.stock_name,
                StockConceptRanking.trading_volume,
                StockConceptRanking.concept_rank,
                StockConceptRanking.volume_percentage
            ).join(
                Stock, StockConceptRanking.stock_code == Stock.stock_code
            ).filter(
                and_(
                    StockConceptRanking.concept_name == concept.concept_name,
                    StockConceptRanking.trading_date == base_date
                )
            ).order_by(
                StockConceptRanking.concept_rank.asc()
            ).limit(10).all()  # 每个概念只返回前10名股票
            
            concept_data = {
                "concept_name": concept.concept_name,
                "total_volume": float(concept.total_volume),
                "stock_count": concept.stock_count,
                "avg_volume": float(concept.avg_volume),
                "trading_date": concept.trading_date.strftime('%Y-%m-%d'),
                "stocks": []
            }
            
            for stock in stock_rankings:
                stock_data = {
                    "stock_code": stock.stock_code,
                    "stock_name": stock.stock_name,
                    "trading_volume": float(stock.trading_volume),
                    "concept_rank": stock.concept_rank,
                    "volume_percentage": float(stock.volume_percentage) if stock.volume_percentage else 0.0
                }
                concept_data["stocks"].append(stock_data)
            
            result.append(concept_data)
        
        return {
            "trading_date": base_date.strftime('%Y-%m-%d'),
            "query_days": days,
            "start_date": start_date.strftime('%Y-%m-%d'),
            "innovation_concepts": result,
            "total_concepts": len(result)
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式错误，请使用YYYY-MM-DD格式")
    except Exception as e:
        logger.error(f"获取创新高概念时出错: {e}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")