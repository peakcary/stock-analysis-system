"""
TTV 交易数据专用导入脚本 (修正版)
将 TTV.txt 文件中的交易数据批量导入到 ttv_daily_trading 表
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from decimal import Decimal
import hashlib

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def calculate_file_hash(file_path: str) -> str:
    """计算文件哈希值"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def parse_ttv_file(file_path: str):
    """
    解析 TTV.txt 文件，按日期分组返回数据
    格式: 股票代码[Tab]交易日期[Tab]数值
    例如: BJ920000\t2024-07-30\t0.000000
    """
    data_by_date = defaultdict(list)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            line_num = 0
            for line in f:
                line_num += 1
                line = line.strip()

                if not line or line.startswith('#'):
                    continue

                try:
                    parts = line.split('\t')

                    if len(parts) < 3:
                        logger.warning(f"第{line_num}行数据不完整: {line}")
                        continue

                    original_stock_code = parts[0].strip()
                    trade_date = parts[1].strip()
                    value = int(float(parts[2].strip()))  # 转为整数

                    # 提取前缀和规范化代码
                    if original_stock_code.startswith('SH'):
                        stock_code_prefix = 'SH'
                        stock_code = original_stock_code[2:]
                    elif original_stock_code.startswith('SZ'):
                        stock_code_prefix = 'SZ'
                        stock_code = original_stock_code[2:]
                    elif original_stock_code.startswith('BJ'):
                        stock_code_prefix = 'BJ'
                        stock_code = original_stock_code[2:]
                    else:
                        stock_code_prefix = ''
                        stock_code = original_stock_code

                    record = {
                        'original_stock_code': original_stock_code,
                        'stock_code': stock_code,
                        'stock_code_prefix': stock_code_prefix,
                        'trade_date': trade_date,
                        'value': value,
                        'row_number': line_num
                    }

                    data_by_date[trade_date].append(record)

                except ValueError as e:
                    logger.warning(f"第{line_num}行解析失败: {line}, 错误: {e}")
                    continue

        logger.info(f"✓ {file_path} 解析完成，包含 {len(data_by_date)} 个交易日期，共 {sum(len(v) for v in data_by_date.values())} 条记录")
        return data_by_date

    except Exception as e:
        logger.error(f"读取文件失败: {file_path}, 错误: {e}")
        raise


def insert_ttv_data(db: Session, data_by_date: dict, file_path: str, file_hash: str):
    """
    将 TTV 数据插入到 ttv_daily_trading 表
    """
    from app.models.stock import TtvDailyTrading, TtvImportRecord

    total_inserted = 0
    success_dates = []
    failed_dates = []

    # 创建导入记录
    file_size = os.path.getsize(file_path)
    total_records = sum(len(v) for v in data_by_date.values())

    for trade_date_str, records in sorted(data_by_date.items()):
        try:
            trade_date = datetime.strptime(trade_date_str, '%Y-%m-%d').date()

            # 检查是否已存在该日期的数据
            existing_count = db.query(TtvDailyTrading).filter(
                TtvDailyTrading.trading_date == trade_date
            ).count()

            if existing_count > 0:
                logger.warning(f"  ⚠️  {trade_date_str} 已存在 {existing_count} 条数据，跳过")
                failed_dates.append(trade_date_str)
                continue

            # 插入该日期的所有记录
            for record in records:
                ttv_data = TtvDailyTrading(
                    original_stock_code=record['original_stock_code'],
                    normalized_stock_code=record['stock_code'],
                    stock_code=f"{record['stock_code_prefix']}{record['stock_code']}",
                    trading_date=trade_date,
                    trading_volume=record['value']
                )
                db.add(ttv_data)

            db.commit()
            total_inserted += len(records)
            success_dates.append(trade_date_str)
            logger.info(f"  ✓ {trade_date_str}: 插入 {len(records)} 条记录到 ttv_daily_trading")

        except Exception as e:
            db.rollback()
            logger.error(f"  ✗ {trade_date_str} 插入失败: {e}")
            failed_dates.append(trade_date_str)
            continue

    # 创建导入记录
    try:
        import_record = TtvImportRecord(
            filename=Path(file_path).name,
            trading_date=datetime.now().date(),
            file_size=file_size,
            file_hash=file_hash,
            import_status='success' if len(failed_dates) == 0 else 'partial',
            imported_by='system',
            total_records=total_records,
            success_records=total_inserted,
            error_records=0,
            duplicate_records=len(failed_dates),
            import_started_at=datetime.now(),
            import_completed_at=datetime.now(),
            calculation_time=0,
            notes=f"Batch import from {Path(file_path).name}"
        )
        db.add(import_record)
        db.commit()
        logger.info(f"✓ 导入记录已创建")
    except Exception as e:
        logger.warning(f"⚠️  创建导入记录失败: {e}")

    logger.info(f"\n总计插入 {total_inserted} 条 TTV 数据到 ttv_daily_trading\n")
    logger.info(f"成功日期: {len(success_dates)}, 失败日期: {len(failed_dates)}")

    return len(success_dates), len(failed_dates)


def main():
    """
    主函数
    """
    import argparse

    parser = argparse.ArgumentParser(description='TTV 交易数据导入脚本 (修正版)')
    parser.add_argument('--file', type=str, default='/Users/peakom/Downloads/TTV.txt',
                        help='TTV.txt 文件路径')
    parser.add_argument('--db-url', type=str, default='postgresql://postgres:Pp123456@localhost/stockdb',
                        help='数据库URL')

    args = parser.parse_args()

    if not os.path.exists(args.file):
        logger.error(f"文件不存在: {args.file}")
        return

    logger.info(f"""
╔════════════════════════════════════════════════════════╗
║     TTV 交易数据批量导入脚本 (修正版)                  ║
╚════════════════════════════════════════════════════════╝

配置:
  文件路径: {args.file}
  目标表: ttv_daily_trading
  数据库: {args.db_url.split('@')[-1]}
""")

    try:
        # 1. 计算文件哈希
        logger.info("Step 1: 计算文件哈希...")
        file_hash = calculate_file_hash(args.file)
        logger.info(f"✓ 文件哈希: {file_hash}")

        # 2. 解析文件
        logger.info("\nStep 2: 解析 TTV.txt 文件...")
        data_by_date = parse_ttv_file(args.file)

        if not data_by_date:
            logger.warning("没有数据可导入")
            return

        # 3. 连接数据库并插入数据
        logger.info("\nStep 3: 导入数据到 ttv_daily_trading...")
        engine = create_engine(args.db_url)
        with Session(engine) as db:
            successful, failed = insert_ttv_data(db, data_by_date, args.file, file_hash)

        logger.info(f"""
╔════════════════════════════════════════════════════════╗
║                    导入完成！                           ║
╚════════════════════════════════════════════════════════╝

统计:
  交易日期: {len(data_by_date)} 个
  总记录数: {sum(len(v) for v in data_by_date.values())}
  成功导入: {successful} 个日期
  失败日期: {failed} 个日期
  目标表: ttv_daily_trading
""")

    except Exception as e:
        logger.error(f"发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
