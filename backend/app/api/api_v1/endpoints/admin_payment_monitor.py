"""
管理员支付监控API
Admin Payment Monitoring API
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.core.logging import logger
from app.models.user import User
from app.services.payment_monitor import payment_monitor
from app.middleware.payment_security import payment_security_middleware

router = APIRouter()


def get_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    """验证管理员权限"""
    if current_user.username != 'admin':  # 简单的管理员验证，可以扩展为角色系统
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


@router.get("/health-metrics")
async def get_payment_health_metrics(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """获取支付系统健康指标"""
    try:
        metrics = await payment_monitor.get_payment_health_metrics(db)
        return {
            "status": "success",
            "data": metrics
        }
    except Exception as e:
        logger.error(f"Get payment health metrics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取支付健康指标失败"
        )


@router.get("/alerts")
async def get_payment_alerts(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """获取支付告警信息"""
    try:
        alerts = await payment_monitor.check_alerts(db)
        return {
            "status": "success",
            "data": {
                "alerts": alerts,
                "count": len(alerts),
                "has_critical": any(alert.get('severity') == 'high' for alert in alerts)
            }
        }
    except Exception as e:
        logger.error(f"Get payment alerts error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取支付告警失败"
        )


@router.get("/trends")
async def get_payment_trends(
    days: int = Query(default=7, ge=1, le=30, description="查询天数（1-30天）"),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """获取支付趋势数据"""
    try:
        trends = await payment_monitor.get_payment_trends(db, days=days)
        return {
            "status": "success",
            "data": trends
        }
    except Exception as e:
        logger.error(f"Get payment trends error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取支付趋势数据失败"
        )


@router.get("/security-stats")
async def get_security_stats(
    admin_user: User = Depends(get_admin_user)
):
    """获取支付安全统计"""
    try:
        stats = payment_security_middleware.get_security_stats()
        return {
            "status": "success",
            "data": stats
        }
    except Exception as e:
        logger.error(f"Get security stats error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取安全统计失败"
        )


@router.post("/test-alert")
async def test_alert_notification(
    alert_type: str = Query(description="告警类型"),
    message: str = Query(description="告警消息"),
    admin_user: User = Depends(get_admin_user)
):
    """测试告警通知"""
    try:
        test_alert = {
            'type': f'test_{alert_type}',
            'severity': 'medium',
            'message': f'测试告警: {message}',
            'timestamp': str(datetime.now())
        }
        
        await payment_monitor.send_alert_notification(test_alert)
        
        return {
            "status": "success",
            "message": "测试告警已发送"
        }
    except Exception as e:
        logger.error(f"Test alert notification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="测试告警失败"
        )


@router.get("/system-status")
async def get_payment_system_status(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """获取支付系统整体状态"""
    try:
        # 获取健康指标
        metrics = await payment_monitor.get_payment_health_metrics(db)
        
        # 获取告警
        alerts = await payment_monitor.check_alerts(db)
        
        # 获取安全统计
        security_stats = payment_security_middleware.get_security_stats()
        
        # 判断系统状态
        system_status = "healthy"
        if any(alert.get('severity') == 'high' for alert in alerts):
            system_status = "critical"
        elif any(alert.get('severity') == 'medium' for alert in alerts):
            system_status = "warning"
        
        return {
            "status": "success",
            "data": {
                "system_status": system_status,
                "timestamp": metrics.get('timestamp'),
                "metrics_summary": {
                    "total_orders": metrics.get('total_orders', 0),
                    "success_rate": metrics.get('success_rate', 0),
                    "failure_rate": metrics.get('failure_rate', 0),
                    "refund_rate": metrics.get('refund_rate', 0),
                    "total_amount": metrics.get('total_amount', 0)
                },
                "alerts_summary": {
                    "total_alerts": len(alerts),
                    "critical_alerts": sum(1 for alert in alerts if alert.get('severity') == 'high'),
                    "warning_alerts": sum(1 for alert in alerts if alert.get('severity') == 'medium')
                },
                "security_summary": security_stats
            }
        }
        
    except Exception as e:
        logger.error(f"Get payment system status error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取支付系统状态失败"
        )