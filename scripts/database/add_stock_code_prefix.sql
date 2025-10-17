-- ============================================
-- 添加股票代码前缀字段
-- 功能：在表中添加 stock_code_prefix 字段
--      单独保存股票代码前缀（如SH、SZ、BJ、HK等）
-- 版本：v2.7.2
-- ============================================

USE stock_analysis_dev;

-- 1. stocks 表添加 stock_code_prefix 字段
ALTER TABLE stocks
ADD COLUMN stock_code_prefix VARCHAR(10) COMMENT '股票代码前缀（SH/SZ/BJ/HK等）' AFTER original_stock_code;

-- 2. stock_concept_raw_data 表添加 stock_code_prefix 字段
ALTER TABLE stock_concept_raw_data
ADD COLUMN stock_code_prefix VARCHAR(10) COMMENT '股票代码前缀（SH/SZ/BJ/HK等）' AFTER original_stock_code;

-- 3. 从 original_stock_code 提取前缀更新 stocks 表
UPDATE stocks
SET stock_code_prefix = CASE
    WHEN original_stock_code LIKE 'SH%' THEN 'SH'
    WHEN original_stock_code LIKE 'SZ%' THEN 'SZ'
    WHEN original_stock_code LIKE 'BJ%' THEN 'BJ'
    WHEN original_stock_code LIKE 'HK%' THEN 'HK'
    ELSE NULL
END
WHERE original_stock_code IS NOT NULL;

-- 4. 从 original_stock_code 提取前缀更新 stock_concept_raw_data 表
UPDATE stock_concept_raw_data
SET stock_code_prefix = CASE
    WHEN original_stock_code LIKE 'SH%' THEN 'SH'
    WHEN original_stock_code LIKE 'SZ%' THEN 'SZ'
    WHEN original_stock_code LIKE 'BJ%' THEN 'BJ'
    WHEN original_stock_code LIKE 'HK%' THEN 'HK'
    ELSE NULL
END
WHERE original_stock_code IS NOT NULL;

-- 验证
SELECT '=== stocks 表结构 ===' AS info;
DESCRIBE stocks;

SELECT '=== stock_concept_raw_data 表结构 ===' AS info;
DESCRIBE stock_concept_raw_data;

SELECT '=== 数据示例 (stocks) ===' AS info;
SELECT id, stock_code, original_stock_code, stock_code_prefix, stock_name
FROM stocks
LIMIT 5;

SELECT '=== 数据示例 (stock_concept_raw_data) ===' AS info;
SELECT id, stock_code, original_stock_code, stock_code_prefix, stock_name, trade_date
FROM stock_concept_raw_data
ORDER BY trade_date DESC
LIMIT 5;
