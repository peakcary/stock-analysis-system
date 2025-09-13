-- 简化的数据导入表结构
-- 专门用于存储原始导入数据

-- 1. 股票概念数据表 (对应CSV文件)
CREATE TABLE IF NOT EXISTS stock_concept_data (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    stock_code VARCHAR(20) NOT NULL COMMENT '股票代码',
    stock_name VARCHAR(100) NOT NULL COMMENT '股票名称', 
    page_count INT DEFAULT 0 COMMENT '全部页数',
    total_reads BIGINT DEFAULT 0 COMMENT '热帖首页页阅读总数',
    price DECIMAL(10,2) DEFAULT 0 COMMENT '价格',
    industry VARCHAR(100) COMMENT '行业',
    concept VARCHAR(100) COMMENT '概念',
    turnover_rate DECIMAL(8,4) DEFAULT 0 COMMENT '换手率',
    net_inflow DECIMAL(15,2) DEFAULT 0 COMMENT '净流入',
    import_date DATE NOT NULL COMMENT '导入日期',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_stock_code (stock_code),
    INDEX idx_stock_name (stock_name),
    INDEX idx_concept (concept),
    INDEX idx_import_date (import_date),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
COMMENT '股票概念数据表';

-- 2. 股票时间序列数据表 (对应TXT文件)  
CREATE TABLE IF NOT EXISTS stock_timeseries_data (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    stock_code VARCHAR(20) NOT NULL COMMENT '股票代码',
    trade_date DATE NOT NULL COMMENT '交易日期',
    value DECIMAL(15,2) NOT NULL COMMENT '数值',
    import_date DATE NOT NULL COMMENT '导入日期',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_stock_date (stock_code, trade_date),
    INDEX idx_stock_code (stock_code),
    INDEX idx_trade_date (trade_date),
    INDEX idx_import_date (import_date),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT '股票时间序列数据表';

-- 3. 导入任务记录表
CREATE TABLE IF NOT EXISTS import_tasks (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL COMMENT '文件名',
    file_type ENUM('csv', 'txt') NOT NULL COMMENT '文件类型',
    file_size BIGINT NOT NULL COMMENT '文件大小(字节)',
    total_rows BIGINT DEFAULT 0 COMMENT '总行数',
    success_rows BIGINT DEFAULT 0 COMMENT '成功行数',
    error_rows BIGINT DEFAULT 0 COMMENT '错误行数',
    status ENUM('processing', 'completed', 'failed') DEFAULT 'processing' COMMENT '状态',
    error_message TEXT COMMENT '错误信息',
    start_time TIMESTAMP NULL COMMENT '开始时间',
    end_time TIMESTAMP NULL COMMENT '结束时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_file_type (file_type),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT '导入任务记录表';