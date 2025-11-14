# 问题可视化分析

## 问题1：热度值初始化为0

### CSV导入时的数据转换

```
CSV文件行
│
├─ 股票代码: 600000 ───────────────┐
├─ 股票名称: 贵州茅台              │
├─ 热帖首页阅读数: 1000 ──────────┼─> DataImportService.import_csv_data()
├─ 全部页数: 5                    │
├─ 价格: 2000.50                  │
└─ 行业: 白酒                      │
                                   v
                  DailyStockData对象创建
                  ├─ stock_code: 600000
                  ├─ stock_name: 贵州茅台
                  ├─ hot_page_views: 1000
                  ├─ total_pages: 5
                  ├─ price: 2000.50
                  ├─ industry: 白酒
                  └─ heat_value: 0  ❌ 错误！应该是1000或某个计算值
                                    (第369行)
                                    
                            ↓ 写入数据库
                       
                daily_stock_data表
                │
                ├─ 股票1 | heat_value=0 ❌
                ├─ 股票2 | heat_value=0 ❌
                └─ 股票3 | heat_value=0 ❌
```

### 分析时的查询失败

```
RankingCalculatorService.calculate_daily_rankings()
           │
           v
   查询: SELECT * FROM daily_stock_data
         WHERE heat_value > 0
         AND concept_id = 概念ID
         AND trade_date = 2025-08-21
           │
           v
    结果：∅ (空集) ❌
    
    原因：
    ├─ daily_stock_data.heat_value = 0
    └─ 过滤条件: heat_value > 0
    
    因此：没有任何记录返回
           │
           v
   daily_concept_rankings表: 0条记录
           │
           v
   daily_concept_summaries表: 0条记录
```

---

## 问题2：CSV和TXT数据融合不清

### 时间序列导入流程

```
时间t1: 用户上传CSV和TXT文件
        │
        ├─ CSV: 股票代码,股票名称,页数,概念...
        └─ TXT: 股票代码,日期,热度值
        
时间t2: import_daily_batch() 执行
        │
        ├─ Step 1: import_csv_data() ──────────┐
        │   │                                    │
        │   v                                    v
        │   DailyStockData表                  DailyStockData表
        │   ├─ 600000 | heat_value=0         ├─ 600000 | heat_value=0
        │   ├─ 600001 | heat_value=0         ├─ 600001 | heat_value=0
        │   └─ 600002 | heat_value=0         └─ 600002 | heat_value=0
        │                                       (CSV导入完成)
        │
        ├─ Step 2: import_txt_data() ──────────┐
        │   │                                    │
        │   v (第580-600行)                     v
        │   删除现有数据 ❌                    DailyStockData表
        │   DELETE FROM daily_stock_data      (被删除的CSV数据)
        │   WHERE stock_id IN (600000,600001)
        │   AND trade_date = 2025-08-21
        │       │
        │       v (第670-681行)
        │       创建新记录 ❌
        │       INSERT INTO daily_stock_data
        │       (stock_id, trade_date, 
        │        heat_value=459400,
        │        price=0, pages=0, ...)  <- 丢失CSV字段!
        │           │
        │           v
        │           DailyStockData表
        │           ├─ 600000 | heat_value=459400 | pages=0 ❌
        │           ├─ 600001 | heat_value=459400 | pages=0 ❌
        │           └─ 600002 | heat_value=0 (未在TXT中)
        │
        v
时间t3: trigger_full_analysis()
        │
        └─ 数据不完整: 有热度值但丢失其他字段
```

### 正确的融合应该是

```
CSV导入
  ├─ stock_code: 600000
  ├─ stock_name: 贵州茅台
  ├─ price: 2000.50
  ├─ pages: 5
  ├─ hot_page_views: 1000
  └─ concept: 白酒
      │
      v
      DailyStockData
      ├─ stock_code: 600000
      ├─ stock_name: 贵州茅台
      ├─ price: 2000.50
      ├─ pages: 5
      ├─ hot_page_views: 1000
      └─ heat_value: 1000  ✅

TXT导入 (同一股票、同一日期)
  ├─ stock_code: 600000
  ├─ date: 2025-08-21
  └─ heat_value: 459400
      │
      v (更新而非删除)
      DailyStockData (更新)
      ├─ stock_code: 600000
      ├─ stock_name: 贵州茅台  ✅ 保留
      ├─ price: 2000.50         ✅ 保留
      ├─ pages: 5               ✅ 保留
      ├─ hot_page_views: 1000   ✅ 保留
      └─ heat_value: 459400     ✅ 更新
```

---

## 问题3：分析流程依赖链

### 理想的依赖链

