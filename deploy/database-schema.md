# 股票概念分析系统 - 数据库结构文档

## 📊 数据库概览

- **数据库名称**: `stock_analysis_dev`
- **字符集**: UTF8MB4
- **总表数量**: 18个
- **存储引擎**: InnoDB

## 🗄️ 数据表详细结构

### 1. 核心业务表

#### 1.1 stocks (股票基础信息表)
```sql
CREATE TABLE stocks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(20) NOT NULL UNIQUE COMMENT '股票代码',
    name VARCHAR(100) NOT NULL COMMENT '股票名称',
    market VARCHAR(10) COMMENT '市场类型(SH/SZ)',
    industry VARCHAR(100) COMMENT '所属行业',
    market_cap DECIMAL(18,2) COMMENT '市值',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

#### 1.2 concepts (概念信息表)
```sql
CREATE TABLE concepts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE COMMENT '概念名称',
    description TEXT COMMENT '概念描述',
    category VARCHAR(50) COMMENT '概念分类',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

#### 1.3 stock_concepts (股票概念关联表)
```sql
CREATE TABLE stock_concepts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    stock_id INT NOT NULL COMMENT '股票ID',
    concept_id INT NOT NULL COMMENT '概念ID',
    weight DECIMAL(5,2) DEFAULT 1.00 COMMENT '权重',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (stock_id) REFERENCES stocks(id),
    FOREIGN KEY (concept_id) REFERENCES concepts(id),
    UNIQUE KEY uk_stock_concept (stock_id, concept_id)
);
```

### 2. 数据分析表

#### 2.1 daily_stock_data (每日股票数据表)
```sql
CREATE TABLE daily_stock_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    stock_id INT NOT NULL COMMENT '股票ID',
    trade_date DATE NOT NULL COMMENT '交易日期',
    open_price DECIMAL(10,2) COMMENT '开盘价',
    close_price DECIMAL(10,2) COMMENT '收盘价',
    high_price DECIMAL(10,2) COMMENT '最高价',
    low_price DECIMAL(10,2) COMMENT '最低价',
    volume BIGINT COMMENT '成交量',
    turnover DECIMAL(18,2) COMMENT '成交额',
    turnover_rate DECIMAL(8,4) COMMENT '换手率',
    net_inflow DECIMAL(15,2) COMMENT '净流入',
    total_reads BIGINT COMMENT '阅读量',
    page_count INT COMMENT '页面数量',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (stock_id) REFERENCES stocks(id),
    UNIQUE KEY uk_stock_date (stock_id, trade_date)
);
```

#### 2.2 daily_concept_summaries (每日概念汇总表)
```sql
CREATE TABLE daily_concept_summaries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    analysis_date DATE NOT NULL COMMENT '分析日期',
    concept VARCHAR(100) NOT NULL COMMENT '概念名称',
    stock_count INT NOT NULL COMMENT '个股数量',
    total_net_inflow DECIMAL(18,2) NOT NULL COMMENT '净流入总和',
    avg_net_inflow DECIMAL(15,2) COMMENT '净流入平均值',
    total_market_value DECIMAL(18,2) COMMENT '总市值',
    avg_price DECIMAL(10,2) COMMENT '平均价格',
    avg_turnover_rate DECIMAL(8,4) COMMENT '平均换手率',
    total_reads BIGINT COMMENT '总阅读量',
    total_pages BIGINT COMMENT '总页面数',
    concept_rank INT COMMENT '概念排名',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_analysis_date_concept (analysis_date, concept),
    KEY idx_concept_rank (analysis_date, concept_rank),
    KEY idx_analysis_date (analysis_date)
);
```

#### 2.3 daily_stock_concept_rankings (每日股票概念排名表)
```sql
CREATE TABLE daily_stock_concept_rankings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    analysis_date DATE NOT NULL COMMENT '分析日期',
    concept VARCHAR(100) NOT NULL COMMENT '概念名称',
    stock_code VARCHAR(20) NOT NULL COMMENT '股票代码',
    stock_name VARCHAR(100) NOT NULL COMMENT '股票名称',
    net_inflow_rank INT COMMENT '净流入排名',
    price_rank INT COMMENT '价格排名',
    turnover_rate_rank INT COMMENT '换手率排名',
    total_reads_rank INT COMMENT '阅读量排名',
    net_inflow DECIMAL(15,2) COMMENT '净流入',
    price DECIMAL(10,2) COMMENT '价格',
    turnover_rate DECIMAL(8,4) COMMENT '换手率',
    total_reads BIGINT COMMENT '总阅读量',
    page_count INT COMMENT '页面数量',
    industry VARCHAR(100) COMMENT '行业',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    KEY idx_analysis_date_stock (analysis_date, stock_code),
    KEY idx_concept_net_inflow_rank (concept, net_inflow_rank),
    KEY idx_analysis_date_concept (analysis_date, concept)
);
```

