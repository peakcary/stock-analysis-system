# 统一时间序列数据导入框架实现总结

## 概述

完成了统一的时间序列数据导入和计算框架，支持 EEE.txt、TTV.txt 及未来扩展的其他数据源。该框架包含以下核心功能：

1. **统一导入处理器**：基于处理器模式，支持灵活扩展
2. **原始数据保留**：完整保存导入数据用于审计和重新计算
3. **统一汇总数据结构**：多指标类型支持
4. **排名和汇总计算框架**：支持多种聚合操作
5. **可重新计算的任务管理**：完整的版本管理和重试机制

---

## 实现的核心组件

### 1. 导入处理框架（timeseries_import_service.py）

**文件位置**：`app/services/timeseries_import_service.py`

#### 核心类

**TimeSeriesImportHandler（基类）**
- 抽象基类，定义所有导入处理器的接口
- 方法：
  - `parse_file()`：解析文件内容
  - `validate_record()`：验证单条记录
  - `save_raw_data()`：保存原始数据
  - `save_normalized_data()`：保存规范化数据
  - `normalize_stock_code()`：统一股票代码规范化逻辑

**EeeImportHandler（热度数据处理器）**
- 处理 EEE.txt 文件（热度数据）
- metric_type：'eee_heat'
- 特点：
  - 解析格式：`股票代码\t日期\t热度值`
  - 支持格式化的日期字符串（YYYY-MM-DD）
  - 验证热度值为非负浮点数
  - 数据保存到 DailyStockData 表的 heat_value 字段

**TtvImportHandler（交易量处理器）**
- 处理 TTV.txt 文件（交易量数据）
- metric_type：'ttv_trading_volume'
- 特点：
  - 解析格式：`股票代码\t日期\t交易量`
  - 格式与 EEE 相同，但含义不同
  - 数据保存到 DailyTrading 表

**TimeSeriesImportService（统一导入服务）**
- 统一的导入入口
- 支持处理器的动态注册
- 方法：
  - `import_timeseries_data()`：导入数据的主方法
  - `register_handler()`：注册新的处理器

#### 关键设计
- **Stock Code Normalization**：统一处理 SH、SZ、BJ、HK 等前缀的去除
- **Error Handling**：详细的错误记录和跳过机制
- **Raw Data Preservation**：所有导入数据保存到 RawImportData 表
- **Stock Validation**：跳过不存在的股票（数据来源于 CSV）

#### 使用示例

```python
from app.services.timeseries_import_service import TimeSeriesImportService
from app.core.database import get_db

db = get_db()
service = TimeSeriesImportService(db)

# 导入 EEE.txt
with open('EEE.txt', 'rb') as f:
    result = service.import_timeseries_data(
        'eee',
        f.read(),
        'EEE.txt',
        allow_overwrite=False
    )

# 导入 TTV.txt
with open('TTV.txt', 'rb') as f:
    result = service.import_timeseries_data(
        'ttv',
        f.read(),
        'TTV.txt'
    )
```

---

### 2. 统一数据模型（app/models/stock.py）

**文件位置**：`app/models/stock.py`（新增模型）

#### StockDailyMetrics（股票每日指标表）
```sql
CREATE TABLE stock_daily_metrics (
  id INTEGER PRIMARY KEY,
  stock_id INTEGER NOT NULL,        -- 股票ID
  trade_date DATE NOT NULL,         -- 交易日期
  metric_type VARCHAR(50) NOT NULL, -- 指标类型（eee_heat, ttv_trading_volume）
  metric_value DECIMAL(15,2),       -- 指标数值
  ranking_in_concept INTEGER,       -- 在概念中的排名
  percentage_in_concept DECIMAL(5,2), -- 在概念中的占比
  data_source VARCHAR(20),          -- 数据来源
  is_recalculated BOOLEAN,          -- 是否为重新计算
  created_at DATETIME,
  updated_at DATETIME
);

索引：
- (stock_id, trade_date, metric_type)
- (metric_type, trade_date)
- (trade_date, metric_value)
```

**用途**：
- 统一存储各种时间序列指标
- 通过 metric_type 字段区分不同数据源
- 支持快速的排名查询和聚合计算

#### ConceptMetricsSummary（概念指标汇总表）
```sql
CREATE TABLE concept_metrics_summary (
  id INTEGER PRIMARY KEY,
  concept_id INTEGER NOT NULL,      -- 概念ID
  trade_date DATE NOT NULL,         -- 交易日期
  metric_type VARCHAR(50) NOT NULL, -- 指标类型
  total_value DECIMAL(15,2),        -- 指标总值
  avg_value DECIMAL(15,2),          -- 平均值
  max_value DECIMAL(15,2),          -- 最大值
  min_value DECIMAL(15,2),          -- 最小值
  stock_count INTEGER,              -- 参与计算的股票数
  is_new_high BOOLEAN,              -- 是否创新高
  historical_max DECIMAL(15,2),     -- 历史最大值
  created_at DATETIME,
  updated_at DATETIME
);

索引：
- (concept_id, trade_date, metric_type)
- (metric_type, trade_date)
- (trade_date, is_new_high)
```

