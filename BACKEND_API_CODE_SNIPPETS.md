# 关键代码实现摘要

## 文件位置映射

```
后端项目根目录: /Users/peakom/work/stock-analysis-system/backend

关键文件:
├── app/
│   ├── main.py                                    # FastAPI主应用
│   ├── api/
│   │   └── api_v1/
│   │       ├── api.py                           # 路由汇总配置
│   │       └── endpoints/
│   │           ├── chart_data.py                # [API1] 图表数据端点
│   │           └── concept_analysis.py          # [API2] 概念分析端点
│   ├── services/
│   │   ├── chart_data.py                        # ChartDataService
│   │   └── concept_analysis.py                  # ConceptAnalysisService
│   ├── models/
│   │   ├── stock.py                             # Stock, DailyStockData模型
│   │   ├── concept.py                           # Concept模型
│   │   └── concept_analysis.py                  # DailyConceptSummary, DailyConceptRanking模型
│   └── core/
│       ├── database.py                          # 数据库连接配置
│       └── config.py                            # 应用配置
├── .env                                          # 数据库连接字符串
└── requirements.txt                              # Python依赖
```

---

## API1：Market Overview (市场总览)

### 文件：chart_data.py (第220-322行)

#### 路由定义
```python
@router.get("/market-overview")
async def get_market_overview_chart(
    trade_date: Optional[date] = Query(None, description="交易日期，默认为最新日期"),
    db: Session = Depends(get_db)
):
    """获取市场概览图表数据"""
    
    try:
        from app.models import DailyStockData, DailyConceptSummary
        from sqlalchemy import func
        
        # 获取最新的交易日期
        if not trade_date:
            latest_data = db.query(DailyStockData.trade_date).order_by(
                db.query(DailyStockData.trade_date).desc()
            ).first()
            if not latest_data:
                raise HTTPException(status_code=404, detail="没有股票数据")
            trade_date = latest_data.trade_date
        
        # 获取市场统计数据 [SQL 1]
        stock_stats = db.query(
            func.count(DailyStockData.id).label('total_stocks'),
            func.avg(DailyStockData.heat_value).label('avg_heat'),
            func.sum(DailyStockData.heat_value).label('total_heat'),
            func.max(DailyStockData.heat_value).label('max_heat')
        ).filter(
            DailyStockData.trade_date == trade_date,
            DailyStockData.heat_value > 0
        ).first()
        
        # 获取概念统计数据 [SQL 2]
        concept_stats = db.query(
            func.count(DailyConceptSummary.id).label('total_concepts'),
            func.sum(case(
                (DailyConceptSummary.is_new_high == True, 1),
                else_=0
            )).label('innovation_concepts'),
            func.avg(DailyConceptSummary.total_heat_value).label('avg_concept_heat')
        ).filter(
            DailyConceptSummary.trade_date == trade_date
        ).first()

        # 热度分布统计 [SQL 3]
        heat_distribution = db.query(
            func.sum(case(
                (DailyStockData.heat_value.between(0, 9.99), 1),
                else_=0
            )).label('range_0_10'),
            func.sum(case(
                (DailyStockData.heat_value.between(10, 19.99), 1),
                else_=0
            )).label('range_10_20'),
            func.sum(case(
                (DailyStockData.heat_value.between(20, 49.99), 1),
                else_=0
            )).label('range_20_50'),
            func.sum(case(
                (DailyStockData.heat_value.between(50, 99.99), 1),
                else_=0
            )).label('range_50_100'),
            func.sum(case(
                (DailyStockData.heat_value >= 100, 1),
                else_=0
            )).label('range_100_plus')
        ).filter(
            DailyStockData.trade_date == trade_date
        ).first()

        distribution_data = {
            "0-10": heat_distribution.range_0_10 or 0,
            "10-20": heat_distribution.range_10_20 or 0,
            "20-50": heat_distribution.range_20_50 or 0,
            "50-100": heat_distribution.range_50_100 or 0,
            "100+": heat_distribution.range_100_plus or 0
        }
        
        # 返回结果
        return {
            "trade_date": trade_date.isoformat(),
            "market_stats": {
                "total_stocks": stock_stats.total_stocks if stock_stats else 0,
                "avg_heat_value": round(float(stock_stats.avg_heat), 2) if stock_stats and stock_stats.avg_heat else 0,
                "total_heat_value": round(float(stock_stats.total_heat), 2) if stock_stats and stock_stats.total_heat else 0,
                "max_heat_value": float(stock_stats.max_heat) if stock_stats and stock_stats.max_heat else 0,
                "total_concepts": concept_stats.total_concepts if concept_stats else 0,
                "innovation_concepts": concept_stats.innovation_concepts if concept_stats else 0,
                "avg_concept_heat": round(float(concept_stats.avg_concept_heat), 2) if concept_stats and concept_stats.avg_concept_heat else 0
            },
            "heat_distribution_chart": {
                "categories": ["0-10", "10-20", "20-50", "50-100", "100+"],
                "data": [
                    distribution_data.get("0-10", 0),
                    distribution_data.get("10-20", 0),
                    distribution_data.get("20-50", 0),
                    distribution_data.get("50-100", 0),
                    distribution_data.get("100+", 0)
                ]
            }
        }
```

