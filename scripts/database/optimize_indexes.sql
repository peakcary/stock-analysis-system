-- 数据库索引优化脚本
-- Database Index Optimization

-- ============ 用户表索引 ============

-- 用户名查询优化 (登录时使用)
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- 邮箱查询优化 (找回密码、注册验证)
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- 会员类型查询优化 (统计和过滤)
CREATE INDEX IF NOT EXISTS idx_users_membership_type ON users(membership_type);

-- 活跃状态查询优化
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

-- 会员到期时间查询优化 (自动清理过期会员)
CREATE INDEX IF NOT EXISTS idx_users_membership_expires ON users(membership_expires_at);

-- ============ 支付订单表索引 ============

-- 用户支付历史查询优化
CREATE INDEX IF NOT EXISTS idx_payment_orders_user_id ON payment_orders(user_id);

-- 商户订单号查询优化 (支付回调时使用)
CREATE INDEX IF NOT EXISTS idx_payment_orders_trade_no ON payment_orders(out_trade_no);

-- 支付状态查询优化
CREATE INDEX IF NOT EXISTS idx_payment_orders_status ON payment_orders(status);

-- 支付方式统计优化
CREATE INDEX IF NOT EXISTS idx_payment_orders_method ON payment_orders(payment_method);

-- 创建时间范围查询优化 (报表统计)
CREATE INDEX IF NOT EXISTS idx_payment_orders_created_at ON payment_orders(created_at);

-- 过期时间查询优化 (自动清理过期订单)
CREATE INDEX IF NOT EXISTS idx_payment_orders_expire_time ON payment_orders(expire_time);

-- 复合索引：用户+状态+时间 (用户支付历史页面)
CREATE INDEX IF NOT EXISTS idx_payment_orders_user_status_time ON payment_orders(user_id, status, created_at DESC);

-- ============ 支付套餐表索引 ============

-- 套餐类型查询优化
CREATE INDEX IF NOT EXISTS idx_payment_packages_type ON payment_packages(package_type);

-- 启用状态查询优化
CREATE INDEX IF NOT EXISTS idx_payment_packages_active ON payment_packages(is_active);

-- 会员类型过滤优化
CREATE INDEX IF NOT EXISTS idx_payment_packages_membership_type ON payment_packages(membership_type);

-- 排序显示优化
CREATE INDEX IF NOT EXISTS idx_payment_packages_sort ON payment_packages(sort_order, id);

-- ============ 股票数据表索引 ============

-- 股票代码查询优化 (主要查询场景)
CREATE INDEX IF NOT EXISTS idx_stocks_symbol ON stocks(symbol);

-- 股票名称模糊查询优化
CREATE INDEX IF NOT EXISTS idx_stocks_name ON stocks(name);

-- 概念分类查询优化
CREATE INDEX IF NOT EXISTS idx_stocks_concept ON stocks(concept);

-- 最后更新时间查询优化 (数据同步检查)
CREATE INDEX IF NOT EXISTS idx_stocks_updated_at ON stocks(updated_at);

-- ============ 会员日志表索引 ============

-- 用户会员变更历史查询
CREATE INDEX IF NOT EXISTS idx_membership_logs_user_id ON membership_logs(user_id);

-- 会员类型变更统计
CREATE INDEX IF NOT EXISTS idx_membership_logs_membership_type ON membership_logs(membership_type);

-- 创建时间范围查询
CREATE INDEX IF NOT EXISTS idx_membership_logs_created_at ON membership_logs(created_at);

-- ============ 支付通知表索引 ============

-- 微信交易号查询优化 (支付回调验证)
CREATE INDEX IF NOT EXISTS idx_payment_notifications_transaction_id ON payment_notifications(transaction_id);

-- 商户订单号查询优化
CREATE INDEX IF NOT EXISTS idx_payment_notifications_trade_no ON payment_notifications(out_trade_no);

-- 处理状态查询优化
CREATE INDEX IF NOT EXISTS idx_payment_notifications_processed ON payment_notifications(processed);

-- 创建时间查询优化
CREATE INDEX IF NOT EXISTS idx_payment_notifications_created_at ON payment_notifications(created_at);

-- ============ 性能分析查询 ============

-- 显示当前索引使用情况
SELECT 
    TABLE_NAME,
    INDEX_NAME,
    COLUMN_NAME,
    SEQ_IN_INDEX,
    CARDINALITY
FROM 
    information_schema.STATISTICS 
WHERE 
    TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME IN ('users', 'payment_orders', 'payment_packages', 'stocks', 'membership_logs', 'payment_notifications')
ORDER BY 
    TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX;