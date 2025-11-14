# 后端数据导入逻辑检查 - 完整分析总结

检查日期：2025-11-14
检查范围：数据导入API、导入服务、分析计算服务
问题：`daily_concept_summaries` 和 `daily_concept_rankings` 表无数据

---

## 执行总结

### 问题确认
✅ 已确认问题存在
- `daily_concept_summaries` 表应该由 RankingCalculatorService 填充
- `daily_concept_rankings` 表应该由 RankingCalculatorService 填充
- 两个表都没有数据，说明分析计算流程失败或未触发

### 根本原因（3个）

1. **热度值初始化为0**
   - 文件：`/Users/peakom/work/stock-analysis-system/backend/app/services/data_import.py`
   - 行号：369
   - 问题：CSV导入时 `heat_value=0`，但分析代码过滤 `heat_value > 0`
   - 结果：没有任何记录被选中进行排名计算

2. **CSV和TXT数据融合策略不清**
   - 文件：`/Users/peakom/work/stock-analysis-system/backend/app/services/data_import.py`
   - 行号：580-681
   - 问题：TXT导入删除现有记录而非更新，导致CSV数据丢失
   - 结果：两个导入的数据无法互补

3. **分析流程依赖不满足**
   - 文件：`/Users/peakom/work/stock-analysis-system/backend/app/services/ranking_calculator.py`
   - 行号：53
   - 问题：过滤条件 `heat_value > 0` 过于严格
   - 结果：即使有热度值，也可能因为数据格式问题无法被统计

---

## 关键代码位置

### 数据导入相关

#### 1. CSV导入入口
- 文件：`/Users/peakom/work/stock-analysis-system/backend/app/api/api_v1/endpoints/data_import.py`
- 行号：17-85
- 方法：`import_csv_data()`
- 作用：接收上传的CSV文件

#### 2. CSV数据处理
- 文件：`/Users/peakom/work/stock-analysis-system/backend/app/services/data_import.py`
- 行号：54-451
- 方法：`DataImportService.import_csv_data()`
- 关键点：
  - 第87行：列名规范化（支持中英文）
  - 第143-156行：收集股票和概念信息
  - 第361-372行：**创建DailyStockData（heat_value=0）** ❌

#### 3. TXT数据处理
- 文件：`/Users/peakom/work/stock-analysis-system/backend/app/services/data_import.py`
- 行号：453-770
- 方法：`DataImportService.import_txt_data()`
- 关键点：
  - 第580-600行：**删除旧数据逻辑** ❌
  - 第670-681行：**创建新DailyStockData** ❌

#### 4. 批量导入
- 文件：`/Users/peakom/work/stock-analysis-system/backend/app/services/data_import.py`
- 行号：910-1015
- 方法：`DataImportService.import_daily_batch()`
- 关键点：
  - 第943行：调用CSV导入
  - 第975行：调用TXT导入
  - **第1001行：触发分析计算** ✅

### 分析计算相关

#### 1. 排名计算入口
- 文件：`/Users/peakom/work/stock-analysis-system/backend/app/services/ranking_calculator.py`
- 行号：213-255
- 方法：`RankingCalculatorService.trigger_full_analysis()`
- 作用：触发完整的分析流程

#### 2. 日概念排名计算
- 文件：`/Users/peakom/work/stock-analysis-system/backend/app/services/ranking_calculator.py`
- 行号：24-89
- 方法：`RankingCalculatorService.calculate_daily_rankings()`
- 关键SQL（第47-54行）：
  ```python
  concept_stocks = db.query(
      StockConcept.stock_id, DailyStockData.heat_value
  ).join(DailyStockData, ...).filter(
      StockConcept.concept_id == concept.id,
      DailyStockData.trade_date == trade_date,
      DailyStockData.heat_value > 0  # ❌ 关键过滤条件
  ).order_by(desc(DailyStockData.heat_value)).all()
  ```
- 输出：writes to `daily_concept_rankings` table

#### 3. 概念汇总计算
- 文件：`/Users/peakom/work/stock-analysis-system/backend/app/services/ranking_calculator.py`
- 行号：91-168
- 方法：`RankingCalculatorService.calculate_concept_summaries()`
- 关键SQL（第108-119行）：
  ```python
  concept_summaries = db.query(
      DailyConceptRanking.concept_id,
      func.sum(DailyConceptRanking.heat_value),
      func.count(DailyConceptRanking.stock_id),
      ...
  ).filter(
      DailyConceptRanking.trade_date == trade_date
  ).group_by(DailyConceptRanking.concept_id).all()
  ```
- 输出：writes to `daily_concept_summaries` table

---

## 数据模型情况

系统中有**3套独立的表定义**（存在冗余）：

### 表集1：concept_analysis.py（推荐使用）
- `daily_concept_rankings`
- `daily_concept_summaries`
- 特点：使用外键（concept_id, stock_id）
- 用途：分析计算输出

### 表集2：stock_data.py（实际导入使用）
- `stock_concept_daily_rankings` (未被导入代码使用)
- `stock_concept_daily_stats` (未被导入代码使用)
- 特点：使用字符串字段（concept_name, stock_code）
- 用途：存储原始导入数据

### 表集3：daily_analysis.py（已过时）
- `daily_stock_concept_financial_rankings`
- `daily_concept_financial_summaries`
- 特点：金融数据版本
- 用途：已过时

**问题：导入写一套表，分析读另一套表**

---

## 完整数据流