#### 依赖关系
- 数据库表：`daily_stock_data`, `daily_concept_summaries`
- 服务类：无（直接查询）
- 模型：`DailyStockData`, `DailyConceptSummary`

---

## API2：Innovation Concepts (创新高概念)

### 文件：concept_analysis.py (第175-319行)

#### 路由定义
```python
@router.get("/concepts/innovation")
async def get_innovation_concepts(
    trade_date: Optional[date] = Query(None, description="交易日期，默认为最新日期"),
    days_back: int = Query(10, ge=1, le=30, description="创新高检查天数"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """获取创新高概念列表"""
    
    # 日期处理
    if not trade_date:
        from datetime import date
        trade_date = date.today()
        
        try:
            latest_data = db.query(DailyConceptSummary.trade_date).order_by(
                desc(DailyConceptSummary.trade_date)
            ).first()
            
            if latest_data:
                trade_date = latest_data.trade_date
        except Exception as e:
            print(f"Database error when fetching latest date: {e}")
    
    # 尝试查询创新高概念，如果失败返回模拟数据
    try:
        offset = (page - 1) * page_size
        innovation_query = db.query(
            DailyConceptSummary,
            Concept.concept_name
        ).join(
            Concept, DailyConceptSummary.concept_id == Concept.id
        ).filter(
            DailyConceptSummary.trade_date == trade_date,
            DailyConceptSummary.is_new_high == True      # 【关键条件】
        ).order_by(desc(DailyConceptSummary.total_heat_value))
        
        total_count = innovation_query.count()
        innovations = innovation_query.offset(offset).limit(page_size).all()
    except Exception as e:
        print(f"Database error in innovation concepts query: {e}")
        innovations = []
        total_count = 0
    
    innovation_concepts = []
    
    # 【关键特性】：无数据时返回Mock数据
    if not innovations:
        mock_concepts = [
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
            },
            {
                "concept_id": 2,
                "concept_name": "新能源汽车",
                "total_heat_value": 76400.20,
                "stock_count": 28,
                "avg_heat_value": 2728.58,
                "new_high_days": 12,
                "top_stocks": [
                    {"stock_code": "002594", "stock_name": "比亚迪", "heat_value": 9200.10},
                    {"stock_code": "300750", "stock_name": "宁德时代", "heat_value": 8850.90},
                    {"stock_code": "002129", "stock_name": "中环股份", "heat_value": 7100.50}
                ]
            },
            {
                "concept_id": 3,
                "concept_name": "芯片概念",
                "total_heat_value": 65300.80,
                "stock_count": 42,
                "avg_heat_value": 1554.78,
                "new_high_days": 8,
                "top_stocks": [
                    {"stock_code": "000858", "stock_name": "五粮液", "heat_value": 5200.30},
                    {"stock_code": "002415", "stock_name": "海康威视", "heat_value": 4950.20},
                    {"stock_code": "300059", "stock_name": "东方财富", "heat_value": 4650.70}
                ]
            }
        ]
        return {
            "trade_date": trade_date.isoformat(),
            "days_back": days_back,
            "innovation_concepts": mock_concepts,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": len(mock_concepts),
                "total_pages": 1
            }
        }
    
    # 实际数据处理
    for summary, concept_name in innovations:
        # 为每个概念获取前3只热度股票
        top_stocks = db.query(
            Stock.stock_code,
            Stock.stock_name,
            DailyConceptRanking.heat_value
        ).join(
            DailyConceptRanking, Stock.id == DailyConceptRanking.stock_id
        ).filter(
            DailyConceptRanking.concept_id == summary.concept_id,
            DailyConceptRanking.trade_date == trade_date
        ).order_by(desc(DailyConceptRanking.heat_value)).limit(3).all()
        
        innovation_concepts.append({
            "concept_id": summary.concept_id,
            "concept_name": concept_name,
            "total_heat_value": float(summary.total_heat_value),
            "stock_count": summary.stock_count,
            "avg_heat_value": float(summary.avg_heat_value),
            "new_high_days": summary.new_high_days,
            "top_stocks": [
                {
                    "stock_code": code,
                    "stock_name": name,
                    "heat_value": float(heat)
                } for code, name, heat in top_stocks
            ]
        })
    
    return {
        "trade_date": trade_date.isoformat(),
        "days_back": days_back,
        "innovation_concepts": innovation_concepts,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total_count,
            "total_pages": (total_count + page_size - 1) // page_size
        }
    }
```

