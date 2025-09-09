"""
增强股票分析API - 支持原始代码和标准化代码查询
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, text
from app.core.database import get_db
from app.models.daily_trading import DailyTrading, ConceptDailySummary, StockConceptRanking
from app.models.stock import Stock
from app.models.concept import Concept
from app.core.admin_auth import get_current_admin_user
from app.models.admin_user import AdminUser
from datetime import date, datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/market-distribution")
async def get_market_distribution(
    trading_date: Optional[str] = Query(None, description="交易日期 YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """按市场前缀统计交易量分布"""
    try:
        # 解析交易日期
        if trading_date:
            parsed_date = datetime.strptime(trading_date, '%Y-%m-%d').date()
        else:
            # 获取最新日期
            latest_date = db.query(DailyTrading.trading_date).order_by(
                DailyTrading.trading_date.desc()
            ).first()
            parsed_date = latest_date[0] if latest_date else date.today()
        
        # 按市场前缀分组统计
        market_stats = db.query(
            # 从 original_stock_code 中提取前缀
            func.substring(DailyTrading.original_stock_code, 1, 2).label('market_prefix'),
            func.count(DailyTrading.id).label('stock_count'),
            func.sum(DailyTrading.trading_volume).label('total_volume'),
            func.avg(DailyTrading.trading_volume).label('avg_volume'),
            func.max(DailyTrading.trading_volume).label('max_volume')
        ).filter(
            DailyTrading.trading_date == parsed_date
        ).group_by(
            func.substring(DailyTrading.original_stock_code, 1, 2)
        ).all()
        
        result = []
        market_mapping = {
            'SH': '上海交易所',
            'SZ': '深圳交易所', 
            'BJ': '北京交易所',
            '60': '上海A股',  # 纯数字代码情况
            '00': '深圳A股',
            '30': '深圳创业板',
        }
        
        for stat in market_stats:
            prefix = stat.market_prefix if stat.market_prefix else '其他'
            market_name = market_mapping.get(prefix, f'{prefix}市场')
            
            result.append({
                'market_prefix': prefix,
                'market_name': market_name,
                'stock_count': stat.stock_count,
                'total_volume': int(stat.total_volume) if stat.total_volume else 0,
                'avg_volume': round(float(stat.avg_volume), 2) if stat.avg_volume else 0,
                'max_volume': stat.max_volume if stat.max_volume else 0
            })
        
        # 按总交易量排序
        result.sort(key=lambda x: x['total_volume'], reverse=True)
        
        return {
            'trading_date': parsed_date.strftime('%Y-%m-%d'),
            'market_distribution': result,
            'total_markets': len(result),
            'summary': {
                'total_stocks': sum(r['stock_count'] for r in result),
                'total_volume': sum(r['total_volume'] for r in result),
                'avg_volume_all': round(sum(r['total_volume'] for r in result) / sum(r['stock_count'] for r in result), 2) if sum(r['stock_count'] for r in result) > 0 else 0
            }
        }
        
    except Exception as e:
        logger.error(f"获取市场分布失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取市场分布失败: {str(e)}")

@router.get("/search-by-prefix")
async def search_by_prefix(
    prefix: str = Query(..., description="市场前缀 (SH/SZ/BJ等)"),
    trading_date: Optional[str] = Query(None, description="交易日期 YYYY-MM-DD"),
    limit: int = Query(50, ge=1, le=200, description="返回数量"),
    order_by: str = Query("volume", description="排序方式: volume|code"),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """按市场前缀搜索股票"""
    try:
        # 解析交易日期
        if trading_date:
            parsed_date = datetime.strptime(trading_date, '%Y-%m-%d').date()
        else:
            latest_date = db.query(DailyTrading.trading_date).order_by(
                DailyTrading.trading_date.desc()
            ).first()
            parsed_date = latest_date[0] if latest_date else date.today()
        
        # 构建查询
        query = db.query(
            DailyTrading.original_stock_code,
            DailyTrading.normalized_stock_code,
            DailyTrading.trading_volume,
            Stock.stock_name
        ).outerjoin(
            Stock, DailyTrading.normalized_stock_code == Stock.stock_code
        ).filter(
            DailyTrading.original_stock_code.like(f'{prefix.upper()}%'),
            DailyTrading.trading_date == parsed_date
        )
        
        # 排序
        if order_by == "volume":
            query = query.order_by(desc(DailyTrading.trading_volume))
        else:
            query = query.order_by(DailyTrading.original_stock_code)
        
        results = query.limit(limit).all()
        
        stocks = []
        for original_code, normalized_code, volume, stock_name in results:
            stocks.append({
                'original_stock_code': original_code,      # SH600000
                'normalized_stock_code': normalized_code,  # 600000
                'stock_name': stock_name or f'股票{normalized_code}',
                'trading_volume': volume,
                'market_prefix': prefix.upper()
            })
        
        return {
            'trading_date': parsed_date.strftime('%Y-%m-%d'),
            'market_prefix': prefix.upper(),
            'search_results': stocks,
            'total_found': len(stocks),
            'order_by': order_by
        }
        
    except Exception as e:
        logger.error(f"按前缀搜索失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

@router.get("/code-format-analysis")
async def analyze_code_formats(
    trading_date: Optional[str] = Query(None, description="交易日期 YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """分析股票代码格式分布"""
    try:
        # 解析交易日期
        if trading_date:
            parsed_date = datetime.strptime(trading_date, '%Y-%m-%d').date()
        else:
            latest_date = db.query(DailyTrading.trading_date).order_by(
                DailyTrading.trading_date.desc()
            ).first()
            parsed_date = latest_date[0] if latest_date else date.today()
        
        # 分析原始代码格式
        format_stats = db.execute(text("""
            SELECT 
                CASE 
                    WHEN original_stock_code LIKE 'SH%' THEN 'SH前缀'
                    WHEN original_stock_code LIKE 'SZ%' THEN 'SZ前缀'
                    WHEN original_stock_code LIKE 'BJ%' THEN 'BJ前缀'
                    WHEN original_stock_code REGEXP '^[0-9]{6}$' THEN '纯数字6位'
                    ELSE '其他格式'
                END as code_format,
                COUNT(*) as count,
                SUM(trading_volume) as total_volume,
                AVG(trading_volume) as avg_volume,
                MIN(original_stock_code) as sample_code
            FROM daily_trading 
            WHERE trading_date = :trading_date
            GROUP BY code_format
            ORDER BY count DESC
        """), {'trading_date': parsed_date}).fetchall()
        
        formats = []
        total_count = 0
        total_volume = 0
        
        for row in format_stats:
            count = row.count
            volume = int(row.total_volume) if row.total_volume else 0
            
            formats.append({
                'format_type': row.code_format,
                'stock_count': count,
                'total_volume': volume,
                'avg_volume': round(float(row.avg_volume), 2) if row.avg_volume else 0,
                'sample_code': row.sample_code,
                'percentage': 0  # 后续计算
            })
            
            total_count += count
            total_volume += volume
        
        # 计算百分比
        for format_info in formats:
            format_info['percentage'] = round(
                (format_info['stock_count'] / total_count * 100), 2
            ) if total_count > 0 else 0
        
        return {
            'trading_date': parsed_date.strftime('%Y-%m-%d'),
            'code_formats': formats,
            'summary': {
                'total_stocks': total_count,
                'total_volume': total_volume,
                'avg_volume': round(total_volume / total_count, 2) if total_count > 0 else 0
            }
        }
        
    except Exception as e:
        logger.error(f"代码格式分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")

@router.get("/dual-code-query/{stock_identifier}")
async def query_by_dual_code(
    stock_identifier: str,
    trading_date: Optional[str] = Query(None, description="交易日期 YYYY-MM-DD"),
    include_concepts: bool = Query(True, description="是否包含概念信息"),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    双代码查询 - 支持原始代码或标准化代码查询
    stock_identifier 可以是: SH600000 或 600000
    """
    try:
        # 解析交易日期
        if trading_date:
            parsed_date = datetime.strptime(trading_date, '%Y-%m-%d').date()
        else:
            latest_date = db.query(DailyTrading.trading_date).order_by(
                DailyTrading.trading_date.desc()
            ).first()
            parsed_date = latest_date[0] if latest_date else date.today()
        
        # 尝试按原始代码和标准化代码查询
        trading_record = db.query(DailyTrading).filter(
            (DailyTrading.original_stock_code == stock_identifier.upper()) |
            (DailyTrading.normalized_stock_code == stock_identifier),
            DailyTrading.trading_date == parsed_date
        ).first()
        
        if not trading_record:
            raise HTTPException(
                status_code=404, 
                detail=f"未找到股票代码 {stock_identifier} 在 {parsed_date} 的交易数据"
            )
        
        # 获取股票基础信息
        stock = db.query(Stock).filter(
            Stock.stock_code == trading_record.normalized_stock_code
        ).first()
        
        result = {
            'stock_info': {
                'original_stock_code': trading_record.original_stock_code,
                'normalized_stock_code': trading_record.normalized_stock_code,
                'stock_name': stock.stock_name if stock else f'股票{trading_record.normalized_stock_code}',
                'industry': stock.industry if stock else None,
            },
            'trading_data': {
                'trading_date': parsed_date.strftime('%Y-%m-%d'),
                'trading_volume': trading_record.trading_volume,
            },
            'query_matched_by': 'original_code' if stock_identifier.upper() == trading_record.original_stock_code else 'normalized_code'
        }
        
        # 可选：包含概念信息
        if include_concepts:
            concept_rankings = db.query(StockConceptRanking).filter(
                StockConceptRanking.stock_code == trading_record.normalized_stock_code,
                StockConceptRanking.trading_date == parsed_date
            ).all()
            
            concepts = []
            for ranking in concept_rankings:
                concepts.append({
                    'concept_name': ranking.concept_name,
                    'concept_rank': ranking.concept_rank,
                    'volume_percentage': round(ranking.volume_percentage, 2),
                    'concept_total_volume': ranking.concept_total_volume
                })
            
            result['concepts'] = concepts
            result['concept_count'] = len(concepts)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"双代码查询失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")

