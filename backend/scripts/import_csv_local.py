#!/usr/bin/env python3
"""
本地CSV文件导入脚本

功能：
- 导入CSV格式的股票数据（包含股票代码、名称、概念、行业等）
- 支持两种CSV格式（中文和英文列名）
- 自动创建/更新 stocks、concepts、stock_concepts 表
- 支持覆盖模式和增量导入

使用示例：
    # 基础导入
    python3 scripts/import_csv_local.py --file /path/to/data.csv

    # 覆盖模式
    python3 scripts/import_csv_local.py --file /path/to/data.csv --overwrite

    # 指定日期
    python3 scripts/import_csv_local.py --file /path/to/data.csv --date 2024-10-16

    # 使用远程数据库
    python3 scripts/import_csv_local.py --file /path/to/data.csv \
        --db-url mysql+pymysql://user:pass@host/dbname

作者: Claude Code
创建时间: 2024-11
"""

import sys
import os
import argparse
from pathlib import Path
from datetime import datetime, date
import asyncio

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import get_database_url
from app.services.data_import import DataImportService


def parse_date(date_str: str) -> date:
    """解析日期字符串"""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        raise argparse.ArgumentTypeError(f"日期格式错误: {date_str}，应为 YYYY-MM-DD")


def setup_database(db_url: str = None):
    """设置数据库连接"""
    if db_url:
        print(f"📡 使用指定的数据库: {db_url.split('@')[-1] if '@' in db_url else db_url}")
        engine = create_engine(db_url, echo=False)
    else:
        print(f"📡 使用默认数据库配置")
        engine = create_engine(get_database_url(), echo=False)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


async def import_csv_file(file_path: str, allow_overwrite: bool = False,
                         trade_date: date = None, db_url: str = None):
    """
    导入CSV文件

    参数:
        file_path: CSV文件路径
        allow_overwrite: 是否覆盖已存在的数据
        trade_date: 指定交易日期（可选）
        db_url: 数据库连接字符串（可选）
    """
    # 验证文件存在
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return False

    # 验证文件扩展名
    if not file_path.endswith('.csv'):
        print(f"❌ 文件必须是CSV格式: {file_path}")
        return False

    # 获取文件信息
    file_size = os.path.getsize(file_path)
    file_name = os.path.basename(file_path)

    print("\n" + "=" * 70)
    print("📊 CSV本地文件导入脚本")
    print("=" * 70)
    print(f"📁 文件路径: {file_path}")
    print(f"📋 文件名称: {file_name}")
    print(f"📦 文件大小: {file_size:,} bytes ({file_size / 1024:.2f} KB)")
    if trade_date:
        print(f"📅 指定日期: {trade_date}")
    print(f"🔄 覆盖模式: {'是' if allow_overwrite else '否'}")
    print("=" * 70)
    print()

    try:
        # 读取文件内容
        with open(file_path, 'rb') as f:
            content = f.read()

        print(f"✅ 文件读取成功，大小: {len(content):,} bytes")
        print()

        # 设置数据库连接
        db = setup_database(db_url)

        try:
            # 创建导入服务
            import_service = DataImportService(db)

            # 执行导入
            print("🚀 开始导入CSV数据...")
            print("-" * 70)

            result = await import_service.import_csv_data(
                content=content,
                filename=file_name,
                allow_overwrite=allow_overwrite,
                trade_date=trade_date
            )

            print("-" * 70)
            print()

            # 显示导入结果
            if result.get("already_exists") and not allow_overwrite:
                print("⚠️  数据已存在")
                print(f"   📅 导入日期: {result['import_date']}")
                print(f"   📊 已导入记录: {result['imported_records']} 条")
                print(f"   ⏭️  跳过记录: {result['skipped_records']} 条")
                print(f"   💡 提示: 使用 --overwrite 参数可以覆盖已存在的数据")
                print()
                return True

            # 显示详细统计
            print("✅ 导入完成！")
            print()
            print("📈 导入统计:")
            print(f"   📅 导入日期: {result['import_date']}")
            print(f"   ✅ 成功记录: {result['imported_records']} 条")
            print(f"   ⏭️  跳过记录: {result['skipped_records']} 条")

            if result.get('stats'):
                stats = result['stats']
                print()
                print("📊 详细信息:")
                print(f"   🏢 股票: {stats.get('new_stocks', 0)} 新增, {stats.get('updated_stocks', 0)} 更新")
                print(f"   🏷️  概念: {stats.get('new_concepts', 0)} 新增")
                print(f"   🔗 关联: {stats.get('new_relations', 0)} 新增")
                print(f"   📈 每日数据: {stats.get('new_daily_data', 0)} 新增, {stats.get('updated_daily_data', 0)} 更新")
                print(f"   💾 原始数据: {stats.get('raw_data_records', 0)} 条")

            # 显示错误信息
            if result.get('errors'):
                print()
                print(f"⚠️  错误记录: {len(result['errors'])} 条")
                print("   显示前5条错误:")
                for i, error in enumerate(result['errors'][:5], 1):
                    print(f"   {i}. {error}")

            print()
            print("=" * 70)

            return True

        finally:
            db.close()

    except Exception as e:
        print()
        print("=" * 70)
        print(f"❌ 导入失败: {str(e)}")
        print("=" * 70)
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='本地CSV文件导入脚本 - 导入股票、概念和关联数据',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
CSV文件格式:
  支持两种格式：

  1. 英文格式:
     stock_code,stock_name,concept,industry,date,price,turnover_rate,net_inflow

  2. 中文格式:
     股票代码,股票名称,概念,行业,价格,换手,净流入,全部页数,热帖首页页阅读总数

必需字段:
  - 股票代码 (stock_code)
  - 股票名称 (stock_name)
  - 概念 (concept)

使用示例:
  # 基础导入
  python3 scripts/import_csv_local.py --file /path/to/data.csv

  # 覆盖已存在的数据
  python3 scripts/import_csv_local.py --file /path/to/data.csv --overwrite

  # 指定交易日期
  python3 scripts/import_csv_local.py --file /path/to/data.csv --date 2024-10-16

  # 使用远程数据库
  python3 scripts/import_csv_local.py --file /path/to/data.csv \\
      --db-url mysql+pymysql://user:pass@host/dbname

注意事项:
  1. 概念采用增量模式：只添加新关联，不删除旧关联
  2. 股票信息会被更新：名称、行业等会使用最新CSV的数据
  3. 覆盖模式只影响 daily_stock_data，不影响概念关联
  4. 支持SH/SZ/BJ/HK等前缀，会自动规范化
  5. 自动识别转债（1开头的6位代码）
        """
    )

    parser.add_argument(
        '--file',
        required=True,
        help='CSV文件路径（必需）'
    )

    parser.add_argument(
        '--overwrite',
        action='store_true',
        help='覆盖已存在的数据（默认: False）'
    )

    parser.add_argument(
        '--date',
        type=parse_date,
        help='指定交易日期 (格式: YYYY-MM-DD)，不指定则从文件名解析'
    )

    parser.add_argument(
        '--db-url',
        help='数据库连接字符串（可选）'
    )

    args = parser.parse_args()

    # 执行导入
    success = asyncio.run(import_csv_file(
        file_path=args.file,
        allow_overwrite=args.overwrite,
        trade_date=args.date,
        db_url=args.db_url
    ))

    # 返回退出码
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
