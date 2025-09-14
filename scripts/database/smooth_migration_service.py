#!/usr/bin/env python3
"""
平滑迁移服务 - 零停机数据库优化迁移
支持双写模式和渐进式切换
v2.6.4 - 2025-09-13
"""

import os
import sys
import time
import json
import logging
from datetime import date, datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent.parent))

from sqlalchemy import create_engine, text, func, desc
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

# 导入新优化模型
from backend.app.models.optimized_trading import (
    DailyTradingUnified,
    ConceptDailyMetrics,
    StockConceptDailySnapshot,
    TodayTradingCache,
    TxtImportProcessingLog
)

# 导入原有模型
from backend.app.models.daily_trading import DailyTrading, ConceptDailySummary, StockConceptRanking

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class MigrationProgress:
    """迁移进度跟踪"""
    total_records: int = 0
    processed_records: int = 0
    error_records: int = 0
    start_time: datetime = None
    current_table: str = ""
    status: str = "pending"  # pending, running, completed, failed
    
    @property
    def progress_percent(self) -> float:
        if self.total_records == 0:
            return 0.0
        return (self.processed_records / self.total_records) * 100
    
    @property
    def elapsed_time(self) -> float:
        if not self.start_time:
            return 0.0
        return (datetime.now() - self.start_time).total_seconds()
    
    @property
    def records_per_second(self) -> float:
        if self.elapsed_time == 0:
            return 0.0
        return self.processed_records / self.elapsed_time


