-- =====================================================
-- 数据库性能优化表结构 v2.6.4
-- 目标：导入→汇总→查询工作流极致优化
-- 创建时间：2025-09-13
-- =====================================================

-- 1. 统一的每日交易表 (替换 daily_trading 和 daily_stock_data)
DROP TABLE IF EXISTS daily_trading_unified;
CREATE TABLE daily_trading_unified (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    stock_code VARCHAR(20) NOT NULL COMMENT '股票代码(标准化格式)',
    stock_name VARCHAR(100) NOT NULL COMMENT '股票名称',
    trading_date DATE NOT NULL COMMENT '交易日期',
    trading_volume BIGINT NOT NULL DEFAULT 0 COMMENT '交易量',
    heat_value DECIMAL(15,2) DEFAULT 0 COMMENT '热度值(来自TXT文件)',
    
    -- 预计算字段，避免查询时实时计算
    concept_count SMALLINT DEFAULT 0 COMMENT '概念数量(预计算)',
    rank_in_date MEDIUMINT DEFAULT 0 COMMENT '当日排名(预计算)',
    volume_rank_pct DECIMAL(5,2) DEFAULT 0 COMMENT '交易量排名百分位',
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 优化索引设计
    INDEX idx_date_volume (trading_date, trading_volume DESC) COMMENT '日期+交易量倒序(列表查询)',
    INDEX idx_date_rank (trading_date, rank_in_date) COMMENT '日期+排名(分页查询)',
    INDEX idx_stock_date (stock_code, trading_date) COMMENT '股票+日期(个股查询)',
    INDEX idx_name_search (stock_name) COMMENT '股票名称搜索',
    UNIQUE KEY uk_stock_date (stock_code, trading_date) COMMENT '唯一约束'
) ENGINE=InnoDB 
  DEFAULT CHARSET=utf8mb4 
  COLLATE=utf8mb4_unicode_ci
  COMMENT='统一每日交易表-性能优化版'
  -- 按月分区，提升查询性能
  PARTITION BY RANGE (TO_DAYS(trading_date)) (
    PARTITION p202409 VALUES LESS THAN (TO_DAYS('2024-10-01')),
    PARTITION p202410 VALUES LESS THAN (TO_DAYS('2024-11-01')),
    PARTITION p202411 VALUES LESS THAN (TO_DAYS('2024-12-01')),
    PARTITION p202412 VALUES LESS THAN (TO_DAYS('2025-01-01')),
    PARTITION p202501 VALUES LESS THAN (TO_DAYS('2025-02-01')),
    PARTITION p202502 VALUES LESS THAN (TO_DAYS('2025-03-01')),
    PARTITION p202503 VALUES LESS THAN (TO_DAYS('2025-04-01')),
    PARTITION p202504 VALUES LESS THAN (TO_DAYS('2025-05-01')),
    PARTITION p202505 VALUES LESS THAN (TO_DAYS('2025-06-01')),
    PARTITION p202506 VALUES LESS THAN (TO_DAYS('2025-07-01')),
    PARTITION p202507 VALUES LESS THAN (TO_DAYS('2025-08-01')),
    PARTITION p202508 VALUES LESS THAN (TO_DAYS('2025-09-01')),
    PARTITION p202509 VALUES LESS THAN (TO_DAYS('2025-10-01')),
    PARTITION p202510 VALUES LESS THAN (TO_DAYS('2025-11-01')),
    PARTITION p202511 VALUES LESS THAN (TO_DAYS('2025-12-01')),
    PARTITION p202512 VALUES LESS THAN (TO_DAYS('2026-01-01')),
    PARTITION p_future VALUES LESS THAN MAXVALUE
  );

