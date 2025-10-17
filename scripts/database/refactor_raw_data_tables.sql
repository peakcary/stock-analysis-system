-- ============================================
-- Refactor raw data tables structure (Plan 1)
-- Version: v2.7.3
-- ============================================

USE stock_analysis_dev;

-- 1. Create import batches table
CREATE TABLE import_batches (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT 'primary key',
    import_date DATE NOT NULL COMMENT 'import date',
    import_type VARCHAR(10) NOT NULL COMMENT 'import type csv/txt',
    file_name VARCHAR(255) NOT NULL COMMENT 'source file name',
    record_count INT DEFAULT 0 COMMENT 'record count',
    status VARCHAR(20) DEFAULT 'success' COMMENT 'import status success/partial/failed',
    remark TEXT COMMENT 'remark',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'created time',

    INDEX idx_import_date (import_date),
    INDEX idx_import_type (import_type),
    UNIQUE KEY uk_file_date_type (file_name, import_date, import_type)
) COMMENT='import batches management';

-- 2. Create raw import data table
CREATE TABLE raw_import_data (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT 'primary key',

    -- batch association
    import_batch_id INT NOT NULL COMMENT 'import batch id',
    row_number INT NOT NULL COMMENT 'original row number',

    -- time info
    trade_date DATE NOT NULL COMMENT 'trade date',
    import_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'import time',

    -- stock code three columns
    stock_code_raw VARCHAR(20) NOT NULL COMMENT 'original stock code like SH600036',
    stock_code_normalized VARCHAR(10) NOT NULL COMMENT 'normalized code like 600036',
    stock_code_prefix VARCHAR(10) COMMENT 'code prefix SH/SZ/BJ/HK',

    -- stock basic info
    stock_name VARCHAR(100) NOT NULL COMMENT 'stock name',
    industry VARCHAR(100) COMMENT 'industry',

    -- trading data
    price DECIMAL(10, 2) DEFAULT 0 COMMENT 'price',
    turnover_rate DECIMAL(5, 2) DEFAULT 0 COMMENT 'turnover rate',
    net_inflow DECIMAL(15, 2) DEFAULT 0 COMMENT 'net inflow',
    pages_count INT DEFAULT 0 COMMENT 'pages count',
    total_reads INT DEFAULT 0 COMMENT 'total reads',

    -- CSV only
    concept VARCHAR(100) COMMENT 'concept csv only',

    -- TXT only
    heat_value DECIMAL(15, 2) COMMENT 'heat value txt only',

    -- data source
    source_type VARCHAR(10) NOT NULL COMMENT 'source type csv/txt',
    source_file VARCHAR(255) COMMENT 'source file name',

    -- foreign key
    CONSTRAINT fk_import_batch FOREIGN KEY (import_batch_id) REFERENCES import_batches(id) ON DELETE CASCADE,

    -- indexes
    INDEX idx_import_batch_id (import_batch_id),
    INDEX idx_trade_date (trade_date),
    INDEX idx_stock_code (stock_code_normalized),
    INDEX idx_source_type (source_type)
) COMMENT='raw import data table';

-- 3. Create raw data mapping table
CREATE TABLE raw_data_mapping (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT 'primary key',

    -- raw data association
    raw_import_data_id BIGINT NOT NULL COMMENT 'raw import data id',

    -- business data association
    stock_id INT COMMENT 'stock id',
    concept_id INT COMMENT 'concept id',
    daily_stock_data_id INT COMMENT 'daily stock data id',
    stock_concept_id INT COMMENT 'stock-concept association id',

    -- process status
    process_status VARCHAR(20) DEFAULT 'pending' COMMENT 'process status pending/success/error',
    error_message TEXT COMMENT 'error message',

    -- timestamp
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'created time',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'updated time',

    -- foreign key
    CONSTRAINT fk_raw_import_data FOREIGN KEY (raw_import_data_id) REFERENCES raw_import_data(id) ON DELETE CASCADE,

    INDEX idx_raw_import_data_id (raw_import_data_id),
    INDEX idx_stock_id (stock_id),
    INDEX idx_process_status (process_status)
) COMMENT='raw data to business data mapping';

-- 4. Verification
SELECT '=== import_batches structure ===' AS info;
DESCRIBE import_batches;

SELECT '=== raw_import_data structure ===' AS info;
DESCRIBE raw_import_data;

SELECT '=== raw_data_mapping structure ===' AS info;
DESCRIBE raw_data_mapping;
