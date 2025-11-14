# 后端数据导入逻辑分析报告

## 问题概述
`daily_concept_summaries` 和 `daily_concept_rankings` 表没有数据。

## 一、存在的数据模型混乱

### 1. 表定义的不一致性

系统中存在两套完全独立的表结构定义：

#### 套1：在 `concept_analysis.py` 中定义
- **DailyConceptRanking** - 表名: `daily_concept_rankings`
- **DailyConceptSummary** - 表名: `daily_concept_summaries`
- 字段包括：`concept_id`、`stock_id`、`rank_in_concept`、`heat_value`、`trade_date`
- 使用**外键关联** Concept 和 Stock 表

#### 套2：在 `stock_data.py` 中定义
- **StockConceptRanking** - 表名: `stock_concept_daily_rankings`
- **ConceptDailyStats** - 表名: `stock_concept_daily_stats`（部分功能替代）
- 字段包括：`concept_name`(字符串，非外键)、`stock_code`(字符串，非外键)、`volume_rank`、`hot_views_rank`

#### 套3：在 `daily_analysis.py` 中定义
- **DailyConceptFinancialRanking** - 表名: `daily_stock_concept_financial_rankings`
- **DailyConceptFinancialSummary** - 表名: `daily_concept_financial_summaries`

---

## 二、导入流程分析

### 数据流向：

```
CSV文件 + TXT文件
         |
         v
  DataImportService
    (data_import.py)
         |
    +---------+--------+
    |         |        |
    v         v        v
Stock    Concept   DailyStockData
(stocks)  (concepts) (daily_stock_data)
    |         |        |
    +---------+--------+
         |
         v
    没有直接写入
    daily_concept_rankings
    daily_concept_summaries
```

### 关键发现：

**导入流程在 `data_import.py` 的 `import_csv_data()` 和 `import_txt_data()` 方法中：**

1. **CSV导入** → 写入：
   - `Stock` 表（股票基础信息）
   - `Concept` 表（概念分类）
   - `StockConcept` 表（股票-概念关联）
   - `DailyStockData` 表（每日股票数据）
   - `RawImportData` 表（原始数据）
   - `StockConceptRawData` 表（未拆分的原始数据）

2. **TXT导入** → 写入：
   - `DailyStockData` 表（热度数据）
   - `RawImportData` 表（原始数据）

3. **完整分析触发** → 在 `import_daily_batch()` 的第1004行：
   ```python
   analysis_result = await ranking_service.trigger_full_analysis(trade_date)
   ```

---

## 三、分析数据生成的责任链

### 1. **RankingCalculatorService** (`ranking_calculator.py`)

负责计算两个关键表的数据：

#### ✅ `calculate_daily_rankings()` (第24-89行)
- 写入表：**`daily_concept_rankings`**
- 流程：
  1. 删除当日旧排名数据
  2. 遍历所有 `Concept`
  3. 对每个概念，查询其下的股票及热度数据
  4. 按热度排序，分配排名
  5. 批量插入 `DailyConceptRanking` 记录

#### ✅ `calculate_concept_summaries()` (第91-168行)
- 写入表：**`daily_concept_summaries`**
- 流程：
  1. 删除当日旧汇总数据
  2. 从 `DailyConceptRanking` 查询已计算的排名
  3. **按 `concept_id` 分组**聚合统计
  4. 计算：总热度、股票数量、平均热度、最高/最低热度
  5. 检测是否创新高
  6. 批量插入 `DailyConceptSummary` 记录

#### ✅ `trigger_full_analysis()` (第213-255行)
- 触发完整流程：
  1. 调用 `calculate_daily_rankings()`
  2. 调用 `calculate_concept_summaries()`
  3. 调用 `detect_innovation_highs()`

---

## 四、问题根本原因

### 🔴 **关键问题 1：表与模型使用混乱**

数据导入代码（`data_import.py`）写入的表结构：
```python
# stock_data.py 中定义（在stock_concept_xxx名称空间）
Stock                      # stocks 表
Concept                    # concepts 表
StockConcept               # stock_concepts 表
DailyStockData             # daily_stock_data 表
```

但分析代码（`ranking_calculator.py`）期望的表结构：
```python
# concept_analysis.py 中定义（在daily_concept_xxx名称空间）
DailyConceptRanking        # daily_concept_rankings 表
DailyConceptSummary        # daily_concept_summaries 表
```

**这两个系统使用不同的数据模型定义，导致虽然导入了数据到一张表，但分析代码生成数据到另一张表！**