class SmoothMigrationService:
    """平滑迁移服务"""
    
    def __init__(self, database_url: str, batch_size: int = 1000):
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.batch_size = batch_size
        self.progress = MigrationProgress()
        
        # 迁移状态文件
        self.state_file = Path("migration_state.json")
        
    def save_migration_state(self):
        """保存迁移状态"""
        state = {
            "progress": {
                "total_records": self.progress.total_records,
                "processed_records": self.progress.processed_records,
                "error_records": self.progress.error_records,
                "current_table": self.progress.current_table,
                "status": self.progress.status,
                "start_time": self.progress.start_time.isoformat() if self.progress.start_time else None
            },
            "last_updated": datetime.now().isoformat()
        }
        
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def load_migration_state(self) -> bool:
        """加载迁移状态"""
        if not self.state_file.exists():
            return False
            
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
            
            progress_data = state.get("progress", {})
            self.progress.total_records = progress_data.get("total_records", 0)
            self.progress.processed_records = progress_data.get("processed_records", 0)
            self.progress.error_records = progress_data.get("error_records", 0)
            self.progress.current_table = progress_data.get("current_table", "")
            self.progress.status = progress_data.get("status", "pending")
            
            if progress_data.get("start_time"):
                self.progress.start_time = datetime.fromisoformat(progress_data["start_time"])
            
            logger.info(f"已加载迁移状态: {self.progress.status}, 进度: {self.progress.progress_percent:.1f}%")
            return True
            
        except Exception as e:
            logger.error(f"加载迁移状态失败: {e}")
            return False
    
    def verify_table_structure(self, db: Session) -> Dict[str, bool]:
        """验证表结构是否就绪"""
        tables_to_check = [
            'daily_trading_unified',
            'concept_daily_metrics', 
            'stock_concept_daily_snapshot',
            'today_trading_cache',
            'txt_import_processing_log'
        ]
        
        results = {}
        for table in tables_to_check:
            try:
                # 检查表是否存在且有正确结构
                result = db.execute(text(f"SHOW TABLES LIKE '{table}'")).fetchone()
                if result:
                    # 检查基本字段是否存在
                    columns = db.execute(text(f"SHOW COLUMNS FROM {table}")).fetchall()
                    column_names = [col[0] for col in columns]
                    
                    required_columns = {
                        'daily_trading_unified': ['stock_code', 'trading_date', 'trading_volume', 'concept_count', 'rank_in_date'],
                        'concept_daily_metrics': ['concept_name', 'trading_date', 'total_volume', 'volume_rank', 'is_new_high'],
                        'stock_concept_daily_snapshot': ['stock_code', 'concept_name', 'trading_date', 'concept_rank'],
                        'today_trading_cache': ['stock_code', 'trading_volume'],
                        'txt_import_processing_log': ['batch_id', 'trading_date', 'stage']
                    }
                    
                    required = required_columns.get(table, [])
                    has_required = all(col in column_names for col in required)
                    results[table] = has_required
                    
                    if has_required:
                        logger.info(f"✓ 表 {table} 结构验证通过")
                    else:
                        logger.error(f"✗ 表 {table} 缺少必要字段: {set(required) - set(column_names)}")
                else:
                    results[table] = False
                    logger.error(f"✗ 表 {table} 不存在")
                    
            except Exception as e:
                logger.error(f"检查表 {table} 时出错: {e}")
                results[table] = False
        
        return results
    
    def migrate_daily_trading_data(self, db: Session, start_date: Optional[date] = None, 
                                 end_date: Optional[date] = None) -> int:
        """迁移每日交易数据"""
        logger.info("开始迁移每日交易数据...")
        
        # 构建查询条件
        query = db.query(DailyTrading)
        if start_date:
            query = query.filter(DailyTrading.trading_date >= start_date)
        if end_date:
            query = query.filter(DailyTrading.trading_date <= end_date)
        
        # 获取总数
        total_count = query.count()
        logger.info(f"待迁移的每日交易记录数: {total_count}")
        
        if total_count == 0:
            return 0
        
        # 分批处理
        migrated_count = 0
        offset = 0
        
        while offset < total_count:
            try:
                # 获取一批数据
                batch_data = query.offset(offset).limit(self.batch_size).all()
                
                if not batch_data:
                    break
                
                # 预计算概念数量（使用子查询优化）
                stock_codes = [item.stock_code for item in batch_data]
                if stock_codes:
                    concept_counts = {}
                    for trading_date in set(item.trading_date for item in batch_data):
                        concept_count_query = db.query(
                            StockConceptRanking.stock_code,
                            func.count().label('concept_count')
                        ).filter(
                            StockConceptRanking.trading_date == trading_date,
                            StockConceptRanking.stock_code.in_(stock_codes)
                        ).group_by(StockConceptRanking.stock_code).all()
                        
                        for stock_code, count in concept_count_query:
                            concept_counts[f"{stock_code}_{trading_date}"] = count
                
                # 转换并插入新表
                new_records = []
                for old_record in batch_data:
                    concept_count = concept_counts.get(f"{old_record.stock_code}_{old_record.trading_date}", 0)
                    
                    new_record = DailyTradingUnified(
                        stock_code=old_record.stock_code,
                        stock_name=getattr(old_record, 'stock_name', f"股票{old_record.stock_code}"),
                        trading_date=old_record.trading_date,
                        trading_volume=old_record.trading_volume,
                        heat_value=getattr(old_record, 'heat_value', 0),
                        concept_count=concept_count,
                        rank_in_date=0,  # 后续批量计算
                        volume_rank_pct=0  # 后续批量计算
                    )
                    new_records.append(new_record)
                
                # 批量插入
                db.bulk_save_objects(new_records)
                db.commit()
                
                migrated_count += len(batch_data)
                offset += self.batch_size
                
                # 更新进度
                self.progress.processed_records = migrated_count
                self.save_migration_state()
                
                logger.info(f"已迁移每日交易数据: {migrated_count}/{total_count} ({migrated_count/total_count*100:.1f}%)")
                
            except Exception as e:
                logger.error(f"迁移每日交易数据批次失败: {e}")
                db.rollback()
                self.progress.error_records += len(batch_data) if 'batch_data' in locals() else 0
                offset += self.batch_size  # 跳过问题批次
        
        return migrated_count
    
    def migrate_concept_daily_data(self, db: Session, start_date: Optional[date] = None,
                                 end_date: Optional[date] = None) -> int:
        """迁移概念每日数据"""
        logger.info("开始迁移概念每日数据...")
        
        query = db.query(ConceptDailySummary)
        if start_date:
            query = query.filter(ConceptDailySummary.trading_date >= start_date)
        if end_date:
            query = query.filter(ConceptDailySummary.trading_date <= end_date)
        
        total_count = query.count()
        logger.info(f"待迁移的概念每日记录数: {total_count}")
        
        if total_count == 0:
            return 0
        
        migrated_count = 0
        offset = 0
        
        while offset < total_count:
            try:
                batch_data = query.offset(offset).limit(self.batch_size).all()
                
                if not batch_data:
                    break
                
                new_records = []
                for old_record in batch_data:
                    new_record = ConceptDailyMetrics(
                        concept_name=old_record.concept_name,
                        trading_date=old_record.trading_date,
                        total_volume=old_record.total_volume,
                        stock_count=old_record.stock_count,
                        avg_volume=old_record.average_volume,
                        max_volume=old_record.max_volume,
                        min_volume=getattr(old_record, 'min_volume', 0),
                        volume_rank=0,  # 后续批量计算
                        stock_count_rank=0,  # 后续批量计算
                        is_new_high=False,  # 后续分析计算
                        new_high_days=0,
                        volume_change_pct=0,  # 后续计算
                        prev_day_volume=0
                    )
                    new_records.append(new_record)
                
                db.bulk_save_objects(new_records)
                db.commit()
                
                migrated_count += len(batch_data)
                offset += self.batch_size
                
                self.progress.processed_records += len(batch_data)
                self.save_migration_state()
                
                logger.info(f"已迁移概念每日数据: {migrated_count}/{total_count} ({migrated_count/total_count*100:.1f}%)")
                
            except Exception as e:
                logger.error(f"迁移概念每日数据批次失败: {e}")
                db.rollback()
                self.progress.error_records += len(batch_data) if 'batch_data' in locals() else 0
                offset += self.batch_size
        
        return migrated_count
    
    def migrate_stock_concept_ranking_data(self, db: Session, start_date: Optional[date] = None,
                                         end_date: Optional[date] = None) -> int:
        """迁移股票概念排名数据"""
        logger.info("开始迁移股票概念排名数据...")
        
        query = db.query(StockConceptRanking)
        if start_date:
            query = query.filter(StockConceptRanking.trading_date >= start_date)
        if end_date:
            query = query.filter(StockConceptRanking.trading_date <= end_date)
        
        total_count = query.count()
        logger.info(f"待迁移的股票概念排名记录数: {total_count}")
        
        if total_count == 0:
            return 0
        
        migrated_count = 0
        offset = 0
        
        while offset < total_count:
            try:
                batch_data = query.offset(offset).limit(self.batch_size).all()
                
                if not batch_data:
                    break
                
                new_records = []
                for old_record in batch_data:
                    new_record = StockConceptDailySnapshot(
                        stock_code=old_record.stock_code,
                        concept_name=old_record.concept_name,
                        trading_date=old_record.trading_date,
                        trading_volume=old_record.trading_volume,
                        concept_rank=old_record.concept_rank,
                        volume_percentage=old_record.volume_percentage,
                        concept_total_volume=old_record.concept_total_volume,
                        concept_stock_count=0  # 后续补充计算
                    )
                    new_records.append(new_record)
                
                db.bulk_save_objects(new_records)
                db.commit()
                
                migrated_count += len(batch_data)
                offset += self.batch_size
                
                self.progress.processed_records += len(batch_data)
                self.save_migration_state()
                
                logger.info(f"已迁移股票概念排名数据: {migrated_count}/{total_count} ({migrated_count/total_count*100:.1f}%)")
                
            except Exception as e:
                logger.error(f"迁移股票概念排名数据批次失败: {e}")
                db.rollback()
                self.progress.error_records += len(batch_data) if 'batch_data' in locals() else 0
                offset += self.batch_size
        
        return migrated_count
    
    def calculate_rankings_and_metrics(self, db: Session, trading_date: date):
        """计算排名和指标"""
        logger.info(f"计算 {trading_date} 的排名和指标...")
        
        try:
            # 1. 计算股票当日排名
            db.execute(text("""
                UPDATE daily_trading_unified 
                SET rank_in_date = (
                    SELECT rank_num FROM (
                        SELECT stock_code, 
                               ROW_NUMBER() OVER (ORDER BY trading_volume DESC) as rank_num
                        FROM daily_trading_unified 
                        WHERE trading_date = :trading_date
                    ) ranked 
                    WHERE ranked.stock_code = daily_trading_unified.stock_code
                ) 
                WHERE trading_date = :trading_date
            """), {"trading_date": trading_date})
            
            # 2. 计算概念排名
            db.execute(text("""
                UPDATE concept_daily_metrics 
                SET volume_rank = (
                    SELECT rank_num FROM (
                        SELECT concept_name,
                               ROW_NUMBER() OVER (ORDER BY total_volume DESC) as rank_num
                        FROM concept_daily_metrics 
                        WHERE trading_date = :trading_date
                    ) ranked 
                    WHERE ranked.concept_name = concept_daily_metrics.concept_name
                ) 
                WHERE trading_date = :trading_date
            """), {"trading_date": trading_date})
            
            # 3. 更新概念股票数量
            db.execute(text("""
                UPDATE stock_concept_daily_snapshot s
                SET concept_stock_count = (
                    SELECT COUNT(*) 
                    FROM stock_concept_daily_snapshot s2 
                    WHERE s2.concept_name = s.concept_name 
                      AND s2.trading_date = s.trading_date
                )
                WHERE trading_date = :trading_date
            """), {"trading_date": trading_date})
            
            db.commit()
            logger.info(f"完成 {trading_date} 排名和指标计算")
            
        except Exception as e:
            logger.error(f"计算排名和指标失败: {e}")
            db.rollback()
            raise
    
    def create_today_cache(self, db: Session, trading_date: date):
        """创建当天缓存数据"""
        if trading_date != date.today():
            return
            
        logger.info("创建当天缓存数据...")
        
        try:
            # 清空现有缓存
            db.execute(text("TRUNCATE TABLE today_trading_cache"))
            
            # 插入当天数据到缓存表
            db.execute(text("""
                INSERT INTO today_trading_cache (
                    stock_code, stock_name, trading_volume, concept_count, rank_in_date
                )
                SELECT stock_code, stock_name, trading_volume, concept_count, rank_in_date
                FROM daily_trading_unified 
                WHERE trading_date = :trading_date
            """), {"trading_date": trading_date})
            
            db.commit()
            logger.info("当天缓存数据创建完成")
            
        except Exception as e:
            logger.error(f"创建当天缓存失败: {e}")
            db.rollback()
    
    def run_full_migration(self, start_date: Optional[date] = None, 
                          end_date: Optional[date] = None) -> bool:
        """运行完整迁移"""
        self.progress.start_time = datetime.now()
        self.progress.status = "running"
        self.save_migration_state()
        
        try:
            with self.SessionLocal() as db:
                # 1. 验证表结构
                logger.info("步骤 1/6: 验证表结构...")
                table_status = self.verify_table_structure(db)
                if not all(table_status.values()):
                    logger.error("表结构验证失败，请先运行 create_optimized_tables.sql")
                    self.progress.status = "failed"
                    self.save_migration_state()
                    return False
                
                # 2. 计算总工作量
                logger.info("步骤 2/6: 计算迁移工作量...")
                daily_count = db.query(DailyTrading).count()
                concept_count = db.query(ConceptDailySummary).count() 
                ranking_count = db.query(StockConceptRanking).count()
                
                self.progress.total_records = daily_count + concept_count + ranking_count
                logger.info(f"总迁移记录数: {self.progress.total_records}")
                
                # 3. 迁移每日交易数据
                logger.info("步骤 3/6: 迁移每日交易数据...")
                self.progress.current_table = "daily_trading_unified"
                migrated_daily = self.migrate_daily_trading_data(db, start_date, end_date)
                
                # 4. 迁移概念每日数据
                logger.info("步骤 4/6: 迁移概念每日数据...")
                self.progress.current_table = "concept_daily_metrics"
                migrated_concept = self.migrate_concept_daily_data(db, start_date, end_date)
                
                # 5. 迁移股票概念排名数据
                logger.info("步骤 5/6: 迁移股票概念排名数据...")
                self.progress.current_table = "stock_concept_daily_snapshot"
                migrated_ranking = self.migrate_stock_concept_ranking_data(db, start_date, end_date)
                
                # 6. 计算排名和指标
                logger.info("步骤 6/6: 计算排名和指标...")
                
                # 获取需要计算的日期范围
                date_query = db.query(DailyTradingUnified.trading_date).distinct()
                if start_date:
                    date_query = date_query.filter(DailyTradingUnified.trading_date >= start_date)
                if end_date:
                    date_query = date_query.filter(DailyTradingUnified.trading_date <= end_date)
                
                trading_dates = [row[0] for row in date_query.all()]
                
                for trading_date in trading_dates:
                    self.calculate_rankings_and_metrics(db, trading_date)
                    
                    # 如果是今天，创建缓存
                    if trading_date == date.today():
                        self.create_today_cache(db, trading_date)
                
                # 完成
                self.progress.status = "completed"
                self.save_migration_state()
                
                logger.info("数据迁移完成！")
                logger.info(f"迁移统计:")
                logger.info(f"  - 每日交易数据: {migrated_daily} 条")
                logger.info(f"  - 概念每日数据: {migrated_concept} 条") 
                logger.info(f"  - 股票概念排名: {migrated_ranking} 条")
                logger.info(f"  - 总用时: {self.progress.elapsed_time:.1f} 秒")
                logger.info(f"  - 处理速度: {self.progress.records_per_second:.1f} 记录/秒")
                
                return True
                
        except Exception as e:
            logger.error(f"迁移过程中出错: {e}")
            self.progress.status = "failed"
            self.save_migration_state()
            return False
    
    def verify_migration_data(self, db: Session) -> Dict[str, Any]:
        """验证迁移数据的完整性"""
        logger.info("验证迁移数据完整性...")
        
        results = {}
        
        try:
            # 检查记录数量对比
            old_daily_count = db.query(DailyTrading).count()
            new_daily_count = db.query(DailyTradingUnified).count()
            
            old_concept_count = db.query(ConceptDailySummary).count()
            new_concept_count = db.query(ConceptDailyMetrics).count()
            
            old_ranking_count = db.query(StockConceptRanking).count()
            new_ranking_count = db.query(StockConceptDailySnapshot).count()
            
            results["record_counts"] = {
                "daily_trading": {"old": old_daily_count, "new": new_daily_count, "match": old_daily_count == new_daily_count},
                "concept_daily": {"old": old_concept_count, "new": new_concept_count, "match": old_concept_count == new_concept_count},
                "ranking": {"old": old_ranking_count, "new": new_ranking_count, "match": old_ranking_count == new_ranking_count}
            }
            
            # 抽样检查数据一致性
            sample_date = db.query(DailyTrading.trading_date).order_by(desc(DailyTrading.trading_date)).first()
            if sample_date:
                sample_date = sample_date[0]
                
                old_sample = db.query(DailyTrading).filter(DailyTrading.trading_date == sample_date).limit(10).all()
                new_sample = db.query(DailyTradingUnified).filter(DailyTradingUnified.trading_date == sample_date).limit(10).all()
                
                results["sample_verification"] = {
                    "date": sample_date.strftime('%Y-%m-%d'),
                    "old_count": len(old_sample),
                    "new_count": len(new_sample),
                    "data_matches": []
                }
                
                for old_record in old_sample:
                    new_record = next((r for r in new_sample if r.stock_code == old_record.stock_code), None)
                    if new_record:
                        match = {
                            "stock_code": old_record.stock_code,
                            "volume_match": old_record.trading_volume == new_record.trading_volume,
                            "date_match": old_record.trading_date == new_record.trading_date
                        }
                        results["sample_verification"]["data_matches"].append(match)
            
            # 检查索引和约束
            results["table_structure"] = self.verify_table_structure(db)
            
            # 生成验证报告
            all_counts_match = all(item["match"] for item in results["record_counts"].values())
            all_tables_ready = all(results["table_structure"].values())
            
            results["overall_status"] = {
                "migration_successful": all_counts_match and all_tables_ready,
                "ready_for_production": all_counts_match and all_tables_ready
            }
            
            return results
            
        except Exception as e:
            logger.error(f"验证迁移数据时出错: {e}")
            results["error"] = str(e)
            return results


