"""
EEE和TTV数据汇总计算脚本
支持单日期、日期范围、整月批量计算
类似于前端"重新计算"按钮的逻辑
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict
import argparse
import logging

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, func, and_
from sqlalchemy.orm import Session
from app.models.stock import Stock, EeeDailyTrading, TtvDailyTrading
from app.models.concept import StockConcept, Concept
from app.models.concept_analysis import DailyConceptRanking, DailyConceptSummary, DailyAnalysisTask

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RankingCalculator:
    """排名计算引擎"""

    def __init__(self, db: Session):
        self.db = db

    def calculate_for_date(self, trade_date, data_source='eee'):
        """
        计算指定日期的排名数据

        Args:
            trade_date: 交易日期
            data_source: 数据源 ('eee' 或 'ttv')
        """
        logger.info(f"\n开始计算 {trade_date} 的 {data_source.upper()} 数据排名...")

        # 选择数据源表
        if data_source == 'eee':
            source_table = EeeDailyTrading
        else:
            source_table = TtvDailyTrading

        # 获取该日期的所有原始数据
        raw_data = self.db.query(source_table).filter(
            source_table.trading_date == trade_date
        ).all()

        if not raw_data:
            logger.warning(f"  ⚠️  {trade_date} 没有 {data_source.upper()} 数据")
            return None

        logger.info(f"  ✓ 读取 {len(raw_data)} 条原始记录")

        # 按概念分组数据
        data_by_concept = defaultdict(list)
        stock_info = {}  # 缓存股票信息

        for record in raw_data:
            # 获取股票和概念信息
            stock = self.db.query(Stock).filter(
                Stock.stock_code == record.normalized_stock_code
            ).first()

            if not stock:
                logger.warning(f"  ⚠️  找不到股票: {record.normalized_stock_code}")
                continue

            stock_info[stock.id] = {
                'name': stock.stock_name,
                'code': record.stock_code,
                'normalized_code': record.normalized_stock_code
            }

            # 获取股票所属的概念
            concepts = self.db.query(Concept).join(
                StockConcept, StockConcept.concept_id == Concept.id
            ).filter(StockConcept.stock_id == stock.id).all()

            for concept in concepts:
                data_by_concept[concept.id].append({
                    'concept': concept,
                    'stock_id': stock.id,
                    'heat_value': record.trading_volume,
                    'record': record
                })

        logger.info(f"  ✓ 分组到 {len(data_by_concept)} 个概念")

        # 为每个概念计算排名
        total_rankings = 0
        total_summaries = 0

        for concept_id, stocks_data in data_by_concept.items():
            # 按热度值排序
            sorted_stocks = sorted(
                stocks_data,
                key=lambda x: x['heat_value'],
                reverse=True
            )

            # 创建排名记录
            for rank, item in enumerate(sorted_stocks, 1):
                try:
                    # 检查是否已存在
                    existing = self.db.query(DailyConceptRanking).filter(
                        and_(
                            DailyConceptRanking.concept_id == concept_id,
                            DailyConceptRanking.stock_id == item['stock_id'],
                            DailyConceptRanking.trade_date == trade_date
                        )
                    ).first()

                    if existing:
                        # 更新现有记录
                        existing.rank_in_concept = rank
                        existing.heat_value = Decimal(str(item['heat_value']))
                    else:
                        # 创建新记录
                        ranking = DailyConceptRanking(
                            concept_id=concept_id,
                            stock_id=item['stock_id'],
                            trade_date=trade_date,
                            rank_in_concept=rank,
                            heat_value=Decimal(str(item['heat_value']))
                        )
                        self.db.add(ranking)

                    total_rankings += 1

                except Exception as e:
                    logger.error(f"  ✗ 创建排名记录失败: {e}")
                    continue

            # 创建概念汇总记录
            try:
                total_heat = sum(Decimal(str(s['heat_value'])) for s in sorted_stocks)
                avg_heat = total_heat / len(sorted_stocks)
                max_heat = max(Decimal(str(s['heat_value'])) for s in sorted_stocks)
                min_heat = min(Decimal(str(s['heat_value'])) for s in sorted_stocks)

                # 检查是否已存在
                existing_summary = self.db.query(DailyConceptSummary).filter(
                    and_(
                        DailyConceptSummary.concept_id == concept_id,
                        DailyConceptSummary.trade_date == trade_date
                    )
                ).first()

                if existing_summary:
                    # 更新现有记录
                    existing_summary.total_heat_value = total_heat
                    existing_summary.stock_count = len(sorted_stocks)
                    existing_summary.avg_heat_value = avg_heat
                    existing_summary.max_heat_value = max_heat
                    existing_summary.min_heat_value = min_heat
                else:
                    # 创建新记录
                    summary = DailyConceptSummary(
                        concept_id=concept_id,
                        trade_date=trade_date,
                        total_heat_value=total_heat,
                        stock_count=len(sorted_stocks),
                        avg_heat_value=avg_heat,
                        max_heat_value=max_heat,
                        min_heat_value=min_heat
                    )
                    self.db.add(summary)

                total_summaries += 1

            except Exception as e:
                logger.error(f"  ✗ 创建汇总记录失败: {e}")
                continue

        # 提交事务
        try:
            self.db.commit()
            logger.info(f"  ✓ {trade_date}: 创建 {total_rankings} 条排名记录，{total_summaries} 条汇总记录")
            return {
                'date': trade_date,
                'rankings': total_rankings,
                'summaries': total_summaries,
                'concepts': len(data_by_concept)
            }
        except Exception as e:
            self.db.rollback()
            logger.error(f"  ✗ 提交失败: {e}")
            return None

    def calculate_date_range(self, start_date, end_date, data_source='eee'):
        """
        计算日期范围内的所有数据

        Args:
            start_date: 开始日期
            end_date: 结束日期
            data_source: 数据源
        """
        logger.info(f"\n计算日期范围: {start_date} 至 {end_date}")

        current_date = start_date
        results = []

        while current_date <= end_date:
            result = self.calculate_for_date(current_date, data_source)
            if result:
                results.append(result)
            current_date += timedelta(days=1)

        return results


def record_task(db: Session, trade_date, task_type, status, processed_records=0, error_msg=None):
    """记录分析任务"""
    try:
        task = DailyAnalysisTask(
            trade_date=trade_date,
            task_type=task_type,
            status=status,
            started_at=datetime.now(),
            completed_at=datetime.now() if status == 'completed' else None,
            error_message=error_msg,
            processed_records=processed_records
        )
        db.add(task)
        db.commit()
    except Exception as e:
        logger.warning(f"⚠️  无法记录任务: {e}")


def main():
    """主函数"""

    parser = argparse.ArgumentParser(description='EEE/TTV 数据排名计算脚本')

    # 数据源
    parser.add_argument('--source', type=str, default='eee', choices=['eee', 'ttv'],
                        help='数据源 (eee/ttv，默认: eee)')

    # 日期参数
    date_group = parser.add_mutually_exclusive_group(required=True)
    date_group.add_argument('--date', type=str, help='单个日期 (YYYY-MM-DD)')
    date_group.add_argument('--range', type=str, nargs=2, metavar=('START', 'END'),
                           help='日期范围 (YYYY-MM-DD YYYY-MM-DD)')
    date_group.add_argument('--month', type=str, help='整月计算 (YYYY-MM)')

    # 数据库
    parser.add_argument('--db-url', type=str, default='postgresql://postgres:Pp123456@localhost/stockdb',
                        help='数据库URL')

    args = parser.parse_args()

    logger.info(f"""
