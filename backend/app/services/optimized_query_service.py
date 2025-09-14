"""
优化查询服务 - 智能切换新旧表结构
支持渐进式迁移和A/B测试

注意：此服务设计为可选启用，不会影响现有API的正常运行
v2.6.4 - 2025-09-13
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import text, func, desc, asc
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


def check_optimization_enabled():
    """检查是否启用了优化功能"""
    return os.getenv('USE_OPTIMIZED_TABLES', 'false').lower() == 'true'


def check_optimized_tables_exist(db: Session) -> bool:
    """检查优化表是否存在"""
    try:
        required_tables = [
            'daily_trading_unified',
            'concept_daily_metrics',
            'stock_concept_daily_snapshot'
        ]
        
        for table in required_tables:
            result = db.execute(text(f"SHOW TABLES LIKE '{table}'")).fetchone()
            if not result:
                return False
        return True
    except Exception as e:
        logger.warning(f"检查优化表失败: {e}")
        return False


class OptimizedQueryService:
    """优化查询服务 - 支持新旧表智能切换"""
    
    def __init__(self, db: Session):
        self.db = db
        
        # 从环境变量控制优化开关
        self.use_optimized_tables = (
            check_optimization_enabled() and 
            check_optimized_tables_exist(db)
        )
        
        self.enable_performance_log = os.getenv('ENABLE_PERFORMANCE_LOG', 'false').lower() == 'true'
        
        if self.use_optimized_tables:
            logger.info("已启用优化查询模式")
        else:
            logger.info("使用兼容查询模式")
    
    def get_stocks_daily_summary_optimized(self, trading_date: date, page: int = 1, 
                                         size: int = 50, search: Optional[str] = None,
                                         sort_by: str = "trading_volume", 
                                         sort_order: str = "desc") -> Tuple[List[Dict], int]:
        """使用优化表查询股票汇总"""
        
        if not self.use_optimized_tables:
            raise Exception("优化表未启用或不存在")
        
        # 检查是否使用当天缓存表
        table_name = "today_trading_cache" if trading_date == date.today() else "daily_trading_unified"
        
        # 构建基础查询
        base_query = f"""
            SELECT stock_code, stock_name, trading_volume, concept_count, rank_in_date, 0 as heat_value
            FROM {table_name}
        """
        
        conditions = []
        params = {}
        
        if table_name == "daily_trading_unified":
            conditions.append("trading_date = :trading_date")
            params["trading_date"] = trading_date
        
        # 搜索过滤
        if search:
            conditions.append("(stock_code LIKE :search OR stock_name LIKE :search)")
            params["search"] = f"%{search}%"
        
        # 添加条件
        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)
        
        # 排序
        valid_sort_columns = ["trading_volume", "stock_code", "stock_name", "concept_count", "rank_in_date"]
        if sort_by not in valid_sort_columns:
            sort_by = "trading_volume"
        
        sort_direction = "DESC" if sort_order.lower() == "desc" else "ASC"
        base_query += f" ORDER BY {sort_by} {sort_direction}"
        
        # 计算总数
        count_query = f"SELECT COUNT(*) as total FROM ({base_query}) as counted"
        total_count = self.db.execute(text(count_query), params).scalar()
        
        # 分页
        offset = (page - 1) * size
        paginated_query = base_query + f" LIMIT :limit OFFSET :offset"
        params.update({"limit": size, "offset": offset})
        
        # 执行查询
        results = self.db.execute(text(paginated_query), params).fetchall()
        
        # 格式化结果
        stocks = []
        for row in results:
            stocks.append({
                "stock_code": row[0],
                "stock_name": row[1],
                "trading_volume": row[2],
                "concept_count": row[3],
                "rank_in_date": row[4],
                "heat_value": row[5]
            })
        
        return stocks, total_count
    
    def get_concept_rankings_optimized(self, trading_date: date, limit: int = 100, 
                                     new_high_only: bool = False) -> List[Dict]:
        """使用优化表查询概念排行"""
        
        if not self.use_optimized_tables:
            raise Exception("优化表未启用或不存在")
        
        base_query = """
            SELECT concept_name, total_volume, stock_count, avg_volume, max_volume, 
                   volume_rank, is_new_high, new_high_days, volume_change_pct
            FROM concept_daily_metrics
            WHERE trading_date = :trading_date
        """
        
        params = {"trading_date": trading_date}
        
        if new_high_only:
            base_query += " AND is_new_high = 1"
        
        base_query += " ORDER BY volume_rank ASC LIMIT :limit"
        params["limit"] = limit
        
        results = self.db.execute(text(base_query), params).fetchall()
        
        concepts = []
        for row in results:
            concepts.append({
                "concept_name": row[0],
                "total_volume": row[1],
                "stock_count": row[2],
                "avg_volume": float(row[3]),
                "max_volume": row[4],
                "volume_rank": row[5],
                "is_new_high": bool(row[6]),
                "new_high_days": row[7],
                "volume_change_pct": float(row[8]) if row[8] else 0
            })
        
        return concepts
    
    def get_stock_concepts_optimized(self, stock_code: str, trading_date: date) -> List[Dict]:
        """使用优化表查询股票概念"""
        
        if not self.use_optimized_tables:
            raise Exception("优化表未启用或不存在")
        
        query = """
            SELECT concept_name, concept_rank, volume_percentage, 
                   concept_total_volume, concept_stock_count, trading_volume
            FROM stock_concept_daily_snapshot
            WHERE stock_code = :stock_code AND trading_date = :trading_date
            ORDER BY concept_total_volume DESC
        """
        
        params = {"stock_code": stock_code, "trading_date": trading_date}
        results = self.db.execute(text(query), params).fetchall()
        
        concepts = []
        for row in results:
            concepts.append({
                "concept_name": row[0],
                "concept_rank": row[1],
                "volume_percentage": float(row[2]),
                "concept_total_volume": row[3],
                "concept_stock_count": row[4],
                "trading_volume": row[5]
            })
        
        return concepts
    
    def is_optimization_available(self) -> Dict[str, Any]:
        """检查优化功能可用性"""
        return {
            "optimization_enabled": check_optimization_enabled(),
            "tables_exist": check_optimized_tables_exist(self.db),
            "service_ready": self.use_optimized_tables,
            "performance_logging": self.enable_performance_log
        }


# 提供独立的工具函数，不依赖类
def get_optimized_stock_summary(db: Session, trading_date: date, page: int = 1, 
                               size: int = 50, search: Optional[str] = None) -> Optional[Tuple[List[Dict], int]]:
    """
    独立的优化查询函数，可安全调用
    如果优化不可用，返回None
    """
    try:
        if not check_optimization_enabled() or not check_optimized_tables_exist(db):
            return None
        
        service = OptimizedQueryService(db)
        return service.get_stocks_daily_summary_optimized(trading_date, page, size, search)
    
    except Exception as e:
        logger.warning(f"优化查询失败，将使用原始查询: {e}")
        return None


def get_optimization_status(db: Session) -> Dict[str, Any]:
    """获取优化状态信息"""
    try:
        service = OptimizedQueryService(db)
        return service.is_optimization_available()
    except Exception as e:
        return {
            "optimization_enabled": False,
            "tables_exist": False,
            "service_ready": False,
            "error": str(e)
        }