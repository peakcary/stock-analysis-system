"""
系统监控和健康检查API
System Monitoring and Health Check API
"""

from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db, engine
from app.core.redis_cache import cache

router = APIRouter()


@router.get("/health", summary="系统健康检查")
async def health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    全面的系统健康检查
    检查数据库、缓存、文件系统等组件状态
    """
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    # 1. 数据库连接检查
    try:
        db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = {
            "status": "healthy",
            "message": "数据库连接正常"
        }
    except Exception as e:
        health_status["checks"]["database"] = {
            "status": "unhealthy", 
            "message": f"数据库连接失败: {str(e)}"
        }
        health_status["status"] = "unhealthy"
    
    # 2. Redis缓存检查
    try:
        if cache.redis_client:
            cache.redis_client.ping()
            health_status["checks"]["cache"] = {
                "status": "healthy",
                "message": "Redis缓存连接正常"
            }
        else:
            health_status["checks"]["cache"] = {
                "status": "degraded",
                "message": "Redis未启用，使用内存缓存"
            }
    except Exception as e:
        health_status["checks"]["cache"] = {
            "status": "unhealthy",
            "message": f"Redis连接失败: {str(e)}"
        }
    
    # 3. 数据库表检查
    try:
        # 检查核心表是否存在
        tables = ['users', 'payment_orders', 'payment_packages', 'stocks']
        missing_tables = []
        
        for table in tables:
            result = db.execute(text(f"SELECT COUNT(*) FROM {table} LIMIT 1"))
            
        health_status["checks"]["database_tables"] = {
            "status": "healthy",
            "message": "核心数据表正常"
        }
        
    except Exception as e:
        health_status["checks"]["database_tables"] = {
            "status": "unhealthy",
            "message": f"数据表检查失败: {str(e)}"
        }
        health_status["status"] = "unhealthy"
    
    return health_status


@router.get("/stats", summary="系统统计信息")
async def system_stats(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    系统运行统计信息
    提供关键指标和性能数据
    """
    
    stats = {}
    
    try:
        # 用户统计
        user_stats = db.execute(text("""
            SELECT 
                COUNT(*) as total_users,
                COUNT(CASE WHEN is_active = 1 THEN 1 END) as active_users,
                COUNT(CASE WHEN membership_type = 'PRO' THEN 1 END) as pro_users,
                COUNT(CASE WHEN membership_type = 'PREMIUM' THEN 1 END) as premium_users
            FROM users
        """)).fetchone()
        
        stats["users"] = {
            "total": user_stats.total_users,
            "active": user_stats.active_users, 
            "pro": user_stats.pro_users,
            "premium": user_stats.premium_users
        }
        
        # 支付统计
        payment_stats = db.execute(text("""
            SELECT 
                COUNT(*) as total_orders,
                COUNT(CASE WHEN status = 'PAID' THEN 1 END) as paid_orders,
                SUM(CASE WHEN status = 'PAID' THEN amount ELSE 0 END) as total_revenue
            FROM payment_orders
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        """)).fetchone()
        
        stats["payments_30days"] = {
            "total_orders": payment_stats.total_orders,
            "paid_orders": payment_stats.paid_orders,
            "total_revenue": float(payment_stats.total_revenue or 0)
        }
        
        # 股票数据统计
        stock_stats = db.execute(text("""
            SELECT 
                COUNT(*) as total_stocks,
                COUNT(DISTINCT concept) as total_concepts
            FROM stocks
        """)).fetchone()
        
        stats["stocks"] = {
            "total_stocks": stock_stats.total_stocks,
            "total_concepts": stock_stats.total_concepts
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"统计数据获取失败: {str(e)}")
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "stats": stats
    }


@router.get("/version", summary="系统版本信息")
async def version_info() -> Dict[str, str]:
    """获取系统版本和构建信息"""
    
    return {
        "app_name": "股票概念分析系统",
        "version": "1.0.0",
        "build_time": "2024-01-01",  # 可以从环境变量获取
        "api_version": "v1",
        "framework": "FastAPI",
        "python_version": "3.9+",
        "database": "MySQL 8.0+"
    }


@router.get("/metrics", summary="性能指标")
async def performance_metrics() -> Dict[str, Any]:
    """
    系统性能指标
    用于监控和性能分析
    """
    
    metrics = {
        "timestamp": datetime.utcnow().isoformat(),
        "uptime": "需要实现",  # 可以记录应用启动时间
        "memory_usage": "需要实现",  # 内存使用情况
        "cpu_usage": "需要实现",   # CPU使用情况
    }
    
    # 缓存使用情况
    if cache.redis_client:
        try:
            info = cache.redis_client.info()
            metrics["cache"] = {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0)
            }
        except:
            metrics["cache"] = {"status": "unavailable"}
    else:
        metrics["cache"] = {"status": "disabled"}
    
    return metrics