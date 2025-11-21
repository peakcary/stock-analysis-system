# stock_concept_data 表设计详解

## 表定义

表名: `stock_concept_data`
模型文件: `backend/app/models/simple_import.py` (lines 23-38)

### 字段清单

| 字段名 | 类型 | 说明 | 用途 |
|--------|------|------|------|
| **id** | Integer | 主键 | 唯一标识 |
| **stock_code** | String(20) | 股票代码 | 规范化的股票代码（如600036） |
| **stock_name** | String(100) | 股票名称 | 股票的中文名称 |
| **concept** | String(100) | 概念名称 | 股票所属的概念 |
| **industry** | String(100) | 行业 | 股票所属的行业 |
| **price** | DECIMAL(10,2) | 价格 | 该概念下该股票的价格 |
| **turnover_rate** | DECIMAL(8,4) | 换手率 | 该股票的换手率 |
| **net_inflow** | DECIMAL(15,2) | 净流入 | 该股票的净流入金额 |
| **page_count** | Integer | 全部页数 | 论坛热帖页数统计 |
| **total_reads** | BigInteger | 热帖首页阅读总数 | 论坛热帖阅读量统计 |
| **import_date** | Date | 导入日期 | 数据对应的交易日期 |
| **created_at** | DateTime | 创建时间 | 记录创建时间戳 |

## 核心设计原则

### 1. 数据粒度：**股票-概念-日期** 三维组合

每一条记录代表：
- 某只**股票** (stock_code)
- 在某个**概念** (concept)
- 的某个**交易日** (import_date)
- 的完整财务数据快照

**示例数据结构：**
```
stock_code=600036, concept=金融, price=20.15, turnover_rate=3.25, 
net_inflow=1500000, import_date=2024-10-16
```

### 2. 与 stock_concepts 表的区别

**stock_concepts 表（关系表）:**
- 仅存储 stock_id 和 concept_id（外键）
- 结构简洁，用于ORM导航
- 数据量小，关系维护简单
- 无法直接进行财务聚合

**stock_concept_data 表（数据快照表）:**
- 存储完整的财务数据
- 每条记录是一个完整的数据快照
- 便于按日期、按概念进行批量查询和聚合计算
- **专为分析系统设计**

## 使用场景

### 场景1：概念内个股排名 (`_calculate_concept_rankings`)

```sql
-- DailyAnalysisService 第100-128行
SELECT 
    stock_code,
    stock_name,
    concept,
    price,
    turnover_rate,
    net_inflow,
    total_reads,
    page_count,
    industry,
    datetime('now') as created_at
FROM stock_concept_data 
WHERE import_date = :analysis_date
  AND concept IS NOT NULL 
  AND concept != ''
```

**用途：**
- 为每个概念中的股票生成排名记录
- 插入到 DailyConceptRanking 表
- 支持概念内的股票热度对比

### 场景2：概念汇总统计 (`_generate_concept_summaries`)

```sql
-- DailyAnalysisService 第181-194行
SELECT 
    concept,
    COUNT(*) as stock_count,           -- 该概念下的股票数
    SUM(net_inflow) as total_net_inflow,
    AVG(net_inflow) as avg_net_inflow,
    AVG(price) as avg_price,
    AVG(turnover_rate) as avg_turnover_rate,
    SUM(total_reads) as total_reads,   -- 总阅读数
    SUM(page_count) as total_pages     -- 总页数
FROM stock_concept_data 
WHERE import_date = :analysis_date
  AND concept IS NOT NULL 
  AND concept != ''
GROUP BY concept
```

**用途：**
- 按概念进行聚合统计
- 计算概念级别的财务指标
- 插入到 DailyConceptSummary 表

### 场景3：数据统计查询

```sql
-- 统计该日期的数据规模
SELECT COUNT(DISTINCT concept) as concept_count,
       COUNT(*) as total_records
FROM stock_concept_data 
WHERE import_date = :analysis_date
```

## 数据流转关系

```
CSV文件
  ↓
DataImportService.import_csv_data()
  ├→ 创建/更新 stocks 表（股票基础信息）
  ├→ 创建/更新 concepts 表（概念基础信息）
  ├→ 创建/更新 stock_concepts 表（关系表）
  ├→ 创建/更新 daily_stock_data 表（日线数据）
  └→ ❌ 现在缺失：创建 stock_concept_data 表（数据快照）
       ↓
DailyAnalysisService 需要这个表！
  ├→ _calculate_concept_rankings()
  │   └→ 查询 stock_concept_data 生成排名
  └→ _generate_concept_summaries()
      └→ 查询 stock_concept_data 生成汇总
```

## 为什么需要这个表？

1. **性能优化**：
   - 避免复杂的多表JOIN
   - 预先准备好分析所需的数据

2. **数据独立性**：
   - 快照数据不受后续修改影响
   - 保证报表数据的一致性

3. **灵活查询**：
   - 支持按日期、按概念、按股票的多维查询
   - 易于编写聚合统计SQL

4. **历史追踪**：
   - 每个import_date都保留完整的数据快照
   - 便于分析时间序列变化

## 与日期相关的关键字段

- **import_date (Date)**：
  - 标记数据对应的交易日期
  - 是最重要的分组维度
  - 用于分析系统按日期隔离数据

- **created_at (DateTime)**：
  - 记录数据入库的时间
  - 用于审计和日志

## 与其他表的主要差异

| 特性 | stock_concepts | stock_concept_data | stock_concept_raw_data |
|------|---------------|--------------------|----------------------|
| 粒度 | 股票-概念关系 | 股票-概念-日期数据 | CSV原始行数据 |
| 存储内容 | ID关系 | 完整财务快照 | CSV的所有字段 |
| 行数 | 少（关系表） | 多（数据表） | 最多（原始数据） |
| 用途 | ORM导航 | 分析聚合 | 数据审计追踪 |
| 导入来源 | 处理后 | 处理后 | 原始 |

## 总结

**stock_concept_data 是分析系统的核心数据表**，它：
- 提供 **股票-概念-日期** 粒度的完整财务数据
- 支持 DailyAnalysisService 的所有聚合分析
- 是生成排名、汇总、评分等分析结果的数据源
- 当前在 CSV 导入过程中缺失，导致分析功能无法工作
