"""
数据库优化状态检查API
提供优化功能的状态信息和切换控制
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.admin_auth import get_current_admin_user
from app.models.admin_user import AdminUser

import logging
import os

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/optimization/status")
async def get_optimization_status(
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """获取数据库优化功能状态"""
    try:
        # 检查环境变量配置
        env_config = {
            "USE_OPTIMIZED_TABLES": os.getenv('USE_OPTIMIZED_TABLES', 'false'),
            "ENABLE_PERFORMANCE_LOG": os.getenv('ENABLE_PERFORMANCE_LOG', 'false'),
            "ENABLE_QUERY_CACHE": os.getenv('ENABLE_QUERY_CACHE', 'false'),
            "API_PERFORMANCE_MONITORING": os.getenv('API_PERFORMANCE_MONITORING', 'false')
        }
        
        # 检查优化表是否存在
        required_tables = [
            'daily_trading_unified',
            'concept_daily_metrics', 
            'stock_concept_daily_snapshot',
            'today_trading_cache'
        ]
        
        table_status = {}
        for table in required_tables:
            try:
                result = db.execute(f"SHOW TABLES LIKE '{table}'").fetchone()
                table_status[table] = result is not None
            except Exception as e:
                table_status[table] = False
                logger.error(f"检查表 {table} 失败: {e}")
        
        # 检查优化视图是否存在
        required_views = [
            'v_stock_daily_summary',
            'v_concept_daily_ranking',
            'v_stock_concept_performance',
            'v_concept_new_highs',
            'v_today_market_overview'
        ]
        
        view_status = {}
        for view in required_views:
            try:
                result = db.execute(f"SHOW TABLES LIKE '{view}'").fetchone()
                view_status[view] = result is not None
            except Exception as e:
                view_status[view] = False
        
        # 计算整体状态
        optimization_enabled = env_config["USE_OPTIMIZED_TABLES"].lower() == 'true'
        all_tables_exist = all(table_status.values())
        all_views_exist = all(view_status.values())
        
        ready_for_optimization = all_tables_exist and all_views_exist
        
        # 如果启用了优化但表不存在，提供建议
        suggestions = []
        if optimization_enabled and not all_tables_exist:
            suggestions.append("优化表不存在，请运行: mysql < scripts/database/create_optimized_tables.sql")
        
        if optimization_enabled and not all_views_exist:
            suggestions.append("优化视图不存在，请运行: mysql < scripts/database/create_views_and_indexes.sql")
        
        if not optimization_enabled and ready_for_optimization:
            suggestions.append("优化表已就绪，可以运行: python scripts/database/enable_optimization.py enable --mode optimized")
        
        return {
            "optimization_enabled": optimization_enabled,
            "ready_for_optimization": ready_for_optimization,
            "environment_config": env_config,
            "table_status": table_status,
            "view_status": view_status,
            "suggestions": suggestions,
            "performance_summary": {
                "tables_ready": f"{sum(table_status.values())}/{len(required_tables)}",
                "views_ready": f"{sum(view_status.values())}/{len(required_views)}",
                "overall_status": "可用" if ready_for_optimization else "未就绪"
            }
        }
        
    except Exception as e:
        logger.error(f"获取优化状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取优化状态失败: {str(e)}")


@router.get("/optimization/test")
async def test_optimization_performance(
    trading_date: str = "2025-09-02",
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """测试优化查询性能"""
    try:
        from datetime import datetime
        import time
        
        parsed_date = datetime.strptime(trading_date, '%Y-%m-%d').date()
        
        # 测试原始查询性能
        start_time = time.time()
        try:
            from app.models.daily_trading import DailyTrading
            original_count = db.query(DailyTrading).filter(
                DailyTrading.trading_date == parsed_date
            ).count()
            original_time = (time.time() - start_time) * 1000
        except Exception as e:
            original_count = 0
            original_time = -1
            logger.error(f"原始查询测试失败: {e}")
        
        # 测试优化查询性能（如果可用）
        start_time = time.time()
        try:
            # 检查优化表是否存在
            result = db.execute(f"SHOW TABLES LIKE 'daily_trading_unified'").fetchone()
            if result:
                optimized_count = db.execute(
                    f"SELECT COUNT(*) FROM daily_trading_unified WHERE trading_date = '{parsed_date}'"
                ).scalar()
                optimized_time = (time.time() - start_time) * 1000
            else:
                optimized_count = 0
                optimized_time = -1
        except Exception as e:
            optimized_count = 0
            optimized_time = -1
            logger.error(f"优化查询测试失败: {e}")
        
        # 计算性能提升
        performance_improvement = None
        if original_time > 0 and optimized_time > 0:
            performance_improvement = round(original_time / optimized_time, 2)
        
        return {
            "testing_date": trading_date,
            "original_query": {
                "record_count": original_count,
                "execution_time_ms": round(original_time, 2) if original_time > 0 else None,
                "status": "成功" if original_time > 0 else "失败"
            },
            "optimized_query": {
                "record_count": optimized_count,
                "execution_time_ms": round(optimized_time, 2) if optimized_time > 0 else None,
                "status": "成功" if optimized_time > 0 else "未启用/失败"
            },
            "performance_comparison": {
                "improvement_factor": performance_improvement,
                "improvement_description": f"{performance_improvement}倍提升" if performance_improvement else "无法比较",
                "data_consistency": "一致" if original_count == optimized_count and original_count > 0 else "不一致或无数据"
            }
        }
        
    except Exception as e:
        logger.error(f"性能测试失败: {e}")
        raise HTTPException(status_code=500, detail=f"性能测试失败: {str(e)}")


@router.get("/optimization/migration-status")
async def get_migration_status(
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """获取数据迁移状态"""
    try:
        import json
        from pathlib import Path
        
        # 检查迁移状态文件
        migration_state_file = Path("migration_state.json")
        migration_status = None
        
        if migration_state_file.exists():
            try:
                with open(migration_state_file, 'r') as f:
                    migration_status = json.load(f)
            except Exception as e:
                logger.error(f"读取迁移状态文件失败: {e}")
        
        # 检查数据量对比
        data_comparison = {}
        try:
            # 检查原始表数据量
            from app.models.daily_trading import DailyTrading, ConceptDailySummary, StockConceptRanking
            
            original_counts = {
                "daily_trading": db.query(DailyTrading).count(),
                "concept_daily_summary": db.query(ConceptDailySummary).count(),
                "stock_concept_ranking": db.query(StockConceptRanking).count()
            }
            
            # 检查优化表数据量
            optimized_counts = {}
            optimized_tables = {
                "daily_trading_unified": "daily_trading_unified",
                "concept_daily_metrics": "concept_daily_metrics", 
                "stock_concept_daily_snapshot": "stock_concept_daily_snapshot"
            }
            
            for key, table in optimized_tables.items():
                try:
                    result = db.execute(f"SHOW TABLES LIKE '{table}'").fetchone()
                    if result:
                        count = db.execute(f"SELECT COUNT(*) FROM {table}").scalar()
                        optimized_counts[key] = count
                    else:
                        optimized_counts[key] = 0
                except Exception:
                    optimized_counts[key] = 0
            
            data_comparison = {
                "original_tables": original_counts,
                "optimized_tables": optimized_counts,
                "migration_progress": {
                    "daily_data": f"{optimized_counts.get('daily_trading_unified', 0)}/{original_counts.get('daily_trading', 0)}",
                    "concept_data": f"{optimized_counts.get('concept_daily_metrics', 0)}/{original_counts.get('concept_daily_summary', 0)}",
                    "ranking_data": f"{optimized_counts.get('stock_concept_daily_snapshot', 0)}/{original_counts.get('stock_concept_ranking', 0)}"
                }
            }
            
        except Exception as e:
            logger.error(f"数据对比检查失败: {e}")
            data_comparison["error"] = str(e)
        
        return {
            "migration_file_exists": migration_state_file.exists(),
            "migration_status": migration_status,
            "data_comparison": data_comparison,
            "recommendations": [
                "如果未开始迁移，运行: python scripts/database/smooth_migration_service.py --database-url your-db-url",
                "如果迁移中断，运行: python scripts/database/smooth_migration_service.py --resume",
                "如果需要验证数据，运行: python scripts/database/smooth_migration_service.py --verify-only"
            ]
        }
        
    except Exception as e:
        logger.error(f"获取迁移状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取迁移状态失败: {str(e)}")