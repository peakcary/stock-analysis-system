"""
本地文件批量导入脚本
将EEE.txt/TTV.txt文件的原始数据导入到数据库，然后触发重新计算
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from decimal import Decimal

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


def parse_tsv_file(file_path: str, file_type: str):
    """
    解析TSV文件，按日期分组返回数据

    返回：
    {
        'yyyy-mm-dd': [
            {'stock_code': '600000', 'heat_value': 1000.0, 'original_stock_code': 'SH600000', ...},
            ...
        ],
        ...
    }
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
                    value = float(parts[2].strip())

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


def insert_raw_data(db: Session, file_type: str, data_by_date: dict):
    """
    将解析的数据插入到原始表
    """
    from app.models.stock import ImportBatch, RawImportData

    total_inserted = 0

    for trade_date_str, records in sorted(data_by_date.items()):
        try:
            trade_date = datetime.strptime(trade_date_str, '%Y-%m-%d').date()

            # 1. 检查是否已存在该日期的导入批次
            existing_batch = db.query(ImportBatch).filter(
                ImportBatch.import_date == trade_date,
                ImportBatch.import_type == file_type
            ).first()

            if existing_batch:
                logger.warning(f"  ⚠️  {trade_date_str} ({file_type}) 已存在导入批次，跳过")
                continue

            # 2. 创建新的导入批次记录
            batch = ImportBatch(
                import_date=trade_date,
                import_type=file_type,
                file_name=f"batch_import_{file_type}_{trade_date_str}",
                record_count=len(records),
                status='success'
            )
            db.add(batch)
            db.flush()  # 获取batch.id

            # 3. 插入原始数据记录
            for record in records:
                raw_data = RawImportData(
                    import_batch_id=batch.id,
                    row_number=record['row_number'],
                    trade_date=trade_date,
                    stock_code_raw=record['original_stock_code'],
                    stock_code_normalized=record['stock_code'],
                    stock_code_prefix=record['stock_code_prefix'],
                    stock_name='',  # 暂时为空，可后续补充
                    industry='',    # 暂时为空
                    heat_value=Decimal(str(record['value'])) if file_type.upper() == 'EEE' else None,
                    source_type=file_type.lower(),
                    source_file=f"{file_type.upper()}_{trade_date_str}"
                )
                db.add(raw_data)

            db.commit()
            total_inserted += len(records)
            logger.info(f"  ✓ {trade_date_str} ({file_type}): 插入 {len(records)} 条记录")

        except Exception as e:
            db.rollback()
            logger.error(f"  ✗ {trade_date_str} ({file_type}) 插入失败: {e}")
            continue

    logger.info(f"\n总计插入 {total_inserted} 条原始数据记录\n")
    return total_inserted


def perform_local_calculations(db: Session, file_type: str, data_by_date: dict):
    """
    在本地直接执行计算逻辑（不需要调用 API）
    这样速度更快，且不需要启动后端服务
    """
    from datetime import date as date_class
    from app.services.universal_import_service import UniversalImportService

    successful_dates = []
    failed_dates = []

    logger.info(f"\n开始本地计算 {file_type.upper()} 数据汇总...\n")

    for trade_date_str in sorted(data_by_date.keys()):
        try:
            trade_date = datetime.strptime(trade_date_str, '%Y-%m-%d').date()

            logger.info(f"  计算中... {trade_date_str}", end=' ', flush=True)

            # 创建导入服务实例并执行计算
            import_service = UniversalImportService(db, file_type)
            calculation_result = import_service.perform_calculations(trade_date, None)

            logger.info(
                f"✓ 完成 | 概念: {calculation_result.get('concept_count', 0)}, "
                f"排名: {calculation_result.get('ranking_count', 0)}, "
                f"创新高: {calculation_result.get('new_high_count', 0)}"
            )
            successful_dates.append(trade_date_str)

        except Exception as e:
            logger.error(f"✗ 错误: {str(e)[:100]}")
            failed_dates.append(trade_date_str)
            continue

    logger.info(f"\n本地计算统计: {len(successful_dates)} 成功, {len(failed_dates)} 失败\n")

    if failed_dates:
        logger.warning(f"失败的日期: {', '.join(failed_dates[:10])}")

    return len(successful_dates), len(failed_dates)


