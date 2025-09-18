"""
TXT文件处理器使用示例
演示如何使用新的处理器架构来处理不同格式的TXT文件
"""

from processor_factory import get_processor_factory
from typing import Optional


def process_txt_file(file_content: str, filename: str = None) -> dict:
    """
    自动检测并处理TXT文件

    Args:
        file_content: 文件内容
        filename: 文件名（可选）

    Returns:
        dict: 处理结果
    """
    # 获取处理器工厂
    factory = get_processor_factory()

    # 自动选择最合适的处理器
    processor = factory.get_best_processor(file_content, filename)

    if not processor:
        return {
            'success': False,
            'message': '没有找到合适的处理器',
            'available_processors': factory.list_processors()
        }

    # 使用选择的处理器处理文件
    result = processor.parse_content(file_content)

    return {
        'success': result.success,
        'message': result.message,
        'processor_used': processor.processor_type,
        'total_count': result.total_count,
        'valid_count': result.valid_count,
        'error_count': result.error_count,
        'warnings': result.warnings,
        'records': [
            {
                'stock_code': record.stock_code,
                'trading_date': record.trading_date.isoformat(),
                'trading_volume': record.trading_volume,
                'extra_fields': record.extra_fields
            }
            for record in result.records[:10]  # 只返回前10条作为示例
        ]
    }


def add_custom_processor_example():
    """演示如何添加自定义处理器"""
    from base_processor import BaseTxtProcessor, ProcessResult, TradingRecord
    from typing import Tuple
    from datetime import datetime

    class JsonTxtProcessor(BaseTxtProcessor):
        """JSON格式TXT文件处理器示例"""

        def __init__(self):
            super().__init__(
                processor_type="json_txt",
                description="JSON格式TXT文件处理器"
            )

        def can_process(self, content: str, filename: str = None) -> Tuple[bool, float]:
            """检查是否为JSON格式"""
            try:
                import json
                lines = content.strip().split('\n')
                valid_lines = 0

                for line in lines[:5]:  # 检查前5行
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        if all(key in data for key in ['stock_code', 'date', 'volume']):
                            valid_lines += 1
                    except json.JSONDecodeError:
                        pass

                confidence = valid_lines / min(5, len([l for l in lines if l.strip()]))
                return confidence >= 0.8, confidence

            except Exception:
                return False, 0.0

        def parse_content(self, content: str, **kwargs) -> ProcessResult:
            """解析JSON格式内容"""
            try:
                import json
                lines = content.strip().split('\n')
                records = []
                valid_count = 0
                error_count = 0
                warnings = []

                for line_num, line in enumerate(lines, 1):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        data = json.loads(line)

                        # 创建交易记录
                        record = TradingRecord(
                            stock_code=data['stock_code'],
                            original_stock_code=data['stock_code'],
                            normalized_stock_code=self.normalize_stock_code(data['stock_code'])['normalized'],
                            trading_date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
                            trading_volume=float(data['volume']),
                            extra_fields=data.get('extra', {})
                        )

                        is_valid, error_msg = self.validate_record(record)
                        if is_valid:
                            records.append(record)
                            valid_count += 1
                        else:
                            error_count += 1
                            warnings.append(f"第{line_num}行验证失败: {error_msg}")

                    except Exception as e:
                        error_count += 1
                        warnings.append(f"第{line_num}行解析错误: {str(e)}")

                return ProcessResult(
                    success=valid_count > 0,
                    message=f"JSON格式处理完成: 有效{valid_count}, 错误{error_count}",
                    records=records,
                    total_count=len(lines),
                    valid_count=valid_count,
                    error_count=error_count,
                    warnings=warnings[:10]
                )

            except Exception as e:
                return ProcessResult(
                    success=False,
                    message=f"JSON格式解析失败: {str(e)}"
                )

        def get_date_from_content(self, content: str) -> Optional[date]:
            """从JSON内容中提取日期"""
            try:
                import json
                lines = content.strip().split('\n')

                for line in lines[:5]:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        if 'date' in data:
                            return datetime.strptime(data['date'], '%Y-%m-%d').date()
                    except:
                        continue

                return None
            except:
                return None

    # 注册自定义处理器
    factory = get_processor_factory()
    custom_processor = JsonTxtProcessor()
    factory.register_processor(custom_processor)

    print(f"已注册自定义处理器: {custom_processor.processor_type}")
    print("当前所有处理器:")
    for proc_info in factory.list_processors():
        print(f"  - {proc_info['type']}: {proc_info['description']}")


def list_all_processors():
    """列出所有可用的处理器"""
    factory = get_processor_factory()
    processors = factory.list_processors()

    print("可用的TXT文件处理器:")
    for proc in processors:
        print(f"类型: {proc['type']}")
        print(f"描述: {proc['description']}")
        print(f"类名: {proc['class']}")
        print("-" * 40)


if __name__ == "__main__":
    # 演示基本用法
    print("=== TXT文件处理器架构演示 ===\n")

    # 列出默认处理器
    list_all_processors()

    # 测试标准格式
    print("\n=== 测试标准格式 ===")
    standard_content = "SH000001\t2024-01-01\t123456.0\nSZ000002\t2024-01-01\t234567.0"
    result = process_txt_file(standard_content, "standard.txt")
    print(f"处理结果: {result['success']}")
    print(f"使用处理器: {result['processor_used']}")
    print(f"有效记录: {result['valid_count']}")

    # 测试CSV样式格式
    print("\n=== 测试CSV样式格式 ===")
    csv_content = "SH000001,平安银行,2024-01-01,123456.0,999999.0,2.5%\nSZ000002,万科A,2024-01-01,234567.0,888888.0,-1.2%"
    result = process_txt_file(csv_content, "data.csv")
    print(f"处理结果: {result['success']}")
    print(f"使用处理器: {result['processor_used']}")
    print(f"有效记录: {result['valid_count']}")

    # 演示添加自定义处理器
    print("\n=== 添加自定义处理器 ===")
    add_custom_processor_example()