#### 2.4 daily_analysis_tasks (每日分析任务表)
```sql
CREATE TABLE daily_analysis_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    analysis_date DATE NOT NULL COMMENT '分析日期',
    task_type VARCHAR(50) NOT NULL COMMENT '任务类型：concept_ranking, concept_summary',
    status VARCHAR(20) COMMENT '状态：processing, completed, failed',
    processed_concepts INT COMMENT '处理的概念数量',
    processed_stocks INT COMMENT '处理的个股数量',
    source_data_count INT COMMENT '源数据条数',
    start_time DATETIME COMMENT '开始时间',
    end_time DATETIME COMMENT '结束时间',
    error_message TEXT COMMENT '错误信息',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    KEY idx_analysis_date_type (analysis_date, task_type)
);
```

### 3. 用户管理表

#### 3.1 users (用户表)
```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    email VARCHAR(100) NOT NULL UNIQUE COMMENT '邮箱',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
    membership_type ENUM('FREE', 'PRO', 'PREMIUM') DEFAULT 'FREE' COMMENT '会员类型',
    queries_remaining INT DEFAULT 10 COMMENT '剩余查询次数',
    membership_expires_at DATETIME COMMENT '会员到期时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

#### 3.2 user_queries (用户查询记录表)
```sql
CREATE TABLE user_queries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '用户ID',
    query_type ENUM('CONCEPT_ANALYSIS', 'STOCK_RANKING', 'DATA_EXPORT') NOT NULL COMMENT '查询类型',
    query_params JSON COMMENT '查询参数',
    result_count INT COMMENT '结果数量',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### 4. 支付系统表

#### 4.1 payment_packages (支付套餐表)
```sql
CREATE TABLE payment_packages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    package_type VARCHAR(50) NOT NULL UNIQUE COMMENT '套餐类型',
    name VARCHAR(100) NOT NULL COMMENT '套餐名称',
    price DECIMAL(10,2) NOT NULL COMMENT '价格',
    queries_count INT NOT NULL COMMENT '查询次数',
    validity_days INT NOT NULL COMMENT '有效天数',
    membership_type ENUM('FREE', 'PRO', 'PREMIUM') NOT NULL COMMENT '会员类型',
    description TEXT COMMENT '套餐描述',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    sort_order INT DEFAULT 0 COMMENT '排序',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

#### 4.2 payment_orders (支付订单表)
```sql
CREATE TABLE payment_orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_no VARCHAR(64) NOT NULL UNIQUE COMMENT '订单号',
    user_id INT NOT NULL COMMENT '用户ID',
    package_id INT NOT NULL COMMENT '套餐ID',
    amount DECIMAL(10,2) NOT NULL COMMENT '支付金额',
    status ENUM('PENDING', 'PAID', 'CANCELLED', 'EXPIRED') DEFAULT 'PENDING' COMMENT '订单状态',
    payment_method ENUM('WECHAT', 'ALIPAY', 'MOCK') COMMENT '支付方式',
    third_party_order_no VARCHAR(128) COMMENT '第三方订单号',
    paid_at DATETIME COMMENT '支付时间',
    expires_at DATETIME COMMENT '过期时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (package_id) REFERENCES payment_packages(id)
);
```

#### 4.3 payment_notifications (支付通知表)
```sql
CREATE TABLE payment_notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL COMMENT '订单ID',
    notification_type ENUM('PAYMENT', 'REFUND') NOT NULL COMMENT '通知类型',
    third_party_data JSON COMMENT '第三方通知数据',
    processed BOOLEAN DEFAULT FALSE COMMENT '是否已处理',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES payment_orders(id)
);
```

#### 4.4 membership_logs (会员变更日志表)
```sql
CREATE TABLE membership_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '用户ID',
    action_type ENUM('UPGRADE', 'RENEW', 'EXPIRE', 'DOWNGRADE') NOT NULL COMMENT '操作类型',
    old_membership_type ENUM('FREE', 'PRO', 'PREMIUM') COMMENT '原会员类型',
    new_membership_type ENUM('FREE', 'PRO', 'PREMIUM') COMMENT '新会员类型',
    old_expires_at DATETIME COMMENT '原到期时间',
    new_expires_at DATETIME COMMENT '新到期时间',
    order_id INT COMMENT '关联订单ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (order_id) REFERENCES payment_orders(id)
);
```

### 5. 系统管理表

#### 5.1 data_import_records (数据导入记录表)
```sql
CREATE TABLE data_import_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    import_type ENUM('STOCK_DATA', 'CONCEPT_DATA', 'DAILY_DATA') NOT NULL COMMENT '导入类型',
    file_name VARCHAR(255) COMMENT '文件名',
    file_size BIGINT COMMENT '文件大小',
    total_records INT COMMENT '总记录数',
    success_records INT COMMENT '成功记录数',
    failed_records INT COMMENT '失败记录数',
    status ENUM('PROCESSING', 'COMPLETED', 'FAILED') DEFAULT 'PROCESSING' COMMENT '状态',
    error_message TEXT COMMENT '错误信息',
    import_date DATE COMMENT '导入日期',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

