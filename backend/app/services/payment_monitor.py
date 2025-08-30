"""
支付监控和告警服务
Payment Monitoring and Alert Service
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, text

from app.core.database import get_db
from app.core.logging import logger
from app.core.config import settings
from app.models.payment import PaymentOrder, RefundRecord, PaymentStatus, RefundStatus
from app.models.user import User


class PaymentMonitor:
    """支付监控服务"""
    
    def __init__(self):
        self.alert_thresholds = {
            'high_failure_rate': 0.1,  # 失败率超过10%
            'suspicious_refund_rate': 0.05,  # 退款率超过5%
            'large_amount_threshold': 1000,  # 大额交易阈值（元）
            'monitor_window_hours': 24  # 监控窗口（小时）
        }
    
    async def get_payment_health_metrics(self, db: Session) -> Dict[str, Any]:
        """获取支付系统健康指标"""
        try:
            # 设置监控时间窗口
            window_start = datetime.now() - timedelta(hours=self.alert_thresholds['monitor_window_hours'])
            
            # 1. 基础支付统计
            payment_stats = db.query(
                func.count(PaymentOrder.id).label('total_orders'),
                func.sum(func.case((PaymentOrder.status == PaymentStatus.PAID, 1), else_=0)).label('paid_orders'),
                func.sum(func.case((PaymentOrder.status == PaymentStatus.FAILED, 1), else_=0)).label('failed_orders'),
                func.sum(func.case((PaymentOrder.status == PaymentStatus.CANCELLED, 1), else_=0)).label('cancelled_orders'),
                func.sum(func.case((PaymentOrder.status == PaymentStatus.PAID, PaymentOrder.amount), else_=0)).label('total_amount'),
                func.avg(func.case((PaymentOrder.status == PaymentStatus.PAID, PaymentOrder.amount), else_=None)).label('avg_amount')
            ).filter(PaymentOrder.created_at >= window_start).first()
            
            # 2. 退款统计
            refund_stats = db.query(
                func.count(RefundRecord.id).label('total_refunds'),
                func.sum(func.case((RefundRecord.refund_status == RefundStatus.SUCCESS, 1), else_=0)).label('successful_refunds'),
                func.sum(func.case((RefundRecord.refund_status == RefundStatus.SUCCESS, RefundRecord.refund_amount), else_=0)).label('total_refund_amount')
            ).filter(RefundRecord.created_at >= window_start).first()
            
            # 3. 计算关键指标
            total_orders = payment_stats.total_orders or 0
            paid_orders = payment_stats.paid_orders or 0
            failed_orders = payment_stats.failed_orders or 0
            total_refunds = refund_stats.total_refunds or 0
            
            success_rate = (paid_orders / total_orders) if total_orders > 0 else 0
            failure_rate = (failed_orders / total_orders) if total_orders > 0 else 0
            refund_rate = (total_refunds / paid_orders) if paid_orders > 0 else 0
            
            # 4. 获取大额交易
            large_transactions = db.query(PaymentOrder).filter(
                and_(
                    PaymentOrder.created_at >= window_start,
                    PaymentOrder.amount >= self.alert_thresholds['large_amount_threshold'],
                    PaymentOrder.status == PaymentStatus.PAID
                )
            ).count()
            
            # 5. 活跃用户统计
            active_users = db.query(func.count(func.distinct(PaymentOrder.user_id))).filter(
                and_(
                    PaymentOrder.created_at >= window_start,
                    PaymentOrder.status == PaymentStatus.PAID
                )
            ).scalar()
            
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'window_hours': self.alert_thresholds['monitor_window_hours'],
                'total_orders': total_orders,
                'paid_orders': paid_orders,
                'failed_orders': failed_orders,
                'cancelled_orders': payment_stats.cancelled_orders or 0,
                'success_rate': round(success_rate, 4),
                'failure_rate': round(failure_rate, 4),
                'refund_rate': round(refund_rate, 4),
                'total_amount': float(payment_stats.total_amount or 0),
                'avg_amount': float(payment_stats.avg_amount or 0),
                'total_refunds': total_refunds,
                'successful_refunds': refund_stats.successful_refunds or 0,
                'total_refund_amount': float(refund_stats.total_refund_amount or 0),
                'large_transactions': large_transactions,
                'active_users': active_users or 0
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Get payment health metrics error: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def check_alerts(self, db: Session) -> List[Dict[str, Any]]:
        """检查告警条件"""
        alerts = []
        
        try:
            metrics = await self.get_payment_health_metrics(db)
            
            if 'error' in metrics:
                alerts.append({
                    'type': 'system_error',
                    'severity': 'high',
                    'message': f"支付监控系统异常: {metrics['error']}",
                    'timestamp': metrics['timestamp']
                })
                return alerts
            
            # 1. 检查失败率告警
            if metrics['failure_rate'] > self.alert_thresholds['high_failure_rate']:
                alerts.append({
                    'type': 'high_failure_rate',
                    'severity': 'high',
                    'message': f"支付失败率过高: {metrics['failure_rate']:.2%} (阈值: {self.alert_thresholds['high_failure_rate']:.2%})",
                    'value': metrics['failure_rate'],
                    'threshold': self.alert_thresholds['high_failure_rate'],
                    'timestamp': metrics['timestamp']
                })
            
            # 2. 检查退款率告警
            if metrics['refund_rate'] > self.alert_thresholds['suspicious_refund_rate']:
                alerts.append({
                    'type': 'high_refund_rate',
                    'severity': 'medium',
                    'message': f"退款率异常: {metrics['refund_rate']:.2%} (阈值: {self.alert_thresholds['suspicious_refund_rate']:.2%})",
                    'value': metrics['refund_rate'],
                    'threshold': self.alert_thresholds['suspicious_refund_rate'],
                    'timestamp': metrics['timestamp']
                })
            
            # 3. 检查大额交易告警
            if metrics['large_transactions'] > 0:
                alerts.append({
                    'type': 'large_transactions',
                    'severity': 'low',
                    'message': f"检测到 {metrics['large_transactions']} 笔大额交易 (>¥{self.alert_thresholds['large_amount_threshold']})",
                    'value': metrics['large_transactions'],
                    'threshold': self.alert_thresholds['large_amount_threshold'],
                    'timestamp': metrics['timestamp']
                })
            
            # 4. 检查异常订单
            window_start = datetime.now() - timedelta(hours=1)  # 最近1小时
            
            # 检查异常快速支付（可能的测试或异常行为）
            rapid_payments = db.query(PaymentOrder).filter(
                and_(
                    PaymentOrder.created_at >= window_start,
                    PaymentOrder.paid_at.isnot(None),
                    func.timestampdiff(text('SECOND'), PaymentOrder.created_at, PaymentOrder.paid_at) < 10
                )
            ).count()
            
            if rapid_payments > 5:
                alerts.append({
                    'type': 'rapid_payments',
                    'severity': 'medium',
                    'message': f"检测到 {rapid_payments} 笔异常快速支付（<10秒完成）",
                    'value': rapid_payments,
                    'timestamp': metrics['timestamp']
                })
            
            logger.info(f"Payment health check completed. Metrics: {metrics}, Alerts: {len(alerts)}")
            return alerts
            
        except Exception as e:
            logger.error(f"Check payment alerts error: {e}")
            return [{
                'type': 'monitor_error',
                'severity': 'high',
                'message': f"支付监控检查异常: {e}",
                'timestamp': datetime.now().isoformat()
            }]
    
    async def get_payment_trends(self, db: Session, days: int = 7) -> Dict[str, Any]:
        """获取支付趋势数据"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # 按日统计支付数据
            daily_stats = db.execute(text("""
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as total_orders,
                    SUM(CASE WHEN status = 'paid' THEN 1 ELSE 0 END) as paid_orders,
                    SUM(CASE WHEN status = 'paid' THEN amount ELSE 0 END) as total_amount
                FROM payment_orders 
                WHERE created_at >= :start_date AND created_at <= :end_date
                GROUP BY DATE(created_at)
                ORDER BY date
            """), {'start_date': start_date, 'end_date': end_date}).fetchall()
            
            trends = {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': days
                },
                'daily_data': []
            }
            
            for row in daily_stats:
                trends['daily_data'].append({
                    'date': row.date.isoformat(),
                    'total_orders': row.total_orders,
                    'paid_orders': row.paid_orders,
                    'total_amount': float(row.total_amount or 0),
                    'success_rate': (row.paid_orders / row.total_orders) if row.total_orders > 0 else 0
                })
            
            return trends
            
        except Exception as e:
            logger.error(f"Get payment trends error: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def send_alert_notification(self, alert: Dict[str, Any]):
        """发送告警通知（可扩展到邮件、短信、钉钉等）"""
        try:
            # 目前仅记录日志，可以扩展为发送邮件、短信等
            severity = alert.get('severity', 'low')
            message = alert.get('message', '')
            
            log_message = f"[PAYMENT ALERT] {severity.upper()}: {message}"
            
            if severity == 'high':
                logger.critical(log_message)
            elif severity == 'medium':
                logger.warning(log_message)
            else:
                logger.info(log_message)
            
            # TODO: 这里可以添加更多通知渠道
            # - 邮件通知
            # - 短信通知
            # - 钉钉/企业微信通知
            # - Slack通知
            
        except Exception as e:
            logger.error(f"Send alert notification error: {e}")
    
    async def run_monitoring_cycle(self):
        """运行监控循环"""
        while True:
            try:
                # 获取数据库会话
                db = next(get_db())
                
                # 检查告警
                alerts = await self.check_alerts(db)
                
                # 发送告警通知
                for alert in alerts:
                    await self.send_alert_notification(alert)
                
                # 记录监控执行
                if alerts:
                    logger.info(f"Payment monitoring cycle completed with {len(alerts)} alerts")
                
                db.close()
                
            except Exception as e:
                logger.error(f"Payment monitoring cycle error: {e}")
            
            # 每10分钟执行一次监控
            await asyncio.sleep(600)


# 全局实例
payment_monitor = PaymentMonitor()


# 异步启动监控任务的函数
async def start_payment_monitoring():
    """启动支付监控任务"""
    if settings.PAYMENT_ENABLED:
        logger.info("Starting payment monitoring service...")
        asyncio.create_task(payment_monitor.run_monitoring_cycle())
    else:
        logger.info("Payment monitoring disabled (PAYMENT_ENABLED=False)")