-- 2. 概念每日指标表 (替换 ConceptDailySummary 和其他重复表)
DROP TABLE IF EXISTS concept_daily_metrics;
CREATE TABLE concept_daily_metrics (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    concept_name VARCHAR(100) NOT NULL COMMENT '概念名称',
    trading_date DATE NOT NULL COMMENT '交易日期',
    
    -- 核心指标
    total_volume BIGINT NOT NULL DEFAULT 0 COMMENT '概念总交易量',
    stock_count SMALLINT NOT NULL DEFAULT 0 COMMENT '概念包含股票数量',
    avg_volume DECIMAL(15,2) NOT NULL DEFAULT 0 COMMENT '平均交易量',
    max_volume BIGINT NOT NULL DEFAULT 0 COMMENT '概念内最大单股交易量',
    min_volume BIGINT NOT NULL DEFAULT 0 COMMENT '概念内最小单股交易量',
    
    -- 预计算排名和趋势
    volume_rank SMALLINT DEFAULT 0 COMMENT '概念交易量排名(预计算)',
    stock_count_rank SMALLINT DEFAULT 0 COMMENT '概念股票数量排名(预计算)',
    
    -- 趋势分析
    is_new_high BOOLEAN DEFAULT FALSE COMMENT '是否创新高',
    new_high_days SMALLINT DEFAULT 0 COMMENT '新高天数范围',
    volume_change_pct DECIMAL(5,2) DEFAULT 0 COMMENT '交易量变化百分比',
    prev_day_volume BIGINT DEFAULT 0 COMMENT '前一日交易量',
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 覆盖索引优化 - 避免回表查询
    INDEX idx_date_rank (trading_date, volume_rank) COMMENT '日期+排名(概念排行查询)',
    INDEX idx_date_volume (trading_date, total_volume DESC) COMMENT '日期+交易量倒序',
    INDEX idx_concept_date (concept_name, trading_date) COMMENT '概念+日期(时间序列)',
    INDEX idx_new_high (trading_date, is_new_high, volume_rank) COMMENT '创新高查询',
    UNIQUE KEY uk_concept_date (concept_name, trading_date) COMMENT '唯一约束'
) ENGINE=InnoDB 
  DEFAULT CHARSET=utf8mb4 
  COLLATE=utf8mb4_unicode_ci
  COMMENT='概念每日指标表-极致优化版'
  -- 按月分区
  PARTITION BY RANGE (TO_DAYS(trading_date)) (
    PARTITION p202409 VALUES LESS THAN (TO_DAYS('2024-10-01')),
    PARTITION p202410 VALUES LESS THAN (TO_DAYS('2024-11-01')),
    PARTITION p202411 VALUES LESS THAN (TO_DAYS('2024-12-01')),
    PARTITION p202412 VALUES LESS THAN (TO_DAYS('2025-01-01')),
    PARTITION p202501 VALUES LESS THAN (TO_DAYS('2025-02-01')),
    PARTITION p202502 VALUES LESS THAN (TO_DAYS('2025-03-01')),
    PARTITION p202503 VALUES LESS THAN (TO_DAYS('2025-04-01')),
    PARTITION p202504 VALUES LESS THAN (TO_DAYS('2025-05-01')),
    PARTITION p202505 VALUES LESS THAN (TO_DAYS('2025-06-01')),
    PARTITION p202506 VALUES LESS THAN (TO_DAYS('2025-07-01')),
    PARTITION p202507 VALUES LESS THAN (TO_DAYS('2025-08-01')),
    PARTITION p202508 VALUES LESS THAN (TO_DAYS('2025-09-01')),
    PARTITION p202509 VALUES LESS THAN (TO_DAYS('2025-10-01')),
    PARTITION p202510 VALUES LESS THAN (TO_DAYS('2025-11-01')),
    PARTITION p202511 VALUES LESS THAN (TO_DAYS('2025-12-01')),
    PARTITION p202512 VALUES LESS THAN (TO_DAYS('2026-01-01')),
    PARTITION p_future VALUES LESS THAN MAXVALUE
  );

