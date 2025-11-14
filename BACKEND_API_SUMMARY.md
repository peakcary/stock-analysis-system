# 后端API端点总结 - 快速参考

## 概览

本文档总结了两个关键API端点的实现情况和验证结果。

## API端点列表

### 1. 市场总览API
**路径**: `GET /api/v1/chart-data/market-overview`
**实现文件**: `/backend/app/api/api_v1/endpoints/chart_data.py` (第220-322行)
**状态**: ✓ 已实现，可正常返回真实数据

**功能**:
- 获取特定日期（或最新日期）的市场统计数据
- 包含股票总数、热度统计、概念统计、热度分布
- 共执行3条SQL查询

**返回示例**:
```json
{
  "trade_date": "2024-11-14",
  "market_stats": {
    "total_stocks": 50,
    "avg_heat_value": 25.5,
    "total_heat_value": 1275.0,
    "max_heat_value": 85.5,
    "total_concepts": 10,
    "innovation_concepts": 3,
    "avg_concept_heat": 1234.56
  },
  "heat_distribution_chart": {
    "categories": ["0-10", "10-20", "20-50", "50-100", "100+"],
    "data": [15, 20, 10, 4, 1]
  }
}
```

**数据库表**: `daily_stock_data`, `daily_concept_summaries`

---

### 2. 创新高概念API
**路径**: `GET /api/v1/concept-analysis/concepts/innovation`
**实现文件**: `/backend/app/api/api_v1/endpoints/concept_analysis.py` (第175-319行)
**状态**: ⚠️ 已实现，有Mock数据回退机制

**功能**:
- 获取特定日期的创新高概念列表
- 为每个概念返回前3只热度最高的股票
- 支持分页查询

**参数**:
- `trade_date` (可选): 交易日期，默认使用最新日期
- `days_back` (可选): 创新高检查天数，默认10天，范围1-30
- `page` (可选): 页码，默认1
- `page_size` (可选): 每页数量，默认20，范围1-100

**返回示例**:
```json
{
  "trade_date": "2024-11-14",
  "days_back": 10,
  "innovation_concepts": [
    {
      "concept_id": 1,
      "concept_name": "人工智能",
      "total_heat_value": 89500.50,
      "stock_count": 35,
      "avg_heat_value": 2557.16,
      "new_high_days": 15,
      "top_stocks": [
        {"stock_code": "000001", "stock_name": "平安银行", "heat_value": 8950.50},
        {"stock_code": "600036", "stock_name": "招商银行", "heat_value": 7823.40},
        {"stock_code": "000002", "stock_name": "万科A", "heat_value": 6545.30}
      ]
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 15,
    "total_pages": 1
  }
}
```

**数据库表**: `daily_concept_summaries`, `concepts`, `daily_concept_rankings`, `stocks`

**特殊处理**: 当数据库中无创新高概念数据时，返回3条预设的Mock概念数据（人工智能、新能源汽车、芯片概念）

---

## 数据库连接配置

**配置文件**: `/backend/.env`
```
DATABASE_URL=postgresql+psycopg2://postgres:Pp123456@localhost/stockdb
```

**驱动**: PostgreSQL + psycopg2
**主机**: localhost:5432
**数据库**: stockdb
**用户**: postgres

**连接池配置** (`core/database.py`):
- `pool_size`: 连接池大小
- `max_overflow`: 最大溢出连接
- `pool_timeout`: 连接超时时间
- `pool_recycle`: 连接回收时间
- `pool_pre_ping`: 连接前检查（已启用）

---

## 关键数据库表

### daily_stock_data (每日股票数据)
```
id (PK)
stock_id (FK) - 指向stocks表
trade_date - 交易日期
heat_value - 热度值 [DECIMAL(15,2)]
pages_count - 页数
total_reads - 阅读数
price - 价格
turnover_rate - 换手率
net_inflow - 净流入
created_at - 创建时间

索引: trade_date, heat_value
```

### daily_concept_summaries (每日概念汇总)
```
id (PK)
concept_id (FK) - 指向concepts表
trade_date - 交易日期
total_heat_value - 总热度值 [DECIMAL(15,2)]
stock_count - 股票数量
avg_heat_value - 平均热度值
max_heat_value - 最大热度值
min_heat_value - 最小热度值
is_new_high - 是否创新高 [Boolean]
new_high_days - 创新高天数
created_at - 创建时间

索引: concept_id, trade_date, is_new_high, total_heat_value
```

### daily_concept_rankings (每日概念排名)
```
id (PK)
concept_id (FK) - 指向concepts表
stock_id (FK) - 指向stocks表
trade_date - 交易日期
rank_in_concept - 在概念内的排名
heat_value - 热度值 [DECIMAL(15,2)]
created_at - 创建时间

索引: concept_id, stock_id, trade_date, rank_in_concept
```

---

## 路由注册方式

```python
# 在 api/api_v1/api.py 中
api_router.include_router(chart_data.router, prefix="/chart-data", tags=["chart-data"])
api_router.include_router(concept_analysis.router, prefix="/concept-analysis", tags=["concept-analysis"])

# 在 main.py 中
app.include_router(api_router, prefix="/api/v1")
```

