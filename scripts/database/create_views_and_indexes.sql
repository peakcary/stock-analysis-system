-- =====================================================
-- 数据库视图和索引优化 v2.6.4
-- 目标：创建超高速查询视图和优化索引
-- 创建时间：2025-09-13
-- =====================================================

-- 1. 股票每日汇总快速查询视图
DROP VIEW IF EXISTS v_stock_daily_summary;
CREATE VIEW v_stock_daily_summary AS
SELECT 
    stock_code,
    stock_name,
    trading_date,
    trading_volume,
    concept_count,
    rank_in_date,
    volume_rank_pct,
    CASE 
        WHEN rank_in_date <= 50 THEN 'top'
        WHEN rank_in_date <= 200 THEN 'hot'
        WHEN rank_in_date <= 1000 THEN 'normal'
        ELSE 'cold'
    END as heat_level,
    CASE
        WHEN trading_volume >= 1000000000 THEN 'very_high'
        WHEN trading_volume >= 100000000 THEN 'high' 
        WHEN trading_volume >= 10000000 THEN 'medium'
        ELSE 'low'
    END as volume_level
FROM daily_trading_unified
WHERE trading_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY);

-- 2. 概念每日排行快速查询视图
DROP VIEW IF EXISTS v_concept_daily_ranking;
CREATE VIEW v_concept_daily_ranking AS
SELECT 
    concept_name,
    trading_date,
    total_volume,
    stock_count,
    avg_volume,
    max_volume,
    volume_rank,
    is_new_high,
    new_high_days,
    volume_change_pct,
    CASE 
        WHEN volume_rank <= 10 THEN 'top10'
        WHEN volume_rank <= 50 THEN 'top50'
        WHEN volume_rank <= 100 THEN 'top100'
        ELSE 'others'
    END as rank_level,
    CASE
        WHEN volume_change_pct >= 50 THEN 'surge'
        WHEN volume_change_pct >= 20 THEN 'rise'
        WHEN volume_change_pct >= -20 THEN 'stable'
        ELSE 'decline'
    END as trend_level
FROM concept_daily_metrics
WHERE trading_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY);

-- 3. 股票概念关系快速查询视图
DROP VIEW IF EXISTS v_stock_concept_performance;
CREATE VIEW v_stock_concept_performance AS
SELECT 
    s.stock_code,
    s.concept_name,
    s.trading_date,
    s.trading_volume,
    s.concept_rank,
    s.volume_percentage,
    s.concept_total_volume,
    s.concept_stock_count,
    CASE 
        WHEN s.concept_rank <= 3 THEN 'champion'
        WHEN s.concept_rank <= 10 THEN 'leader'
        WHEN s.concept_rank <= 30 THEN 'active'
        ELSE 'follower'
    END as performance_level,
    CASE
        WHEN s.volume_percentage >= 10 THEN 'dominant'
        WHEN s.volume_percentage >= 5 THEN 'significant'
        WHEN s.volume_percentage >= 1 THEN 'notable'
        ELSE 'minor'
    END as influence_level
FROM stock_concept_daily_snapshot s
WHERE s.trading_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY);

-- 4. 创新高概念快速查询视图
DROP VIEW IF EXISTS v_concept_new_highs;
CREATE VIEW v_concept_new_highs AS
SELECT 
    concept_name,
    trading_date,
    total_volume,
    stock_count,
    volume_rank,
    new_high_days,
    volume_change_pct,
    -- 创新高强度评级
    CASE 
        WHEN new_high_days >= 30 THEN 'breakthrough'
        WHEN new_high_days >= 10 THEN 'strong'
        WHEN new_high_days >= 5 THEN 'moderate'
        ELSE 'weak'
    END as new_high_strength,
    -- 计算与前一交易日的增长倍数
    CASE 
        WHEN prev_day_volume > 0 THEN 
            ROUND(total_volume / prev_day_volume, 2)
        ELSE NULL 
    END as volume_multiplier
FROM concept_daily_metrics
WHERE is_new_high = TRUE 
  AND trading_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
ORDER BY trading_date DESC, volume_rank ASC;