def trigger_recalculation(api_base_url: str, file_type: str, data_by_date: dict):
    """
    通过 API 触发后端重新计算（需要后端服务运行）
    """
    import requests
    from datetime import datetime as dt

    successful_dates = []
    failed_dates = []

    logger.info(f"\n开始通过 API 触发 {file_type.upper()} 重新计算...\n")

    for trade_date_str in sorted(data_by_date.keys()):
        try:
            url = f"{api_base_url}/api/v1/universal-import/{file_type}/recalculate"
            params = {'trading_date': trade_date_str}

            logger.info(f"  计算中... {trade_date_str}", end=' ')

            response = requests.post(
                url,
                params=params,
                timeout=180  # 3分钟超时
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    calc = data.get('calculation_result', {})
                    logger.info(
                        f"✓ 完成 | 概念: {calc.get('concept_count', 0)}, "
                        f"排名: {calc.get('ranking_count', 0)}, "
                        f"创新高: {calc.get('new_high_count', 0)}"
                    )
                    successful_dates.append(trade_date_str)
                else:
                    logger.error(f"✗ 失败 | {data.get('message', '未知错误')}")
                    failed_dates.append(trade_date_str)
            else:
                logger.error(f"✗ HTTP {response.status_code} | {response.text[:100]}")
                failed_dates.append(trade_date_str)

        except requests.exceptions.Timeout:
            logger.error(f"✗ 超时")
            failed_dates.append(trade_date_str)
        except Exception as e:
            logger.error(f"✗ 错误: {str(e)[:100]}")
            failed_dates.append(trade_date_str)

    logger.info(f"\nAPI 计算统计: {len(successful_dates)} 成功, {len(failed_dates)} 失败\n")

    if failed_dates:
        logger.warning(f"失败的日期: {', '.join(failed_dates[:10])}")

    return len(successful_dates), len(failed_dates)


def main():
    """
    主函数
    """
    import argparse

    parser = argparse.ArgumentParser(description='本地文件批量导入脚本')
    parser.add_argument('--file', type=str, help='文件路径 (EEE.txt 或 TTV.txt)')
    parser.add_argument('--type', type=str, choices=['eee', 'ttv'], help='文件类型')
    parser.add_argument('--db-url', type=str, default='postgresql://postgres:Pp123456@localhost/stockdb',
                        help='数据库URL')
    parser.add_argument('--api-url', type=str, default='http://localhost:3007',
                        help='API基础URL')
    parser.add_argument('--skip-calc', action='store_true', help='跳过重新计算步骤')
    parser.add_argument('--use-api', action='store_true', help='使用 API 进行重新计算（默认使用本地计算）')

    args = parser.parse_args()

    # 获取默认文件路径
    if not args.file:
        if args.type:
            file_path = f'/Users/peakom/Downloads/{args.type.upper()}.txt'
        else:
            print("错误: 必须指定 --file 或 --type")
            return
    else:
        file_path = args.file

    if not args.type and args.file:
        filename = Path(args.file).name.upper()
        if 'EEE' in filename:
            args.type = 'eee'
        elif 'TTV' in filename:
            args.type = 'ttv'
        else:
            print("错误: 无法确定文件类型，请使用 --type 指定")
            return

    if not os.path.exists(file_path):
        logger.error(f"文件不存在: {file_path}")
        return

    logger.info(f"""
╔════════════════════════════════════════════════════════╗
║          本地文件批量导入脚本                           ║
╚════════════════════════════════════════════════════════╝

配置:
  文件类型: {args.type.upper()}
  文件路径: {file_path}
  数据库: {args.db_url.split('@')[-1]}
  API: {args.api_url}
""")

    try:
        # 1. 解析文件
        logger.info("Step 1: 解析本地文件...")
        data_by_date = parse_tsv_file(file_path, args.type)

        if not data_by_date:
            logger.warning("没有数据可导入")
            return

        # 2. 连接数据库并插入数据
        logger.info("\nStep 2: 导入原始数据到数据库...")
        engine = create_engine(args.db_url)
        with Session(engine) as db:
            insert_raw_data(db, args.type, data_by_date)

        # 3. 触发重新计算（可选）
        if not args.skip_calc:
            if args.use_api:
                logger.info("Step 3: 通过 API 触发后端重新计算...")
                successful, failed = trigger_recalculation(args.api_url, args.type, data_by_date)
            else:
                logger.info("Step 3: 执行本地重新计算...")
                engine = create_engine(args.db_url)
                with Session(engine) as db:
                    successful, failed = perform_local_calculations(db, args.type, data_by_date)

            logger.info(f"""
╔════════════════════════════════════════════════════════╗
║                    导入完成！                           ║
╚════════════════════════════════════════════════════════╝

统计:
  文件类型: {args.type.upper()}
  交易日期: {len(data_by_date)} 个
  总记录数: {sum(len(v) for v in data_by_date.values())}
  重新计算成功: {successful} 个日期
  重新计算失败: {failed} 个日期
  计算模式: {'API' if args.use_api else '本地'}
""")
        else:
            logger.info(f"""
╔════════════════════════════════════════════════════════╗
║                  数据导入完成！                        ║
╚════════════════════════════════════════════════════════╝

统计:
  文件类型: {args.type.upper()}
  交易日期: {len(data_by_date)} 个
  总记录数: {sum(len(v) for v in data_by_date.values())}

提示: 使用 --skip-calc=false 或不加该参数来触发重新计算
""")

    except Exception as e:
        logger.error(f"发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