最终的完整路径：
- `/api/v1/chart-data/market-overview`
- `/api/v1/concept-analysis/concepts/innovation`

---

## 数据流向

### API1 (市场总览) 的数据流
```
HTTP GET /api/v1/chart-data/market-overview
    ↓
fastapi路由处理
    ↓
chart_data.py::get_market_overview_chart()
    ↓
数据库查询:
  1. 获取最新trade_date (from daily_stock_data)
  2. 股票统计 (count, avg, sum, max from daily_stock_data)
  3. 概念统计 (count, sum(new_high), avg from daily_concept_summaries)
  4. 热度分布 (5个CASE统计 from daily_stock_data)
    ↓
返回JSON响应
```

### API2 (创新高概念) 的数据流
```
HTTP GET /api/v1/concept-analysis/concepts/innovation
    ↓
fastapi路由处理
    ↓
concept_analysis.py::get_innovation_concepts()
    ↓
Try数据库查询:
  1. 获取创新高概念列表 (from daily_concept_summaries + concepts)
  2. 对每个概念，获取前3只热度股票 (from daily_concept_rankings + stocks)
    ↓
Catch异常:
  如果查询失败或无数据
    ↓
  返回3条Mock数据
    ↓
返回JSON响应
```

---

## 关键代码片段

### API1 - 市场总览
```python
@router.get("/market-overview")
async def get_market_overview_chart(
    trade_date: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    # 获取最新日期
    # 执行股票统计、概念统计、热度分布查询
    # 返回聚合结果
```

### API2 - 创新高概念
```python
@router.get("/concepts/innovation")
async def get_innovation_concepts(
    trade_date: Optional[date] = Query(None),
    days_back: int = Query(10),
    page: int = Query(1),
    page_size: int = Query(20),
    db: Session = Depends(get_db)
):
    # Try: 查询真实数据
    # Catch: 返回Mock数据
    # 为每个概念获取前3只股票
    # 返回分页结果
```

---

## 验证清单

### 实现完整性
- [x] API端点已定义和注册
- [x] 数据库连接已配置
- [x] 数据库模型已定义
- [x] SQL查询逻辑已实现
- [x] 响应数据结构已定义

### 功能完整性
- [x] API1: 市场统计数据完整
- [x] API1: 热度分布统计完整
- [x] API2: 创新高概念列表完整
- [x] API2: 股票排名信息完整
- [x] API2: 分页机制完整

### 数据库支持
- [x] 表结构完整（daily_stock_data, daily_concept_summaries, daily_concept_rankings等）
- [x] 字段类型正确（DECIMAL(15,2)用于热度值）
- [x] 索引优化完整（trade_date, concept_id, is_new_high等）
- [x] 外键关系完整（concept_id -> concepts, stock_id -> stocks）

---

## 常见问题排查

### 问题1: API返回404或无数据
**原因**: 数据库中没有该日期的数据
**解决**: 
1. 检查daily_stock_data表中是否有数据
2. 确保数据的trade_date与查询日期匹配
3. 运行数据导入/分析任务

### 问题2: 创新高概念API返回Mock数据
**原因**: 数据库中无创新高概念或查询失败
**解决**:
1. 检查daily_concept_summaries表中is_new_high=true的记录数
2. 运行概念分析任务: POST /api/v1/concept-analysis/analysis/trigger
3. 检查后端日志是否有错误信息

### 问题3: 热度值为0或不正确
**原因**: 数据导入未完成或热度值未计算
**解决**:
1. 检查TXT文件导入是否完成
2. 检查heat_value字段是否有值
3. 运行数据验证任务

---

## 测试方法

### 使用提供的测试脚本
```bash
cd /Users/peakom/work/stock-analysis-system/backend
python test_api_endpoints.py
```

### 使用curl命令
```bash
# 测试市场总览
curl "http://localhost:8000/api/v1/chart-data/market-overview"

# 测试创新高概念
curl "http://localhost:8000/api/v1/concept-analysis/concepts/innovation?page=1&page_size=10"
```

### 使用Postman
1. 导入API文档 (可从 /docs 获取)
2. 配置认证（如需要）
3. 发送请求并查看响应

---

## 性能考虑

### API1 (市场总览)
- 执行3条SQL查询
- 大部分操作为聚合函数（COUNT, AVG, SUM, MAX）
- 性能预期: < 100ms (假设表有适当索引)

### API2 (创新高概念)
- 执行1条主查询 + N条子查询（N = 概念数量）
- 可能的N+1问题：为每个概念执行一条子查询
- 性能预期: < 500ms (假设概念数量 < 20)
- 优化建议：可使用JOIN替代子查询

---

## 文档链接

| 文档 | 描述 |
|------|------|
| BACKEND_API_ANALYSIS.md | 完整的深度分析报告 |
| BACKEND_API_CODE_SNIPPETS.md | 详细的代码实现摘要 |
| test_api_endpoints.py | 自动化测试脚本 |

---

## 最后更新

**日期**: 2024-11-14
**分析范围**: 后端项目完整搜索和验证
**确认状态**: 
- ✓ API端点存在且正确注册
- ✓ 数据库配置完整
- ✓ 数据模型完整
- ⚠️ 数据库中是否有实际数据需要验证

