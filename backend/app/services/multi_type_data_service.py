"""
多类型独立数据服务
每种导入类型都有独立的数据处理逻辑，复制TxtImportService的逻辑
"""

from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func, text
from app.models.multi_type_trading import (
    get_models_for_type, get_table_names_for_type, MULTI_TYPE_MODELS
)
from app.models.concept import Concept, StockConcept
from app.services.bulk_insert_optimizer import BulkInsertOptimizer
from datetime import datetime, date, timedelta
import logging
import time

logger = logging.getLogger(__name__)


class MultiTypeDataService:
    """多类型独立数据服务"""

    def __init__(self, db: Session, import_type: str):
        self.db = db
        self.import_type = import_type
        self.models = get_models_for_type(import_type)
        self.optimizer = BulkInsertOptimizer(db)

    def clear_daily_data(self, trading_date: date, keep_trading_data: bool = False):
        """清理指定日期的数据（只清理当前类型的数据）"""
        try:
            # 清理汇总数据
            self.db.query(self.models['concept_daily_summary']).filter(
                self.models['concept_daily_summary'].trading_date == trading_date
            ).delete()

            # 清理排名数据
            self.db.query(self.models['stock_concept_ranking']).filter(
                self.models['stock_concept_ranking'].trading_date == trading_date
            ).delete()

            # 清理创新高数据
            self.db.query(self.models['concept_high_record']).filter(
                self.models['concept_high_record'].trading_date == trading_date
            ).delete()

            # 根据参数决定是否清理基础交易数据
            if not keep_trading_data:
                self.db.query(self.models['daily_trading']).filter(
                    self.models['daily_trading'].trading_date == trading_date
                ).delete()

            self.db.commit()
            logger.info(f"已清理{self.import_type}类型{trading_date}的{'汇总' if keep_trading_data else '所有'}数据")

        except Exception as e:
            logger.error(f"清理{self.import_type}类型数据失败: {e}")
            self.db.rollback()
            raise

    def insert_daily_trading(self, trading_data: List[Dict]) -> int:
        """插入每日交易数据到当前类型的表"""
        count = 0
        try:
            for item in trading_data:
                trading_record = self.models['daily_trading'](
                    original_stock_code=item['original_stock_code'],
                    normalized_stock_code=item['normalized_stock_code'],
                    stock_code=item['stock_code'],
                    trading_date=item['trading_date'],
                    trading_volume=item['trading_volume']
                )
                self.db.add(trading_record)
                count += 1

            self.db.commit()
            logger.info(f"向{self.import_type}类型表插入{count}条交易数据")
            return count

        except Exception as e:
            logger.error(f"插入{self.import_type}类型交易数据失败: {e}")
            self.db.rollback()
            raise

    def perform_calculations(self, trading_date: date) -> Dict[str, int]:
        """执行概念计算（复制TxtImportService的逻辑）"""
        try:
            logger.info(f"开始执行{self.import_type}类型 {trading_date} 的概念计算")

            # 1. 计算概念汇总
            concept_summary_count = self._calculate_concept_summary(trading_date)

            # 2. 计算排名
            ranking_count = self._calculate_concept_ranking(trading_date)

            # 3. 计算创新高
            new_high_count = self._calculate_concept_high_records(trading_date)

            logger.info(f"完成{self.import_type}类型概念计算: 汇总{concept_summary_count}, 排名{ranking_count}, 新高{new_high_count}")

            return {
                'concept_summary_count': concept_summary_count,
                'ranking_count': ranking_count,
                'new_high_count': new_high_count
            }

        except Exception as e:
            logger.error(f"{self.import_type}类型概念计算失败: {e}")
            raise

    def _calculate_concept_summary(self, trading_date: date) -> int:
        """计算概念汇总"""
        try:
            # 获取当日所有交易数据按概念分组
            sql = f"""
            SELECT
                stc.concept_id,
                c.concept_name,
                SUM(dt.trading_volume) as total_volume,
                COUNT(DISTINCT dt.stock_code) as stock_count,
                AVG(dt.trading_volume) as average_volume,
                MAX(dt.trading_volume) as max_volume
            FROM {self.models['daily_trading'].__tablename__} dt
            JOIN stocks s ON dt.stock_code = s.stock_code
            JOIN stock_concepts stc ON s.id = stc.stock_id
            JOIN concepts c ON stc.concept_id = c.id
            WHERE dt.trading_date = :trading_date
            GROUP BY stc.concept_id, c.concept_name
            """

            results = self.db.execute(text(sql), {"trading_date": trading_date}).fetchall()

            # 批量插入概念汇总数据
            summary_records = []
            for row in results:
                summary_record = self.models['concept_daily_summary'](
                    concept_name=row.concept_name,
                    trading_date=trading_date,
                    total_volume=int(row.total_volume),
                    stock_count=int(row.stock_count),
                    average_volume=float(row.average_volume),
                    max_volume=int(row.max_volume)
                )
                summary_records.append(summary_record)

            if summary_records:
                self.db.add_all(summary_records)
                self.db.commit()

            logger.info(f"{self.import_type}类型概念汇总计算完成: {len(summary_records)}个概念")
            return len(summary_records)

        except Exception as e:
            logger.error(f"{self.import_type}类型概念汇总计算失败: {e}")
            raise

    def _calculate_concept_ranking(self, trading_date: date) -> int:
        """计算概念排名"""
        try:
            # 获取概念汇总数据来计算排名
            summaries = self.db.query(self.models['concept_daily_summary']).filter(
                self.models['concept_daily_summary'].trading_date == trading_date
            ).all()

            ranking_records = []

            for summary in summaries:
                # 获取该概念下的所有股票交易数据
                sql = f"""
                SELECT dt.stock_code, dt.trading_volume, stc.concept_id, c.concept_name
                FROM {self.models['daily_trading'].__tablename__} dt
                JOIN stocks s ON dt.stock_code = s.stock_code
                JOIN stock_concepts stc ON s.id = stc.stock_id
                JOIN concepts c ON stc.concept_id = c.id
                WHERE dt.trading_date = :trading_date
                AND c.concept_name = :concept_name
                ORDER BY dt.trading_volume DESC
                """

                concept_stocks = self.db.execute(text(sql), {
                    "trading_date": trading_date,
                    "concept_name": summary.concept_name
                }).fetchall()

                # 计算排名
                for rank, stock in enumerate(concept_stocks, 1):
                    volume_percentage = (stock.trading_volume / summary.total_volume) * 100 if summary.total_volume > 0 else 0

                    ranking_record = self.models['stock_concept_ranking'](
                        stock_code=stock.stock_code,
                        concept_name=summary.concept_name,
                        trading_date=trading_date,
                        trading_volume=stock.trading_volume,
                        concept_rank=rank,
                        concept_total_volume=summary.total_volume,
                        volume_percentage=volume_percentage
                    )
                    ranking_records.append(ranking_record)

            if ranking_records:
                self.db.add_all(ranking_records)
                self.db.commit()

            logger.info(f"{self.import_type}类型排名计算完成: {len(ranking_records)}条记录")
            return len(ranking_records)

        except Exception as e:
            logger.error(f"{self.import_type}类型排名计算失败: {e}")
            raise

    def _calculate_concept_high_records(self, trading_date: date) -> int:
        """计算概念创新高记录"""
        try:
            new_high_records = []
            periods = [5, 10, 20, 60]  # 统计周期

            # 获取当日的概念汇总
            current_summaries = self.db.query(self.models['concept_daily_summary']).filter(
                self.models['concept_daily_summary'].trading_date == trading_date
            ).all()

            for summary in current_summaries:
                for period in periods:
                    # 计算过去period天的最大值
                    start_date = trading_date - timedelta(days=period)

                    max_volume = self.db.query(
                        func.max(self.models['concept_daily_summary'].total_volume)
                    ).filter(
                        and_(
                            self.models['concept_daily_summary'].concept_name == summary.concept_name,
                            self.models['concept_daily_summary'].trading_date >= start_date,
                            self.models['concept_daily_summary'].trading_date < trading_date
                        )
                    ).scalar()

                    # 如果当日交易量创新高
                    if max_volume is None or summary.total_volume > max_volume:
                        high_record = self.models['concept_high_record'](
                            concept_name=summary.concept_name,
                            trading_date=trading_date,
                            total_volume=summary.total_volume,
                            days_period=period,
                            is_active=True
                        )
                        new_high_records.append(high_record)

            if new_high_records:
                self.db.add_all(new_high_records)
                self.db.commit()

            logger.info(f"{self.import_type}类型创新高计算完成: {len(new_high_records)}条记录")
            return len(new_high_records)

        except Exception as e:
            logger.error(f"{self.import_type}类型创新高计算失败: {e}")
            raise

    def get_trading_data_count(self, trading_date: date) -> int:
        """获取指定日期的交易数据条数"""
        try:
            count = self.db.query(self.models['daily_trading']).filter(
                self.models['daily_trading'].trading_date == trading_date
            ).count()
            return count
        except Exception as e:
            logger.error(f"获取{self.import_type}类型交易数据条数失败: {e}")
            return 0

    def get_concept_summary_data(self, trading_date: date, limit: int = 50):
        """获取概念汇总数据"""
        try:
            summaries = self.db.query(self.models['concept_daily_summary']).filter(
                self.models['concept_daily_summary'].trading_date == trading_date
            ).order_by(desc(self.models['concept_daily_summary'].total_volume)).limit(limit).all()

            return [{
                'concept_name': s.concept_name,
                'total_volume': s.total_volume,
                'stock_count': s.stock_count,
                'average_volume': s.average_volume,
                'max_volume': s.max_volume
            } for s in summaries]
        except Exception as e:
            logger.error(f"获取{self.import_type}类型概念汇总数据失败: {e}")
            return []

    def get_concept_rankings(self, trading_date: date, concept_name: str = None, limit: int = 50):
        """获取概念排名数据"""
        try:
            query = self.db.query(self.models['stock_concept_ranking']).filter(
                self.models['stock_concept_ranking'].trading_date == trading_date
            )

            if concept_name:
                query = query.filter(self.models['stock_concept_ranking'].concept_name == concept_name)

            rankings = query.order_by(
                self.models['stock_concept_ranking'].concept_name,
                self.models['stock_concept_ranking'].concept_rank
            ).limit(limit).all()

            return [{
                'stock_code': r.stock_code,
                'concept_name': r.concept_name,
                'trading_volume': r.trading_volume,
                'concept_rank': r.concept_rank,
                'volume_percentage': r.volume_percentage
            } for r in rankings]
        except Exception as e:
            logger.error(f"获取{self.import_type}类型概念排名数据失败: {e}")
            return []