---

### 🔴 **关键问题 2：导入后分析的关键数据缺失**

`RankingCalculatorService.calculate_daily_rankings()` 依赖于：
```python
DailyStockData.heat_value > 0  # 第53行的过滤条件
```

但查看导入代码 (`data_import.py` 第369行)：
```python
daily_data = DailyStockData(
    stock_id=stock.id,
    trade_date=trade_date,
    ...
    heat_value=0  # 默认热度值为0  ❌ 问题！
)
```

**导入时 `heat_value` 被设置为 0，而分析代码过滤 `heat_value > 0`，导致没有任何记录被选中！**

---

### 🔴 **关键问题 3：缺少TXT数据的热度融合**

TXT文件导入 (`import_txt_data()` 第670-680行)：
```python
daily_data = DailyStockData(
    stock_id=stock.id,
    trade_date=target_date,
    heat_value=heat_value,  # 设置热度值
    ...
)
```

但 TXT 数据是分开导入的，而 CSV 数据导入时 `heat_value=0`。

**两个导入的数据没有融合，导致：**
1. 如果只导入CSV，热度值为0，分析失败
2. 如果先CSV后TXT，可能出现数据覆盖或重复

---

## 五、数据流追踪

### 当前导入流程中缺失的环节：

```
CSV导入
 ├─ 创建Stock
 ├─ 创建Concept
 ├─ 创建StockConcept
 └─ 创建DailyStockData (heat_value=0) ❌ 问题在这

TXT导入
 └─ 更新DailyStockData (heat_value=heat_value_from_txt)
 
触发分析
 ├─ 调用 calculate_daily_rankings()
 │   └─ 过滤: heat_value > 0 ❌ 筛选不到CSV-only数据
 └─ 调用 calculate_concept_summaries()
     └─ 从DailyConceptRanking查询 ❌ 可能为空
```

---

## 六、具体代码位置对照

| 文件位置 | 类/方法 | 作用 | 问题 |
|---------|-------|------|------|
| `data_import.py` 第54-451 | `import_csv_data()` | 导入CSV | heat_value=0 |
| `data_import.py` 第453-770 | `import_txt_data()` | 导入TXT | 数据融合问题 |
| `data_import.py` 第910-1015 | `import_daily_batch()` | 批量导入 | 触发分析 |
| `ranking_calculator.py` 第24-89 | `calculate_daily_rankings()` | 生成daily_concept_rankings | 依赖heat_value>0 |
| `ranking_calculator.py` 第91-168 | `calculate_concept_summaries()` | 生成daily_concept_summaries | 依赖rankings结果 |
| `ranking_calculator.py` 第213-255 | `trigger_full_analysis()` | 完整分析流程 | 在导入后调用 |

---

## 七、根本原因总结

### ❌ **三个致命问题：**

1. **表结构定义混乱**
   - 概念分析用的是 `daily_concept_rankings`、`daily_concept_summaries`（使用ID外键）
   - 导入代码用的是 `stock_concept_daily_rankings`、`stock_concept_daily_stats`（使用字符串字段）
   - 两个系统的表完全不兼容

2. **热度值初始化为0**
   - CSV导入时 `heat_value=0`
   - 排名计算时过滤 `heat_value > 0`
   - 结果：没有任何记录被统计

3. **TXT和CSV数据融合策略不清**
   - TXT导入会创建新的 `DailyStockData` 记录
   - 没有清晰的合并策略
   - 可能出现数据不完整或覆盖

---

## 八、解决方案建议

### 立即修复（短期）：

1. **修复热度值初始化**
   ```python
   # data_import.py 第369行改为
   heat_value=hot_page_views  # 或其他热度计算逻辑
   ```

2. **修复TXT导入的融合逻辑**
   ```python
   # 不创建新记录，改为更新现有记录
   existing_data = query DailyStockData
   if existing_data:
       existing_data.heat_value = heat_value
   ```

3. **统一表结构使用**
   - 要么统一使用 `daily_concept_rankings/summaries`（推荐）
   - 要么统一使用 `stock_concept_daily_rankings/stats`

### 长期重构（中期）：

1. **重新设计数据模型**
   - 明确定义主表（推荐使用stock_concept_*前缀的表）
   - 删除冗余的表定义

2. **标准化导入流程**
   - CSV导入：基础股票信息 + 每日交易数据
   - TXT导入：热度数据融合（更新而非创建）

3. **统一分析流程**
   - 确保所有分析代码使用同一套表和模型