```
DailyStockData (完整数据)
  ├─ stock_code: 600000
  ├─ trade_date: 2025-08-21
  ├─ heat_value: 459400 ✅
  ├─ hot_page_views: 1000
  └─ concept_name: 白酒
      │
      v (filter: heat_value > 0)
  
calculate_daily_rankings()
  │
  ├─ 查询所有概念 (白酒, 芯片, AI...)
  │
  ├─ 对每个概念:
  │  ├─ 查询: SELECT stock_code, heat_value
  │  │        FROM daily_stock_data
  │  │        WHERE concept=XX AND heat_value>0
  │  │        ORDER BY heat_value DESC
  │  │
  │  └─ 结果: [(600000, 459400), (600001, 200000), ...]
  │
  ├─ 分配排名: rank=1,2,3,...
  │
  └─> 写入 daily_concept_rankings (✅ 成功)
         ├─ 概念: 白酒
         ├─ 股票: 600000
         ├─ 排名: 1
         ├─ 热度: 459400
         └─ 日期: 2025-08-21
             │
             v
calculate_concept_summaries()
  │
  ├─ 查询: SELECT concept_id, 
  │        SUM(heat_value), COUNT(*),
  │        AVG(heat_value), MAX, MIN
  │        FROM daily_concept_rankings
  │        WHERE trade_date=2025-08-21
  │        GROUP BY concept_id
  │
  ├─ 结果: [(白酒, 总热度=1000000, 股票数=50, ...),
  │         (芯片, 总热度=800000, 股票数=30, ...),
  │         ...]
  │
  └─> 写入 daily_concept_summaries (✅ 成功)
         ├─ 概念: 白酒
         ├─ 总热度: 1000000
         ├─ 股票数: 50
         ├─ 平均热度: 20000
         ├─ 最高热度: 459400
         ├─ 最低热度: 100
         ├─ 是否创新高: true/false
         └─ 日期: 2025-08-21
```

### 实际的依赖链（有问题）

```
DailyStockData (不完整)
  ├─ stock_code: 600000
  ├─ trade_date: 2025-08-21
  ├─ heat_value: 0 ❌ (或者被删除)
  ├─ hot_page_views: 1000
  └─ concept_name: 白酒
      │
      v (filter: heat_value > 0)
      │
      └─ 结果: ∅ (空集) ❌
           │
           v
calculate_daily_rankings()
  │
  ├─ 查询: SELECT ... WHERE heat_value > 0
  │        结果: 空集
  │
  └─> 写入 daily_concept_rankings (0条记录) ❌
           │
           v
calculate_concept_summaries()
  │
  ├─ 查询: SELECT ... FROM daily_concept_rankings
  │        结果: 空集
  │
  └─> 写入 daily_concept_summaries (0条记录) ❌
```

---

## 表结构混乱（加剧问题）

### 现状：3套独立的表定义

```
导入代码使用                    分析代码使用
  ↓                               ↓
stock_data.py                concept_analysis.py
  ├─ Stock (stocks)           ├─ DailyConceptRanking
  ├─ Concept (concepts)       │   (daily_concept_rankings)
  ├─ StockConcept             │
  │ (stock_concepts)          ├─ DailyConceptSummary
  ├─ DailyStockData           │   (daily_concept_summaries)
  │ (daily_stock_data)        │
  │                           └─ 使用外键: concept_id, stock_id
  └─ 使用字符串字段:
     concept_name, stock_code

                    daily_analysis.py
                    ├─ DailyConceptFinancialRanking
                    │   (daily_stock_concept_financial_rankings)
                    └─ DailyConceptFinancialSummary
                        (daily_concept_financial_summaries)
                        (已过时)

问题：
  导入代码     ────────X────────>  分析代码
  (Stock表)               (DailyConceptRanking表)
  (DailyStockData)        (DailyConceptSummary表)
  
  两个系统没有共同的数据输出点！
```

### 理想状态：统一的表结构

```
导入代码                分析代码
  ├─ Stock              ├─ DailyConceptRanking
  ├─ Concept           └─ DailyConceptSummary
  ├─ StockConcept
  └─ DailyStockData ──────────────────┐
                                       v
                         (热度值完整，支持JOIN)
                                       │
                                       v
                         calculate_daily_rankings()
                                       │
                                       v
                    ✅ 写入 daily_concept_rankings
                                       │
                                       v
                         calculate_concept_summaries()
                                       │
                                       v
                    ✅ 写入 daily_concept_summaries
```

---

## 优先级修复方案

### 优先级1（立即修复）

```
现状:
  DailyStockData.heat_value = 0
         │
         └─> analyze_daily_rankings() 查询 WHERE heat_value > 0 失败

解决方案:
  DailyStockData.heat_value = hot_page_views
         │
         └─> analyze_daily_rankings() 查询成功
             │
             └─> 生成daily_concept_rankings ✅
                 │
                 └─> 生成daily_concept_summaries ✅

修复文件: data_import.py 第369行
```

### 优先级2（短期改进）

```
现状: TXT导入删除CSV数据
      CSV: 股票信息 + 页数
      TXT: 热度值
      
      删除 ──────────────> 丢失信息

解决方案: TXT导入更新字段
          CSV: 股票信息 + 页数 + 热度=0
          TXT: 热度值 ──> 更新热度字段
          
          融合 ──────────────> 完整数据 ✅

修复文件: data_import.py 第580-681行
```

### 优先级3（中期重构）

```
现状: 3套表定义，两个系统独立

解决方案: 统一使用 daily_concept_rankings/summaries
         ├─ 这套表由ranking_calculator.py维护
         ├─ 使用外键引用Stock和Concept
         └─ 与导入代码完整衔接

修复文件: models/*.py, services/*.py
```

