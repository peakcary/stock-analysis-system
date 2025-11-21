# stock_concepts vs stock_concept_data 的设计区别

## 1️⃣ stock_concepts（关系表）

### 定义
```python
class StockConcept(Base):
    __tablename__ = "stock_concepts"
    
    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"))  # 引用 stocks.id
    concept_id = Column(Integer, ForeignKey("concepts.id"))  # 引用 concepts.id
    created_at = Column(DateTime)
```

### 用途
- **纯关系表**：只存储"哪个股票属于哪个概念"的对应关系
- **无财务数据**：不存储价格、换手率、净流入等指标
- **ORM友好**：使用外键，支持对象关系映射

### 数据特征
- 记录数：1股票 × N概念 = N条记录
- 粒度：stock-concept 关联（不含日期、财务数据）
- 唯一性：同一股票同一概念只有1条记录

### 例子
```
stock_id=1, concept_id=5  (股票001属于概念"半导体")
stock_id=1, concept_id=8  (股票001属于概念"芯片")
stock_id=2, concept_id=5  (股票002属于概念"半导体")
```

### 用途场景
- 查询"这只股票属于哪些概念"
- 查询"这个概念包含哪些股票"
- 构建股票-概念导航

---

## 2️⃣ stock_concept_data（数据表）

### 定义
```python
class StockConceptData(Base):
    __tablename__ = "stock_concept_data"
    
    id = Column(Integer, primary_key=True)
    stock_code = Column(String(20))  # 字符串代码，而非ID
    stock_name = Column(String(100))
    concept = Column(String(100))  # 字符串概念名，而非ID
    
    # 财务数据字段
    price = Column(DECIMAL(10, 2))
    turnover_rate = Column(DECIMAL(8, 4))
    net_inflow = Column(DECIMAL(15, 2))
    page_count = Column(Integer)
    total_reads = Column(BigInteger)
    industry = Column(String(100))
    
    import_date = Column(Date)  # 导入日期
    created_at = Column(DateTime)
```

### 用途
- **数据快照表**：存储股票在每个概念中的完整财务指标
- **包含财务数据**：价格、换手率、净流入、阅读数等
- **原始数据格式**：直接存储 CSV 导入的原始数据，无需关联查询

### 数据特征
- 记录数：1股票 × N概念 × M导入日期 = 记录数
- 粒度：stock-concept-import_date（含具体的财务数据）
- 一条记录 = CSV的一行数据

### 例子
```
stock_code="000001", concept="半导体", import_date="2025-04-16"
  ├─ price=15.5, turnover_rate=2.3%, net_inflow=1000.5万, page_count=100, total_reads=5000

stock_code="000001", concept="芯片", import_date="2025-04-16"
  ├─ price=15.5, turnover_rate=2.3%, net_inflow=1000.5万, page_count=100, total_reads=5000

stock_code="000002", concept="半导体", import_date="2025-04-16"
  ├─ price=20.3, turnover_rate=1.8%, net_inflow=500.2万, page_count=50, total_reads=2500
```

### 用途场景
- 分析服务汇总数据（按概念求和、平均）
- 查询"这个概念在某日期的财务数据"
- 计算概念的排名、汇总统计

---

## 关键差异对比表

| 方面 | stock_concepts | stock_concept_data |
|-----|----------------|-------------------|
| **表类型** | 关系表 | 数据表 |
| **主键字段** | stock_id, concept_id | stock_code, concept, import_date |
| **外键** | ✓ 有（stock_id, concept_id） | ✗ 无 |
| **财务数据** | ✗ 无 | ✓ 有（price, turnover, net_inflow等） |
| **日期字段** | ✗ 无 | ✓ 有（import_date） |
| **数据格式** | ID格式（引用）| 字符串格式（原始数据） |
| **粒度** | stock-concept | stock-concept-date |
| **来源** | 手动创建或导入关联 | CSV 导入时逐行创建 |
| **用于ORM** | ✓ 是 | ✗ 否 |
| **用于分析** | ✗ 否 | ✓ 是 |
| **一行代表** | "该股票属于该概念" | "该股票在该概念的完整财务数据" |

---

## 为什么需要两个表？

### stock_concepts 的用途
```python
# ORM查询：获取某股票的所有概念
stock = db.query(Stock).filter(Stock.stock_code=="000001").first()
concepts = stock.stock_concepts  # 自动加载关联的概念

# 或者反向查询：获取某概念的所有股票
concept = db.query(Concept).filter(Concept.concept_name=="半导体").first()
stocks = concept.stock_concepts  # 自动加载关联的股票
```

### stock_concept_data 的用途
```python
# SQL聚合查询：汇总某概念的财务数据
result = db.execute("""
    SELECT concept,
           COUNT(*) as stock_count,
           SUM(net_inflow) as total_net_inflow,
           AVG(price) as avg_price,
           SUM(total_reads) as total_reads
    FROM stock_concept_data
    WHERE import_date = '2025-04-16'
    GROUP BY concept
""")
```

---

## CSV 导入时的映射关系

### CSV 的一行数据
```
股票代码=000001, 股票名称=浦发银行, 概念=半导体, 价格=15.5, 换手=2.3%, 净流入=1000.5, 页数=100, 阅读=5000
```

### 导入后的表映射

```
stock_concepts:
├─ stock_id=1 (对应 Stock.stock_code=000001)
└─ concept_id=5 (对应 Concept.concept_name=半导体)
   ↓
   [建立关联关系：该股票属于该概念]

stock_concept_data:
└─ stock_code=000001, concept=半导体, price=15.5, turnover_rate=2.3, ...
   ↓
   [存储这个概念下该股票的完整财务快照]
```

---

## 设计哲学

### stock_concepts
- **范式化设计**：遵循数据库范式，无冗余
- **灵活性**：支持动态关联
- **ORM友好**：支持对象关系映射
- **小数据量**：只存储关系，记录数少

### stock_concept_data
- **反范式化设计**：冗余存储原始数据快照
- **分析优化**：为聚合查询优化，无需JOIN
- **历史追踪**：保存每个导入日期的数据快照
- **大数据量**：存储完整财务数据，记录数多

---

## 问题诊断

### 当前问题
CSV 导入时：
1. ✓ stock_concepts 被正确填充（创建了股票-概念关联）
2. ❌ stock_concept_data 没有被填充（缺失财务数据快照）

### 为什么分析服务失败？
```python
# DailyAnalysisService 的查询
SELECT concept, COUNT(*), SUM(net_inflow), AVG(price), ...
FROM stock_concept_data  # ❌ 这个表是空的！
WHERE import_date = '2025-04-16'
```

因为：
- stock_concepts 只有 ID 关联，没有财务数据
- 分析服务需要财务数据来计算汇总统计
- 所以必须有 stock_concept_data 表被填充

---

## 总结

| 需求 | 使用表 | 原因 |
|------|--------|------|
| "股票000001属于哪些概念?" | stock_concepts | 关系查询 |
| "概念'半导体'包含哪些股票?" | stock_concepts | 关系查询 |
| "2025-04-16 半导体概念的平均价格?" | stock_concept_data | 需要财务数据 |
| "2025-04-16 半导体概念的总净流入?" | stock_concept_data | 需要财务数据 |
| "显示某股票的详情和所属概念" | stock_concepts (JOIN) | ORM 导航 |

**关键认识**：
- `stock_concepts` = **关系图** (谁与谁相关)
- `stock_concept_data` = **数据快照** (完整的财务指标)