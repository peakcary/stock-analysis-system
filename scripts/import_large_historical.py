#!/usr/bin/env python3
"""
大文件历史数据导入脚本
支持处理包含多个日期的大型TXT文件，自动按日期分组并逐日导入
"""

# 必须在导入任何SQLAlchemy相关模块之前完全禁用SQL日志
import logging
import os

# 设置环境变量完全禁用SQLAlchemy日志
os.environ['SQLALCHEMY_SILENCE_UBER_WARNING'] = '1'

# 配置日志系统
logging.basicConfig(level=logging.CRITICAL, format='')

# 获取根日志器并禁用所有处理器
root_logger = logging.getLogger()
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

# 创建空的处理器避免日志输出
class NullHandler(logging.Handler):
    def emit(self, record):
        pass

null_handler = NullHandler()
root_logger.addHandler(null_handler)
root_logger.setLevel(logging.CRITICAL)

# 彻底禁用SQLAlchemy相关日志
for logger_name in [
    'sqlalchemy', 'sqlalchemy.engine', 'sqlalchemy.pool',
    'sqlalchemy.orm', 'sqlalchemy.dialects', 'sqlalchemy.engine.Engine'
]:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.CRITICAL)
    logger.disabled = True
    logger.propagate = False
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

# 抑制警告信息
import warnings
warnings.filterwarnings("ignore")

import os
import sys
import time
import argparse
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Optional

# 添加后端目录到路径
script_dir = Path(__file__).parent
backend_dir = script_dir.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.core.database import get_db
from app.services.historical_txt_import import HistoricalTxtImportService


def parse_large_txt_by_date(file_path: str, encoding: str = 'utf-8', quiet: bool = False, ignore_errors: bool = False, _retry_count: int = 0) -> Dict[str, List[str]]:
    """按日期分组解析大型TXT文件"""
    if not quiet:
        print(f"📁 开始解析文件: {file_path}")

    date_groups = defaultdict(list)
    total_lines = 0
    valid_lines = 0
    error_lines = 0

    file_size = os.path.getsize(file_path)
    file_size_mb = file_size / 1024 / 1024

    if not quiet:
        print(f"📊 文件大小: {file_size_mb:.2f} MB")

    start_time = time.time()

    try:
        with open(file_path, 'r', encoding=encoding) as file:
            for line_num, line in enumerate(file, 1):
                total_lines += 1

                # 显示进度（每10000行）
                if not quiet and total_lines % 10000 == 0:
                    elapsed = time.time() - start_time
                    print(f"📈 已处理 {total_lines:,} 行，用时 {elapsed:.1f}s")

                line = line.strip()
                if not line:
                    continue

                try:
                    parts = line.split('\t')
                    if len(parts) != 3:
                        error_lines += 1
                        continue

                    stock_code, date_str, volume_str = parts

                    # 验证日期格式
                    datetime.strptime(date_str, '%Y-%m-%d')

                    # 验证交易量
                    float(volume_str)

                    date_groups[date_str].append(line)
                    valid_lines += 1

                except (ValueError, IndexError) as e:
                    error_lines += 1
                    # 如果不忽略错误，显示错误信息
                    if not ignore_errors and not quiet:
                        if error_lines <= 5:
                            print(f"⚠️  第{line_num}行格式错误: {line[:50]}...")
                        elif error_lines == 6:
                            print(f"⚠️  ... 还有更多格式错误，将自动跳过")

                    # 如果不忽略错误且错误太多，终止处理
                    if not ignore_errors and error_lines > 1000:
                        print(f"❌ 错误行数过多 ({error_lines})，请检查文件格式")
                        break

    except UnicodeDecodeError:
        if _retry_count == 0 and encoding.lower() != 'gbk':
            print(f"❌ 编码错误，尝试使用GBK编码...")
            return parse_large_txt_by_date(file_path, 'gbk', quiet, ignore_errors, 1)
        else:
            print(f"❌ 编码错误，无法解析文件，请检查文件编码")
            return {}

    elapsed = time.time() - start_time

    if not quiet:
        print(f"\n✅ 文件解析完成:")
        print(f"   📝 总行数: {total_lines:,}")
        print(f"   ✅ 有效行数: {valid_lines:,}")
        print(f"   ❌ 错误行数: {error_lines:,}")
        print(f"   📅 发现日期: {len(date_groups)} 个")
        print(f"   ⏱️  解析用时: {elapsed:.2f}s")

    return dict(date_groups)


