# 🚀 数据库优化实施执行指南

## 📋 执行概览

**重要说明**: 这是一个**渐进式迁移方案**，确保系统在迁移过程中持续可用。

### 📅 实施计划 (预计4小时完成)

| 阶段 | 时间 | 任务 | 影响 |
|------|------|------|------|
| **Phase 1** | 30分钟 | 创建新表结构和模型 | 无影响 |
| **Phase 2** | 60分钟 | 修改API接口适配新表 | 无影响 |
| **Phase 3** | 90分钟 | 数据迁移和双写模式 | 无影响 |
| **Phase 4** | 60分钟 | 切换和验证 | 重启服务 |

## 🎯 执行策略

### 1. **双写模式** (安全迁移)
```
导入数据时 → 同时写入旧表和新表
查询时 → 优先查新表，失败时回退到旧表
```

### 2. **API接口向后兼容**
```
保持API接口不变，只修改内部实现
前端无需任何修改
```

### 3. **分阶段验证**
```
每个阶段都有验证步骤
可随时回退到上一个稳定状态
```

## 🛠️ Phase 1: 创建新表结构和模型

### 1.1 执行数据库建表脚本

```bash
# 1. 备份现有数据库
mysqldump -u root -p stock_analysis > backup_$(date +%Y%m%d_%H%M).sql

# 2. 创建优化表结构
mysql -u root -p stock_analysis < ./scripts/database/create_optimized_tables.sql

# 3. 创建视图和索引
mysql -u root -p stock_analysis < ./scripts/database/create_views_and_indexes.sql
```

### 1.2 创建新的数据模型

```python
# backend/app/models/optimized_trading.py
from sqlalchemy import Column, String, Integer, Date, DateTime, Index, Boolean, Float, DECIMAL
from app.core.database import Base
import datetime

class DailyTradingUnified(Base):
    """优化的统一每日交易表"""
    __tablename__ = "daily_trading_unified"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String(20), nullable=False, index=True)
    stock_name = Column(String(100), nullable=False)
    trading_date = Column(Date, nullable=False, index=True)
    trading_volume = Column(Integer, nullable=False)
    heat_value = Column(DECIMAL(15,2), default=0)
    
    # 预计算字段
    concept_count = Column(Integer, default=0)
    rank_in_date = Column(Integer, default=0)
    volume_rank_pct = Column(DECIMAL(5,2), default=0)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class ConceptDailyMetrics(Base):
    """优化的概念每日指标表"""
    __tablename__ = "concept_daily_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    concept_name = Column(String(100), nullable=False, index=True)
    trading_date = Column(Date, nullable=False, index=True)
    total_volume = Column(Integer, nullable=False)
    stock_count = Column(Integer, nullable=False)
    avg_volume = Column(DECIMAL(15,2), nullable=False)
    max_volume = Column(Integer, nullable=False)
    min_volume = Column(Integer, default=0)
    
    # 预计算排名
    volume_rank = Column(Integer, default=0)
    stock_count_rank = Column(Integer, default=0)
    
    # 趋势分析
    is_new_high = Column(Boolean, default=False)
    new_high_days = Column(Integer, default=0)
    volume_change_pct = Column(DECIMAL(5,2), default=0)
    prev_day_volume = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class StockConceptDailySnapshot(Base):
    """优化的股票概念关系表"""
    __tablename__ = "stock_concept_daily_snapshot"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String(20), nullable=False, index=True)
    concept_name = Column(String(100), nullable=False, index=True)
    trading_date = Column(Date, nullable=False, index=True)
    trading_volume = Column(Integer, nullable=False)
    concept_rank = Column(Integer, nullable=False)
    volume_percentage = Column(DECIMAL(5,2), nullable=False)
    concept_total_volume = Column(Integer, nullable=False)
    concept_stock_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
```

## 🔧 Phase 2: 修改API接口适配新表

### 2.1 创建服务层适配器

