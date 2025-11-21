# CSV导入中的日期处理逻辑

## 核心问题
**CSV文件本身可能没有日期列，那日期信息从哪里来？**

## 日期获取的三层逻辑（优先级从高到低）

### 层级1：从CSV文件的'date'列读取（如果存在）
**条件：** CSV中包含 'date' 列
**代码位置：** `data_import.py` 第290-291行
```python
if 'date' in df.columns:
    trade_date = pd.to_datetime(row['date']).date()
```
**说明：** 如果CSV中有日期列，就使用CSV中的日期

### 层级2：从文件名提取日期
**条件：** 使用 `import_csv_local.py` 脚本时没有指定 `--date` 参数
**代码位置：** `data_import.py` 第62-65行
```python
if not trade_date:
    import_date = self._extract_date_from_filename(filename)
    if not import_date:
        import_date = date.today()
```

**支持的文件名格式（`_extract_date_from_filename` 方法）：**
- `2025-08-28` (YYYY-MM-DD)
- `2025_08_28` (YYYY_MM_DD)
- `20250828` (YYYYMMDD)
- `08-28-2025` (MM-DD-YYYY)
- `08/28/2025` (MM/DD/YYYY)

**例子：**
- 文件名：`2025-04-16-16-55.csv` → 提取日期 `2025-04-16`
- 文件名：`data_20240828.csv` → 提取日期 `2024-08-28`
- 文件名：`random_name.csv` → 无法提取，使用今天的日期

### 层级3：从命令行 `--date` 参数指定
**条件：** 使用 `import_csv_local.py` 脚本时指定了 `--date` 参数
**代码位置：** `scripts/import_csv_local.py` 第244行
```python
parser.add_argument(
    '--date',
    type=parse_date,
    help='指定交易日期 (格式: YYYY-MM-DD)，不指定则从文件名解析'
)
```

**使用示例：**
```bash
python3 scripts/import_csv_local.py --file data.csv --date 2024-10-16
```

## 实际导入流程中的日期使用

### 当有日期列时（逐行处理）
```python
# 对CSV中的每一行
for index, row in df.iterrows():
    if 'date' in df.columns:
        # 使用该行的日期
        trade_date = pd.to_datetime(row['date']).date()
        
        # 创建 DailyStockData、StockConceptRawData 等记录
        daily_data = DailyStockData(
            stock_id=stock.id,
            trade_date=trade_date,  # ← 使用该行日期
            ...
        )
```

### 当没有日期列时（全文件统一日期）
```python
# 文件级别的日期（从文件名或参数提取）
import_date = self._extract_date_from_filename(filename)

# CSV中的每一行都使用这个统一日期
for index, row in df.iterrows():
    # 如果没有日期列，默认为 import_date
    trade_date = import_date  # 整个CSV文件使用同一个日期
    
    daily_data = DailyStockData(
        stock_id=stock.id,
        trade_date=trade_date,  # ← 使用文件级日期
        ...
    )
```

## 用于 stock_concept_data 表的日期处理

**关键点：** `stock_concept_data` 表的 `import_date` 字段就是来自上述日期处理逻辑

```python
# 创建 stock_concept_data 记录时
stock_concept_data = StockConceptData(
    stock_code=stock_code,
    stock_name=stock_name,
    concept=concept_name,
    price=price,
    turnover_rate=turnover_rate,
    net_inflow=net_inflow,
    import_date=trade_date,  # ← 来自上述三层逻辑提取的日期
    ...
)
```

## 数据流示意

```
CSV文件
  ↓
[检查日期列]
  ├─ 有 'date' 列？
  │   ├─ 是 → 逐行使用 row['date']
  │   └─ 否 → 使用文件级日期（来自 _extract_date_from_filename）
  │           或使用 --date 参数指定的日期
  │           或使用 today()
  ↓
得到 trade_date（可能是CSV中的日期，或文件名提取的日期）
  ↓
使用该日期填充：
  ├─ DailyStockData.trade_date
  ├─ StockConceptRawData.trade_date  
  ├─ RawImportData.trade_date
  └─ stock_concept_data.import_date （如果实现的话）
```

## 关键特点

1. **单源真实：** 日期最终来自 CSV 本身或文件名，不是凭空生成
2. **灵活性：** 支持多种日期格式和来源
3. **一致性：** 同一行数据的所有表记录使用相同的日期
4. **可追踪性：** import_date 清晰标记了数据的导入日期

## 现有实现中的缺陷

**当前状态：**
- ✅ DailyStockData 表 已正确填充 trade_date
- ✅ StockConceptRawData 表 已正确填充 trade_date
- ✅ RawImportData 表 已正确填充 trade_date
- ❌ stock_concept_data 表 **完全没有被填充**

**为什么是缺陷：**
- DailyAnalysisService 需要从 stock_concept_data 查询数据
- stock_concept_data 中的 import_date 应该与 trade_date 保持一致
- 如果不填充这个表，分析服务就无法工作