-- 3. 股票概念关系每日快照表 (替换 StockConceptRanking)
DROP TABLE IF EXISTS stock_concept_daily_snapshot;
CREATE TABLE stock_concept_daily_snapshot (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    stock_code VARCHAR(20) NOT NULL COMMENT '股票代码',
    concept_name VARCHAR(100) NOT NULL COMMENT '概念名称',
    trading_date DATE NOT NULL COMMENT '交易日期',
    
    -- 股票在概念中的表现
    trading_volume BIGINT NOT NULL DEFAULT 0 COMMENT '股票交易量',
    concept_rank SMALLINT NOT NULL DEFAULT 0 COMMENT '在概念中的排名',
    volume_percentage DECIMAL(5,2) NOT NULL DEFAULT 0 COMMENT '占概念交易量百分比',
    
    -- 概念整体数据(冗余存储，避免JOIN)
    concept_total_volume BIGINT NOT NULL DEFAULT 0 COMMENT '概念总交易量',
    concept_stock_count SMALLINT NOT NULL DEFAULT 0 COMMENT '概念股票总数',
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    -- 多维度查询优化索引
    INDEX idx_stock_date (stock_code, trading_date) COMMENT '股票概念查询',
    INDEX idx_concept_date_rank (concept_name, trading_date, concept_rank) COMMENT '概念排行查询',
    INDEX idx_date_volume (trading_date, trading_volume DESC) COMMENT '全市场排行',
    INDEX idx_concept_rank (concept_name, concept_rank) COMMENT '概念内排名',
    UNIQUE KEY uk_stock_concept_date (stock_code, concept_name, trading_date) COMMENT '唯一约束'
) ENGINE=InnoDB 
  DEFAULT CHARSET=utf8mb4 
  COLLATE=utf8mb4_unicode_ci
  COMMENT='股票概念关系每日快照-超高速查询版'
  -- 按月分区，数据量最大的表
  PARTITION BY RANGE (TO_DAYS(trading_date)) (
    PARTITION p202409 VALUES LESS THAN (TO_DAYS('2024-10-01')),
    PARTITION p202410 VALUES LESS THAN (TO_DAYS('2024-11-01')),
    PARTITION p202411 VALUES LESS THAN (TO_DAYS('2024-12-01')),
    PARTITION p202412 VALUES LESS THAN (TO_DAYS('2025-01-01')),
    PARTITION p202501 VALUES LESS THAN (TO_DAYS('2025-02-01')),
    PARTITION p202502 VALUES LESS THAN (TO_DAYS('2025-03-01')),
    PARTITION p202503 VALUES LESS THAN (TO_DAYS('2025-04-01')),
    PARTITION p202504 VALUES LESS THAN (TO_DAYS('2025-05-01')),
    PARTITION p202505 VALUES LESS THAN (TO_DAYS('2025-06-01')),
    PARTITION p202506 VALUES LESS THAN (TO_DAYS('2025-07-01')),
    PARTITION p202507 VALUES LESS THAN (TO_DAYS('2025-08-01')),
    PARTITION p202508 VALUES LESS THAN (TO_DAYS('2025-09-01')),
    PARTITION p202509 VALUES LESS THAN (TO_DAYS('2025-10-01')),
    PARTITION p202510 VALUES LESS THAN (TO_DAYS('2025-11-01')),
    PARTITION p202511 VALUES LESS THAN (TO_DAYS('2025-12-01')),
    PARTITION p202512 VALUES LESS THAN (TO_DAYS('2026-01-01')),
    PARTITION p_future VALUES LESS THAN MAXVALUE
  );

-- 4. 内存缓存表 - 当天热数据 (极速查询)
DROP TABLE IF EXISTS today_trading_cache;
CREATE TABLE today_trading_cache (
    stock_code VARCHAR(20) PRIMARY KEY COMMENT '股票代码',
    stock_name VARCHAR(100) NOT NULL COMMENT '股票名称',
    trading_volume BIGINT NOT NULL COMMENT '交易量',
    concept_count SMALLINT DEFAULT 0 COMMENT '概念数量',
    rank_in_date MEDIUMINT DEFAULT 0 COMMENT '当日排名',
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最后更新时间'
) ENGINE=MEMORY 
  DEFAULT CHARSET=utf8mb4 
  COMMENT='当天交易数据缓存表-内存引擎';