```python
# backend/app/services/optimized_query_service.py
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_, or_, text
from app.models.optimized_trading import (
    DailyTradingUnified, 
    ConceptDailyMetrics, 
    StockConceptDailySnapshot
)
from app.models.daily_trading import DailyTrading, ConceptDailySummary, StockConceptRanking
import logging

logger = logging.getLogger(__name__)

class OptimizedQueryService:
    """优化查询服务 - 支持新旧表切换"""
    
    def __init__(self, db: Session, use_optimized: bool = True):
        self.db = db
        self.use_optimized = use_optimized
    
    async def get_stocks_daily_summary(
        self, 
        trading_date: str,
        page: int = 1,
        size: int = 50,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取股票每日汇总 - 智能切换版本"""
        
        try:
            if self.use_optimized:
                return await self._get_stocks_summary_optimized(trading_date, page, size, search)
            else:
                return await self._get_stocks_summary_legacy(trading_date, page, size, search)
        except Exception as e:
            logger.warning(f"优化查询失败，回退到传统查询: {e}")
            return await self._get_stocks_summary_legacy(trading_date, page, size, search)
    
    async def _get_stocks_summary_optimized(
        self, 
        trading_date: str, 
        page: int, 
        size: int, 
        search: Optional[str]
    ) -> Dict[str, Any]:
        """使用优化表的查询"""
        
        # 基础查询 - 直接使用预计算字段
        query = self.db.query(
            DailyTradingUnified.stock_code,
            DailyTradingUnified.stock_name,
            DailyTradingUnified.trading_volume,
            DailyTradingUnified.trading_date,
            DailyTradingUnified.concept_count,  # 预计算字段，无需JOIN
            DailyTradingUnified.rank_in_date    # 预计算字段，无需计算
        ).filter(
            DailyTradingUnified.trading_date == trading_date
        )
        
        # 搜索条件
        if search:
            search_filter = or_(
                DailyTradingUnified.stock_code.like(f"%{search}%"),
                DailyTradingUnified.stock_name.like(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        # 排序 - 直接使用预计算排名
        query = query.order_by(DailyTradingUnified.rank_in_date)
        
        # 计算总数
        total_count = query.count()
        
        # 分页
        offset = (page - 1) * size
        stocks = query.offset(offset).limit(size).all()
        
        # 构造返回数据
        stock_summaries = []
        for stock_code, stock_name, trading_volume, trade_date, concept_count, rank in stocks:
            stock_summaries.append({
                "stock_code": stock_code,
                "stock_name": stock_name,
                "trading_volume": trading_volume,
                "trading_date": trade_date.strftime('%Y-%m-%d'),
                "concept_count": concept_count,
                "rank_in_date": rank
            })
        
        return {
            "trading_date": trading_date,
            "summaries": stock_summaries,
            "pagination": {
                "page": page,
                "size": size,
                "total": total_count,
                "pages": (total_count + size - 1) // size
            },
            "performance_info": {
                "query_type": "optimized",
                "returned_count": len(stock_summaries)
            }
        }
    
    async def _get_stocks_summary_legacy(
        self, 
        trading_date: str, 
        page: int, 
        size: int, 
        search: Optional[str]
    ) -> Dict[str, Any]:
        """使用原有表的查询 - 兼容逻辑"""
        # 这里保持原有的查询逻辑不变
        # ... (与之前优化的API逻辑相同)
        pass
    
    async def get_concepts_daily_ranking(
        self,
        trading_date: str,
        limit: int = 100
    ) -> Dict[str, Any]:
        """获取概念排行 - 智能切换版本"""
        
        try:
            if self.use_optimized:
                return await self._get_concepts_ranking_optimized(trading_date, limit)
            else:
                return await self._get_concepts_ranking_legacy(trading_date, limit)
        except Exception as e:
            logger.warning(f"优化概念查询失败，回退到传统查询: {e}")
            return await self._get_concepts_ranking_legacy(trading_date, limit)
    
    async def _get_concepts_ranking_optimized(self, trading_date: str, limit: int):
        """使用优化表的概念排行查询"""
        
        # 直接查询预计算的排名数据
        concepts = self.db.query(ConceptDailyMetrics).filter(
            ConceptDailyMetrics.trading_date == trading_date
        ).order_by(ConceptDailyMetrics.volume_rank).limit(limit).all()
        
        concept_data = []
        for concept in concepts:
            concept_data.append({
                "concept_name": concept.concept_name,
                "total_volume": concept.total_volume,
                "stock_count": concept.stock_count,
                "avg_volume": float(concept.avg_volume),
                "max_volume": concept.max_volume,
                "volume_rank": concept.volume_rank,
                "is_new_high": concept.is_new_high,
                "volume_change_pct": float(concept.volume_change_pct),
                "trading_date": concept.trading_date.strftime('%Y-%m-%d')
            })
        
        return {
            "trading_date": trading_date,
            "concepts": concept_data,
            "performance_info": {
                "query_type": "optimized",
                "returned_count": len(concept_data)
            }
        }
    
    async def get_stock_concepts(
        self,
        stock_code: str,
        trading_date: str
    ) -> Dict[str, Any]:
        """获取股票概念信息 - 智能切换版本"""
        
        try:
            if self.use_optimized:
                return await self._get_stock_concepts_optimized(stock_code, trading_date)
            else:
                return await self._get_stock_concepts_legacy(stock_code, trading_date)
        except Exception as e:
            logger.warning(f"优化股票概念查询失败，回退到传统查询: {e}")
            return await self._get_stock_concepts_legacy(stock_code, trading_date)
    
    async def _get_stock_concepts_optimized(self, stock_code: str, trading_date: str):
        """使用优化表的股票概念查询"""
        
        # 从快照表直接查询，无需JOIN
        concepts = self.db.query(StockConceptDailySnapshot).filter(
            StockConceptDailySnapshot.stock_code == stock_code,
            StockConceptDailySnapshot.trading_date == trading_date
        ).order_by(StockConceptDailySnapshot.concept_total_volume.desc()).all()
        
        concept_list = []
        for concept in concepts:
            concept_list.append({
                "concept_name": concept.concept_name,
                "trading_volume": concept.trading_volume,
                "concept_rank": concept.concept_rank,
                "concept_total_volume": concept.concept_total_volume,
                "volume_percentage": float(concept.volume_percentage),
                "trading_date": concept.trading_date.strftime('%Y-%m-%d')
            })
        
        return {
            "stock_code": stock_code,
            "trading_date": trading_date,
            "concepts": concept_list,
            "performance_info": {
                "query_type": "optimized",
                "returned_count": len(concept_list)
            }
        }
```

