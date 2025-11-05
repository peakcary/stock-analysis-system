USE stock_analysis_dev;

CREATE TABLE IF NOT EXISTS import_batches (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    import_date DATE NOT NULL,
    import_type VARCHAR(10) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    record_count INT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'success',
    remark TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_import_date (import_date),
    INDEX idx_import_type (import_type),
    UNIQUE KEY uk_file_date_type (file_name, import_date, import_type)
);

CREATE TABLE IF NOT EXISTS raw_import_data (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    import_batch_id INT NOT NULL,
    row_number INT NOT NULL,
    trade_date DATE NOT NULL,
    import_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    stock_code_raw VARCHAR(20) NOT NULL,
    stock_code_normalized VARCHAR(10) NOT NULL,
    stock_code_prefix VARCHAR(10),
    stock_name VARCHAR(100) NOT NULL,
    industry VARCHAR(100),
    price DECIMAL(10, 2) DEFAULT 0,
    turnover_rate DECIMAL(5, 2) DEFAULT 0,
    net_inflow DECIMAL(15, 2) DEFAULT 0,
    pages_count INT DEFAULT 0,
    total_reads INT DEFAULT 0,
    concept VARCHAR(100),
    heat_value DECIMAL(15, 2),
    source_type VARCHAR(10) NOT NULL,
    source_file VARCHAR(255),
    CONSTRAINT fk_import_batch FOREIGN KEY (import_batch_id) REFERENCES import_batches(id) ON DELETE CASCADE,
    INDEX idx_import_batch_id (import_batch_id),
    INDEX idx_trade_date (trade_date),
    INDEX idx_stock_code (stock_code_normalized),
    INDEX idx_source_type (source_type)
);

CREATE TABLE IF NOT EXISTS raw_data_mapping (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    raw_import_data_id BIGINT NOT NULL,
    stock_id INT,
    concept_id INT,
    daily_stock_data_id INT,
    stock_concept_id INT,
    process_status VARCHAR(20) DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_raw_import_data FOREIGN KEY (raw_import_data_id) REFERENCES raw_import_data(id) ON DELETE CASCADE,
    INDEX idx_raw_import_data_id (raw_import_data_id),
    INDEX idx_stock_id (stock_id),
    INDEX idx_process_status (process_status)
);

SELECT '=== raw_import_data structure ===' AS info;
DESCRIBE raw_import_data;

SELECT '=== raw_data_mapping structure ===' AS info;
DESCRIBE raw_data_mapping;
