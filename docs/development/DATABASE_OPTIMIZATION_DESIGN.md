# 📊 数据库优化设计方案

## 📋 文档信息

- **优化目标**: 导入→汇总→查询工作流性能提升
- **核心原则**: 查询时数据已预计算，避免实时计算
- **设计理念**: 空间换时间，读写分离优化
- **版本**: v2.6.4-optimization
- **更新日期**: 2025-09-13

## 🔍 现有问题分析

### 1. **数据模型混乱**
```
❌ 问题：
- daily_trading vs daily_stock_data 重复
- ConceptDailySummary vs DailyConceptSum 功能重叠
- 多个表存储相同概念但字段不一致

✅ 影响：
- 数据一致性问题
- 查询时需要多表JOIN
- 存储空间浪费
```

### 2. **索引设计不优化**
```
❌ 问题：
- 缺少覆盖索引
- 联合索引顺序不当
- 分区策略缺失

✅ 影响：
- 查询扫描大量数据
- 排序操作慢
- 分页查询效率低
```

### 3. **查询路径不优化**
```
❌ 问题：
- 实时计算概念数量
- 跨表JOIN查询多
- 缺少快速查询视图

✅ 影响：
- 5000+股票查询5-10秒
- CPU使用率高
- 用户体验差
```

## 🎯 优化设计方案

### 1. **统一数据模型**

#### 📊 核心业务表设计

```sql
-- 1. 统一的每日交易表
CREATE TABLE daily_trading_unified (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    stock_code VARCHAR(20) NOT NULL COMMENT '股票代码(标准化)',
    stock_name VARCHAR(100) NOT NULL COMMENT '股票名称',
    trading_date DATE NOT NULL COMMENT '交易日期',
    trading_volume BIGINT NOT NULL COMMENT '交易量',
    heat_value DECIMAL(15,2) DEFAULT 0 COMMENT '热度值',
    concept_count SMALLINT DEFAULT 0 COMMENT '概念数量(预计算)',
    rank_in_date MEDIUMINT DEFAULT 0 COMMENT '当日排名(预计算)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 优化索引设计
    INDEX idx_date_volume (trading_date, trading_volume DESC),
    INDEX idx_stock_date (stock_code, trading_date),
    INDEX idx_date_rank (trading_date, rank_in_date),
    UNIQUE KEY uk_stock_date (stock_code, trading_date)
) ENGINE=InnoDB 
  PARTITION BY RANGE (TO_DAYS(trading_date)) (
    PARTITION p2024 VALUES LESS THAN (TO_DAYS('2025-01-01')),
    PARTITION p2025 VALUES LESS THAN (TO_DAYS('2026-01-01')),
    PARTITION p_future VALUES LESS THAN MAXVALUE
  );

-- 2. 概念每日汇总表(终极版)
CREATE TABLE concept_daily_metrics (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    concept_name VARCHAR(100) NOT NULL COMMENT '概念名称',
    trading_date DATE NOT NULL COMMENT '交易日期',
    total_volume BIGINT NOT NULL COMMENT '总交易量',
    stock_count SMALLINT NOT NULL COMMENT '股票数量',
    avg_volume DECIMAL(15,2) NOT NULL COMMENT '平均交易量',
    max_volume BIGINT NOT NULL COMMENT '最大交易量',
    volume_rank SMALLINT DEFAULT 0 COMMENT '概念排名(预计算)',
    is_new_high BOOLEAN DEFAULT FALSE COMMENT '是否创新高',
    volume_change_pct DECIMAL(5,2) DEFAULT 0 COMMENT '交易量变化百分比',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 覆盖索引优化
    INDEX idx_date_rank (trading_date, volume_rank),
    INDEX idx_date_volume (trading_date, total_volume DESC),
    INDEX idx_concept_date (concept_name, trading_date),
    UNIQUE KEY uk_concept_date (concept_name, trading_date)
) ENGINE=InnoDB
  PARTITION BY RANGE (TO_DAYS(trading_date)) (
    PARTITION p2024 VALUES LESS THAN (TO_DAYS('2025-01-01')),
    PARTITION p2025 VALUES LESS THAN (TO_DAYS('2026-01-01')),
    PARTITION p_future VALUES LESS THAN MAXVALUE
  );

-- 3. 股票概念关系快照表
CREATE TABLE stock_concept_daily_snapshot (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    stock_code VARCHAR(20) NOT NULL COMMENT '股票代码',
    concept_name VARCHAR(100) NOT NULL COMMENT '概念名称',
    trading_date DATE NOT NULL COMMENT '交易日期',
    trading_volume BIGINT NOT NULL COMMENT '股票交易量',
    concept_rank SMALLINT NOT NULL COMMENT '在概念中排名',
    concept_total_volume BIGINT NOT NULL COMMENT '概念总交易量',
    volume_percentage DECIMAL(5,2) NOT NULL COMMENT '占概念百分比',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 多维度查询优化
    INDEX idx_stock_date (stock_code, trading_date),
    INDEX idx_concept_date_rank (concept_name, trading_date, concept_rank),
    INDEX idx_date_volume (trading_date, trading_volume DESC),
    UNIQUE KEY uk_stock_concept_date (stock_code, concept_name, trading_date)
) ENGINE=InnoDB
  PARTITION BY RANGE (TO_DAYS(trading_date)) (
    PARTITION p2024 VALUES LESS THAN (TO_DAYS('2025-01-01')),
    PARTITION p2025 VALUES LESS THAN (TO_DAYS('2026-01-01')),
    PARTITION p_future VALUES LESS THAN MAXVALUE
  );
```