-- 5. 数据导入处理记录表 (增强版)
DROP TABLE IF EXISTS txt_import_processing_log;
CREATE TABLE txt_import_processing_log (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    batch_id VARCHAR(50) NOT NULL COMMENT '批次ID',
    trading_date DATE NOT NULL COMMENT '交易日期',
    filename VARCHAR(255) NOT NULL COMMENT '文件名',
    
    -- 处理阶段
    stage ENUM('parsing', 'importing', 'calculating', 'indexing', 'completed', 'failed') 
        DEFAULT 'parsing' COMMENT '处理阶段',
    
    -- 数据统计
    total_records INT DEFAULT 0 COMMENT '总记录数',
    processed_records INT DEFAULT 0 COMMENT '已处理记录数',
    error_records INT DEFAULT 0 COMMENT '错误记录数',
    stocks_count INT DEFAULT 0 COMMENT '股票数量',
    concepts_count INT DEFAULT 0 COMMENT '概念数量',
    
    -- 性能指标
    start_time TIMESTAMP NOT NULL COMMENT '开始时间',
    end_time TIMESTAMP NULL COMMENT '结束时间',
    duration_seconds DECIMAL(10,3) DEFAULT 0 COMMENT '处理耗时(秒)',
    records_per_second DECIMAL(10,2) DEFAULT 0 COMMENT '处理速度(记录/秒)',
    
    -- 错误信息
    error_message TEXT COMMENT '错误信息',
    imported_by VARCHAR(50) NOT NULL COMMENT '导入人',
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    INDEX idx_trading_date (trading_date) COMMENT '交易日期查询',
    INDEX idx_batch_id (batch_id) COMMENT '批次查询',
    INDEX idx_stage_time (stage, start_time) COMMENT '处理阶段监控'
) ENGINE=InnoDB 
  DEFAULT CHARSET=utf8mb4 
  COLLATE=utf8mb4_unicode_ci
  COMMENT='TXT导入处理日志表-监控优化版';

-- 6. 查询性能监控表
DROP TABLE IF EXISTS query_performance_log;
CREATE TABLE query_performance_log (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    query_type ENUM('stock_list', 'concept_ranking', 'stock_concepts', 'search') 
        NOT NULL COMMENT '查询类型',
    trading_date DATE COMMENT '查询的交易日期',
    
    -- 查询参数
    query_params JSON COMMENT '查询参数',
    result_count INT DEFAULT 0 COMMENT '返回结果数量',
    
    -- 性能指标
    execution_time_ms DECIMAL(10,3) NOT NULL COMMENT '执行时间(毫秒)',
    database_time_ms DECIMAL(10,3) DEFAULT 0 COMMENT '数据库时间(毫秒)',
    cache_hit BOOLEAN DEFAULT FALSE COMMENT '是否命中缓存',
    
    -- 请求信息
    user_id VARCHAR(50) COMMENT '用户ID',
    ip_address VARCHAR(45) COMMENT 'IP地址',
    user_agent TEXT COMMENT '用户代理',
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    INDEX idx_query_type_time (query_type, created_at) COMMENT '查询类型和时间',
    INDEX idx_trading_date (trading_date) COMMENT '交易日期',
    INDEX idx_performance (execution_time_ms DESC) COMMENT '性能分析'
) ENGINE=InnoDB 
  DEFAULT CHARSET=utf8mb4 
  COLLATE=utf8mb4_unicode_ci
  COMMENT='查询性能监控表';

-- =====================================================
-- 创建优化后的表结构完成
-- 预期性能提升：查询速度提升50-200倍
-- 存储空间：合理增加30%，换取查询性能大幅提升
-- =====================================================

-- 显示表创建结果
SELECT 
    TABLE_NAME as '表名',
    ENGINE as '存储引擎',
    TABLE_ROWS as '预估行数',
    DATA_LENGTH as '数据大小',
    INDEX_LENGTH as '索引大小',
    TABLE_COMMENT as '表注释'
FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = DATABASE() 
  AND TABLE_NAME IN (
    'daily_trading_unified',
    'concept_daily_metrics', 
    'stock_concept_daily_snapshot',
    'today_trading_cache',
    'txt_import_processing_log',
    'query_performance_log'
  )
ORDER BY TABLE_NAME;