╔════════════════════════════════════════════════════════╗
║         排名和汇总数据计算脚本                         ║
╚════════════════════════════════════════════════════════╝

配置:
  数据源: {args.source.upper()}
  数据库: {args.db_url.split('@')[-1]}
""")

    # 解析日期
    try:
        if args.date:
            start_date = datetime.strptime(args.date, '%Y-%m-%d').date()
            end_date = start_date
            logger.info(f"  计算模式: 单日期 ({args.date})")

        elif args.range:
            start_date = datetime.strptime(args.range[0], '%Y-%m-%d').date()
            end_date = datetime.strptime(args.range[1], '%Y-%m-%d').date()
            logger.info(f"  计算模式: 日期范围 ({args.range[0]} 至 {args.range[1]})")

        elif args.month:
            year_month = datetime.strptime(args.month, '%Y-%m')
            start_date = year_month.date().replace(day=1)
            # 计算月末
            next_month = year_month.replace(day=28) + timedelta(days=4)
            end_date = (next_month - timedelta(days=next_month.day)).date()
            logger.info(f"  计算模式: 整月 ({args.month}，{(end_date - start_date).days + 1} 天)")

    except ValueError as e:
        logger.error(f"日期解析失败: {e}")
        return

    try:
        # 连接数据库
        engine = create_engine(args.db_url)
        with Session(engine) as db:
            calculator = RankingCalculator(db)

            # 执行计算
            if start_date == end_date:
                # 单日期
                result = calculator.calculate_for_date(start_date, args.source)

                if result:
                    record_task(db, start_date, f'{args.source}_ranking', 'completed',
                               result['rankings'])
                    logger.info(f"\n✅ 计算完成!")
                    logger.info(f"""
统计:
  日期: {start_date}
  排名记录: {result['rankings']}
  汇总记录: {result['summaries']}
  涉及概念: {result['concepts']}
""")
            else:
                # 日期范围
                results = calculator.calculate_date_range(start_date, end_date, args.source)

                if results:
                    total_rankings = sum(r['rankings'] for r in results)
                    total_summaries = sum(r['summaries'] for r in results)
                    total_concepts = len(set(d for r in results for d in [r['concepts']]))

                    logger.info(f"\n✅ 批量计算完成!")
                    logger.info(f"""
统计:
  日期范围: {start_date} 至 {end_date}，共 {(end_date - start_date).days + 1} 天
  成功计算: {len(results)} 天
  总排名记录: {total_rankings}
  总汇总记录: {total_summaries}
  涉及概念数: {total_concepts}
""")

    except Exception as e:
        logger.error(f"计算失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
