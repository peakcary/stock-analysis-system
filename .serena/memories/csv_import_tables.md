# CSV 导入实际存储的表信息

## CSV 导入时的表操作总结

### 1. ImportBatch 表（导入批次管理）
**位置：** data_import.py 第187行
```python
import_batch = ImportBatch(
    import_date=import_date,
    import_type='csv',
    file_name=filename,
    record_count=len(df),
    status='pending'
)
self.db.add(import_batch)
self.db.flush()
```
**记录内容：** 导入的元信息（日期、文件名、记录数、状态等）

---

### 2. Stock 表（股票基本信息）
**位置：** data_import.py 第239行
```python
stock = Stock(
    stock_code=stock_code,                    # 规范化的代码 (600036)
    original_stock_code=stock_code_raw,       # 原始代码 (SH600036)
    stock_code_prefix=stock_code_prefix,      # 前缀 (SH)
    stock_name=stock_name,
    industry=industry,
    is_convertible_bond=is_convertible_bond
)
self.db.add(stock)
```
**特点：** 
- 创建新股票或更新现有股票信息
- 通过 stock_code（规范化）检查是否存在

---

### 3. Concept 表（概念信息）
**位置：** data_import.py 第269行
```python
concept = Concept(concept_name=concept_name)
self.db.add(concept)
```
**特点：**
- 每个唯一的概念名称创建一条记录
- 通过 concept_name 检查是否存在

---

### 4. StockConcept 表（股票-概念关系表）
**位置：** data_import.py 第285行
```python
stock_concept = StockConcept(
    stock_id=stock.id,
    concept_id=concept.id
)
self.db.add(stock_concept)
```
**特点：**
- 关键关系表：存储哪个股票属于哪个概念
- 增量模式：只添加新关系，不删除旧关系
- 只存储 ID 外键，没有财务数据

---

### 5. DailyStockData 表（日线数据）
**位置：** data_import.py 第361行
```python
daily_data = DailyStockData(
    stock_id=stock.id,
    trade_date=trade_date,           # ← CSV中的日期或文件名提取
    price=price,
    turnover_rate=turnover_rate,
    net_inflow=net_inflow,
    pages_count=pages_count,
    total_reads=total_reads,
    heat_value=0                      # ← 默认为0，等待EEE.txt填充
)
self.db.add(daily_data)
```
**特点：**
- 每条 CSV 行生成一条记录（如果未处理过该股票-日期组合）
- 按股票-日期唯一性检查
- **heat_value 初始化为 0，后续由 EEE.txt 填充**

---

### 6. RawImportData 表（导入原始数据追踪）
**位置：** data_import.py 第302行
```python
raw_import_record = RawImportData(
    import_batch_id=import_batch.id,
    row_number=index + 2,              # CSV 行号
    trade_date=trade_date,
    stock_code_raw=stock_code_raw,
    stock_code_normalized=stock_code,
    stock_code_prefix=stock_code_prefix,
    stock_name=stock_name,
    industry=industry,
    price=price,
    turnover_rate=turnover_rate,
    net_inflow=net_inflow,
    pages_count=pages_count,
    total_reads=total_reads,
    concept=concept_name,
    source_type='csv',
    source_file=filename
)
raw_import_records.append(raw_import_record)
# 批量保存：self.db.bulk_save_objects(raw_import_records)
```
**特点：**
- 审计追踪：记录原始数据
- 关联到 ImportBatch，便于追溯导入来源
- 保留了原始代码、前缀等信息

---

### 7. StockConceptRawData 表（概念原始数据）
**位置：** data_import.py 第323行
```python
raw_record = StockConceptRawData(
    import_date=import_date,
    trade_date=trade_date,
    stock_code=stock_code,
    original_stock_code=stock_code_raw,
    stock_code_prefix=stock_code_prefix,
    stock_name=stock_name,
    concept=concept_name,              # ← 关键：包含概念信息
    industry=industry,
    price=price,
    turnover_rate=turnover_rate,
    net_inflow=net_inflow,
    pages_count=pages_count,
    total_reads=total_reads,
    file_name=filename,
    row_number=index + 2
)
raw_data_records.append(raw_record)
# 批量保存：self.db.bulk_save_objects(raw_data_records)
```
**特点：**
- **这是最完整的原始数据备份**
- 每行 CSV 都对应一条记录
- 包含股票-概念-日期-交易数据的完整信息

---

## 总结：CSV 导入涉及的 7 张表

| 表名 | 作用 | 存储的信息 | 行数关系 |
|------|------|----------|---------|
| **import_batches** | 导入元数据 | 批次信息 | 1行 |
| **stocks** | 股票基础 | 股票代码、名称、行业 | M (唯一股票数) |
| **concepts** | 概念基础 | 概念名称 | N (唯一概念数) |
| **stock_concepts** | 关系表 | 股票ID + 概念ID | M×N (最多) |
| **daily_stock_data** | 日线数据 | 股票+日期+交易数据 | M×D (最多，M=股票数，D=日期数) |
| **raw_import_data** | 审计追踪 | 导入原始行信息 | CSV行数 |
| **stock_concept_raw_data** | 数据备份 | 完整股票-概念-日期-交易数据 | CSV行数 |

---

## 关键发现

### CSV 导入完成后的数据分布：
- ✅ **stocks** 表有数据 - 股票基础信息
- ✅ **concepts** 表有数据 - 概念信息
- ✅ **stock_concepts** 表有数据 - 股票-概念关系
- ✅ **daily_stock_data** 表有数据 - 日线数据（heat_value=0）
- ✅ **stock_concept_raw_data** 表有数据 - 原始数据备份

### CSV 导入**NOT**包含的数据：
- ❌ **stock_concept_data** 表 - **完全为空！**
  - 这是 DailyAnalysisService 需要的表
  - 用于按股票-概念-日期维度的聚合分析

---

## stock_concept_data 应该何时被填充？

根据数据流：
1. CSV 导入 → 建立股票、概念、关系 + 日线数据
2. EEE.txt 导入 → 填充 daily_stock_data.heat_value
3. **应该在这里：** 合并两者的数据到 stock_concept_data

**当前缺失：** stock_concept_data 表完全没有逻辑来填充它

### 可能的设计意图：
stock_concept_data 应该在 EEE.txt 导入完成后被填充，包含：
```python
StockConceptData(
    stock_code = 来自 Stock 表
    stock_name = 来自 Stock 表
    concept = 来自 Concept 表（通过 StockConcept 关系）
    price = 来自 DailyStockData 表
    turnover_rate = 来自 DailyStockData 表
    net_inflow = 来自 DailyStockData 表
    page_count = 来自 DailyStockData 表
    total_reads = 来自 DailyStockData 表
    import_date = 交易日期
)
```

这样就能为 DailyAnalysisService 提供完整的数据源。