**用途**：
- 概念级的汇总指标
- 快速查询概念的日度聚合数据
- 创新高检测基础

#### MetricsCalculationTask（计算任务表）
```sql
CREATE TABLE metrics_calculation_task (
  id INTEGER PRIMARY KEY,
  task_type VARCHAR(50) NOT NULL,   -- 任务类型（daily_ranking等）
  target_date DATE NOT NULL,        -- 目标计算日期
  metric_type VARCHAR(50),          -- 指标类型过滤
  status VARCHAR(20) NOT NULL,      -- 状态：pending/processing/success/failed
  started_at DATETIME,              -- 开始时间
  completed_at DATETIME,            -- 完成时间
  duration_seconds INTEGER,         -- 执行耗时
  total_items INTEGER,              -- 总处理项数
  success_items INTEGER,            -- 成功项数
  failed_items INTEGER,             -- 失败项数
  error_message TEXT,               -- 错误信息
  log_details TEXT,                 -- 详细日志（JSON）
  retry_count INTEGER,              -- 重试次数
  max_retries INTEGER,              -- 最大重试数
  data_version VARCHAR(50),         -- 数据版本标识
  is_latest BOOLEAN,                -- 是否为最新版本
  created_by VARCHAR(50),           -- 创建人
  remarks TEXT,                     -- 备注
  created_at DATETIME,
  updated_at DATETIME
);

索引：
- (task_type, target_date)
- (status, target_date)
- (target_date, is_latest)
```

**用途**：
- 追踪所有计算任务的执行情况
- 支持失败重试
- 版本管理和审计日志

---

### 3. 指标计算服务（metrics_calculation_service.py）

**文件位置**：`app/services/metrics_calculation_service.py`

#### MetricsCalculationService（计算服务主类）

**核心方法**

1. `calculate_daily_metrics()`
   - 计算指定日期的所有指标
   - 包括：排名、汇总、创新高检测
   - 支持任务跟踪

2. `_calculate_stock_rankings()`
   - 计算股票在各概念中的排名
   - 更新 ranking_in_concept 和 percentage_in_concept
   - 按指标值从高到低排序

3. `_calculate_concept_summaries()`
   - 计算概念级的汇总指标
   - 总值、平均值、最大值、最小值
   - 参与计算的股票数

4. `_detect_new_highs()`
   - 检测创新高（超过历史最大值）
   - 记录到 ConceptHighRecord 表

5. `recalculate_metrics()`
   - 支持重新计算指定日期的所有指标
   - 清除旧的计算结果
   - 用于原始数据修正后的重新计算

#### 使用示例

```python
from app.services.metrics_calculation_service import MetricsCalculationService
from datetime import date

service = MetricsCalculationService(db)

# 计算某日期的所有指标
result = service.calculate_daily_metrics(
    target_date=date(2024, 2, 20),
    metric_type='eee_heat'  # 可选，指定指标类型
)

# 重新计算（如原始数据更正后）
result = service.recalculate_metrics(
    target_date=date(2024, 2, 20),
    metric_type='eee_heat',
    force=True  # 强制重新计算
)
```

---

### 4. 计算任务管理器（calculation_task_manager.py）

**文件位置**：`app/services/calculation_task_manager.py`

#### CalculationTaskManager（任务管理主类）

**核心方法**

1. `submit_task()`
   - 提交新的计算任务
   - 返回任务ID
   - 可指定任务类型、目标日期、指标类型

2. `process_pending_tasks()`
   - 批量处理所有待处理任务
   - 按创建时间顺序处理

3. `execute_task()`
   - 执行单个任务
   - 状态管理：pending → processing → success/failed
   - 失败重试机制（指数退避）

4. `get_task_status()`
   - 查询任务状态
   - 返回详细的任务信息

5. `get_task_history()`
   - 查询任务历史记录
   - 支持按日期、任务类型过滤

6. `cleanup_old_tasks()`
   - 清理旧的非最新任务
   - 保留审计日志

7. `recalculate_date_metrics()`
   - 请求重新计算指定日期的指标
   - 标记旧版本为非最新
   - 提交新计算任务

#### 任务类型

支持以下任务类型：
- `daily_ranking`：每日排名计算
- `concept_summary`：概念汇总计算
- `new_high_detection`：创新高检测

#### 重试机制
- 失败自动重试（最多3次）
- 每次重试时 retry_count 递增
- 失败任务可手动重新提交

#### 版本管理
- 每个计算结果都有版本ID（data_version）
- 格式：`YYYY-MM-DD_vN`（N = 版本号）
- is_latest 字段标识最新版本
- 支持追踪数据版本历史

#### 使用示例