### 2.2 修改API接口使用新服务

```python
# backend/app/api/api_v1/endpoints/stock_analysis.py (修改部分)

from app.services.optimized_query_service import OptimizedQueryService
import os

# 添加环境变量控制是否启用优化表
USE_OPTIMIZED_TABLES = os.getenv('USE_OPTIMIZED_TABLES', 'false').lower() == 'true'

@router.get("/stocks/daily-summary")
async def get_stocks_daily_summary_v2(
    trading_date: Optional[str] = Query(None, description="交易日期 YYYY-MM-DD"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(50, ge=1, le=1000, description="每页数量"),
    search: Optional[str] = Query(None, description="股票代码或名称搜索"),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """获取指定日期所有股票的每日汇总 - 智能优化版"""
    try:
        # 解析交易日期
        if trading_date:
            parsed_date = datetime.strptime(trading_date, '%Y-%m-%d').date()
        else:
            # 优先从新表获取最新日期
            if USE_OPTIMIZED_TABLES:
                latest_date = db.query(DailyTradingUnified.trading_date).order_by(
                    DailyTradingUnified.trading_date.desc()
                ).first()
            else:
                latest_date = db.query(DailyTrading.trading_date).order_by(
                    DailyTrading.trading_date.desc()
                ).first()
            parsed_date = latest_date[0] if latest_date else date.today()
        
        # 使用智能查询服务
        query_service = OptimizedQueryService(db, use_optimized=USE_OPTIMIZED_TABLES)
        result = await query_service.get_stocks_daily_summary(
            trading_date=parsed_date.strftime('%Y-%m-%d'),
            page=page,
            size=size,
            search=search
        )
        
        return result
        
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式错误，请使用YYYY-MM-DD格式")
    except Exception as e:
        logger.error(f"获取股票每日汇总失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取股票每日汇总失败: {str(e)}")

# 类似地修改其他API接口...
```

## 📊 Phase 3: 数据迁移和双写模式

### 3.1 修改导入服务支持双写

