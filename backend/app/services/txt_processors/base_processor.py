"""
TXT文件处理器基类
定义了统一的处理接口和通用方法
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)


@dataclass
class TradingRecord:
    """标准化的交易记录数据结构"""
    stock_code: str
    original_stock_code: str
    normalized_stock_code: str
    trading_date: date
    trading_volume: float
    # 可扩展字段
    extra_fields: Dict[str, Any] = None

    def __post_init__(self):
        if self.extra_fields is None:
            self.extra_fields = {}


@dataclass
class ProcessResult:
    """处理结果数据结构"""
    success: bool
    message: str
    records: List[TradingRecord] = None
    total_count: int = 0
    valid_count: int = 0
    error_count: int = 0
    warnings: List[str] = None
    trading_date: Optional[date] = None

    def __post_init__(self):
        if self.records is None:
            self.records = []
        if self.warnings is None:
            self.warnings = []


class BaseTxtProcessor(ABC):
    """TXT文件处理器基类"""

    def __init__(self, processor_type: str, description: str):
        self.processor_type = processor_type
        self.description = description
        self.logger = logging.getLogger(f"{__name__}.{processor_type}")

    @abstractmethod
    def can_process(self, content: str, filename: str = None) -> Tuple[bool, float]:
        """
        判断是否可以处理该文件

        Args:
            content: 文件内容
            filename: 文件名（可选）

        Returns:
            Tuple[bool, float]: (是否可以处理, 置信度 0-1)
        """
        pass

    @abstractmethod
    def parse_content(self, content: str, **kwargs) -> ProcessResult:
        """
        解析文件内容

        Args:
            content: 文件内容
            **kwargs: 额外参数

        Returns:
            ProcessResult: 处理结果
        """
        pass

    @abstractmethod
    def get_date_from_content(self, content: str) -> Optional[date]:
        """
        从内容中提取日期信息

        Args:
            content: 文件内容

        Returns:
            Optional[date]: 提取到的日期，None表示无法确定
        """
        pass

    def validate_record(self, record: TradingRecord) -> Tuple[bool, str]:
        """
        验证交易记录的有效性

        Args:
            record: 交易记录

        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        try:
            # 基础验证
            if not record.stock_code or not record.stock_code.strip():
                return False, "股票代码为空"

            if not record.trading_date:
                return False, "交易日期为空"

            if record.trading_volume < 0:
                return False, "交易量不能为负数"

            # 日期合理性检查
            if record.trading_date > date.today():
                return False, "交易日期不能是未来日期"

            min_date = date(1990, 1, 1)  # 中国股市开始时间
            if record.trading_date < min_date:
                return False, f"交易日期不能早于{min_date}"

            return True, ""

        except Exception as e:
            return False, f"验证时发生错误: {str(e)}"

    def normalize_stock_code(self, original_code: str) -> Dict[str, str]:
        """
        标准化股票代码

        Args:
            original_code: 原始股票代码

        Returns:
            Dict: 包含original, normalized, prefix等信息
        """
        original = original_code.strip().upper()

        # 提取前缀和标准化代码
        if original.startswith('SH'):
            return {
                'original': original,
                'normalized': original[2:],
                'prefix': 'SH'
            }
        elif original.startswith('SZ'):
            return {
                'original': original,
                'normalized': original[2:],
                'prefix': 'SZ'
            }
        else:
            # 无前缀情况
            return {
                'original': original,
                'normalized': original,
                'prefix': ''
            }

    def get_processor_info(self) -> Dict[str, str]:
        """获取处理器信息"""
        return {
            'type': self.processor_type,
            'description': self.description,
            'class': self.__class__.__name__
        }