# 表结构和数据流完整分析

## 现存表的定义和层级关系

### 第1层：原始数据导入表（来自 CSV）

#### DailyStockData（stocks.py）
- stock_id (FK)
- trade_date
- price, turnover_rate, net_inflow, pages_count, total_reads
- heat_value

**数据来源**：DataImportService 直接从 CSV 导入

---

### 第2层：股票-概念原始关联表

#### StockConceptRawData（stocks.py）
- stock_code, stock_name
- concept
- price, turnover_rate, net_inflow, pages_count, total_reads
- import_date, trade_date
- industry

**数据来源**：DataImportService 在导入 CSV 时逐行创建

#### StockConceptData（simple_import.py）
- stock_code, stock_name
- concept
- price, turnover_rate, net_inflow, page_count, total_reads
- import_date
- industry

**数据来源**：SimpleImportService（目前未被使用）

**问题**：虽然 DailyAnalysisService 需要从此表查询数据，但 DataImportService 没有填充它！

---

### 第3层：旧分析表（可能已弃用）

#### DailyTrading（daily_trading.py）
- stock_code, trading_date, trading_volume
- **用途**：交易量数据

#### ConceptDailySummary（daily_trading.py）
- concept_name, trading_date
- total_volume, stock_count, average_volume
- **用途**：按交易量汇总

#### StockConceptRanking（daily_trading.py）
- stock_code, concept_name, trading_date
- trading_volume, concept_rank, volume_percentage
- **用途**：股票在概念中的排名（按交易量）

#### ConceptHighRecord（daily_trading.py）
- concept_name, trading_date
- total_volume, days_period, is_active
- **用途**：记录创新高

**状态**：这组表以 trading_volume 为核心，可能来自 TXT 文件导入

---

### 第4层：新分析表（按热度和财务指标）

#### DailyConceptRanking（concept_analysis.py）
- concept_id (FK), stock_id (FK), trade_date
- rank_in_concept, heat_value
- **用途**：记录股票在每个概念中的排名和热度

#### DailyConceptSummary（concept_analysis.py）
- concept_id (FK), trade_date
- total_heat_value, stock_count, avg_heat_value, max/min_heat_value
- is_new_high, new_high_days
- **用途**：按概念的每日热度汇总

**数据来源**：RankingCalculatorService 从数据库计算生成

---

### 第5层：财务数据分析表（最新）

#### DailyConceptFinancialRanking（daily_analysis.py）
- analysis_date, concept, stock_code, stock_name
- net_inflow_rank, price_rank, turnover_rate_rank, total_reads_rank
- net_inflow, price, turnover_rate, total_reads, page_count, industry
- **用途**：股票在概念中的财务排名（新增）

#### DailyConceptFinancialSummary（daily_analysis.py）
- analysis_date, concept
- stock_count, total_net_inflow, avg_net_inflow, avg_price, avg_turnover_rate
- total_reads, total_pages, concept_rank
- **用途**：概念的每日财务汇总（新增）

**数据来源**：需要从 stock_concept_data 查询，但该表为空！

---

## 数据流关系图

```
CSV 文件
  ↓
DataImportService.import_csv_data()
  ├→ stocks (创建)
  ├→ concepts (创建)
  ├→ stock_concepts (创建)
  ├→ daily_stock_data (按 stock_id 创建)
  ├→ stock_concept_raw_data (按 stock-concept 创建)
  └→ raw_import_data (记录)
  ↓
RankingCalculatorService.calculate_daily_rankings()
  ├→ DailyConceptRanking (从数据库计算)
  └→ DailyConceptSummary (从数据库计算)

DailyAnalysisService._generate_concept_summaries()
  └→ 需要从 stock_concept_data 查询数据
     ❌ 问题：stock_concept_data 为空！
```

---

## 核心问题

