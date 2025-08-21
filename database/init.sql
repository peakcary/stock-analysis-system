-- 股票概念分析系统数据库初始化脚本
-- Stock Concept Analysis System Database Initialization Script

-- 创建数据库
CREATE DATABASE IF NOT EXISTS stock_analysis CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE stock_analysis;

-- 1. 股票基本信息表
CREATE TABLE stocks (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    stock_code VARCHAR(10) UNIQUE NOT NULL COMMENT '股票代码',
    stock_name VARCHAR(100) NOT NULL COMMENT '股票名称',
    industry VARCHAR(100) COMMENT '行业',
    is_convertible_bond BOOLEAN DEFAULT FALSE COMMENT '是否为转债',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_stock_code (stock_code),
    INDEX idx_convertible_bond (is_convertible_bond),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='股票基本信息表';

-- 2. 概念表
CREATE TABLE concepts (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    concept_name VARCHAR(100) UNIQUE NOT NULL COMMENT '概念名称',
    description TEXT COMMENT '概念描述',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_concept_name (concept_name),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='概念表';

-- 3. 股票概念关联表
CREATE TABLE stock_concepts (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    stock_id INT NOT NULL COMMENT '股票ID',
    concept_id INT NOT NULL COMMENT '概念ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (stock_id) REFERENCES stocks(id) ON DELETE CASCADE,
    FOREIGN KEY (concept_id) REFERENCES concepts(id) ON DELETE CASCADE,
    UNIQUE KEY unique_stock_concept (stock_id, concept_id),
    INDEX idx_stock_id (stock_id),
    INDEX idx_concept_id (concept_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='股票概念关联表';

-- 4. 每日股票数据表
CREATE TABLE daily_stock_data (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    stock_id INT NOT NULL COMMENT '股票ID',
    trade_date DATE NOT NULL COMMENT '交易日期',
    pages_count INT DEFAULT 0 COMMENT '页数',
    total_reads INT DEFAULT 0 COMMENT '总阅读数',
    price DECIMAL(10, 2) DEFAULT 0 COMMENT '价格',
    turnover_rate DECIMAL(5, 2) DEFAULT 0 COMMENT '换手率',
    net_inflow DECIMAL(15, 2) DEFAULT 0 COMMENT '净流入',
    heat_value DECIMAL(15, 2) DEFAULT 0 COMMENT '热度值(来自TXT文件)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (stock_id) REFERENCES stocks(id) ON DELETE CASCADE,
    UNIQUE KEY unique_stock_date (stock_id, trade_date),
    INDEX idx_trade_date (trade_date),
    INDEX idx_stock_date (stock_id, trade_date),
    INDEX idx_heat_value (heat_value)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='每日股票数据表';

-- 5. 每日概念排名表
CREATE TABLE daily_concept_rankings (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    concept_id INT NOT NULL COMMENT '概念ID',
    stock_id INT NOT NULL COMMENT '股票ID',
    trade_date DATE NOT NULL COMMENT '交易日期',
    rank_in_concept INT NOT NULL COMMENT '在概念中的排名',
    heat_value DECIMAL(15, 2) DEFAULT 0 COMMENT '热度值',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (concept_id) REFERENCES concepts(id) ON DELETE CASCADE,
    FOREIGN KEY (stock_id) REFERENCES stocks(id) ON DELETE CASCADE,
    UNIQUE KEY unique_concept_stock_date (concept_id, stock_id, trade_date),
    INDEX idx_concept_date (concept_id, trade_date),
    INDEX idx_trade_date_rank (trade_date, rank_in_concept),
    INDEX idx_concept_rank (concept_id, rank_in_concept)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='每日概念排名表';

-- 6. 每日概念总和表
CREATE TABLE daily_concept_sums (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    concept_id INT NOT NULL COMMENT '概念ID',
    trade_date DATE NOT NULL COMMENT '交易日期',
    total_heat_value DECIMAL(15, 2) NOT NULL COMMENT '概念总热度值',
    stock_count INT NOT NULL COMMENT '概念包含股票数量',
    average_heat_value DECIMAL(15, 2) NOT NULL COMMENT '平均热度值',
    is_new_high BOOLEAN DEFAULT FALSE COMMENT '是否创新高',
    days_for_high_check INT DEFAULT 10 COMMENT '新高检查天数',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (concept_id) REFERENCES concepts(id) ON DELETE CASCADE,
    UNIQUE KEY unique_concept_date (concept_id, trade_date),
    INDEX idx_trade_date (trade_date),
    INDEX idx_new_high (trade_date, is_new_high),
    INDEX idx_concept_date (concept_id, trade_date),
    INDEX idx_total_heat (total_heat_value)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='每日概念总和表';

-- 7. 用户表
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    username VARCHAR(50) UNIQUE NOT NULL COMMENT '用户名',
    email VARCHAR(100) UNIQUE NOT NULL COMMENT '邮箱',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
    membership_type ENUM('free', 'paid_10', 'monthly', 'quarterly', 'yearly') DEFAULT 'free' COMMENT '会员类型',
    queries_remaining INT DEFAULT 10 COMMENT '剩余查询次数',
    membership_expires_at DATETIME NULL COMMENT '会员到期时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_membership (membership_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- 8. 用户查询记录表
CREATE TABLE user_queries (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    user_id INT NOT NULL COMMENT '用户ID',
    query_type ENUM('stock_search', 'concept_search', 'top_concepts', 'new_highs', 'bond_search') NOT NULL COMMENT '查询类型',
    query_params JSON COMMENT '查询参数',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_date (user_id, created_at),
    INDEX idx_query_type (query_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户查询记录表';

-- 9. 支付记录表
CREATE TABLE payments (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    user_id INT NOT NULL COMMENT '用户ID',
    amount DECIMAL(10, 2) NOT NULL COMMENT '支付金额',
    payment_type ENUM('10_queries', 'monthly', 'quarterly', 'yearly') NOT NULL COMMENT '支付类型',
    payment_status ENUM('pending', 'completed', 'failed', 'refunded') DEFAULT 'pending' COMMENT '支付状态',
    payment_method VARCHAR(50) COMMENT '支付方式',
    transaction_id VARCHAR(100) COMMENT '交易ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    completed_at TIMESTAMP NULL COMMENT '完成时间',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_payment (user_id, created_at),
    INDEX idx_payment_status (payment_status),
    INDEX idx_transaction_id (transaction_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='支付记录表';

-- 插入一些测试数据
-- 测试股票数据
INSERT INTO stocks (stock_code, stock_name, industry, is_convertible_bond) VALUES
('000001', '平安银行', '银行业', FALSE),
('000002', '万科A', '房地产业', FALSE),
('118058', '微导转债', '电子信息', TRUE),
('127110', '广核转债', '电力行业', TRUE),
('111023', '利柏转债', '专用设备', TRUE);

-- 测试概念数据
INSERT INTO concepts (concept_name, description) VALUES
('银行股', '银行业相关股票'),
('房地产', '房地产行业相关股票'),
('半导体', '半导体行业相关股票'),
('新能源', '新能源行业相关股票'),
('人工智能', '人工智能概念相关股票');

-- 测试股票概念关联
INSERT INTO stock_concepts (stock_id, concept_id) VALUES
(1, 1), -- 平安银行 -> 银行股
(2, 2), -- 万科A -> 房地产
(3, 3), -- 微导转债 -> 半导体
(4, 4), -- 广核转债 -> 新能源
(5, 5); -- 利柏转债 -> 人工智能

-- 创建默认管理员用户 (密码: admin123)
INSERT INTO users (username, email, password_hash, membership_type, queries_remaining) VALUES
('admin', 'admin@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewxOr4f4eP3QdWJa', 'yearly', 999999);

COMMIT;

-- 显示创建结果
SELECT 'Database initialization completed successfully!' as status;