-- 微信支付相关数据库表
-- Payment related database tables for WeChat Pay

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 使用现有数据库
USE stock_analysis_dev;

-- 1. 支付套餐配置表
CREATE TABLE payment_packages (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    package_type VARCHAR(20) UNIQUE NOT NULL COMMENT '套餐类型',
    name VARCHAR(50) NOT NULL COMMENT '套餐名称',
    price DECIMAL(10, 2) NOT NULL COMMENT '价格',
    queries_count INT DEFAULT 0 COMMENT '查询次数',
    validity_days INT DEFAULT 0 COMMENT '有效天数',
    membership_type ENUM('free', 'pro', 'premium') DEFAULT 'free' COMMENT '会员类型',
    description TEXT COMMENT '套餐描述',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    sort_order INT DEFAULT 0 COMMENT '排序',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX idx_package_type (package_type),
    INDEX idx_is_active (is_active),
    INDEX idx_sort_order (sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='支付套餐配置表';

-- 2. 支付订单表
CREATE TABLE payment_orders (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    user_id INT NOT NULL COMMENT '用户ID',
    out_trade_no VARCHAR(64) UNIQUE NOT NULL COMMENT '商户订单号',
    transaction_id VARCHAR(64) COMMENT '微信交易号',
    package_type VARCHAR(20) NOT NULL COMMENT '套餐类型',
    package_name VARCHAR(50) NOT NULL COMMENT '套餐名称',
    amount DECIMAL(10, 2) NOT NULL COMMENT '支付金额',
    status ENUM('pending', 'paid', 'failed', 'cancelled', 'refunded', 'expired') DEFAULT 'pending' COMMENT '订单状态',
    payment_method ENUM('wechat_native', 'wechat_h5', 'wechat_miniprogram', 'alipay') DEFAULT 'wechat_native' COMMENT '支付方式',
    prepay_id VARCHAR(64) COMMENT '微信预支付ID',
    code_url TEXT COMMENT '支付二维码URL',
    h5_url TEXT COMMENT 'H5支付链接',
    expire_time DATETIME NOT NULL COMMENT '订单过期时间',
    paid_at DATETIME COMMENT '支付完成时间',
    cancelled_at DATETIME COMMENT '取消时间',
    refunded_at DATETIME COMMENT '退款时间',
    refund_amount DECIMAL(10, 2) DEFAULT 0 COMMENT '退款金额',
    client_ip VARCHAR(45) COMMENT '客户端IP',
    user_agent TEXT COMMENT '用户代理',
    notify_data JSON COMMENT '支付通知原始数据',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_out_trade_no (out_trade_no),
    INDEX idx_transaction_id (transaction_id),
    INDEX idx_status (status),
    INDEX idx_package_type (package_type),
    INDEX idx_expire_time (expire_time),
    INDEX idx_paid_at (paid_at),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='支付订单表';

-- 3. 支付通知记录表
CREATE TABLE payment_notifications (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    out_trade_no VARCHAR(64) NOT NULL COMMENT '商户订单号',
    transaction_id VARCHAR(64) COMMENT '微信交易号',
    notification_type ENUM('payment', 'refund') DEFAULT 'payment' COMMENT '通知类型',
    return_code VARCHAR(16) COMMENT '返回状态码',
    result_code VARCHAR(16) COMMENT '业务结果',
    raw_data TEXT NOT NULL COMMENT '原始通知数据',
    is_valid BOOLEAN DEFAULT FALSE COMMENT '签名是否有效',
    processed BOOLEAN DEFAULT FALSE COMMENT '是否已处理',
    process_result TEXT COMMENT '处理结果',
    client_ip VARCHAR(45) COMMENT '通知来源IP',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '接收时间',
    processed_at TIMESTAMP NULL COMMENT '处理时间',
    
    INDEX idx_out_trade_no (out_trade_no),
    INDEX idx_transaction_id (transaction_id),
    INDEX idx_processed (processed),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='支付通知记录表';

-- 4. 用户会员变更记录表
CREATE TABLE membership_logs (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    user_id INT NOT NULL COMMENT '用户ID',
    payment_order_id INT COMMENT '支付订单ID',
    action_type ENUM('upgrade', 'renew', 'add_queries', 'expire', 'manual') NOT NULL COMMENT '操作类型',
    old_membership_type ENUM('free', 'pro', 'premium') COMMENT '原会员类型',
    new_membership_type ENUM('free', 'pro', 'premium') COMMENT '新会员类型',
    old_queries_remaining INT DEFAULT 0 COMMENT '原剩余查询次数',
    new_queries_remaining INT DEFAULT 0 COMMENT '新剩余查询次数',
    queries_added INT DEFAULT 0 COMMENT '增加的查询次数',
    old_expires_at DATETIME COMMENT '原到期时间',
    new_expires_at DATETIME COMMENT '新到期时间',
    days_added INT DEFAULT 0 COMMENT '增加的天数',
    operator_id INT COMMENT '操作员ID（管理员操作时）',
    notes TEXT COMMENT '备注',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (payment_order_id) REFERENCES payment_orders(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_payment_order_id (payment_order_id),
    INDEX idx_action_type (action_type),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户会员变更记录表';

-- 5. 退款记录表
CREATE TABLE refund_records (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    payment_order_id INT NOT NULL COMMENT '支付订单ID',
    out_refund_no VARCHAR(64) UNIQUE NOT NULL COMMENT '商户退款单号',
    refund_id VARCHAR(64) COMMENT '微信退款单号',
    refund_amount DECIMAL(10, 2) NOT NULL COMMENT '退款金额',
    refund_reason VARCHAR(255) COMMENT '退款原因',
    refund_status ENUM('processing', 'success', 'failed', 'closed') DEFAULT 'processing' COMMENT '退款状态',
    refund_channel VARCHAR(32) COMMENT '退款渠道',
    operator_id INT COMMENT '操作员ID',
    notify_data JSON COMMENT '退款通知数据',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '申请时间',
    completed_at TIMESTAMP NULL COMMENT '完成时间',
    
    FOREIGN KEY (payment_order_id) REFERENCES payment_orders(id) ON DELETE CASCADE,
    INDEX idx_payment_order_id (payment_order_id),
    INDEX idx_out_refund_no (out_refund_no),
    INDEX idx_refund_id (refund_id),
    INDEX idx_refund_status (refund_status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='退款记录表';

-- 插入默认支付套餐配置
INSERT INTO payment_packages (package_type, name, price, queries_count, validity_days, membership_type, description, sort_order) VALUES
('queries_10', '10次查询包', 9.90, 10, 30, 'free', '适合偶尔使用的用户，30天内有效', 1),
('queries_50', '50次查询包', 39.90, 50, 60, 'free', '高频使用推荐，60天内有效', 2),
('monthly_pro', '专业版月卡', 29.90, 1000, 30, 'pro', '专业版权限，1000次查询/月', 3),
('quarterly_pro', '专业版季卡', 79.90, 3000, 90, 'pro', '专业版权限，3000次查询/季', 4),
('yearly_pro', '专业版年卡', 299.90, 12000, 365, 'pro', '专业版权限，12000次查询/年', 5),
('monthly_premium', '旗舰版月卡', 59.90, 2000, 30, 'premium', '旗舰版全功能，2000次查询/月', 6),
('quarterly_premium', '旗舰版季卡', 149.90, 6000, 90, 'premium', '旗舰版全功能，6000次查询/季', 7),
('yearly_premium', '旗舰版年卡', 499.90, 24000, 365, 'premium', '旗舰版全功能，24000次查询/年', 8);

-- 创建索引优化查询性能
CREATE INDEX idx_users_membership ON users(membership_type, membership_expires_at);
CREATE INDEX idx_payments_user_status ON payments(user_id, payment_status, created_at);

COMMIT;

-- 显示创建结果
SELECT 'Payment tables created successfully!' as status;

-- 显示套餐配置
SELECT 'Payment packages:' as info;
SELECT package_type, name, price, queries_count, validity_days, membership_type FROM payment_packages ORDER BY sort_order;