def main():
    """主函数 - 命令行工具"""
    import argparse
    
    parser = argparse.ArgumentParser(description="数据库平滑迁移工具")
    parser.add_argument("--database-url", required=True, help="数据库连接URL")
    parser.add_argument("--start-date", help="开始日期 (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="结束日期 (YYYY-MM-DD)")
    parser.add_argument("--batch-size", type=int, default=1000, help="批处理大小")
    parser.add_argument("--verify-only", action="store_true", help="仅验证数据，不执行迁移")
    parser.add_argument("--resume", action="store_true", help="从上次中断点继续迁移")
    
    args = parser.parse_args()
    
    # 解析日期参数
    start_date = datetime.strptime(args.start_date, '%Y-%m-%d').date() if args.start_date else None
    end_date = datetime.strptime(args.end_date, '%Y-%m-%d').date() if args.end_date else None
    
    # 创建迁移服务
    migration_service = SmoothMigrationService(args.database_url, args.batch_size)
    
    # 如果是恢复模式，加载之前的状态
    if args.resume:
        migration_service.load_migration_state()
    
    if args.verify_only:
        # 仅验证模式
        with migration_service.SessionLocal() as db:
            results = migration_service.verify_migration_data(db)
            print(json.dumps(results, indent=2, default=str))
    else:
        # 执行迁移
        success = migration_service.run_full_migration(start_date, end_date)
        
        if success:
            print("✓ 数据迁移成功完成")
            
            # 验证迁移结果
            with migration_service.SessionLocal() as db:
                results = migration_service.verify_migration_data(db)
                print("\n迁移验证结果:")
                print(json.dumps(results, indent=2, default=str))
        else:
            print("✗ 数据迁移失败")
            sys.exit(1)


if __name__ == "__main__":
    main()