```python
from app.services.calculation_task_manager import CalculationTaskManager
from datetime import date

manager = CalculationTaskManager(db)

# 1. 提交任务
task_id = manager.submit_task(
    task_type='daily_ranking',
    target_date=date(2024, 2, 20),
    metric_type='eee_heat',
    created_by='admin',
    remarks='手动触发的排名计算'
)

# 2. 处理待处理任务
stats = manager.process_pending_tasks()

# 3. 查询任务状态
status = manager.get_task_status(task_id)

# 4. 查询任务历史
history = manager.get_task_history(
    target_date=date(2024, 2, 20),
    limit=20
)

# 5. 重新计算某日期的指标
task_id = manager.recalculate_date_metrics(
    target_date=date(2024, 2, 20),
    force=True,
    created_by='admin'
)

# 6. 清理旧任务（保留30天）
deleted_count = manager.cleanup_old_tasks(days=30)
```

---

## 工作流程

### 导入工作流

```
1. 用户上传 EEE.txt / TTV.txt
   ↓
2. TimeSeriesImportService 选择对应的处理器
   ↓
3. 处理器解析文件，验证格式和内容
   ↓
4. 保存原始数据到 RawImportData 表
   ↓
5. 查询股票存在性，跳过不存在的记录
   ↓
6. 保存规范化数据到对应的业务表
   (DailyStockData for EEE heat_value,
    DailyTrading for TTV trading_volume)
   ↓
7. 返回导入统计结果
```

### 计算工作流

```
1. 提交计算任务
   ↓
2. 任务进入队列（status = pending）
   ↓
3. 任务管理器选择对应的计算处理函数
   ↓
4. 标记任务为处理中（status = processing）
   ↓
5. 执行计算：
   a. 计算股票排名
   b. 计算概念汇总
   c. 检测创新高
   ↓
6. 更新任务状态和统计信息
   ↓
7. 失败则重试（最多3次）
   ↓
8. 返回最终结果
```

### 重新计算工作流

```
1. 原始数据被更正
   ↓
2. 调用 recalculate_date_metrics()
   ↓
3. 标记旧版本为非最新
   ↓
4. 清除旧的计算结果
   ↓
5. 提交新的计算任务
   ↓
6. 按正常流程执行计算
   ↓
7. 生成新版本的计算结果
```

---

## 扩展性设计

### 支持新的数据源

要支持新的时间序列数据源（如未来的 XYZ.txt），只需：

1. **创建新的处理器**：继承 TimeSeriesImportHandler

```python
class XyzImportHandler(TimeSeriesImportHandler):
    @property
    def metric_type(self) -> str:
        return 'xyz_metric'

    def parse_file(self, content: bytes, filename: str):
        # 实现文件解析逻辑
        pass

    def validate_record(self, record: Dict):
        # 实现记录验证逻辑
        pass

    def save_normalized_data(self, records: List[Dict], target_date: date):
        # 实现数据保存逻辑
        pass
```

2. **注册处理器**

```python
service = TimeSeriesImportService(db)
service.register_handler('xyz', XyzImportHandler(db))
```

3. **使用处理器**

```python
result = service.import_timeseries_data('xyz', file_content, 'XYZ.txt')
```

---

## 数据流完整示例

### EEE.txt 导入和计算完整流程

```python
from app.services.timeseries_import_service import TimeSeriesImportService
from app.services.calculation_task_manager import CalculationTaskManager
from datetime import date

db = get_db()

# 第一步：导入原始数据
import_service = TimeSeriesImportService(db)
import_result = import_service.import_timeseries_data(
    'eee',
    eee_file_content,
    'EEE_20240220.txt',
    trade_date=date(2024, 2, 20)
)

if import_result['success']:
    print(f"导入成功: {import_result['stats']['imported']} 条记录")

    # 第二步：提交计算任务
    task_manager = CalculationTaskManager(db)
    task_id = task_manager.submit_task(
        task_type='daily_ranking',
        target_date=date(2024, 2, 20),
        metric_type='eee_heat',
        created_by='system'
    )

    # 第三步：执行计算任务
    task_result = task_manager.execute_task(task_id)

    if task_result['success']:
        print(f"计算成功: {task_result['details']}")
```

---

## 关键特性总结

| 特性 | 实现方式 |
|-----|--------|
| **多源支持** | 处理器模式，易于扩展 |
| **数据完整性** | 原始数据完全保留 |
| **性能优化** | 批量操作，索引优化 |
| **错误处理** | 详细的错误日志，跳过无效数据 |
| **版本管理** | 每个计算结果都有版本标识 |
| **重试机制** | 失败自动重试，指数退避 |
| **审计能力** | 完整的任务历史和执行日志 |
| **可重新计算** | 支持数据修正后的完整重新计算 |

---

## 后续优化建议

1. **性能优化**
   - 实现批量计算（同时处理多个日期）
   - 添加数据库连接池
   - 使用异步处理器

2. **功能扩展**
   - 支持增量计算（仅计算新增数据）
   - 添加计算缓存层
   - 实现分布式计算支持

3. **监控和告警**
   - 任务执行监控仪表板
   - 失败告警机制
   - 性能指标收集

4. **API 接口**
   - RESTful API 支持数据导入查询
   - WebSocket 实时任务状态推送
   - 计算结果查询接口

---

**版本**：3.0.0（统一时间序列框架）
**最后更新**：2024-11-25
