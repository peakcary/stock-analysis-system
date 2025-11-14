# 数据导入到分析生成的完整代码调用栈分析

## 调用链路追踪

### 路径 1：批量导入触发分析完整流程

```
POST /api/v1/data_import/import-daily-batch
         |
         v
api_v1/endpoints/data_import.py:274-348
  @router.post("/import-daily-batch")
  async def import_daily_batch(...)
         |
         v
services/data_import.py:910-1015
  DataImportService.import_daily_batch()
    |
    +-- 第943行: csv_result = await self.import_csv_data(...)
    |     |
    |     v
    |   services/data_import.py:54-451
    |     DataImportService.import_csv_data()
    |       |
    |       +-- 导入CSV数据
    |       |     └─ 写入: Stock, Concept, StockConcept, DailyStockData
    |       |       （heat_value=0 ❌）
    |       |
    |       └─ 返回 csv_result
    |
    +-- 第975行: txt_result = await self.import_txt_data(...)
    |     |
    |     v
    |   services/data_import.py:453-770
    |     DataImportService.import_txt_data()
    |       |
    |       +-- 导入TXT数据
    |       |     └─ 写入: DailyStockData (heat_value=heat_value_from_txt)
    |       |
    |       └─ 返回 txt_result
    |
    +-- 第980-985行: 检查导入是否成功
    |
    +-- 第1001行: ⭐ 触发分析计算
    |     |
    |     v
    |   services/ranking_calculator.py:213-255
    |     RankingCalculatorService.trigger_full_analysis(trade_date)
    |       |
    |       +-- 第234行: ranking_result = await self.calculate_daily_rankings(trade_date)
    |       |     |
    |       |     v
    |       |   services/ranking_calculator.py:24-89
    |       |     RankingCalculatorService.calculate_daily_rankings()
    |       |       |
    |       |       +-- 第36-38行: 删除当日已存在的排名数据
    |       |       |     └─ DELETE FROM daily_concept_rankings WHERE trade_date=X
    |       |       |
    |       |       +-- 第43行: 获取所有Concept
    |       |       |     └─ SELECT * FROM concepts
    |       |       |
    |       |       +-- 第45-74行: 对每个Concept计算排名
    |       |       |     |
    |       |       |     └─ 第47-54行: 查询该概念下的股票及热度
    |       |       |           |
    |       |       |           v
    |       |       |         SELECT dsd.stock_code, dsd.heat_value
    |       |       |         FROM daily_stock_data dsd
    |       |       |         JOIN stock_concepts sc ON dsd.stock_id = sc.stock_id
    |       |       |         WHERE sc.concept_id = X
    |       |       |           AND dsd.trade_date = X
    |       |       |           AND dsd.heat_value > 0  ❌ 过滤条件
    |       |       |
    |       |       +-- 第72-73行: 批量插入DailyConceptRanking
    |       |       |     └─ INSERT INTO daily_concept_rankings (...)
    |       |       |
    |       |       └─ 返回ranking_result
    |       |
    |       +-- 第238行: summary_result = await self.calculate_concept_summaries(trade_date)
    |       |     |
    |       |     v
    |       |   services/ranking_calculator.py:91-168
    |       |     RankingCalculatorService.calculate_concept_summaries()
    |       |       |
    |       |       +-- 第103-105行: 删除当日已存在的汇总数据
    |       |       |     └─ DELETE FROM daily_concept_summaries WHERE trade_date=X
    |       |       |
    |       |       +-- 第108-119行: 从daily_concept_rankings查询汇总数据
    |       |       |     |
    |       |       |     v
    |       |       |   SELECT concept_id, 
    |       |       |          SUM(heat_value), COUNT(*), AVG(heat_value), 
    |       |       |          MAX(heat_value), MIN(heat_value)
    |       |       |   FROM daily_concept_rankings
    |       |       |   WHERE trade_date = X
    |       |       |   GROUP BY concept_id
    |       |       |
    |       |       +-- 第121-150行: 对每个汇总数据生成记录
    |       |       |     |
    |       |       |     +-- 第133-135行: 检查是否创新高
    |       |       |     |     └─ 调用 _check_innovation_high()
    |       |       |     |
    |       |       |     └─ 创建DailyConceptSummary对象
    |       |       |
    |       |       +-- 第153行: 批量插入DailyConceptSummary
    |       |       |     └─ INSERT INTO daily_concept_summaries (...)
    |       |       |
    |       |       └─ 返回summary_result
    |       |
    |       +-- 第242行: innovation_concepts = await self.detect_innovation_highs(trade_date)
    |       |     |
    |       |     v
    |       |   services/ranking_calculator.py:257-274
    |       |     RankingCalculatorService.detect_innovation_highs()
    |       |       |
    |       |       └─ SELECT concept_id FROM daily_concept_summaries
    |       |          WHERE trade_date = X AND is_new_high = True
    |       |
    |       └─ 返回完整的analysis_result

    └─ 返回 import_daily_batch_result
```

---

## 关键数据转换点

### 数据源 1：CSV文件