## 🔧 数据库维护方案

### 1. 备份策略

#### 1.1 全量备份
```bash
#!/bin/bash
# 每日全量备份
mysqldump -u root -p stock_analysis_dev > backup_$(date +%Y%m%d).sql
```

#### 1.2 增量备份
```bash
# 开启二进制日志
# my.cnf 配置：
log-bin=mysql-bin
expire_logs_days=7
```

### 2. 性能优化

#### 2.1 索引优化
```sql
-- 核心查询索引
CREATE INDEX idx_daily_stock_data_date ON daily_stock_data(trade_date);
CREATE INDEX idx_daily_stock_data_stock_date ON daily_stock_data(stock_id, trade_date);
CREATE INDEX idx_concept_summaries_date_rank ON daily_concept_summaries(analysis_date, concept_rank);
CREATE INDEX idx_stock_rankings_concept_rank ON daily_stock_concept_rankings(concept, net_inflow_rank);
```

#### 2.2 表分区（大数据量时使用）
```sql
-- daily_stock_data 按月分区
ALTER TABLE daily_stock_data 
PARTITION BY RANGE (YEAR(trade_date) * 100 + MONTH(trade_date)) (
    PARTITION p202501 VALUES LESS THAN (202502),
    PARTITION p202502 VALUES LESS THAN (202503),
    -- ... 更多分区
);
```

### 3. 数据清理策略

#### 3.1 历史数据清理
```sql
-- 删除90天前的用户查询记录
DELETE FROM user_queries WHERE created_at < DATE_SUB(NOW(), INTERVAL 90 DAY);

-- 删除过期的支付订单
DELETE FROM payment_orders 
WHERE status = 'EXPIRED' AND created_at < DATE_SUB(NOW(), INTERVAL 30 DAY);
```

#### 3.2 数据归档
```sql
-- 将历史数据移动到归档表
CREATE TABLE daily_stock_data_archive LIKE daily_stock_data;
INSERT INTO daily_stock_data_archive 
SELECT * FROM daily_stock_data WHERE trade_date < DATE_SUB(CURDATE(), INTERVAL 1 YEAR);
```

### 4. 监控脚本

#### 4.1 表大小监控
```sql
-- 监控表大小
SELECT 
    TABLE_NAME,
    ROUND(((DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024), 2) AS 'SIZE_MB',
    TABLE_ROWS
FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = 'stock_analysis_dev'
ORDER BY (DATA_LENGTH + INDEX_LENGTH) DESC;
```

#### 4.2 慢查询监控
```sql
-- 开启慢查询日志
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 2;
```

### 5. 数据迁移工具

#### 5.1 Alembic 迁移配置
```python
# alembic.ini 配置
sqlalchemy.url = mysql+pymysql://user:password@localhost/stock_analysis_dev

# 创建迁移文件
alembic revision --autogenerate -m "add new table"

# 执行迁移
alembic upgrade head
```

## 📈 数据增长预估

### 预计数据量增长
- **daily_stock_data**: 每日约5000条记录，年增长约180万条
- **daily_concept_summaries**: 每日约100条记录，年增长约3.6万条
- **user_queries**: 日活跃用户查询，预计每日1000条，年增长约36万条
- **payment_orders**: 预计每日订单50条，年增长约1.8万条

### 存储规划
- **第一年预计总存储**: 5GB
- **三年后预计存储**: 20GB
- **建议预留空间**: 50GB

## 🚨 紧急恢复方案

### 1. 数据恢复
```bash
# 从备份恢复
mysql -u root -p stock_analysis_dev < backup_20250905.sql
```

### 2. 主从切换
```sql
-- 从库提升为主库
STOP SLAVE;
RESET SLAVE ALL;
```

### 3. 数据修复
```sql
-- 修复表
REPAIR TABLE daily_stock_data;
CHECK TABLE daily_stock_data;
```