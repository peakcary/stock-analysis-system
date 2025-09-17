from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.daily_trading import DailyTrading, ConceptDailySummary, StockConceptRanking, ConceptHighRecord
import logging
from contextlib import contextmanager
import time

logger = logging.getLogger(__name__)

class BulkInsertOptimizer:
    """数据库批量插入优化器"""

    def __init__(self, db: Session):
        self.db = db
        self.batch_size = 1000  # 每批次插入的记录数

    @contextmanager
    def optimized_session(self):
        """优化的数据库会话上下文管理器"""
        try:
            # 开始事务
            self.db.execute(text("SET autocommit = 0"))

            # 优化MySQL设置（仅在批量操作时使用）
            self.db.execute(text("SET unique_checks = 0"))
            self.db.execute(text("SET foreign_key_checks = 0"))
            self.db.execute(text("SET sql_log_bin = 0"))

            yield self.db

            # 提交事务
            self.db.commit()

        except Exception as e:
            self.db.rollback()
            logger.error(f"批量操作失败: {e}")
            raise
        finally:
            # 恢复MySQL设置
            try:
                self.db.execute(text("SET unique_checks = 1"))
                self.db.execute(text("SET foreign_key_checks = 1"))
                self.db.execute(text("SET sql_log_bin = 1"))
                self.db.execute(text("SET autocommit = 1"))
            except Exception as e:
                logger.warning(f"恢复数据库设置时出错: {e}")

    def bulk_insert_daily_trading(self, trading_data: List[Dict]) -> int:
        """优化的每日交易数据批量插入"""
        if not trading_data:
            return 0

        total_inserted = 0
        start_time = time.time()

        try:
            with self.optimized_session():
                # 分批插入
                for i in range(0, len(trading_data), self.batch_size):
                    batch = trading_data[i:i + self.batch_size]

                    # 构建批量插入SQL
                    values = []
                    for item in batch:
                        values.append(
                            f"('{item['original_stock_code']}', '{item['normalized_stock_code']}', "
                            f"'{item['stock_code']}', '{item['trading_date']}', {item['trading_volume']}, NOW())"
                        )

                    sql = f"""
                    INSERT INTO daily_trading
                    (original_stock_code, normalized_stock_code, stock_code, trading_date, trading_volume, created_at)
                    VALUES {','.join(values)}
                    """

                    self.db.execute(text(sql))
                    total_inserted += len(batch)

                    logger.debug(f"批量插入交易数据: {len(batch)} 条 (总共: {total_inserted})")

            end_time = time.time()
            logger.info(f"批量插入 {total_inserted} 条交易数据完成，耗时: {end_time - start_time:.2f} 秒")

            return total_inserted

        except Exception as e:
            logger.error(f"批量插入交易数据失败: {e}")
            raise

    def bulk_insert_concept_summaries(self, summaries: List[ConceptDailySummary]) -> int:
        """优化的概念汇总数据批量插入"""
        if not summaries:
            return 0

        total_inserted = 0
        start_time = time.time()

        try:
            with self.optimized_session():
                # 分批插入
                for i in range(0, len(summaries), self.batch_size):
                    batch = summaries[i:i + self.batch_size]

                    # 构建批量插入SQL
                    values = []
                    for summary in batch:
                        values.append(
                            f"('{summary.concept_name}', '{summary.trading_date}', "
                            f"{summary.total_volume}, {summary.stock_count}, "
                            f"{summary.average_volume}, {summary.max_volume}, NOW())"
                        )

                    sql = f"""
                    INSERT INTO concept_daily_summary
                    (concept_name, trading_date, total_volume, stock_count, average_volume, max_volume, created_at)
                    VALUES {','.join(values)}
                    """

                    self.db.execute(text(sql))
                    total_inserted += len(batch)

            end_time = time.time()
            logger.info(f"批量插入 {total_inserted} 条概念汇总数据完成，耗时: {end_time - start_time:.2f} 秒")

            return total_inserted

        except Exception as e:
            logger.error(f"批量插入概念汇总数据失败: {e}")
            raise

    def bulk_insert_rankings(self, rankings: List[StockConceptRanking]) -> int:
        """优化的排名数据批量插入"""
        if not rankings:
            return 0

        total_inserted = 0
        start_time = time.time()

        try:
            with self.optimized_session():
                # 分批插入
                for i in range(0, len(rankings), self.batch_size):
                    batch = rankings[i:i + self.batch_size]

                    # 构建批量插入SQL
                    values = []
                    for ranking in batch:
                        values.append(
                            f"('{ranking.stock_code}', '{ranking.concept_name}', "
                            f"'{ranking.trading_date}', {ranking.trading_volume}, "
                            f"{ranking.concept_rank}, {ranking.concept_total_volume}, "
                            f"{ranking.volume_percentage}, NOW())"
                        )

                    sql = f"""
                    INSERT INTO stock_concept_ranking
                    (stock_code, concept_name, trading_date, trading_volume,
                     concept_rank, concept_total_volume, volume_percentage, created_at)
                    VALUES {','.join(values)}
                    """

                    self.db.execute(text(sql))
                    total_inserted += len(batch)

            end_time = time.time()
            logger.info(f"批量插入 {total_inserted} 条排名数据完成，耗时: {end_time - start_time:.2f} 秒")

            return total_inserted

        except Exception as e:
            logger.error(f"批量插入排名数据失败: {e}")
            raise

    def bulk_insert_high_records(self, high_records: List[ConceptHighRecord]) -> int:
        """优化的创新高记录批量插入"""
        if not high_records:
            return 0

        total_inserted = 0
        start_time = time.time()

        try:
            with self.optimized_session():
                # 分批插入
                for i in range(0, len(high_records), self.batch_size):
                    batch = high_records[i:i + self.batch_size]

                    # 构建批量插入SQL
                    values = []
                    for record in batch:
                        is_active = 1 if record.is_active else 0
                        values.append(
                            f"('{record.concept_name}', '{record.trading_date}', "
                            f"{record.total_volume}, {record.days_period}, {is_active}, NOW())"
                        )

                    sql = f"""
                    INSERT INTO concept_high_record
                    (concept_name, trading_date, total_volume, days_period, is_active, created_at)
                    VALUES {','.join(values)}
                    """

                    self.db.execute(text(sql))
                    total_inserted += len(batch)

            end_time = time.time()
            logger.info(f"批量插入 {total_inserted} 条创新高记录完成，耗时: {end_time - start_time:.2f} 秒")

            return total_inserted

        except Exception as e:
            logger.error(f"批量插入创新高记录失败: {e}")
            raise

    def bulk_delete_by_date(self, table_name: str, trading_date) -> int:
        """优化的按日期批量删除"""
        try:
            with self.optimized_session():
                sql = f"DELETE FROM {table_name} WHERE trading_date = :trading_date"
                result = self.db.execute(text(sql), {"trading_date": trading_date})
                deleted_count = result.rowcount

                logger.info(f"从 {table_name} 删除 {trading_date} 的数据: {deleted_count} 条")
                return deleted_count

        except Exception as e:
            logger.error(f"批量删除 {table_name} 数据失败: {e}")
            raise

    def vacuum_tables(self, table_names: List[str]):
        """优化表空间（仅MySQL 8.0+支持）"""
        try:
            for table_name in table_names:
                try:
                    sql = f"OPTIMIZE TABLE {table_name}"
                    self.db.execute(text(sql))
                    logger.info(f"已优化表: {table_name}")
                except Exception as e:
                    logger.warning(f"优化表 {table_name} 失败: {e}")

        except Exception as e:
            logger.error(f"表空间优化失败: {e}")

    def get_table_stats(self, table_name: str) -> Dict[str, Any]:
        """获取表统计信息"""
        try:
            sql = f"""
            SELECT
                TABLE_ROWS as row_count,
                DATA_LENGTH as data_size,
                INDEX_LENGTH as index_size,
                (DATA_LENGTH + INDEX_LENGTH) as total_size
            FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :table_name
            """

            result = self.db.execute(text(sql), {"table_name": table_name}).fetchone()

            if result:
                return {
                    "table_name": table_name,
                    "row_count": result.row_count or 0,
                    "data_size_mb": round((result.data_size or 0) / 1024 / 1024, 2),
                    "index_size_mb": round((result.index_size or 0) / 1024 / 1024, 2),
                    "total_size_mb": round((result.total_size or 0) / 1024 / 1024, 2)
                }
            else:
                return {"table_name": table_name, "error": "Table not found"}

        except Exception as e:
            logger.error(f"获取表 {table_name} 统计信息失败: {e}")
            return {"table_name": table_name, "error": str(e)}

    def analyze_tables(self, table_names: List[str]):
        """分析表以更新统计信息"""
        try:
            for table_name in table_names:
                try:
                    sql = f"ANALYZE TABLE {table_name}"
                    self.db.execute(text(sql))
                    logger.info(f"已分析表: {table_name}")
                except Exception as e:
                    logger.warning(f"分析表 {table_name} 失败: {e}")

        except Exception as e:
            logger.error(f"表分析失败: {e}")


class OptimizedTxtImportService:
    """使用优化器的TXT导入服务"""

    def __init__(self, db: Session):
        self.db = db
        self.optimizer = BulkInsertOptimizer(db)

    def optimized_insert_daily_trading(self, trading_data: List[Dict]) -> int:
        """使用优化器插入交易数据"""
        return self.optimizer.bulk_insert_daily_trading(trading_data)

    def optimized_clear_daily_data(self, trading_date):
        """使用优化器清理日期数据"""
        tables = [
            "concept_daily_summary",
            "stock_concept_ranking",
            "concept_high_record",
            "daily_trading"
        ]

        total_deleted = 0
        for table in tables:
            deleted = self.optimizer.bulk_delete_by_date(table, trading_date)
            total_deleted += deleted

        return total_deleted

    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        tables = [
            "daily_trading",
            "concept_daily_summary",
            "stock_concept_ranking",
            "concept_high_record"
        ]

        stats = {}
        for table in tables:
            stats[table] = self.optimizer.get_table_stats(table)

        return stats