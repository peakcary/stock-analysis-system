-- ============================================
-- 添加原始股票代码字段
-- 功能：在表中添加 original_stock_code 字段
--      保存带前缀的原始代码（如SH600036）
-- 版本：v2.7.1
-- ============================================

USE stock_analysis_dev;

-- 1. stocks 表添加 original_stock_code 字段
ALTER TABLE stocks
ADD COLUMN original_stock_code VARCHAR(20) COMMENT '原始股票代码（含SH/SZ等前缀）' AFTER stock_code;

-- 2. stock_concept_raw_data 表添加 original_stock_code 字段
ALTER TABLE stock_concept_raw_data
ADD COLUMN original_stock_code VARCHAR(20) COMMENT '原始股票代码（含前缀）' AFTER stock_code;

-- 3. 更新 stocks 表的 stock_code 字段注释
ALTER TABLE stocks
MODIFY COLUMN stock_code VARCHAR(10) NOT NULL COMMENT '股票代码（规范化后，无前缀）';

-- 4. 更新 stock_concept_raw_data 表的 stock_code 字段注释
ALTER TABLE stock_concept_raw_data
MODIFY COLUMN stock_code VARCHAR(10) NOT NULL COMMENT '股票代码（规范化后）';

-- 5. 数据迁移：已有数据的 original_stock_code 暂时设置为与 stock_code 相同
UPDATE stocks
SET original_stock_code = stock_code
WHERE original_stock_code IS NULL;

UPDATE stock_concept_raw_data
SET original_stock_code = stock_code
WHERE original_stock_code IS NULL;

-- 验证
SELECT '=== stocks 表结构 ===' AS info;
DESCRIBE stocks;

SELECT '=== stock_concept_raw_data 表结构 ===' AS info;
DESCRIBE stock_concept_raw_data;

SELECT '=== 数据示例 (stocks) ===' AS info;
SELECT id, stock_code, original_stock_code, stock_name
FROM stocks
LIMIT 5;

SELECT '=== 数据示例 (stock_concept_raw_data) ===' AS info;
SELECT id, stock_code, original_stock_code, stock_name, trade_date
FROM stock_concept_raw_data
ORDER BY trade_date DESC
LIMIT 5;
