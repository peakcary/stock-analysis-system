"""
历史多日期TXT文件处理器
处理包含多个日期数据的大型文件
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, date
from collections import defaultdict
from .base_processor import BaseTxtProcessor, TradingRecord, ProcessResult


class HistoricalTxtProcessor(BaseTxtProcessor):
    """历史多日期TXT文件处理器"""

    def __init__(self):
        super().__init__(
            processor_type="historical",
            description="历史多日期TXT文件处理器 (包含多个交易日期的大型文件)"
        )

    def can_process(self, content: str, filename: str = None) -> Tuple[bool, float]:
        """
        判断是否为历史多日期格式文件

        特征:
        - 包含多个不同的交易日期
        - 日期跨度较大（超过1天）
        - 文件较大（通常超过1000行）
        """
        try:
            lines = content.strip().split('\n')
            if len(lines) < 100:  # 历史文件通常比较大
                return False, 0.0

            # 检查前100行，查找日期分布
            dates_found = set()
            valid_lines = 0
            total_checked = 0

            sample_lines = lines[:min(100, len(lines))]

            for line in sample_lines:
                line = line.strip()
                if not line:
                    continue

                total_checked += 1
                parts = line.split('\t')

                if len(parts) == 3:
                    stock_code, date_str, volume_str = parts

                    try:
                        # 验证日期格式并收集
                        trading_date = datetime.strptime(date_str.strip(), '%Y-%m-%d').date()
                        dates_found.add(trading_date)
                        valid_lines += 1
                    except ValueError:
                        continue

            if total_checked == 0:
                return False, 0.0

            # 计算置信度
            format_confidence = valid_lines / total_checked if total_checked > 0 else 0

            # 如果格式匹配度不够，不是历史文件
            if format_confidence < 0.8:
                return False, format_confidence

            # 判断是否是多日期文件
            unique_dates = len(dates_found)

            # 文件名提示
            filename_hint = False
            if filename:
                filename_lower = filename.lower()
                historical_keywords = ['历史', 'history', 'multi', '批量', 'large']
                filename_hint = any(keyword in filename_lower for keyword in historical_keywords)

            # 综合判断
            if unique_dates >= 3:  # 包含3个或以上不同日期
                confidence = min(0.9, format_confidence + 0.1)
            elif unique_dates >= 2:  # 包含2个不同日期
                confidence = format_confidence
            elif filename_hint:  # 文件名提示是历史文件
                confidence = format_confidence * 0.8
            else:
                confidence = format_confidence * 0.3  # 可能是单日期文件

            can_process = confidence >= 0.7

            return can_process, confidence

        except Exception as e:
            self.logger.error(f"检查历史文件格式时出错: {e}")
            return False, 0.0

    def parse_content(self, content: str, **kwargs) -> ProcessResult:
        """解析历史多日期TXT内容"""
        try:
            lines = content.strip().split('\n')
            records = []
            total_count = 0
            valid_count = 0
            error_count = 0
            warnings = []
            date_groups = defaultdict(int)  # 统计每个日期的记录数

            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line:
                    continue

                total_count += 1

                # 进度提示（每10000行）
                if total_count % 10000 == 0:
                    self.logger.info(f"已处理 {total_count} 行...")

                try:
                    parts = line.split('\t')
                    if len(parts) != 3:
                        error_count += 1
                        if len(warnings) < 10:  # 限制警告数量
                            warnings.append(f"第{line_num}行格式错误: 字段数量不是3个")
                        continue

                    stock_code, date_str, volume_str = parts

                    # 解析日期
                    try:
                        trading_date = datetime.strptime(date_str.strip(), '%Y-%m-%d').date()
                        date_groups[trading_date] += 1
                    except ValueError:
                        error_count += 1
                        if len(warnings) < 10:
                            warnings.append(f"第{line_num}行日期格式错误: {date_str}")
                        continue

                    # 解析交易量
                    try:
                        trading_volume = float(volume_str.strip())
                    except ValueError:
                        error_count += 1
                        if len(warnings) < 10:
                            warnings.append(f"第{line_num}行交易量格式错误: {volume_str}")
                        continue

                    # 标准化股票代码
                    code_info = self.normalize_stock_code(stock_code.strip())

                    # 创建交易记录
                    record = TradingRecord(
                        stock_code=code_info['normalized'],
                        original_stock_code=code_info['original'],
                        normalized_stock_code=code_info['normalized'],
                        trading_date=trading_date,
                        trading_volume=trading_volume,
                        extra_fields={
                            'line_number': line_num,
                            'processor_type': 'historical'
                        }
                    )

                    # 验证记录
                    is_valid, error_msg = self.validate_record(record)
                    if not is_valid:
                        error_count += 1
                        if len(warnings) < 10:
                            warnings.append(f"第{line_num}行数据验证失败: {error_msg}")
                        continue

                    records.append(record)
                    valid_count += 1

                except Exception as e:
                    error_count += 1
                    if len(warnings) < 10:
                        warnings.append(f"第{line_num}行处理时出错: {str(e)}")

            # 生成统计信息
            unique_dates = len(date_groups)
            date_range = ""
            if date_groups:
                min_date = min(date_groups.keys())
                max_date = max(date_groups.keys())
                date_range = f"从 {min_date} 到 {max_date}"

            # 生成结果
            success = valid_count > 0
            message = f"历史文件处理完成: 总行数 {total_count}, 有效 {valid_count}, 错误 {error_count}, 包含 {unique_dates} 个交易日 {date_range}"

            result = ProcessResult(
                success=success,
                message=message,
                records=records,
                total_count=total_count,
                valid_count=valid_count,
                error_count=error_count,
                warnings=warnings
            )

            # 添加额外的统计信息
            result.extra_info = {
                'unique_dates': unique_dates,
                'date_distribution': dict(sorted(date_groups.items())),
                'file_type': 'historical_multi_date'
            }

            return result

        except Exception as e:
            self.logger.error(f"解析历史文件内容时出错: {e}")
            return ProcessResult(
                success=False,
                message=f"历史文件解析失败: {str(e)}"
            )

    def get_date_from_content(self, content: str) -> Optional[date]:
        """
        从内容中提取日期信息（历史文件返回None，表示包含多个日期）
        """
        # 历史文件包含多个日期，返回None表示无法确定单一日期
        return None

    def get_date_groups(self, content: str) -> Dict[date, List[str]]:
        """
        按日期分组返回数据行

        Returns:
            Dict[date, List[str]]: 日期到数据行的映射
        """
        date_groups = defaultdict(list)

        try:
            lines = content.strip().split('\n')

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                parts = line.split('\t')
                if len(parts) == 3:
                    stock_code, date_str, volume_str = parts

                    try:
                        trading_date = datetime.strptime(date_str.strip(), '%Y-%m-%d').date()
                        date_groups[trading_date].append(line)
                    except ValueError:
                        continue

        except Exception as e:
            self.logger.error(f"分组日期时出错: {e}")

        return dict(date_groups)