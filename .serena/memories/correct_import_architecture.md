# 正确的导入架构理解

## 三类数据源和导入逻辑

### 1. CSV 文件 - 股票与概念的关系数据
**内容：** 股票代码、股票名称、概念名称、行业等 **静态关系数据**
**不包含：** 日期信息、交易数据
**导入逻辑：** 只填充关系表
- stocks 表 - 股票基础信息
- concepts 表 - 概念基础信息  
- stock_concepts 表 - 股票-概念关系
- stock_concept_raw_data 表 - 原始CSV数据备份

**重点：** CSV导入只是建立股票和概念的对应关系，**不产生任何交易数据或排名数据**

---

### 2. EEE.txt 文件 - 热度数据（按日期）
**内容：** 股票代码 + 交易日期 + 热度值
**格式：** `股票代码[Tab]交易日期[Tab]热度值`
**导入目标表：**
- eee_daily_trading 表 - 存储原始热度数据
- eee_import_record 表 - 记录导入元信息

**导入后的作用：** 为 DailyAnalysisService 提供日期维度的交易数据基础

---

### 3. TTV.txt 文件 - 交易数据（按日期）
**内容：** 股票代码 + 交易日期 + 交易值
**格式：** `股票代码[Tab]交易日期[Tab]数值`
**导入目标表：**
- ttv_daily_trading 表 - 存储原始交易数据
- ttv_import_record 表 - 记录导入元信息

**导入后的作用：** 为 DailyAnalysisService 提供日期维度的交易数据基础

---

## 数据流转和概念排名的生成

### 完整的数据加工流程

```
第一步：导入 CSV（建立关系）
CSV文件
  ↓
DataImportService.import_csv_data()
  └─→ 创建/更新：
      ├─ stocks （股票信息）
      ├─ concepts （概念信息）
      ├─ stock_concepts （关系表）
      └─ stock_concept_raw_data （原始备份）

第二步：导入 EEE.txt（获取热度数据）
EEE.txt (股票代码 + 日期 + 热度值)
  ↓
import_eee.py
  └─→ 插入：
      ├─ eee_daily_trading （热度数据）
      └─ eee_import_record （导入记录）

第三步：导入 TTV.txt（获取交易数据）
TTV.txt (股票代码 + 日期 + 交易值)
  ↓
import_ttv.py
  └─→ 插入：
      ├─ ttv_daily_trading （交易数据）
      └─ ttv_import_record （导入记录）

第四步：触发分析计算（生成排名和汇总）
EEE/TTV 数据 + stock_concepts 关系
  ↓
DailyAnalysisService.trigger_full_analysis()
  ├─→ _calculate_concept_rankings()
  │   └─→ 生成 DailyConceptRanking （概念内个股排名）
  │
  └─→ _generate_concept_summaries()
      └─→ 生成 DailyConceptSummary （概念汇总统计）
```

---

## 关键理解：stock_concept_data 的真实作用

**问题：** DailyAnalysisService 的 `_generate_concept_summaries()` 方法查询 `stock_concept_data` 表，但这个表：
- CSV 导入中没有创建
- EEE/TTV 导入中也没有创建
- 一直是空的

**原因分析：**
1. CSV 只有关系数据，没有交易数据
2. EEE/TTV 有交易数据，但只创建了各自的表（eee_daily_trading、ttv_daily_trading）
3. 没有任何地方把这些数据合并到 stock_concept_data

**stock_concept_data 的设计意图可能是：**
- 存储 stock_concepts 关系 与 EEE/TTV 交易数据的 **合并视图**
- 目的是便于按 股票-概念-日期 维度查询财务数据
- 用于分析系统的数据源

**但实际上：**
- 这个表从未被填充过
- DailyAnalysisService 的查询会失败
- 系统的分析功能无法正常工作

---

## 现在的架构缺陷

```
应该：
CSV 关系 + EEE/TTV 交易数据
        ↓
    合并到 stock_concept_data
        ↓
DailyAnalysisService 查询 stock_concept_data
        ↓
生成排名和汇总

实际：
CSV 关系 + EEE/TTV 交易数据
        ↓
分别存储在各自的表中（stock_concepts、eee_daily_trading、ttv_daily_trading）
        ↓
DailyAnalysisService 试图查询 stock_concept_data（空表）
        ↓
分析功能失效 ❌
```

---

## 解决方案的考虑方向

1. **在 EEE/TTV 导入后合并数据到 stock_concept_data**
   - 在 import_eee.py 或 import_ttv.py 中，导入数据后，合并 stock_concepts 关系和交易数据

2. **在 DailyAnalysisService 中直接用 eee_daily_trading/ttv_daily_trading + stock_concepts 的 JOIN**
   - 不依赖 stock_concept_data，直接从原始表查询
   - 但这样比较复杂，需要多表 JOIN

3. **在分析触发时动态生成 stock_concept_data**
   - DailyAnalysisService.trigger_full_analysis() 开始时，先构建 stock_concept_data
   - 然后再执行分析逻辑

4. **保留 stock_concept_data，在 EEE/TTV 导入后填充**
   - 最符合设计的做法
   - EEE/TTV 导入完成后，把合并后的数据写入 stock_concept_data
