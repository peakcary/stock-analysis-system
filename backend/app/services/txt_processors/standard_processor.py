"""
标准TXT文件处理器
处理标准格式: 股票代码\t日期\t交易量
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, date
from .base_processor import BaseTxtProcessor, TradingRecord, ProcessResult


class StandardTxtProcessor(BaseTxtProcessor):
    """标准TXT文件处理器"""

    def __init__(self):
        super().__init__(
            processor_type="standard",
            description="标准格式TXT文件处理器 (股票代码\\t日期\\t交易量)"
        )

    def can_process(self, content: str, filename: str = None) -> Tuple[bool, float]:
        """
        判断是否为标准格式TXT文件

        标准格式特征:
        - 制表符分隔
        - 三列: 股票代码、日期、交易量
        - 日期格式: YYYY-MM-DD
        """
        try:
            lines = content.strip().split('\n')
            if not lines:
                return False, 0.0

            valid_lines = 0
            total_lines = 0

            # 检查前10行（或全部行如果少于10行）
            sample_lines = lines[:min(10, len(lines))]

            for line in sample_lines:
                line = line.strip()
                if not line:
                    continue

                total_lines += 1
                parts = line.split('\t')

                if len(parts) == 3:
                    stock_code, date_str, volume_str = parts

                    # 验证股票代码格式
                    if self._is_valid_stock_code(stock_code):
                        # 验证日期格式
                        if self._is_valid_date_format(date_str):
                            # 验证交易量格式
                            if self._is_valid_volume_format(volume_str):
                                valid_lines += 1

            if total_lines == 0:
                return False, 0.0

            confidence = valid_lines / total_lines
            can_process = confidence >= 0.8  # 80%以上匹配度才认为可以处理

            return can_process, confidence

        except Exception as e:
            self.logger.error(f"检查文件格式时出错: {e}")
            return False, 0.0

    def parse_content(self, content: str, **kwargs) -> ProcessResult:
        """解析标准格式TXT内容"""
        try:
            lines = content.strip().split('\n')
            records = []
            total_count = 0
            valid_count = 0
            error_count = 0
            warnings = []

            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line:
                    continue

                total_count += 1

                try:
                    parts = line.split('\t')
                    if len(parts) != 3:
                        error_count += 1
                        warnings.append(f"第{line_num}行格式错误: 字段数量不是3个")
                        continue

                    stock_code, date_str, volume_str = parts

                    # 解析日期
                    try:
                        trading_date = datetime.strptime(date_str.strip(), '%Y-%m-%d').date()
                    except ValueError:
                        error_count += 1
                        warnings.append(f"第{line_num}行日期格式错误: {date_str}")
                        continue

                    # 解析交易量
                    try:
                        trading_volume = float(volume_str.strip())
                    except ValueError:
                        error_count += 1
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
                        trading_volume=trading_volume
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

            # 获取交易日期（假设所有记录都是同一天）
            trading_date = None
            if records:
                trading_date = records[0].trading_date

            # 生成结果
            success = valid_count > 0
            message = f"处理完成: 总行数 {total_count}, 有效 {valid_count}, 错误 {error_count}"

            return ProcessResult(
                success=success,
                message=message,
                records=records,
                total_count=total_count,
                valid_count=valid_count,
                error_count=error_count,
                warnings=warnings[:10],  # 最多返回10个警告
                trading_date=trading_date
            )

        except Exception as e:
            self.logger.error(f"解析内容时出错: {e}")
            return ProcessResult(
                success=False,
                message=f"解析失败: {str(e)}"
            )

    def get_date_from_content(self, content: str) -> Optional[date]:
        """从内容中提取日期信息（标准格式通常是单日期）"""
        try:
            lines = content.strip().split('\n')

            for line in lines[:5]:  # 检查前5行
                line = line.strip()
                if not line:
                    continue

                parts = line.split('\t')
                if len(parts) >= 2:
                    date_str = parts[1].strip()
                    try:
                        return datetime.strptime(date_str, '%Y-%m-%d').date()
                    except ValueError:
                        continue

            return None

        except Exception:
            return None

    def _is_valid_stock_code(self, stock_code: str) -> bool:
        """验证股票代码格式"""
        if not stock_code:
            return False

        stock_code = stock_code.strip().upper()

        # 支持的格式: SH123456, SZ123456, 123456
        patterns = [
            r'^SH\d{6}$',  # 上海
            r'^SZ\d{6}$',  # 深圳
            r'^\d{6}$',    # 纯数字
        ]

        return any(re.match(pattern, stock_code) for pattern in patterns)

    def _is_valid_date_format(self, date_str: str) -> bool:
        """验证日期格式"""
        try:
            datetime.strptime(date_str.strip(), '%Y-%m-%d')
            return True
        except ValueError:
            return False

    def _is_valid_volume_format(self, volume_str: str) -> bool:
        """验证交易量格式"""
        try:
            float(volume_str.strip())
            return True
        except ValueError:
            return False