#### 依赖关系
- 数据库表：`daily_concept_summaries`, `concepts`, `daily_concept_rankings`, `stocks`
- 服务类：无（直接查询）
- 模型：`DailyConceptSummary`, `Concept`, `DailyConceptRanking`, `Stock`

---

## 数据库模型定义

### 文件：models/concept_analysis.py

```python
class DailyConceptSummary(Base):
    """每日概念汇总表 - 记录每个概念的每日汇总统计数据"""
    __tablename__ = "daily_concept_summaries"

    id = Column(Integer, primary_key=True, index=True)
    concept_id = Column(Integer, ForeignKey("concepts.id"), nullable=False)
    trade_date = Column(Date, nullable=False)
    total_heat_value = Column(DECIMAL(15, 2), nullable=False, comment="概念总热度值")
    stock_count = Column(Integer, nullable=False, comment="概念内股票数量")
    avg_heat_value = Column(DECIMAL(15, 2), nullable=False, comment="平均热度值")
    max_heat_value = Column(DECIMAL(15, 2), nullable=False, comment="最高热度值")
    min_heat_value = Column(DECIMAL(15, 2), nullable=False, comment="最低热度值")
    is_new_high = Column(Boolean, default=False, comment="是否创新高")
    new_high_days = Column(Integer, default=0, comment="创多少天新高")
    created_at = Column(Date, default=datetime.now)

    # 索引
    __table_args__ = (
        Index('idx_dcs_unique_concept_date', 'concept_id', 'trade_date', unique=True),
        Index('idx_dcs_concept_id', 'concept_id'),
        Index('idx_dcs_trade_date', 'trade_date'),
        Index('idx_dcs_total_heat_desc', 'total_heat_value', postgresql_using='btree'),
        Index('idx_dcs_new_high', 'is_new_high', 'trade_date'),
        Index('idx_dcs_new_high_days', 'new_high_days'),
    )


class DailyConceptRanking(Base):
    """每日概念排名表 - 记录每个股票在其所属概念内的排名"""
    __tablename__ = "daily_concept_rankings"

    id = Column(Integer, primary_key=True, index=True)
    concept_id = Column(Integer, ForeignKey("concepts.id"), nullable=False)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    trade_date = Column(Date, nullable=False)
    rank_in_concept = Column(Integer, nullable=False, comment="股票在概念内的排名")
    heat_value = Column(DECIMAL(15, 2), nullable=False, comment="热度值")
    created_at = Column(Date, default=datetime.now)

    # 索引
    __table_args__ = (
        Index('idx_dcr_unique_concept_stock_date', 'concept_id', 'stock_id', 'trade_date', unique=True),
        Index('idx_dcr_concept_date', 'concept_id', 'trade_date'),
        Index('idx_dcr_stock_date', 'stock_id', 'trade_date'),
        Index('idx_dcr_trade_date', 'trade_date'),
        Index('idx_dcr_rank', 'rank_in_concept'),
    )
```

### 文件：models/stock.py

```python
class DailyStockData(Base):
    """每日股票数据表"""
    __tablename__ = "daily_stock_data"
    
    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False, index=True, comment="股票ID")
    trade_date = Column(Date, nullable=False, index=True, comment="交易日期")
    pages_count = Column(Integer, default=0, comment="页数")
    total_reads = Column(Integer, default=0, comment="总阅读数")
    price = Column(DECIMAL(10, 2), default=0, comment="价格")
    turnover_rate = Column(DECIMAL(5, 2), default=0, comment="换手率")
    net_inflow = Column(DECIMAL(15, 2), default=0, comment="净流入")
    heat_value = Column(DECIMAL(15, 2), default=0, index=True, comment="热度值(来自TXT文件)")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")

    # 关联关系
    stock = relationship("Stock", back_populates="daily_data")
```

---

## 数据库连接配置

### 文件：core/database.py

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from app.core.config import settings, get_database_url

