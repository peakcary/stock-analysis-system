# TXT文件处理器架构设计

## 概述

这是一个基于**策略模式（Strategy Pattern）**和**工厂模式（Factory Pattern）**的可扩展TXT文件处理架构，专为处理多种格式的股票交易数据文件而设计。

## 设计原则

### 1. 开闭原则（Open-Closed Principle）
- 对扩展开放：可以轻松添加新的文件格式处理器
- 对修改封闭：现有代码无需修改即可支持新格式

### 2. 单一职责原则
- 每个处理器只负责一种特定的文件格式
- 工厂类只负责处理器的管理和选择
- 基类定义统一的接口和通用功能

### 3. 策略模式
- 将不同的文件解析算法封装成独立的策略类
- 运行时动态选择最合适的处理策略

## 架构组件

### 1. 基础类 (`base_processor.py`)

```python
# 数据结构
@dataclass
class TradingRecord:
    stock_code: str              # 股票代码
    original_stock_code: str     # 原始股票代码
    normalized_stock_code: str   # 标准化股票代码
    trading_date: date           # 交易日期
    trading_volume: float        # 交易量
    extra_fields: Dict[str, Any] # 扩展字段

@dataclass
class ProcessResult:
    success: bool                # 处理是否成功
    message: str                 # 处理消息
    records: List[TradingRecord] # 处理后的记录
    total_count: int             # 总记录数
    valid_count: int             # 有效记录数
    error_count: int             # 错误记录数
    warnings: List[str]          # 警告信息

# 抽象基类
class BaseTxtProcessor(ABC):
    @abstractmethod
    def can_process(self, content: str, filename: str = None) -> Tuple[bool, float]:
        """判断是否可以处理该文件，返回(是否可处理, 置信度)"""

    @abstractmethod
    def parse_content(self, content: str, **kwargs) -> ProcessResult:
        """解析文件内容"""

    @abstractmethod
    def get_date_from_content(self, content: str) -> Optional[date]:
        """从内容中提取日期信息"""
```

### 2. 具体处理器

#### 标准处理器 (`standard_processor.py`)
- **格式**: `股票代码\t日期\t交易量`
- **特征**: Tab分隔，固定三列，单一日期
- **适用**: 日常单日交易数据文件

#### 历史处理器 (`historical_processor.py`)
- **格式**: `股票代码\t日期\t交易量`
- **特征**: Tab分隔，包含多个交易日期，大文件
- **适用**: 历史批量数据导入

#### CSV样式处理器 (`csv_like_processor.py`)
- **格式**: `股票代码,股票名称,日期,交易量,成交额,涨跌幅`
- **特征**: 逗号分隔，支持扩展字段，智能字段映射
- **适用**: CSV格式或类CSV格式的交易数据

### 3. 处理器工厂 (`processor_factory.py`)

```python
class TxtProcessorFactory:
    def get_best_processor(self, content: str, filename: str = None) -> Optional[BaseTxtProcessor]:
        """自动选择最合适的处理器"""

    def register_processor(self, processor: BaseTxtProcessor):
        """注册新处理器"""

    def list_processors(self) -> List[Dict[str, str]]:
        """列出所有处理器"""
```

## 使用方法

### 1. 基本使用

```python
from processor_factory import get_processor_factory

# 获取工厂实例
factory = get_processor_factory()

# 自动选择处理器
processor = factory.get_best_processor(file_content, filename)

if processor:
    result = processor.parse_content(file_content)
    print(f"处理成功: {result.success}")
    print(f"有效记录: {result.valid_count}")
```

### 2. 添加新的文件格式

#### 步骤1: 创建新处理器

```python
class XmlTxtProcessor(BaseTxtProcessor):
    def __init__(self):
        super().__init__(
            processor_type="xml_txt",
            description="XML格式TXT文件处理器"
        )

    def can_process(self, content: str, filename: str = None) -> Tuple[bool, float]:
        # 实现格式检测逻辑
        pass

    def parse_content(self, content: str, **kwargs) -> ProcessResult:
        # 实现解析逻辑
        pass

    def get_date_from_content(self, content: str) -> Optional[date]:
        # 实现日期提取逻辑
        pass
```

#### 步骤2: 注册到工厂

```python
from processor_factory import get_processor_factory

factory = get_processor_factory()
factory.register_processor(XmlTxtProcessor())
```

### 3. 处理器选择机制

工厂会自动测试所有注册的处理器，选择置信度最高的处理器：

1. **格式检测**: 每个处理器分析文件内容，返回置信度(0-1)
2. **最佳匹配**: 选择置信度最高且超过阈值的处理器
3. **智能选择**: 结合文件名提示进行更准确的判断

## 扩展能力

### 1. 支持的扩展类型
- **新的文件格式**: JSON、XML、固定宽度等
- **新的字段类型**: 价格、成交额、技术指标等
- **新的验证规则**: 行业特定的数据验证
- **新的后处理逻辑**: 数据清洗、格式转换等

### 2. 扩展示例

```python
# 支持Excel导出格式的TXT文件
class ExcelTxtProcessor(BaseTxtProcessor):
    # 实现Excel特有的格式解析

# 支持期货数据格式
class FuturesTxtProcessor(BaseTxtProcessor):
    # 实现期货特有的字段和验证

# 支持国际市场数据格式
class InternationalTxtProcessor(BaseTxtProcessor):
    # 实现多时区、多货币的处理
```

## 优势

### 1. 可维护性
- 每个处理器独立，修改不影响其他组件
- 统一的接口使得代码易于理解和维护

### 2. 可扩展性
- 添加新格式只需实现新的处理器类
- 无需修改现有代码，符合开闭原则

### 3. 可测试性
- 每个处理器可以独立测试
- 明确的输入输出接口便于编写单元测试

### 4. 性能优化
- 智能的格式检测避免不必要的解析尝试
- 大文件处理器专门优化内存使用

## 最佳实践

### 1. 处理器开发
- 优先检测最有辨识度的特征
- 使用合理的置信度评分
- 提供详细的错误信息和警告

### 2. 错误处理
- 优雅降级：一个处理器失败不影响其他处理器
- 详细日志：记录格式检测和解析过程
- 用户友好：提供可理解的错误消息

### 3. 性能考虑
- 限制格式检测的数据量（通常前几行即可）
- 对大文件实现流式处理
- 合理的内存使用和垃圾回收

这个架构为您的股票分析系统提供了一个坚实、灵活的文件处理基础，可以轻松适应未来的格式变化和业务需求。