def import_date_groups(date_groups: Dict[str, List[str]], imported_by: str = "script", quiet: bool = False):
    """按日期分组导入数据"""
    if not quiet:
        print(f"\n🚀 开始数据导入...")

    # 按日期排序
    sorted_dates = sorted(date_groups.keys())
    total_dates = len(sorted_dates)

    if not quiet:
        print(f"📅 将按时间顺序导入 {total_dates} 个日期的数据")

    # 获取数据库会话
    db = next(get_db())
    historical_service = HistoricalTxtImportService(db)
    txt_service = historical_service.txt_service

    success_count = 0
    failed_count = 0
    total_records = 0
    failed_dates = []

    start_time = time.time()

    for i, date_str in enumerate(sorted_dates, 1):
        date_lines = date_groups[date_str]

        print(f"\n📊 [{i}/{total_dates}] 正在导入 {date_str} ({len(date_lines):,} 条记录)")

        try:
            # 构造单日数据内容
            single_date_content = '\n'.join(date_lines)

            # 使用TXT导入服务（会创建导入记录）
            result = txt_service.import_daily_trading(
                txt_content=single_date_content,
                filename=f"large_file_{date_str}.txt",
                file_size=len(single_date_content.encode('utf-8')),
                imported_by=imported_by
            )

            if result["success"]:
                success_count += 1
                records_count = result["stats"]["trading_data_count"]
                total_records += records_count
                print(f"   ✅ 导入成功: {records_count:,} 条记录")
            else:
                failed_count += 1
                failed_dates.append(date_str)
                print(f"   ❌ 导入失败: {result['message']}")

        except Exception as e:
            failed_count += 1
            failed_dates.append(date_str)
            print(f"   ❌ 导入异常: {str(e)}")

        # 显示进度
        progress = (i / total_dates) * 100
        elapsed = time.time() - start_time
        avg_time = elapsed / i
        eta = avg_time * (total_dates - i)

        print(f"   📈 进度: {progress:.1f}% | 用时: {elapsed:.1f}s | 预计剩余: {eta:.1f}s")

    # 关闭数据库连接
    db.close()

    total_time = time.time() - start_time

    print(f"\n🎉 导入完成!")
    print(f"   📅 总日期数: {total_dates}")
    print(f"   ✅ 成功: {success_count}")
    print(f"   ❌ 失败: {failed_count}")
    print(f"   📝 总记录数: {total_records:,}")
    print(f"   ⏱️  总用时: {total_time:.2f}s")

    if failed_dates:
        print(f"\n❌ 失败的日期:")
        for date in failed_dates:
            print(f"   - {date}")

    return {
        "total_dates": total_dates,
        "success_count": success_count,
        "failed_count": failed_count,
        "total_records": total_records,
        "failed_dates": failed_dates,
        "total_time": total_time
    }


def main():
    parser = argparse.ArgumentParser(description='导入大型历史TXT文件')
    parser.add_argument('file_path', help='TXT文件路径')
    parser.add_argument('--encoding', default='utf-8', help='文件编码 (默认: utf-8)')
    parser.add_argument('--imported-by', default='script', help='导入者标识')
    parser.add_argument('--preview-only', action='store_true', help='仅预览，不导入')
    parser.add_argument('--yes', '-y', action='store_true', help='自动确认导入，不询问')
    parser.add_argument('--quiet', '-q', action='store_true', help='静默模式，减少输出信息')
    parser.add_argument('--ignore-errors', action='store_true', help='忽略数据格式错误，继续处理')

    args = parser.parse_args()

    # 检查文件是否存在
    if not os.path.exists(args.file_path):
        print(f"❌ 文件不存在: {args.file_path}")
        return 1

    print(f"🚀 大文件历史数据导入工具")
    print(f"📁 文件: {args.file_path}")
    print(f"🔤 编码: {args.encoding}")
    print(f"👤 导入者: {args.imported_by}")
    print(f"={'='*50}")

    try:
        # 解析文件
        date_groups = parse_large_txt_by_date(args.file_path, args.encoding, args.quiet, args.ignore_errors)

        if not date_groups:
            print("❌ 未找到有效数据")
            return 1

        # 显示预览信息
        print(f"\n📋 数据预览:")
        for date_str in sorted(list(date_groups.keys())[:10]):  # 显示前10个日期
            count = len(date_groups[date_str])
            print(f"   {date_str}: {count:,} 条记录")

        if len(date_groups) > 10:
            print(f"   ... 还有 {len(date_groups) - 10} 个日期")

        if args.preview_only:
            print("\n👀 预览模式，不执行导入")
            return 0

        # 确认导入
        if args.yes:
            print(f"\n✅ 自动确认导入 {len(date_groups)} 个日期的数据")
        else:
            response = input(f"\n❓ 确认导入 {len(date_groups)} 个日期的数据吗? (y/N): ")
            if response.lower() != 'y':
                print("❌ 取消导入")
                return 0

        # 执行导入
        result = import_date_groups(date_groups, args.imported_by, args.quiet)

        if result["failed_count"] > 0:
            return 1

        return 0

    except KeyboardInterrupt:
        print("\n⚠️  用户中断")
        return 1
    except Exception as e:
        print(f"\n❌ 执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())