# 创建数据库引擎
engine = create_engine(
    get_database_url(),
    pool_pre_ping=True,                          # 连接前检查
    pool_size=settings.DATABASE_POOL_SIZE,       # 连接池大小
    max_overflow=settings.DATABASE_MAX_OVERFLOW, # 最大溢出连接数
    pool_timeout=settings.DATABASE_POOL_TIMEOUT, # 连接超时时间
    pool_recycle=settings.DATABASE_POOL_RECYCLE, # 连接回收时间（秒）
    echo=settings.DEBUG                          # 调试模式下打印SQL
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """获取数据库会话 - 用作FastAPI的依赖注入"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 文件：.env

```
DATABASE_URL=postgresql+psycopg2://postgres:Pp123456@localhost/stockdb
```

---

## 路由注册

### 文件：api/api_v1/api.py

```python
from fastapi import APIRouter
from app.api.api_v1.endpoints import (
    chart_data, 
    concept_analysis
)

api_router = APIRouter()

# 新增概念分析接口 (第31行)
api_router.include_router(
    concept_analysis.router, 
    prefix="/concept-analysis", 
    tags=["concept-analysis"]
)

# 新增图表数据接口 (第33行)
api_router.include_router(
    chart_data.router, 
    prefix="/chart-data", 
    tags=["chart-data"]
)
```

### 文件：main.py

```python
# 在FastAPI应用中添加API路由
app.include_router(api_router, prefix="/api/v1")

# 最终的完整API路径：
# GET /api/v1/chart-data/market-overview
# GET /api/v1/concept-analysis/concepts/innovation
```

---

## SQL查询分析

### API1 - Market Overview 执行的SQL

```sql
-- SQL 1: 股票统计
SELECT COUNT(id), AVG(heat_value), SUM(heat_value), MAX(heat_value)
FROM daily_stock_data
WHERE trade_date = '2024-11-14' AND heat_value > 0;

-- SQL 2: 概念统计
SELECT COUNT(id), SUM(CASE WHEN is_new_high = true THEN 1 ELSE 0 END), AVG(total_heat_value)
FROM daily_concept_summaries
WHERE trade_date = '2024-11-14';

-- SQL 3: 热度分布
SELECT 
  SUM(CASE WHEN heat_value BETWEEN 0 AND 9.99 THEN 1 ELSE 0 END) as range_0_10,
  SUM(CASE WHEN heat_value BETWEEN 10 AND 19.99 THEN 1 ELSE 0 END) as range_10_20,
  SUM(CASE WHEN heat_value BETWEEN 20 AND 49.99 THEN 1 ELSE 0 END) as range_20_50,
  SUM(CASE WHEN heat_value BETWEEN 50 AND 99.99 THEN 1 ELSE 0 END) as range_50_100,
  SUM(CASE WHEN heat_value >= 100 THEN 1 ELSE 0 END) as range_100_plus
FROM daily_stock_data
WHERE trade_date = '2024-11-14';
```

### API2 - Innovation Concepts 执行的SQL

```sql
-- SQL 1: 获取创新高概念列表
SELECT dcs.*, c.concept_name
FROM daily_concept_summaries dcs
JOIN concepts c ON dcs.concept_id = c.id
WHERE dcs.trade_date = '2024-11-14' AND dcs.is_new_high = true
ORDER BY dcs.total_heat_value DESC
LIMIT 20 OFFSET 0;

-- SQL 2: 对每个概念，获取前3只热度股票（为每个概念执行一次）
SELECT s.stock_code, s.stock_name, dcr.heat_value
FROM stocks s
JOIN daily_concept_rankings dcr ON s.id = dcr.stock_id
WHERE dcr.concept_id = 1 AND dcr.trade_date = '2024-11-14'
ORDER BY dcr.heat_value DESC
LIMIT 3;
```

---

## 总结

### 代码行数统计

| 组件 | 文件 | 行数 | 说明 |
|------|------|------|------|
| API1路由 | chart_data.py | 220-322 | 103行 |
| API2路由 | concept_analysis.py | 175-319 | 145行 |
| 数据库连接 | database.py | 13-39 | 27行 |
| 数据库模型 | stock.py + concept_analysis.py | 50+ | 50+ |
| 路由注册 | api.py | 31,33 | 2行 |
| 总计 | - | - | ~350行核心代码 |

### 关键发现

1. ✓ API1 (Market Overview) - 完全正常，返回真实数据
2. ⚠️ API2 (Innovation Concepts) - 有Mock数据回退机制，可能掩盖数据库错误
3. ✓ 数据库连接配置完整
4. ✓ 数据模型完整，所有必需字段都已定义
5. ✓ 索引优化良好，查询性能应该不错