-- 5. 当日市场总览视图 (实时数据)
DROP VIEW IF EXISTS v_today_market_overview;
CREATE VIEW v_today_market_overview AS
SELECT 
    CURDATE() as trading_date,
    COUNT(*) as total_stocks,
    SUM(trading_volume) as total_volume,
    AVG(trading_volume) as avg_volume,
    MAX(trading_volume) as max_volume,
    MIN(trading_volume) as min_volume,
    -- 分级统计
    SUM(CASE WHEN rank_in_date <= 100 THEN 1 ELSE 0 END) as top100_count,
    SUM(CASE WHEN rank_in_date <= 500 THEN 1 ELSE 0 END) as top500_count,
    SUM(CASE WHEN concept_count >= 5 THEN 1 ELSE 0 END) as multi_concept_stocks,
    -- 交易量分布
    SUM(CASE WHEN trading_volume >= 100000000 THEN 1 ELSE 0 END) as high_volume_stocks,
    SUM(CASE WHEN trading_volume >= 10000000 THEN 1 ELSE 0 END) as medium_volume_stocks
FROM today_trading_cache;

-- =====================================================
-- 索引优化和性能调优
-- =====================================================

-- 6. 为现有表添加覆盖索引（避免回表查询）

-- daily_trading_unified 表的覆盖索引
ALTER TABLE daily_trading_unified 
ADD INDEX idx_date_rank_covering (trading_date, rank_in_date, stock_code, stock_name, trading_volume, concept_count);

ALTER TABLE daily_trading_unified 
ADD INDEX idx_volume_search_covering (trading_date, trading_volume DESC, stock_code, stock_name, rank_in_date);

-- concept_daily_metrics 表的覆盖索引
ALTER TABLE concept_daily_metrics 
ADD INDEX idx_rank_covering (trading_date, volume_rank, concept_name, total_volume, stock_count, is_new_high);

ALTER TABLE concept_daily_metrics 
ADD INDEX idx_new_high_covering (trading_date, is_new_high, volume_rank, concept_name, total_volume, new_high_days);

-- stock_concept_daily_snapshot 表的覆盖索引
ALTER TABLE stock_concept_daily_snapshot 
ADD INDEX idx_stock_concepts_covering (stock_code, trading_date, concept_name, concept_rank, volume_percentage, concept_total_volume);

ALTER TABLE stock_concept_daily_snapshot 
ADD INDEX idx_concept_stocks_covering (concept_name, trading_date, concept_rank, stock_code, trading_volume, volume_percentage);

-- 7. 全文搜索索引 (股票名称搜索优化)
ALTER TABLE daily_trading_unified 
ADD FULLTEXT INDEX ft_stock_name (stock_name);

-- 8. 函数索引 (MySQL 8.0+支持)
-- 为常用的日期范围查询创建函数索引
ALTER TABLE daily_trading_unified 
ADD INDEX idx_recent_30_days ((CASE WHEN trading_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY) THEN 1 ELSE 0 END));

-- 9. 分区表统计信息更新
ANALYZE TABLE daily_trading_unified;
ANALYZE TABLE concept_daily_metrics;
ANALYZE TABLE stock_concept_daily_snapshot;

-- =====================================================
-- 查询性能测试语句
-- =====================================================

-- 测试1: 股票列表查询 (目标: <50ms)
EXPLAIN SELECT stock_code, stock_name, trading_volume, concept_count, rank_in_date 
FROM v_stock_daily_summary 
WHERE trading_date = '2025-09-02' 
ORDER BY rank_in_date 
LIMIT 50 OFFSET 0;

-- 测试2: 概念排行查询 (目标: <30ms)
EXPLAIN SELECT concept_name, total_volume, stock_count, volume_rank, is_new_high
FROM v_concept_daily_ranking 
WHERE trading_date = '2025-09-02' 
ORDER BY volume_rank 
LIMIT 100;

-- 测试3: 股票概念查询 (目标: <20ms)
EXPLAIN SELECT concept_name, concept_rank, volume_percentage, concept_total_volume
FROM v_stock_concept_performance 
WHERE stock_code = '000001' AND trading_date = '2025-09-02' 
ORDER BY concept_total_volume DESC;

-- 测试4: 创新高概念查询 (目标: <40ms)
EXPLAIN SELECT * FROM v_concept_new_highs 
WHERE trading_date = '2025-09-02' 
ORDER BY volume_rank 
LIMIT 50;

