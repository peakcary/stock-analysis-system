"""
CSV样式TXT文件处理器
处理逗号分隔的TXT文件，支持更多字段
格式: 股票代码,股票名称,日期,交易量,成交额,涨跌幅
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, date
from .base_processor import BaseTxtProcessor, TradingRecord, ProcessResult


class CsvLikeTxtProcessor(BaseTxtProcessor):
    """CSV样式TXT文件处理器"""

    def __init__(self):
        super().__init__(
            processor_type="csv_like",
            description="CSV样式TXT文件处理器 (逗号分隔，支持扩展字段)"
        )

    def can_process(self, content: str, filename: str = None) -> Tuple[bool, float]:
        """
        判断是否为CSV样式TXT文件

        特征:
        - 逗号分隔
        - 至少包含: 股票代码,日期,交易量
        - 可能包含更多字段如股票名称、成交额等
        """
        try:
            lines = content.strip().split('\n')
            if not lines:
                return False, 0.0

            valid_lines = 0
            total_lines = 0

            # 检查前10行
            sample_lines = lines[:min(10, len(lines))]

            for line in sample_lines:
                line = line.strip()
                if not line:
                    continue

                total_lines += 1
                parts = [p.strip() for p in line.split(',')]

                # CSV样式至少要有3个字段
                if len(parts) >= 3:
                    # 尝试识别股票代码、日期、数字字段
                    stock_code_found = False
                    date_found = False
                    number_found = False

                    for part in parts:
                        if self._is_valid_stock_code(part):
                            stock_code_found = True
                        elif self._is_valid_date_format(part):
                            date_found = True
                        elif self._is_numeric(part):
                            number_found = True

                    if stock_code_found and date_found and number_found:
                        valid_lines += 1

            if total_lines == 0:
                return False, 0.0

            confidence = valid_lines / total_lines
            can_process = confidence >= 0.7  # 70%以上匹配度

            # 文件名提示
            if filename and ('.csv' in filename.lower() or 'csv' in filename.lower()):
                confidence = min(0.95, confidence + 0.1)

            return can_process, confidence

        except Exception as e:
            self.logger.error(f"检查CSV样式文件格式时出错: {e}")
            return False, 0.0

    def parse_content(self, content: str, **kwargs) -> ProcessResult:
        """解析CSV样式TXT内容"""
        try:
            lines = content.strip().split('\n')
            records = []
            total_count = 0
            valid_count = 0
            error_count = 0
            warnings = []

            # 尝试检测字段顺序
            field_mapping = self._detect_field_mapping(lines[:5])

            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line:
                    continue

                total_count += 1

                try:
                    parts = [p.strip() for p in line.split(',')]

                    if len(parts) < 3:
                        error_count += 1
                        warnings.append(f"第{line_num}行字段数量不足")
                        continue

                    # 根据字段映射提取数据
                    try:
                        stock_code = parts[field_mapping['stock_code']]
                        date_str = parts[field_mapping['date']]
                        volume_str = parts[field_mapping['volume']]
                    except (IndexError, KeyError):
                        error_count += 1
                        warnings.append(f"第{line_num}行字段映射错误")
                        continue

                    # 解析日期
                    try:
                        # 支持多种日期格式
                        trading_date = self._parse_date(date_str)
                    except ValueError:
                        error_count += 1
                        warnings.append(f"第{line_num}行日期格式错误: {date_str}")
                        continue

                    # 解析交易量
                    try:
                        trading_volume = float(volume_str.replace(',', ''))  # 移除千分位逗号
                    except ValueError:
                        error_count += 1
                        warnings.append(f"第{line_num}行交易量格式错误: {volume_str}")
                        continue

                    # 标准化股票代码
                    code_info = self.normalize_stock_code(stock_code)

                    # 提取额外字段
                    extra_fields = {}
                    if 'stock_name' in field_mapping and field_mapping['stock_name'] < len(parts):
                        extra_fields['stock_name'] = parts[field_mapping['stock_name']]
                    if 'amount' in field_mapping and field_mapping['amount'] < len(parts):
                        try:
                            extra_fields['amount'] = float(parts[field_mapping['amount']].replace(',', ''))
                        except ValueError:
                            pass
                    if 'change_percent' in field_mapping and field_mapping['change_percent'] < len(parts):
                        try:
                            extra_fields['change_percent'] = float(parts[field_mapping['change_percent']].replace('%', ''))
                        except ValueError:
                            pass

                    # 创建交易记录
                    record = TradingRecord(
                        stock_code=code_info['normalized'],
                        original_stock_code=code_info['original'],
                        normalized_stock_code=code_info['normalized'],
                        trading_date=trading_date,
                        trading_volume=trading_volume,
                        extra_fields=extra_fields
                    )

                    # 验证记录
                    is_valid, error_msg = self.validate_record(record)
                    if not is_valid:
                        error_count += 1
                        warnings.append(f"第{line_num}行数据验证失败: {error_msg}")
                        continue

                    records.append(record)
                    valid_count += 1

                except Exception as e:
                    error_count += 1
                    warnings.append(f"第{line_num}行处理时出错: {str(e)}")

            # 生成结果
            success = valid_count > 0
            message = f"CSV样式文件处理完成: 总行数 {total_count}, 有效 {valid_count}, 错误 {error_count}"

            return ProcessResult(
                success=success,
                message=message,
                records=records,
                total_count=total_count,
                valid_count=valid_count,
                error_count=error_count,
                warnings=warnings[:10]
            )

        except Exception as e:
            self.logger.error(f"解析CSV样式内容时出错: {e}")
            return ProcessResult(
                success=False,
                message=f"CSV样式文件解析失败: {str(e)}"
            )

    def get_date_from_content(self, content: str) -> Optional[date]:
        """从内容中提取日期信息"""
        try:
            lines = content.strip().split('\n')
            field_mapping = self._detect_field_mapping(lines[:5])

            for line in lines[:5]:
                line = line.strip()
                if not line:
                    continue

                parts = [p.strip() for p in line.split(',')]
                if len(parts) > field_mapping.get('date', 999):
                    date_str = parts[field_mapping['date']]
                    try:
                        return self._parse_date(date_str)
                    except ValueError:
                        continue

            return None

        except Exception:
            return None

    def _detect_field_mapping(self, sample_lines: List[str]) -> Dict[str, int]:
        """
        检测字段映射关系

        Returns:
            Dict[str, int]: 字段名到列索引的映射
        """
        mapping = {'stock_code': 0, 'date': 1, 'volume': 2}  # 默认映射

        try:
            for line in sample_lines:
                line = line.strip()
                if not line:
                    continue

                parts = [p.strip() for p in line.split(',')]
                if len(parts) < 3:
                    continue

                # 尝试识别各字段位置
                for i, part in enumerate(parts):
                    if self._is_valid_stock_code(part):
                        mapping['stock_code'] = i
                    elif self._is_valid_date_format(part):
                        mapping['date'] = i
                    elif self._is_numeric(part) and float(part.replace(',', '')) > 1000:  # 可能是交易量
                        if 'volume' not in mapping or i == 2:  # 优先使用第3列作为交易量
                            mapping['volume'] = i

                # 尝试识别可选字段
                if len(parts) > 3:
                    for i, part in enumerate(parts):
                        if i not in mapping.values():
                            if self._looks_like_stock_name(part):
                                mapping['stock_name'] = i
                            elif self._is_numeric(part):
                                if 'amount' not in mapping:
                                    mapping['amount'] = i

                break  # 只分析第一行有效数据

        except Exception as e:
            self.logger.error(f"检测字段映射时出错: {e}")

        return mapping

    def _parse_date(self, date_str: str) -> date:
        """解析多种日期格式"""
        date_str = date_str.strip()

        # 尝试多种日期格式
        formats = [
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%Y.%m.%d',
            '%Y年%m月%d日',
            '%m/%d/%Y',
            '%d/%m/%Y'
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue

        raise ValueError(f"无法解析日期格式: {date_str}")

    def _is_valid_stock_code(self, stock_code: str) -> bool:
        """验证股票代码格式"""
        if not stock_code:
            return False

        stock_code = stock_code.strip().upper()
        patterns = [
            r'^SH\d{6}$',
            r'^SZ\d{6}$',
            r'^\d{6}$',
        ]
        return any(re.match(pattern, stock_code) for pattern in patterns)

    def _is_valid_date_format(self, date_str: str) -> bool:
        """验证日期格式"""
        try:
            self._parse_date(date_str)
            return True
        except ValueError:
            return False

    def _is_numeric(self, value: str) -> bool:
        """检查是否为数字"""
        try:
            float(value.replace(',', '').replace('%', ''))
            return True
        except ValueError:
            return False

    def _looks_like_stock_name(self, name: str) -> bool:
        """判断是否看起来像股票名称"""
        if not name or len(name) < 2:
            return False

        # 中文字符或常见股票名称特征
        chinese_pattern = r'[\u4e00-\u9fff]'
        has_chinese = bool(re.search(chinese_pattern, name))

        # 常见股票名称后缀
        stock_suffixes = ['科技', '股份', '集团', '有限', '发展', '控股', '银行', '保险']
        has_suffix = any(suffix in name for suffix in stock_suffixes)

        return has_chinese or has_suffix