```
CSV行 → DataImportService.import_csv_data()
  ├─ 股票代码: "600000" (或 "SH600000")
  │   └─ 规范化: _normalize_stock_code() → "600000"
  │       └─ 写入 Stock.stock_code = "600000"
  │
  ├─ 概念: "AI芯片"
  │   └─ 写入 Concept.concept_name = "AI芯片"
  │
  ├─ 热帖首页页阅读总数: 1000
  │   └─ 映射到 DailyStockData.hot_page_views = 1000
  │   └─ ❌ 但 heat_value = 0 (默认值，第369行)
  │
  └─ 页数: 5
      └─ 映射到 DailyStockData.total_pages = 5
```

### 数据源 2：TXT文件

```
TXT行 (格式: "SH600000\t2025-08-21\t459400")
  └─ DataImportService.import_txt_data()
      ├─ 股票代码: "SH600000"
      │   └─ 规范化: _normalize_stock_code() → "600000"
      │
      ├─ 日期: "2025-08-21"
      │   └─ 解析: _parse_date_from_string() → date(2025, 8, 21)
      │
      └─ 热度值: 459400
          └─ 写入 DailyStockData.heat_value = 459400 ✅
          
          ❌ 问题：
             - 如果是新建，这条记录单独有效
             - 如果是更新，会覆盖CSV导入的记录
             - 没有融合逻辑
```

---

## 问题演示：为什么daily_concept_summaries为空

### 场景 A：仅导入CSV

```
Step 1: CSV导入创建DailyStockData
  stock_code="600000", heat_value=0 ❌

Step 2: 触发calculate_daily_rankings()
  查询: SELECT * FROM daily_stock_data 
        WHERE heat_value > 0
  结果: 空集 ❌
  
Step 3: 插入DailyConceptRanking
  0条记录被插入

Step 4: 触发calculate_concept_summaries()
  查询: SELECT * FROM daily_concept_rankings 
        WHERE trade_date = X
  结果: 空集 ❌
  
Step 5: 插入DailyConceptSummary
  0条记录被插入

最终: daily_concept_summaries 表为空 ❌
```

### 场景 B：先CSV后TXT

```
Step 1: CSV导入创建DailyStockData
  stock_code="600000", heat_value=0
  
  DailyStockData表:
  ├─ stock_code | heat_value | total_pages | ...
  └─ 600000     | 0          | 5           | ...

Step 2: TXT导入处理相同日期和股票
  
  第580-600行: 如果allow_overwrite或已存在
    └─ DELETE FROM daily_stock_data 
       WHERE stock_id=X AND trade_date=X
       
       ❌ 删除了CSV导入的记录！
  
  第670-681行: 创建新的DailyStockData
    └─ INSERT INTO daily_stock_data
       (stock_id, trade_date, heat_value=459400, ...)
       
  DailyStockData表:
  ├─ stock_code | heat_value | total_pages | ...
  └─ 600000     | 459400     | 0           | ...
              (仅来自TXT)    (丢失了CSV的页数信息)

Step 3-5: 分析
  ✅ heat_value > 0，可以进行排名计算
  ✅ daily_concept_rankings 有数据
  ✅ daily_concept_summaries 有数据
  
  ⚠️ 但数据不完整（缺少CSV的字段）
```

---

## 导入代码关键位置清单

| 行号 | 文件 | 描述 | 问题 |
|-----|------|------|------|
| 54-451 | data_import.py | `import_csv_data()` 方法 | 导入CSV |
| 87-88 | data_import.py | `_normalize_csv_columns()` 列名映射 | 支持中文列名 |
| 369 | data_import.py | `daily_data = DailyStockData(..., heat_value=0)` | ❌ 热度值初始化为0 |
| 453-770 | data_import.py | `import_txt_data()` 方法 | 导入TXT |
| 580-600 | data_import.py | TXT导入的删除逻辑 | ❌ 可能删除CSV数据 |
| 670-681 | data_import.py | TXT导入的插入逻辑 | ❌ 没有更新现有记录 |
| 910-1015 | data_import.py | `import_daily_batch()` 批量导入 | 触发分析 |
| 1001 | data_import.py | `trigger_full_analysis()` 调用 | 分析触发点 |
| 24-89 | ranking_calculator.py | `calculate_daily_rankings()` | 写入daily_concept_rankings |
| 53 | ranking_calculator.py | `DailyStockData.heat_value > 0` 过滤 | ❌ 关键过滤条件 |
| 91-168 | ranking_calculator.py | `calculate_concept_summaries()` | 写入daily_concept_summaries |
| 108-119 | ranking_calculator.py | 从ranking表查询汇总数据 | 依赖ranking数据存在 |

---

## 数据流完整性检查清单

```
导入前检查
├─ [ ] CSV文件格式是否正确
├─ [ ] TXT文件格式是否正确
└─ [ ] 日期解析是否成功

CSV导入后检查
├─ [ ] Stock表是否有新记录
├─ [ ] Concept表是否有新记录
├─ [ ] StockConcept表是否有新关联
├─ [ ] DailyStockData表记录数是否正确
└─ [ ] ❌ DailyStockData.heat_value是否为0

TXT导入后检查
├─ [ ] DailyStockData表热度值是否正确
├─ [ ] ❌ 是否删除了CSV的记录
└─ [ ] ❌ 是否丢失了CSV的其他字段

分析计算前检查
├─ [ ] DailyStockData中是否有heat_value > 0的记录
└─ [ ] 股票-概念关联是否完整

分析后检查
├─ [ ] daily_concept_rankings表是否有数据
├─ [ ] daily_concept_summaries表是否有数据
└─ [ ] 两个表的数据是否互相对应

