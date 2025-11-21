# 完整导入架构分析

## 三个导入系统的对比

### 1️⃣ EEE.txt 导入系统（纯热度数据）
**入口脚本**：`backend/scripts/import_eee.py`
**数据源**：EEE.txt（股票代码 + 日期 + 热度值）

**生成的表**：
- `eee_daily_trading` 
  - 字段：stock_code, trading_date, trading_volume(热度值)
- `eee_import_record`
  - 元数据记录

**导入逻辑**：
```
EEE.txt 
  ↓ (逐行解析) 
  ↓ (按日期分组)
  ↓ (日期为单位事务提交)
eee_daily_trading (直接插入，无额外处理)
eee_import_record (记录元数据)
```

**特点**：
- 简单直接，无关系处理
- 一条行 = 一条数据库记录
- 完全独立，不涉及其他表

---

### 2️⃣ TTV.txt 导入系统（纯交易数据）
**入口脚本**：`backend/scripts/import_ttv.py`
**数据源**：TTV.txt（股票代码 + 日期 + 值）

**生成的表**：
- `ttv_daily_trading`（同 eee_daily_trading）
- `ttv_import_record`（同 eee_import_record）

**特点**：
- 完全同 EEE 的导入逻辑
- 纯数据导入，无复杂度

---

### 3️⃣ CSV 导入系统（复杂的股票-概念数据）
**入口脚本**：`backend/scripts/import_csv_local.py`
**使用服务**：`DataImportService`
**数据源**：CSV（股票代码 + 名称 + 概念 + 财务数据）

**生成的表**：
```
基础表：
  ├─ stocks (股票基本信息)
  ├─ concepts (概念信息)
  └─ stock_concepts (股票-概念关联)

原始数据表：
  ├─ daily_stock_data (按 stock 粒度)
  ├─ stock_concept_raw_data (按 stock-concept 粒度)
  └─ raw_import_data (导入元数据)

❌ 缺失表：
  └─ stock_concept_data (分析服务需要的表，但没有被填充！)

分析表：
  ├─ daily_concept_rankings (热度排名)
  ├─ daily_concept_summaries (热度汇总)
  ├─ daily_concept_financial_rankings (财务排名)
  └─ daily_concept_financial_summaries (财务汇总，依赖 stock_concept_data)
```

**导入逻辑**：
```
CSV 文件
  ↓ (逐行迭代)
  ├→ 创建/查询 Stock (按 stock_code)
  ├→ 创建/查询 Concept (按 concept_name)
  ├→ 创建/查询 StockConcept (按 stock_id + concept_id)
  ├→ 创建/更新 DailyStockData (按 stock_id + trade_date)
  ├→ 创建 StockConceptRawData (每行都创建)
  ├→ 创建 RawImportData (每行都创建)
  └→ [缺失：创建 StockConceptData]  ❌

RankingCalculatorService.calculate_daily_rankings()
  ├→ 从数据库计算生成 DailyConceptRanking
  └→ 从数据库计算生成 DailyConceptSummary

DailyAnalysisService._generate_concept_summaries()
  └→ 从 stock_concept_data 查询汇总数据 ❌ 表为空！
```

**复杂度来源**：
- CSV 每一行代表一个 stock-concept 组合
- 同一股票可能出现多次（多个概念）
- 需要处理 stock 和 stock-concept 的不同粒度
- 涉及多个关系表的创建和维护

---

## 关键差异分析

### 数据粒度
| | EEE | TTV | CSV |
|---|---|---|---|
| 粒度 | stock-date | stock-date | stock-concept-date |
| 每行代表 | 1个股票的1天热度 | 1个股票的1天交易值 | 1个股票在1个概念内的完整财务数据 |

### 关系处理
| | EEE | TTV | CSV |
|---|---|---|---|
| 需要创建 stocks | ✗ | ✗ | ✓ |
| 需要创建 concepts | ✗ | ✗ | ✓ |
| 需要创建关联表 | ✗ | ✗ | ✓ |
| 处理重复问题 | 简单 | 简单 | 复杂 |

### 目标表的差异
| | EEE | TTV | CSV |
|---|---|---|---|
| 数据表 | eee_daily_trading | ttv_daily_trading | daily_stock_data + stock_concept_raw_data |
| 用途 | 纯数据存储 | 纯数据存储 | 既存储也分析 |
| 是否供分析服务使用 | ✗ | ✗ | ✓ |

---

## 核心问题的本质

### 问题陈述
CSV 导入的分析链条被破坏：
```
CSV 导入完成
  ↓ ✓ (成功)
  ├→ RankingCalculatorService 计算排名 ✓ (成功)
  └→ DailyAnalysisService 查询 stock_concept_data ✗ (失败：表为空)
```

### 根本原因
1. **设计初衷**：`stock_concept_data` 应该在 CSV 导入时被填充
2. **实现缺陷**：`DataImportService` 没有填充 `stock_concept_data`
3. **依赖关系**：但 `DailyAnalysisService` 的 SQL 依赖这个表

### 为什么 EEE/TTV 不需要 stock_concept_data
- EEE/TTV 是单纯的数据导入，不需要分析
- 它们的数据粒度与 stock_concept_data 不匹配
- 它们没有关联 DailyAnalysisService

---

## 解决方案选择

### 方案A：修改 DataImportService 填充 stock_concept_data ✓ 推荐
**优点**：
- 符合原始设计意图
- 最小化改动（只在 import_csv_data 中添加几行）
- CSV 和 stock_concept_data 的数据匹配完美
- DailyAnalysisService 能正常工作

**缺点**：
- 需要写入两个表（stock_concept_raw_data + stock_concept_data），有冗余

**实施方案**：
```python
# 在导入循环中，添加：
stock_concept_data_record = {
    'stock_code': stock_code,
    'stock_name': stock_name,
    'concept': concept_name,
    'industry': industry,
    'price': price,
    'turnover_rate': turnover_rate,
    'net_inflow': net_inflow,
    'page_count': pages_count,
    'total_reads': total_reads,
    'import_date': import_date
}
stock_concept_data_list.append(stock_concept_data_record)

# 在批量插入之前：
if stock_concept_data_list:
    db.bulk_insert_mappings(StockConceptData, stock_concept_data_list)
```

### 方案B：修改 DailyAnalysisService 使用 stock_concept_raw_data
**优点**：
- 不需要新的表
- 利用现有的已填充数据

**缺点**：
- 两个表字段不完全兼容（需要处理 trade_date vs import_date）
- 修改分析服务，影响范围更大

### 方案C：改用 SimpleImportService
**优点**：
- 语义清晰，stock_concept_data 就是为此设计的

**缺点**：
- 需要改变导入入口脚本
- 可能有其他兼容性问题

---

## 推荐方案：**方案A**

1. **原因**：
   - CSV 数据完美匹配 stock_concept_data 的字段
   - 修改最少（就几行代码）
   - 无需改变导入脚本入口
   - 分析服务能正常工作

2. **实施步骤**：
   - 在 `DataImportService.import_csv_data()` 的循环中收集 stock_concept_data 数据
   - 在所有记录处理完成后，批量插入 stock_concept_data
   - 处理覆盖模式（先删除该日期的数据，再插入）

3. **验证方法**：
   - 导入完成后检查 stock_concept_data 表有数据
   - 运行 DailyAnalysisService 检查是否能查询到数据
   - 验证分析结果正确