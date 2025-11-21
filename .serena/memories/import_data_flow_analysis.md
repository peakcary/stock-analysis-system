# 导入数据流问题分析 - 已更新

## 发现的真实问题

系统中存在**三个不同的导入服务**，但它们的关系不清楚：

### 1. DataImportService（当前使用）
- 位置：`backend/app/services/data_import.py`
- 用途：导入 CSV/TXT 格式数据
- 创建的表：stocks, concepts, stock_concepts, daily_stock_data, stock_concept_raw_data
- **问题**：不填充 `stock_concept_data` 表
- 入口脚本：`backend/scripts/import_csv_local.py`

### 2. SimpleImportService（未被使用）
- 位置：`backend/app/services/simple_import.py`
- 用途：专门填充 `stock_concept_data` 表
- 填充的表：stock_concept_data
- 方法：`_batch_insert_concept_data()` 等

### 3. StockDataImportService（可能也未被使用）
- 位置：`backend/app/services/stock_data_import.py`
- 用途：导入股票和概念数据
- 包含方法：calculate_concept_rankings

## 分析服务的依赖

`DailyAnalysisService._generate_concept_summaries()` 执行的 SQL：
```sql
SELECT concept, COUNT(*) as stock_count, SUM(net_inflow)...
FROM stock_concept_data 
WHERE import_date = :analysis_date
```

**这个查询依赖 `stock_concept_data` 表有数据**。

## 解决方案选择

### 选项A：改用 SimpleImportService 填充 stock_concept_data
- 优点：表的语义正确，stock-concept 粒度
- 缺点：需要修改导入脚本入口

### 选项B：修改 DataImportService 同时填充 stock_concept_data
- 优点：保持当前使用的导入脚本不变
- 缺点：创建更多重复的表和数据

### 选项C：修改分析服务使用已有的表（stock_concept_raw_data）
- 优点：不需要额外修改导入逻辑
- 缺点：需要理解 stock_concept_raw_data 的数据结构

## 建议

需要确认一下：CSV 导入的文件格式是否包含 `stock_concept_data` 所需的所有字段？
- stock_code ✓
- stock_name ✓
- concept ✓
- price ✓
- turnover_rate ✓
- net_inflow ✓
- total_reads ✓
- page_count ✓

## 问题描述
CSV导入逻辑和分析计算逻辑之间存在数据流断裂：

### 当前的 DataImportService 创建的表：
1. `stocks` - 股票基本信息
2. `concepts` - 概念信息  
3. `stock_concepts` - 股票-概念关联
4. `daily_stock_data` - **按stock_id+trade_date组织** (price, turnover_rate, net_inflow, pages_count, total_reads)
5. `stock_concept_raw_data` - 原始导入数据（未拆分）
6. `raw_import_data` - 原始导入数据记录

### 分析服务需要的数据格式：
`DailyAnalysisService._generate_concept_summaries()` 需要从 `stock_concept_data` 表查询：
- stock_code
- stock_name
- concept
- 财务指标: price, turnover_rate, net_inflow, total_reads, page_count
- import_date

这个表按 **stock_code + concept + import_date** 组织，而不是按 stock_id

### 根本差异：
- `DailyStockData`: 存储stock级别的数据 (1个stock, 1个trade_date = 1条记录)
- `StockConceptData`: 存储stock-concept级别的数据 (1个stock_code, 1个concept, 1个import_date = 1条记录)

一只股票可能属于多个概念，所以：
- DailyStockData: 100个股票 → 100条记录
- StockConceptData: 100个股票 × 5个概念/股票 = 500条记录

### 解决方案：
需要在 `DataImportService.import_csv_data()` 中添加一个步骤，将stock级别的财务数据映射到stock-concept级别的 `stock_concept_data` 表：

```python
# 对于每条CSV行（对应1个stock-concept组合）：
# 创建或更新 StockConceptData 记录
# stock_code, stock_name, concept, price, turnover_rate, net_inflow, total_reads, page_count, import_date
```

这样就能连接导入和分析两个系统。
