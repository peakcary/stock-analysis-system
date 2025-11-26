"""
统一指标计算服务
支持多种指标类型的排名、汇总和创新高检测

功能特性：
1. 支持多种指标类型（eee_heat, ttv_trading_volume等）
2. 股票级指标存储和排名计算
3. 概念级指标汇总和聚合
4. 创新高检测和记录
5. 可重新计算和版本管理
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import date, timedelta, datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
import logging

from app.models import (
    Stock, Concept, StockConcept,
    StockDailyMetrics, ConceptMetricsSummary, MetricsCalculationTask
)
from app.models.daily_trading import ConceptHighRecord

logger = logging.getLogger(__name__)


class MetricsCalculationService:
    """统一指标计算服务"""

    def __init__(self, db: Session):
        """
        初始化服务

        Args:
            db: 数据库会话
        """
        self.db = db

    def calculate_daily_metrics(
        self,
        target_date: date,
        metric_type: Optional[str] = None,
        task_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        计算指定日期的所有指标（排名、汇总等）

        Args:
            target_date: 目标计算日期
            metric_type: 指标类型过滤（None表示所有）
            task_id: 任务ID（用于更新任务状态）

        Returns:
            计算结果字典
        """
        logger.info(f"开始计算 {target_date} 的指标数据")

        stats = {
            'total_items': 0,
            'success_items': 0,
            'failed_items': 0,
            'details': {}
        }

        try:
            # 创建或获取计算任务
            task = self._get_or_create_task(target_date, 'daily_ranking', metric_type)

            if task_id:
                task.id = task_id

            # 标记任务为处理中
            task.status = 'processing'
            task.started_at = datetime.now()
            self.db.add(task)
            self.db.flush()

            # 1. 计算股票级的排名
            ranking_result = self._calculate_stock_rankings(target_date, metric_type)
            stats['details']['stock_rankings'] = ranking_result
            stats['total_items'] += ranking_result['total']
            stats['success_items'] += ranking_result['success']

            # 2. 计算概念级的汇总
            summary_result = self._calculate_concept_summaries(target_date, metric_type)
            stats['details']['concept_summaries'] = summary_result
            stats['total_items'] += summary_result['total']
            stats['success_items'] += summary_result['success']

            # 3. 检测创新高
            high_result = self._detect_new_highs(target_date, metric_type)
            stats['details']['new_highs'] = high_result
            stats['total_items'] += high_result['total']
            stats['success_items'] += high_result['success']

            # 更新任务状态为成功
            task.status = 'success'
            task.completed_at = datetime.now()
            duration = (task.completed_at - task.started_at).total_seconds()
            task.duration_seconds = int(duration)
            task.success_items = stats['success_items']
            task.failed_items = len(stats.get('errors', []))
            task.total_items = stats['total_items']

            self.db.commit()
            logger.info(f"指标计算完成: {stats['success_items']}/{stats['total_items']} 成功")

            return {
                'success': True,
                'message': f'成功计算 {stats["success_items"]}/{stats["total_items"]} 个指标项',
                'target_date': target_date.isoformat(),
                'task_id': task.id,
                'stats': stats
            }

        except Exception as e:
            logger.error(f"指标计算失败: {str(e)}")
            self.db.rollback()
            return {
                'success': False,
                'message': f'指标计算失败: {str(e)}',
                'error': str(e)
            }

    def _calculate_stock_rankings(
        self,
        target_date: date,
        metric_type: Optional[str] = None
    ) -> Dict[str, int]:
        """
        计算股票在各概念中的排名

        Args:
            target_date: 目标日期
            metric_type: 指标类型过滤

        Returns:
            计算统计: {'total': int, 'success': int}
        """
        stats = {'total': 0, 'success': 0}

        try:
            # 查询该日期的所有指标数据
            query = self.db.query(StockDailyMetrics).filter(
                StockDailyMetrics.trade_date == target_date
            )

            if metric_type:
                query = query.filter(StockDailyMetrics.metric_type == metric_type)

            metrics = query.all()
            stats['total'] = len(metrics)

            if not metrics:
                logger.info(f"没有 {target_date} 的指标数据需要排名计算")
                return stats

            # 按概念分组计算排名
            concept_groups = self._group_metrics_by_concept(metrics)

            for concept_id, metric_items in concept_groups.items():
                # 按指标值从高到低排序
                sorted_items = sorted(metric_items, key=lambda x: x.metric_value, reverse=True)

                # 分配排名
                for rank, metric in enumerate(sorted_items, 1):
                    metric.ranking_in_concept = rank

                    # 计算占比
                    total_value = sum(m.metric_value for m in sorted_items)
                    if total_value > 0:
                        percentage = (metric.metric_value / total_value) * 100
                        metric.percentage_in_concept = round(percentage, 2)

                    self.db.add(metric)
                    stats['success'] += 1

            self.db.flush()

        except Exception as e:
            logger.error(f"股票排名计算失败: {str(e)}")
            stats['success'] = 0

        return stats

    def _calculate_concept_summaries(
        self,
        target_date: date,
        metric_type: Optional[str] = None
    ) -> Dict[str, int]:
        """
        计算概念级的汇总指标

        Args:
            target_date: 目标日期
            metric_type: 指标类型过滤

        Returns:
            计算统计: {'total': int, 'success': int}
        """
        stats = {'total': 0, 'success': 0}

        try:
            # 查询该日期涉及的所有概念
            query = self.db.query(Concept).join(
                StockConcept, StockConcept.concept_id == Concept.id
            ).join(
                Stock, Stock.id == StockConcept.stock_id
            ).join(
                StockDailyMetrics, and_(
                    StockDailyMetrics.stock_id == Stock.id,
                    StockDailyMetrics.trade_date == target_date
                )
            ).distinct()

            if metric_type:
                query = query.filter(StockDailyMetrics.metric_type == metric_type)

            concepts = query.all()
            stats['total'] = len(concepts)

            if not concepts:
                logger.info(f"没有 {target_date} 的概念汇总数据需要计算")
                return stats

            # 为每个概念计算汇总
            metric_types_to_process = [metric_type] if metric_type else [
                'eee_heat', 'ttv_trading_volume'
            ]

            for concept in concepts:
                for mtype in metric_types_to_process:
                    summary = self._calculate_concept_summary_for_type(
                        concept, target_date, mtype
                    )
                    if summary:
                        self.db.add(summary)
                        stats['success'] += 1

            self.db.flush()

        except Exception as e:
            logger.error(f"概念汇总计算失败: {str(e)}")
            stats['success'] = 0

        return stats

    def _calculate_concept_summary_for_type(
        self,
        concept: Concept,
        target_date: date,
        metric_type: str
    ) -> Optional[ConceptMetricsSummary]:
        """
        计算单个概念单个指标类型的汇总

        Args:
            concept: 概念对象
            target_date: 目标日期
            metric_type: 指标类型

        Returns:
            汇总结果对象或None
        """
        try:
            # 查询该概念该日期该指标类型的所有值
            metrics = self.db.query(StockDailyMetrics).join(
                Stock, Stock.id == StockDailyMetrics.stock_id
            ).join(
                StockConcept, and_(
                    StockConcept.stock_id == Stock.id,
                    StockConcept.concept_id == concept.id
                )
            ).filter(
                and_(
                    StockDailyMetrics.trade_date == target_date,
                    StockDailyMetrics.metric_type == metric_type
                )
            ).all()

            if not metrics:
                return None

            # 计算聚合指标
            values = [m.metric_value for m in metrics]
            total_value = sum(values)
            avg_value = total_value / len(values) if values else 0
            max_value = max(values) if values else 0
            min_value = min(values) if values else 0

            # 检查是否为创新高（比较历史最大值）
            historical_max = self.db.query(func.max(ConceptMetricsSummary.total_value)).filter(
                and_(
                    ConceptMetricsSummary.concept_id == concept.id,
                    ConceptMetricsSummary.metric_type == metric_type,
                    ConceptMetricsSummary.trade_date < target_date
                )
            ).scalar() or 0

            is_new_high = total_value > historical_max

            # 创建或更新汇总记录
            summary = ConceptMetricsSummary(
                concept_id=concept.id,
                trade_date=target_date,
                metric_type=metric_type,
                total_value=total_value,
                avg_value=avg_value,
                max_value=max_value,
                min_value=min_value,
                stock_count=len(metrics),
                is_new_high=is_new_high,
                historical_max=float(historical_max)
            )

            return summary

        except Exception as e:
            logger.error(f"计算概念汇总失败 [{concept.concept_name}, {metric_type}]: {str(e)}")
            return None

    def _detect_new_highs(
        self,
        target_date: date,
        metric_type: Optional[str] = None
    ) -> Dict[str, int]:
        """
        检测创新高

        Args:
            target_date: 目标日期
            metric_type: 指标类型过滤

        Returns:
            检测统计: {'total': int, 'success': int}
        """
        stats = {'total': 0, 'success': 0}

        try:
            # 查询该日期的所有创新高汇总
            query = self.db.query(ConceptMetricsSummary).filter(
                and_(
                    ConceptMetricsSummary.trade_date == target_date,
                    ConceptMetricsSummary.is_new_high == True
                )
            )

            if metric_type:
                query = query.filter(ConceptMetricsSummary.metric_type == metric_type)

            new_highs = query.all()
            stats['total'] = len(new_highs)

            # 记录创新高
            for summary in new_highs:
                concept = self.db.query(Concept).filter(
                    Concept.id == summary.concept_id
                ).first()

                if concept:
                    record = ConceptHighRecord(
                        concept_name=concept.concept_name,
                        trading_date=target_date,
                        total_volume=int(summary.total_value),
                        days_period=30,  # 默认30天周期
                        is_active=True
                    )
                    self.db.add(record)
                    stats['success'] += 1

            self.db.flush()

        except Exception as e:
            logger.error(f"创新高检测失败: {str(e)}")
            stats['success'] = 0

        return stats

    def _group_metrics_by_concept(
        self,
        metrics: List[StockDailyMetrics]
    ) -> Dict[int, List[StockDailyMetrics]]:
        """
        按概念分组指标

        Args:
            metrics: 指标列表

        Returns:
            按概念ID分组的字典
        """
        groups = {}

        for metric in metrics:
            # 查询该股票所属的概念
            stock_concepts = self.db.query(StockConcept).filter(
                StockConcept.stock_id == metric.stock_id
            ).all()

            for sc in stock_concepts:
                concept_id = sc.concept_id
                if concept_id not in groups:
                    groups[concept_id] = []
                groups[concept_id].append(metric)

        return groups

    def _get_or_create_task(
        self,
        target_date: date,
        task_type: str,
        metric_type: Optional[str] = None
    ) -> MetricsCalculationTask:
        """
        获取或创建计算任务

        Args:
            target_date: 目标日期
            task_type: 任务类型
            metric_type: 指标类型

        Returns:
            任务对象
        """
        # 检查是否存在最新版本的任务
        existing = self.db.query(MetricsCalculationTask).filter(
            and_(
                MetricsCalculationTask.target_date == target_date,
                MetricsCalculationTask.task_type == task_type,
                MetricsCalculationTask.metric_type == metric_type,
                MetricsCalculationTask.is_latest == True
            )
        ).first()

        if existing:
            # 标记旧任务为非最新
            existing.is_latest = False
            self.db.add(existing)

        # 创建新任务
        task = MetricsCalculationTask(
            task_type=task_type,
            target_date=target_date,
            metric_type=metric_type,
            status='pending',
            is_latest=True,
            data_version=f"{target_date.isoformat()}_v1"
        )

        self.db.add(task)
        self.db.flush()

        return task

    def recalculate_metrics(
        self,
        target_date: date,
        metric_type: Optional[str] = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        重新计算指定日期的指标

        这个方法支持在原始数据更正后重新计算所有衍生数据

        Args:
            target_date: 目标日期
            metric_type: 指标类型过滤
            force: 是否强制重新计算（即使已计算过）

        Returns:
            计算结果
        """
        logger.info(f"重新计算 {target_date} 的指标数据 (force={force})")

        # 清除旧的计算结果
        if force:
            self._clear_old_calculations(target_date, metric_type)

        # 执行计算
        return self.calculate_daily_metrics(target_date, metric_type)

    def _clear_old_calculations(
        self,
        target_date: date,
        metric_type: Optional[str] = None
    ):
        """
        清除旧的计算结果

        Args:
            target_date: 目标日期
            metric_type: 指标类型过滤
        """
        try:
            # 清除股票指标中的排名数据
            query = self.db.query(StockDailyMetrics).filter(
                StockDailyMetrics.trade_date == target_date
            )
            if metric_type:
                query = query.filter(StockDailyMetrics.metric_type == metric_type)

            metrics = query.all()
            for m in metrics:
                m.ranking_in_concept = 0
                m.percentage_in_concept = 0
                m.is_recalculated = True
                self.db.add(m)

            # 清除概念汇总
            query = self.db.query(ConceptMetricsSummary).filter(
                ConceptMetricsSummary.trade_date == target_date
            )
            if metric_type:
                query = query.filter(ConceptMetricsSummary.metric_type == metric_type)

            self.db.query(ConceptMetricsSummary).filter(
                ConceptMetricsSummary.trade_date == target_date
            ).delete()

            self.db.flush()
            logger.info(f"已清除 {target_date} 的旧计算结果")

        except Exception as e:
            logger.error(f"清除旧计算结果失败: {str(e)}")