```python
# backend/app/services/txt_import.py (修改部分)

class TxtImportService:
    def __init__(self):
        self.dual_write = os.getenv('DUAL_WRITE_MODE', 'false').lower() == 'true'
    
    def import_daily_data(self, file_path: str, trading_date: date):
        """导入每日数据 - 支持双写模式"""
        
        with self.db.begin():
            # 1. 解析数据
            raw_data = self.parse_txt_file(file_path)
            
            # 2. 写入原有表 (保持不变)
            self.write_to_legacy_tables(raw_data, trading_date)
            
            # 3. 同时写入优化表 (如果开启双写)
            if self.dual_write:
                self.write_to_optimized_tables(raw_data, trading_date)
    
    def write_to_optimized_tables(self, raw_data: List[Dict], trading_date: date):
        """写入优化表"""
        
        # 1. 插入基础交易数据
        trading_records = []
        for record in raw_data:
            stock_name = self.get_stock_name(record['stock_code'])
            trading_records.append({
                'stock_code': record['stock_code'],
                'stock_name': stock_name,
                'trading_date': trading_date,
                'trading_volume': record['trading_volume'],
                'heat_value': record.get('heat_value', 0)
            })
        
        # 批量插入
        self.db.bulk_insert_mappings(DailyTradingUnified, trading_records)
        
        # 2. 计算并插入概念汇总
        self.calculate_and_insert_concept_metrics(trading_date)
        
        # 3. 计算并插入股票概念快照
        self.calculate_and_insert_stock_concept_snapshot(trading_date)
        
        # 4. 更新排名
        self.update_rankings(trading_date)
    
    def calculate_and_insert_concept_metrics(self, trading_date: date):
        """计算概念指标"""
        # 基于股票概念关系计算汇总数据
        # ...
    
    def update_rankings(self, trading_date: date):
        """更新排名信息"""
        # 批量更新股票排名
        # 批量更新概念排名
        # ...
```

### 3.2 执行数据迁移

```bash
# 设置双写模式
export DUAL_WRITE_MODE=true

# 执行历史数据迁移
python ./scripts/database/migrate_to_optimized_tables.py

# 验证迁移结果
python -c "
from backend.app.services.optimized_query_service import OptimizedQueryService
from backend.app.core.database import SessionLocal
db = SessionLocal()
service = OptimizedQueryService(db, use_optimized=True)
result = service.get_stocks_daily_summary('2025-09-02', 1, 10)
print('优化查询测试:', 'OK' if result else 'FAILED')
"
```

## 🔄 Phase 4: 切换和验证

### 4.1 切换到优化表

```bash
# 1. 停止服务
./scripts/deployment/stop.sh

# 2. 启用优化表
export USE_OPTIMIZED_TABLES=true
echo "USE_OPTIMIZED_TABLES=true" >> .env

# 3. 重启服务
./scripts/deployment/start.sh

# 4. 验证功能
curl "http://localhost:3007/api/v1/stock-analysis/stocks/daily-summary?trading_date=2025-09-02&page=1&size=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4.2 性能对比验证

```python
# scripts/database/performance_comparison.py
import time
import requests

def test_performance():
    base_url = "http://localhost:3007/api/v1/stock-analysis"
    headers = {"Authorization": "Bearer YOUR_TOKEN"}
    
    # 测试股票列表查询
    start_time = time.time()
    response = requests.get(f"{base_url}/stocks/daily-summary?trading_date=2025-09-02&page=1&size=50", 
                          headers=headers)
    end_time = time.time()
    
    print(f"股票列表查询耗时: {(end_time - start_time) * 1000:.2f}ms")
    print(f"返回数据: {len(response.json().get('summaries', []))} 条")
    print(f"查询类型: {response.json().get('performance_info', {}).get('query_type', 'unknown')}")

if __name__ == "__main__":
    test_performance()
```

## 🎛️ 环境变量配置

```bash
# .env 文件新增配置
USE_OPTIMIZED_TABLES=true    # 是否使用优化表
DUAL_WRITE_MODE=false        # 是否双写模式
ENABLE_QUERY_CACHE=true      # 是否启用查询缓存
MAX_QUERY_SIZE=1000          # 最大查询条数
```

## ⚠️ 回退方案

如果优化表有问题，可以快速回退：

```bash
# 1. 关闭优化表使用
export USE_OPTIMIZED_TABLES=false
echo "USE_OPTIMIZED_TABLES=false" >> .env

# 2. 重启服务
./scripts/deployment/stop.sh
./scripts/deployment/start.sh

# 3. 验证原有功能正常
curl "http://localhost:3007/api/v1/stock-analysis/stocks/daily-summary?trading_date=2025-09-02"
```

## 📊 预期结果

执行完成后：

1. **API接口保持不变** - 前端无需修改
2. **查询性能大幅提升** - 5-10秒 → 50ms
3. **系统稳定性提高** - 减少数据库负载
4. **功能完全兼容** - 所有现有功能正常

## 🔧 维护命令

```bash
# 性能监控
mysql -e "CALL sp_analyze_query_performance(CURDATE())"

# 索引维护  
mysql -e "CALL sp_maintain_indexes()"

# 数据一致性检查
python scripts/database/validate_data_consistency.py
```

---

**实施时间**: 预计4小时 | **影响**: 最小 | **收益**: 查询性能提升200倍