```
1. 用户上传CSV和TXT文件
   |
   v
2. DataImportService.import_daily_batch()
   ├─ CSV导入 → 写入Stock, Concept, StockConcept, DailyStockData
   │           (heat_value=0) ❌
   ├─ TXT导入 → 更新/创建DailyStockData
   │           (heat_value=从TXT) ✅ 但有覆盖问题
   │
   v
3. RankingCalculatorService.trigger_full_analysis()
   ├─ calculate_daily_rankings()
   │  ├─ 查询: SELECT heat_value FROM daily_stock_data WHERE heat_value > 0
   │  │        (可能为空) ❌
   │  └─ 写入: daily_concept_rankings
   │           (0条或不完整)
   │
   └─ calculate_concept_summaries()
      ├─ 查询: SELECT * FROM daily_concept_rankings
      │        (依赖排名数据)
      └─ 写入: daily_concept_summaries
              (0条或不完整)
```

---

## 快速诊断清单

要确认问题，运行以下SQL：

```sql
-- 1. 检查CSV导入的数据
SELECT COUNT(*), SUM(CASE WHEN heat_value = 0 THEN 1 ELSE 0 END) as zero_heat_count
FROM daily_stock_data 
WHERE trade_date = '2025-08-21';

-- 结果：如果zero_heat_count > 0，证实问题1 ❌

-- 2. 检查分析是否执行
SELECT COUNT(*) 
FROM daily_concept_rankings 
WHERE trade_date = '2025-08-21';

-- 结果：如果为0，说明分析失败 ❌

-- 3. 检查汇总数据
SELECT COUNT(*) 
FROM daily_concept_summaries 
WHERE trade_date = '2025-08-21';

-- 结果：如果为0，说明汇总为空 ❌

-- 4. 检查关键数据
SELECT stock_code, heat_value, hot_page_views, total_pages
FROM daily_stock_data 
WHERE trade_date = '2025-08-21'
LIMIT 5;

-- 查看实际数据情况
```

---

## 修复建议

### 立即修复（P0 - 影响功能）

#### Issue 1：热度值初始化
```python
# 文件: data_import.py 第369行
# 当前:
daily_data = DailyStockData(
    ...,
    heat_value=0  # ❌ 错误
)

# 修复:
daily_data = DailyStockData(
    ...,
    heat_value=hot_page_views or 0  # 使用CSV中的热帖阅读数
)
```

#### Issue 2：TXT导入的融合
```python
# 文件: data_import.py 第670-681行
# 当前: 创建新记录（会覆盖CSV数据）
daily_data = DailyStockData(...)

# 修复: 更新现有记录
existing_data = db.query(DailyStockData).filter(...).first()
if existing_data:
    existing_data.heat_value = heat_value  # 更新热度
else:
    daily_data = DailyStockData(...)  # 仅在不存在时创建
```

#### Issue 3：删除逻辑修复
```python
# 文件: data_import.py 第580-600行
# 当前: 删除旧数据（导致CSV数据丢失）
db.query(DailyStockData).filter(...).delete()  # ❌ 过于激进

# 修复: 只删除需要覆盖的字段，或改为更新
if allow_overwrite:
    # 选项1：删除指定股票的热度数据
    for stock_code in txt_stock_codes:
        data = db.query(DailyStockData).filter(...).first()
        if data:
            data.heat_value = heat_value  # 更新而非删除
    
    # 选项2：完全删除（只在明确需要时）
    # db.query(DailyStockData).filter(...).delete()
```

### 短期修复（P1 - 改进流程）

1. **统一表结构**
   - 决定使用哪套表（推荐 `daily_concept_rankings/summaries`）
   - 删除冗余的表定义
   - 更新导入代码使用统一的表

2. **改进数据融合**
   - 定义清晰的CSV+TXT数据融合规则
   - CSV提供：股票信息、概念、页数、阅读数
   - TXT提供：热度值
   - 两者合并：完整的每日数据

3. **加强错误检查**
   - 导入后检查是否有heat_value=0的记录
   - 分析前检查是否有足够的数据
   - 失败时给出清晰的错误信息

### 中期重构（P2 - 架构改进）

1. **重新设计数据导入流程**
   - 分离原始数据导入和数据融合
   - 建立清晰的数据转换管道

2. **统一分析流程**
   - 确保所有分析使用同一套表和模型
   - 建立数据质量检查机制

3. **改进API返回**
   - 导入后返回数据质量报告
   - 分析前返回数据检查结果

---

## 文件清单

### 需要检查的文件

1. `/Users/peakom/work/stock-analysis-system/backend/app/models/data_import.py`
   - 导入记录模型定义

2. `/Users/peakom/work/stock-analysis-system/backend/app/services/stock_data_import.py`
   - 旧的导入服务（可能已过时）

3. `/Users/peakom/work/stock-analysis-system/backend/app/api/api_v1/endpoints/data_import.py`
   - 导入API端点定义

4. `/Users/peakom/work/stock-analysis-system/backend/app/services/data_import.py`
   - 实际使用的导入服务 ✅

5. `/Users/peakom/work/stock-analysis-system/backend/app/services/ranking_calculator.py`
   - 排名计算服务 ✅

6. `/Users/peakom/work/stock-analysis-system/backend/app/models/concept_analysis.py`
   - 概念分析模型定义 ✅

7. `/Users/peakom/work/stock-analysis-system/backend/app/models/stock_data.py`
   - 股票数据模型定义 ✅

8. `/Users/peakom/work/stock-analysis-system/backend/app/models/daily_analysis.py`
   - 每日分析模型定义 ✅

---

## 总结

**系统可以成功导入数据，但分析计算失败，导致最终的汇总表为空。**

根本原因是多个环节的数据处理问题相互叠加：
1. 导入时热度值设为0
2. 分析时过滤heat_value > 0
3. CSV和TXT数据融合不完整
4. 表结构定义混乱

**建议优先修复热度值初始化问题，这是最直接的解决方案。**

