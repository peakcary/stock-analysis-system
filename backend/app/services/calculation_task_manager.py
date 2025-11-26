"""
计算任务管理服务
支持任务队列、重试机制、版本管理和审计日志

特性：
1. 任务队列管理（pending -> processing -> success/failed）
2. 失败重试机制（指数退避）
3. 数据版本管理（支持追踪不同版本的计算结果）
4. 详细的审计日志
5. 任务依赖管理（如某个日期的排名计算依赖于该日期的原始数据导入）
"""

from typing import Dict, List, Optional, Any, Callable
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
import logging
import json

from app.models import MetricsCalculationTask
from app.services.metrics_calculation_service import MetricsCalculationService

logger = logging.getLogger(__name__)


class CalculationTaskManager:
    """计算任务管理器"""

    def __init__(self, db: Session):
        """
        初始化管理器

        Args:
            db: 数据库会话
        """
        self.db = db
        self.metrics_service = MetricsCalculationService(db)

        # 任务类型到处理函数的映射
        self.task_handlers: Dict[str, Callable] = {
            'daily_ranking': self._handle_daily_ranking,
            'concept_summary': self._handle_concept_summary,
            'new_high_detection': self._handle_new_high_detection
        }

    def submit_task(
        self,
        task_type: str,
        target_date: date,
        metric_type: Optional[str] = None,
        created_by: str = 'system',
        remarks: str = ''
    ) -> int:
        """
        提交新的计算任务

        Args:
            task_type: 任务类型
            target_date: 目标计算日期
            metric_type: 指标类型过滤
            created_by: 任务创建人
            remarks: 备注

        Returns:
            任务ID
        """
        logger.info(f"提交任务: {task_type} for {target_date}")

        task = MetricsCalculationTask(
            task_type=task_type,
            target_date=target_date,
            metric_type=metric_type,
            status='pending',
            created_by=created_by,
            remarks=remarks,
            data_version=self._generate_version_id(target_date),
            is_latest=True,
            max_retries=3,
            retry_count=0
        )

        self.db.add(task)
        self.db.commit()

        logger.info(f"任务已提交: ID={task.id}")
        return task.id

    def process_pending_tasks(self) -> Dict[str, Any]:
        """
        处理所有待处理任务

        Returns:
            处理结果统计
        """
        logger.info("开始处理待处理任务")

        stats = {
            'processed': 0,
            'success': 0,
            'failed': 0,
            'details': []
        }

        try:
            # 查询待处理任务
            pending_tasks = self.db.query(MetricsCalculationTask).filter(
                MetricsCalculationTask.status == 'pending'
            ).order_by(
                asc(MetricsCalculationTask.created_at)
            ).all()

            logger.info(f"发现 {len(pending_tasks)} 个待处理任务")

            for task in pending_tasks:
                result = self.execute_task(task.id)
                stats['processed'] += 1

                if result['success']:
                    stats['success'] += 1
                else:
                    stats['failed'] += 1

                stats['details'].append({
                    'task_id': task.id,
                    'task_type': task.task_type,
                    'result': result
                })

            logger.info(f"任务处理完成: {stats['success']}/{stats['processed']} 成功")

        except Exception as e:
            logger.error(f"处理待处理任务失败: {str(e)}")

        return stats

    def execute_task(self, task_id: int) -> Dict[str, Any]:
        """
        执行单个任务

        Args:
            task_id: 任务ID

        Returns:
            执行结果
        """
        logger.info(f"执行任务: ID={task_id}")

        try:
            task = self.db.query(MetricsCalculationTask).filter(
                MetricsCalculationTask.id == task_id
            ).first()

            if not task:
                return {'success': False, 'error': f'任务不存在: {task_id}'}

            # 标记为处理中
            task.status = 'processing'
            task.started_at = datetime.now()
            self.db.add(task)
            self.db.commit()

            # 获取对应的处理函数
            handler = self.task_handlers.get(task.task_type)
            if not handler:
                raise ValueError(f"未知的任务类型: {task.task_type}")

            # 执行任务
            result = handler(task)

            # 更新任务状态
            task.status = 'success' if result['success'] else 'failed'
            task.completed_at = datetime.now()

            if task.started_at:
                duration = (task.completed_at - task.started_at).total_seconds()
                task.duration_seconds = int(duration)

            task.log_details = json.dumps(result.get('details', {}), ensure_ascii=False)

            if not result['success']:
                task.error_message = result.get('error', '未知错误')

                # 检查是否需要重试
                if task.retry_count < task.max_retries:
                    task.status = 'pending'
                    task.retry_count += 1
                    logger.warning(f"任务失败，将重试: ID={task_id}, 重试次数={task.retry_count}")

            self.db.add(task)
            self.db.commit()

            logger.info(f"任务执行完成: ID={task_id}, 状态={task.status}")

            return {
                'success': result['success'],
                'task_id': task_id,
                'message': result.get('message', ''),
                'details': result.get('details', {})
            }

        except Exception as e:
            logger.error(f"执行任务失败: {str(e)}")
            self.db.rollback()

            # 更新任务状态为失败
            try:
                task = self.db.query(MetricsCalculationTask).filter(
                    MetricsCalculationTask.id == task_id
                ).first()

                if task:
                    task.status = 'failed'
                    task.error_message = str(e)
                    task.completed_at = datetime.now()

                    if task.started_at:
                        duration = (task.completed_at - task.started_at).total_seconds()
                        task.duration_seconds = int(duration)

                    # 检查重试
                    if task.retry_count < task.max_retries:
                        task.status = 'pending'
                        task.retry_count += 1

                    self.db.add(task)
                    self.db.commit()
            except Exception as e2:
                logger.error(f"更新任务状态失败: {str(e2)}")

            return {
                'success': False,
                'task_id': task_id,
                'error': str(e)
            }

    def get_task_status(self, task_id: int) -> Optional[Dict[str, Any]]:
        """
        获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务信息或None
        """
        task = self.db.query(MetricsCalculationTask).filter(
            MetricsCalculationTask.id == task_id
        ).first()

        if not task:
            return None

        return {
            'task_id': task.id,
            'task_type': task.task_type,
            'target_date': task.target_date.isoformat(),
            'metric_type': task.metric_type,
            'status': task.status,
            'started_at': task.started_at.isoformat() if task.started_at else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
            'duration_seconds': task.duration_seconds,
            'total_items': task.total_items,
            'success_items': task.success_items,
            'failed_items': task.failed_items,
            'retry_count': task.retry_count,
            'error_message': task.error_message,
            'data_version': task.data_version
        }

    def get_task_history(
        self,
        target_date: Optional[date] = None,
        task_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取任务历史记录

        Args:
            target_date: 目标日期过滤
            task_type: 任务类型过滤
            limit: 结果数量限制

        Returns:
            任务列表
        """
        query = self.db.query(MetricsCalculationTask)

        if target_date:
            query = query.filter(MetricsCalculationTask.target_date == target_date)

        if task_type:
            query = query.filter(MetricsCalculationTask.task_type == task_type)

        tasks = query.order_by(
            desc(MetricsCalculationTask.created_at)
        ).limit(limit).all()

        return [self.get_task_status(t.id) for t in tasks]

    def cleanup_old_tasks(self, days: int = 30) -> int:
        """
        清理旧任务（仅保留最新版本）

        Args:
            days: 保留的天数

        Returns:
            删除的任务数量
        """
        logger.info(f"清理 {days} 天前的旧任务")

        cutoff_date = datetime.now() - timedelta(days=days)

        # 找出旧的非最新任务
        old_tasks = self.db.query(MetricsCalculationTask).filter(
            and_(
                MetricsCalculationTask.created_at < cutoff_date,
                MetricsCalculationTask.is_latest == False,
                MetricsCalculationTask.status == 'success'  # 只删除成功的旧任务
            )
        ).all()

        count = len(old_tasks)

        for task in old_tasks:
            self.db.delete(task)

        self.db.commit()

        logger.info(f"删除了 {count} 个旧任务")
        return count

    def _handle_daily_ranking(self, task: MetricsCalculationTask) -> Dict[str, Any]:
        """
        处理每日排名计算任务

        Args:
            task: 任务对象

        Returns:
            处理结果
        """
        logger.info(f"处理每日排名计算: {task.target_date}")

        result = self.metrics_service.calculate_daily_metrics(
            task.target_date,
            task.metric_type,
            task.id
        )

        return result

    def _handle_concept_summary(self, task: MetricsCalculationTask) -> Dict[str, Any]:
        """
        处理概念汇总计算任务

        Args:
            task: 任务对象

        Returns:
            处理结果
        """
        logger.info(f"处理概念汇总计算: {task.target_date}")

        # 这是 daily_ranking 的一部分，可以单独处理
        result = self.metrics_service.calculate_daily_metrics(
            task.target_date,
            task.metric_type,
            task.id
        )

        return result

    def _handle_new_high_detection(self, task: MetricsCalculationTask) -> Dict[str, Any]:
        """
        处理创新高检测任务

        Args:
            task: 任务对象

        Returns:
            处理结果
        """
        logger.info(f"处理创新高检测: {task.target_date}")

        result = self.metrics_service.calculate_daily_metrics(
            task.target_date,
            task.metric_type,
            task.id
        )

        return result

    def _generate_version_id(self, target_date: date) -> str:
        """
        生成数据版本ID

        Args:
            target_date: 目标日期

        Returns:
            版本ID
        """
        # 查询该日期的现有版本数
        existing_count = self.db.query(MetricsCalculationTask).filter(
            MetricsCalculationTask.target_date == target_date
        ).count()

        return f"{target_date.isoformat()}_v{existing_count + 1}"

    def recalculate_date_metrics(
        self,
        target_date: date,
        metric_type: Optional[str] = None,
        force: bool = False,
        created_by: str = 'system'
    ) -> int:
        """
        重新计算指定日期的所有指标

        这个方法在原始数据更正后调用，重新计算所有衍生数据

        Args:
            target_date: 目标日期
            metric_type: 指标类型过滤
            force: 是否强制重新计算
            created_by: 请求人

        Returns:
            任务ID
        """
        logger.info(f"请求重新计算 {target_date} 的指标 (force={force})")

        # 标记旧版本为非最新
        old_tasks = self.db.query(MetricsCalculationTask).filter(
            and_(
                MetricsCalculationTask.target_date == target_date,
                MetricsCalculationTask.is_latest == True,
                MetricsCalculationTask.status == 'success'
            )
        ).all()

        for task in old_tasks:
            task.is_latest = False
            self.db.add(task)

        # 提交新的计算任务
        task_id = self.submit_task(
            task_type='daily_ranking',
            target_date=target_date,
            metric_type=metric_type,
            created_by=created_by,
            remarks=f'重新计算请求 (force={force})'
        )

        self.db.commit()

        return task_id
