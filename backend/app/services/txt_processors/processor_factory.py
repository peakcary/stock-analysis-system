"""
TXT文件处理器工厂
负责自动选择合适的处理器处理不同格式的文件
"""

from typing import List, Optional, Tuple, Type, Dict
import logging
from .base_processor import BaseTxtProcessor
from .standard_processor import StandardTxtProcessor
from .historical_processor import HistoricalTxtProcessor
from .csv_like_processor import CsvLikeTxtProcessor

logger = logging.getLogger(__name__)


class TxtProcessorFactory:
    """TXT文件处理器工厂"""

    def __init__(self):
        self._processors: List[BaseTxtProcessor] = []
        self._register_default_processors()

    def _register_default_processors(self):
        """注册默认的处理器"""
        self.register_processor(StandardTxtProcessor())
        self.register_processor(HistoricalTxtProcessor())
        self.register_processor(CsvLikeTxtProcessor())

    def register_processor(self, processor: BaseTxtProcessor):
        """
        注册新的处理器

        Args:
            processor: 处理器实例
        """
        if not isinstance(processor, BaseTxtProcessor):
            raise ValueError("处理器必须继承自BaseTxtProcessor")

        # 检查是否已存在相同类型的处理器
        existing_types = [p.processor_type for p in self._processors]
        if processor.processor_type in existing_types:
            logger.warning(f"处理器类型 '{processor.processor_type}' 已存在，将替换现有处理器")
            self._processors = [p for p in self._processors if p.processor_type != processor.processor_type]

        self._processors.append(processor)
        logger.info(f"注册处理器: {processor.processor_type} - {processor.description}")

    def get_best_processor(self, content: str, filename: str = None) -> Optional[BaseTxtProcessor]:
        """
        根据内容自动选择最合适的处理器

        Args:
            content: 文件内容
            filename: 文件名（可选）

        Returns:
            Optional[BaseTxtProcessor]: 最适合的处理器，None表示没有合适的处理器
        """
        if not content.strip():
            return None

        best_processor = None
        best_confidence = 0.0
        processor_scores = []

        # 测试所有处理器
        for processor in self._processors:
            try:
                can_process, confidence = processor.can_process(content, filename)
                processor_scores.append({
                    'processor': processor,
                    'confidence': confidence,
                    'can_process': can_process
                })

                if can_process and confidence > best_confidence:
                    best_processor = processor
                    best_confidence = confidence

            except Exception as e:
                logger.error(f"测试处理器 {processor.processor_type} 时出错: {e}")

        # 记录处理器选择过程
        if logger.isEnabledFor(logging.DEBUG):
            for score in processor_scores:
                logger.debug(
                    f"处理器 {score['processor'].processor_type}: "
                    f"可处理={score['can_process']}, 置信度={score['confidence']:.2f}"
                )

        if best_processor:
            logger.info(f"选择处理器: {best_processor.processor_type} (置信度: {best_confidence:.2f})")
        else:
            logger.warning("未找到合适的处理器")

        return best_processor

    def get_processor_by_type(self, processor_type: str) -> Optional[BaseTxtProcessor]:
        """
        根据类型获取处理器

        Args:
            processor_type: 处理器类型

        Returns:
            Optional[BaseTxtProcessor]: 指定类型的处理器
        """
        for processor in self._processors:
            if processor.processor_type == processor_type:
                return processor
        return None

    def list_processors(self) -> List[Dict[str, str]]:
        """
        列出所有注册的处理器

        Returns:
            List[Dict]: 处理器信息列表
        """
        return [processor.get_processor_info() for processor in self._processors]

    def unregister_processor(self, processor_type: str) -> bool:
        """
        注销处理器

        Args:
            processor_type: 处理器类型

        Returns:
            bool: 是否成功注销
        """
        original_count = len(self._processors)
        self._processors = [p for p in self._processors if p.processor_type != processor_type]

        if len(self._processors) < original_count:
            logger.info(f"注销处理器: {processor_type}")
            return True
        return False


# 全局处理器工厂实例
_processor_factory = None


def get_processor_factory() -> TxtProcessorFactory:
    """获取全局处理器工厂实例"""
    global _processor_factory
    if _processor_factory is None:
        _processor_factory = TxtProcessorFactory()
    return _processor_factory


def register_custom_processor(processor: BaseTxtProcessor):
    """
    注册自定义处理器的便捷方法

    Args:
        processor: 自定义处理器实例
    """
    factory = get_processor_factory()
    factory.register_processor(processor)