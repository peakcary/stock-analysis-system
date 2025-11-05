-- ============================================
-- CSV原始数据表创建脚本
-- 功能：保存CSV文件的原始数据，不进行拆分
-- 创建日期：2025-10-15
-- ============================================

-- 创建原始数据表
CREATE TABLE IF NOT EXISTS stock_concept_raw_data (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    import_date DATE NOT NULL COMMENT '导入日期',
    trade_date DATE NOT NULL COMMENT '交易日期',

    -- CSV原始字段
    stock_code VARCHAR(10) NOT NULL COMMENT '股票代码',
    stock_name VARCHAR(100) NOT NULL COMMENT '股票名称',
    concept VARCHAR(100) NOT NULL COMMENT '概念',
    industry VARCHAR(100) COMMENT '行业',

    -- 交易数据
    price DECIMAL(10,2) DEFAULT 0 COMMENT '价格',
    turnover_rate DECIMAL(5,2) DEFAULT 0 COMMENT '换手率',
    net_inflow DECIMAL(15,2) DEFAULT 0 COMMENT '净流入',
    pages_count INT DEFAULT 0 COMMENT '页数',
    total_reads INT DEFAULT 0 COMMENT '总阅读数',

    -- 元数据
    file_name VARCHAR(255) COMMENT '来源文件名',
    `row_number` INT COMMENT 'CSV行号',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    -- 索引
    INDEX idx_import_date (import_date),
    INDEX idx_trade_date (trade_date),
    INDEX idx_stock_code (stock_code),
    INDEX idx_concept (concept),
    INDEX idx_raw_trade_date_stock (trade_date, stock_code),
    INDEX idx_raw_trade_date_concept (trade_date, concept),
    INDEX idx_raw_stock_concept (stock_code, concept)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='CSV原始数据表-不拆分';

-- 查看表结构
DESCRIBE stock_concept_raw_data;

-- 查询示例（注释形式）
-- SELECT * FROM stock_concept_raw_data WHERE trade_date = '2025-10-15' ORDER BY net_inflow DESC LIMIT 50;
-- SELECT stock_code, stock_name, concept, net_inflow FROM stock_concept_raw_data WHERE trade_date = '2025-10-15' AND concept = '人工智能';
-- SELECT COUNT(*) FROM stock_concept_raw_data WHERE trade_date = '2025-10-15';