@router.get("/migration-status")
async def get_migration_status(
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """检查数据迁移状态"""
    try:
        # 统计总记录数和已迁移记录数
        total_records = db.query(DailyTrading).count()
        
        migrated_records = db.query(DailyTrading).filter(
            DailyTrading.original_stock_code.isnot(None),
            DailyTrading.original_stock_code != '',
            DailyTrading.normalized_stock_code.isnot(None),
            DailyTrading.normalized_stock_code != ''
        ).count()
        
        # 统计各种代码格式
        code_stats = db.execute(text("""
            SELECT 
                'total' as category,
                COUNT(*) as count
            FROM daily_trading
            UNION ALL
            SELECT 
                'with_original' as category,
                COUNT(*) as count
            FROM daily_trading 
            WHERE original_stock_code IS NOT NULL AND original_stock_code != ''
            UNION ALL
            SELECT 
                'with_normalized' as category,
                COUNT(*) as count
            FROM daily_trading 
            WHERE normalized_stock_code IS NOT NULL AND normalized_stock_code != ''
        """)).fetchall()
        
        stats = {row.category: row.count for row in code_stats}
        
        # 计算完成率
        migration_rate = (migrated_records / total_records * 100) if total_records > 0 else 0
        
        return {
            'migration_status': {
                'is_completed': migration_rate == 100.0,
                'completion_rate': round(migration_rate, 2),
                'total_records': total_records,
                'migrated_records': migrated_records,
                'pending_records': total_records - migrated_records
            },
            'statistics': {
                'total_records': stats.get('total', 0),
                'with_original_code': stats.get('with_original', 0),
                'with_normalized_code': stats.get('with_normalized', 0),
            },
            'recommendations': [
                "如果迁移未完成，运行: python backend/database/migrate_stock_codes.py",
                "迁移完成后重启服务以确保新字段生效",
                "测试TXT导入功能验证SH/SZ前缀处理是否正常"
            ] if migration_rate < 100 else [
                "数据迁移已完成 ✅",
                "可以使用新的双代码查询功能",
                "支持按市场前缀分析和统计"
            ]
        }
        
    except Exception as e:
        logger.error(f"检查迁移状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"状态检查失败: {str(e)}")