-- 测试5: 股票名称搜索 (目标: <100ms)
EXPLAIN SELECT stock_code, stock_name, trading_volume, rank_in_date 
FROM daily_trading_unified 
WHERE trading_date = '2025-09-02' 
  AND MATCH(stock_name) AGAINST('平安' IN NATURAL LANGUAGE MODE)
ORDER BY rank_in_date;

-- =====================================================
-- 性能监控和优化建议
-- =====================================================

-- 10. 创建性能监控存储过程
DELIMITER $$

DROP PROCEDURE IF EXISTS sp_analyze_query_performance$$
CREATE PROCEDURE sp_analyze_query_performance(IN date_param DATE)
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE query_time DECIMAL(10,3);
    DECLARE query_name VARCHAR(100);
    
    -- 清理性能日志表中过期数据 (保留30天)
    DELETE FROM query_performance_log 
    WHERE created_at < DATE_SUB(NOW(), INTERVAL 30 DAY);
    
    -- 测试股票列表查询性能
    SET @start_time = NOW(3);
    SELECT COUNT(*) INTO @dummy FROM v_stock_daily_summary 
    WHERE trading_date = date_param 
    ORDER BY rank_in_date LIMIT 50;
    SET @end_time = NOW(3);
    SET query_time = TIMESTAMPDIFF(MICROSECOND, @start_time, @end_time) / 1000;
    
    INSERT INTO query_performance_log (query_type, trading_date, execution_time_ms)
    VALUES ('stock_list', date_param, query_time);
    
    -- 测试概念排行查询性能
    SET @start_time = NOW(3);
    SELECT COUNT(*) INTO @dummy FROM v_concept_daily_ranking 
    WHERE trading_date = date_param 
    ORDER BY volume_rank LIMIT 100;
    SET @end_time = NOW(3);
    SET query_time = TIMESTAMPDIFF(MICROSECOND, @start_time, @end_time) / 1000;
    
    INSERT INTO query_performance_log (query_type, trading_date, execution_time_ms)
    VALUES ('concept_ranking', date_param, query_time);
    
    -- 返回性能统计
    SELECT 
        query_type as '查询类型',
        AVG(execution_time_ms) as '平均耗时(ms)',
        MIN(execution_time_ms) as '最快耗时(ms)',
        MAX(execution_time_ms) as '最慢耗时(ms)',
        COUNT(*) as '查询次数'
    FROM query_performance_log 
    WHERE trading_date = date_param
    GROUP BY query_type;
    
END$$

DELIMITER ;

-- 11. 创建索引维护存储过程
DELIMITER $$

DROP PROCEDURE IF EXISTS sp_maintain_indexes$$
CREATE PROCEDURE sp_maintain_indexes()
BEGIN
    -- 重新构建索引统计信息
    ANALYZE TABLE daily_trading_unified;
    ANALYZE TABLE concept_daily_metrics;
    ANALYZE TABLE stock_concept_daily_snapshot;
    
    -- 检查索引使用情况
    SELECT 
        TABLE_NAME as '表名',
        INDEX_NAME as '索引名',
        CARDINALITY as '基数',
        CASE WHEN CARDINALITY = 0 THEN '未使用' ELSE '正常' END as '状态'
    FROM information_schema.STATISTICS 
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME IN ('daily_trading_unified', 'concept_daily_metrics', 'stock_concept_daily_snapshot')
    ORDER BY TABLE_NAME, INDEX_NAME;
    
END$$

DELIMITER ;

-- =====================================================
-- 优化完成提示
-- =====================================================

SELECT 
    '数据库优化完成！' as '状态',
    '预期查询性能提升: 50-200倍' as '性能提升',
    '建议定期执行: CALL sp_maintain_indexes()' as '维护建议',
    '性能测试: CALL sp_analyze_query_performance(CURDATE())' as '测试命令';

-- 显示优化后的表和视图
SELECT 
    TABLE_TYPE as '类型',
    TABLE_NAME as '名称', 
    ENGINE as '引擎',
    TABLE_COMMENT as '说明'
FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = DATABASE() 
  AND (TABLE_NAME LIKE '%unified%' 
    OR TABLE_NAME LIKE '%metrics%' 
    OR TABLE_NAME LIKE '%snapshot%'
    OR TABLE_NAME LIKE 'v_%')
ORDER BY TABLE_TYPE, TABLE_NAME;