### 2. **快速查询视图**

```sql
-- 股票列表快速查询视图
CREATE VIEW v_stock_daily_summary AS
SELECT 
    stock_code,
    stock_name,
    trading_date,
    trading_volume,
    concept_count,
    rank_in_date,
    CASE 
        WHEN rank_in_date <= 100 THEN 'hot'
        WHEN rank_in_date <= 1000 THEN 'normal' 
        ELSE 'cold'
    END as heat_level
FROM daily_trading_unified
WHERE trading_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY);

-- 概念排行快速查询视图  
CREATE VIEW v_concept_daily_ranking AS
SELECT 
    concept_name,
    trading_date,
    total_volume,
    stock_count,
    volume_rank,
    is_new_high,
    volume_change_pct
FROM concept_daily_metrics
WHERE trading_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
ORDER BY trading_date DESC, volume_rank ASC;
```

### 3. **分层存储策略**

#### 🔥 热数据层 (最近30天)
```sql
-- 内存表：当天数据
CREATE TABLE today_trading_cache (
    stock_code VARCHAR(20) PRIMARY KEY,
    stock_name VARCHAR(100),
    trading_volume BIGINT,
    concept_count SMALLINT,
    rank_in_date MEDIUMINT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=MEMORY;

-- 热数据表：最近30天 (SSD存储)
CREATE TABLE recent_trading_data AS SELECT * FROM daily_trading_unified 
WHERE trading_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY);
```

#### ❄️ 冷数据层 (历史数据)
```sql
-- 历史数据归档表 (机械硬盘存储)
CREATE TABLE historical_trading_archive (
    -- 相同结构但存储在归档存储
    LIKE daily_trading_unified
) ENGINE=InnoDB DATA DIRECTORY='/archive/mysql/';
```

## 🚀 导入→汇总→查询工作流优化

### 1. **导入阶段优化**

```python
# 批量导入优化策略
class OptimizedImportService:
    
    def import_txt_data(self, file_path: str, trading_date: date):
        """优化的导入流程"""
        
        # Step 1: 关闭自动提交，使用大事务
        with db.begin():
            # Step 2: 清理当日旧数据（如果存在）
            self.cleanup_existing_data(trading_date)
            
            # Step 3: 批量插入原始数据 (5000条/批次)
            batch_size = 5000
            raw_data = self.parse_txt_file(file_path)
            
            for batch in self.chunk_data(raw_data, batch_size):
                db.bulk_insert_mappings(DailyTradingUnified, batch)
            
            # Step 4: 立即计算汇总数据
            self.calculate_daily_metrics(trading_date)
            
            # Step 5: 更新缓存表
            self.refresh_cache_tables(trading_date)
    
    def calculate_daily_metrics(self, trading_date: date):
        """一次性计算所有汇总指标"""
        
        # 计算股票排名
        db.execute("""
            UPDATE daily_trading_unified SET rank_in_date = (
                SELECT rank_num FROM (
                    SELECT stock_code, 
                           ROW_NUMBER() OVER (ORDER BY trading_volume DESC) as rank_num
                    FROM daily_trading_unified 
                    WHERE trading_date = %s
                ) ranked WHERE ranked.stock_code = daily_trading_unified.stock_code
            ) WHERE trading_date = %s
        """, [trading_date, trading_date])
        
        # 计算概念汇总
        db.execute("""
            INSERT INTO concept_daily_metrics (
                concept_name, trading_date, total_volume, stock_count, avg_volume, max_volume
            )
            SELECT 
                concept_name,
                %s,
                SUM(trading_volume),
                COUNT(*),
                AVG(trading_volume),
                MAX(trading_volume)
            FROM stock_concept_daily_snapshot 
            WHERE trading_date = %s
            GROUP BY concept_name
        """, [trading_date, trading_date])
        
        # 计算概念排名
        db.execute("""
            UPDATE concept_daily_metrics SET volume_rank = (
                SELECT rank_num FROM (
                    SELECT concept_name,
                           ROW_NUMBER() OVER (ORDER BY total_volume DESC) as rank_num
                    FROM concept_daily_metrics 
                    WHERE trading_date = %s
                ) ranked WHERE ranked.concept_name = concept_daily_metrics.concept_name
            ) WHERE trading_date = %s
        """, [trading_date, trading_date])
```

