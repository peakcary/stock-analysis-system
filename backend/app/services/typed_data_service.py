"""
类型化数据服务
使用type1、type2、type3等简洁命名的数据处理服务
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_, text
from app.models.typed_trading import get_models_for_type, TYPED_MODELS
from datetime import date, datetime
import logging

logger = logging.getLogger(__name__)


class TypedDataService:
    """类型化数据服务"""

    def __init__(self, db: Session, import_type: str):
        """
        初始化数据服务

        Args:
            db: 数据库会话
            import_type: 导入类型 (type1, type2, type3 等)
        """
        self.db = db
        self.import_type = import_type

        # 验证类型是否支持
        if import_type not in TYPED_MODELS:
            raise ValueError(f"不支持的导入类型: {import_type}, 支持的类型: {list(TYPED_MODELS.keys())}")

        # 获取对应的模型类
        self.models = get_models_for_type(import_type)
        self.daily_trading_model = self.models['daily_trading']
        self.concept_summary_model = self.models['concept_daily_summary']
        self.stock_ranking_model = self.models['stock_concept_ranking']
        self.concept_high_model = self.models['concept_high_record']

    def check_existing_data(self, trading_date: date) -> int:
        """检查指定日期是否已有数据"""
        try:
            count = self.db.query(self.daily_trading_model).filter(
                self.daily_trading_model.trading_date == trading_date
            ).count()
            return count
        except Exception as e:
            logger.error(f"检查{self.import_type}类型{trading_date}数据时出错: {e}")
            return 0

    def clear_daily_data(self, trading_date: date) -> None:
        """清除指定日期的所有数据"""
        try:
            # 按依赖关系倒序删除
            tables_to_clear = [
                self.concept_summary_model,
                self.stock_ranking_model,
                self.concept_high_model,
                self.daily_trading_model
            ]

            for model in tables_to_clear:
                self.db.query(model).filter(
                    model.trading_date == trading_date
                ).delete()

            self.db.commit()
            logger.info(f"已清理{self.import_type}类型{trading_date}的所有数据")

        except Exception as e:
            self.db.rollback()
            logger.error(f"{self.import_type}类型数据清理失败: {e}")
            raise

    def insert_daily_trading(self, trading_data: List[Dict]) -> int:
        """批量插入每日交易数据"""
        try:
            insert_count = 0
            for data in trading_data:
                trading_record = self.daily_trading_model(
                    original_stock_code=data['original_stock_code'],
                    normalized_stock_code=data['normalized_stock_code'],
                    stock_code=data['stock_code'],
                    trading_date=data['trading_date'],
                    trading_volume=data['trading_volume'],
                    created_at=datetime.utcnow()
                )
                self.db.add(trading_record)
                insert_count += 1

            self.db.commit()
            logger.info(f"向{self.import_type}类型表插入{insert_count}条交易数据")
            return insert_count

        except Exception as e:
            self.db.rollback()
            logger.error(f"{self.import_type}类型交易数据插入失败: {e}")
            raise

    def perform_calculations(self, trading_date: date) -> Dict[str, Any]:
        """执行概念计算和排名统计"""
        try:
            logger.info(f"开始执行{self.import_type}类型 {trading_date} 的概念计算")

            # 1. 概念汇总计算
            concept_stats = self._calculate_concept_summary(trading_date)

            # 2. 股票概念排名计算
            ranking_stats = self._calculate_stock_ranking(trading_date)

            # 3. 概念创新高计算
            high_records = self._calculate_concept_highs(trading_date)

            results = {
                'concept_summaries': concept_stats,
                'stock_rankings': ranking_stats,
                'high_records': high_records
            }

            logger.info(f"{self.import_type}类型概念计算完成")
            return results

        except Exception as e:
            logger.error(f"{self.import_type}类型概念计算失败: {e}")
            raise

    def _calculate_concept_summary(self, trading_date: date) -> int:
        """计算概念每日汇总"""
        try:
            # 使用SQL查询聚合概念数据
            query = text(f"""
            SELECT
                sc.concept_id,
                c.concept_name,
                SUM(dt.trading_volume) as total_volume,
                COUNT(DISTINCT dt.stock_code) as stock_count,
                AVG(dt.trading_volume) as average_volume,
                MAX(dt.trading_volume) as max_volume
            FROM {self.daily_trading_model.__tablename__} dt
            JOIN stock_concepts sc ON dt.stock_code = sc.stock_code
            JOIN concepts c ON sc.concept_id = c.id
            WHERE dt.trading_date = :trading_date
            GROUP BY sc.concept_id, c.concept_name
            """)

            result = self.db.execute(query, {'trading_date': trading_date})
            concept_data = result.fetchall()

            # 插入概念汇总数据
            insert_count = 0
            for row in concept_data:
                summary = self.concept_summary_model(
                    concept_name=row.concept_name,
                    trading_date=trading_date,
                    total_volume=int(row.total_volume),
                    stock_count=int(row.stock_count),
                    average_volume=float(row.average_volume),
                    max_volume=int(row.max_volume),
                    created_at=datetime.utcnow()
                )
                self.db.add(summary)
                insert_count += 1

            self.db.commit()
            logger.info(f"{self.import_type}类型概念汇总: {insert_count}条")
            return insert_count

        except Exception as e:
            self.db.rollback()
            logger.error(f"{self.import_type}类型概念汇总计算失败: {e}")
            return 0

    def _calculate_stock_ranking(self, trading_date: date) -> int:
        """计算股票在概念中的排名"""
        try:
            # 查询每个概念的股票排名
            query = text(f"""
            SELECT
                dt.stock_code,
                c.concept_name,
                dt.trading_volume,
                cs.total_volume as concept_total_volume,
                RANK() OVER (PARTITION BY c.concept_name ORDER BY dt.trading_volume DESC) as concept_rank,
                (dt.trading_volume * 100.0 / cs.total_volume) as volume_percentage
            FROM {self.daily_trading_model.__tablename__} dt
            JOIN stock_concepts sc ON dt.stock_code = sc.stock_code
            JOIN concepts c ON sc.concept_id = c.id
            JOIN {self.concept_summary_model.__tablename__} cs ON c.concept_name = cs.concept_name AND cs.trading_date = :trading_date
            WHERE dt.trading_date = :trading_date
            ORDER BY c.concept_name, concept_rank
            """)

            result = self.db.execute(query, {'trading_date': trading_date})
            ranking_data = result.fetchall()

            # 插入排名数据
            insert_count = 0
            for row in ranking_data:
                ranking = self.stock_ranking_model(
                    stock_code=row.stock_code,
                    concept_name=row.concept_name,
                    trading_date=trading_date,
                    trading_volume=int(row.trading_volume),
                    concept_rank=int(row.concept_rank),
                    concept_total_volume=int(row.concept_total_volume),
                    volume_percentage=float(row.volume_percentage),
                    created_at=datetime.utcnow()
                )
                self.db.add(ranking)
                insert_count += 1

            self.db.commit()
            logger.info(f"{self.import_type}类型股票排名: {insert_count}条")
            return insert_count

        except Exception as e:
            self.db.rollback()
            logger.error(f"{self.import_type}类型股票排名计算失败: {e}")
            return 0

    def _calculate_concept_highs(self, trading_date: date) -> int:
        """计算概念创新高记录"""
        try:
            # 检查各个周期的创新高
            periods = [5, 10, 20, 60]
            insert_count = 0

            for days in periods:
                # 查找在指定周期内创新高的概念
                query = text(f"""
                SELECT
                    cs.concept_name,
                    cs.total_volume,
                    {days} as days_period
                FROM {self.concept_summary_model.__tablename__} cs
                WHERE cs.trading_date = :trading_date
                AND cs.total_volume > COALESCE((
                    SELECT MAX(cs2.total_volume)
                    FROM {self.concept_summary_model.__tablename__} cs2
                    WHERE cs2.concept_name = cs.concept_name
                    AND cs2.trading_date < :trading_date
                    AND cs2.trading_date >= DATE_SUB(:trading_date, INTERVAL {days} DAY)
                ), 0)
                """)

                result = self.db.execute(query, {'trading_date': trading_date})
                high_data = result.fetchall()

                # 插入创新高记录
                for row in high_data:
                    high_record = self.concept_high_model(
                        concept_name=row.concept_name,
                        trading_date=trading_date,
                        total_volume=int(row.total_volume),
                        days_period=int(row.days_period),
                        is_active=True,
                        created_at=datetime.utcnow()
                    )
                    self.db.add(high_record)
                    insert_count += 1

            self.db.commit()
            logger.info(f"{self.import_type}类型创新高记录: {insert_count}条")
            return insert_count

        except Exception as e:
            self.db.rollback()
            logger.error(f"{self.import_type}类型创新高计算失败: {e}")
            return 0

    def get_data_stats(self, trading_date: Optional[date] = None) -> Dict[str, Any]:
        """获取数据统计信息"""
        try:
            stats = {}

            # 基础数据统计
            query = self.db.query(self.daily_trading_model)
            if trading_date:
                query = query.filter(self.daily_trading_model.trading_date == trading_date)

            stats['total_records'] = query.count()
            stats['trading_dates'] = self.db.query(
                func.distinct(self.daily_trading_model.trading_date)
            ).count()

            # 概念统计
            concept_query = self.db.query(self.concept_summary_model)
            if trading_date:
                concept_query = concept_query.filter(
                    self.concept_summary_model.trading_date == trading_date
                )

            stats['concept_count'] = concept_query.count()

            # 最新数据日期
            latest_date = self.db.query(
                func.max(self.daily_trading_model.trading_date)
            ).scalar()
            stats['latest_date'] = latest_date.isoformat() if latest_date else None

            return stats

        except Exception as e:
            logger.error(f"{self.import_type}类型统计查询失败: {e}")
            return {}

    def validate_data_integrity(self, trading_date: date) -> Dict[str, Any]:
        """验证数据完整性"""
        try:
            # 检查各表数据一致性
            daily_count = self.db.query(self.daily_trading_model).filter(
                self.daily_trading_model.trading_date == trading_date
            ).count()

            concept_count = self.db.query(self.concept_summary_model).filter(
                self.concept_summary_model.trading_date == trading_date
            ).count()

            ranking_count = self.db.query(self.stock_ranking_model).filter(
                self.stock_ranking_model.trading_date == trading_date
            ).count()

            high_count = self.db.query(self.concept_high_model).filter(
                self.concept_high_model.trading_date == trading_date
            ).count()

            return {
                'type': self.import_type,
                'trading_date': trading_date.isoformat(),
                'daily_trading_records': daily_count,
                'concept_summaries': concept_count,
                'stock_rankings': ranking_count,
                'high_records': high_count,
                'data_complete': daily_count > 0 and concept_count > 0
            }

        except Exception as e:
            logger.error(f"{self.import_type}类型数据完整性检查失败: {e}")
            return {'error': str(e)}