**DailyAnalysisService 依赖关系：**
```python
# 来自 daily_analysis.py 第 185-195 行
sql_query = text("""
    SELECT concept, COUNT(*) as stock_count,
           SUM(net_inflow), AVG(net_inflow), AVG(price), AVG(turnover_rate),
           SUM(total_reads), SUM(page_count)
    FROM stock_concept_data 
    WHERE import_date = :analysis_date
    GROUP BY concept
""")
```

**必需字段**（均存在于 CSV 文件）：
- stock_code ✓
- stock_name ✓
- concept ✓
- price ✓
- turnover_rate ✓
- net_inflow ✓
- total_reads ✓
- page_count ✓
- industry ✓
- import_date ✓

---

---

## EEE 和 TTV 导入的完整逻辑

### EEE.txt 导入流程（import_eee.py）
**文件格式**：`股票代码[Tab]交易日期[Tab]热度值`
**例**：`SH110062\t2024-02-20\t33082.000000`

**导入步骤**：
1. 解析 EEE.txt，按日期分组
2. 创建表：`eee_daily_trading`
   - original_stock_code, normalized_stock_code, stock_code
   - trading_date, trading_volume (热度值)
   - created_at
3. 创建导入记录：`eee_import_record`
   - filename, trading_date, file_hash, import_status
   - total_records, success_records, error_records, duplicate_records
   - import_started_at, import_completed_at

**关键特点**：
- ✓ 只有 2 个表（数据表 + 元数据表）
- ✓ 简单直接：1条EEE行 → 1条 eee_daily_trading 记录
- ✓ 没有涉及 stocks, concepts, stock_concepts 关系表

### TTV.txt 导入流程（import_ttv.py）
**文件格式**：`股票代码[Tab]交易日期[Tab]数值`

**导入步骤**：
1. 解析 TTV.txt，按日期分组
2. 创建表：`ttv_daily_trading`
   - 结构同 eee_daily_trading
3. 创建导入记录：`ttv_import_record`
   - 同 eee_import_record

**关键特点**：
- ✓ 同样简单：只需 2 个表
- ✓ 没有复杂的关系处理

### CSV 导入流程（import_csv_local.py）vs EEE/TTV
| 方面 | CSV | EEE | TTV |
|-----|-----|-----|-----|
| 入口脚本 | import_csv_local.py | import_eee.py | import_ttv.py |
| 使用的服务 | DataImportService | 直接SQL插入 | 直接SQL插入 |
| 创建表数量 | 6+ 个 | 2 个 | 2 个 |
| 关系处理 | 复杂（stocks, concepts, stock_concepts） | 无 | 无 |
| 财务数据 | ✓ 包含（price, turnover_rate, net_inflow等） | ✗ 无 | ✗ 无 |
| 数据粒度 | stock-concept 组合 | stock-date | stock-date |

**核心区别**：
- EEE/TTV：纯数据导入，没有业务逻辑复杂度
- CSV：涉及股票、概念、关系，数据粒度更细

---

## 解决方案评估

### 方案A：修改 DataImportService 填充 stock_concept_data
- **优点**：一条导入链完整
- **缺点**：重复存储数据（stock_concept_raw_data + stock_concept_data）
- **工作量**：小（添加几行代码）
- **推荐**：✓ 推荐

### 方案B：使用 SimpleImportService
- **优点**：语义清晰
- **缺点**：需要改变整个导入脚本入口
- **工作量**：大
- **推荐**：✗ 不推荐

### 方案C：修改 DailyAnalysisService 使用 stock_concept_raw_data
- **优点**：不需要新增填充逻辑
- **缺点**：两个表的结构略有不同（需要处理 trade_date vs import_date）
- **工作量**：中等
- **推荐**：？ 可选

---

## 建议

采用 **方案A**：在 DataImportService 中添加代码，每导入一条 CSV 行就创建一个 StockConceptData 记录。

这样可以保证：
1. DailyAnalysisService 能找到需要的数据
2. 分析流程能正常运行
3. 无需改变现有的导入脚本入口