### 2. **查询阶段优化**

```python
# 超高速查询服务
class HighSpeedQueryService:
    
    def get_stock_daily_summary(self, trading_date: date, page: int, size: int):
        """毫秒级股票列表查询"""
        
        # 直接查询优化视图，无需JOIN
        query = """
            SELECT stock_code, stock_name, trading_volume, concept_count, rank_in_date
            FROM v_stock_daily_summary 
            WHERE trading_date = %s 
            ORDER BY rank_in_date 
            LIMIT %s OFFSET %s
        """
        
        # 使用覆盖索引，避免回表查询
        return db.execute(query, [trading_date, size, (page-1)*size]).fetchall()
    
    def get_concept_rankings(self, trading_date: date, limit: int):
        """毫秒级概念排行查询"""
        
        # 直接从预计算表查询
        query = """
            SELECT concept_name, total_volume, stock_count, volume_rank, is_new_high
            FROM concept_daily_metrics 
            WHERE trading_date = %s 
            ORDER BY volume_rank 
            LIMIT %s
        """
        
        return db.execute(query, [trading_date, limit]).fetchall()
    
    def get_stock_concepts(self, stock_code: str, trading_date: date):
        """毫秒级股票概念查询"""
        
        # 一次查询获取所有概念信息
        query = """
            SELECT concept_name, concept_rank, volume_percentage, 
                   concept_total_volume, trading_volume
            FROM stock_concept_daily_snapshot 
            WHERE stock_code = %s AND trading_date = %s 
            ORDER BY concept_total_volume DESC
        """
        
        return db.execute(query, [stock_code, trading_date]).fetchall()
```

## 📊 性能预期提升

### 查询性能对比

| 查询类型 | 优化前 | 优化后 | 提升倍数 |
|---------|--------|--------|----------|
| **股票列表(5000条)** | 5-10秒 | 50-100ms | **50-200倍** |
| **概念排行(500个)** | 2-3秒 | 20-50ms | **60-150倍** |
| **股票概念查询** | 500ms | 10-20ms | **25-50倍** |
| **分页查询** | 1-2秒 | 5-10ms | **100-400倍** |

### 存储空间预估

| 表名 | 单日数据量 | 月存储空间 | 年存储空间 |
|------|-----------|-----------|-----------|
| **daily_trading_unified** | 5000条 | ~15MB | ~180MB |
| **concept_daily_metrics** | 500条 | ~1.5MB | ~18MB |
| **stock_concept_snapshot** | 50000条 | ~150MB | ~1.8GB |
| **索引空间** | - | ~50MB | ~600MB |
| **总计** | - | ~220MB/月 | ~2.6GB/年 |

## 🛠️ 实施计划

### Phase 1: 新表结构创建 (1天)
```bash
# 1. 创建新的优化表结构
./scripts/database/create_optimized_tables.sql

# 2. 创建视图和索引
./scripts/database/create_views_and_indexes.sql
```

### Phase 2: 数据迁移 (1天)
```bash
# 1. 迁移历史数据到新表
./scripts/database/migrate_historical_data.py

# 2. 验证数据一致性
./scripts/database/validate_migration.py
```

### Phase 3: 应用层适配 (1天)
```python
# 1. 更新导入服务
# 2. 更新查询API
# 3. 更新前端调用
```

### Phase 4: 性能测试和调优 (1天)
```bash
# 1. 压力测试
# 2. 索引调优
# 3. 缓存策略验证
```

## ⚠️ 注意事项

### 1. **向后兼容**
- 保留旧表结构，逐步迁移
- API接口保持兼容
- 数据校验和回滚预案

### 2. **监控指标**
- 查询响应时间
- 导入处理时间  
- 存储空间使用
- 索引命中率

### 3. **维护策略**
- 定期分区维护
- 历史数据归档
- 索引重建计划
- 性能监控告警

## 🎯 预期收益

### 1. **性能提升**
- 查询速度提升50-200倍
- 导入效率提升5-10倍
- 并发处理能力提升10倍

### 2. **用户体验**
- 页面加载从秒级降至毫秒级
- 支持更大数据量
- 更流畅的分页浏览

### 3. **系统稳定性**
- 减少数据库负载
- 降低CPU使用率
- 提高系统并发能力

---

**设计负责人**: 数据库架构师 | **评审时间**: 2025-09-13 | **实施优先级**: 高